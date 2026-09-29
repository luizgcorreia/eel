# Isabelle Lemma Aspect Schema: Expert Epistemic Model

## 1. Overview & Theoretical Foundation

In Isabelle/Landscape (I/L) and EDEL, formal mathematical entities (lemmas, theorems, and definitions) are projected into four semantic aspects forming an **epistemic trajectory** in concept space. Rather than a flat, undifferentiated concatenation of code text, the four aspects represent orthogonal epistemic dimensions of formal mathematical knowledge:

```
emb_P ──(D_pm)──► emb_M ──(D_mf)──► emb_F ──(D_fi)──► emb_I
  │                                                        │
  └────────────────── D_pi (epistemic closure) ────────────┘
```

The inferential trajectory traces the natural lifecycle of formal mathematical discovery:
$$\mathbf{P} \xrightarrow{\quad \text{Strategic Conception } (D_{pm}) \quad} \mathbf{M} \xrightarrow{\quad \text{Tactical Execution } (D_{mf}) \quad} \mathbf{F} \xrightarrow{\quad \text{Harvest \& Integration } (D_{fi}) \quad} \mathbf{I}$$

Each transition operator $D_{xy} = \|\mathbf{emb}_y - \mathbf{emb}_x\|$ quantifies semantic translation across reasoning boundaries:
- **$D_{pi}$ (Epistemic Closure / Implication Leap):** Distance from preconditions/hypotheses to consequent conclusion.
- **$D_{pm}$ (Strategy Formulation):** Divergence between assumed constraints and the high-level deductive architecture chosen to resolve them.
- **$D_{mf}$ (Automation Gap / Execution Detail):** Divergence between the strategic blueprint and concrete operational tactics.
- **$D_{fi}$ (Harvest Yield):** Translation from concrete tactical closure to final established mathematical fact.

---

## 2. The 80% Emptiness Flaw & The Expert Revision

### The Degeneracy Problem of the Legacy Model
In early formulations, Aspect 2 (`method`) strictly captured explicit declarative Isar keywords (`proof`, `qed`, `have`, `show`, `also`, `finally`). In modern interactive theorem proving archives (such as the Archive of Formal Proofs), approximately **75%–85% of lemmas are procedural apply-scripts or compressed one-liners** (`by simp`, `apply (induction xs) ...`). 

Consequently:
1. $\approx 80\%$ of lemmas had an empty `method` string (`""`), collapsing to zero vectors $\mathbf{0}$.
2. The epistemic tetrahedron collapsed into a 2-simplex:
   $$\mathbf{emb}_M = \mathbf{0} \implies D_{mf} = \|\mathbf{emb}_F\|$$
   The distance metric ceased to measure the gap between strategy and execution, becoming merely the norm of the tactic embedding.
3. Neural code models received empty strings for a core aspect, discarding structural reasoning patterns from one-liners.

### The Expert (Achim Brucker Perspective) Epistemic Invariant
From an expert proof engineer's perspective, **every proof embodies a strategic method**, regardless of syntactic style:
- `apply (induction xs) ... by auto` embodies the **exact same strategic architecture** as `proof (induction xs) ... qed`.
- `by (auto simp: algebra)` executes an **equational normalization / decision procedure** strategy.
- `by (meson ...)` executes a **first-order tableau / ATP refutation** strategy.

Under the Expert Model, **all four aspects are guaranteed 100% non-empty ($0\%$ emptiness)** and maintain distinct embeddings ($D_{xy} > 0$) across all formal entities.

---

## 3. The Four Expert Epistemic Aspects

```
+-------------------------------------------------------------------------------+
|                             ISABELLE LEMMA UNIT                               |
+-------------------------------------------------------------------------------+
                                        |
      +--------------------+------------+------------+--------------------+
      |                    |                         |                    |
      v                    v                         v                    v
+---------------+  +------------------+  +----------------------+  +---------------+
|   ASPECT 1    |  |     ASPECT 2     |  |       ASPECT 3       |  |   ASPECT 4    |
|    Problem    |  |      Method      |  |       Finding        |  |Interpretation|
+---------------+  +------------------+  +----------------------+  +---------------+
| - Hypotheses  |  | - Strategy Type  |  | - Coupled Step Map   |  | - Consequent  |
| - Sort bounds |  | - Major Inductor |  | - Claims & Goals     |  | - Attributes  |
| - Fixes/Vars  |  | - Decomposition  |  | - Tactics & Proof    |  | - Rule Class  |
| - Preconditions| | - Proof Roadmap  |  | - Cited Dependencies |  | - Locale/Cont.|
+---------------+  +------------------+  +----------------------+  +---------------+
```

---

### Aspect 1: `problem` ($P$) — Epistemic Antecedent & Domain Boundary

**Epistemic Role:** The antecedent conditions, variable bounds, and typed signatures necessary for the lemma to hold. Answers: *"Under what assumptions and domain constraints does this problem live?"*

**Dual-Backend Extraction:**
1. **PIDE Compiler Mapping (Native):**
   - Extracted from `Keyword.THY_GOAL` (`lemma`, `theorem`, `corollary`).
   - Evaluates `prop = Thm.prop_of(thm)`:
     - Hypotheses: `Logic.strip_horn(prop) |> fst` $\implies [A_1, \dots, A_k]$.
     - Variables & Sort Bounds: `Variable.dest_fixes(ctxt)` extracts fixed variables and sort bounds (e.g. `'a :: linorder`).
2. **I/R Regex Fallback (Legacy):**
   - String decomposition on `assumes ... shows` or top-level `⟹` with bracket-nesting parsing ([`_split_on_top_level_implies`](file:///home/correia/edel/edel/il/aspects.py#L101-L132)).

**Deterministic Behavior on Unconditional & Spec Entities:**
- **Conditional Theorems ($k \ge 1$):** Conjunction of all premises: $A_1 \land \dots \land A_k$ alongside `fixes` signatures.
- **Unconditional Rewrites ($k = 0$, $L = R$):** $P$ takes the unreduced Left-Hand Side ($L$).
- **Axioms & Definitions:** $P \equiv \text{statement}$ (Envelope leveled to `[Role: Statement]`).
- **Unconditional Facts ($k = 0$, non-equality):** Fixed point: $P \equiv \text{concl}$.

**Contextual Envelope Format:**
```text
[Theory: {theory}] [Locale: {locale}] [Role: Premises] [Types: {types}]
Lemma: {name} | Premises:
{P_content}
```

---

### Aspect 2: `method` ($M$) — Proof Architecture & Strategic Blueprint

**Epistemic Role:** The macroscopic proof architecture and reasoning paradigm. In category-theoretic terms, Method acts as the **morphism (arrow)** translating Problem into Interpretation:
$$P \xrightarrow{\quad M \quad} I$$
Answers: *"What high-level mathematical strategy decomposes and bridges this goal?"*

**The Dual Invariants of Method ($M$):**
1. **Domain Abstraction (Orthogonality to Finding):**  
   To enable cross-domain analogical proof transfer (e.g. applying a tree induction strategy to a network routing theorem), $M$ must be **strictly abstracted from domain-specific lemma citations**. Concrete cited theorems (`bot_option_def`, `StrictRefEq_def`, `Option.is_none_def`) belong strictly to Finding ($F$).
2. **Comparable Continuous Dimension (Balanced Shannon Entropy):**  
   Naive domain-stripping risks a dangerous degeneracy: collapsing proofs into a handful of coarse labels (e.g., 71 out of 210 lemmas sharing `[strategy: equational-normalization (simp)]`). This collapses Shannon entropy to $\mathcal{H} \approx 2.74$ bits, destroying the continuous vector field $\vec{v}(x)$ and collapsing the $M$ aspect subspace into discrete Dirac delta spikes.  
   **The Method aspect must achieve $\mathcal{H} \approx 7.0$ bits**—making it fully comparable to Problem ($\approx 7.4$ bits), Finding ($\approx 7.1$ bits), and Interpretation ($\approx 7.6$ bits)—by capturing rich domain-orthogonal structural proof information.

**Five Orthogonal Information Dimensions in Method ($M$):**
1. **Morphism Transformation Shape & Algebraic Reduction ($T_{\text{shape}}$):**  
   Category-theoretically, Method is the morphism $P \xrightarrow{M} I$. Without naming domain concepts, we classify the universal algebraic / logical nature of the transformation:
   - *Algebraic Operand Reductions:* `idempotent-absorption` ($x \star x = x$), `left-operand-absorption` ($x \star y = x$), `right-operand-absorption` ($x \star y = y$), `unary-fixed-point` ($f(x) = x$).
   - *Canonical Constant Collapses:* `unary-constant-absorption` (e.g. $f(c) = c'$), `binary-constant-collapse`, `constant-absorption` (reduction to canonical terminals like $\bot, \top, 0, \emptyset$, etc.).
   - *Structural Expansions & Complexity Deltas:* `conditional-branching-expansion` (`if-then-else`), `functional-lifting` ($\lambda$-abstraction), `term-compression` vs `term-expansion` (syntactic token complexity ratio).
   - *Deductive Shapes:* `implication-derivation`, `quantified-implication-derivation`, `logical-equivalence`, `disjunctive-case-split`.
2. **Composite Method Combinators in One-Liners (`by (m1, m2)`):**  
   In Isabelle, one-liners frequently execute sequential reductions (e.g. `by (rule ext, simp add: ...)`). Decomposing this into its explicit transition chain:  
   `[strategy: composite-one-liner (target: right-operand-absorption, rule:rule=ext ⟶ simp:unfolds: [7 definitions])]`  
   separates multi-stage deductive reductions from monolithic solver calls.
3. **Ontological Fact Categorization (Epistemic Debt Profile):**  
   Rather than citing domain names (which leaks into Finding) or stripping them (which destroys entropy), we classify the *nature of the unfolded epistemic background*:
   - Definitions count (`_def`, `.def`, `_defs`)
   - Recursive rewrite equations count (`.simps`, `_simps`)
   - General lemmas/theorems count  
   E.g., `unfolds: [7 definitions]`, `unfolds: [1 definitions, 2 lemmas]`.
4. **Definition Construction Architecture in Contextual Envelopes (Path C):**  
   For definitions, specifications, and datatypes, there is no proof trajectory. As conservative extensions ($c \equiv t$), they are **rigorous 0-simplices ($P \equiv M \equiv F \equiv I \equiv \text{statement}$)** with identically zero deductive displacement ($D_{pi} = 0, D_{mf} = 0, \operatorname{Vol}(\Delta) = 0$).  
   Rather than inflating definitions into artificial simplices, their mathematical construction traits are embedded into the **Contextual Envelope header**:
   - Function arity: `arity=1`, `arity=2`, `ground-constant`.
   - Structural traits: `higher-order-abstraction` ($\lambda$-lifting), `conditional-branching` (`if ... then ... else ...`).
   - E.g., `[Role: Statement] [Architecture: arity=1, higher-order-abstraction]`.
5. **Pipeline Depth & Isar Milestone Topology:**  
   - Procedural scripts: exact transformational pipeline depth ($k$-step apply chains).
   - Structured Isar: number of `case` partitions, `have` milestones, `obtain` witness instantiations.

**Empirical 4-Aspect Entropy Audit ($N = 210$, `Featherweight_OCL.UML_Logic`, Path C):**
$$\mathcal{H}(X) = -\sum_{i=1}^k p(x_i) \log_2 p(x_i), \quad \mathcal{H}_{\max} = \log_2(210) \approx 7.714 \text{ bits}$$

| Epistemic Aspect | Shannon Entropy $\mathcal{H}$ | % of Theoretical Max | Unique Classes | Max Frequency (Top Cluster) | Mathematical / Geometric Role |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Problem ($P$)** | **7.62 bits** | **98.8%** | **202 / 210** | **4 (1.9%)** | Antecedents + Def Statements (0% empty) |
| **Method ($M$, Naive)** | 2.74 bits | 35.5% | 23 / 210 | 71 (33.8%) | Generic Engine Only |
| **Method ($M$, Initial)** | 5.35 bits | 69.4% | 74 / 210 | 25 (11.9%) | Basic Rule Filtering |
| **Method ($M$, Path C)** | **6.96 bits** | **90.2%** | **145 / 210** | **5 (2.4%)** | **0 Domain Leaks in Proofs + 0-Simplex Defs** |
| **Finding ($F$)** | **7.09 bits** | **91.9%** | **162 / 210** | **7 (3.3%)** | Concrete Tactics & Citations + Def Statements |
| **Interpretation ($I$)** | **7.63 bits** | **98.9%** | **203 / 210** | **4 (1.9%)** | Consequents & Attributes + Def Statements |

*All four aspects are now balanced across a narrow band ($\approx 7.0 - 7.6$ bits), with normalized entropy all $\ge 90.2\%$ and top cluster concentration under $3.5\%$, preserving exact 0-simplices on definitions.*

**Contextual Envelope Format:**
```text
[Theory: {theory}] [Locale: {locale}] [Role: Strategy] [Rule: {rule_type}]
Lemma: {name} | Strategy:
{M_content}
```

---

### Aspect 3: `finding` ($F$) — Microscopic Execution Trace & Coupled Step Map

**Epistemic Role:** The concrete operational mechanics of the proof—coupling each intermediate claim to the exact tactic and lemmas that validated it. Answers: *"What exact tactic invocations and lemma citations discharged each subgoal?"*

**The Step Map Principle:**
Unlike $M$ (which is abstract and structural), $F$ is **grounded and operational**. It constructs a serialized **Coupled Step Map**:

$$\text{Step}_k = \langle \text{Command}_k, \text{CitedDependencies}_k \rangle$$

**Dual-Backend Extraction:**
1. **PIDE Compiler Mapping (Native):**
   - Extracted from `Keyword.PRF_SCRIPT` (`apply (...)`, `apply_end (...)`) and `Keyword.PRF_SOLVE` (`by (...)`, `done`).
   - **Compiler-Verified Citations:** Within each command span, PIDE inspects the `Markup_Tree` for `Markup.ENTITY(Markup.THEOREM, full_name)`. This captures **both explicitly written arguments and implicit theorems used by the simplifier or classical reasoner**.
2. **I/R Regex Fallback (Legacy):**
   - Extracts commands from `tactic_segments` and regex-parses `simp add:`, `using`, `rule` ([`_DEP_INTRODUCERS`](file:///home/correia/edel/edel/il/aspects.py#L23-L30)).

**Example Step Map:**
```text
Step 1: [action="apply (simp only: append_Nil)", deps=["HOL.List.append_Nil"]]
Step 2: [action="by (blast intro: list.induct)", deps=["HOL.List.list.induct"]]
```

**Contextual Envelope Format:**
```text
[Theory: {theory}] [Locale: {locale}] [Role: StepMap] [Rule: {rule_type}]
Lemma: {name} | StepMap:
{F_content}
```

---

### Aspect 4: `interpretation` ($I$) — Consequent, Attributes & Automation Role

**Epistemic Role:** The formal mathematical invariant established by the theorem, enriched with its operational role in Isabelle's automation engine. Answers: *"What new truth was established, and what automation rules did it activate?"*

**Dual-Backend Extraction:**
1. **PIDE Compiler Mapping (Native):**
   - **Target Consequent:** Evaluates `Logic.strip_horn(prop) |> snd` $\implies C$ (the atomic conclusion), or RHS for unconditional equality rewrites. All constants and types are fully qualified (e.g. `HOL.List.map`).
   - **Automation Directives:** Parsed from theorem attributes in the PIDE snapshot:
     - `[simp]`: Active term rewriting rule.
     - `[intro]`, `[intro!]`: Backward chaining rule.
     - `[elim]`, `[elim!]`: Context elimination rule.
     - `[dest]`: Forward deduction rule.
   - **Rule Classification:** `rule_type` (`induction_rule`, `simplification_rule`, `definition_rule`, `general_theorem`).
2. **I/R Regex Fallback (Legacy):**
   - Substring extraction following `shows` or RHS of `⟹`, paired with rule classification heuristics ([`classify_rule_type`](file:///home/correia/edel/edel/il/parser.py)).

**Contextual Envelope Format:**
```text
[Theory: {theory}] [Locale: {locale}] [Role: Conclusion] [Rule: {rule_type}] [Attributes: {attrs}]
Lemma: {name} | Conclusion:
{I_content}
```

---

## 4. Epistemic Closure Metric ($D_{pi} = \|\mathbf{emb}_I - \mathbf{emb}_P\|$)

The distance between Problem ($P$) and Interpretation ($I$) measures the **substantive deductive leap** accomplished by the proof:

$$D_{pi} = \|\mathbf{emb}_I - \mathbf{emb}_P\|$$

Under the Expert Epistemic Invariant, four distinct regimes are rigorously maintained:

| Class | Isabelle Construct | Mathematical Behavior | Epistemic Metric ($D_{pi}$) |
| :--- | :--- | :--- | :--- |
| **Axioms & Definitions** | `definition`, `fun`, `datatype`, `abbreviation` | $P \equiv I \equiv \text{statement}$ (both leveled to `[Role: Statement]`). | **$D_{pi} = 0$** (Strictly zero deductive displacement). |
| **Unconditional Facts** | `lemma "finite (UNIV :: 'a :: finite set)"` | $P = I = \text{statement}$ (differing only in `[Role: Premises]` vs `[Role: Conclusion]`). | **$D_{pi} \approx \epsilon$** (Near-zero displacement). |
| **Equational Rewrites** | `lemma rev_rev: "rev (rev xs) = xs"` | $P = \text{LHS}$, $I = \text{RHS}$ (unreduced term $\to$ canonical normal form). | **$D_{pi} = \|\mathbf{emb}_R - \mathbf{emb}_L\|$** (Simplification distance). |
| **Conditional Theorems** | `lemma "distinct (map fst xs) ⟹ ... = ..."` | $P = \text{Assumptions} \land \text{Fixes}$, $I = \text{Consequent}$. | **$D_{pi} = \|\mathbf{emb}_C - \mathbf{emb}_A\| \gg 0$** (Formal implication leap). |

---

## 5. Neural Embedding Safeguards (`voyage-code-3`)

Embedding formal proof fragments using general dense models requires specialized engineering to avoid vector space degeneracy:

### 1. The Token Starvation Problem
A raw proposition like `avl l` or `by auto` contains only 2 to 4 tokens. Code embedding models suffer representation collapse when given 3-token strings.

### 2. Contextual Envelopes
Every aspect is wrapped in a structured semantic envelope before embedding ([`format_aspect_with_metadata`](file:///home/correia/edel/edel/il/aspects.py#L533-L582)):

```text
[Theory: {theory}] [Locale: {locale}] [Role: {label}] [Rule: {rule_type}] [Attributes: {attributes}] [Types: {type_signature}]
Lemma: {title} | {label}:
{aspect_content}
```

This guarantees:
- Token count is lifted to $\ge 40$ tokens per aspect.
- Disambiguation: Two lemmas named `insert_def` in different theories (`Set` vs `Multiset` vs `RB_Tree`) inhabit distinct coordinates in embedding space.
- Simplex Non-Degeneracy: Because $M$ and $F$ have distinct semantic content (Strategy Paradigm vs Step Map) and distinct role headers (`[Role: Strategy]` vs `[Role: StepMap]`), **$D_{mf} > 0$ is strictly maintained across 100% of the archive**.

---

## 6. Summary Comparison: Legacy vs. Current I/R vs. Native PIDE

| Dimension | Legacy Model (Format A) | Current I/R Model (Format B) | Next-Gen PIDE Model (Format C) |
| :--- | :--- | :--- | :--- |
| **Aspect 1 (`problem`)** | Raw antecedent text string | Preserves types, sorts, eigenvariables | Kernel-decomposed `Logic.strip_horn` + `Variable.dest_fixes` |
| **Aspect 2 (`method`)** | Isar skeleton only ($\approx 80\%$ empty) | **0% empty.** Unified Isar roadmaps, apply strategies, one-liner paradigms ($\mathcal{H} \approx 2.7$ bits) | **0% empty, high-entropy structural blueprint ($\mathcal{H} > 5.3$ bits)**: Pure/HOL proof calculus rules (`ext`, `iffI`, `ccontr`), case-splits (`split: if_split`), unfold complexity, and Isar milestone topology |
| **Aspect 3 (`finding`)** | Uncoupled list of tactics | Coupled Step Map via regex token matching | Compiler-verified Step Map via `Markup.ENTITY(Markup.THEOREM)` |
| **Aspect 4 (`interpretation`)** | Raw consequent text string | Consequent + Rule Classification + Attributes (`[simp]`) | Fully qualified `Thm.prop_of` AST + Compiler attributes |
| **Simplex Non-Degeneracy** | $D_{mf} = \|\mathbf{emb}_F\|$ on $80\%$ of archive | $D_{mf} > 0$ strictly maintained | $D_{mf} > 0$ compiler-guaranteed |
| **Implicit Dependencies** | Completely lost | Lost behind `auto`/`simp` | **100% captured** via PIDE proof markup |
| **Eisbach Tactics** | Unrecognized | Classed as generic script | **Fully parsed** via formal method registry |
