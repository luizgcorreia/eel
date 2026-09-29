"""Legacy I/R Theory Ingestion Implementation.

Communicates with Isabelle REPL over TCP to ingest and decompose loaded theories.
"""

from __future__ import annotations

import os
import re
from typing import Any
import pandas as pd

from edel.il.aspects import _extract_dependencies, extract_aspects
from edel.il.ingest import EphemeralReplClient, ingest_session_lemmas
from edel.il.ingest_interface import BaseTheoryIngester
from edel.il.metadata import AFPMetadataParser
from edel.il.parser import group_segments_to_lemmas, parse_source_segments


class IrTheoryIngester(BaseTheoryIngester):
    """Theory ingester connecting to Amazon's AutoCorrode ir/repl.py daemon."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 9147,
        token: str = "",
        **kwargs: Any,
    ):
        self.host = host
        self.port = port
        self.token = token or os.getenv("IR_AUTH_TOKEN", "")
        self.client = EphemeralReplClient(host=self.host, port=self.port, token=self.token)
        self.metadata_parser = AFPMetadataParser()

    def list_theories(self, session: str = "", pattern: str | None = None) -> list[str]:
        """Fetch all theories loaded in the active I/R session."""
        raw_thys = self.client.send("Ir.theories ();")
        theories = [t.strip() for t in raw_thys.splitlines() if t.strip()]
        if pattern:
            regex = re.compile(pattern)
            theories = [t for t in theories if regex.search(t)]
        return theories

    def ingest_theory(self, theory_name: str, session: str = "") -> list[dict[str, Any]]:
        """Fetch source and source_map for a single theory and extract aspect records."""
        # 1. Fetch source segments
        raw_source = self.client.send(f'Ir.source "{theory_name}" 0 ~1;')
        if not raw_source.strip():
            return []

        segments = parse_source_segments(raw_source)

        # 2. Fetch segment keyword mapping
        raw_map = self.client.send(f'Ir.source_map "{theory_name}" 0 ~1;')
        seg_map = {}
        for line in raw_map.splitlines():
            m = re.match(r'\s*(\d+)\s+(\S+)\s+(\d+)\s+(\d+)\s+(\S+)', line)
            if m:
                seg_map[int(m.group(1))] = {
                    "keyword": m.group(2),
                    "line": int(m.group(3)),
                    "offset": int(m.group(4)),
                    "file": m.group(5).strip(),
                    "theory": theory_name,
                }

        # 3. Group segments into logical lemma/definition units
        lemmas = group_segments_to_lemmas(seg_map, segments)

        # 4. Resolve AFP theory metadata
        entry_name = theory_name.split('.')[0] if '.' in theory_name else theory_name
        entry_meta = self.metadata_parser.load_entry_metadata(entry_name)
        pub_year = None
        date_str = entry_meta.get("date", "")
        if date_str:
            try:
                parts = date_str.split("-")
                if parts and parts[0].isdigit():
                    pub_year = int(parts[0])
            except Exception:
                pass

        records = []
        for lemma in lemmas:
            aspects = extract_aspects(lemma, text_comments=lemma.get("text_comments", []))
            records.append({
                "title": lemma["id"],
                "problem": aspects["aspect_statement"],
                "method": aspects["aspect_strategy"],
                "finding": aspects["aspect_dependencies"],
                "interpretation": aspects["aspect_context"],
                "theory": lemma["theory"],
                "session": session,
                "locale": lemma.get("locale", ""),
                "context_scope": lemma.get("context_scope", "global"),
                "attributes": lemma.get("attributes", []),
                "rule_type": lemma.get("rule_type", "general_theorem"),
                "keyword": lemma["keyword"],
                "file": lemma["file"],
                "line": lemma["line"],
                "proof_text": lemma["proof_text"],
                "statement_text": lemma["statement_text"],
                "proof_steps": lemma.get("proof_steps", []),
                "cited_deps": _extract_dependencies(lemma["proof_text"]),
                "dependents": "none",
                "publication_year": pub_year,
            })

        return records

    def ingest_session(self, session: str = "", pattern: str | None = None) -> pd.DataFrame:
        """Ingest entire session using the batch method."""
        return ingest_session_lemmas(
            host=self.host,
            port=self.port,
            token=self.token,
            theory_filter=pattern,
        )
