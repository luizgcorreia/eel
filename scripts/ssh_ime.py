#!/usr/bin/env python3
"""
Utility script to interact with the IME USP server family (lobby: shell / compute: deeptwelve).
Reads configuration from .env or ~/.ssh/config.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load local .env
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

REMOTE_HOST_ALIAS = "ime-deeptwelve"
REMOTE_REPO_DIR = os.getenv("IME_REPO_PATH", "~/lcorreia/eel")


def run_ssh_command(cmd: str, activate_venv: bool = True):
    """Executes a command on deeptwelve via SSH."""
    if activate_venv:
        full_cmd = f"cd {REMOTE_REPO_DIR} && source .venv/bin/activate && {cmd}"
    else:
        full_cmd = cmd

    print(f"\n[ssh_ime] Running on deeptwelve: {cmd}")
    ssh_cmd = ["ssh", REMOTE_HOST_ALIAS, full_cmd]
    res = subprocess.run(ssh_cmd)
    return res.returncode


def test_gpu():
    """Checks GPU and PyTorch CUDA availability on deeptwelve."""
    py_check = (
        "python -c \""
        "import torch; "
        "print('PyTorch Version:', torch.__version__); "
        "print('CUDA Available:', torch.cuda.is_available()); "
        "print('Device Count  :', torch.cuda.device_count()); "
        "[print(f'GPU {i}:', torch.cuda.get_device_name(i)) for i in range(torch.cuda.device_count())]"
        "\""
    )
    return run_ssh_command(f"nvidia-smi && {py_check}")


def sync_env():
    """Copies local .env to deeptwelve repo."""
    print(f"[ssh_ime] Syncing .env to {REMOTE_HOST_ALIAS}:{REMOTE_REPO_DIR}/.env...")
    res = subprocess.run(["scp", str(ROOT_DIR / ".env"), f"{REMOTE_HOST_ALIAS}:{REMOTE_REPO_DIR}/.env"])
    return res.returncode


def interactive_shell():
    """Opens an interactive SSH shell directly on deeptwelve."""
    print(f"[ssh_ime] Opening interactive shell on {REMOTE_HOST_ALIAS}...")
    subprocess.run(["ssh", "-t", REMOTE_HOST_ALIAS, f"cd {REMOTE_REPO_DIR} && bash -l"])


def main():
    parser = argparse.ArgumentParser(description="Helper for IME USP deeptwelve node.")
    parser.add_argument("--cmd", type=str, help="Command to run on deeptwelve in the venv.")
    parser.add_argument("--raw-cmd", type=str, help="Command to run without activating venv.")
    parser.add_argument("--gpu", action="store_true", help="Check GPU status on deeptwelve.")
    parser.add_argument("--sync-env", action="store_true", help="Sync .env to deeptwelve.")
    parser.add_argument("--shell", action="store_true", help="Open interactive terminal.")
    
    args = parser.parse_args()

    if args.gpu:
        sys.exit(test_gpu())
    elif args.sync_env:
        sys.exit(sync_env())
    elif args.cmd:
        sys.exit(run_ssh_command(args.cmd, activate_venv=True))
    elif args.raw_cmd:
        sys.exit(run_ssh_command(args.raw_cmd, activate_venv=False))
    elif args.shell:
        interactive_shell()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
