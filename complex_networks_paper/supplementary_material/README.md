# Supplementary Material: Higher-Order Epistemic Networks for Navigating the Archive of Formal Proofs

**Submission to:** The 15th International Conference on Complex Networks and their Applications (**Complex Networks 2026 / CNA 2026**)  
**Authors:** Luiz G. Correia$^1$, Jesus P. Mena-Chalco$^1$, and Ronaldo Menezes$^2$  
$^1$Centre for Mathematics, Computing and Cognition, Federal University of ABC (UFABC), Santo André, Brazil  
$^2$Department of Computer Science, University of Exeter, Exeter, UK  
**Framework:** EEL (Embedding-driven Epistemic Landscape) & I/L (Isabelle/Landscape)

---

## 1. Package Overview & File Manifest

This supplementary material package provides full source code, benchmark indices, granular trial logs, and extended figures accompanying our paper:

```
supplementary_material/
├── README.md                              # This manifest and master replication guide
├── setup_guide.md                         # Complete end-to-end setup guide (uv, Isabelle2025-2, AFP, Extended AutoCorrode MCP)
├── code/                                  # Self-contained, runnable source code of I/L and evaluation
│   ├── edel/                              # Core implementation of the EEL pipeline & MCP servers
│   │   ├── il/                            # Ingestion, transition operators, MCP servers, evaluation harness
│   │   ├── pipeline/                      # Neural code embedding pipelines (voyage-code-3)
│   │   └── providers/                     # AFP & session data providers
│   ├── AutoCorrode/ir/                    # Headless Isabelle Poly/ML REPL daemon (TCP/MCP)
│   ├── scripts/                           # Reproducibility scripts (evaluation, index generation)
│   ├── pyproject.toml                     # Package metadata configuration
│   └── requirements.txt                   # Frozen dependency specifications
├── data/                                  # Benchmark RAG indices and datasets
│   ├── rag_index/                         # Treatment multi-aspect index (1,924 lemmas, 4-aspect embeddings)
│   ├── flat_rag_index/                    # Control monolithic flat index (1,924 lemmas, flat proposition embeddings)
│   ├── benchmark_datasets/                # The 140 benchmark theorems across 5 tiers
│   └── README.md                          # Data dictionary and schema documentation
├── results/                               # Benchmark trial executions and statistical evaluations
│   ├── benchmark_trials_full.xlsx         # Master formatted Excel spreadsheet (8 sheets)
│   ├── benchmark_140_theorems.csv         # Tabular list of all benchmark theorems and features
│   ├── benchmark_420_trials.csv           # Granular record of all 420 live trials on compute node deeptwelve
│   ├── proved_lemmas_comparison.md        # Comprehensive comparison of native vs generated proofs for all 78 solved theorems
│   ├── summary_performance_table.csv      # Table 2 replication (Pass@1 across all 5 tiers)
│   ├── summary_friction_table.csv         # Table 3 replication (Tokens, turns, error rate, Wilcoxon tests)
│   ├── discordant_pairs_analysis.csv      # Contingency analysis (b=8, c=4, Odds Ratio 2.0x, bootstrap)
│   ├── prompt_caching_economics.csv       # Token economics and latency acceleration metrics
│   └── spectral_sweep.csv                 # Table S1 replication (All-but-the-Top sweep across k in [0, 100])
├── figures/                               # Extended figures and publication vector assets (including 2D Landscape Terrain)
│   ├── fig_simplex_const_subst.pdf & .png
│   ├── fig_joint_simplices.pdf & .png
│   ├── fig_transition_neighborhood_const_subst.pdf & .png
│   ├── fig_landscape_terrain_2d.pdf & .png
│   ├── fig_landscape_terrain_3d.pdf & .png
│   └── figures_guide.md                   # Captions, mathematical descriptions, and epistemic interpretations
└── scripts/
    ├── generate_benchmark_spreadsheet.py  # Standalone script to reproduce the spreadsheet and CSVs
    ├── generate_lemma_comparisons.py      # Script generating the native vs generated proof comparisons
    └── verify_package.py                  # Self-check script validating file checksums and trial integrity
```

---

## 2. Key Empirical Findings Condensed

The experimental evaluation was conducted on compute node `deeptwelve` (64 CPU cores, 251 GB RAM, 2x NVIDIA RTX A5000) using Claude 3.5 Sonnet across **140 formal Isabelle/HOL theorems** (420 paired live trials):

1. **Proving Pass Rate (Table 2):**
   * **Treatment (I/L Simplicial Navigation):** **55.7%** (78/140) overall Pass@1.
   * **Control (Monolithic Flat RAG):** 52.9% (74/140).
   * **Baseline (Zero-RAG):** 53.6% (75/140).
2. **Discordant Pair Advantage:**
   * Treatment wins $b = 8$ vs. Control wins $c = 4$, establishing an empirical **Odds Ratio of 2.00x**.
   * Resampling ($10^4$ iterations) confirms an **84.8% posterior probability** that higher-order simplicial navigation strictly dominates flat monolithic retrieval.
3. **Cognitive Friction Suppression (Table 3):**
   * **16.5% reduction in completion tokens** (Wilcoxon $W = 2077.0, p = 0.00014$).
   * **10.3% reduction in interaction turns** (Wilcoxon $W = 464.5, p = 0.04713$).
   * Kernel error rate reduced to an archive-low **5.87%**.
4. **Prompt Caching Economics:**
   * 912,111 prompt cache read tokens at a 90% discount yielded exact dollar parity (\$1.74 vs \$1.73) and a **2.65x acceleration in generation latency**.
5. **Breakthrough on Deep AFP Proofs:**
   * On `Featherweight_OCL.UML_Logic.const_subst` (19-line structural theorem), Treatment I/L retrieved parent bridge lemmas (`cp_OclIf`, `cp_OclNot`) and completed the proof in 14 turns, whereas unguided baselines exhausted their 15-turn budgets on distractor lemmas.

---

## 3. Quick Replication Instructions

### Step 1: Environment Setup
```bash
# Clone and enter directory
cd supplementary_material/code

# Create virtual environment via uv
uv venv .venv --python 3.11
source .venv/bin/activate
uv pip install -e .
uv pip install -r requirements.txt
```

### Step 2: Verify Package Integrity and Reproduce Spreadsheet
Run the automated verification script from the `supplementary_material` directory:
```bash
python scripts/verify_package.py
```
This script checks:
* Existence and valid schema of all 140 benchmark theorems.
* Exact integrity of all 420 trial logs.
* Pass rates, Wilcoxon test statistics, discordant odds ratios, and token counts.
* Non-degeneracy of the 1,924 embeddings in `rag_index/`.

---

## 4. Contact & Citation

For inquiries regarding the dataset, benchmarks, or continuous AFP index construction:
* **Luiz G. Correia:** `luiz.gabriel@ufabc.edu.br`
* **Jesus P. Mena-Chalco:** `jesus.mena@ufabc.edu.br`
* **Ronaldo Menezes:** `r.menezes@exeter.ac.uk`
