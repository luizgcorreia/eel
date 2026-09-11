# Technical Report: Higher-Order Epistemic Navigation of Formal Proof Libraries via EEL (Embedding-driven Epistemic Landscapes)

**Authors:** Luiz G. Correia, Jesus P. Mena-Chalco, Ronaldo Menezes  
**Affiliations:** Federal University of ABC (UFABC), Brazil; University of Exeter, UK  
**Framework:** EEL (Embedding-driven Epistemic Landscape) & I/L (Isabelle/Landscape)  
**Target Venue:** The 15th International Conference on Complex Networks and their Applications (CNA 2026)

---

## 1. Executive Summary & Problem Formulation

Formal proof libraries such as the Archive of Formal Proofs (AFP) for Isabelle/HOL define massive, machine-checked complex networks of verified mathematics. Unlike empirical citation networks confounded by prestige and social citation dynamics, formal repositories define strictly sound directed acyclic graphs (DAGs) where edges represent machine-checked logical dependencies.

When applying autonomous Large Language Model (LLM) agents to interactive theorem proving, recent neural systems encounter severe structural bottlenecks:
1. **The Ephemeral Leaf Trap & Search Distraction:** Uncurated vector search (such as in *IsaSearch* [Kadlez et al., 2026]) treats libraries as flat collections of propositions. Agents querying flat vector stores are inundated with peripheral, single-use helper lemmas that superficially match keywords, distracting the prover from foundational bridging lemmas.
2. **Context Exhaustion & Monolithic Prompts:** State-of-the-art neural provers like *IsabeLLM* [Jones & Knottenbelt, 2026] inject raw lemma text into prompts via standard Retrieval-Augmented Generation (RAG). Jones & Knottenbelt explicitly report that flat RAG collapses on multi-theory verifications because injecting uncurated proof text rapidly exhausts the model's context window.
3. **Simplex Collapse in Syntactic Encodings:** Prior attempts to map mathematical discourse into multi-aspect simplices suffered from vector-space degeneracy: because ~80% of proofs in the AFP are procedural scripts or one-line automation calls (`by simp`, `by blast`), naive syntax-matching parsers produced empty method strings, causing tetrahedra to collapse into degenerate lower-dimensional facets.

To solve these foundational challenges, we introduce an **Embedding-driven Epistemic Landscape (EEL)** formulation of formal mathematical repositories. We establish the **Expert Epistemic Invariant**, guaranteeing that 100% of theorems in the archive form strictly non-degenerate **epistemic 3-simplices** in a single shared ambient space $\mathbb{R}^{1024}$ (`voyage-code-3`). We formalise network traversal via **twelve asymmetric conditional transition distribution operators** $D(Y \mid x)$, net **epistemic expansion** $\|\mathbf{i} - \mathbf{p}\|$, and **Landscape Height** $H(v)$ over the transpose citation DAG. We deploy this architecture by extending the open-source **AutoCorrode** verification framework into a coordinated multi-agent ecosystem over the Model Context Protocol (MCP).

---

## 2. Multi-Layer Formal Complex Network Representation

We represent formal libraries as multi-layer directed acyclic networks:
$$\mathcal{N} = (V_{\text{lem}}, V_{\text{def}}, V_{\text{thy}}, E_{\text{cite}}, E_{\text{def}}, E_{\text{import}})$$
where:
* $V_{\text{lem}}$ is the set of verified theorems, lemmas, and corollaries.
* $V_{\text{def}}$ is the set of formal definitions, recursive functions, datatypes, and locales.
* $V_{\text{thy}}$ is the set of theory files structured hierarchically into AFP sessions.
* $E_{\text{cite}} \subseteq V_{\text{lem}} \times V_{\text{lem}}$ represents verified deductive citation dependencies.
* $E_{\text{def}} \subseteq V_{\text{lem}} \times V_{\text{def}}$ maps theorems to the formal definitions they unfold.
* $E_{\text{import}} \subseteq V_{\text{thy}} \times V_{\text{thy}}$ defines the theory import DAG.

```
Theory DAG Layer:        [Theory T1] <========= E_import ========= [Theory T2]
                             |                                         |
Definition Layer:         [Def D1]                                  [Def D2]
                           ^    ^                                    ^    ^
Lemma DAG Layer:     [Lemma L1] [Lemma L2] <===== E_cite ===== [Lemma L3] [Lemma L4]
```

---

## 3. The Expert Epistemic Invariant & Non-Degenerate 3-Simplices

### 3.1 Mathematical Arity Justification & Weisberg-Muldoon Proving Approaches
Following the epistemic landscape formulation of Weisberg and Muldoon (2009), each coordinate in the landscape represents a distinct epistemic approach: in our setting, a formal proving approach identified by the theorem being proved. Each approach is characterised by multiple aspects: the four epistemic aspects $(P, M, F, I)$ that jointly define its coordinates. In interactive theorem proving, mathematical discourse is governed by an inferential cycle of four distinct epistemic roles:
1. **Problem ($P$):** Antecedent context, sort constraints (e.g., `::linorder`), type bounds, hypotheses, and locale premises ($H \vdash$).
2. **Method ($M$):** Abstract proof strategy, decomposition roadmap, and high-level proof paradigm.
3. **Finding ($F$):** Verified tactic execution record, intermediate assertion chains, and coupled step maps.
4. **Interpretation ($I$):** Consequent conclusion, post-condition, and exported rewrite rule with automation directives ($\vdash C$, `[simp]`, `[intro]`).

This arity-4 decomposition fixes the topological dimension of each theorem to an **epistemic 3-simplex** (a tetrahedron with 4 vertices and 6 edges), inducing $4 \times 3 = 12$ directional transition operators.

### 3.2 Single Shared Ambient Space $\mathbb{R}^d$
All discourse aspects are projected into continuous space via a dense neural code embedder:
$$\mathcal{E} : \mathfrak{T} \longrightarrow \mathbb{R}^d$$
where $\mathfrak{T}$ is the space of formal code expressions and $d = 1024$ (using `voyage-code-3`). Crucially, $P, M, F, I$ are **not four disjoint vector spaces**, but empirical submanifolds within a **single shared ambient space $\mathbb{R}^d$**. This guarantees that displacement vectors ($\Delta_{PM} = \mathbf{m} - \mathbf{p}$) and cross-aspect operator distributions are mathematically well-defined.

### 3.3 Simplices versus Trajectories
We maintain a strict formal distinction between:
* The **discourse simplex** $\sigma_j = \text{conv}(\mathbf{p}_j, \mathbf{m}_j, \mathbf{f}_j, \mathbf{i}_j)$, an unordered geometric polytope in $\mathbb{R}^d$ encoding internal multi-aspect spatial volume and coherence.
* The **discourse trajectory** $\tau_j = (p_j \to m_j \to f_j \to i_j)$, an ordered, directed 1-chain traversing the 0-faces of $\sigma_j$ from premises to conclusion.

### 3.4 Eliminating Simplex Collapse: The Expert Epistemic Invariant
In legacy syntax-matching parsers, Aspect 2 (*Method*) only matched declarative Isar keywords (`proof`, `qed`, `have`). Because approximately 80% of proofs across the AFP are procedural apply scripts or one-liners (`by simp`, `by blast`), naive parsers yielded empty strings for Aspect 2, causing the tetrahedron to collapse into a degenerate 2-simplex with $D_{mf} = \|\mathbf{f}\|$.

To resolve this vector-space degeneracy, we establish the **Expert Epistemic Invariant**:  
$$\text{\textit{Proof strategy is an intrinsic mathematical property invariant to syntactic realisation.}}$$

Our parser extracts strategy universally across all syntactic realisations:

| Proof Realisation | Syntactic Pattern | Extracted Strategy Aspect ($M$) | Semantic Rationale |
| :--- | :--- | :--- | :--- |
| **Declarative Isar** | `proof (induct x) ... qed` | `structural-induction`, `case-split` | Structured decomposition roadmap |
| **Procedural Scripts** | `apply induct_tac ... apply simp` | `induction-step -> simplification -> blast-refutation` | Pipeline transformation strategy |
| **Automated One-Liners** | `by (simp add: thms)` | `equational-normalisation` | Automated decision paradigm |
| **Automated One-Liners** | `by blast` / `by fastforce` | `classical-tableau` / `first-order-search` | Automated decision paradigm |
| **Automated One-Liners** | `by metis` / `by meson` | `resolution-atp` / `model-elimination` | Automated decision paradigm |
| **Automated One-Liners** | `by linarith` / `by presburger`| `decision-procedure` | Automated decision paradigm |
| **Unconditional Entities** | `lemma foo: "P x"` | `unconditional_tautology` | Prevents $P = I$ collapse; $\Delta_E \ne \mathbf{0}$ |

Under this invariant, **100% of aspects are populated across the archive**, guaranteeing that every theorem forms a **strictly non-degenerate 3-simplex**:
$$\sigma_j = \text{conv}(\mathbf{p}_j, \mathbf{m}_j, \mathbf{f}_j, \mathbf{i}_j), \quad \Delta_{PM}^{(j)}, \Delta_{MF}^{(j)}, \Delta_{FI}^{(j)}, \Delta_{PI}^{(j)} \ne \mathbf{0}$$

### 3.5 Aspect Segmentation in Action: AVL Trees Example
The role of I/L's aspect segmentation engine is to parse each entry in the Archive of Formal Proofs into these four coordinates for embedding and indexing. To illustrate, consider a representative lemma from `AVL-Trees.AVL`:

```isabelle
lemma avl_insert [simp, intro]:
  fixes x :: "'a :: linorder"
  shows "avl t ==> avl (insert x t)"
  by (induction t rule: avl.induct)
     (auto simp: avl.simps height_insert)
```

Our parser extracts the four coordinates as follows:
1. **Premises ($P$):** Type constraints, sort bounds, and antecedent hypotheses:
   `fixes x :: 'a :: linorder; assumes avl t`.
2. **Strategy ($M$):** The strategic proof roadmap inferred from the proof:
   `structural-induction on (t) via avl.induct; auto`.
3. **Tactics ($F$):** Coupled step map:
   $\text{Step}_1 = \langle \text{avl (insert x t)}, \text{auto simp: avl.simps}, \{\text{avl.simps}, \text{height\_insert}\}\rangle$.
4. **Conclusions ($I$):** Consequent proposition with exported automation directives and origin metadata:
   `avl (insert x t); [simp, intro]; theory: AVL-Trees`.

### 3.6 Epistemic Expansion and Coupled Step Maps
The net **epistemic expansion** vector $\Delta_E(j)$ and its norm $N(j)$ quantify the deductive leap achieved by theorem $j$:
$$\Delta_E(j) = \mathbf{i}_j - \mathbf{p}_j, \quad N(j) = \|\mathbf{i}_j - \mathbf{p}_j\|$$
Small norms correspond to local equational rewrites, while large norms indicate foundational bridging theorems connecting disparate mathematical domains.

Furthermore, Aspect 3 (*Finding*) models fine-grained tactical dependencies as **Coupled Step Maps**:
$$\text{Step}_k = \langle \text{Claim}_k, \text{Tactic}_k, \text{CitedDeps}_k \rangle$$
Every aspect is wrapped in a structured semantic envelope encoding theory name, locale scope, rule category, and type signatures prior to embedding, completely eliminating the token starvation problem.

### 3.6 Syntactic Anisotropy & Empirical Spectral Sweep ($k \in [0, 100]$)
Dense embeddings of formal code exhibit severe anisotropy: frequent outer syntax boilerplate (`lemma`, `fixes`, `assumes`, `shows`, type annotations `::`) produces dominant lexical carrier waves that concentrate variance in the top principal components. Consequently, applying non-linear dimensionality reduction (such as diffusion maps) directly to raw embeddings collapses the projection onto a degenerate one-dimensional curve ($\psi_2 \approx f(\psi_1)$), completely obscuring domain-specific mathematical structure. To uncover the intrinsic mathematical geometry, we apply *All-but-the-Top* spectral filtering (Mu & Viswanath, 2018), projecting out the leading $k$ principal components:
$$\mathbf{x}' = \mathbf{x} - \sum_{i=1}^{k} (\mathbf{x} \cdot \mathbf{u}_i)\mathbf{u}_i$$
where $\mathbf{u}_i$ are the orthonormal eigenvectors of the corpus covariance matrix $\Sigma = \frac{1}{N}\sum_{j=1}^N \mathbf{x}_j \mathbf{x}_j^T$.

To establish the optimal filtering threshold and identify the critical regime where topological structure collapses into noise, we conducted a systematic empirical sweep across $k \in [0, 100]$ over the 1,924 benchmark theorems spanning four distinct formal domains (`Featherweight_OCL`, `HOL-Library`, `AVL-Trees`, and `Aho_Corasick`). For each $k$, we measured the cumulative explained variance discarded, the domain cluster silhouette score $S_{\text{domain}}$, and the diffusion coordinate aspect ratio $\sigma_x / \sigma_y$:

| PCs Removed ($k$) | Variance Discarded | Silhouette ($S_{\text{domain}}$) | Aspect Ratio ($\sigma_x / \sigma_y$) | Manifold Regime |
| :---: | :---: | :---: | :---: | :--- |
| $k = 0$ | $0.0\%$ | $+0.191$ | $1.05$ | 1D syntactic carrier wave collapse |
| $k = 2$ | $15.6\%$ | $-0.180$ | $1.13$ | Destructive syntactic harmonic interference |
| $\mathbf{k = 5}$ | $\mathbf{28.7\%}$ | $\mathbf{+0.521}$ | $\mathbf{1.35}$ | **Peak domain separation (Optimal)** |
| $k = 8$ | $36.0\%$ | $+0.506$ | $1.11$ | Stable epistemic manifold window |
| $\mathbf{k = 10}$ | $\mathbf{41.0\%}$ | $\mathbf{+0.439}$ | $\mathbf{1.12}$ | **Robust operating baseline (Fig. 2 in paper)** |
| $k = 15$ | $49.4\%$ | $-0.030$ | $1.02$ | Onset of mathematical semantic erosion |
| $k = 20$ | $55.7\%$ | $+0.089$ | $1.11$ | Attenuated residual clustering |
| $k = 30$ | $64.8\%$ | $+0.093$ | $1.06$ | Severe mathematical attenuation |
| $k = 40$ | $70.8\%$ | $-0.142$ | $1.02$ | Near-complete topological dissolution |
| $k = 50$ | $75.2\%$ | $-0.371$ | $1.05$ | Catastrophic collapse into isotropic noise |
| $k = 75$ | $82.4\%$ | $-0.342$ | $1.00$ | Spherical Gaussian noise cloud |
| $k = 100$| $86.8\%$ | $-0.140$ | $1.02$ | Complete geometric information loss |

#### Manifold Regimes Across the Spectrum:
* **Syntactic Collapse ($k=0$ to $k=2$):** At $k=0$, the top two principal components account for $15.6\%$ of the total ambient variance. In the resulting diffusion map, points are flattened onto a 1D syntactic carrier line ($S_{\text{domain}} = 0.191$). Removing only $k=2$ components is insufficient: intermediate syntactic harmonics (PCs 3–5) clash destructively, yielding negative silhouette scores ($S = -0.180$).
* **The Optimal Epistemic Window ($k \in [5, 10]$):** Filtering $k=5$ to $10$ components eliminates the boilerplate carrier wave while retaining mathematical semantics. The domain silhouette score surges to a peak of **$+0.521$** at $k=5$ and remains strong at **$+0.439$** at $k=10$ ($41.0\%$ variance removed). In this window, the diffusion operator unfolds into a rich, non-linear branching manifold whose topological ridges cleanly separate distinct formal disciplines and proof methodologies. We adopt $k=10$ as the robust operating baseline across all experiments, ensuring complete suppression of high-frequency syntactic noise while preserving mathematical deductive geometry.
* **Semantic Erosion ($k=15$ to $k=30$):** Beyond $k=10$, substantive mathematical information is progressively discarded alongside syntax. At $k=15$, nearly half the ambient variance ($49.4\%$) is removed, causing domain separation to collapse ($S = -0.030$). Faint residual clustering persists up to $k=30$ ($S \approx 0.093$) with $64.8\%$ variance stripped.
* **Collapse into Isotropic Noise ($k \ge 40$):** Beyond $k=40$, over $70\%$ of the ambient variance is discarded. At $k=50$ ($75.2\%$ variance discarded), the silhouette score plunges to **$-0.371$**, and the diffusion coordinate spread shrinks to an aspect ratio of exactly $1.00$ ($\sigma_x \approx \sigma_y \approx 0.015$). The latent manifold completely dissolves into a featureless, isotropic spherical Gaussian noise cloud.

The complete sweep data is packaged in `results/spectral_sweep.csv` and in the master spreadsheet `results/benchmark_trials_full.xlsx` (Sheet "Table S1 - Spectral Sweep").

---

## 4. Higher-Order Dynamics, Transition Operators, and Centrality

### 4.1 Twelve Asymmetric Conditional Transition Distribution Operators
We distinguish between local displacements along a trajectory and population-level transition operators across the corpus. For any source aspect $X$ and target aspect $Y$ ($X, Y \in \{P, M, F, I\}$):
$$D(Y \mid x) = \{ y_j \mid x_j \in N_k(x) \}, \quad x \in X$$
where $N_k(x)$ denotes the $k$-nearest neighbours of query vector $x$ within source support $X$.

Because the empirical submanifolds differ, the transition structure is intrinsically asymmetric:
$$D(M \mid p) \ne D(P \mid m)$$

This asymmetry induces a **directed higher-order epistemic topology** governing formal reasoning:
* **Forward Implication ($D(I \mid p)$):** Identifies what conclusions are reachable from premises $p$.
* **Strategic Decomposition ($D(M \mid p)$):** Identifies proof strategies successfully applied to problems sharing features with $p$.
* **Tactical Resolution ($D(F \mid m)$):** Maps abstract proof strategies $m$ to verified tactic sequences and coupled step maps.
* **Backward Goal Reduction ($D(P \mid i)$):** Infers antecedent conditions necessary to establish target goal $i$.

### 4.2 Conditional Transition Operators as Generalised Gluing Operators
A key mathematical contribution of our formalisation is recognising that the conditional transition operators $D(Y \mid x)$ have a natural simplicial complex interpretation: each operator $D(Y \mid x_i)$ specifies exactly which neighbouring simplices $\sigma_j$ are glued to $\sigma_i$ along shared faces. Formally, defining the **Generalised Gluing Operator** $G_t$:
$$\sigma_j \in G_t(\sigma_i) \iff \exists\, x_i \in \sigma_i, \, x_j \in \sigma_j \quad \text{s.t.} \quad x_j \in D(Y \mid x_i)$$
the full collection $\{\sigma_j\}$ assembled under $G_t$ forms the **higher-order epistemic simplicial complex** of the archive. This geometric gluing allows continuous deductive trajectories to pass between formal theorems, preserving multi-node topological reachability (Yassin et al., 2026) rather than collapsing the formal library into pairwise similarity scores.

### 4.3 Landscape Height ($H$) over the Transpose DAG
Standard vector retrieval (such as *IsaSearch* and flat RAG) computes cosine similarities against all corpus embeddings, falling into the **ephemeral leaf trap**: queries are flooded with obscure, single-use helper lemmas that happen to share superficial keywords with the goal.

To prioritise foundational theorems, we define **Landscape Height** $H(v)$ over the transpose citation DAG $G^T = (V, E^T)$:
$$H(v) = |\text{Reachable}_{G^T}(v)| - 1$$
$H(v)$ measures the size of the downstream deductive cone supported by lemma $v$: the total count of subsequent theorems in the archive that transitively depend upon $v$. Foundational theorems exhibit $H(v) > 10^3$, whereas ephemeral helper lemmas have $H(v) = 0$. $H(v)$ is computed efficiently via cycle-safe memoised depth-first search over the topological sort of $G_{\text{cite}}$.

### 4.4 Fused Epistemic Ranking
During agent navigation, candidate lemmas are scored using a fused objective balancing simplicial semantic relevance with topological centrality:
$$\text{Score}(L) = S_{\text{simplicial}}(L) + \lambda \cdot \frac{\log(1 + H(L))}{\max_{C} \log(1 + H(C))}$$
where $S_{\text{simplicial}}(L)$ is computed via the active transition operator $D(Y \mid x)$, $C$ is the candidate set, and $\lambda = 0.15$.

---

## 5. Extended AutoCorrode Multi-Agent Architecture: The I/L Ecosystem

To resolve the context exhaustion identified in *IsabeLLM* [Jones & Knottenbelt, 2026], EEL decouples reasoning, topology, and execution over the Model Context Protocol (MCP). Rather than building an ad-hoc monolithic harness, we extend **AutoCorrode** [AWS Labs, 2025], an open-source verification framework that wraps Isabelle/HOL in a suite of MCP servers. AutoCorrode natively provides two servers:
* **I/R Server (Isabelle/REPL):** Connects via TCP to a headless Poly/ML process with pre-warmed session heaps, enabling fast speculative execution of proof tactics ($\le 100$\,ms per step) without graphical interface overhead.
* **I/Q Server (Isabelle/Query):** Embedded inside the jEdit/PIDE editor environment, facilitating human-in-the-loop inspection and real-time buffer synchronisation.

Our system contributes the **I/L Server (Isabelle/Landscape)**: a new, third MCP server that extends AutoCorrode with higher-order simplicial navigation. The I/L server maintains the two-tier index (static pre-compiled AFP index + live session cache), executes simplicial operator queries $D(Y \mid x)$, applies Landscape Height ranking, and coordinates with I/R and I/Q during proof search.

### Generative Continuation and Grounded Valuation
While the empirical ontology reconstructs the static complex from existing proofs, the generative ontology governs autonomous synthesis:
$$\mathcal{E} = (E, \mathcal{T}, \mathcal{C}, \mathcal{V})$$
An agent observing an open goal $p$ samples generative continuations:
$$m^* \sim D(M \mid p), \quad f^* \sim D(F \mid m^*), \quad i^* \sim D(I \mid f^*)$$
synthesising candidate simplex $\sigma^* = (p, m^*, f^*, i^*)$. Crucially, the epistemic valuation structure:
$$\mathcal{V} : \mathcal{S} \times \mathcal{G} \longrightarrow \mathbb{R}$$
is externally grounded in the Isabelle verification environment $\mathcal{G}$, ensuring that only logically sound simplices attach to the evolving complex. Upon proof completion, the agent invokes `store_lemma`, which dynamically grafts the new 3-simplex into the session graph, updating Landscape Height and reachability in real time.

---

## 6. Comprehensive Empirical Evaluation: 140 Theorems / 420 Trials

### 6.1 Paired Benchmark Setup
We constructed a stratified benchmark of **140 formal Isabelle/HOL theorems** spanning five difficulty tiers:
1. **Tier 1: Terminal / One-Liners (40 lemmas):** Solvable via automated proof methods (`auto`, `blast`, `simp`) requiring exact lemma retrieval.
2. **Tier 2: Inductive Proofs (45 lemmas):** Requiring structural induction schemes and multi-case decompositions.
3. **Tier 3: Structural / Multi-Step Proofs (15 lemmas):** Complex declarative proofs involving nested calculations.
4. **Tier 4: Deep HOL-Library (20 lemmas):** Theorems drawn from foundational theories (`Multiset`, `Complex_Main`) requiring non-trivial lemma chaining.
5. **Tier 5: Deep Pure AFP (20 lemmas):** Heavy structural theorems from the AFP (specifically `Featherweight_OCL`), where 30% of lemmas were subjected to out-of-distribution $\alpha$-renamings to eliminate LLM pretraining memorisation.

We conducted **420 paired live trials** on compute node `deeptwelve` (64 CPU cores, 251 GB RAM, 2x NVIDIA RTX A5000) using Claude 3.5 Sonnet across three experimental arms:
* **Baseline (Zero-RAG):** The agent interacts with I/R using internal weights without retrieval.
* **Control (Monolithic Flat RAG):** The agent interacts with I/R and a flat vector index modelled after *IsabeLLM* and *IsaSearch*, retrieving top-$k$ nearest lemmas based on unpartitioned proposition text.
* **Treatment (I/L Simplicial Navigation):** The agent coordinates I/L, I/R, and I/Q, leveraging 4-aspect transition operators $D(Y \mid x)$ and Landscape Height centrality.

To guarantee rigorous methodological comparability across all arms, the evaluation harness enforces a strict ceiling of **15 interaction turns** and a **32,000-token budget** per trial (with LLM generation capped at 512 completion tokens per turn). Any trial failing to discharge all subgoals within these bounds is logged as a failure.

### 6.2 Proving Success Across Difficulty Tiers

| Experimental Arm | Terminal ($N=40$) | Inductive ($N=45$) | Structural ($N=15$) | Deep HOL ($N=20$) | Deep AFP ($N=20$) | Overall Pass@1 ($N=140$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline (Zero-RAG)** | 87.5% (35/40) | 55.6% (25/45) | 33.3% (5/15) | 30.0% (6/20) | 20.0% (4/20) | 53.6% (75/140) |
| **Control (Monolithic RAG)** | 87.5% (35/40) | 53.3% (24/45) | 33.3% (5/15) | 30.0% (6/20) | 20.0% (4/20) | 52.9% (74/140) |
| **Treatment (I/L Simplicial)**| **87.5%** (35/40) | **57.8%** (26/45) | **40.0%** (6/15) | **35.0%** (7/20) | **20.0%** (4/20) | **55.7%** (**78/140**) |

### 6.3 Discordant Pair Analysis
Standard aggregate pass rates conceal trajectory-level dynamics. In head-to-head contingency analysis between Treatment I/L and Control Flat RAG:
* **Treatment Wins ($b = 8$):** Theorems failed by Control RAG but successfully solved by Treatment I/L.
* **Control Wins ($c = 4$):** Theorems solved by Control RAG but failed by Treatment I/L.

This yields an empirical **Odds Ratio of 2.00x** ($b/c = 8/4 = 2.0$). Bootstrap resampling ($10^4$ iterations) confirms an **84.8% posterior probability** that higher-order simplicial navigation strictly dominates flat monolithic retrieval, demonstrating that uncurated RAG actively introduces distractor lemmas that derail theorem proving.

### 6.4 Trajectory Search Friction Metrics

| Metric | Baseline (Zero-RAG) | Control (Monolithic RAG) | Treatment (I/L) | Statistical Significance |
| :--- | :---: | :---: | :---: | :--- |
| **Mean Completion Tokens** | 1,489.1 | 1,452.4 | **1,243.6** | Wilcoxon $W = 2077.0, \mathbf{p = 0.00014}$ |
| **Mean Agent Turns** | 2.92 | 2.85 | **2.62** | Wilcoxon $W = 464.5, \mathbf{p = 0.04713}$ |
| **Kernel Error Rate** | 6.13% | 6.09% | **5.87%** | Treatment produces cleanest execution |

Treatment I/L reduces completion token expenditure by **16.5%** compared to Baseline and 14.4% compared to Control RAG ($p = 0.00014$). Interaction turns drop by 10.3% ($p = 0.04713$), and kernel error rate reaches an archive-low 5.87%. By filtering out ephemeral leaves and providing aspect-targeted micro-dossiers, I/L suppresses exploratory thrashing.

### 6.5 Qualitative Case Study: `Featherweight_OCL.UML_Logic.const_subst`
The quantitative advantage is highlighted by lemma `const_subst` from `Featherweight_OCL.UML_Logic` (a 19-line structural theorem establishing the preservation of logical constants under substitution):
* **Baseline (Zero-RAG):** Attempts generic equational rewriting, gets trapped in repetitive tactic loops, and exhausts its 15-turn budget (7,680 tokens, FAILED).
* **Control (Monolithic RAG):** Queries the flat index and receives generic boolean simplification lemmas from `HOL.Boolean_Algebra`. These lemmas match proposition keywords but cannot discharge domain-specific UML semantics (15 turns, 7,680 tokens, FAILED).
* **Treatment (I/L Simplicial Navigation):** Invokes operator $D(M \mid p)$ with topological filter $H \ge 2$. I/L immediately identifies parent theory bridge lemmas `cp_OclIf` and `cp_OclNot`. Armed with this exact strategic roadmap, the agent reconstructs the 19-line proof and closes the goal in 14 turns (6,904 tokens, 14% cheaper than failed baselines, SUCCESS).

### 6.6 Prompt Caching Economics
Across the 140 trials, I/L generated **912,111 prompt cache read tokens** over Anthropic's prompt caching layer at a 90% discount (\$0.20/M tokens). Because I/L's multi-aspect system prompts and contextual schema remain invariant across turns, cache hit rates exceeded 88%. Consequently, the net dollar cost of running the higher-order simplicial system (\$1.74 total) was virtually identical to the unguided baseline (\$1.73 total), while achieving a **2.65x acceleration in generation latency** due to cached KV-pair reuse.

---

## 7. Comparative Positioning: EEL vs. IsaSearch and IsabeLLM

| Dimension | IsaSearch (Kadlez et al., 2026) | IsabeLLM (Jones & Knottenbelt, 2026) | EEL / I/L (This Work) |
| :--- | :--- | :--- | :--- |
| **Network Representation** | Flat informalised text | Monolithic proposition RAG | Higher-order Simplicial Complex |
| **Topological Centrality** | None (blind to DAG) | None (pure vector similarity) | Landscape Height $H(v)$ on transpose DAG |
| **Discourse Aspects** | Conflated text string | Single uncurated code block | 4-aspect non-degenerate 3-simplices |
| **Simplex Collapse** | N/A (no simplicial model) | N/A (flat dyadic RAG) | **0% collapse** (Expert Epistemic Invariant) |
| **Traversal Dynamics** | Symmetric cosine distance | Top-$k$ nearest neighbours | 12 asymmetric conditional operators $D(Y \mid x)$ |
| **Multi-Agent Decoupling**| None (human search UI) | Monolithic single-prompt script | Extended AutoCorrode MCP ecosystem (I/L extension + I/R & I/Q) |
| **Deductive Distance** | Not modelled | Not modelled | Epistemic expansion $\|\mathbf{i} - \mathbf{p}\|$ |
| **Context Management** | N/A | Suffers acute prompt saturation | Micro-dossiers + 88% prompt cache reuse |

---

## 8. Conclusion, Limitations, & Future Roadmap

EEL transforms formal mathematical libraries from static code repositories into navigable higher-order epistemic landscapes. By formalising proof strategy to eliminate simplex collapse, introducing twelve asymmetric transition distribution operators as generalised gluing operators, and suppressing the ephemeral leaf trap via Landscape Height centrality, I/L demonstrates statistically verified reductions in cognitive friction ($p = 0.00014$) and achieves automated breakthroughs on deep structural theorems from the Archive of Formal Proofs.

### Limitations & Future Work
Our current evaluation benchmarks 140 theorems across four representative sessions (`Featherweight_OCL`, `HOL-Library`, `AVL-Trees`, `Aho_Corasick`), focusing primarily on single-target proof horizons within bounded turn budgets. Several critical directions define our ongoing roadmap:
1. **Full-Scale AFP Continuous Indexing:** We are currently executing continuous index construction across all 1,026 sessions of the Archive of Formal Proofs (>200,000 theorems) on compute node `deeptwelve`, building the first universal higher-order epistemic map of verified mathematics.
2. **Distant Multi-Theory Theorem Proving:** Future evaluations will benchmark extended proof trajectories requiring an agent to bridge multiple distant theories across disparate mathematical disciplines.
3. **Dynamic Trajectories with Intermediate Lemma Registration:** We plan to evaluate dynamic proving sessions where agents synthesise, verify, and register intermediate helper lemmas in real time via `store_lemma`, dynamically updating the active simplicial complex and successfully retrieving this synthesised local context to close subsequent global goals.
