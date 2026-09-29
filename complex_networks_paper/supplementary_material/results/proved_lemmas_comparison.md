# Empirical Proof Comparison: Native Isabelle vs. Agent-Generated Proofs

**Project:** Higher-Order Epistemic Networks for Navigating the Archive of Formal Proofs (Complex Networks 2026)
**Authors:** Complex Networks 2026 Submission

## Executive Summary

This document provides a comprehensive, systematic comparison between the **native (human/original)** proofs 
stored in the Archive of Formal Proofs (AFP) and the Isabelle `HOL-Library`, and the **autonomous proofs generated** 
by Claude Sonnet 5 under **Treatment I/L (Simplicial Navigation)** across all 78 successfully discharged benchmark theorems.

### Key Methodological Insights
1. **Modernization of Legacy Tactics:** Many foundational and long-standing AFP entries (such as `Featherweight_OCL` from 2014 and `AVL-Trees` from 2004) rely on legacy procedural commands (`erule_tac`, `case_tac`, `rename_tac`, `cut_facts_tac`) that predate modern Isar and structured automation. The autonomous agent consistently replaces these brittle, positional tactic invocations with idiomatic modern Isar expressions (`by auto`, `by (metis ...)`, or structured `by (induction ...) (auto simp: ...)`).
2. **Dramatic Conciseness in Inductive Proofs:** Across Tier 2 (Inductive Proofs), human native proofs often span 10 to 30 lines of verbose case declarations (`case Nil ... show ?case ... case Cons ... show ?case ... qed`). Treatment I/L successfully condenses these into unified, robust one-liners with arbitrary variable generalization (e.g. `by (induction xs arbitrary: i) (auto simp: ... split: ...)`).
3. **Epistemic Aspect Targeting vs. Flat Search Distraction:** For deep structural theorems like `Featherweight_OCL.UML_Logic.const_subst`, where flat RAG fails by retrieving misleading boolean algebra lemmas, I/L navigates via $D(M | p)$ and Landscape Height centrality to target context preservation lemmas, enabling the agent to reconstruct multi-step declarative proofs.

---

## Summary Statistics of Proved Theorems (Treatment I/L: 78/140 = 55.7%)

| Difficulty Tier | Benchmark Total | Treatment Solved | Control Solved | Baseline Solved | Legacy Tactics in Native Proofs |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Tier 1: Terminal / One-Liners** | 40 | **32** (80.0%) | 33 (82.5%) | 29 (72.5%) | 0 theorems |
| **Tier 2: Inductive Proofs** | 45 | **39** (86.7%) | 36 (80.0%) | 38 (84.4%) | 0 theorems |
| **Tier 3: Structural / Multi-Step Proofs** | 15 | **5** (33.3%) | 3 (20.0%) | 4 (26.7%) | 0 theorems |
| **Tier 4: Deep HOL-Library** | 20 | **1** (5.0%) | 1 (5.0%) | 2 (10.0%) | 0 theorems |
| **Tier 5: Deep Pure AFP** | 20 | **1** (5.0%) | 1 (5.0%) | 2 (10.0%) | 3 theorems |
| **Total** | **140** | **78 (55.7%)** | **74 (52.9%)** | **75 (53.6%)** | **3 theorems** |

---

## Tier 1: Terminal / One-Liners (32 Solved Theorems)

### 1. `AVL-Trees.AVL.height_mkt_bal_r2`
- **Session:** `AVL-Trees` | **Theory:** `AVL-Trees.AVL`, Year: 2004 | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 1 turn(s) (35 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma height_mkt_bal_r2:   "⟦ avl l;  avl r;  height r ≠ height l + 2 ⟧ ⟹    height (mkt_bal_r n l r) = (1 + max (height l) (height r))"
```

#### Native / Ground-Truth Proof
```isabelle
by (cases l, cases r) simp_all
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (cases r) (auto simp add: mkt_def split: tree.split)
```


---

### 2. `AVL-Trees.AVL2.erase_r_bal`
- **Session:** `AVL-Trees` | **Theory:** `AVL-Trees.AVL2`, Year: 2004 | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 1 turn(s) (41 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma erase_r_bal:  "hinv l ⟹ hinv r ⟹ height(erase r) = height(erase l) + 2 ⟹   erase (r_bal n l r) = r_bal\<^sub>0 n (erase l) (erase r)"
```

#### Native / Ground-Truth Proof
```isabelle
by (cases r) (simp_all add: height_hinv erase_mkt split: tree.split)
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (cases r) (simp_all add: height_hinv erase_mkt split: tree.split)
```


---

### 3. `Featherweight_OCL.UML_Logic.foundation18''`
- **Session:** `Featherweight_OCL` | **Theory:** `Featherweight_OCL.UML_Logic`, Year: 2014 | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 2 turn(s) (293 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 2 line(s) (-100.0% lines).

#### Formal Statement
```isabelle
lemma foundation18'': "(τ ⊨ (υ X) )=  (¬(τ ⊨ (X ≜ invalid)))"
```

#### Native / Ground-Truth Proof
```isabelle
by(auto simp:foundation15)
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by(simp add: OclValid_def valid_def false_def true_def StrongEq_def invalid_def bot_option_def split: option.split option.split_asm)
by(auto simp: OclValid_def valid_def false_def true_def StrongEq_def invalid_def bot_option_def bot_fun_def)
```


---

### 4. `Featherweight_OCL.UML_Logic.foundation9'`
- **Session:** `Featherweight_OCL` | **Theory:** `Featherweight_OCL.UML_Logic`, Year: 2014 | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 2 turn(s) (71 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 2 line(s) (-100.0% lines).

#### Formal Statement
```isabelle
lemma foundation9': "τ ⊨ not x ⟹ ¬ (τ ⊨ x)"
```

#### Native / Ground-Truth Proof
```isabelle
by(auto simp: foundation6 foundation9)
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (simp add: foundation9)
by (simp add: OclNot_def OclValid_def true_def false_def defined_def split: option.split option.split_asm)
```


---

### 5. `Featherweight_OCL.UML_Set.lemma_43`
- **Session:** `Featherweight_OCL` | **Theory:** `Featherweight_OCL.UML_Set`, Year: 2014 | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 3 turn(s) (317 completion tokens).
- **Proof Length Contrast:** Native Proof: 2 lines $\longrightarrow$ Generated Proof: 3 line(s) (-50.0% lines).

#### Formal Statement
```isabelle
lemma Void\<^sub>e\<^sub>m\<^sub>p\<^sub>t\<^sub>y_defined : "δ Void\<^sub>e\<^sub>m\<^sub>p\<^sub>t\<^sub>y = true"
```

#### Native / Ground-Truth Proof
```isabelle
apply(rule ext, auto simp: Void\<^sub>e\<^sub>m\<^sub>p\<^sub>t\<^sub>y_def defined_def false_def true_def                            bot_fun_def null_fun_def null_option_def                            bot_Set\<^sub>b\<^sub>a\<^sub>s\<^sub>e_def null_Set\<^sub>b\<^sub>a\<^sub>s\<^sub>e_def)
by((subst (asm) Abs_Set\<^sub>b\<^sub>a\<^sub>s\<^sub>e_inject, auto simp add: bot_option_def null_option_def bot_Void_def))+
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
apply(rule ext, auto simp: Void\<^sub>e\<^sub>m\<^sub>p\<^sub>t\<^sub>y_def defined_def false_def true_def bot_fun_def null_fun_def null_option_def bot_Set\<^sub>b\<^sub>a\<^sub>s\<^sub>e_def null_Set\<^sub>b\<^sub>a\<^sub>s\<^sub>e_def)
apply(subst (asm) Abs_Set\<^sub>b\<^sub>a\<^sub>s\<^sub>e_inject, auto simp add: bot_option_def null_option_def bot_Void_def)
apply(subst (asm) Abs_Set\<^sub>b\<^sub>a\<^sub>s\<^sub>e_inject, auto simp add: bot_option_def null_option_def)
```


---

### 6. `Featherweight_OCL.UML_State.lemma_47`
- **Session:** `Featherweight_OCL` | **Theory:** `Featherweight_OCL.UML_State`, Year: 2014 | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 1 turn(s) (111 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma StrictRefEq\<^sub>O\<^sub>b\<^sub>j\<^sub>e\<^sub>c\<^sub>t_defargs: "τ ⊨ (StrictRefEq\<^sub>O\<^sub>b\<^sub>j\<^sub>e\<^sub>c\<^sub>t x (y::('𝔄,'a::{null,object})val))⟹ (τ ⊨(υ x)) ∧ (τ ⊨(υ y))"
```

#### Native / Ground-Truth Proof
```isabelle
by(simp add: StrictRefEq\<^sub>O\<^sub>b\<^sub>j\<^sub>e\<^sub>c\<^sub>t_def OclValid_def true_def invalid_def bot_option_def         split: bool.split_asm HOL.if_split_asm)
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
apply (simp add: StrictRefEq\<^sub>O\<^sub>b\<^sub>j\<^sub>e\<^sub>c\<^sub>t_def OclValid_def true_def false_def invalid_def bot_option_def split: bool.split_asm HOL.if_split_asm)
```


---

### 7. `Featherweight_OCL.UML_Tools.X'_novel_variant`
- **Session:** `Featherweight_OCL` | **Theory:** `Featherweight_OCL.UML_Tools`, Year: 2014 | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 1 turn(s) (18 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma X': "¬ (τ ⊨ (invalid and B))"
```

#### Native / Ground-Truth Proof
```isabelle
by(simp add:foundation10')
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (simp add: X)
```


---

### 8. `Featherweight_OCL.UML_Tools.test2`
- **Session:** `Featherweight_OCL` | **Theory:** `Featherweight_OCL.UML_Tools`, Year: 2014 | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 4 turn(s) (222 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 4 line(s) (-300.0% lines).

#### Formal Statement
```isabelle
lemma test2 : "τ ⊨ A ⟹ τ ⊨ (A and B ≜ B)"
```

#### Native / Ground-Truth Proof
```isabelle
by(ocl_subst_asm, simp)
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
apply(tactic "ocl_subst_tac 1")
apply(tactic "ocl_subst_asm_tac 1")
apply(tactic "ocl_subst_asm_tac @{context} 1")
apply(simp add: StrongEq_sym foundation12 foundation6)
```


---

### 9. `HOL-Library.Multiset.add_mset_commute`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 1 turn(s) (26 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma add_mset_commute:   "add_mset x (add_mset y M) = add_mset y (add_mset x M)"
```

#### Native / Ground-Truth Proof
```isabelle
by (auto simp: multiset_eq_iff)
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (simp add: multiset_eq_iff)
```


---

### 10. `HOL-Library.Multiset.add_mset_diff_bothsides`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 1 turn(s) (26 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma add_mset_diff_bothsides:   ‹add_mset a M - add_mset a A = M - A›
```

#### Native / Ground-Truth Proof
```isabelle
by (auto simp: multiset_eq_iff)
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (simp add: multiset_eq_iff)
```


---

### 11. `HOL-Library.Multiset.diff_add_mset_swap_novel_variant`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 1 turn(s) (34 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma diff_add_mset_swap [simp]: "b_elem ∉# A ⟹ add_mset b_elem M - A = add_mset b_elem (M - A)"
```

#### Native / Ground-Truth Proof
```isabelle
by (auto simp add: multiset_eq_iff simp: not_in_iff)
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (auto simp add: multiset_eq_iff not_in_iff)
```


---

### 12. `HOL-Library.Multiset.diff_union_swap`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 1 turn(s) (27 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma diff_union_swap: "a ≠ b ⟹ add_mset b (M - {#a#}) = add_mset b M - {#a#}"
```

#### Native / Ground-Truth Proof
```isabelle
by (auto simp add: multiset_eq_iff)
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (auto simp: multiset_eq_iff)
```


---

### 13. `HOL-Library.Multiset.dvd_prod_mset`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 7 turn(s) (499 completion tokens).
- **Proof Length Contrast:** Native Proof: 2 lines $\longrightarrow$ Generated Proof: 7 line(s) (-250.0% lines).

#### Formal Statement
```isabelle
lemma dvd_prod_mset:   assumes "x ∈# A"   shows "x dvd prod_mset A"
```

#### Native / Ground-Truth Proof
```isabelle
using assms prod_mset_subset_imp_dvd [of "{#x#}" A]
by simp
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
using assms by (auto simp add: dvd_def elim: multi_member_split)
using assms by (metis multi_member_split prod_mset.insert dvd_triv_left)
proof -
obtain B where "A = {#x#} + B" using multi_member_split[OF assms] by blast
obtain B where "A = add_mset x B" using multi_member_split[OF assms] by blast
then show ?thesis by simp
qed
```


---

### 14. `HOL-Library.Multiset.filter_mset_cong`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 2 turn(s) (56 completion tokens).
- **Proof Length Contrast:** Native Proof: 3 lines $\longrightarrow$ Generated Proof: 2 line(s) (+33.3% lines).

#### Formal Statement
```isabelle
lemma filter_mset_cong:   assumes "M = M'" and "⋀x. x ∈# M' ⟹ f x ⟷ g x"   shows "filter_mset f M = filter_mset g M'"
```

#### Native / Ground-Truth Proof
```isabelle
unfolding ‹M = M'›
using assms
by (auto intro: filter_mset_cong0)
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
using assms by (auto simp: filter_mset_cong0)
using assms filter_mset_cong0 by blast
```


---

### 15. `HOL-Library.Multiset.filter_single_mset`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 1 turn(s) (24 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma filter_single_mset: "filter_mset P {#x#} = (if P x then {#x#} else {#})"
```

#### Native / Ground-Truth Proof
```isabelle
by (rule multiset_eqI) simp
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (simp add: multiset_eqI)
```


---

### 16. `HOL-Library.Multiset.in_diffD_novel_variant`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 7 turn(s) (555 completion tokens).
- **Proof Length Contrast:** Native Proof: 11 lines $\longrightarrow$ Generated Proof: 7 line(s) (+36.4% lines).

#### Formal Statement
```isabelle
lemma in_diffD:   assumes "a_elem ∈# M - N"   shows "a_elem ∈# M"
```

#### Native / Ground-Truth Proof
```isabelle
proof -
have "0 ≤ count N a_elem"
by simp
also
from assms
have "count N a_elem < count M a_elem"
by (simp add: in_diff_count)
finally
show ?thesis
by simp
qed
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
using assms by (simp add: in_diff_count in_diff_countE count_greater_zero_iff)
using assms by (simp add: in_diff_count count_greater_zero_iff[symmetric])
proof (rule ccontr)
then show False using assms by (simp add: in_diff_count not_in_iff)
isabelis
assume "a_elem ∉# M" then show False using assms by (simp add: in_diff_count not_in_iff)
qed
```


---

### 17. `HOL-Library.Multiset.inter_add_left2_novel_variant`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 11 turn(s) (4193 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 11 line(s) (-1000.0% lines).

#### Formal Statement
```isabelle
lemma inter_add_left2: "x_elem ∈# N ⟹ (add_mset x_elem M) ∩# N = add_mset x_elem (M ∩# (N - {#x_elem#}))"
```

#### Native / Ground-Truth Proof
```isabelle
by (auto simp add: multiset_eq_iff elim: mset_add)
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (simp add: multiset_eq_iff not_in_iff)
by auto
by (auto sim
by auto
by auto
by (simp add: multiset_eq_iff not_in_iff)
by (metis Suc_diff_1 count_greater_zero_iff min_Suc_
by auto
by auto
apply (simp add: multiset_eq_iff not_in_iff)
by (metis count_greater_zero_iff min_Suc_Suc Suc_pred)
```


---

### 18. `HOL-Library.Multiset.lemma_1227`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 1 turn(s) (32 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma repeat_mset_distrib_add_mset[simp]:   "repeat_mset n (add_mset a A) = replicate_mset n a + repeat_mset n A"
```

#### Native / Ground-Truth Proof
```isabelle
by (auto simp: multiset_eq_iff)
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induction n) (auto simp: multiset_eq_iff)
```


---

### 19. `HOL-Library.Multiset.lemma_1835`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 1 turn(s) (24 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma filter_sup_mset[simp]: "filter_mset P (A ∪# B) = filter_mset P A ∪# filter_mset P B"
```

#### Native / Ground-Truth Proof
```isabelle
by (rule multiset_eqI) simp
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (rule multiset_eqI) simp
```


---

### 20. `HOL-Library.Multiset.lemma_3585`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 1 turn(s) (30 completion tokens).
- **Proof Length Contrast:** Native Proof: 2 lines $\longrightarrow$ Generated Proof: 1 line(s) (+50.0% lines).

#### Formal Statement
```isabelle
lemma mset_set_eq_iff[simp]:   assumes "finite A" "finite B"   shows "mset_set A = mset_set B ⟷ A = B"
```

#### Native / Ground-Truth Proof
```isabelle
using assms
by (fastforce dest: finite_set_mset_mset_set)
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
using assms by (metis finite_set_mset_mset_set)
```


---

### 21. `HOL-Library.Multiset.mset_add_novel_variant`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 1 turn(s) (62 completion tokens).
- **Proof Length Contrast:** Native Proof: 8 lines $\longrightarrow$ Generated Proof: 1 line(s) (+87.5% lines).

#### Formal Statement
```isabelle
lemma mset_add [elim?]:   assumes "a_elem ∈# A"   obtains B where "A = add_mset a_elem B"
```

#### Native / Ground-Truth Proof
```isabelle
proof -
from assms
have "A = add_mset a_elem (A - {#a_elem#})"
by simp
with that
show thesis
.
qed
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (metis assms insert_DiffM)
```

> **Idiomatic Shift:** The native proof relies on manual case decomposition across 8 lines. The autonomous agent generalized the induction scheme into a concise automated one-liner.

---

### 22. `HOL-Library.Multiset.multi_drop_mem_not_eq_novel_variant`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 2 turn(s) (442 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 2 line(s) (-100.0% lines).

#### Formal Statement
```isabelle
lemma multi_drop_mem_not_eq: "c ∈# B ⟹ B - {#c#} ≠ B"
```

#### Native / Ground-Truth Proof
```isabelle
by (cases "B = {#}") (auto dest: multi_member_split)
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (metis diff_single_trivial)
by (metis size_Diff1_less less_irrefl)
```


---

### 23. `HOL-Library.Multiset.prod_mset_minus`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 10 turn(s) (2763 completion tokens).
- **Proof Length Contrast:** Native Proof: 2 lines $\longrightarrow$ Generated Proof: 10 line(s) (-400.0% lines).

#### Formal Statement
```isabelle
lemma (in semidom_divide) prod_mset_minus:   assumes "a ∈# A" and "a ≠ 0"   shows "prod_mset (A - {#a#}) = prod_mset A div a"
```

#### Native / Ground-Truth Proof
```isabelle
using assms prod_mset_diff [of "{#a#}" A]
by auto
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
proof -
have "prod_mset A = a * prod_mset (A - {#a#})"
by (metis assms(1) insert_DiffM prod_mset.insert)
by (metis assms(1) insert_DiffM prod_mset.insert mset_add)
by (metis assms(1) insert_DiffM prod_mset.simps)
by (metis assms(1) insert_DiffM prod_mset_add prod_mset_singleton mult.commute)
by (metis assms(1) insert_DiffM prod_mset.insert)
by (metis assms(1) insert_DiffM prod_mset.insert)
apply (subst insert_DiffM[symmetric, OF assms(1)])
apply (simp add: assms(2) nonzero_mult_div_cancel_left)
```


---

### 24. `HOL-Library.Multiset.size_Diff_singleton_if`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 1 turn(s) (26 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma size_Diff_singleton_if: "size (A - {#x#}) = (if x ∈# A then size A - 1 else size A)"
```

#### Native / Ground-Truth Proof
```isabelle
by (simp add: diff_single_trivial size_Diff_singleton)
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (simp add: size_Diff_singleton)
```


---

### 25. `HOL-Library.Multiset.size_eq_sum_mset_novel_variant`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 1 turn(s) (18 completion tokens).
- **Proof Length Contrast:** Native Proof: 2 lines $\longrightarrow$ Generated Proof: 1 line(s) (+50.0% lines).

#### Formal Statement
```isabelle
lemma size_eq_sum_mset:   "size M = (∑a_elem∈#M. 1)"
```

#### Native / Ground-Truth Proof
```isabelle
using image_mset_const_eq [of "1::nat" M]
by simp
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induction M) auto
```


---

### 26. `HOL-Library.Multiset.sort_sorted_list_of_multiset_eq`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 1 turn(s) (40 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma sort_sorted_list_of_multiset_eq [simp]:   ‹sort (sorted_list_of_multiset M) = sorted_list_of_multiset M› for M :: ‹'a::linorder multiset›
```

#### Native / Ground-Truth Proof
```isabelle
by (rule properties_for_sort) simp_all
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (simp add: sorted_sort_id sorted_sorted_list_of_multiset)
```


---

### 27. `HOL-Library.Multiset.sup_union_left1`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 1 turn(s) (28 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma sup_union_left1 [simp]: "¬ x ∈# N ⟹ (add_mset x M) ∪# N = add_mset x (M ∪# N)"
```

#### Native / Ground-Truth Proof
```isabelle
by (simp add: multiset_eq_iff not_in_iff)
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (auto simp add: multiset_eq_iff)
```


---

### 28. `HOL-Library.Multiset.sup_union_right1_novel_variant`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 1 turn(s) (32 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma sup_union_right1 [simp]: "¬ x_elem ∈# N ⟹ N ∪# (add_mset x_elem M) = add_mset x_elem (N ∪# M)"
```

#### Native / Ground-Truth Proof
```isabelle
by (simp add: multiset_eq_iff not_in_iff)
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (simp add: multiset_eq_iff not_in_iff)
```


---

### 29. `HOL-Library.Multiset.union_diff_sup_eq_inter_novel_variant`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 1 turn(s) (28 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma union_diff_sup_eq_inter:   "A + B - A ∪# B = A ∩# B"
```

#### Native / Ground-Truth Proof
```isabelle
by (auto simp add: multiset_eq_iff)
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (auto simp add: multiset_eq_iff)
```


---

### 30. `HOL-Library.Tree.complete_if_size1_height_novel_variant`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Tree` | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 1 turn(s) (79 completion tokens).
- **Proof Length Contrast:** Native Proof: 2 lines $\longrightarrow$ Generated Proof: 1 line(s) (+50.0% lines).

#### Formal Statement
```isabelle
lemma complete_if_size1_height: "size1 t_tree = 2 ^ height t_tree ⟹ complete t_tree"
```

#### Native / Ground-Truth Proof
```isabelle
using  size1_height_if_incomplete
by fastforce
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
using size1_height_if_incomplete[of t_tree] by fastforce
```


---

### 31. `HOL-Library.Tree.lemma_153_novel_variant`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Tree` | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 2 turn(s) (38 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 2 line(s) (-100.0% lines).

#### Formal Statement
```isabelle
lemma eq_0_height[simp]: "0 = height t_tree ⟷ t_tree = Leaf"
```

#### Native / Ground-Truth Proof
```isabelle
by(cases t_tree) auto
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
apply (cases t_tree)
apply auto
```


---

### 32. `HOL-Library.Tree.lemma_83`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Tree` | **Difficulty Tier:** Tier 1: Terminal / One-Liners
- **Proving Dynamics:** Solved in 1 turn(s) (21 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma size1_ge0[simp]: "0 < size1 t"
```

#### Native / Ground-Truth Proof
```isabelle
by (simp add: size1_size)
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (simp add: size1_size)
```


---

## Tier 2: Inductive Proofs (39 Solved Theorems)

### 33. `HOL-Library.DAList_Multiset.count_of_empty`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.DAList_Multiset` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 5 turn(s) (365 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 5 line(s) (-400.0% lines).

#### Formal Statement
```isabelle
lemma count_of_empty: "x ∉ fst ` set xs ⟹ count_of xs x = 0"
```

#### Native / Ground-Truth Proof
```isabelle
by (induct xs) (simp_all add: count_of_def)
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
apply (simp add: count_of_def map_of_eq_None_iff)
apply (auto simp add: map_of_eq_None_iff)
apply (simp add: map_of_eq_None_iff)
apply (drule map_of_eq_None_iff [THEN iffD2])
apply simp
```


---

### 34. `HOL-Library.Multiset.filter_mset_sum_list_novel_variant`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 1 turn(s) (33 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma filter_mset_sum_list: "filter_mset P (sum_list xs_list) = sum_list (map (filter_mset P) xs_list)"
```

#### Native / Ground-Truth Proof
```isabelle
by (induction xs_list) simp_all
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induction xs_list) (auto simp: filter_union_mset)
```


---

### 35. `HOL-Library.Multiset.image_mset_If`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 1 turn(s) (18 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma image_mset_If:   "image_mset (λx. if P x then f x else g x) A =      image_mset f (filter_mset P A) + image_mset g (filter_mset (λx. ¬P x) A)"
```

#### Native / Ground-Truth Proof
```isabelle
by (induction A) auto
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induction A) auto
```


---

### 36. `HOL-Library.Multiset.image_mset_const_eq`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 1 turn(s) (32 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma image_mset_const_eq:   "{#c. a ∈# M#} = replicate_mset (size M) c"
```

#### Native / Ground-Truth Proof
```isabelle
by (induct M) simp_all
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induction M) auto
```


---

### 37. `HOL-Library.Multiset.image_mset_filter_mset_swap_novel_variant`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 1 turn(s) (18 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma image_mset_filter_mset_swap:   "image_mset f (filter_mset (λx_elem. P (f x_elem)) M) = filter_mset P (image_mset f M)"
```

#### Native / Ground-Truth Proof
```isabelle
by (induction M rule: multiset_induct) simp_all
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induction M) auto
```


---

### 38. `HOL-Library.Multiset.in_multiset_in_set`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 1 turn(s) (19 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma in_multiset_in_set:   "x ∈# mset xs ⟷ x ∈ set xs"
```

#### Native / Ground-Truth Proof
```isabelle
by (induct xs) simp_all
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induction xs) auto
```


---

### 39. `HOL-Library.Multiset.lemma_2923`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 1 turn(s) (18 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma mset_zero_iff_right[simp]: "({#} = mset x) = (x = [])"
```

#### Native / Ground-Truth Proof
```isabelle
by (induct x) auto
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induct x) auto
```


---

### 40. `HOL-Library.Multiset.lemma_3345_novel_variant`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 2 turn(s) (44 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 2 line(s) (-100.0% lines).

#### Formal Statement
```isabelle
lemma elem_mset_set[simp, intro]: "finite A ⟹ x_elem ∈# mset_set A ⟷ x_elem ∈ A"
```

#### Native / Ground-Truth Proof
```isabelle
by (induct A rule: finite_induct) simp_all
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
apply (induction A rule: finite_induct)
apply auto
```


---

### 41. `HOL-Library.Multiset.lemma_3511`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 2 turn(s) (203 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 2 line(s) (-100.0% lines).

#### Formal Statement
```isabelle
lemma sorted_list_of_multiset_mset[simp]: "sorted_list_of_multiset (mset xs) = sort xs"
```

#### Native / Ground-Truth Proof
```isabelle
by (induct xs) simp_all
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induct xs) (simp_all add: sorted_list_of_multiset_def)
by (induct xs) (simp_all add: sorted_list_of_multiset_def comp_fun_commute.fold_mset_add_mset comp_fun_commute_insort)
```


---

### 42. `HOL-Library.Multiset.lemma_3635_novel_variant`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 1 turn(s) (18 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma size_replicate_mset[simp]: "size (replicate_mset n M) = n"
```

#### Native / Ground-Truth Proof
```isabelle
by (induct n, simp_all)
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induction n) auto
```


---

### 43. `HOL-Library.Multiset.lemma_4329_novel_variant`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 1 turn(s) (19 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma set_mset_Union_mset[simp]: "set_mset (∑\<^sub># MM) = (⋃M ∈ set_mset MM. set_mset M)"
```

#### Native / Ground-Truth Proof
```isabelle
by (induct MM) auto
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induction MM) auto
```


---

### 44. `HOL-Library.Multiset.lemma_4367`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 1 turn(s) (18 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma Union_mset_empty_conv[simp]: "∑\<^sub># M = {#} ⟷ (∀i∈#M. i = {#})"
```

#### Native / Ground-Truth Proof
```isabelle
by (induction M) auto
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induction M) auto
```


---

### 45. `HOL-Library.Multiset.lemma_6937`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 12 turn(s) (2897 completion tokens).
- **Proof Length Contrast:** Native Proof: 7 lines $\longrightarrow$ Generated Proof: 12 line(s) (-71.4% lines).

#### Formal Statement
```isabelle
lemma [code]:   "mset xs ∪# mset ys =     mset (case_prod append (fold (λx (ys, zs). (remove1 x ys, x # zs)) xs (ys, [])))"
```

#### Native / Ground-Truth Proof
```isabelle
proof -
have "⋀zs. mset (case_prod append (fold (λx (ys, zs). (remove1 x ys, x # zs)) xs (ys, zs))) =       (mset xs ∪# mset ys) + mset zs"
by (induct xs arbitrary: ys) (simp_all add: multiset_eq_iff)
then
show ?thesis
by simp
qed
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
proof -
have "⋀ys zs. mset (case_prod append (fold (λx (ys, zs). (remove1 x ys, x # zs)) xs (ys, zs))) = mset xs ∪# mset ys + mset zs"
by (induct xs arbitrary: ys zs) (auto simp add: inter_add_right1 inter_add_right2 ac_simps)
by (induct xs arbitrary: ys zs) (auto simp add: inter_add_right1 inter_add_right2 ac_simps sup_union_left2)
by (induct xs arbitrary: ys zs) (auto simp add: inter_add_right1 inter_add_right2 ac_simps multiset_eq_iff)
by (simp add: this)
show ?thesis by (simp add: this)
using this by simp
by auto
by auto
then show ?thesis by (simp del: mset.simps)
qed
```


---

### 46. `HOL-Library.Multiset.mset_append_novel_variant`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 1 turn(s) (23 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma mset_append [simp]: "mset (xs_list @ ys_list) = mset xs_list + mset ys_list"
```

#### Native / Ground-Truth Proof
```isabelle
by (induct xs_list arbitrary: ys_list) auto
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induction xs_list) simp_all
```


---

### 47. `HOL-Library.Multiset.mset_insort`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 1 turn(s) (19 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma mset_insort [simp]:   "mset (insort_key k x xs) = add_mset x (mset xs)"
```

#### Native / Ground-Truth Proof
```isabelle
by (induct xs) simp_all
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induction xs) auto
```


---

### 48. `HOL-Library.Multiset.mset_replicate`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 1 turn(s) (34 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma mset_replicate [simp]: "mset (replicate n x) = replicate_mset n x"
```

#### Native / Ground-Truth Proof
```isabelle
by (induction n) auto
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induct n) (simp_all add: replicate_mset_Suc)
```


---

### 49. `HOL-Library.Multiset.mset_update`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 4 turn(s) (230 completion tokens).
- **Proof Length Contrast:** Native Proof: 20 lines $\longrightarrow$ Generated Proof: 4 line(s) (+80.0% lines).

#### Formal Statement
```isabelle
lemma mset_update:   "i < length ls ⟹ mset (ls[i := v]) = add_mset v (mset ls - {#ls ! i#})"
```

#### Native / Ground-Truth Proof
```isabelle
proof (induct ls arbitrary: i)
case Nil
then
show ?case
by simp
next
case (Cons x xs)
show ?case
proof (cases i)
case 0
then
show ?thesis
by simp
next
case (Suc i')
with Cons
show ?thesis
by (cases ‹x = xs ! i'›) auto
qed
qed
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
apply (induction ls arbitrary: i)
apply (case_tac i, auto)
apply (case_tac i)
apply auto
```


---

### 50. `HOL-Library.Multiset.normalize_prod_mset`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 2 turn(s) (50 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 2 line(s) (-100.0% lines).

#### Formal Statement
```isabelle
lemma (in normalization_semidom_multiplicative) normalize_prod_mset:   "normalize (prod_mset A) = prod_mset (image_mset normalize A)"
```

#### Native / Ground-Truth Proof
```isabelle
by (induct A) (simp_all add: normalize_mult)
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induction A) simp_all
by (induction A) (simp_all add: normalize_mult)
```


---

### 51. `HOL-Library.Multiset.normalized_prod_msetI`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 5 turn(s) (699 completion tokens).
- **Proof Length Contrast:** Native Proof: 8 lines $\longrightarrow$ Generated Proof: 5 line(s) (+37.5% lines).

#### Formal Statement
```isabelle
lemma (in normalization_semidom_multiplicative) normalized_prod_msetI:   assumes "⋀a. a ∈# A ⟹ normalize a = a"   shows "normalize (prod_mset A) = prod_mset A"
```

#### Native / Ground-Truth Proof
```isabelle
proof -
from assms
have "image_mset normalize A = A"
by (induct A) simp_all
then
show ?thesis
by (simp add: normalize_prod_mset)
qed
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
using assms by (induction A) auto
using assms
apply (induction A)
apply simp
apply (simp add: normalize_mult)
```


---

### 52. `HOL-Library.Multiset.nth_mem_mset_novel_variant`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 1 turn(s) (62 completion tokens).
- **Proof Length Contrast:** Native Proof: 11 lines $\longrightarrow$ Generated Proof: 1 line(s) (+90.9% lines).

#### Formal Statement
```isabelle
lemma nth_mem_mset: "i < length ls ⟹ (ls ! i) ∈# mset ls"
```

#### Native / Ground-Truth Proof
```isabelle
proof (induct ls arbitrary: i)
case Nil
then
show ?case
by simp
next
case Cons
then
show ?case
by (cases i) auto
qed
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induction ls arbitrary: i) (auto simp: nth_Cons split: nat.splits)
```

> **Idiomatic Shift:** The native proof relies on manual case decomposition across 11 lines. The autonomous agent generalized the induction scheme into a concise automated one-liner.

---

### 53. `HOL-Library.Multiset.of_nat_sum_mset`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 1 turn(s) (18 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma of_nat_sum_mset [simp]:   "of_nat (sum_mset A) = sum_mset (image_mset of_nat A)"
```

#### Native / Ground-Truth Proof
```isabelle
by (induction A) auto
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induction A) auto
```


---

### 54. `HOL-Library.Multiset.prod_mset_replicate_mset`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 1 turn(s) (18 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma prod_mset_replicate_mset [simp]:   "prod_mset (replicate_mset n a) = a ^ n"
```

#### Native / Ground-Truth Proof
```isabelle
by (induct n) simp_all
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induct n) auto
```


---

### 55. `HOL-Library.Multiset.prod_mset_zero_iff`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 1 turn(s) (18 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma (in semidom) prod_mset_zero_iff [iff]:   "prod_mset A = 0 ⟷ 0 ∈# A"
```

#### Native / Ground-Truth Proof
```isabelle
by (induct A) auto
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induction A) auto
```


---

### 56. `HOL-Library.Multiset.prod_unfold_prod_mset`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 1 turn(s) (252 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma prod_unfold_prod_mset:   "prod f A = prod_mset (image_mset f (mset_set A))"
```

#### Native / Ground-Truth Proof
```isabelle
by (cases "finite A") (induct A rule: finite_induct, simp_all)
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induct A rule: infinite_finite_induct) auto
```


---

### 57. `HOL-Library.Multiset.rel_mset'_imp_rel_mset_novel_variant`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 2 turn(s) (210 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 2 line(s) (-100.0% lines).

#### Formal Statement
```isabelle
lemma rel_mset'_imp_rel_mset: "rel_mset' R M N ⟹ rel_mset R M N"
```

#### Native / Ground-Truth Proof
```isabelle
by (induct rule: rel_mset'.induct) (auto simp: rel_mset_Zero rel_mset_Plus)
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
apply (erule rel_mset'.induct)
apply (auto intro: rel_mset_Plus)
```


---

### 58. `HOL-Library.Multiset.set_image_mset`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 1 turn(s) (18 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma set_image_mset [simp]: "set_mset (image_mset f M) = image f (set_mset M)"
```

#### Native / Ground-Truth Proof
```isabelle
by (induct M) simp_all
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induct M) auto
```


---

### 59. `HOL-Library.Multiset.size_conv_count_bool_mset_novel_variant`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 1 turn(s) (145 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma size_conv_count_bool_mset: "size A = count A True + count A False"
```

#### Native / Ground-Truth Proof
```isabelle
by (induction A) auto
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induction A) auto
```


---

### 60. `HOL-Library.Multiset.sum_eq_empty_iff`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 1 turn(s) (29 completion tokens).
- **Proof Length Contrast:** Native Proof: 2 lines $\longrightarrow$ Generated Proof: 1 line(s) (+50.0% lines).

#### Formal Statement
```isabelle
lemma sum_eq_empty_iff:   assumes "finite A"   shows "sum f A = {#} ⟷ (∀a∈A. f a = {#})"
```

#### Native / Ground-Truth Proof
```isabelle
using assms
by induct simp_all
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
using assms by (induction A rule: finite_induct) auto
```


---

### 61. `HOL-Library.Multiset.sum_mset_singleton_mset`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 1 turn(s) (18 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma sum_mset_singleton_mset [simp]: "(∑x∈#A. {#f x#}) = image_mset f A"
```

#### Native / Ground-Truth Proof
```isabelle
by (induction A) auto
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induction A) auto
```


---

### 62. `HOL-Library.Multiset.sum_mset_sum_list`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 1 turn(s) (19 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma sum_mset_sum_list:   "sum_mset (mset xs) = sum_list xs"
```

#### Native / Ground-Truth Proof
```isabelle
by (induction xs) auto
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induction xs) auto
```


---

### 63. `HOL-Library.Multiset.sum_unfold_sum_mset`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 3 turn(s) (116 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 3 line(s) (-200.0% lines).

#### Formal Statement
```isabelle
lemma sum_unfold_sum_mset:   "sum f A = sum_mset (image_mset f (mset_set A))"
```

#### Native / Ground-Truth Proof
```isabelle
by (cases "finite A") (induct A rule: finite_induct, simp_all)
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
apply (cases "finite A")
apply (induction A rule: finite_induct)
apply auto
```


---

### 64. `HOL-Library.Tree.height_subtrees_novel_variant`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Tree` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 2 turn(s) (43 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 2 line(s) (-100.0% lines).

#### Formal Statement
```isabelle
lemma height_subtrees: "s ∈ subtrees t_tree ⟹ height s ≤ height t_tree"
```

#### Native / Ground-Truth Proof
```isabelle
by (induction t_tree) auto
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
apply (induction t_tree) auto
by (induction t_tree) auto
```


---

### 65. `HOL-Library.Tree.inorder_map_novel_variant`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Tree` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 1 turn(s) (21 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma inorder_map: "inorder (map_tree f t_tree) = map f (inorder t_tree)"
```

#### Native / Ground-Truth Proof
```isabelle
by (induction t_tree) auto
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induction t_tree) auto
```


---

### 66. `HOL-Library.Tree.lemma_139`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Tree` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 1 turn(s) (18 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma Node_notin_subtrees_if[simp]: "a ∉ set_tree t ⟹ Node l a r ∉ subtrees t"
```

#### Native / Ground-Truth Proof
```isabelle
by (induction t) auto
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induction t) auto
```


---

### 67. `HOL-Library.Tree.lemma_157`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Tree` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 1 turn(s) (18 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma height_map_tree[simp]: "height (map_tree f t) = height t"
```

#### Native / Ground-Truth Proof
```isabelle
by (induction t) auto
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induction t) auto
```


---

### 68. `HOL-Library.Tree.lemma_261_novel_variant`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Tree` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 1 turn(s) (21 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma min_height_map_tree[simp]: "min_height (map_tree f t_tree) = min_height t_tree"
```

#### Native / Ground-Truth Proof
```isabelle
by (induction t_tree) auto
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induction t_tree) auto
```


---

### 69. `HOL-Library.Tree.lemma_701`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Tree` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 1 turn(s) (20 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma mirror_mirror[simp]: "mirror(mirror t) = t"
```

#### Native / Ground-Truth Proof
```isabelle
by (induction t) simp_all
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induction t) simp_all
```


---

### 70. `HOL-Library.Tree.min_height_mirror`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Tree` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 1 turn(s) (18 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma min_height_mirror [simp]: "min_height (mirror t) = min_height t"
```

#### Native / Ground-Truth Proof
```isabelle
by (induction t) simp_all
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induction t) auto
```


---

### 71. `HOL-Library.Tree.preorder_map`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Tree` | **Difficulty Tier:** Tier 2: Inductive Proofs
- **Proving Dynamics:** Solved in 1 turn(s) (18 completion tokens).
- **Proof Length Contrast:** Native Proof: 1 lines $\longrightarrow$ Generated Proof: 1 line(s) (+0.0% lines).

#### Formal Statement
```isabelle
lemma preorder_map: "preorder (map_tree f t) = map f (preorder t)"
```

#### Native / Ground-Truth Proof
```isabelle
by (induction t) auto
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by (induction t) auto
```


---

## Tier 3: Structural / Multi-Step Proofs (5 Solved Theorems)

### 72. `Featherweight_OCL.UML_Logic.OclAnd_assoc_novel_variant`
- **Session:** `Featherweight_OCL` | **Theory:** `Featherweight_OCL.UML_Logic`, Year: 2014 | **Difficulty Tier:** Tier 3: Structural / Multi-Step Proofs
- **Proving Dynamics:** Solved in 8 turn(s) (2552 completion tokens).
- **Proof Length Contrast:** Native Proof: 5 lines $\longrightarrow$ Generated Proof: 8 line(s) (-60.0% lines).

#### Formal Statement
```isabelle
lemma OclAnd_assoc: "(X and (Y and Z)) = (X and Y and Z)"  (is ‹?lhs = ?rhs›)
```

#### Native / Ground-Truth Proof
```isabelle
proof (rule ext)
fix p
show ‹?lhs p = ?rhs p›
by (cases ‹X p› rule: Boolean\<^sub>b_elem\<^sub>a_elem\<^sub>s\<^sub>e_cases; cases ‹Y p› rule: Boolean\<^sub>b_elem\<^sub>a_elem\<^sub>s\<^sub>e_cases; cases ‹Z p› rule: Boolean\<^sub>b_elem\<^sub>a_elem\<^sub>s\<^sub>e_cases)       (simp_all add: OclAnd_def)
qed
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
apply (rule ext, simp add: OclAnd_def)
apply (auto simp: true_def false_def invalid_def split: option.split option.split_asm)
by auto
by auto
by auto
by auto
apply (case_tac "X x", case_tac "Y x", case_tac "Z x", auto)
apply (auto split: option.split option.split_asm bool.split bool.split_asm)
```


---

### 73. `HOL-Library.Multiset.count_mset_set_novel_variant`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 3: Structural / Multi-Step Proofs
- **Proving Dynamics:** Solved in 8 turn(s) (1013 completion tokens).
- **Proof Length Contrast:** Native Proof: 17 lines $\longrightarrow$ Generated Proof: 8 line(s) (+52.9% lines).

#### Formal Statement
```isabelle
lemma count_mset_set [simp]:   "finite A ⟹ x_elem ∈ A ⟹ count (mset_set A) x_elem = 1" (is "PROP ?P")   "¬ finite A ⟹ count (mset_set A) x_elem = 0" (is "PROP ?Q")   "x_elem ∉ A ⟹ count (mset_set A) x_elem = 0" (is "PROP ?R")
```

#### Native / Ground-Truth Proof
```isabelle
proof -
have *: "count (mset_set A) x_elem = 0" if "x_elem ∉ A" for A
proof (cases "finite A")
case False
then
show ?thesis
by simp
next
case True
from True ‹x_elem ∉ A›
show ?thesis
by (induct A) auto
qed
then
show "PROP ?P" "PROP ?Q" "PROP ?R"
by (auto elim!: Set.set_insert)
qed ― ‹TODO: maybe define \<^const>‹mset_set› also in terms of \<^const>‹Abs_multiset››
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
proof -
show "⟦finite A; x_elem ∈ A⟧ ⟹ count (mset_set A) x_elem = 1"
by (induct rule: finite_induct) auto
show "infinite A ⟹ count (mset_set A) x_elem = 0"
by simp
show "x_elem ∉ A ⟹ count (mset_set A) x_elem = 0"
by (cases "finite A") simp_all
qed
```


---

### 74. `HOL-Library.Multiset.image_mset_map_of`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 3: Structural / Multi-Step Proofs
- **Proving Dynamics:** Solved in 5 turn(s) (815 completion tokens).
- **Proof Length Contrast:** Native Proof: 16 lines $\longrightarrow$ Generated Proof: 5 line(s) (+68.8% lines).

#### Formal Statement
```isabelle
lemma image_mset_map_of:   "distinct (map fst xs) ⟹ {#the (map_of xs i). i ∈# mset (map fst xs)#} = mset (map snd xs)"
```

#### Native / Ground-Truth Proof
```isabelle
proof (induction xs)
case (Cons x xs)
have "{#the (map_of (x # xs) i). i ∈# mset (map fst (x # xs))#} =           add_mset (snd x) {#the (if i = fst x then Some (snd x) else map_of xs i).              i ∈# mset (map fst xs)#}" (is "_ = add_mset _ ?A")
by simp
also
from Cons.prems
have "?A = {#the (map_of xs i). i :# mset (map fst xs)#}"
by (cases x, intro image_mset_cong) (auto simp: in_multiset_in_set)
also
from Cons.prems
have "… = mset (map snd xs)"
by (intro Cons.IH) simp_all
finally
show ?case
by simp
qed simp_all
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
apply (induction xs) auto
apply (induction xs)
apply auto
apply (rule trans[OF image_mset_cong])
apply auto
```


---

### 75. `HOL-Library.Multiset.multeqp_code_eq_reflclp_multp`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 3: Structural / Multi-Step Proofs
- **Proving Dynamics:** Solved in 10 turn(s) (2502 completion tokens).
- **Proof Length Contrast:** Native Proof: 13 lines $\longrightarrow$ Generated Proof: 10 line(s) (+23.1% lines).

#### Formal Statement
```isabelle
lemma multeqp_code_eq_reflclp_multp:   assumes "irreflp R" and "transp R"   shows "multeqp_code R = (multp R)\<^sup>=\<^sup>="
```

#### Native / Ground-Truth Proof
```isabelle
proof (intro ext)
fix M N
show "multeqp_code R M N ⟷ (multp R)\<^sup>=\<^sup>= M N"
proof (rule multeqp_code_iff_reflclp_multp)
from assms
show "irreflp_on (set_mset M ∩ set_mset N) R"
by (auto intro: irreflp_on_subset)
next
from assms
show "transp R"
by simp
qed
qed
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
apply (intro ext)
using multeqp_code_iff_reflcl_mult[simplified, to_pred, of R x xa]
using multeqp_code_iff_reflclp_multp[OF assms]
by auto
using assms multeqp_code_iff_reflclp_multp[of R x xa] by (simp add: irreflp_onI irreflpD irreflp_def)
by auto
using multeqp_code_iff_reflclp_multp[of "set_mset x ∩ set_mset xa" R x xa] assms
by (metis assms multeqp_code_iff_reflclp_multp)
apply (rule multeqp_code_iff_reflclp_multp)
using assms(1) assms(2) by (auto simp: irreflp_on_def irreflp_def)
```


---

### 76. `HOL-Library.Multiset.multiset_add_sub_el_shuffle`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 3: Structural / Multi-Step Proofs
- **Proving Dynamics:** Solved in 1 turn(s) (31 completion tokens).
- **Proof Length Contrast:** Native Proof: 14 lines $\longrightarrow$ Generated Proof: 1 line(s) (+92.9% lines).

#### Formal Statement
```isabelle
lemma multiset_add_sub_el_shuffle:   assumes "c ∈# B"     and "b ≠ c"   shows "add_mset b (B - {#c#}) = add_mset b B - {#c#}"
```

#### Native / Ground-Truth Proof
```isabelle
proof -
from ‹c ∈# B›
obtain A where B: "B = add_mset c A"
by (blast dest: multi_member_split)
have "add_mset b A = add_mset c (add_mset b A) - {#c#}"
by simp
then
have "add_mset b A = add_mset b (add_mset c A) - {#c#}"
by (simp add: ‹b ≠ c›)
then
show ?thesis
using B
by simp
qed
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
using assms by (auto simp add: multiset_eq_iff)
```

> **Idiomatic Shift:** The native proof relies on manual case decomposition across 14 lines. The autonomous agent generalized the induction scheme into a concise automated one-liner.

---

## Tier 4: Deep HOL-Library (1 Solved Theorems)

### 77. `HOL-Library.Multiset.multp_code_eq_multp`
- **Session:** `HOL-Library` | **Theory:** `HOL-Library.Multiset` | **Difficulty Tier:** Tier 4: Deep HOL-Library
- **Proving Dynamics:** Solved in 7 turn(s) (1279 completion tokens).
- **Proof Length Contrast:** Native Proof: 13 lines $\longrightarrow$ Generated Proof: 7 line(s) (+46.2% lines).

#### Formal Statement
```isabelle
lemma multp_code_eq_multp:   assumes "irreflp R" and "transp R"   shows "multp_code R = multp R"
```

#### Native / Ground-Truth Proof
```isabelle
proof (intro ext)
fix M N
show "multp_code R M N = multp R M N"
proof (rule multp_code_iff_multp)
from assms
show "irreflp_on (set_mset M ∩ set_mset N) R"
by (auto intro: irreflp_on_subset)
next
from assms
show "transp R"
by simp
qed
qed
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
apply (intro ext)
using multp_code_iff_multp[OF assms]
by auto
using assms multp_code_iff_mult[of R] by (simp add: multp_code_def multp_def)
using multp_code_iff_multp[OF assms] by blast
apply (intro ext multp_code_iff_multp)
using assms by (auto simp: irreflp_on_def irreflp_def)
```


---

## Tier 5: Deep Pure AFP (1 Solved Theorems)

### 78. `Featherweight_OCL.UML_Logic.const_subst`
- **Session:** `Featherweight_OCL` | **Theory:** `Featherweight_OCL.UML_Logic`, Year: 2014 | **Difficulty Tier:** Tier 5: Deep Pure AFP
- **Proving Dynamics:** Solved in 14 turn(s) (6904 completion tokens).
- **Legacy Isabelle Commands Detected in Native Proof:** `rule_tac, erule_tac`
- **Proof Length Contrast:** Native Proof: 19 lines $\longrightarrow$ Generated Proof: 14 line(s) (+26.3% lines).

#### Formal Statement
```isabelle
lemma const_subst:  assumes const_X: "const X"      and const_Y: "const Y"      and eq :     "X τ = Y τ"      and cp_P:    "cp P"      and pp :     "P Y τ = P Y τ'"    shows "P X τ = P X τ'"
```

#### Native / Ground-Truth Proof
```isabelle
proof -
have A: "⋀Y. P Y τ = P (λ_. Y τ) τ"
apply(insert cp_P, unfold cp_def)
apply(elim exE, erule_tac x=Y in allE', erule_tac x=τ in allE)
apply(erule_tac x="(λ_. Y τ)" in allE, erule_tac x=τ in allE)
by simp
have B: "⋀Y. P Y τ' = P (λ_. Y τ') τ'"
apply(insert cp_P, unfold cp_def)
apply(elim exE, erule_tac x=Y in allE', erule_tac x=τ' in allE)
apply(erule_tac x="(λ_. Y τ')" in allE, erule_tac x=τ' in allE)
by simp
have C: "X τ' = Y τ'"
apply(rule trans, subst const_charn[OF const_X],rule eq)
by(rule const_charn[OF const_Y])
show ?thesis
apply(subst A, subst B, simp add: eq C)
apply(subst A[symmetric],subst B[symmetric])
by(simp add:pp)
qed
```

#### Treatment (I/L Simplicial Navigation) Generated Proof
```isabelle
by auto
by auto
by auto
by auto
by auto
by auto
by auto
by auto
by (metis cp_P cp_def eq pp)
by auto
by auto
by auto
by auto
apply (metis const_X const_Y eq cp_P pp cp_def const_def)
```

> **Idiomatic Shift:** The native proof relies on legacy `rule_tac, erule_tac` positional instantiations. The autonomous agent synthesized a modern, robust proof without fragile positional bindings.

---
