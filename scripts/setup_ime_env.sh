#!/usr/bin/env bash
# ==============================================================================
# Setup Environment for EDEL / EEL on IME USP Cluster (deeptwelve)
# Rootless / 100% user-space installation via astral uv
# ==============================================================================
set -euo pipefail

echo "=========================================================="
echo ">>> Checking Hostname..."
CURRENT_HOST=$(hostname)
echo "Current host: ${CURRENT_HOST}"

if [[ "${CURRENT_HOST}" != *"deeptwelve"* ]]; then
    echo "ERROR: You are running on ${CURRENT_HOST}, NOT deeptwelve!"
    echo "Please switch to deeptwelve first: ssh deeptwelve"
    exit 1
fi

echo "=========================================================="
echo ">>> Step 1: Setting up user-space tools (uv)..."
export PATH="${HOME}/.local/bin:${PATH}"

if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | bash
    export PATH="${HOME}/.local/bin:${PATH}"
fi
echo "uv version: $(uv --version)"

# Ensure ~/.bashrc has ~/.local/bin in PATH
if ! grep -q 'export PATH="${HOME}/.local/bin:${PATH}"' "${HOME}/.bashrc" 2>/dev/null; then
    echo 'export PATH="${HOME}/.local/bin:${PATH}"' >> "${HOME}/.bashrc"
    echo "Added ~/.local/bin to ~/.bashrc"
fi

echo "=========================================================="
echo ">>> Step 2: Setting up virtual environment with Python 3.11..."
REPO_DIR="${HOME}/lcorreia/eel"
mkdir -p "${REPO_DIR}"
cd "${REPO_DIR}"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment .venv with Python 3.11..."
    uv venv --python 3.11 .venv
else
    echo "Virtual environment .venv already exists at ${REPO_DIR}/.venv"
fi

echo "=========================================================="
echo ">>> Step 3: Installing PyTorch with CUDA 12.1..."
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

echo "=========================================================="
echo ">>> Step 4: Installing EEL repository dependencies..."
uv pip install -e .

echo "=========================================================="
echo ">>> Step 5: Validating Python & GPU Environment..."
.venv/bin/python -c '
import sys, torch
print("Python executable:", sys.executable)
print("Python version   :", sys.version.split()[0])
print("PyTorch version  :", torch.__version__)
print("CUDA available   :", torch.cuda.is_available())
if torch.cuda.is_available():
    print("Device count     :", torch.cuda.device_count())
    for i in range(torch.cuda.device_count()):
        print(f"  GPU {i}: {torch.cuda.get_device_name(i)} ({torch.cuda.get_device_properties(i).total_memory / (1024**3):.1f} GB)")
'

echo "=========================================================="
echo ">>> Environment setup complete on deeptwelve!"
echo "To activate in future sessions, run:"
echo "    source ~/lcorreia/eel/.venv/bin/activate"
echo "=========================================================="
