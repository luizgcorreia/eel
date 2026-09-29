"""Abstract Theory Ingestion Interface for Constructing Epistemic Knowledge Indices.

Defines the contract for extracting and decomposing Isabelle/AFP theories into 4-aspect units.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
import pandas as pd


class BaseTheoryIngester(ABC):
    """Abstract interface for ingesting and decomposing AFP theories into 4-aspect units."""

    @abstractmethod
    def list_theories(self, session: str, pattern: str | None = None) -> list[str]:
        """List all available theories within a formal session.

        Args:
            session: Isabelle session name (e.g. 'Featherweight_OCL', 'HOL-Library').
            pattern: Optional regex pattern to filter theory names.

        Returns:
            List of qualified theory names.
        """
        pass

    @abstractmethod
    def ingest_theory(self, theory_name: str, session: str = "") -> list[dict[str, Any]]:
        """Extract and decompose all lemmas in a theory into structured aspect dictionaries.

        Args:
            theory_name: Qualified name of the theory to ingest.
            session: Parent session name.

        Returns:
            List of dictionaries containing lemma metadata and 4 aspects.
        """
        pass

    def ingest_session(self, session: str, pattern: str | None = None) -> pd.DataFrame:
        """Batch-ingest all theories in a session into a unified DataFrame.

        Args:
            session: Isabelle session name.
            pattern: Optional regex pattern to filter theories.

        Returns:
            DataFrame of all ingested lemma aspect records.
        """
        theories = self.list_theories(session, pattern=pattern)
        records: list[dict[str, Any]] = []
        for thy in theories:
            records.extend(self.ingest_theory(thy, session=session))
        return pd.DataFrame(records)


def get_theory_ingester(backend: str = "ir", **kwargs: Any) -> BaseTheoryIngester:
    """Factory creating the appropriate theory ingester backend.

    Args:
        backend: Ingestion backend selector ('ir' for legacy REPL, 'pide' for PIDE MCP).
        **kwargs: Backend-specific configuration parameters.

    Returns:
        Instance of BaseTheoryIngester.
    """
    backend_norm = backend.lower().strip()
    if backend_norm == "ir":
        from edel.il.ir_ingest import IrTheoryIngester
        return IrTheoryIngester(**kwargs)
    elif backend_norm == "pide":
        from edel.il.pide_ingest import PideTheoryIngester
        return PideTheoryIngester(**kwargs)
    else:
        raise ValueError(
            f"Unknown ingest backend: '{backend}'. Supported backends: 'ir', 'pide'."
        )
