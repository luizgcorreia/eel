"""Unit tests for paired statistical evaluation engine (edel/il/eval_stats.py)."""

import pandas as pd
import pytest
from edel.il.eval_stats import compute_paired_statistics, format_statistical_report_markdown


@pytest.fixture
def synthetic_trials_df() -> pd.DataFrame:
    """Create synthetic trial dataset across 3 arms with known properties."""
    records = []
    # 10 theorems
    for i in range(10):
        lemma = f"test_lemma_{i}"
        tier = "tier_1_terminal" if i < 4 else ("tier_2_inductive" if i < 8 else "tier_3_structural")
        is_pert = (i % 2 == 0)

        # Baseline: succeeds on 0..4 (5/10)
        succ_base = (i < 5)
        records.append({
            "arm": "baseline",
            "lemma_title": lemma,
            "difficulty_tier": tier,
            "is_perturbed": is_pert,
            "success": succ_base,
            "completion_tokens": 500 if succ_base else 2000,
            "prompt_tokens": 1000,
            "total_tokens": 1500 if succ_base else 3000,
            "interaction_turns": 2 if succ_base else 10,
            "error_count": 1 if succ_base else 5,
        })

        # Control RAG: succeeds on 0..5 (6/10)
        succ_ctrl = (i < 6)
        records.append({
            "arm": "control_rag",
            "lemma_title": lemma,
            "difficulty_tier": tier,
            "is_perturbed": is_pert,
            "success": succ_ctrl,
            "completion_tokens": 400 if succ_ctrl else 1800,
            "prompt_tokens": 1200,
            "total_tokens": 1600 if succ_ctrl else 3000,
            "interaction_turns": 2 if succ_ctrl else 9,
            "error_count": 1 if succ_ctrl else 4,
        })

        # Treatment I/L: succeeds on 0..7 (8/10)
        succ_il = (i < 8)
        records.append({
            "arm": "il_treatment",
            "lemma_title": lemma,
            "difficulty_tier": tier,
            "is_perturbed": is_pert,
            "success": succ_il,
            "completion_tokens": 200 if succ_il else 1000,
            "prompt_tokens": 2500,
            "total_tokens": 2700 if succ_il else 3500,
            "interaction_turns": 1 if succ_il else 6,
            "error_count": 0 if succ_il else 3,
        })

    return pd.DataFrame(records)


def test_compute_paired_statistics(synthetic_trials_df: pd.DataFrame):
    """Verify paired statistics computation, discordant counts, and Wilcoxon tests."""
    stats = compute_paired_statistics(
        synthetic_trials_df,
        primary_arm="il_treatment",
        reference_arms=["control_rag", "baseline"],
        n_bootstrap=500,
        random_seed=42,
    )

    assert stats["n_theorems"] == 10
    assert stats["arm_summary"]["il_treatment"]["pass_rate"] == 80.0
    assert stats["arm_summary"]["control_rag"]["pass_rate"] == 60.0
    assert stats["arm_summary"]["baseline"]["pass_rate"] == 50.0

    # Pairwise: IL vs Control
    pair_ctrl = stats["pairwise"]["il_treatment_vs_control_rag"]
    assert pair_ctrl["n_paired"] == 10
    # IL wins on 6, 7 where control lost -> b = 2. Control has no wins where IL lost -> c = 0.
    assert pair_ctrl["discordant"]["b"] == 2
    assert pair_ctrl["discordant"]["c"] == 0
    assert pair_ctrl["mcnemar"]["p_one_sided"] <= 0.25

    # Pairwise: IL vs Baseline
    pair_base = stats["pairwise"]["il_treatment_vs_baseline"]
    assert pair_base["discordant"]["b"] == 3
    assert pair_base["discordant"]["c"] == 0

    # Wilcoxon: IL completion tokens should be significantly lower
    assert pair_ctrl["wilcoxon"]["completion_tokens"]["p_value"] < 0.05
    assert pair_base["wilcoxon"]["completion_tokens"]["p_value"] < 0.05

    # Bootstrap
    assert pair_ctrl["bootstrap"]["prob_primary_greater"] > 0.90


def test_format_statistical_report_markdown(synthetic_trials_df: pd.DataFrame):
    """Verify markdown report generation contains required tables and metrics."""
    stats = compute_paired_statistics(synthetic_trials_df, n_bootstrap=100)
    md = format_statistical_report_markdown(stats)

    assert "## 3. Paired Statistical Significance" in md
    assert "## 4. Continuous Process Trajectory Significance" in md
    assert "## 5. Difficulty Monotonicity" in md
    assert "McNemar Exact" in md
    assert "Wilcoxon" in md
    assert "Treatment I/L vs. Control Rag" in md
