# AI Agent Operating Guidelines: IME USP Server Family (`deeptwelve`)

This document defines the operational procedures, architecture, and environment conventions for executing EDEL (now EEL) experiments and tasks on the **IME USP server family**.

---

## 1. Remote Server Architecture & Credentials

The IME USP cluster uses a two-tier architecture:

| Component | Host / Identifier | Role | Specs |
| :--- | :--- | :--- | :--- |
| **Lobby Host** | `shell.vision.ime.usp.br` (internal: `net03`) | SSH Gateway / Jump Host | Gateway only. **No experiments allowed.** |
| **Processing Node** | `deeptwelve` | Compute & Experiment Node | 64 CPU cores, 251 GB RAM, 2x NVIDIA RTX A5000 (24GB VRAM each) |

### Credentials & Configuration
- **Server:** `shell.vision.ime.usp.br`
- **User:** `jmena`
- **Password:** Referenced in `.env` (`IME_PASSWORD`)
- **Remote Repository Path:** `~/lcorreia/eel` (or `/home/jmena/lcorreia/eel`)
- **Filesystem:** The `/home` directory is shared via NFS (`homefs:/mnt/pool01-data/home`, 24 TB available) between `net03` and `deeptwelve`.

---

## 2. Cardinal Rule: Host Verification & Switching to `deeptwelve`

> [!IMPORTANT]
> **NEVER execute experiments, training runs, or heavy compute on the lobby machine (`net03` / `shell`).**
> Every time you login or execute remote operations:
> 1. Check current hostname: `hostname`
> 2. If it is `net03` (or not `deeptwelve`), you **MUST** switch to `deeptwelve`:
>    ```bash
>    ssh deeptwelve
>    ```
> 3. Verify you are on `deeptwelve`:
>    ```bash
>    [jmena@deeptwelve] ~ $ hostname
>    deeptwelve
>    ```

---

## 3. SSH Connectivity & Shortcuts

### Direct Access via Local SSH Config
Passwordless SSH public key authentication has been configured. The local `~/.ssh/config` has the following aliases:

```sshconfig
Host ime-usp
    Hostname shell.vision.ime.usp.br
    User jmena

Host ime-deeptwelve
    Hostname deeptwelve
    User jmena
    ProxyJump ime-usp
```

### Quick Commands from Local Terminal
- **Direct shell on compute node:**
  ```bash
  ssh ime-deeptwelve
  ```
- **Run command on `deeptwelve` from local machine:**
  ```bash
  ssh ime-deeptwelve "source ~/lcorreia/eel/.venv/bin/activate && python -c 'import torch; print(torch.cuda.is_available())'"
  ```
- **Copy files to remote repo:**
  ```bash
  scp local_file ime-deeptwelve:~/lcorreia/eel/path/
  ```

---

## 4. Rootless Environment & Dependency Management

> [!NOTE]
> We **do not** have `sudo` or `apt` permissions on the IME USP servers.
> All environments, runtimes, and dependencies must be maintained in user-space (`~`).

### Runtime Stack
- **Tooling:** Astral `uv` installed at `~/.local/bin/uv` (added to `~/.bashrc`).
- **Python Version:** Python 3.11 (installed via `uv python install 3.11`).
- **Virtual Environment:** `~/lcorreia/eel/.venv` (Python 3.11).
- **GPU Acceleration:** PyTorch with CUDA 12.1 runtime (`cu121`) matching the NVIDIA RTX A5000 GPUs and Driver 535.247.

### Activating the Environment on `deeptwelve`
```bash
cd ~/lcorreia/eel
source .venv/bin/activate
```

### Installing / Updating Dependencies
- Using `uv` (recommended, ultra-fast):
  ```bash
  ~/.local/bin/uv pip install -e .
  ```
- Installing PyTorch with CUDA 12.1:
  ```bash
  ~/.local/bin/uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
  ```

### Automated Re-setup Script
To reinstall or verify the environment on `deeptwelve` at any time, run:
```bash
bash ~/lcorreia/eel/scripts/setup_ime_env.sh
```

---

## 5. Hardware Verification Quick-Checks

When running on `deeptwelve`, agents can verify hardware status with:
```bash
# Verify GPU availability and memory
nvidia-smi

# Check active CPU resources
nproc
htop

# Check memory
free -h

# Check shared storage
df -h /home
```
