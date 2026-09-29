"""Run full PIDE segmentation on all 25 CNA paper theories and compare against legacy deeptwelve index."""

from __future__ import annotations

import os
import re
from pathlib import Path
from collections import Counter
import numpy as np
import pandas as pd

from edel.il.pide_ingest import PideTheoryIngester

def compute_entropy(vals: list[str]) -> tuple[float, float, int, int]:
    """Compute Shannon entropy, normalized entropy, unique count, max frequency."""
    c = Counter(vals)
    n = len(vals)
    if n == 0:
        return 0.0, 0.0, 0, 0
    probs = np.array(list(c.values())) / n
    h = -np.sum(probs * np.log2(probs))
    h_max = np.log2(n)
    return h, (h / h_max * 100.0) if h_max > 0 else 0.0, len(c), max(c.values())

def count_tokens(text: str) -> int:
    return len(re.findall(r"\w+|[^\s\w]", str(text)))

def main():
    print("=" * 80)
    print("RUNNING FULL CNA BENCHMARK THEORIES SEGMENTATION VIA PIDE")
    print("=" * 80)

    legacy_path = Path("artifacts/rag_index/metadata.parquet")
    if not legacy_path.exists():
        raise FileNotFoundError(f"Missing legacy benchmark at {legacy_path}")

    df_legacy = pd.read_parquet(legacy_path)
    print(f"Loaded Legacy deeptwelve index: {len(df_legacy)} units across {df_legacy['theory'].nunique()} theories.")

    # Unique sessions and theories in order
    theory_groups = df_legacy.groupby(["session", "theory"]).size().reset_index(name="legacy_count")
    
    afp_dir = Path("/home/correia/edel/external/afp-2025-2/thys")
    pide = PideTheoryIngester(afp_thys_dir=afp_dir)

    all_pide_records = []
    theory_concordance = []

    print("\n--- Ingesting all 25 theories with PIDE ---")
    for idx, row in theory_groups.iterrows():
        sess = row["session"]
        th = row["theory"]
        l_cnt = row["legacy_count"]

        recs = pide.ingest_theory(th, session=sess)
        p_cnt = len(recs)
        match = "MATCH" if p_cnt == l_cnt else f"DIFF ({p_cnt} vs {l_cnt})"
        print(f"[{idx+1:02d}/25] {sess:18s} | {th:36s} | PIDE: {p_cnt:3d} | Legacy: {l_cnt:3d} | {match}")
        
        theory_concordance.append({
            "session": sess,
            "theory": th,
            "pide_count": p_cnt,
            "legacy_count": l_cnt,
            "match": p_cnt == l_cnt,
        })
        all_pide_records.extend(recs)

    df_pide = pd.DataFrame(all_pide_records)
    print("\n" + "=" * 80)
    print(f"TOTAL UNITS INGESTED: PIDE = {len(df_pide)} | Legacy = {len(df_legacy)}")
    print("=" * 80)

    # 1. Check title alignment
    legacy_titles = set(df_legacy["title"].dropna())
    pide_titles = set(df_pide["title"].dropna())
    common_titles = legacy_titles.intersection(pide_titles)
    print(f"Title Alignment: {len(common_titles)} / {len(legacy_titles)} common units ({len(common_titles)/len(legacy_titles)*100:.1f}%)")

    # 2. Aspect Emptiness Audit
    print("\n--- Aspect Emptiness Rates ---")
    for aspect in ["problem", "method", "finding", "interpretation"]:
        leg_empty = sum(df_legacy[aspect].str.strip() == "")
        pide_empty = sum(df_pide[aspect].str.strip() == "")
        print(f"{aspect.capitalize():14s}: Legacy Emptiness = {leg_empty:4d}/{len(df_legacy)} ({leg_empty/len(df_legacy)*100:.1f}%) | PIDE Emptiness = {pide_empty:4d}/{len(df_pide)} ({pide_empty/len(df_pide)*100:.1f}%)")

    # 3. Method = Finding Collapse (2-Simplex degeneracy) on non-definitions
    def_kws = {"definition", "fun", "primrec", "datatype", "type_synonym", "abbreviation"}
    leg_non_def = df_legacy[~df_legacy["keyword"].isin(def_kws)]
    pide_non_def = df_pide[~df_pide["keyword"].isin(def_kws)]

    leg_mf_collapse = sum(leg_non_def["method"] == leg_non_def["finding"])
    pide_mf_collapse = sum(pide_non_def["method"] == pide_non_def["finding"])
    print("\n--- Degeneracy / Method = Finding Collapse (on non-definitions) ---")
    print(f"Legacy (I/R) M = F Collapse: {leg_mf_collapse:4d} / {len(leg_non_def)} ({leg_mf_collapse/len(leg_non_def)*100:.1f}%)")
    print(f"PIDE Model   M = F Collapse: {pide_mf_collapse:4d} / {len(pide_non_def)} ({pide_mf_collapse/len(pide_non_def)*100:.1f}%)")

    # 4. Token Counts Comparison
    print("\n--- Token Statistics Comparison ---")
    tok_stats = []
    for aspect in ["problem", "method", "finding", "interpretation"]:
        leg_toks = df_legacy[aspect].apply(count_tokens)
        pide_toks = df_pide[aspect].apply(count_tokens)
        tok_stats.append({
            "Aspect": aspect.capitalize(),
            "Legacy Mean": f"{leg_toks.mean():.1f}",
            "PIDE Mean": f"{pide_toks.mean():.1f}",
            "Legacy Median": f"{leg_toks.median():.0f}",
            "PIDE Median": f"{pide_toks.median():.0f}",
            "Legacy Min-Max": f"{leg_toks.min()}-{leg_toks.max()}",
            "PIDE Min-Max": f"{pide_toks.min()}-{pide_toks.max()}",
        })
    df_tok = pd.DataFrame(tok_stats)
    print(df_tok.to_string(index=False))

    # 5. Shannon Entropy Across All 1,924 Units
    print("\n--- Global Shannon Entropy Across all 1,924 Entities ---")
    print(f"Theoretical Max Entropy H_max = log2({len(df_pide)}) = {np.log2(len(df_pide)):.2f} bits")
    entropy_rows = []
    for aspect in ["problem", "method", "finding", "interpretation"]:
        leg_h, leg_pct, leg_u, leg_mf = compute_entropy(df_legacy[aspect].tolist())
        pide_h, pide_pct, pide_u, pide_mf = compute_entropy(df_pide[aspect].tolist())
        entropy_rows.append({
            "Aspect": aspect.capitalize(),
            "Legacy H": f"{leg_h:.2f} ({leg_pct:.1f}%)",
            "PIDE H": f"{pide_h:.2f} ({pide_pct:.1f}%)",
            "Legacy Unique": f"{leg_u}/{len(df_legacy)}",
            "PIDE Unique": f"{pide_u}/{len(df_pide)}",
            "Legacy MaxFreq": f"{leg_mf} ({leg_mf/len(df_legacy)*100:.1f}%)",
            "PIDE MaxFreq": f"{pide_mf} ({pide_mf/len(df_pide)*100:.1f}%)",
        })
    df_ent = pd.DataFrame(entropy_rows)
    print(df_ent.to_string(index=False))

    # 6. Save PIDE segmented parquet for further inspection
    out_dir = Path("artifacts/pide_cna_benchmark")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "pide_segmented_metadata.parquet"
    df_pide.to_parquet(out_path, index=False)
    print(f"\nSaved PIDE segmentation dataset ({len(df_pide)} units) to {out_path}")

    # 7. Qualitative Samples (Side-by-Side)
    print("\n" + "=" * 80)
    print("QUALITATIVE SIDE-BY-SIDE INSPECTION OF REPRESENTATIVE UNITS")
    print("=" * 80)

    sample_queries = [
        ("Featherweight_OCL", "const_subst", "Deep Isar Theorem"),
        ("AVL-Trees", "sorted_insort", "Procedural Induction"),
        ("Aho_Corasick", "build_trie_step", "Complex Automaton Step"),
        ("HOL-Library", "size_mset", "One-liner Simplification"),
        ("Featherweight_OCL", "true", "0-Simplex Definition"),
    ]

    for sess, term, desc in sample_queries:
        print(f"\n[{desc.upper()}] Session: {sess} | Query: {term}")
        leg_sub = df_legacy[(df_legacy["session"] == sess) & (df_legacy["title"].str.contains(term, case=False, regex=False))]
        pide_sub = df_pide[(df_pide["session"] == sess) & (df_pide["title"].str.contains(term, case=False, regex=False))]

        if not leg_sub.empty and not pide_sub.empty:
            l_row = leg_sub.iloc[0]
            p_row = pide_sub.iloc[0]
            print(f"Title: {p_row['title']}")
            print(f"  Legacy Method: {l_row['method'][:90]}...")
            print(f"  PIDE Method:   {p_row['method'][:90]}...")
            print(f"  Legacy Finding: {l_row['finding'][:90]}...")
            print(f"  PIDE Finding:   {p_row['finding'][:90]}...")
            print(f"  Legacy Interp:  {l_row['interpretation'][:80]}...")
            print(f"  PIDE Interp:    {p_row['interpretation'][:80]}...")
            if p_row.get("architecture"):
                print(f"  PIDE Architecture: {p_row['architecture']}")

if __name__ == "__main__":
    main()
