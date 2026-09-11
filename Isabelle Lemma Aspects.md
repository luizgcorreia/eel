# Isabelle Lemma Aspect Schema: Expert Epistemic Model

## 1. Overview & Theoretical Foundation

In Isabelle/Landscape (I/L) and EDEL, formal mathematical entities (lemmas, theorems, and definitions) are projected into four semantic aspects forming an **epistemic trajectory** in semantic concept space. Rather than a flat, undifferentiated concatenation of text, the four aspects represent orthogonal epistemic dimensions of formal mathematical knowledge:

```
emb_P ──(D_pm)──► emb_M ──(D_mf)──► emb_F ──(D_fi)──► emb_I
  │                                                        │
  └────────────────── D_pi (epistemic closure) ────────────┘
```

Each transition operator $D_{xy} = \|\mathbf{emb}_y - \mathbf{emb}_x\|$ quantifies semantic translation across reasoning boundaries:
- **$D_{pi}$ (Epistemic Closure / Implication Leap):** Distance from premises/hypotheses to consequent conclusion.
- **$D_{pm}$ (Strategy Formulation):** Divergence between assumed constraints and the high-level deductive architecture chosen to resolve them.
- **$D_{mf}$ (Automation Gap / Execution Detail):** Divergence between the strategic architecture and concrete operational tactics.
- **$D_{fi}$ (Harvest Yield):** Translation from concrete tactical closure to final established mathematical fact.

---

## 2. The 80% Emptiness Flaw & The Expert Revision

### The Degeneracy Problem of the Legacy Model
In the legacy formulation, Aspect 2 (`method`) strictly captured explicit declarative Isar keywords (`proof`, `qed`, `have`, `show`, `also`, `finally`). In modern interactive theorem proving archives (such as the Archive of Formal Proofs), approximately **75%–85% of lemmas are procedural apply-scripts or compressed one-liners** (`by simp`, `apply (induction xs) ...`). 

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

Under the Expert Model, **all four aspects are guaranteed 100% non-empty ($0\%$ emptiness)** across all formal entities.

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

### Aspect 1: `problem` — Premises, Hypotheses & Sort Constraints

**Epistemic Role:** The antecedent conditions and typed variable signatures necessary for the lemma to hold.

**Mathematical Requirements & Safeguards:**
1. **Preserving Types and Sort Constraints:** In Isabelle/HOL, raw syntax without types is ambiguous. A property like `count A x = count B x ⟹ A = B` requires knowing whether $A, B$ are `'a multiset`, `'a set`, or `'a fset`. Sort constraints (`'a :: linorder`, `'a :: comm_monoid_add`) determine whether automated tools (`linarith`, `algebra`) can function. Sort constraints and fixed signatures are explicitly preserved.
2. **Eigenvariables & Fixed Parameters (`fixes` / $\bigwedge$):** Quantifier status is preserved (e.g. `fixes e :: real assumes "e > 0"`).
3. **Unconditional Entities:** For unconditional lemmas (`lemma "rev (rev xs) = xs"`), Aspect 1 emits `unconditional_tautology_or_identity: <statement>` rather than an empty string, guaranteeing non-zero vector representation.

**Example:**
```isabelle
[Hypotheses & Sort Constraints]:
fixes A B :: "'a :: linorder multiset"
assumes "count A x = count B x" and "x ∈# A"
```

---

### Aspect 2: `method` — Proof Architecture & Strategic Roadmap

**Epistemic Role:** The overarching deductive strategy and architectural blueprint of the proof.

**Unified Strategy Synthesis (Isar + Apply + One-Liner):**
1. **Structured Isar Proofs:** Extracted declarative roadmap:
   - Initial proof method: `proof (induction xs rule: rev_induct)`
   - Major structural sub-claims: `have "... "`, `show ?thesis`
   - Case analysis splits: `case (Cons x xs)`
2. **Apply-Script Proofs:** Unified induction and structural tactics:
   - Pipeline signature: `strategy: structural-induction [induction xs] -> simplification-pipeline [auto]`
3. **One-Liner Proofs:** Classified strategic signature:
   - `by (induction ...)` $\to$ `strategy: structural-induction`
   - `by simp` / `by auto` $\to$ `strategy: equational-normalization`
   - `by blast` / `by fastforce` $\to$ `strategy: classical-reasoning-tableau`
   - `by metis` / `by meson` $\to$ `strategy: resolution-atp`
   - `by (linarith | presburger | algebra)` $\to$ `strategy: decision-procedure`
4. **Definitions & Datatypes:**
   - Emits structural specification signature: `definitional-specification: primitive-recursion` or `corecursive-coinduction`.

**Example (Structured):**
```isabelle
[Proof Architecture]:
proof (induction n arbitrary: s)
  case 0 ...
  case (Suc n)
  have "length (take (Suc n) s) = Suc (min n (length s))"
  show ?case
qed
```

**Example (One-Liner / Procedural):**
```isabelle
[Proof Architecture]:
strategy: structural-induction on (xs) via induct_list; automation: equational-normalization (auto)
```

---

### Aspect 3: `finding` — Coupled Step Map & Operational Content

**Epistemic Role:** The concrete operational mechanics of the proof—coupling each intermediate claim to the exact tactic and lemmas that validated it.

**The Step Map Principle:**
In the legacy model, tactics were collected into a flat list of strings (`["by auto", "by auto"]`), completely detached from the claims they proved. Under the Expert Model, Aspect 3 constructs a **Coupled Step Map**:

$$\text{Step}_k = \langle \text{Claim}_k, \text{Tactic}_k, \text{CitedDeps}_k \rangle$$

**Representation:**
```isabelle
[Coupled Proof Step Map]:
- step 1:
    claim: have "set (tree_to_list l) = set_tree l"
    tactic: by (simp add: tree_to_list_def)
    dependencies: [tree_to_list_def, set_simps]
- step 2:
    claim: show ?thesis
    tactic: using assms by (auto intro: tree_orderedI)
    dependencies: [tree_orderedI]
```

For procedural apply scripts and one-liners:
```isabelle
[Proof Execution]:
apply (induction xs rule: rev_induct)
apply (auto simp add: list_eq_iff)
by (metis append_assoc)
Cited Dependencies: [rev_induct, list_eq_iff, append_assoc]
```

---

### Aspect 4: `interpretation` — Consequent, Attributes & Scope

**Epistemic Role:** The formal mathematical result established by the theorem, enriched with its logical role in Isabelle's automation engine.

**Metadata Enrichment:**
1. **Consequent / Target Goal:** The terminal claim established by the proof.
2. **Rule Classification (`rule_type`):**
   - `induction_rule`: Provides structural induction principles for datatypes or recursive functions.
   - `simplification_rule` (`[simp]`): Rewriting equations active in the term rewriting engine.
   - `introduction_rule` (`[intro]`, `[intro!]`): Backward chaining rules.
   - `elimination_rule` (`[elim]`, `[elim!]`): Forward context elimination rules.
   - `destruction_rule` (`[dest]`): Direct extraction rules.
   - `definition_rule`: Definitional equations (`=`).
   - `general_theorem`: General logical inferences.
3. **Locale & Context Scope (`locale`, `context_scope`):**
   - Qualified under local assumption environments (e.g., `in order`, `in complete_lattice`).
4. **Equational Directionality:**
   - Preserves whether $P \longleftrightarrow Q$ is registered as a directed rewrite rule $P \implies Q$ via `[simp]`.

**Example:**
```isabelle
[Conclusion & Automation Directives]:
Target: "avl (insert x t)"
Rule Type: introduction_rule
Attributes: [simp, intro!]
Context: locale "tree_order" in theory "AVL-Trees.AVL"
```

---

## 4. Neural Embedding Precautions (`voyage-code-3`)

Embedding formal proof fragments using general dense embedding models requires specialized engineering to avoid vector space degeneracy:

### 1. The Token Starvation Problem
A raw proposition like `avl l` or `by auto` contains only 2 to 4 tokens. Code embedding models fine-tuned on natural language docstrings and 500-token function bodies suffer representation collapse when given 3-token strings.

### 2. Contextual Envelopes
Every aspect is wrapped in a structured semantic envelope before embedding:

```
[Theory: {theory}] [Locale: {locale}] [Role: {keyword}] [Rule: {rule_type}] [Attributes: {attributes}] [Types: {type_signature}]
Lemma: {title} | {aspect_title}:
{aspect_content}
```

This guarantees:
- Token count is lifted to $\ge 40$ tokens per aspect.
- Semantic disambiguation: Two lemmas named `insert_def` in different theories (`Set` vs `Multiset` vs `RB_Tree`) inhabit distinct coordinates in embedding space.
- The model embeds the logical purpose and scope along with the syntax.

---

## 5. Summary of Schema Features

| Feature | Legacy Model | Expert Epistemic Model |
| :--- | :--- | :--- |
| **Aspect 1 (`problem`)** | Raw antecedent text | Preserves types, sort bounds (`::linorder`), eigenvariables & fixes |
| **Aspect 2 (`method`)** | Isar skeleton only ($\approx 80\%$ empty) | **0% empty.** Unified Isar roadmaps, apply strategies, and one-liner signatures |
| **Aspect 3 (`finding`)** | Uncoupled list of tactics | **Coupled Step Map:** `(claim, tactic, cited_dependencies)` |
| **Aspect 4 (`interpretation`)** | Raw consequent text | Consequent + Rule Classification + Attributes (`[simp, intro]`) + Locales |
| **Simplex Non-Degeneracy** | $D_{mf} = \|\mathbf{emb}_F\|$ on $80\%$ of archive | $D_{mf} > 0$ strictly maintained across $100\%$ of archive |
| **Embedding Protocol** | Raw code tokens (starvation) | Contextual Envelope (`voyage-code-3` optimized) |
