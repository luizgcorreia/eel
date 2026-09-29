#!/usr/bin/env python3
"""Generate real Voyage AI dense embeddings for Control Flat RAG and Treatment EEL indices.

Embeds the full 1,924 extracted lemma corpus from:
  artifacts/segmentation_benchmarks/extracted_lemmas.parquet

Output:
1. Control Flat RAG (artifacts/flat_rag_index/):
   - metadata.parquet (1,924 records with monolithic_text)
   - embeddings.npz (shape: (1924, 1024))
2. Treatment EEL Landscape (artifacts/rag_index/):
   - metadata.parquet (1,924 records with 4 aspects, step maps, rule classifications)
   - embeddings.npz (keys: 'problem', 'method', 'finding', 'interpretation', each shape: (1924, 1024))
   - landscape heights and dependents counts computed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv
from tqdm import tqdm

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

load_dotenv(REPO_ROOT / ".env")

from edel.il.compute_landscape_height import compute_and_save_landscape_height
from edel.il.flat_index import FlatRAGIndex, format_monolithic_text
from edel.il.index import NumpyRAGIndex


def embed_texts_in_batches(
    texts: list[str],
    api_key: str,
    model: str = "voyage-code-3",
    batch_size: int = 64,
    desc: str = "Embedding",
) -> np.ndarray:
    """Send text batches to Voyage AI with exponential backoff and rate limit handling."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    url = "https://api.voyageai.com/v1/embeddings"

    embeddings_list: list[list[float]] = []
    total_texts = len(texts)

    with tqdm(total=total_texts, desc=desc) as pbar:
        for i in range(0, total_texts, batch_size):
            batch = texts[i : i + batch_size]
            # Replace empty or pure whitespace strings with fallback token
            clean_batch = [t if t and t.strip() else "<empty>" for t in batch]

            payload = {
                "input": clean_batch,
                "model": model,
                "input_type": "document",
            }

            max_retries = 5
            for attempt in range(max_retries):
                try:
                    resp = requests.post(url, headers=headers, json=payload, timeout=60)
                    if resp.status_code == 200:
                        data = resp.json()
                        for item in data["data"]:
                            embeddings_list.append(item["embedding"])
                        pbar.update(len(batch))
                        time.sleep(0.15)  # Gentle pacing
                        break
                    elif resp.status_code == 429:
                        wait = 2 ** (attempt + 1)
                        print(f"\n[Rate Limit] 429 Too Many Requests. Retrying in {wait}s...")
                        time.sleep(wait)
                    else:
                        raise RuntimeError(f"Voyage API error ({resp.status_code}): {resp.text}")
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise RuntimeError(f"Failed to embed batch {i}..{i+len(batch)} after {max_retries} attempts: {e}")
                    time.sleep(2 ** (attempt + 1))

    return np.array(embeddings_list, dtype=np.float32)


def main():
    parser = argparse.ArgumentParser(description="Embed evaluation indices using Voyage AI.")
    parser.add_argument(
        "--source-parquet",
        default="artifacts/segmentation_benchmarks/extracted_lemmas.parquet",
        help="Path to full extracted lemmas dataframe.",
    )
    parser.add_argument(
        "--flat-output",
        default="artifacts/flat_rag_index",
        help="Output directory for Flat RAG index.",
    )
    parser.add_argument(
        "--il-output",
        default="artifacts/rag_index",
        help="Output directory for Treatment I/L index.",
    )
    parser.add_argument(
        "--model",
        default="voyage-code-3",
        help="Voyage embedding model (default: voyage-code-3).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Batch size for Voyage embedding requests (default: 64).",
    )
    parser.add_argument(
        "--skip-flat",
        action="store_true",
        help="Skip embedding the Flat RAG index.",
    )
    parser.add_argument(
        "--skip-il",
        action="store_true",
        help="Skip embedding the Treatment I/L index.",
    )
    args = parser.parse_args()

    api_key = os.getenv("VOYAGE_API_KEY", "")
    if not api_key:
        print("Error: VOYAGE_API_KEY not found in .env or environment.")
        sys.exit(1)

    src_path = Path(args.source_parquet)
    if not src_path.exists():
        print(f"Error: Source parquet not found: {src_path}")
        sys.exit(1)

    print(f"Loading extracted formal units from {src_path}...")
    df = pd.read_parquet(src_path)
    n_records = len(df)
    print(f"Loaded {n_records} formal units across {df['theory'].nunique()} theories.")

    # -----------------------------------------------------------------------
    # 1. Control Monolithic Flat RAG Index
    # -----------------------------------------------------------------------
    if not args.skip_flat:
        print("\n=======================================================")
        print("1. Embedding Control Flat RAG Index (Monolithic Text)")
        print("=======================================================")
        flat_dir = Path(args.flat_output)
        flat_dir.mkdir(parents=True, exist_ok=True)

        records = df.to_dict(orient="records")
        monolithic_texts = [format_monolithic_text(r) for r in records]

        print(f"Generating {len(monolithic_texts)} monolithic embeddings with {args.model}...")
        flat_embeddings = embed_texts_in_batches(
            monolithic_texts,
            api_key=api_key,
            model=args.model,
            batch_size=args.batch_size,
            desc="Flat RAG Monolithic",
        )

        flat_index = FlatRAGIndex()
        flat_index.build_from_dataframe(df, embeddings=flat_embeddings)
        flat_index.save(flat_dir)
        print(f"Control Flat RAG index successfully saved to {flat_dir} (embeddings shape: {flat_embeddings.shape})")

    # -----------------------------------------------------------------------
    # 2. Treatment I/L Epistemic Landscape Index (4 Aspects)
    # -----------------------------------------------------------------------
    if not args.skip_il:
        print("\n=======================================================")
        print("2. Embedding Treatment I/L Epistemic Landscape Index (4 Aspects)")
        print("=======================================================")
        il_dir = Path(args.il_output)
        il_dir.mkdir(parents=True, exist_ok=True)

        aspect_embeddings: dict[str, np.ndarray] = {}
        aspects = ["problem", "method", "finding", "interpretation"]

        for aspect in aspects:
            texts = df[aspect].fillna("").astype(str).tolist()
            print(f"\nGenerating {len(texts)} embeddings for Aspect: '{aspect}'...")
            emb_arr = embed_texts_in_batches(
                texts,
                api_key=api_key,
                model=args.model,
                batch_size=args.batch_size,
                desc=f"Aspect [{aspect}]",
            )
            aspect_embeddings[aspect] = emb_arr

        # Save metadata parquet (exclude raw embeddings column if present)
        meta_cols = [c for c in df.columns if not c.endswith("_embedding")]
        df[meta_cols].to_parquet(il_dir / "metadata.parquet", index=False)

        # Save multi-aspect compressed embeddings array
        np.savez_compressed(il_dir / "embeddings.npz", **aspect_embeddings)
        print(f"Treatment I/L embeddings saved to {il_dir / 'embeddings.npz'}")

        # Compute topological landscape heights & dependents
        print("\nComputing topological landscape heights across dependency network...")
        compute_and_save_landscape_height(il_dir)
        print(f"Treatment I/L Index successfully constructed and saved to {il_dir}")

    print("\n=======================================================")
    print("All indices embedded and saved successfully!")
    print(f"Control Flat Index: {args.flat_output}")
    print(f"Treatment I/L Index: {args.il_output}")
    print("=======================================================")


if __name__ == "__main__":
    main()
