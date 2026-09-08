# First Index to try with I/L

For demonstrating this system to an expert like Achim Brucker, you want a theory that is self-contained, quick to compile, and features a clean mix of **inductive definitions**, **recursive functions**, and **highly structured Isar proofs** (rather than just simple automated one-liners like `by auto`).

Here are the two best candidates from HOL-Library to test and show him:

### Option 1: `HOL-Data_Structures.AVL_Set` (or `AVL_Trees` in the AFP)

- **What it is**: The classic verification of AVL trees (balanced binary search trees).
- **Why it's perfect for a demo**:
    - **Rich Isar Proof Skeletons**: Balance restoration proofs require structural induction and multiple nested case analyses (`case (Node l x d r) ... next ...`). This will beautifully highlight the distinction between the **Skeleton aspect** (which captures the mathematical cases and intermediate assertions like `have ... also ... finally show`) and the **Tactics aspect** (which captures the operational steps like `by (simp add: ...)`).
    - **Concrete Definitions**: Contains recursive function definitions (e.g., insertion, balance, rotation) that demonstrate how the **Definition Space** works and how lemmas dynamically map back to these definitions as `dependents`.

### Option 2: `HOL-Library.Multiset`

- **What it is**: The standard Isabelle library theory defining multisets (bags) and their operations.
- **Why it's perfect for a demo**:
    - **Zero Setup**: It is part of the core Isabelle heap, meaning you can test it immediately without needing to clone and register large external AFP sessions.
    - **Mathematical Implication Vectors**: Multisets feature deep order-theoretic properties and algebraic structures. This is a great testbed to show how the **Epistemic Closure Operator ($\mathbf{D}_{pi} = \mathbf{emb}_{\text{conclusion}} - \mathbf{emb}_{\text{premises}}$)** represents mathematical implications as geometric vectors rather than simple bag-of-words text matches.

---

### Key Points to Discuss with Achim Brucker

When you show him the system, here are the most valuable questions to ask him regarding our segmentation parser:

1. **Handling of Isar Proof Blocks**: Our parser uses command keywords (like `have`, `show`, `also`, `finally` for **Skeleton** vs. `by`, `apply`, `using` for **Tactics**). Ask him if he thinks intermediate calculations (e.g., `obtain` or complex `unfolding` chains) are best routed to the declarative skeleton or the operational tactics.
2. **Definition Boundaries**: In Isabelle, definitions can take many forms (`definition`, `fun`, `primrec`, `inductive`). Ask him if we should treat inductive predicate definitions differently from standard functional definitions when indexing them in our partitioned Definition Space.
3. **Local Facts vs. Global Lemmas**: In large proofs, provers often define local lemmas inside a `context` block. Ask how he recommends handling the scope of these lemmas so the agent doesn't get confused by local context names.

For the AFP entries, here are the best choices for your demonstration to Achim Brucker:

### 1. The Prime Candidate: `Featherweight_OCL`

- **Why**: **Achim Brucker is one of the co-authors of this entry** (along with Burkhart Wolff). It is his formalization of the UML/OCL semantics in Isabelle/HOL.
- **The Impact**:
    - Running the ingestion pipeline on `Featherweight_OCL` means he will know every definition and lemma by heart.
    - When you demo `search_lemmas` or `search_definitions`, he will be able to instantly tell you if the semantic retrieval is accurate, if the retrieved lemmas are actually relevant to the queries, and if the aspect partitioning (premises, skeleton, tactics, conclusion) makes mathematical sense in his domain.

### 2. The Algorithmic Candidate: `Dijkstra_Shortest_Path` (or `Gabow_SCC`)

- **Why**: These are classic verification theories by Peter Lammich using the Isabelle Refinement Framework.
- **The Impact**:
    - Refinement-based proofs are notoriously complex, containing layers of abstract-to-concrete definitions and structured step-by-step refinements.
    - This is perfect for testing the **Definition Space dependents mapping** (showing how concrete implementation lemmas link back to abstract algorithm definitions) and showing how the agent can find specific refinement strategies.

### 3. The Self-Contained Candidate: `Aho_Corasick`

- **Why**: A classic, self-contained string-matching algorithm.
- **The Impact**: It compiles quickly and contains a beautiful balance of inductive data types, recursive function definitions, and clean induction proofs.

---

### Recommended Testing Commands

To index `Featherweight_OCL` using our newly renamed `I/L` indexing script, make sure the REPL daemon is running against the heap containing `Featherweight_OCL` (or standard `HOL` if it can load it dynamically), then run:

```bash
export IR_AUTH_TOKEN="your-token"
export VOYAGE_API_KEY="your-voyage-key"

python -m edel.il.build_il_index \
  --provider voyage \
  --model voyage-code-3 \
  --filter "Featherweight_OCL" \
  --output artifacts/featherweight_ocl_index
```

Presenting him with search results from `Featherweight_OCL` will be the most compelling way to get his expert feedback on how to fine-tune the RAG parameters and the aspect parsing engine!