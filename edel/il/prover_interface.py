"""Abstract Prover Client Interface for Interactive Theorem Proving Agents.

Defines the contract for communicating with Isabelle backends (I/R REPL vs. PIDE MCP).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class StepResult:
    """Standardized result of executing a proof step or applying a document edit."""

    is_closed: bool
    is_error: bool
    state_text: str
    diagnostics: str = ""
    raw_response: str = ""


class BaseProverClient(ABC):
    """Abstract interface governing communication with an interactive Isabelle backend."""

    @abstractmethod
    def init_session(self, theory_import: str, lemma_name: str, statement: str) -> str:
        """Initialize proof session, load theory context, and set the target lemma goal.

        Args:
            theory_import: Theory name or path to import (e.g. 'HOL-Library.Multiset').
            lemma_name: Identifier for the lemma.
            statement: Full formal statement text (e.g. 'lemma foo: "x + 0 = x"').

        Returns:
            Session identifier, REPL ID, or active scratch theory path.
        """
        pass

    @abstractmethod
    def step(self, command_or_edit: str) -> StepResult:
        """Execute a single tactic step or apply a document replacement.

        Args:
            command_or_edit: Isabelle command line (e.g. 'apply auto') or edit string.

        Returns:
            StepResult indicating proof closure, error status, and updated goal state.
        """
        pass

    @abstractmethod
    def get_state(self) -> str:
        """Return the current unproved subgoals and proof state."""
        pass

    @abstractmethod
    def close_session(self) -> None:
        """Clean up active processes, delete scratch files, and free resources."""
        pass


def get_prover_client(backend: str = "ir", **kwargs: Any) -> BaseProverClient:
    """Factory creating the appropriate prover client backend.

    Args:
        backend: Backend selector ('ir' for legacy REPL, 'pide' for PIDE MCP).
        **kwargs: Backend-specific configuration parameters.

    Returns:
        Instance of BaseProverClient.
    """
    backend_norm = backend.lower().strip()
    if backend_norm == "ir":
        from edel.il.ir_client import ReplProverClient
        return ReplProverClient(**kwargs)
    elif backend_norm == "pide":
        from edel.il.pide_client import PideMcpProverClient
        return PideMcpProverClient(**kwargs)
    else:
        raise ValueError(
            f"Unknown prover backend: '{backend}'. Supported backends: 'ir', 'pide'."
        )
