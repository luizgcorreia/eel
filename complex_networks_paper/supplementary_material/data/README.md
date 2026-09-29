# Data Directory: Benchmark Indices and Datasets

**Project:** EEL (Embedding-driven Epistemic Landscape) & I/L (Isabelle/Landscape)  
**Paper:** *Higher-Order Epistemic Networks for Navigating the Archive of Formal Proofs*  
**Venue:** The 15th International Conference on Complex Networks and their Applications (CNA 2026)

---

## Directory Contents

```
data/
├── rag_index/              # Treatment multi-aspect simplicial RAG index (I/L)
│   ├── metadata.parquet    # Metadata table for 1,924 formal theorems and definitions
│   └── embeddings.npz      # 4-aspect dense embeddings (voyage-code-3, d = 1024)
├── flat_rag_index/         # Control monolithic flat RAG index (baseline RAG)
│   ├── metadata.parquet    # Identical 1,924 theorem entries
│   └── embeddings.npz      # Flat unpartitioned proposition embeddings (d = 1024)
└── benchmark_datasets/     # The 140 formal Isabelle/HOL benchmark theorems across 5 tiers
    ├── stratified_100_lemmas.parquet (and .json)   # Tiers 1-3 (40 terminal, 45 inductive, 15 structural)
    ├── deep_structural_20_lemmas.parquet          # Tier 4 (20 deep HOL-Library theorems)
    └── afp_deep_structural_20_lemmas.parquet      # Tier 5 (20 deep pure AFP Featherweight_OCL theorems)
```

---

## 1. Multi-Aspect Treatment Index (`rag_index/`)

Used by **Treatment (I/L Simplicial Navigation)** to evaluate the 12 asymmetric conditional transition distribution operators $D(Y \mid x)$ ($X, Y \in \{P, M, F, I\}$) and Landscape Height centrality $H(v)$.

### Metadata Schema (`metadata.parquet`)
* Total Records: **1,924 theorems and definitions** across `HOL-Library` and `Featherweight_OCL`.
* Primary Columns:
  * `title`: Fully qualified lemma or definition name (e.g., `Featherweight_OCL.UML_Logic.const_subst`).
  * `session`: Isabelle/AFP session name (`HOL-Library` or `Featherweight_OCL`).
  * `theory`: Formal theory identifier (e.g., `HOL-Library.Multiset`).
  * `keyword`: Isabelle statement keyword (`lemma`, `theorem`, `definition`, etc.).
  * `locale`: Active locale scope (if bounded within a formal locale context).
  * `problem`: Formatted Problem aspect string (hypotheses, antecedents, local assumptions).
  * `method`: Formatted Method aspect string (extracted strategy under the Expert Epistemic Invariant).
  * `finding`: Formatted Finding aspect string (tactics, intermediate claims, coupled step maps).
  * `interpretation`: Formatted Interpretation aspect string (consequent conclusion, exported rewrite rule).
  * `landscape_height`: Topological centrality $H(v) = |\text{Reachable}_{G^T}(v)| - 1$ computed over the transpose citation DAG.

### Embeddings Schema (`embeddings.npz`)
Compressed NumPy archive containing 4 separate arrays corresponding to the 4 epistemic aspect submanifolds:
* `problem`: Shape `(1924, 1024)`, `float32`.
* `method`: Shape `(1924, 1024)`, `float32`.
* `finding`: Shape `(1924, 1024)`, `float32`.
* `interpretation`: Shape `(1924, 1024)`, `float32`.

---

## 2. Monolithic Flat Control Index (`flat_rag_index/`)

Used by **Control (Monolithic Flat RAG)** to evaluate conventional RAG architectures (modeled after *IsabeLLM* and *IsaSearch*).
* Contains the exact same 1,924 mathematical entities.
* `embeddings.npz`: Contains a single array `embeddings` of shape `(1924, 1024)`, where each vector is computed over the unpartitioned, raw formal proposition text without epistemic aspect segmentation.

---

## 3. Benchmark Datasets (`benchmark_datasets/`)

The 140 formal theorems evaluated in the 420-trial paired live evaluation on compute node `deeptwelve`:
1. `stratified_100_lemmas.parquet`:
   * **Tier 1 (Terminal Automation, 40 lemmas):** Discharged by single-step automation given exact premise dependencies.
   * **Tier 2 (Inductive Proofs, 45 lemmas):** Requiring structural induction schemes and step-by-step induction pipelines.
   * **Tier 3 (Structural Isar, 15 lemmas):** Multi-step declarative proofs with nested calculations.
   * Includes 30% out-of-distribution isomorphic $\alpha$-renamings to prevent LLM training memorization.
2. `deep_structural_20_lemmas.parquet`:
   * **Tier 4 (Deep HOL-Library, 20 lemmas):** Non-trivial theorems from core libraries requiring deep lemma chaining.
3. `afp_deep_structural_20_lemmas.parquet`:
   * **Tier 5 (Deep Pure AFP, 20 lemmas):** Heavy structural theorems drawn from the Archive of Formal Proofs (`Featherweight_OCL`).
