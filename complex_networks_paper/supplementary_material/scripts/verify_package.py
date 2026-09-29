#!/usr/bin/env python3
"""
Verification and Self-Check Script for Supplementary Material Package.
Validates file integrity, index shapes, trial counts, and statistical reproducibility.
"""

import os
import sys
import pandas as pd
import numpy as np
import openpyxl

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SUPP_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "../"))

def check(condition, message):
    if condition:
        print(f"  [\033[92mOK\033[0m] {message}")
    else:
        print(f"  [\033[91mFAIL\033[0m] {message}")
        sys.exit(1)

def main():
    print("=" * 60)
    print("Supplementary Material Integrity and Reproducibility Checks")
    print("=" * 60)

    # 1. Document checks
    print("\n1. Verifying Core Documentation:")
    check(os.path.exists(os.path.join(SUPP_DIR, "README.md")), "README.md exists")
    check(os.path.exists(os.path.join(SUPP_DIR, "setup_guide.md")), "setup_guide.md exists")
    check(os.path.exists(os.path.join(SUPP_DIR, "figures/figures_guide.md")), "figures/figures_guide.md exists")
    check(os.path.exists(os.path.join(SUPP_DIR, "data/README.md")), "data/README.md exists")

    # 2. Data Index Checks
    print("\n2. Verifying RAG Index Data & Embeddings:")
    rag_npz_path = os.path.join(SUPP_DIR, "data/rag_index/embeddings.npz")
    rag_meta_path = os.path.join(SUPP_DIR, "data/rag_index/metadata.parquet")
    check(os.path.exists(rag_npz_path), "Treatment embeddings.npz exists")
    check(os.path.exists(rag_meta_path), "Treatment metadata.parquet exists")
    
    rag_npz = np.load(rag_npz_path)
    for aspect in ['problem', 'method', 'finding', 'interpretation']:
        check(aspect in rag_npz.files, f"Aspect '{aspect}' present in embeddings.npz")
        check(rag_npz[aspect].shape == (1924, 1024), f"Aspect '{aspect}' shape is (1924, 1024)")
        # Check non-degeneracy
        norms = np.linalg.norm(rag_npz[aspect], axis=1)
        check(np.all(norms > 0.0), f"All {aspect} embeddings have non-zero norm (zero collapse)")

    flat_npz_path = os.path.join(SUPP_DIR, "data/flat_rag_index/embeddings.npz")
    flat_npz = np.load(flat_npz_path)
    check('embeddings' in flat_npz.files, "Control flat embeddings array present")
    check(flat_npz['embeddings'].shape == (1924, 1024), "Control embeddings shape is (1924, 1024)")

    # 3. Results Checks
    print("\n3. Verifying Results & Spreadsheet Data:")
    thms_csv = os.path.join(SUPP_DIR, "results/benchmark_140_theorems.csv")
    trials_csv = os.path.join(SUPP_DIR, "results/benchmark_420_trials.csv")
    excel_path = os.path.join(SUPP_DIR, "results/benchmark_trials_full.xlsx")
    
    check(os.path.exists(thms_csv), "benchmark_140_theorems.csv exists")
    check(os.path.exists(trials_csv), "benchmark_420_trials.csv exists")
    check(os.path.exists(excel_path), "benchmark_trials_full.xlsx exists")

    df_thms = pd.read_csv(thms_csv)
    check(len(df_thms) == 140, f"Exactly 140 benchmark theorems present (found {len(df_thms)})")

    df_tri = pd.read_csv(trials_csv)
    check(len(df_tri) == 420, f"Exactly 420 live trials present (found {len(df_tri)})")

    # Pass rates check
    t_succ = df_tri[df_tri['experimental_arm'] == 'Treatment (I/L Simplicial)']['success'].sum()
    c_succ = df_tri[df_tri['experimental_arm'] == 'Control (Monolithic Flat RAG)']['success'].sum()
    b_succ = df_tri[df_tri['experimental_arm'] == 'Baseline (Zero-RAG)']['success'].sum()

    check(t_succ == 78, f"Treatment pass rate is 78/140 (55.7%) (verified {t_succ})")
    check(c_succ == 74, f"Control pass rate is 74/140 (52.9%) (verified {c_succ})")
    check(b_succ == 75, f"Baseline pass rate is 75/140 (53.6%) (verified {b_succ})")

    # Excel sheets check
    wb = openpyxl.load_workbook(excel_path, read_only=True)
    expected_sheets = [
        'Overview & Metadata', 'Table 2 - Proving Performance', 
        'Table 3 - Search Friction', 'Discordant Pairs Analysis', 
        'Prompt Caching Economics', 'All 420 Live Trials', 
        '140 Benchmark Theorems'
    ]
    for s in expected_sheets:
        check(s in wb.sheetnames, f"Excel sheet '{s}' present in workbook")

    # 4. Figures checks
    print("\n4. Verifying Cut Figures:")
    figures = [
        "fig_simplex_const_subst",
        "fig_joint_simplices",
        "fig_transition_neighborhood_const_subst",
        "fig_landscape_terrain_2d",
        "fig_landscape_terrain_3d"
    ]
    for fig in figures:
        check(os.path.exists(os.path.join(SUPP_DIR, f"figures/{fig}.pdf")), f"{fig}.pdf exists")
        check(os.path.exists(os.path.join(SUPP_DIR, f"figures/{fig}.png")), f"{fig}.png exists")

    print("\n" + "=" * 60)
    print("ALL INTEGRITY AND REPRODUCIBILITY CHECKS PASSED (100% OK)")
    print("=" * 60)

if __name__ == "__main__":
    main()
