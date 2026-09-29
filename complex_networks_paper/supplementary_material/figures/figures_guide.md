# Supplementary Figures Guide: Topographic & Simplicial Visualisations of the AFP

**Project:** EEL (Embedding-driven Epistemic Landscape) & I/L (Isabelle/Landscape)  
**Paper:** *Higher-Order Epistemic Networks for Navigating the Archive of Formal Proofs*  
**Venue:** The 15th International Conference on Complex Networks and their Applications (CNA 2026)

---

## Overview

The main 12-page conference manuscript includes the composite system architecture diagram (Figure 1 in `main.tex`) and the 2D Epistemic Landscape Height Contour Terrain (Figure 2 in `main.tex`). This supplementary guide provides comprehensive mathematical details, projection methodologies, and qualitative epistemic interpretations for the **extended figures** generated during our empirical investigation (Figures S1, S2, S3, S4, and S5).

All figures are provided in both vector format (`.pdf`) for publication-grade rendering and raster format (`.png`) for quick inspection.

---

## Figure S1: Intrinsic Epistemic 3-Simplex of `const_subst`

* **Vector File:** [`fig_simplex_const_subst.pdf`](fig_simplex_const_subst.pdf)
* **Raster File:** [`fig_simplex_const_subst.png`](fig_simplex_const_subst.png)

```
                       Finding (F)
                         [Tactic]
                           /  \
                          /    \
                         /      \
                        /        \
                       /          \
                      /            \
          Problem (P) -------------- Interpretation (I)
          [Premises]  \            /  [Conclusion]
                       \          /
                        \        /
                         \      /
                        Method (M)
                        [Strategy]
```

### Mathematical Formulation & Projection Method
* **Target Theorem:** `Featherweight_OCL.UML_Logic.const_subst` (an un-memorised 19-line structural theorem establishing the preservation of logical constants under context substitution).
* **Embedding Coordinates:** The four aspect vectors ($\mathbf{p}, \mathbf{m}, \mathbf{f}, \mathbf{i} \in \mathbb{R}^{1024}$) were generated via `voyage-code-3`.
* **Projection:** Projected into 3D using **Classical Multidimensional Scaling (MDS)** (Principal Coordinate Analysis). Classical MDS preserves all $\binom{4}{2} = 6$ pairwise Euclidean distances between the aspect vertices:
  $$D_{ij} = \|\mathbf{x}_i - \mathbf{x}_j\|_2, \quad i, j \in \{P, M, F, I\}$$
* **Visual Topology:**
  * The sequential **discourse trajectory** $\tau_j = (P \to M \to F \to I)$ is rendered as a directed solid gold backbone.
  * The non-adjacent edges ($P \leftrightarrow F$, $M \leftrightarrow I$) and the epistemic closure edge ($P \leftrightarrow I$) are rendered with dashed structural lines.
  * **Zero Simplex Collapse:** The spatial volume of the resulting convex hull $\sigma_j = \text{conv}(\mathbf{p}, \mathbf{m}, \mathbf{f}, \mathbf{i})$ is strictly non-zero ($V(\sigma_j) > 0$), visually verifying that the Expert Epistemic Invariant prevents dimensional collapse into degenerate 2D triangles or 1D lines.

---

## Figure S2: Joint 3D PCA Projection of Epistemic 3-Simplices

* **Vector File:** [`fig_joint_simplices.pdf`](fig_joint_simplices.pdf)
* **Raster File:** [`fig_joint_simplices.png`](fig_joint_simplices.png)

### Mathematical Formulation & Projection Method
* **Theorems Projected:**
  1. `Featherweight_OCL.UML_Logic.const_subst` (Target structural theorem).
  2. `Featherweight_OCL.UML_Logic.cp_OclIf` (Parent theory structural bridge lemma).
  3. `Featherweight_OCL.UML_Logic.cp_OclNot` (Parent theory structural bridge lemma).
  4. `HOL-Library.Multiset.mset_le_incr_right` (Foundational algebra lemma).
* **Projection:** A joint 3D Principal Component Analysis (**PCA**) fitted over the union of aspect embeddings across all four theorems ($4 \times 4 = 16$ points in $\mathbb{R}^{1024}$).
* **Epistemic Interpretation:**
  * Demonstrates that lemmas within the same domain (`Featherweight_OCL`) form coordinated, oriented simplices clustered in a specific conceptual neighbourhood, yet maintain distinct internal trajectory geometries corresponding to their strategic decomposition.
  * In contrast, foundational algebraic lemmas (`Multiset`) occupy an orthogonal region of the shared ambient space $\mathbb{R}^{1024}$, illustrating how the embedding space clusters theorems by foundational semantic domains while preserving fine-grained inferential shapes.

---

## Figure S3: Strategic Transition Neighbourhood $D(M \mid p)$ for `const_subst`

* **Vector File:** [`fig_transition_neighborhood_const_subst.pdf`](fig_transition_neighborhood_const_subst.pdf)
* **Raster File:** [`fig_transition_neighborhood_const_subst.png`](fig_transition_neighborhood_const_subst.png)

### Mathematical Formulation & Projection Method
* **Operator:** Evaluates the conditional transition distribution operator:
  $$D(M \mid p) = \{ \mathbf{m}_j \mid \mathbf{p}_j \in N_k(\mathbf{p}) \}, \quad k = 5$$
* **Comparison with Flat Retrieval:**
  * **Flat Monolithic Retrieval:** Computes cosine similarity against unpartitioned proposition strings, returning generic boolean lemmas (`HOL.Boolean_Algebra`) that match lexical surface tokens but cannot discharge UML logic semantics.
  * **Simplicial Transition Mapping:** Takes the premise embedding $\mathbf{p}$ of `const_subst` and directly targets the Method manifold ($M$).
* **Outcome:** The top retrieved candidates directly include the critical parent bridge lemmas `cp_OclIf` and `cp_OclNot`. Providing these exact roadmap strategies enabled the agent to reconstruct the 19-line proof in 14 turns, whereas unguided baselines failed by exhausting their budget.

---

## Figure S4: 2D Epistemic Landscape Height ($H$) Contour Terrain (Figure 2 in Paper)

* **Vector File:** [`fig_landscape_terrain_2d.pdf`](fig_landscape_terrain_2d.pdf)
* **Raster File:** [`fig_landscape_terrain_2d.png`](fig_landscape_terrain_2d.png)

*(Note: This visualisation appears as Figure 2 in `main.tex`, featuring explicit domain boundaries across `Featherweight_OCL`, `HOL-Library`, `AVL-Trees`, and `Aho_Corasick`)*

### Mathematical Formulation & Projection Method
* **Corpus:** Evaluated across the 1,924 benchmark theorems and definitions.
* **Topological Centrality:** For each node $v$, **Landscape Height** $H(v)$ is computed over the transpose citation DAG $G^T$:
  $$H(v) = |\text{Reachable}_{G^T}(v)| - 1$$
* **Projection:** 2D dimensionality reduction via t-SNE / PCA over proposition embeddings, overlaid with a Gaussian Kernel Density Estimate (KDE) and continuous contour lines representing $H(v)$.
* **Topological Features:**
  * **Topological Peaks ($H > 10^3$):** Highly concentrated deductive anchors (such as `true`, `false`, `StrongEq`, and fundamental induction principles) that serve as foundational hubs across the library.
  * **Topological Lowlands ($H = 0$):** Peripheral helper lemmas and specialised application facts.
  * **Resolution of the Ephemeral Leaf Trap:** In fused ranking, this elevation surface heavily boosts foundational peaks while penalising peripheral leaves that happen to share superficial keywords with queries.

---

## Figure S5: 3D Continuous Epistemic Landscape Topography

* **Vector File:** [`fig_landscape_terrain_3d.pdf`](fig_landscape_terrain_3d.pdf)
* **Raster File:** [`fig_landscape_terrain_3d.png`](fig_landscape_terrain_3d.png)

### Mathematical Formulation & Projection Method
* **Elevation Surface:** Represents the formal mathematical library as a continuous epistemic landscape:
  $$z = \mathcal{H}(x, y) = \sum_{v \in V} H(v) \cdot K\left(\frac{(x - x_v, y - y_v)}{\sigma}\right)$$
  where $(x_v, y_v)$ are the 2D projected semantic coordinates of theorem $v$, $K(\cdot)$ is a radial basis kernel, and $H(v)$ is its Landscape Height.
* **Epistemic Dynamics:**
  * Mathematical reasoning is visualised as navigation across this 3D topography.
  * An agent seeking to prove an open goal navigates from low-altitude exploratory valleys towards established topological peaks to anchor its deductive steps, before descending along new trajectories to establish novel formal assertions.
