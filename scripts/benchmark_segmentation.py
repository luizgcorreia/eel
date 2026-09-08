#!/usr/bin/env python3
"""Benchmark and qualitative analysis script for Isabelle session segmentation in I/L.

Processes target Isabelle/AFP sessions (e.g. HOL-Library, AVL-Trees, Aho_Corasick, Featherweight_OCL),
measures exact per-theory and per-lemma extraction timings, validates the four aspects
(problem, method, finding, interpretation), and extrapolates the total processing time
for the entire AFP on the compute node.
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
from typing import Any

import pandas as pd
import numpy as np

# Ensure edel is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from edel.il.ingest import EphemeralReplClient, compute_definition_dependencies
from edel.il.parser import parse_source_segments, group_segments_to_lemmas
from edel.il.aspects import extract_aspects, _extract_dependencies
from edel.il.metadata import AFPMetadataParser

SENTINEL = "<<DONE>>"


class SessionReplContext:
    """Context manager to spawn and gracefully shutdown an Isabelle REPL session."""

    def __init__(
        self,
        isabelle_path: str,
        afp_thys_dir: str,
        session: str,
        port: int = 9148,
        token: str = "il_bench_token_xyz"
    ):
        self.isabelle_path = isabelle_path
        self.afp_thys_dir = afp_thys_dir
        self.session = session
        self.port = port
        self.token = token
        self.proc: subprocess.Popen | None = None
        self.client: EphemeralReplClient | None = None

    def __enter__(self) -> EphemeralReplClient:
        print(f"\n[REPL] Launching REPL daemon for session '{self.session}' on port {self.port}...")
        env = os.environ.copy()
        env["IR_AUTH_TOKEN"] = self.token

        cmd = [
            sys.executable,
            str(Path(__file__).resolve().parent.parent / "AutoCorrode" / "ir" / "repl.py"),
            "--isabelle", self.isabelle_path,
            "--session", self.session,
            "--dir", self.afp_thys_dir,
            "--port", str(self.port),
            "--server-only"
        ]

        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)

        # Wait for TCP port to open
        t0 = time.time()
        connected = False
        while time.time() - t0 < 60:
            try:
                s = socket.socket()
                s.settimeout(2.0)
                s.connect(("127.0.0.1", self.port))
                s.close()
                connected = True
                break
            except Exception:
                time.sleep(0.5)

        if not connected:
            if self.proc.poll() is not None:
                out = self.proc.stdout.read() if self.proc.stdout else ""
                raise RuntimeError(f"REPL process died on startup:\n{out}")
            self.proc.terminate()
            raise TimeoutError(f"REPL port {self.port} did not become available in 60s.")

        time.sleep(2.0)
        self.client = EphemeralReplClient(host="127.0.0.1", port=self.port, token=self.token)

        # Configure un-truncated command spans (retry if initializing)
        for _ in range(10):
            try:
                self.client.send(
                    "Ir.config (fn cfg => {color = #color cfg, show_ignored = #show_ignored cfg, "
                    "full_spans = true, show_theory_in_source = #show_theory_in_source cfg, "
                    "auto_replay = #auto_replay cfg});"
                )
                break
            except Exception:
                time.sleep(1.0)

        print(f"[REPL] Session '{self.session}' ready in {time.time() - t0:.2f}s.")
        return self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.proc:
            print(f"[REPL] Terminating REPL daemon for session '{self.session}'...")
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()


def benchmark_theories(
    client: EphemeralReplClient,
    session: str,
    theories: list[str],
    metadata_parser: AFPMetadataParser
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Process a list of theories in a session, recording fine-grained benchmarks."""
    theory_stats = []
    all_records = []

    for theory in theories:
        t_start = time.perf_counter()

        # Step 1: Fetch raw source and source map via TCP socket
        t_fetch_0 = time.perf_counter()
        raw_source = client.send(f'Ir.source "{theory}" 0 ~1;')
        raw_map = client.send(f'Ir.source_map "{theory}" 0 ~1;')
        t_fetch = time.perf_counter() - t_fetch_0

        if not raw_source.strip():
            print(f"  [SKIP] No command spans in session database for {theory}")
            continue

        # Step 2: Parse source segments and map
        t_parse_0 = time.perf_counter()
        segments = parse_source_segments(raw_source)

        seg_map = {}
        for line in raw_map.splitlines():
            m = re.match(r'\s*(\d+)\s+(\S+)\s+(\d+)\s+(\d+)\s+(\S+)', line)
            if m:
                seg_map[int(m.group(1))] = {
                    "keyword": m.group(2),
                    "line": int(m.group(3)),
                    "offset": int(m.group(4)),
                    "file": m.group(5).strip(),
                    "theory": theory
                }

        lemmas = group_segments_to_lemmas(seg_map, segments)
        t_parse = time.perf_counter() - t_parse_0

        # Step 3: Resolve metadata
        entry_name = theory.split('.')[0] if '.' in theory else theory
        entry_meta = metadata_parser.load_entry_metadata(entry_name)
        pub_year = None
        date_str = entry_meta.get("date", "")
        if date_str:
            try:
                parts = date_str.split("-")
                if parts and parts[0].isdigit():
                    pub_year = int(parts[0])
            except Exception:
                pass

        # Step 4: Extract aspects for each lemma
        t_aspects_0 = time.perf_counter()
        theory_records = []
        isar_count = 0
        tactic_count = 0
        def_count = 0
        lemma_count = 0

        DEF_KEYWORDS = {
            "definition", "fun", "primrec", "function", "datatype", "type_synonym",
            "inductive", "coinductive", "record", "abbreviation"
        }
        LEMMA_KEYWORDS = {"lemma", "theorem", "corollary", "proposition", "schematic_goal"}

        for lemma in lemmas:
            aspects = extract_aspects(lemma, text_comments=lemma.get("text_comments", []))
            kw = lemma.get("keyword", "")

            if kw in DEF_KEYWORDS:
                def_count += 1
            elif kw in LEMMA_KEYWORDS:
                lemma_count += 1

            # Check if proof uses structured Isar or tactic style
            proof_txt = lemma.get("proof_text", "")
            if any(k in proof_txt for k in ["proof", "qed", "have ", "show ", "also", "finally", "next"]):
                isar_count += 1
            elif any(k in proof_txt for k in ["by ", "apply "]):
                tactic_count += 1

            rec = {
                "title": lemma["id"],
                "session": session,
                "theory": lemma["theory"],
                "keyword": lemma["keyword"],
                "problem": aspects["aspect_statement"],
                "method": aspects["aspect_strategy"],
                "finding": aspects["aspect_dependencies"],
                "interpretation": aspects["aspect_context"],
                "proof_text": lemma["proof_text"],
                "statement_text": lemma["statement_text"],
                "cited_deps": _extract_dependencies(lemma["proof_text"]),
                "dependents": "none",
                "file": lemma["file"],
                "line": lemma["line"],
                "publication_year": pub_year,
            }
            theory_records.append(rec)
            all_records.append(rec)

        t_aspects = time.perf_counter() - t_aspects_0
        t_total = time.perf_counter() - t_start

        stat = {
            "session": session,
            "theory": theory,
            "segments_count": len(segments),
            "units_count": len(lemmas),
            "lemmas_count": lemma_count,
            "definitions_count": def_count,
            "isar_proofs_count": isar_count,
            "tactic_proofs_count": tactic_count,
            "t_fetch_sec": round(t_fetch, 4),
            "t_parse_sec": round(t_parse, 4),
            "t_aspects_sec": round(t_aspects, 4),
            "t_total_sec": round(t_total, 4),
        }
        theory_stats.append(stat)

        print(
            f"  [Processed] {theory:<40} | Units: {len(lemmas):>3} "
            f"(Lemmas: {lemma_count:>3}, Defs: {def_count:>2}, Isar: {isar_count:>2}) | "
            f"Time: {t_total*1000:>6.1f}ms (fetch: {t_fetch*1000:>5.1f}ms, parse: {t_parse*1000:>4.1f}ms, aspects: {t_aspects*1000:>4.1f}ms)"
        )

    return theory_stats, all_records


def main():
    parser = argparse.ArgumentParser(description="Isabelle Session Segmentation Benchmarking")
    parser.add_argument("--isabelle", default="/home/jmena/Isabelle2025-2/bin/isabelle", help="Path to isabelle binary")
    parser.add_argument("--afp-dir", default="/home/jmena/lcorreia/eel/external/afp-2025-2/thys", help="Path to AFP thys/")
    parser.add_argument("--output-dir", default="artifacts/segmentation_benchmarks", help="Output directory")
    parser.add_argument("--sessions", nargs="+", default=["HOL-Library", "AVL-Trees", "Aho_Corasick", "Featherweight_OCL"], help="Sessions to benchmark")
    parser.add_argument("--max-theories-per-session", type=int, default=15, help="Max theories to benchmark per session (0 = all)")
    args = parser.parse_args()

    out_path = Path(args.output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    metadata_parser = AFPMetadataParser()

    all_benchmarks = []
    all_extracted_records = []

    print("=" * 80)
    print("ISABELLE / LANDSCAPE (I/L) SEGMENTATION BENCHMARKING")
    print(f"Target Sessions: {args.sessions}")
    print("=" * 80)

    t_global_start = time.time()

    for session in args.sessions:
        print(f"\n>>> Benchmarking Session: {session}")
        try:
            with SessionReplContext(args.isabelle, args.afp_dir, session, port=9151) as client:
                raw_theories = client.send("Ir.theories ();")
                all_thys = [t.strip() for t in raw_theories.splitlines() if t.strip()]

                # Filter session-specific theories
                if session == "HOL-Library":
                    session_thys = [t for t in all_thys if t.startswith("HOL-Library.")]
                elif session == "AVL-Trees":
                    session_thys = [t for t in all_thys if t.startswith("AVL-Trees.") or "AVL" in t]
                elif session == "Aho_Corasick":
                    session_thys = [t for t in all_thys if t.startswith("Aho_Corasick.") or t.startswith("Trie.")]
                elif session == "Featherweight_OCL":
                    session_thys = [t for t in all_thys if t.startswith("Featherweight_OCL.")]
                else:
                    session_thys = [t for t in all_thys if t.startswith(f"{session}.")]

                # Prioritize key demo theories if present
                priority = ["Multiset", "Tree", "Big_O", "AVL_Tree", "Aho_Corasick", "Core_init"]
                sorted_thys = []
                for p in priority:
                    for t in session_thys:
                        if p in t and t not in sorted_thys:
                            sorted_thys.append(t)
                for t in session_thys:
                    if t not in sorted_thys:
                        sorted_thys.append(t)

                if args.max_theories_per_session > 0:
                    sorted_thys = sorted_thys[:args.max_theories_per_session]

                print(f"Selected {len(sorted_thys)} theories for session '{session}':")
                for st in sorted_thys[:6]:
                    print(f"  - {st}")
                if len(sorted_thys) > 6:
                    print(f"  ... and {len(sorted_thys)-6} more.")

                stats, records = benchmark_theories(client, session, sorted_thys, metadata_parser)
                all_benchmarks.extend(stats)
                all_extracted_records.extend(records)

        except Exception as e:
            print(f"[ERROR] Failed to process session '{session}': {e}")

    # Post-process definition dependencies
    t_dep_0 = time.perf_counter()
    compute_definition_dependencies(all_extracted_records)
    t_dep = time.perf_counter() - t_dep_0

    total_time = time.time() - t_global_start

    # Save benchmark dataframe
    df_bench = pd.DataFrame(all_benchmarks)
    bench_file = out_path / "benchmarks.parquet"
    bench_json = out_path / "benchmarks.json"
    df_bench.to_parquet(bench_file, index=False)
    with open(bench_json, "w") as f:
        json.dump(all_benchmarks, f, indent=2)

    # Save extracted lemma records
    df_records = pd.DataFrame(all_extracted_records)
    records_file = out_path / "extracted_lemmas.parquet"
    df_records.to_parquet(records_file, index=False)

    # Save qualitative samples (Markdown)
    sample_md_file = out_path / "qualitative_segmentation_samples.md"
    with open(sample_md_file, "w") as f:
        f.write("# I/L Qualitative Segmentation Analysis Samples\n\n")
        f.write("This document showcases real Isabelle lemmas and definitions extracted and partitioned into the four epistemic aspects:\n\n")

        # Select diverse samples: 2 from Multiset, 2 from AVL, 2 from Aho_Corasick, 2 from Featherweight_OCL
        sample_sessions = ["HOL-Library", "AVL-Trees", "Aho_Corasick", "Featherweight_OCL"]
        for s in sample_sessions:
            s_recs = [r for r in all_extracted_records if r["session"] == s]
            # Pick one with Isar proof, one definition
            isar_recs = [r for r in s_recs if "proof" in r.get("proof_text", "") and len(r.get("method", "")) > 40]
            def_recs = [r for r in s_recs if r.get("keyword") in ["definition", "fun", "primrec"]]

            f.write(f"## Session: `{s}`\n\n")

            if def_recs:
                d = def_recs[0]
                f.write(f"### [Definition] `{d['title']}` ({d['theory']})\n\n")
                f.write(f"- **Keyword:** `{d['keyword']}`\n")
                f.write(f"- **Location:** `{d['file']}:{d['line']}`\n")
                f.write(f"- **Dependents (Lemmas that cite this):** {d.get('dependents', 'none')}\n\n")
                f.write("```isabelle\n" + d["statement_text"].strip() + "\n```\n\n")

            if isar_recs:
                l = isar_recs[0]
                f.write(f"### [Isar Lemma] `{l['title']}` ({l['theory']})\n\n")
                f.write(f"- **Keyword:** `{l['keyword']}`\n")
                f.write(f"- **Location:** `{l['file']}:{l['line']}`\n\n")
                f.write("#### Aspect 1: Problem (Formal Statement)\n")
                f.write("```isabelle\n" + l["problem"].strip() + "\n```\n\n")
                f.write("#### Aspect 2: Method (Isar Proof Skeleton & Deductive Steps)\n")
                f.write("```isabelle\n" + l["method"].strip() + "\n```\n\n")
                f.write("#### Aspect 3: Finding (Dependencies & Operational Tactics)\n")
                f.write(f"- **Cited Dependencies:** `{l['cited_deps']}`\n")
                f.write("```isabelle\n" + l["finding"].strip() + "\n```\n\n")
                if l["interpretation"]:
                    f.write("#### Aspect 4: Interpretation (Context & Narrative Comments)\n")
                    f.write(f"> {l['interpretation']}\n\n")
                f.write("---\n\n")

    # Generate Statistical Summary & Extrapolation
    total_theories = len(df_bench)
    total_units = df_bench["units_count"].sum()
    total_lemmas = df_bench["lemmas_count"].sum()
    total_defs = df_bench["definitions_count"].sum()
    total_isar = df_bench["isar_proofs_count"].sum()
    total_tactic = df_bench["tactic_proofs_count"].sum()

    avg_time_per_thy = df_bench["t_total_sec"].mean()
    med_time_per_thy = df_bench["t_total_sec"].median()
    avg_time_per_unit = (df_bench["t_total_sec"].sum() / total_units) * 1000 if total_units > 0 else 0

    # AFP Extrapolation: 1,098 sessions in AFP 2025-2
    # Empirical average theories per session ~6.5 to 7 (estimated ~7,200 total theories)
    ESTIMATED_AFP_THEORIES = 7200
    est_total_afp_seconds = ESTIMATED_AFP_THEORIES * avg_time_per_thy
    est_total_afp_hours = est_total_afp_seconds / 3600

    summary_md_file = out_path / "summary_report.md"
    with open(summary_md_file, "w") as f:
        f.write("# I/L Segmentation Benchmark & AFP Extrapolation Report\n\n")
        f.write(f"- **Machine:** IME USP `deeptwelve` (64 CPU cores, 251 GB RAM)\n")
        f.write(f"- **Total Sessions Evaluated:** {len(args.sessions)}\n")
        f.write(f"- **Total Theories Processed:** {total_theories}\n")
        f.write(f"- **Total Units Extracted:** {total_units} ({total_lemmas} lemmas, {total_defs} definitions)\n")
        f.write(f"- **Proof Styles:** {total_isar} structured Isar proofs, {total_tactic} tactic-style proofs\n\n")
        f.write("## Timing & Throughput Benchmarks\n\n")
        f.write(f"- **Average Time per Theory:** {avg_time_per_thy*1000:.1f} ms\n")
        f.write(f"- **Median Time per Theory:** {med_time_per_thy*1000:.1f} ms\n")
        f.write(f"- **Average Time per Lemma/Unit:** {avg_time_per_unit:.2f} ms\n")
        f.write(f"- **Extraction Throughput:** {total_theories / df_bench['t_total_sec'].sum():.1f} theories/sec (~{total_units / df_bench['t_total_sec'].sum():.1f} lemmas/sec)\n\n")
        f.write("## Extrapolation to the Entire Archive of Formal Proofs (AFP)\n\n")
        f.write(f"- **Total AFP Sessions:** 1,098 sessions\n")
        f.write(f"- **Estimated Total Theories in AFP:** ~{ESTIMATED_AFP_THEORIES:,} theories\n")
        f.write(f"- **Estimated Pure Extraction Wall-Clock Time:** **{est_total_afp_seconds:.1f} seconds (~{est_total_afp_hours:.2f} hours / ~{est_total_afp_hours*60:.1f} minutes)**\n\n")
        f.write("### Breakdown by Session\n\n")
        f.write("| Session | Theories | Total Units | Lemmas | Defs | Isar Proofs | Mean Time/Theory (ms) |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for s, group in df_bench.groupby("session"):
            f.write(
                f"| `{s}` | {len(group)} | {group['units_count'].sum()} | "
                f"{group['lemmas_count'].sum()} | {group['definitions_count'].sum()} | "
                f"{group['isar_proofs_count'].sum()} | {group['t_total_sec'].mean()*1000:.1f} ms |\n"
            )

    print("\n" + "=" * 80)
    print("BENCHMARK SUMMARY RESULTS")
    print(f"Total Theories Processed: {total_theories}")
    print(f"Total Units Ingested:     {total_units} ({total_lemmas} lemmas, {total_defs} definitions)")
    print(f"Isar vs Tactic Proofs:    {total_isar} Isar / {total_tactic} Tactic")
    print(f"Average Time / Theory:    {avg_time_per_thy*1000:.1f} ms")
    print(f"Throughput:               {total_theories / df_bench['t_total_sec'].sum():.1f} theories/sec ({total_units / df_bench['t_total_sec'].sum():.1f} lemmas/sec)")
    print(f"Estimated Whole AFP Time: {est_total_afp_hours*60:.1f} minutes ({est_total_afp_hours:.2f} hours)")
    print("=" * 80)
    print(f"Reports saved in: {out_path}")


if __name__ == "__main__":
    main()
