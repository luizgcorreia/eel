# EDEL / EEL: Epistemic Evolution Landscapes

Modular pipeline for embedding-driven epistemic landscapes, scientific evolution analysis, and citation graph geometry.

---

## 1. Quickstart & Local Installation

### Prerequisites & Configuration
1. Clone the repository and copy the environment template:
   ```bash
   cp .env.example .env
   ```
2. Fill in your API keys (OpenAI, Voyage AI, OpenAlex) in `.env`.

### Option A: Using `uv` (Recommended)
```bash
# Create and activate virtual environment with Python 3.11
uv venv --python 3.11 .venv
source .venv/bin/activate

# Install project dependencies in editable mode
uv pip install -e .
```

### Option B: Using Conda
```bash
conda create -n edel python=3.11
conda activate edel
conda install -c conda-forge pyarrow
pip install -e .
```

---

## 2. Remote Compute Infrastructure

The project is configured to run on two remote servers: the **IME USP Cluster** (for heavy GPU and high-memory workloads) and the **Exeter Erdos Server** (for storage, tunneling, and dashboard hosting).

### A. IME USP Cluster (`deeptwelve`)

The IME USP server family features a high-performance compute node with 2x NVIDIA RTX A5000 GPUs:

| Component | Host / Identifier | Role | Specs |
| :--- | :--- | :--- | :--- |
| **Lobby Host** | `shell.vision.ime.usp.br` (internal: `net03`) | SSH Gateway / Jump Host | Gateway only. **No experiments allowed.** |
| **Processing Node** | `deeptwelve` | Compute & Experiment Node | 64 CPU cores, 251 GB RAM, 2x NVIDIA RTX A5000 (24GB VRAM each), 24 TB NFS storage |

#### Cardinal Rule: Always Run Compute on `deeptwelve`
The login machine `shell.vision.ime.usp.br` (`net03`) is solely a gateway lobby. Whenever you connect, verify your hostname (`hostname`) and switch to `deeptwelve`:
```bash
ssh deeptwelve
```

#### SSH Configuration (Recommended)
Add the following to your local `~/.ssh/config` for direct ProxyJump access:
```sshconfig
Host ime-usp
    Hostname shell.vision.ime.usp.br
    User jmena

Host ime-deeptwelve
    Hostname deeptwelve
    User jmena
    ProxyJump ime-usp
```

#### Quick Remote Commands
- **Direct shell on compute node:**
  ```bash
  ssh ime-deeptwelve
  ```
- **Activate the remote virtual environment:**
  ```bash
  cd ~/lcorreia/eel && source .venv/bin/activate
  ```
- **Execute commands on `deeptwelve` via local helper:**
  ```bash
  python3 scripts/ssh_ime.py --cmd "python -c 'import torch; print(torch.cuda.is_available())'"
  ```
- **Check GPU status remotely:**
  ```bash
  python3 scripts/ssh_ime.py --gpu
  ```
- **Automated setup on `deeptwelve`:**
  ```bash
  bash scripts/setup_ime_env.sh
  ```
For detailed AI agent operating procedures, see [AGENTS.md](AGENTS.md).

---

### B. Exeter Erdos Server (`erdos.ex.ac.uk`)

The Exeter Erdos server is used for persistent processes, data backups, and dashboard hosting.

- **Host:** `erdos.ex.ac.uk`
- **SSH Port:** `9022`

#### SSH Configuration
```sshconfig
Host erdos
    Hostname erdos.ex.ac.uk
    Port 9022
    User lcorreia
```

#### Interactive Dashboard & Port Tunneling
To launch and view the EDEL Dash interactive visualization dashboard:
1. **On Erdos:**
   ```bash
   bash scripts/run_dashboard.sh
   ```
2. **On your local machine (SSH Port Forwarding):**
   ```bash
   ssh -p 9022 -L 8050:localhost:8050 erdos
   ```
3. Open `http://localhost:8050` in your web browser.

#### Resilient Google Drive Backups
Erdos includes automated, background screen-managed backups of artifacts:
```bash
# Start background backup session
./scripts/run_backup_screen.sh start

# Check backup status
./scripts/run_backup_screen.sh status

# View live backup logs
./scripts/run_backup_screen.sh logs
```

---

## 3. Running Experiments & Pipeline

### CLI Execution
```bash
python scripts/run_experiment.py --base-path artifacts --make-plots
```

### In Python / Jupyter Notebooks
```python
from edel.config.defaults import RUN_CONFIG
from edel.pipeline.run import run_pipeline

artifacts = run_pipeline(RUN_CONFIG, base_path="artifacts")
```

### Deterministic Artifact Storage
Pipeline stages persist artifacts with deterministic hashing:
```
<base_path>/<stage>/<label>/<name>__<hash_segment>.(parquet|pkl)
```
Use `edel.io.artifact.make_stage_artifact(...)` and `save_artifact(...)` / `load_artifact(...)`.

---

## 4. Testing

Run the automated test suite:
```bash
pytest tests/
```

Run stage-specific tests:
```bash
pytest tests/test_stage_1_data.py
```
