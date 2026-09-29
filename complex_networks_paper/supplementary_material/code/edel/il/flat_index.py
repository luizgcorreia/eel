"""Control Monolithic RAG Vector Index for Isabelle/AFP lemmas.

Implements the standard baseline RAG representation where each theorem
and its proof are stored and embedded as a single monolithic text chunk.
Includes strict anti-contamination and temporal/file-precedence masking.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def format_monolithic_text(record: dict[str, Any]) -> str:
    """Format a theorem record into a standard monolithic text chunk."""
    theory = record.get("theory", "")
    title = record.get("title", "")
    statement = record.get("statement_text", "").strip()
    proof = record.get("proof_text", "").strip()
    return f"Theory: {theory}\nLemma: {title}\nStatement:\n{statement}\nProof:\n{proof}"


class FlatRAGIndex:
    """Numpy-based dense vector index for monolithic theorem text chunks (Control RAG)."""

    def __init__(self):
        self.metadata: list[dict[str, Any]] = []
        self.embeddings: np.ndarray | None = None

    def build_from_dataframe(
        self,
        df: pd.DataFrame,
        embeddings: np.ndarray | list[list[float]] | None = None,
        embedding_column: str = "embedding"
    ):
        """Build the index from a dataframe of extracted lemma records."""
        records = df.to_dict(orient="records")
        for rec in records:
            if "monolithic_text" not in rec:
                rec["monolithic_text"] = format_monolithic_text(rec)

        self.metadata = records

        if embeddings is not None:
            self.embeddings = np.array(embeddings, dtype=np.float32)
        elif embedding_column in df.columns:
            embs = []
            for val in df[embedding_column]:
                if isinstance(val, str):
                    embs.append(json.loads(val))
                else:
                    embs.append(val)
            self.embeddings = np.array(embs, dtype=np.float32)
        else:
            self.embeddings = None

    def save(self, directory: str | Path):
        """Save the control index to disk."""
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        meta_df = pd.DataFrame(self.metadata)
        # Avoid storing raw embeddings inside the parquet dataframe
        if "embedding" in meta_df.columns:
            meta_df = meta_df.drop(columns=["embedding"])
        meta_df.to_parquet(directory / "metadata.parquet", index=False)

        if self.embeddings is not None:
            np.savez_compressed(directory / "embeddings.npz", embeddings=self.embeddings)

        print(f"Saved FlatRAGIndex to {directory} ({len(self.metadata)} items)")

    def load(self, directory: str | Path):
        """Load the control index from disk."""
        directory = Path(directory)
        meta_path = directory / "metadata.parquet"
        emb_path = directory / "embeddings.npz"

        if not meta_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {meta_path}")

        meta_df = pd.read_parquet(meta_path)
        self.metadata = meta_df.to_dict(orient="records")

        if emb_path.exists():
            with np.load(emb_path) as data:
                self.embeddings = data["embeddings"]
        else:
            self.embeddings = None

        print(f"Loaded FlatRAGIndex from {directory} ({len(self.metadata)} items)")

    def search(
        self,
        query_vector: list[float] | np.ndarray,
        top_k: int = 3,
        exclude_titles: list[str] | set[str] | None = None,
        max_line: int | None = None,
        theory: str | None = None,
        exclude_definitions: bool = False,
    ) -> list[dict[str, Any]]:
        """Search the monolithic index by cosine similarity with anti-contamination masking.

        Args:
            query_vector: Dense embedding vector for the query.
            top_k: Number of nearest items to return.
            exclude_titles: Set of lemma titles to exclude (self-masking).
            max_line: If set with `theory`, excludes lemmas defined at or after this line.
            theory: Target theory file for temporal/precedence masking.
            exclude_definitions: Whether to omit definitions from results.
        """
        if self.embeddings is None or len(self.embeddings) == 0:
            return []

        q = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q)
        if q_norm > 1e-10:
            q = q / q_norm

        norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        norms[norms < 1e-10] = 1.0
        norm_matrix = self.embeddings / norms
        scores = norm_matrix @ q

        exclude_set = set(exclude_titles or [])
        DEF_KEYWORDS = {
            "definition", "fun", "primrec", "function", "datatype", "type_synonym",
            "inductive", "coinductive", "record", "abbreviation"
        }

        candidates = []
        for idx, score in enumerate(scores):
            meta = self.metadata[idx]
            title = meta.get("title", "")

            # 1. Self-masking
            if title in exclude_set:
                continue

            # 2. Temporal & File-Precedence Masking
            if theory and max_line is not None:
                meta_theory = meta.get("theory", "")
                meta_line = meta.get("line", 0)
                if meta_theory == theory and meta_line >= max_line:
                    continue

            # 3. Optional Definition Filtering
            if exclude_definitions and meta.get("keyword") in DEF_KEYWORDS:
                continue

            candidates.append({
                "title": title,
                "theory": meta.get("theory", ""),
                "keyword": meta.get("keyword", "lemma"),
                "score": float(score),
                "statement_text": meta.get("statement_text", ""),
                "proof_text": meta.get("proof_text", ""),
                "monolithic_text": meta.get("monolithic_text", format_monolithic_text(meta)),
                "file": meta.get("file", ""),
                "line": meta.get("line", 0),
            })

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:top_k]
