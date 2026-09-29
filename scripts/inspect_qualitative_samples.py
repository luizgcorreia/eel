import pandas as pd

df_pide = pd.read_parquet("artifacts/pide_cna_benchmark/pide_segmented_metadata.parquet")
df_leg = pd.read_parquet("artifacts/rag_index/metadata.parquet")

targets = [
    ("Featherweight_OCL.UML_Logic.true", "0-Simplex Definition (true)"),
    ("Featherweight_OCL.UML_Logic.const_subst", "Deep 19-line Isar (const_subst)"),
    ("AVL-Trees.AVL.avl_insert_aux", "Inductive Tree Proof (avl_insert_aux)"),
    ("Aho_Corasick.Aho_Corasick.ac_step", "Complex Automaton Step (ac_step)"),
    ("HOL-Library.Multiset.size_mset_mono", "Set Equational Lemma (size_mset_mono)"),
]

for t, desc in targets:
    print("=" * 80)
    print(f"[{desc.upper()}] {t}")
    print("=" * 80)
    p = df_pide[df_pide["title"] == t].iloc[0]
    l = df_leg[df_leg["title"] == t].iloc[0]
    
    for aspect in ["problem", "method", "finding", "interpretation"]:
        print(f"\n--- {aspect.upper()} ---")
        p_val = str(p[aspect]).strip().replace("\n", " ")
        l_val = str(l[aspect]).strip().replace("\n", " ")
        print(f"PIDE   : {p_val[:140]}")
        print(f"LEGACY : {l_val[:140]}")
    if p.get("architecture"):
        arch_val = p.get("architecture")
        print(f"\nPIDE Architecture: {arch_val}")
