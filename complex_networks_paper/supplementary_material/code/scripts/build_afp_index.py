#!/usr/bin/env python3
"""Automated script to build a static RAG index for all AFP entries incrementally.

Verifies and builds the recorded heap for each session on-demand, spawns the REPL,
ingests the aspects, embeds them via Voyage AI, and incrementally updates the static index.
Tracks progress in progress.json to support resuming interrupted jobs gracefully.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from edel.il.ingest import EphemeralReplClient, ingest_session_lemmas
from edel.pipeline.embedding import run_embedding_stage
from edel.il.index import NumpyRAGIndex


def get_afp_sessions(roots_file: Path) -> list[str]:
    """Parse the AFP ROOTS file to get the list of session directory names."""
    if not roots_file.exists():
        print(f"Error: ROOTS file not found at {roots_file}")
        sys.exit(1)

    sessions = []
    with open(roots_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            sessions.append(line)
    return sessions


PROTECTED_HEAPS = {"HOL-Library", "HOL", "Pure"}


def save_progress_atomic(progress_file: Path, processed_sessions: set[str]):
    """Atomically write progress.json via a temporary file to prevent corruption."""
    tmp_file = progress_file.with_suffix(".json.tmp")
    try:
        with open(tmp_file, "w") as f:
            json.dump(sorted(list(processed_sessions)), f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_file, progress_file)
    except Exception as e:
        print(f"[Warning] Failed to write progress file atomically: {e}")
        if tmp_file.exists():
            try:
                tmp_file.unlink()
            except Exception:
                pass


def build_session_heap(isabelle_path: str, afp_thys_dir: Path, session: str, jobs: int = 16, timeout_secs: int = 1800) -> bool:
    """Build the recorded heap for the specific session using isabelle build with timeout."""
    print(f"\n[Isabelle] Verifying/building recorded heap for session: {session} (jobs: {jobs}, timeout: {timeout_secs}s)...")
    cmd = [
        isabelle_path, "build",
        "-b",
        "-o", "record_theories=true",
        "-d", str(afp_thys_dir),
        "-j", str(jobs),
        session
    ]
    try:
        result = subprocess.run(cmd, check=True, text=True, capture_output=True, timeout=timeout_secs)
        print(f"[Isabelle] Heap build successful for session: {session}")
        return True
    except subprocess.TimeoutExpired:
        print(f"[Isabelle Error] Build timed out after {timeout_secs}s for session: {session}")
        return False
    except subprocess.CalledProcessError as e:
        print(f"[Isabelle Error] Failed to build session heap for {session}:\n{e.stderr or e.stdout}")
        return False


def get_isabelle_heaps_dir(isabelle_path: str) -> Path:
    """Get the ISABELLE_HEAPS directory path using isabelle getenv."""
    try:
        res = subprocess.run([isabelle_path, "getenv", "ISABELLE_HEAPS"], capture_output=True, text=True, check=True)
        for line in res.stdout.splitlines():
            if line.startswith("ISABELLE_HEAPS="):
                return Path(line.split("=", 1)[1].strip())
    except Exception as e:
        print(f"Warning: Failed to get ISABELLE_HEAPS via getenv: {e}")
    return Path(os.path.expanduser("~/.isabelle/Isabelle2025-2/heaps"))


def cleanup_session_heaps(heaps_dir: Path, session: str | None = None, clean_all_transient: bool = False):
    """Deletes built heap images and logs to save disk space while protecting base heaps."""
    if not heaps_dir.exists():
        return

    if clean_all_transient:
        for arch_dir in heaps_dir.iterdir():
            if not arch_dir.is_dir():
                continue
            for p in arch_dir.iterdir():
                if p.is_file() and p.name not in PROTECTED_HEAPS:
                    try:
                        p.unlink()
                        print(f"[Cleanup] Deleted transient heap: {p.name}")
                    except Exception as e:
                        print(f"[Cleanup] Warning: Failed to delete heap {p}: {e}")
            log_dir = arch_dir / "log"
            if log_dir.is_dir():
                for p in log_dir.iterdir():
                    stem = p.name.split(".")[0]
                    if stem not in PROTECTED_HEAPS:
                        try:
                            p.unlink()
                        except Exception:
                            pass
    elif session:
        for p in heaps_dir.glob(f"*/{session}"):
            if p.is_file() and p.name not in PROTECTED_HEAPS:
                try:
                    p.unlink()
                    print(f"[Cleanup] Deleted heap image: {p}")
                except Exception as e:
                    print(f"[Cleanup] Warning: Failed to delete heap image {p}: {e}")

        for p in heaps_dir.glob(f"*/log/{session}.*"):
            if p.is_file():
                try:
                    p.unlink()
                    print(f"[Cleanup] Deleted log file: {p}")
                except Exception as e:
                    print(f"[Cleanup] Warning: Failed to delete log file {p}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Incremental AFP RAG Index Builder")
    parser.add_argument("--isabelle", default="/home/correia/Isabelle2025-2/bin/isabelle", help="Path to isabelle binary")
    parser.add_argument("--afp-dir", default="/home/correia/edel/external/afp-2025-2/thys", help="Path to AFP thys/ directory")
    parser.add_argument("--output", default="artifacts/afp_rag_index", help="Output RAG index directory")
    parser.add_argument("--provider", default="voyage", choices=["openai", "voyage"], help="Embedding provider")
    parser.add_argument("--model", default="voyage-code-3", help="Embedding model name")
    parser.add_argument("--port", type=int, default=9155, help="Port to run REPL daemon on")
    parser.add_argument("--jobs", "-j", type=int, default=16, help="Number of parallel Isabelle build jobs")
    parser.add_argument("--sessions", nargs="+", default=None, help="Specific sessions to index (defaults to all in ROOTS)")
    parser.add_argument("--limit", type=int, default=None, help="Max number of sessions to process")
    parser.add_argument("--skip-embedding", action="store_true", help="Skip embedding stage (for debugging segments/metadata)")
    parser.add_argument("--calculate-missing-embeddings", action="store_true", help="Load existing index, calculate missing embeddings, and exit.")
    parser.add_argument("--include-hol", action="store_true", help="Include parent HOL theories in addition to AFP session theories")
    parser.add_argument("--cleanup-heaps", action="store_true", help="Delete built heap images and logs after processing to save disk space")

    args = parser.parse_args()

    # Path auto-detection if running on deeptwelve
    isabelle_path = args.isabelle
    if not os.path.exists(isabelle_path):
        alt_isabelle = os.path.expanduser("~/Isabelle2025-2/bin/isabelle")
        if os.path.exists(alt_isabelle):
            isabelle_path = alt_isabelle

    afp_thys_dir = Path(args.afp_dir)
    if not afp_thys_dir.exists():
        alt_afp = Path(os.path.expanduser("~/lcorreia/eel/external/afp-2025-2/thys"))
        if alt_afp.exists():
            afp_thys_dir = alt_afp

    heaps_dir = get_isabelle_heaps_dir(isabelle_path)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"==================================================")
    print(f"AFP RAG Index Builder Configuration:")
    print(f"  Isabelle Binary: {isabelle_path}")
    print(f"  AFP Thys Dir:    {afp_thys_dir}")
    print(f"  Output Dir:      {output_dir}")
    print(f"  Provider:        {args.provider}")
    print(f"  Model:           {args.model}")
    print(f"  REPL Port:       {args.port}")
    print(f"  Parallel Jobs:   {args.jobs}")
    print(f"  Cleanup Heaps:   {args.cleanup_heaps}")
    print(f"==================================================")
    sys.stdout.flush()

    # 1. Validate API Key (Only if we are actually embedding)
    api_key = None
    if not args.skip_embedding or args.calculate_missing_embeddings:
        api_key_env = "VOYAGE_API_KEY" if args.provider == "voyage" else "OPENAI_API_KEY"
        api_key = os.getenv(api_key_env)
        if not api_key:
            print(f"Error: {api_key_env} is not set in environment or .env file.")
            sys.exit(1)

    # 2. Load Existing Index (if any)
    master_index = NumpyRAGIndex()
    index_exists = (output_dir / "metadata.parquet").exists() and (output_dir / "embeddings.npz").exists()
    if index_exists:
        try:
            master_index.load(output_dir)
            print(f"Loaded existing index with {len(master_index.metadata)} lemmas.")
        except Exception as e:
            print(f"Warning: Failed to load existing index: {e}")
            if args.calculate_missing_embeddings:
                print("Error: Cannot calculate missing embeddings because loading index failed.")
                sys.exit(1)
    else:
        if args.calculate_missing_embeddings:
            print(f"Error: Existing index not found in {output_dir}. Cannot calculate missing embeddings.")
            sys.exit(1)

    # 3. Calculate Missing Embeddings Flow
    if args.calculate_missing_embeddings:
        N = len(master_index.metadata)
        M = N
        aspects = ["problem", "method", "finding", "interpretation"]
        for aspect in aspects:
            arr = master_index.embeddings.get(aspect)
            if arr is None:
                M = 0
            else:
                M = min(M, len(arr))

        if M >= N:
            print("No missing embeddings found. All lemmas have embeddings.")
        else:
            print(f"Found {N - M} lemmas missing embeddings. Calculating...")
            missing_metadata = master_index.metadata[M:]

            for aspect in aspects:
                if master_index.embeddings.get(aspect) is not None:
                    master_index.embeddings[aspect] = master_index.embeddings[aspect][:M]

            chunk_size = 200
            for i in range(0, len(missing_metadata), chunk_size):
                chunk_meta = missing_metadata[i : i + chunk_size]
                print(f"\n[Embedding] Processing missing chunk {i // chunk_size + 1}/{(len(missing_metadata) + chunk_size - 1) // chunk_size}...")
                df_chunk = pd.DataFrame(chunk_meta)
                embed_config = {
                    "embedding": {
                        "provider": args.provider,
                        "model": args.model,
                        "api_key": api_key,
                        "required_aspects": ["problem"],
                    },
                    "processing_mode": "simple"
                }
                try:
                    df_embedded = run_embedding_stage(df_chunk, embed_config)
                    embedding_dim = 1024
                    for aspect in aspects:
                        if master_index.embeddings[aspect] is not None and len(master_index.embeddings[aspect]) > 0:
                            embedding_dim = master_index.embeddings[aspect].shape[1]
                            break

                    for aspect in aspects:
                        col = f"{aspect}_embedding"
                        col_data = df_embedded[col].tolist() if col in df_embedded.columns else [None] * len(df_chunk)
                        parsed_data = []
                        for val in col_data:
                            if val is None:
                                parsed_data.append(np.zeros(embedding_dim, dtype=np.float32))
                            elif isinstance(val, str):
                                try:
                                    parsed_val = json.loads(val)
                                    parsed_data.append(np.array(parsed_val, dtype=np.float32) if parsed_val else np.zeros(embedding_dim, dtype=np.float32))
                                except Exception:
                                    parsed_data.append(np.zeros(embedding_dim, dtype=np.float32))
                            else:
                                parsed_data.append(np.array(val, dtype=np.float32))

                        chunk_arr = np.vstack(parsed_data)
                        old_arr = master_index.embeddings.get(aspect)
                        if old_arr is None or len(old_arr) == 0:
                            master_index.embeddings[aspect] = chunk_arr
                        else:
                            master_index.embeddings[aspect] = np.concatenate([old_arr, chunk_arr], axis=0)

                    master_index.save(output_dir)
                    print(f"[Index] Saved progress. Unified index now has {len(master_index.embeddings['problem'])} embeddings.")
                except Exception as e:
                    print(f"[ERROR] Failed to embed/index chunk: {e}")
                    sys.exit(1)
        return

    # 4. Parse AFP Sessions
    roots_file = afp_thys_dir / "ROOTS"
    sessions = get_afp_sessions(roots_file)
    print(f"Loaded {len(sessions)} total sessions from {roots_file}")

    if args.sessions:
        sessions = [s for s in sessions if s in args.sessions]
        print(f"Filtered to {len(sessions)} requested sessions: {sessions}")

    if args.limit:
        sessions = sessions[:args.limit]
        print(f"Limited run to first {len(sessions)} sessions.")

    # 5. Load Progress
    progress_file = output_dir / "progress.json"
    processed_sessions = set()
    if progress_file.exists() and progress_file.stat().st_size > 0:
        try:
            with open(progress_file, "r") as f:
                processed_sessions = set(json.load(f))
            print(f"Resuming job: {len(processed_sessions)} / {len(sessions)} sessions already recorded in progress.json.")
        except Exception as e:
            print(f"Warning: Failed to load progress file: {e}")

    # Fallback/cross-check: recover any sessions already ingested into master_index metadata
    if len(master_index.metadata) > 0:
        indexed_sessions = set()
        for item in master_index.metadata:
            if "session" in item and item["session"]:
                indexed_sessions.add(item["session"])
            elif "theory" in item and item["theory"] and "." in item["theory"]:
                indexed_sessions.add(item["theory"].split(".")[0])
        recovered = indexed_sessions - processed_sessions
        if recovered:
            print(f"Recovered {len(recovered)} processed session(s) from existing index metadata: {sorted(list(recovered))}")
            processed_sessions.update(indexed_sessions)
            save_progress_atomic(progress_file, processed_sessions)

    # Initial transient heap cleanup to guarantee maximum disk headroom
    if args.cleanup_heaps:
        cleanup_session_heaps(heaps_dir, clean_all_transient=True)

    # 6. Session Processing Loop
    for idx, session in enumerate(sessions, 1):
        print(f"\n==================================================")
        print(f"Processing session [{idx}/{len(sessions)}]: {session}")
        print(f"==================================================")
        sys.stdout.flush()

        if session in processed_sessions:
            print(f"[SKIP] Session '{session}' already processed.")
            continue

        # A. Build the session heap
        build_ok = build_session_heap(isabelle_path, afp_thys_dir, session, jobs=args.jobs)
        if not build_ok:
            print(f"[WARNING] Skipping session '{session}' due to heap build failure.")
            processed_sessions.add(session)
            save_progress_atomic(progress_file, processed_sessions)
            if args.cleanup_heaps:
                cleanup_session_heaps(heaps_dir, session, clean_all_transient=True)
            sys.stdout.flush()
            continue

        # B. Start REPL Daemon
        token = f"ir_afp_token_{session}_{int(time.time())}"
        print(f"[REPL] Starting REPL daemon for session '{session}' on port {args.port}...")
        env = os.environ.copy()
        env["IR_AUTH_TOKEN"] = token

        repl_proc = subprocess.Popen([
            sys.executable, "AutoCorrode/ir/repl.py",
            "--isabelle", isabelle_path,
            "--session", session,
            "--dir", str(afp_thys_dir),
            "--port", str(args.port),
            "--server-only"
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)

        # Wait for TCP port to open
        t0 = time.time()
        connected = False
        while time.time() - t0 < 60:
            try:
                s = socket.socket()
                s.settimeout(2.0)
                s.connect(("127.0.0.1", args.port))
                s.close()
                connected = True
                break
            except Exception:
                time.sleep(0.5)

        if not connected:
            print(f"[ERROR] REPL port {args.port} did not become available in 60s for session '{session}'.")
            if repl_proc.poll() is not None:
                out = repl_proc.stdout.read() if repl_proc.stdout else ""
                print(f"[REPL Crash Output]:\n{out[:500]}")
            repl_proc.terminate()
            try:
                repl_proc.wait(timeout=5)
            except Exception:
                repl_proc.kill()
            processed_sessions.add(session)
            save_progress_atomic(progress_file, processed_sessions)
            if args.cleanup_heaps:
                cleanup_session_heaps(heaps_dir, session, clean_all_transient=True)
            sys.stdout.flush()
            continue

        time.sleep(1.0)
        # Configure full spans
        client = EphemeralReplClient(host="127.0.0.1", port=args.port, token=token)
        for _ in range(10):
            try:
                client.send("Ir.config (fn cfg => {color = #color cfg, show_ignored = #show_ignored cfg, full_spans = true, show_theory_in_source = #show_theory_in_source cfg, auto_replay = #auto_replay cfg});")
                break
            except Exception:
                time.sleep(0.5)

        # C. Ingest lemmas
        df_new = None
        try:
            theory_filter = f"^(?:{session}|HOL|HOL-[a-zA-Z0-9_-]+)\\." if args.include_hol else f"^{session}\\."
            df_new = ingest_session_lemmas(
                host="127.0.0.1",
                port=args.port,
                token=token,
                theory_filter=theory_filter
            )
            print(f"[Ingest] Extracted {len(df_new) if df_new is not None else 0} units from '{session}'.")
        except Exception as e:
            print(f"[ERROR] Ingestion failed for session '{session}': {e}")
        finally:
            print("[REPL] Stopping REPL daemon...")
            repl_proc.terminate()
            try:
                repl_proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                repl_proc.kill()
                repl_proc.wait()

        # D. Embed and index
        if df_new is not None and len(df_new) > 0:
            if len(master_index.metadata) > 0:
                existing_titles = {item["title"] for item in master_index.metadata}
                df_new = df_new[~df_new["title"].isin(existing_titles)].reset_index(drop=True)
                print(f"[Deduplication] Filtered out lemmas already in the index. Remaining: {len(df_new)} new lemmas.")

            df_embedded = None
            if len(df_new) > 0:
                if args.skip_embedding:
                    print(f"[Embedding] Skipping embedding stage as requested for session '{session}'.")
                    df_embedded = df_new
                else:
                    print(f"[Embedding] Generating embeddings for {len(df_new)} new lemmas via {args.provider}/{args.model}...")
                    try:
                        embed_config = {
                            "embedding": {
                                "provider": args.provider,
                                "model": args.model,
                                "api_key": api_key,
                                "required_aspects": ["problem"],
                            },
                            "processing_mode": "simple"
                        }
                        df_embedded = run_embedding_stage(df_new, embed_config)
                        print(f"[Embedding] Embeddings generated successfully. Valid: {len(df_embedded)}")
                    except Exception as e:
                        print(f"[ERROR] Embedding stage failed for '{session}': {e}")

            if df_embedded is not None and len(df_embedded) > 0:
                try:
                    session_index = NumpyRAGIndex()
                    session_index.build_from_dataframe(df_embedded)

                    if len(master_index.metadata) > 0:
                        master_index.metadata.extend(session_index.metadata)
                        for aspect in ["problem", "method", "finding", "interpretation"]:
                            old_arr = master_index.embeddings.get(aspect)
                            new_arr = session_index.embeddings.get(aspect)
                            if new_arr is not None:
                                if old_arr is not None:
                                    master_index.embeddings[aspect] = np.concatenate([old_arr, new_arr], axis=0)
                                else:
                                    master_index.embeddings[aspect] = new_arr
                    else:
                        master_index = session_index

                    master_index.save(output_dir)
                    print(f"[Index] Unified index updated with '{session}' (Total size: {len(master_index.metadata)} lemmas).")
                except Exception as e:
                    print(f"[ERROR] Indexing stage failed for '{session}': {e}")
        else:
            print(f"[Info] No new lemmas to index for session '{session}'.")

        # E. Record Progress
        processed_sessions.add(session)
        save_progress_atomic(progress_file, processed_sessions)

        # F. Cleanup Session Heaps to save space if requested
        if args.cleanup_heaps:
            cleanup_session_heaps(heaps_dir, session, clean_all_transient=True)

        sys.stdout.flush()

    print("\n==================================================")
    print(f"Job complete! All {len(sessions)} sessions processed.")
    print(f"Total size of final static RAG index: {len(master_index.metadata)} lemmas.")
    print("==================================================")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
