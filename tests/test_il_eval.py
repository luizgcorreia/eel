"""Unit and Integration Tests for I/L Comparative Evaluation Harness."""

import json
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from edel.il.flat_index import FlatRAGIndex, format_monolithic_text
from edel.il.eval_dataset import (
    compute_dependency_closure,
    classify_difficulty_tier,
    apply_isomorphic_perturbation,
    build_stratified_benchmark,
    create_pilot_benchmark,
)
from edel.il.eval_agent import (
    extract_isabelle_command,
    is_proof_closed,
    MockProvider,
    ProverAgent,
    format_il_treatment_context,
    format_control_rag_context,
)
from edel.il.index import NumpyRAGIndex


# ---------------------------------------------------------------------------
# Tests for Component 1: FlatRAGIndex (Control Monolithic RAG)
# ---------------------------------------------------------------------------

def test_format_monolithic_text():
    rec = {
        "theory": "HOL-Library.Multiset",
        "title": "count_inI",
        "statement_text": "lemma count_inI: \"count M x = 0 ⟹ False ⟹ x ∈# M\"",
        "proof_text": "proof (rule ccontr)\n  assume \"x ∉# M\"\n  show False by simp\nqed",
    }
    chunk = format_monolithic_text(rec)
    assert "Theory: HOL-Library.Multiset" in chunk
    assert "Lemma: count_inI" in chunk
    assert "Statement:" in chunk
    assert "Proof:" in chunk
    assert "count M x = 0" in chunk


def test_flat_rag_index_build_search_and_masking(tmp_path):
    records = [
        {
            "theory": "Th1",
            "title": "Th1.lem1",
            "statement_text": "lemma lem1: A",
            "proof_text": "by simp",
            "line": 10,
            "keyword": "lemma",
        },
        {
            "theory": "Th1",
            "title": "Th1.lem2",
            "statement_text": "lemma lem2: B",
            "proof_text": "by auto",
            "line": 20,
            "keyword": "lemma",
        },
        {
            "theory": "Th1",
            "title": "Th1.lem3",
            "statement_text": "lemma lem3: C",
            "proof_text": "by blast",
            "line": 30,
            "keyword": "lemma",
        },
    ]
    df = pd.DataFrame(records)
    # 3 mock embeddings: [1, 0], [0.7, 0.7], [0, 1]
    embs = np.array([[1.0, 0.0], [0.7071, 0.7071], [0.0, 1.0]], dtype=np.float32)

    index = FlatRAGIndex()
    index.build_from_dataframe(df, embeddings=embs)

    # Save and reload
    index.save(tmp_path / "flat_index")
    loaded = FlatRAGIndex()
    loaded.load(tmp_path / "flat_index")

    assert len(loaded.metadata) == 3
    assert loaded.embeddings.shape == (3, 2)

    # Search with self-masking: query [1, 0], but exclude Th1.lem1
    res = loaded.search(query_vector=[1.0, 0.0], top_k=2, exclude_titles=["Th1.lem1"])
    assert len(res) == 2
    assert res[0]["title"] == "Th1.lem2"

    # Search with temporal / file-precedence masking: target is at line 20
    # Any lemma at or after line 20 in Th1 should be excluded
    res_masked = loaded.search(
        query_vector=[0.0, 1.0],
        top_k=2,
        theory="Th1",
        max_line=20,
    )
    assert len(res_masked) == 1
    assert res_masked[0]["title"] == "Th1.lem1"


# ---------------------------------------------------------------------------
# Tests for Component 2: eval_dataset (Closure & Perturbations)
# ---------------------------------------------------------------------------

def test_compute_dependency_closure():
    indexed_titles = {"Th1.lem1", "Th1.lem2"}
    indexed_shorts = {"lem1", "lem2"}

    # All dependencies covered
    lemma1 = {"cited_deps": "lem1, ccontr, not_in_iff"}
    assert compute_dependency_closure(lemma1, indexed_titles, indexed_shorts) == 1.0

    # None cited
    lemma2 = {"cited_deps": "none"}
    assert compute_dependency_closure(lemma2, indexed_titles, indexed_shorts) == 1.0

    # Half missing
    lemma3 = {"cited_deps": "lem1, unknown_external_lemma"}
    assert compute_dependency_closure(lemma3, indexed_titles, indexed_shorts) == 0.5


def test_classify_difficulty_tier():
    # Terminal
    rec_term = {"proof_text": "by simp", "proof_steps": ["by simp"], "rule_type": "general_theorem"}
    assert classify_difficulty_tier(rec_term) == "tier_1_terminal"

    # Inductive
    rec_ind = {"proof_text": "apply (induction x)\n apply auto\n done", "proof_steps": ["1", "2", "3"]}
    assert classify_difficulty_tier(rec_ind) == "tier_2_inductive"

    # Structural Isar
    rec_struct = {
        "proof_text": "proof -\n  fix x\n  have A: \"P x\" by simp\n  have B: \"Q x\" by blast\n  show False using A B by auto\nqed",
        "proof_steps": ["proof -", "have A", "have B", "show False", "qed"],
    }
    assert classify_difficulty_tier(rec_struct) == "tier_3_structural"


def test_apply_isomorphic_perturbation():
    original = {
        "title": "count_set_mset",
        "statement_text": "lemma count_set_mset: \"count A x > 0 ⟷ x ∈ set_mset A\"",
        "proof_text": "by (simp add: count_greater_zero_iff)",
        "problem": "count A x > 0",
        "interpretation": "x ∈ set_mset A",
    }
    perturbed = apply_isomorphic_perturbation(original)

    assert perturbed["is_perturbed"] is True
    assert perturbed["title"] == "count_set_mset_novel_variant"
    assert "x_elem" in perturbed["statement_text"]
    assert "A" in perturbed["statement_text"]


def test_build_and_pilot_benchmark():
    records = []
    for i in range(50):
        records.append({
            "title": f"Test.lem_{i}",
            "statement_text": f"lemma lem_{i}: True",
            "proof_text": "by (simp add: ccontr)" if i % 3 == 0 else ("apply (induction n) by auto" if i % 3 == 1 else "proof -\n have True by simp\n show True by simp\n qed\n" * 5),
            "proof_steps": ["s1"] if i % 3 == 0 else ["s1", "s2", "s3", "s4"],
            "cited_deps": "ccontr" if i % 3 == 0 else "none",
            "keyword": "lemma",
            "rule_type": "general_theorem",
        })

    bench = build_stratified_benchmark(records, target_count=30, seed=123, perturbed_ratio=0.30)
    assert len(bench) == 30

    # Verify perturbation ratio
    n_pert = sum(1 for r in bench if r["is_perturbed"])
    assert n_pert == 9  # 30 * 0.30

    # Pilot
    pilot = create_pilot_benchmark(bench, pilot_size=10)
    assert len(pilot) == 10
    tier_counts = {r["difficulty_tier"]: 0 for r in pilot}
    for r in pilot:
        tier_counts[r["difficulty_tier"]] += 1
    assert tier_counts["tier_1_terminal"] == 4
    assert tier_counts["tier_2_inductive"] == 4
    assert tier_counts["tier_3_structural"] == 2


# ---------------------------------------------------------------------------
# Tests for Component 3: eval_agent (ProverAgent & Providers)
# ---------------------------------------------------------------------------

def test_extract_isabelle_command():
    # Markdown block
    resp1 = "Here is the step:\n```isabelle\napply (simp add: foo)\n```"
    assert extract_isabelle_command(resp1) == "apply (simp add: foo)"

    # Multiple lines in block
    resp2 = "```\nby (simp add: a\n         b)\n```"
    assert extract_isabelle_command(resp2) == "by (simp add: a b)"

    # Fallback to plain text line
    resp3 = "We should try simplification:\napply auto\nThis should close the goal."
    assert extract_isabelle_command(resp3) == "apply auto"

    # Multi-command guard: prevents "apply (...) apply (...)" on one line
    resp4 = "```isabelle\napply (induction M) apply auto\n```"
    assert extract_isabelle_command(resp4) == "apply (induction M)"


def test_is_proof_closed():
    # Subgoals 0 outside Isar block
    assert is_proof_closed("apply auto", "OK", "0 subgoals") is True
    assert is_proof_closed("apply auto", "OK", "No subgoals") is True

    # Inside open Isar proof block, proof is only closed by qed
    assert is_proof_closed("apply auto", "OK", "proof (state)\ngoal:\nNo subgoals!") is False
    assert is_proof_closed("qed", "theorem foo: True", "proof (state)") is True

    # Theorem output from REPL
    assert is_proof_closed("by simp", "theorem count_inI: True", "Toplevel state") is True

    # Closing command with no subgoals
    assert is_proof_closed("qed", "OK", "Toplevel state") is True

    # Incomplete proof
    assert is_proof_closed("apply simp", "OK", "goal (1 subgoal):\n 1. True") is False



def test_prover_agent_mock_execution():
    mock_llm = MockProvider(ground_truth_steps=["apply (rule ccontr)", "by simp"])
    agent = ProverAgent(
        arm="baseline",
        repl_client=None,  # Disconnected mock
        llm_provider=mock_llm,
        max_turns=5,
    )

    theorem = {
        "title": "Test.dummy",
        "theory": "Main",
        "statement_text": "lemma dummy: True",
        "difficulty_tier": "tier_1_terminal",
        "is_perturbed": False,
        "cited_deps": "none",
    }

    result = agent.prove_theorem(theorem, trial_id="test_001")
    assert result.trial_id == "test_001"
    assert result.arm == "baseline"
    assert result.interaction_turns > 0
    assert result.total_tokens > 0
    assert result.prompt_tokens > 0
    assert result.completion_tokens > 0


def test_prover_agent_il_treatment_context():
    candidates = [{
        "title": "HOL-Library.Multiset.count_inI",
        "theory": "HOL-Library.Multiset",
        "rule_type": "elim_rule",
        "attributes": "simp, intro!",
        "problem": "count M x = 0 ⟹ False",
        "method": "proof (rule ccontr)",
        "finding": "assume x ∉# M",
        "interpretation": "x ∈# M",
        "proof_steps": ["proof (rule ccontr)", "show False by simp", "qed"],
    }]
    ctx = format_il_treatment_context(candidates)
    assert "PROOF INTELLIGENCE DOSSIER" in ctx
    assert "DOSSIER A — D(Proof-Strategy | Premises)" in ctx
    assert "DOSSIER B — D(Tactic-Map | Conclusion)" in ctx
    assert "DOSSIER C — D(Tactic-Map|Proof-Strategy)∘D(Proof-Strategy|Premises)" in ctx
    assert "HOL-Library.Multiset.count_inI" in ctx
    assert "Rule Class:     elim_rule [simp, intro!]" in ctx
    assert "→ DIRECTIVE:    simp add: count_inI" in ctx


def test_eel_tools_retrieval_and_merging():
    from edel.il.eel_tools import (
        build_expert_system_prompt,
        extract_cited_dependencies,
        format_epistemic_dossier,
        weighted_merge,
    )

    ch_a = [{"title": "L1", "lemma": {"title": "L1", "method": "simp"}, "score": 0.9}]
    ch_b = [{"title": "L2", "lemma": {"title": "L2", "interpretation": "goal"}, "score": 0.8}]
    ch_c = [{"title": "L3", "lemma": {"title": "L3", "finding": "step 1 deps: [foo, bar]"}, "score": 0.85, "hop1_anchor": "L1"}]

    merged = weighted_merge(ch_a, ch_b, ch_c, w_a=0.45, w_b=0.25, w_c=0.30)
    assert len(merged) == 3
    titles = [m["title"] for m in merged]
    assert "L1" in titles
    assert "L2" in titles
    assert "L3" in titles

    dossier = format_epistemic_dossier(channel_a=ch_a, channel_b=ch_b, channel_c=ch_c)
    assert "[A1] L1" in dossier
    assert "[B1] L2" in dossier
    assert "[C1] L3" in dossier
    assert "anchor: L1" in dossier

    deps = extract_cited_dependencies("tactic deps: [foo, bar]", None)
    assert deps == ["bar", "foo"]

    prompt = build_expert_system_prompt()
    assert "Expert EEL Proof Formula" in prompt
    assert "DOSSIER A" in prompt
    assert "DOSSIER B" in prompt
    assert "DOSSIER C" in prompt
    assert "Expert Tactic Execution Ladder" in prompt


def test_completion_result_and_cost_tracking():
    from edel.il.eval_agent import CompletionResult, EvalTrialResult

    res = CompletionResult(
        text="by auto",
        prompt_tokens=3000,
        completion_tokens=100,
        cache_creation_tokens=1000,
        cache_read_tokens=2000,
        cost_usd=0.0039,
    )
    assert res.text == "by auto"
    assert res.prompt_tokens == 3000
    assert res.completion_tokens == 100
    assert res.cache_read_tokens == 2000
    assert res.cost_usd == 0.0039
    # Tuple unpacking
    t, p, c = res[:3]
    assert t == "by auto"
    assert p == 3000
    assert c == 100

