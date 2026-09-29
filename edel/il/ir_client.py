"""Legacy Isabelle/REPL (I/R) Prover Client implementation.

Wraps the socket communication with Amazon's AutoCorrode ir/repl.py daemon.
"""

from __future__ import annotations

import os
import re
import time
from typing import Any

from edel.il.ingest import EphemeralReplClient
from edel.il.prover_interface import BaseProverClient, StepResult


def ml_str(s: str) -> str:
    """Escape a Python string as an ML string literal."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def ml_int(n: int) -> str:
    """Format a Python int as an ML int literal (negative = ~N)."""
    return f"~{-n}" if n < 0 else str(n)


def is_proof_closed(step_cmd: str, step_output: str, repl_state: str) -> bool:
    """Determine whether the target proof goal has successfully closed."""
    # 1. Theorem registered in theory state
    if re.search(r"\b(theorem|lemma|corollary|proposition)\s+[\w\.\'\"\-]+:", step_output):
        return True

    # 2. Subgoals explicitly zero, but not inside an open Isar proof block
    if "0 subgoals" in repl_state or "No subgoals" in repl_state:
        if "proof (state)" in repl_state:
            norm = step_cmd.strip()
            return norm == "qed"
        return True

    # 3. Closing command executed and no goals remaining
    norm = step_cmd.strip()
    if (norm in ["done", "qed"] or norm.startswith("by ")) and "goal" not in repl_state and "proof (state)" not in repl_state:
        return True

    return False


class ReplProverClient(BaseProverClient):
    """Prover client communicating with a running Isabelle/REPL (ir/repl.py) process."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 9147,
        token: str = "",
        repl_client: EphemeralReplClient | None = None,
        **kwargs: Any,
    ):
        self.host = host
        self.port = port
        self.token = token or os.getenv("IR_AUTH_TOKEN", "")
        self.repl_client = repl_client or EphemeralReplClient(host=self.host, port=self.port, token=self.token)
        self.repl_id: str | None = None
        self.current_state: str = ""

    def init_session(self, theory_import: str, lemma_name: str, statement: str) -> str:
        """Initialize REPL session, load theory, and submit lemma statement."""
        self.repl_id = f"eval_{int(time.time() * 1000) % 100000}_{os.getpid()}"

        init_out = self.repl_client.send(f"Ir.init {ml_str(self.repl_id)} [{ml_str(theory_import)}];")
        if init_out.startswith("ERR") or "undefined entry for theory" in init_out:
            # Dynamically load theory if not in initial heap
            self.repl_client.send(f"Ir.load_theory {ml_str(theory_import)};")
            init_out = self.repl_client.send(f"Ir.init {ml_str(self.repl_id)} [{ml_str(theory_import)}];")

        if init_out.startswith("ERR") or "ERR:" in init_out:
            raise RuntimeError(f"Failed to initialize REPL session for theory {theory_import}: {init_out}")

        # Open the lemma goal
        step_init_out = self.repl_client.send(f"Ir.step {ml_str(self.repl_id)} {ml_str(statement)};")
        if step_init_out.startswith("ERR") or "ERR:" in step_init_out:
            raise RuntimeError(f"Failed to open lemma statement in REPL: {step_init_out}")

        # Fetch initial state
        try:
            self.current_state = self.repl_client.send(f"Ir.state {ml_str(self.repl_id)} ~1;")
        except Exception:
            self.current_state = f"goal (1 subgoal):\n 1. {statement}"

        return self.repl_id

    def step(self, command_or_edit: str) -> StepResult:
        """Send a single Isabelle command line to the REPL."""
        if not self.repl_id:
            raise RuntimeError("No active REPL session. Call init_session first.")

        step_cmd = command_or_edit.strip()
        step_out = self.repl_client.send(f"Ir.step {ml_str(self.repl_id)} {ml_str(step_cmd)};")

        is_error = step_out.startswith("ERR\n") or "ERR:" in step_out
        if not is_error:
            try:
                new_state = self.repl_client.send(f"Ir.state {ml_str(self.repl_id)} ~1;")
                self.current_state = new_state if new_state else step_out
            except Exception:
                self.current_state = step_out
        else:
            self.current_state = f"ERR: {step_out}"

        closed = not is_error and is_proof_closed(step_cmd, step_out, self.current_state)

        return StepResult(
            is_closed=closed,
            is_error=is_error,
            state_text=self.current_state,
            diagnostics=step_out if is_error else "",
            raw_response=step_out,
        )

    def get_state(self) -> str:
        """Return the current proof state from the REPL."""
        if not self.repl_id:
            return self.current_state
        try:
            state = self.repl_client.send(f"Ir.state {ml_str(self.repl_id)} ~1;")
            if state:
                self.current_state = state
        except Exception:
            pass
        return self.current_state

    def close_session(self) -> None:
        """Remove the REPL session from memory."""
        if self.repl_id:
            try:
                self.repl_client.send(f"Ir.remove {ml_str(self.repl_id)};")
            except Exception:
                pass
            self.repl_id = None
