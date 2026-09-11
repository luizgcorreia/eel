# I/L (Isabelle/Landscape): Complete Setup and Replication Guide for EEL

This guide provides end-to-end instructions for deploying, configuring, and reproducing **I/L (Isabelle/Landscape)**, the higher-order epistemic navigation and retrieval system within the **EEL (Embedding-driven Epistemic Landscape)** framework. It covers system prerequisites, Isabelle2025-2 installation, Astral `uv` environment configuration, recorded heap compilation, multi-aspect vector index construction, Extended AutoCorrode Model Context Protocol (MCP) coordination, and replication of the 140-theorem / 420-trial empirical benchmark.

---

## 1. System Prerequisites

* **Operating System**: Linux (x86_64, tested on Ubuntu 22.04 / Debian 12 / Rocky Linux 9).
* **Hardware Requirements**:
  * Minimum: 16 CPU cores, 32 GB RAM (for local theory evaluation).
  * Production / Cluster: 64 CPU cores, 251 GB RAM, NVIDIA GPUs (as on compute node `deeptwelve` for bulk AFP heap recording and embedding).
* **Package Management**: Astral `uv` (recommended for ultra-fast, user-space Python runtime and dependency isolation).
* **VCS Tooling**: Git and Mercurial (`hg` $\ge 6.0$, required for AFP repository synchronisation).
* **API Credentials**:
  * `VOYAGE_API_KEY`: Required for generating 1024-dimensional embeddings via `voyage-code-3`.
  * `ANTHROPIC_API_KEY`: Required if executing agentic proof synthesis evaluations with Claude 3.5 Sonnet.

---

## 2. Step 1: Clone Repositories and the Archive of Formal Proofs (AFP)

1. Clone the EEL repository:
   ```bash
   git clone https://github.com/luizgcorreia/edel.git eel
   cd eel
   ```

2. Clone `AutoCorrode` (contains the headless Poly/ML REPL server):
   ```bash
   git clone https://github.com/luizgcorreia/AutoCorrode.git
   ```

3. Obtain the Archive of Formal Proofs (AFP 2025-2):
   ```bash
   mkdir -p external
   hg clone https://foss.heptapod.net/isa-afp/afp-2025-2 external/afp-2025-2
   ```

---

## 3. Step 2: Install and Configure Isabelle2025-2

I/L requires Isabelle2025-2 for its native SQLite command-span tracking via the `record_theories` kernel option.

1. Download and unpack Isabelle2025-2:
   ```bash
   wget https://isabelle.in.tum.de/website-Isabelle2025-2/dist/Isabelle2025-2_linux.tar.gz
   tar -xzf Isabelle2025-2_linux.tar.gz
   ```

2. Add Isabelle to your environment `PATH` (e.g., in `~/.bashrc`):
   ```bash
   export PATH="$HOME/Isabelle2025-2/bin:$PATH"
   ```

3. Register the AFP component with Isabelle:
   ```bash
   isabelle components -u $PWD/external/afp-2025-2
   ```
   Verify registration by running:
   ```bash
   isabelle components -l | grep afp
   ```

---

## 4. Step 3: Python Environment Setup via Astral `uv`

We maintain all runtime environments strictly in user-space without requiring `sudo` or system packages.

1. Install Astral `uv` (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   source $HOME/.cargo/env
   ```

2. Create a dedicated Python 3.11 virtual environment:
   ```bash
   uv venv .venv --python 3.11
   source .venv/bin/activate
   ```

3. Install EEL and required dependencies in editable mode:
   ```bash
   uv pip install -e .
   uv pip install -r AutoCorrode/ir/requirements.txt
   uv pip install voyageai anthropic pandas pyarrow openpyxl scipy
   ```

---

## 5. Step 4: Build Isabelle Heap with Recorded Proof States

For the ingestion parser to extract fine-grained tactics, intermediate claims, and coupled step maps, Isabelle session heaps must be compiled with command recording enabled:

```bash
isabelle build -b -o record_theories=true -d external/afp-2025-2/thys -j 16 HOL-Library
```

*Note: For the deep AFP benchmark evaluation (`Featherweight_OCL`), compile its session heap similarly:*
```bash
isabelle build -b -o record_theories=true -d external/afp-2025-2/thys -j 16 Featherweight_OCL
```

---

## 6. Step 5: Ingestion and EEL Multi-Aspect Vector Index Construction

The EEL pipeline segments formal mathematics into non-degenerate 3-simplices spanned by Problem ($P$), Method ($M$), Finding ($F$), and Interpretation ($I$) under the **Expert Epistemic Invariant**.

### Option A: Build Index for Specific Sessions (e.g., HOL-Library)
1. Launch the headless I/R REPL daemon:
   ```bash
   python AutoCorrode/ir/repl.py \
     --isabelle $HOME/Isabelle2025-2/bin/isabelle \
     --session HOL-Library \
     --dir external/afp-2025-2/thys \
     --mcp
   ```
   *Take note of the authentication token printed on startup (e.g., `IR_Repl.token: abc123xyz`).*

2. In a separate terminal, export credentials and run the ingestion builder:
   ```bash
   export IR_AUTH_TOKEN="abc123xyz"
   export VOYAGE_API_KEY="your-voyage-api-key"

   python -m edel.il.build_il_index \
     --provider voyage \
     --model voyage-code-3 \
     --filter "Multiset" \
     --output artifacts/rag_index
   ```

### Option B: Automated Incremental Indexing Across the AFP
To build the complete multi-theory index automatically:
```bash
export VOYAGE_API_KEY="your-voyage-api-key"

python scripts/build_afp_index.py \
  --isabelle $HOME/Isabelle2025-2/bin/isabelle \
  --afp-dir external/afp-2025-2/thys \
  --provider voyage \
  --model voyage-code-3 \
  --output artifacts/afp_rag_index
```
This script incrementally compiles sessions, launches ephemeral REPL processes, extracts aspects without simplex collapse, computes Landscape Height $H(v)$, and persists progress in `progress.json`.

---

## 7. Step 6: Extended AutoCorrode Multi-Agent Architecture Setup

EEL decouples reasoning, execution, and epistemic topology over the Model Context Protocol (MCP) by extending AWS Labs' open-source AutoCorrode framework:

```
                  ┌───────────────────────────────┐
                  │    Autonomous Proving Agent   │
                  │      (e.g.Claude 5 Sonnet)      │
                  └──────┬───────────────┬────────┘
                         │               │
      MCP Stdio JSON-RPC │               │ MCP Stdio JSON-RPC
                         ▼               ▼
           ┌──────────────────┐    ┌──────────────────┐
           │    I/L Server    │    │    I/R Server    │
           │(Isabelle/Landsc.)│    │  (Isabelle/REPL) │
           └─────────┬────────┘    └─────────┬────────┘
                     │                       │ TCP Socket (Port 9158)
                     ▼                       ▼
           ┌──────────────────┐    ┌──────────────────┐
           │ 4-Aspect Vectors │    │ Headless Poly/ML │
           │ Landscape Height │    │ Pre-warmed Heaps │
           └──────────────────┘    └──────────────────┘
```

### 1. I/L Server (Isabelle/Landscape)
Maintains the static multi-aspect index, computes 12 conditional transition operators $D(Y | x)$, applies Landscape Height ranking, and supports dynamic lemma insertion:
```bash
export VOYAGE_API_KEY="your-voyage-api-key"
export IL_INDEX_DIR="$PWD/artifacts/rag_index"
python -m edel.il.il_server
```

### 2. I/R Server (Isabelle/REPL)
Provides $\le 100$\,ms tactic-stepping and kernel validation:
```bash
python AutoCorrode/ir/repl.py \
  --isabelle $HOME/Isabelle2025-2/bin/isabelle \
  --session HOL-Library \
  --mcp
```

### 3. I/Q Server (Isabelle/Query)
Optional interactive inspection server embedded inside the Isabelle/PIDE editor environment.

---

## 8. Step 7: Configuring MCP Clients (Claude Code / Desktop / AGY)

To equip an LLM agent with the Extended AutoCorrode tools, register the servers in the client's configuration file (e.g., `~/.config/claude/mcp_config.json` or Claude Desktop):

```json
{
  "mcpServers": {
    "isabelle-repl": {
      "command": "/home/user/eel/.venv/bin/python",
      "args": [
        "/home/user/eel/AutoCorrode/ir/repl.py",
        "--isabelle", "/home/user/Isabelle2025-2/bin/isabelle",
        "--session", "HOL-Library",
        "--mcp"
      ]
    },
    "isabelle-landscape": {
      "command": "/home/user/eel/.venv/bin/python",
      "args": ["-m", "edel.il.il_server"],
      "env": {
        "VOYAGE_API_KEY": "your-voyage-api-key",
        "IL_EMBEDDING_PROVIDER": "voyage",
        "IL_EMBEDDING_MODEL": "voyage-code-3",
        "IL_INDEX_DIR": "/home/user/eel/artifacts/rag_index",
        "PYTHONPATH": "/home/user/eel"
      }
    }
  }
}
```

### Available Tool Catalog

| Server | Tool Name | Signature / Functionality |
| :--- | :--- | :--- |
| **I/L** | `search_lemmas_by_aspect` | Query $D(Y \mid x)$ specifying target aspect ($P, M, F, I$) and min height $H$ |
| **I/L** | `retrieve_lemma_aspects` | Retrieve complete 4-aspect micro-dossier for specific lemma |
| **I/L** | `store_lemma` | Dynamically graft newly proved theorem into session simplicial complex |
| **I/L** | `get_aspect_transition` | Compute transition vector between observed goal and library strategies |
| **I/R** | `ir_step` | Execute candidate tactic or Isar command span in the live Poly/ML kernel |
| **I/R** | `ir_undo` | Backtrack previous proof step |
| **I/R** | `ir_state` | Retrieve current subgoals and active proof context |

---

## 9. Step 8: Reproducing the 140-Theorem Benchmark

The benchmark evaluates 140 formal Isabelle/HOL theorems across 5 difficulty tiers under 3 experimental arms (Baseline Zero-RAG, Control Monolithic Flat RAG, Treatment I/L Simplicial Navigation):

1. **Verify Benchmark Datasets**:
   ```bash
   python -c "
   import pandas as pd
   df1 = pd.read_parquet('artifacts/experiment_benchmarks/stratified_100_lemmas.parquet')
   df2 = pd.read_parquet('artifacts/experiment_benchmarks/deep_structural_20_lemmas.parquet')
   df3 = pd.read_parquet('artifacts/experiment_benchmarks/afp_deep_structural_20_lemmas.parquet')
   print(f'Total benchmark theorems: {len(df1) + len(df2) + len(df3)}')
   "
   # Outputs: Total benchmark theorems: 140
   ```

2. **Execute Comparative Proving Trials**:
   ```bash
   export ANTHROPIC_API_KEY="your-anthropic-key"
   export VOYAGE_API_KEY="your-voyage-key"

   # Run evaluation across arms
   python -m edel.il.eval_agent \
     --theorems artifacts/experiment_benchmarks/stratified_100_lemmas.parquet \
     --arms baseline control treatment \
     --output-dir artifacts/experiment_results/benchmark_100_eval
   ```

3. **Compute Statistical Friction and Discordant Pairs**:
   ```bash
   python -m edel.il.eval_stats \
     --trials-dir artifacts/experiment_results/benchmark_100_eval \
     --bootstrap-iterations 10000
   ```
   This outputs the exact Wilcoxon signed-rank tests ($W = 2077.0, p = 0.00014$), discordant odds ratio (2.00x), and prompt caching economics.
