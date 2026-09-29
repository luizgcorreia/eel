"""Construct a stratified Pure AFP Deep Structural Reasoning benchmark suite (20 theorems)."""

from __future__ import annotations

from pathlib import Path
import random
import pandas as pd

from edel.il.eval_dataset import (
    apply_isomorphic_perturbation,
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


def build_afp_deep_benchmark(
    extracted_path: Path,
    existing_bench_paths: list[Path],
    output_path: Path,
    target_count: int = 20,
    perturbed_ratio: float = 0.30,
    seed: int = 42,
) -> list[dict]:
    random.seed(seed)

    df_extracted = pd.read_parquet(extracted_path)
    
    existing_titles = set()
    for bp in existing_bench_paths:
        if bp.exists():
            df_b = pd.read_parquet(bp)
            existing_titles.update(df_b["title"].unique())

    # Filter for deep candidates strictly from AFP sessions, excluding existing benchmark theorems
    candidates = []
    afp_sessions = {"AVL-Trees", "Featherweight_OCL", "Aho_Corasick"}
    for _, row in df_extracted.iterrows():
        title = str(row.get("title", ""))
        session = str(row.get("session", ""))
        theory = str(row.get("theory", ""))
        
        if title in existing_titles:
            continue
        if session not in afp_sessions or theory.startswith("HOL-Library."):
            continue
        if not is_deep_structural_candidate(row):
            continue
        rec = row.to_dict()
        if is_trivial_goal(rec):
            continue
        candidates.append(rec)

    print(f"Found {len(candidates)} valid candidate AFP deep structural theorems.")

    # Group by theory to ensure diverse stratification
    by_theory: dict[str, list[dict]] = {}
    for c in candidates:
        th = c["theory"]
        by_theory.setdefault(th, []).append(c)

    print("Candidates by theory:")
    for th, lst in sorted(by_theory.items()):
        print(f"  {th}: {len(lst)}")

    # Sort and shuffle deterministically
    theories = sorted(by_theory.keys())
    for th in theories:
        random.shuffle(by_theory[th])

    selected: list[dict] = []
    # Stratified round-robin selection across theories
    idx = 0
    while len(selected) < target_count and any(by_theory.values()):
        th = theories[idx % len(theories)]
        if by_theory[th]:
            selected.append(by_theory[th].pop(0))
        idx += 1

    print(f"\nSelected {len(selected)} deep structural theorems across {len(set(s['theory'] for s in selected))} AFP theories.")

    # Mark tier and apply perturbations to 30% of lemmas
    n_perturbed = int(round(len(selected) * perturbed_ratio))
    pert_indices = set(random.sample(range(len(selected)), n_perturbed))

    final_suite: list[dict] = []
    for i, item in enumerate(selected):
        item["difficulty_tier"] = "tier_4_deep_structural_afp"
        if i in pert_indices:
            item = apply_isomorphic_perturbation(item)
        else:
            item["is_perturbed"] = False
        
        lines = str(item.get("proof_text", "")).count("\n") + 1
        pert_mark = " [PERTURBED]" if item["is_perturbed"] else ""
        print(f"[{i+1:02d}] {item['theory']:30s} | {item['title']:45s} | {lines:3d} lines{pert_mark}")
        final_suite.append(item)

    df_out = pd.DataFrame(final_suite)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_parquet(output_path, index=False)
    print(f"\nSaved {len(df_out)} AFP deep theorems to {output_path}")
    return final_suite


if __name__ == "__main__":
    extracted = Path("artifacts/segmentation_benchmarks/extracted_lemmas.parquet")
    existing_100 = Path("artifacts/experiment_benchmarks/stratified_100_lemmas.parquet")
    existing_deep = Path("artifacts/experiment_benchmarks/deep_structural_20_lemmas.parquet")
    out = Path("artifacts/experiment_benchmarks/afp_deep_structural_20_lemmas.parquet")
    build_afp_deep_benchmark(extracted, [existing_100, existing_deep], out)
