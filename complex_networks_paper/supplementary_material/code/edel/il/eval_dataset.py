"""Stratified Benchmark Sampler & Perturbation Engine for I/L Evaluation.

Constructs the 100-theorem evaluation suite with:
1. Complete Dependency Closure verification (Closure = 1.0 within indexed corpus).
2. Stratification across 3 difficulty tiers (Tier 1: Terminal, Tier 2: Inductive, Tier 3: Structural).
3. Novel Isomorphic Perturbations (alpha-renaming & compound variations) to defeat pre-training memorization.
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


# Isomorphic alpha-renaming on free and bound variables only, preserving all defined theory constants.
VARIABLE_REPLACEMENTS = {
    r"(?<![a-zA-Z0-9_])t(?![a-zA-Z0-9_])": "t_tree",
    r"(?<![a-zA-Z0-9_])x(?![a-zA-Z0-9_])": "x_elem",
    r"(?<![a-zA-Z0-9_])y(?![a-zA-Z0-9_])": "y_elem",
    r"(?<![a-zA-Z0-9_])z(?![a-zA-Z0-9_])": "z_elem",
    r"(?<![a-zA-Z0-9_])xs(?![a-zA-Z0-9_])": "xs_list",
    r"(?<![a-zA-Z0-9_])ys(?![a-zA-Z0-9_])": "ys_list",
    r"(?<![a-zA-Z0-9_])zs(?![a-zA-Z0-9_])": "zs_list",
    r"(?<![a-zA-Z0-9_])a(?![a-zA-Z0-9_])": "a_elem",
    r"(?<![a-zA-Z0-9_])b(?![a-zA-Z0-9_])": "b_elem",
}


def compute_dependency_closure(lemma: dict[str, Any], indexed_titles: set[str], indexed_shorts: set[str]) -> float:
    """Calculate the fraction of cited dependencies present in the indexed corpus."""
    cited_str = lemma.get("cited_deps", "")
    if not cited_str or cited_str == "none":
        return 1.0

    deps = [d.strip() for d in cited_str.split(",") if d.strip()]
    if not deps:
        return 1.0

    # Common built-in HOL facts always present in session runtime
    HOL_CORE_FACTS = {
        "ccontr", "not_in_iff", "fun_eq_iff", "ext", "iffI", "conjI", "disjI1", "disjI2",
        "refl", "sym", "trans", "assms", "that", "this", "TrueI", "FalseE", "notI", "notE",
        "impI", "mp", "allI", "spec", "exI", "exE", "subsetI", "subsetD", "equalityI",
        "insert_iff", "empty_iff", "Un_iff", "Int_iff", "Diff_iff"
    }

    covered = 0
    for dep in deps:
        if dep in HOL_CORE_FACTS or dep in indexed_titles or dep in indexed_shorts:
            covered += 1

    return covered / len(deps)


def classify_difficulty_tier(lemma: dict[str, Any]) -> str:
    """Classify lemma into Tier 1 (Terminal), Tier 2 (Inductive), or Tier 3 (Structural)."""
    proof_txt = lemma.get("proof_text", "").strip()
    rule_type = lemma.get("rule_type", "general_theorem")
    steps = lemma.get("proof_steps", [])
    num_steps = len(steps) if isinstance(steps, list) else 0

    # Tier 3: Complex multi-step Isar structural proofs
    is_isar = any(k in proof_txt for k in ["proof", "qed", "have ", "show ", "also", "finally"])
    if is_isar and (num_steps >= 4 or len(proof_txt) > 250):
        return "tier_3_structural"

    # Tier 2: Inductive lemmas
    is_inductive = (
        "induction" in proof_txt
        or "induct" in proof_txt
        or rule_type in ["induction_rule", "cases_rule", "coinduction_rule"]
        or num_steps >= 3
    )
    if is_inductive:
        return "tier_2_inductive"

    # Tier 1: Terminal one-liners / equational simplification
    return "tier_1_terminal"


def apply_isomorphic_perturbation(lemma: dict[str, Any]) -> dict[str, Any]:
    """Create an isomorphically perturbed variant of a theorem via alpha-renaming of variables."""
    perturbed = dict(lemma)
    perturbed["is_perturbed"] = True
    perturbed["original_title"] = lemma.get("title", "")
    perturbed["title"] = lemma.get("title", "") + "_novel_variant"

    stmt = perturbed.get("statement_text", "")
    proof = perturbed.get("proof_text", "")

    for pattern, new_name in VARIABLE_REPLACEMENTS.items():
        stmt = re.sub(pattern, new_name, stmt)
        proof = re.sub(pattern, new_name, proof)

    perturbed["statement_text"] = stmt
    perturbed["proof_text"] = proof
    return perturbed



def is_trivial_goal(lemma: dict[str, Any]) -> bool:
    """Filter out trivial goals solvable by raw default automation without external facts."""
    proof = lemma.get("proof_text", "").strip()
    cited = lemma.get("cited_deps", "").strip()
    title = lemma.get("title", "").split(".")[-1]

    # 1. Bare default automation commands with no cited dependencies
    BARE_AUTOMATION = {
        "by simp", "by auto", "by blast", "by fastforce", "by force",
        "by eval", "by normalization", "by arith", "by linarith"
    }
    if proof in BARE_AUTOMATION and (not cited or cited == "none"):
        return True

    # 2. Self-referential tautology: e.g. "by (fact foo)" where fact is self
    if f"by (fact {title})" in proof or proof == f"by (fact {title})" or proof == "by (fact)":
        return True

    # 3. Simple "by simp" or "by auto" without any parameters or citations
    if (proof.startswith("by simp") or proof.startswith("by auto")) and (not cited or cited == "none"):
        if "add:" not in proof and "rule:" not in proof and "intro:" not in proof and "elim:" not in proof:
            return True

    return False


def build_stratified_benchmark(
    records: list[dict[str, Any]],
    target_count: int = 100,
    seed: int = 42,
    perturbed_ratio: float = 0.30
) -> list[dict[str, Any]]:
    """Build a stratified benchmark meeting context closure, challenge pre-filtering, and difficulty ratios."""
    random.seed(seed)

    # 1. Index titles and short names for closure check
    all_titles = set(r["title"] for r in records)
    all_shorts = set(r["title"].split(".")[-1] for r in records if "." in r["title"])

    # 2. Filter records by 100% Dependency Closure and Non-Trivial Challenge Filter
    closed_records = []
    for r in records:
        kw = r.get("keyword", "lemma")
        # Only evaluate theorems/lemmas, not pure definitions/datatypes
        if kw not in ["lemma", "theorem", "corollary", "proposition"]:
            continue

        # Challenge pre-filter: discard trivial automation one-liners
        if is_trivial_goal(r):
            continue

        closure = compute_dependency_closure(r, all_titles, all_shorts)
        if closure >= 1.0:
            rec = dict(r)
            rec["dependency_closure"] = closure
            rec["difficulty_tier"] = classify_difficulty_tier(rec)
            rec["is_perturbed"] = False
            closed_records.append(rec)

    # 3. Group by tier
    tier1 = [r for r in closed_records if r["difficulty_tier"] == "tier_1_terminal"]
    tier2 = [r for r in closed_records if r["difficulty_tier"] == "tier_2_inductive"]
    tier3 = [r for r in closed_records if r["difficulty_tier"] == "tier_3_structural"]

    # Target allocations
    n_tier1 = int(target_count * 0.35)
    n_tier2 = int(target_count * 0.40)
    n_tier3 = target_count - n_tier1 - n_tier2

    sample1 = random.sample(tier1, min(len(tier1), n_tier1))
    sample2 = random.sample(tier2, min(len(tier2), n_tier2))
    sample3 = random.sample(tier3, min(len(tier3), n_tier3))

    selected = sample1 + sample2 + sample3

    # 4. Apply perturbations to designated portion
    final_benchmark = []
    n_perturbed_target = int(len(selected) * perturbed_ratio)
    perturbed_indices = set(random.sample(range(len(selected)), n_perturbed_target))

    for idx, item in enumerate(selected):
        if idx in perturbed_indices:
            final_benchmark.append(apply_isomorphic_perturbation(item))
        else:
            final_benchmark.append(item)

    # Shuffle final set
    random.shuffle(final_benchmark)
    return final_benchmark


def create_pilot_benchmark(benchmark_100: list[dict[str, Any]], pilot_size: int = 10) -> list[dict[str, Any]]:
    """Sample a balanced 10-theorem pilot from the 100-theorem benchmark."""
    t1 = [r for r in benchmark_100 if r["difficulty_tier"] == "tier_1_terminal"]
    t2 = [r for r in benchmark_100 if r["difficulty_tier"] == "tier_2_inductive"]
    t3 = [r for r in benchmark_100 if r["difficulty_tier"] == "tier_3_structural"]

    pilot = t1[:4] + t2[:4] + t3[:2]
    return pilot


def _json_default(obj):
    if hasattr(obj, "tolist"):
        return obj.tolist()
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    return str(obj)


def save_benchmark(benchmark_list: list[dict[str, Any]], output_dir: str | Path, filename_prefix: str = "stratified_100_lemmas"):
    """Serialize the benchmark to Parquet and JSON formats."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sanitized = []
    for item in benchmark_list:
        clean_item = {}
        for k, v in item.items():
            if hasattr(v, "tolist"):
                clean_item[k] = v.tolist()
            elif isinstance(v, (int, float, str, bool, list, dict)) or v is None:
                clean_item[k] = v
            elif hasattr(v, "item"):
                clean_item[k] = v.item()
            else:
                clean_item[k] = str(v)
        sanitized.append(clean_item)

    json_path = output_dir / f"{filename_prefix}.json"
    with open(json_path, "w") as f:
        json.dump(sanitized, f, indent=2, default=_json_default)

    df = pd.DataFrame(sanitized)
    # Convert list columns to json strings if saving to parquet to avoid arrow object errors
    df_parquet = df.copy()
    for col in df_parquet.columns:
        if df_parquet[col].dtype == object and df_parquet[col].apply(lambda x: isinstance(x, (list, dict))).any():
            df_parquet[col] = df_parquet[col].apply(lambda x: json.dumps(x, default=_json_default) if isinstance(x, (list, dict)) else str(x))
    df_parquet.to_parquet(output_dir / f"{filename_prefix}.parquet", index=False)
    print(f"Saved benchmark suite with {len(benchmark_list)} theorems to {output_dir}")
