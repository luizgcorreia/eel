"""Construct a stratified Tier 4: Deep Structural Reasoning benchmark suite."""

from __future__ import annotations

import json
from pathlib import Path
import random
import pandas as pd

from edel.il.eval_dataset import (
    apply_isomorphic_perturbation,
    compute_dependency_closure,
    is_trivial_goal,
)

ISAR_KEYWORDS = ["proof", "have ", "show ", "fix ", "obtain ", "qed"]


def is_deep_structural_candidate(row: pd.Series) -> bool:
    proof = str(row.get("proof_text", "")).strip()
    cited = str(row.get("cited_deps", "")).strip()
    lines = str(proof).count("\n") + 1

    if lines < 10:
        return False
    if not any(k in proof for k in ISAR_KEYWORDS):
        return False
    if not cited or cited in ["none", "set()"]:
        return False
    if proof.startswith("by ") or proof.startswith("apply "):
        return False
    return True


def build_deep_benchmark(
    extracted_path: Path,
    existing_bench_path: Path,
    output_path: Path,
    target_count: int = 20,
    perturbed_ratio: float = 0.30,
    seed: int = 42,
) -> list[dict]:
    random.seed(seed)

    df_extracted = pd.read_parquet(extracted_path)
    df_existing = pd.read_parquet(existing_bench_path)

    existing_titles = set(df_existing["title"].unique())
    active_theories = set(df_existing["theory"].unique())

    # Filter for deep candidates in verified theories, excluding existing benchmark theorems
    candidates = []
    for _, row in df_extracted.iterrows():
        title = str(row.get("title", ""))
        theory = str(row.get("theory", ""))
        if title in existing_titles:
            continue
        if not theory.startswith("HOL-Library."):
            continue
        if not is_deep_structural_candidate(row):
            continue
        rec = row.to_dict()
        if is_trivial_goal(rec):
            continue
        candidates.append(rec)

    print(f"Found {len(candidates)} valid candidate deep structural theorems.")

    # Group by theory to ensure diverse stratification
    by_theory: dict[str, list[dict]] = {}
    for c in candidates:
        th = c["theory"]
        by_theory.setdefault(th, []).append(c)

    selected: list[dict] = []
    # Stratified round-robin selection across theories
    theories = sorted(by_theory.keys())
    for th in theories:
        random.shuffle(by_theory[th])

    idx = 0
    while len(selected) < target_count and any(by_theory.values()):
        th = theories[idx % len(theories)]
        if by_theory[th]:
            selected.append(by_theory[th].pop(0))
        idx += 1

    print(f"Selected {len(selected)} deep structural theorems.")

    # Mark tier and apply perturbations to 30% of lemmas
    n_perturbed = int(round(len(selected) * perturbed_ratio))
    pert_indices = set(random.sample(range(len(selected)), n_perturbed))

    final_suite: list[dict] = []
    for i, item in enumerate(selected):
        item["difficulty_tier"] = "tier_4_deep_structural"
        if i in pert_indices:
            item = apply_isomorphic_perturbation(item)
        else:
            item["is_perturbed"] = False
        final_suite.append(item)

    df_out = pd.DataFrame(final_suite)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_parquet(output_path, index=False)
    print(f"Saved {len(final_suite)} deep benchmark theorems to {output_path}")

    return final_suite


if __name__ == "__main__":
    extracted = Path("artifacts/segmentation_benchmarks/extracted_lemmas.parquet")
    existing = Path("artifacts/experiment_benchmarks/stratified_100_lemmas.parquet")
    output = Path("artifacts/experiment_benchmarks/deep_structural_20_lemmas.parquet")
    suite = build_deep_benchmark(extracted, existing, output, target_count=20, perturbed_ratio=0.30)
    for i, s in enumerate(suite, 1):
        pert = " [PERTURBED]" if s["is_perturbed"] else ""
        lines = str(s["proof_text"]).count("\n") + 1
        print(f"[{i:2d}] {s['theory']} | {s['title'].split('.')[-1]} (lines: {lines}){pert}")
