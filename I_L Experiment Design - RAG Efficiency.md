# Experimental Design: Evaluating Proof Generation Efficiency in Isabelle/Landscape (I/L)

## 1. Executive Summary & Research Motivation

A central question for the first paper on **Isabelle/Landscape (I/L)** and the **Epistemic Embedded Landscape (EEL)** theory is:
> *Does decomposing formal mathematical libraries into structured epistemic aspects ($P, M, F, I$), coupled step maps, and rule automation directives provide a measurable advantage for autonomous proof generation over traditional monolithic RAG and raw REPL baselines?*

In the literature on machine learning for Interactive Theorem Proving (ITP), retrieval-augmented generation (RAG) is almost exclusively implemented as **"flat" text retrieval**: the raw text of theorems and their proofs are embedded as monolithic chunks, and top-$k$ nearest neighbors are stuffed into the language model's prompt. While this approach can surface relevant lemma names, it suffers from several severe pathologies:
1. **Type-Erasure & Sort Blindness:** Raw Isabelle syntax does not reflect sort constraints (`'a :: linorder`) or typing environments, causing models to retrieve type-incompatible lemmas that fail unification in the proof assistant.
2. **Context Pollution & Noise:** Monolithic proof scripts contain internal subgoals, dead ends, and opaque automation invocations that consume large portions of the context window without providing clear deductive guidance.
3. **Operational Ambiguity:** Traditional RAG retrieves lemmas without specifying *how* they should be used (e.g., as a term rewriting rule via `simp`, a backward-chaining rule via `rule`, or an inductive invariant).

This experiment is designed to empirically demonstrate that **I/L’s structured epistemic landscape enables language models to synthesize formal proofs with significantly higher token efficiency, lower trial-and-error backtracking, and superior success rates** compared to both a raw REPL baseline (no retrieval) and a standard monolithic RAG control.

---

## 2. Theoretical Hypotheses

Let $T_{\text{proof}}$ denote the total token consumption required to successfully close a formal proof in the Isabelle REPL (`I/R`), and let $\text{Err}_{\text{rate}}$ denote the proportion of submitted proof steps rejected by Isabelle's kernel.

### Primary Hypothesis: Token Efficiency
$$\mathcal{H}_1: \quad \mathbb{E}\left[T_{\text{proof}}(\text{I/L Treatment})\right] \ll \mathbb{E}\left[T_{\text{proof}}(\text{Control RAG})\right] < \mathbb{E}\left[T_{\text{proof}}(\text{Baseline})\right]$$
*Rationale:* By presenting the agent with explicit sort constraints, coupled step maps, and automation directives, the agent synthesizes correct Isabelle tactics on the first attempt, eliminating expensive exploratory token loops.

### Secondary Hypothesis: REPL Failure Reduction
$$\mathcal{H}_2: \quad \mathbb{E}\left[\text{Err}_{\text{rate}}(\text{I/L Treatment})\right] \ll \mathbb{E}\left[\text{Err}_{\text{rate}}(\text{Control RAG})\right]$$
*Rationale:* Type-incompatible and syntactically misleading lemma retrievals in naive RAG cause frequent kernel failures (`Failed to apply initial proof method`, `Type unification failed`).

### Tertiary Hypothesis: Structural Proof Scaling
$$\mathcal{H}_3: \quad \text{Pass@1}_{\text{I/L}}(\text{Tier 3 Structural}) - \text{Pass@1}_{\text{Control}}(\text{Tier 3 Structural}) > \text{Pass@1}_{\text{I/L}}(\text{Tier 1 Terminal}) - \text{Pass@1}_{\text{Control}}(\text{Tier 1 Terminal})$$
*Rationale:* While simple one-liner goals can often be closed by brute-force automation, complex multi-step inductive proofs benefit disproportionately from Aspect 2 (`method` roadmaps) and Aspect 3 (Coupled Step Maps).

---

## 3. The Three Experimental Arms

To isolate the causal impact of the epistemic representation, all three arms share the identical base LLM (**Claude Sonnet 5** (`claude-sonnet-5`), priced at $2/MTok input, $10/MTok output), the identical interaction harness, and the same underlying Isabelle REPL (`AutoCorrode/ir/repl.py` on `deeptwelve`).

```
                              Target Theorem to Prove
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        │                                │                                │
        ▼                                ▼                                ▼
  [ARM 0: Baseline]              [ARM 1: Control]                [ARM 2: Treatment]
  Zero-RAG REPL Agent            Naive Monolithic RAG            I/L Epistemic Landscape
  (Pure Interaction)             (Standard Dense RAG)            (4 Aspects + Step Map)
        │                                │                                │
        ├─ REPL Buffer only              ├─ Single dense embedding        ├─ Multi-aspect queries (P,M,F,I)
        ├─ Base LLM weights              ├─ Verbatim statement+proof      ├─ Coupled Step Maps
        └─ No external search            └─ Top-k raw chunks injected     ├─ Rule attributes ([simp], [intro])
                                                                          └─ Sort bounds & fixes
```

### Arm 0: Baseline (Zero-RAG REPL Agent)
- **Configuration:** The agent receives the current goal state from Isabelle's PIDE via `Ir.state` and must generate proof steps (`Ir.step`) using only its parametric memory (weights) and whatever lemmas exist in the imported session context.
- **Purpose:** Establishes the floor of LLM reasoning capability in Isabelle without any external knowledge retrieval.

### Arm 1: Control (Naive / Monolithic Flat RAG)
- **Configuration:** Standard RAG pipeline commonly used in code and theorem proving benchmarks (e.g., Baldur, Thor, DSP).
- **Index:** Each lemma in the background archive is indexed as a **single monolithic text chunk** containing the verbatim statement and verbatim proof.
- **Embedding:** Embedded using `voyage-code-3`.
- **Query:** The current goal proposition string is embedded as a single query vector; top-$k$ ($k=3$) nearest chunks are retrieved by cosine similarity and injected into the prompt.
- **Purpose:** Represents state-of-the-art conventional RAG practice.

### Arm 2: Treatment (I/L Epistemic Landscape Agent)
- **Configuration:** Full I/L representation.
- **Index:** Each lemma is decomposed into the 4 expert epistemic aspects ($P, M, F, I$) with contextual envelopes, plus coupled step maps and rule classifications (`rule_type`, `attributes`, `locale`, `dependents_count`).
- **Embedding:** 4 dense vectors per lemma via `voyage-code-3`.
- **Query:** Multi-aspect retrieval allowing the agent to target:
  - **Consequent Matching:** Querying against Aspect 4 (`interpretation`) to find lemmas that conclude the target goal.
  - **Strategic Matching:** Querying against Aspect 2 (`method`) to find analogous inductive roadmaps or decompositions.
  - **Antecedent Matching:** Querying against Aspect 1 (`problem`) to find lemmas compatible with current hypotheses and sort constraints.
- **Prompt Injection:** Cleaned goal statement + explicit sort bounds + **Coupled Step Map** + **Rule Attribute Directives** (`[simp]`, `[intro!]`).

---

## 4. Control RAG Specification: The Monolithic Baseline

To ensure absolute methodological fairness, **the Control RAG agent must index the exact same background archive of theories as the Treatment agent**, using the exact same embedding model (`voyage-code-3`), the exact same vector dimension, and the exact same retrieval budget ($k=3$ lemmas).

### Control Chunk Text Format
In the Control index, each theorem is serialized as:

```text
Theory: {theory}
Lemma: {title}
Statement:
{statement_text}
Proof:
{proof_text}
```

#### Concrete Example (Control RAG):
```text
Theory: HOL-Library.Multiset
Lemma: HOL-Library.Multiset.count_inI
Statement:
lemma count_inI: "count M x = 0 ⟹ False ⟹ x ∈# M"
Proof:
proof (rule ccontr)
  assume "x ∉# M"
  with assms show False by (simp add: not_in_iff)
qed
```

### Contrast: Control vs. Treatment Representation

| Dimension | Control RAG Agent (Arm 1) | I/L Treatment Agent (Arm 2) |
| :--- | :--- | :--- |
| **Embeddings per Theorem** | 1 monolithic vector | 4 aspect vectors ($\mathbf{emb}_P, \mathbf{emb}_M, \mathbf{emb}_F, \mathbf{emb}_I$) |
| **Query Mechanism** | Flat goal string similarity | Multi-aspect targeted queries ($D_{pi}$ closure, $D_{pm}$ strategy) |
| **Prompt Representation** | Raw unparsed `.thy` text | Proposition + **Coupled Step Map** + **Rule Directives** |
| **Sort / Type Constraints** | None (erased / raw syntax) | Explicit sort constraints (`'a :: linorder`) & fixed parameters |
| **Automation Directives** | Omitted | Explicit Isabelle rule roles (`[simp]`, `[intro!]`, `[elim]`) |
| **Contextual Envelope** | None | Standardized `[Theory] [Locale] [Rule] [Attributes]` header |

---

## 5. Quantitative Evaluation Metrics

Proof efficiency is measured across three primary dimensions: token overhead, kernel interactions, and retrieval utility.

### 1. Token Efficiency Metrics (Primary)
For every theorem $i$ in the test set:
- **Total Proof Tokens ($T_{\text{proof}}$):**
  $$T_{\text{proof}}(i) = T_{\text{prompt}}(i) + T_{\text{completion}}(i)$$
  The total token expenditure across all turns until the proof is closed or the budget is exhausted.
- **Completion Token Cost ($T_{\text{completion}}$):**
  The number of tokens generated by the LLM. This directly reflects trial-and-error overhead: when an agent is confused or guesses wrong tactics, $T_{\text{completion}}$ surges.
- **Prompt Token Overhead ($T_{\text{prompt}}$):**
  The cumulative prompt tokens fed to the model, measuring the density and footprint of the retrieved context.

### 2. Interaction Dynamics & Failure Metrics
- **Success Rate (Pass@1):**
  The percentage of test theorems successfully closed within a strict budget of **30 REPL interaction turns** and **50,000 total tokens**.
- **Kernel Error Rate ($\text{Err}_{\text{rate}}$):**
  $$\text{Err}_{\text{rate}} = \frac{N_{\text{errors}}}{N_{\text{total\_repl\_steps}}}$$
  The fraction of attempted `Ir.step` executions that returned an error (`ERR`) from Isabelle's ML engine.
- **Proof Trajectory Length ($S$):**
  The number of accepted proof steps required to reach `qed` or terminal `done`.

### 3. Retrieval Precision & Utility
- **Token-Normalized Citation Utility ($\text{Util}_{\text{retrieval}}$):**
  $$\text{Util}_{\text{retrieval}} = \frac{\sum_{l \in \text{Retrieved}} \mathbb{I}(l \in \text{CitedDependencies})}{\text{Total Tokens Injected by Retrieval}}$$
  Measures the density of genuinely useful mathematical information delivered to the LLM per token of context consumed.

---

## 6. Benchmark Dataset, Dependency Closure & Anti-Contamination Protocols

A rigorous benchmark design must confront two major empirical threats to validity in LLM theorem proving:
1. **Incomplete Index Bottlenecks:** Because this initial paper indexes a focused subset of sessions rather than the entire 1,098-session AFP, an agent might fail simply because an essential external dependency is absent from the index.
2. **Pre-training Memorization:** Frontier models (Claude 3.5 Sonnet / Claude 3.7 / GPT-4o) have been pre-trained on vast code repositories containing Isabelle/HOL and historical AFP theories. If Claude has memorized the verbatim proof of a theorem, all three arms might collapse into trivial 1-turn closures, flattening the comparative signal.

---

### 6.1 The Context Closure Requirement (Self-Contained Theories)

Because cross-session bridging across the entire AFP is reserved for follow-up work once the full archive is ingested, every target theorem in the benchmark must satisfy **Complete Dependency Closure**:

$$\text{Closure}(T) = \frac{|\text{deps}(T) \cap \text{IndexedCorpus}|}{|\text{deps}(T)|} = 1.0$$

- **Intra-Session Completeness:** All imported theories, definitions, and prerequisite lemmas cited in the historical proof of $T$ must reside within the indexed sessions (`HOL-Library`, `AVL-Trees`, `Aho_Corasick`, `Featherweight_OCL`).
- **Eliminating External Confounders:** This guarantees that if an agent fails to prove $T$, the failure is attributable to retrieval quality or deductive search, rather than an artificial truncation of the search space.

---

### 6.2 Mitigating Model Memorization & Pre-training Bias

To ensure the benchmark presents a genuine deductive challenge rather than a memory-retrieval test, we employ four synergistic countermeasures:

#### 1. Baseline Arm as Empirical Memorization Normalizer
The primary evaluation signal is the differential advantage over parametric memory:
$$\Delta T = T_{\text{Baseline}} - T_{\text{Treatment}}$$
If Claude has memorized a theorem, the Baseline arm will close it in turn 1 with minimal tokens, revealing that the theorem provides zero discriminative power between retrieval architectures.

#### 2. Challenge / Non-Triviality Pre-Filtering
Before freezing the 100-theorem benchmark, all candidate theorems undergo a **pre-screening pass with the Baseline agent**:
- **Discard Rule:** If the Baseline agent solves the theorem in 1 turn using standard default automation (`by auto`, `by simp`) with zero exploratory search, the theorem is flagged as trivialized/memorized and discarded.
- **Inclusion Criteria:** The benchmark retains only theorems where the Baseline agent requires non-trivial multi-step search, encounters backtracking, or fails outright.

#### 3. Isomorphic Semantic Perturbations & Novel Variations (Synthetic Theorems)
To evaluate proof synthesis on genuinely novel problems where LLM weight memorization is strictly neutralized, a designated subset of the benchmark (30%) consists of **isomorphically perturbed variants**:
- **Alpha-Renaming & Symbol Obfuscation:** Theorem and definition identifiers are systematically mapped to novel, out-of-distribution names (e.g., `set_mset` $\to$ `mset_elements`, `count` $\to$ `multiplicity`). While Isabelle's logical semantics are identical, Claude cannot pattern-match against memorized GitHub strings, forcing it to read and apply the retrieved premise types and rule directives.
- **Parametric & Compound Generalizations:** Composing consecutive lemmas into a single unproved composite lemma (e.g., $A \implies B$ and $B \implies C$ combined into $A \wedge D \implies C$), or specializing polymorphic theorems to custom inductive types defined within the session.

#### 4. Domain-Specific & Recent Session Prioritization
The benchmark prioritizes theories from recent AFP publications and specialized formalisms less prevalent in general pre-training corpora:
- `Aho_Corasick` (AFP 2026 release)
- `Featherweight_OCL` (formal object-oriented specification logic)
- Specialized balanced tree invariants in `AVL-Trees`
Theorems from core `HOL.thy` or elementary `List.thy` are avoided.

---

### 6.3 Stratified 100-Lemma Benchmark Suite

The final benchmark comprises **100 theorems stratified across three difficulty tiers**:

```
+-------------------------------------------------------------------------------+
|                      STRATIFIED BENCHMARK SUITE (100 THEOREMS)                |
+-------------------------------------------------------------------------------+
| Tier 1: Equational & Terminal Goals (35%)                                     |
| - Resolvable via term rewriting or algebraic decision procedures              |
| - Challenge: Finding exact rewrite rule [simp] without prompt context noise   |
| - Includes: 25 historical theorems + 10 alpha-perturbed novel variants        |
+-------------------------------------------------------------------------------+
| Tier 2: Inductive Lemmas (40%)                                                |
| - Requires structural induction on lists, trees, or recursive datatypes       |
| - Challenge: Identifying induction rule/variable & setting up case branches   |
| - Includes: 30 historical theorems + 10 compound/generalized variants         |
+-------------------------------------------------------------------------------+
| Tier 3: Multi-Step Structural & Bridging Theorems (25%)                       |
| - Complex Isar proofs involving invariant preservation, case splits, or OCL   |
| - Challenge: Long-horizon deductive roadmap and coupled tactic execution      |
| - Includes: 15 historical theorems + 10 novel composite proofs                |
+-------------------------------------------------------------------------------+
```

---

### 6.4 Strict Anti-Contamination (Temporal & Topological Masking)

During evaluation of each target theorem $T$:
1. **Self-Masking:** $T$ is strictly purged from the search index.
2. **Temporal / File-Precedence Masking:** Any theorem or lemma appearing *at or after* line $k$ in the same theory file is dynamically filtered out of candidate retrieval pools.
3. **Topological Masking:** No lemma that historically cites $T$ may be retrieved while proving $T$.

---

## 7. Interactive Agent Execution Loop

Each experimental trial executes according to the following standard state machine:

```
                          ┌───────────────────────────┐
                          │  Target Theorem Initialized│
                          │      in Isabelle REPL     │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │  PIDE Goal State Observed │
                          │       via Ir.state        │
                          └─────────────┬─────────────┘
                                        │
                 ┌──────────────────────┴──────────────────────┐
                 │                                             │
                 ▼                                             ▼
       [Arms 1 & 2: Query RAG]                      [Arm 0: Direct Generation]
       Retrieve Top-3 Lemmas                        No Retrieval
                 │                                             │
                 └──────────────────────┬──────────────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │    LLM Synthesizes Step   │
                          │   (Recorded: Prompt/Comp) │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │     Submit to Isabelle    │
                          │        via Ir.step        │
                          └─────────────┬─────────────┘
                                        │
                     ┌──────────────────┴──────────────────┐
                     │                                     │
           [Kernel Success]                          [Kernel Error]
                     │                                     │
            Check if Goal Closed?                  Record Error Event
           ┌─────────┴─────────┐                           │
           │                   │                           ▼
         [Yes]                [No]                 Backtrack / Retry Step
           │                   │                           │
           ▼                   ▼                           ▼
        Success!       Next Turn (Loop)          Check Budget Limit?
     Record Metrics                              (Max 15 Turns / 32k Tokens)
```

---

## 8. Telemetry & Output Data Schema

All trials will be executed on the **IME USP `deeptwelve`** compute server and recorded in structured JSON lines and Parquet format in `artifacts/experiment_results/`:

```json
{
  "trial_id": "trial_multiset_042_treatment",
  "arm": "il_treatment",
  "session": "HOL-Library",
  "theory": "HOL-Library.Multiset",
  "lemma_title": "HOL-Library.Multiset.count_inI",
  "difficulty_tier": "tier_1_terminal",
  "success": true,
  "total_tokens": 1420,
  "prompt_tokens": 1280,
  "completion_tokens": 140,
  "interaction_turns": 3,
  "error_count": 0,
  "elapsed_seconds": 4.12,
  "retrieved_lemmas": ["ccontr", "not_in_iff"],
  "cited_dependencies": ["ccontr", "not_in_iff"],
  "retrieval_utility": 1.0,
  "transcript": [
    {"turn": 1, "state": "goal (1 subgoal): 1. x ∈# M", "step": "proof (rule ccontr)", "status": "OK"},
    {"turn": 2, "state": "...", "step": "assume \"x ∉# M\" with assms", "status": "OK"},
    {"turn": 3, "state": "...", "step": "show False by (simp add: not_in_iff)", "status": "OK"}
  ]
}
```

---

## 9. Token Budget & Financial Cost Analysis ($20 Budget Fit)

### 9.1 Anthropic Model Cost Comparison

Anthropic frontier models evaluated against the 100-theorem $\times$ 3-arm benchmark (300 trials total):

| Model | Model ID | Input Rate ($/MTok) | Output Rate ($/MTok) | Expected Input (2.94 MTok) | Expected Output (0.12 MTok) | **Total Expected Cost** | Worst-Case Cap (All 15 Turns) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Sonnet 5** | `claude-sonnet-5` | **$2.00** | **$10.00** | **$5.88** | **$1.20** | **$7.08** | **$19.10** |
| **Opus 5** | `claude-opus-5` | $5.00 | $25.00 | $14.70 | $3.00 | $17.70 | $47.75 |
| **Fable 5.1** | `claude-fable-5-1` | $10.00 | $50.00 | $29.40 | $6.00 | $35.40 | $95.50 |

### 9.2 Model Selection Decision: `claude-sonnet-5`

- **Primary Driver:** **`claude-sonnet-5`** is selected as the primary evaluation model.
- **Budget Compliance:** At an expected total cost of **$7.08**, it comfortably clears the **$20.00 budget limit**, leaving **$12.92 in reserve** for pilot testing, retries, and prompt tuning.
- **Worst-Case Safety:** Even in the pathological event where all 300 trials hit the maximum 15-turn cap ($7.8 \text{ MTok in}, 0.35 \text{ MTok out}$), Sonnet 5 consumes **$19.10**, mathematically guaranteeing that the experiment will **never exceed the $20 budget**.
- **Dense Embedding Cost:** `voyage-code-3` querying (~60,000 query tokens across all runs) adds **< $0.01 USD**.
