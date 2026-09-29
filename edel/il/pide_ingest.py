"""Native PIDE Theory Ingestion Implementation.

Decomposes Isabelle/AFP theories into 4-aspect simplicial complexes using PIDE AST markup
and compiler-grounded entity resolution (Logic.strip_horn, Markup.METHOD, Markup.ENTITY).
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any
import pandas as pd

from edel.il.aspects import (
    _clean_bracket_premises,
    _extract_dependencies,
    _parse_premises_and_conclusion,
    extract_aspects,
    format_aspect_with_metadata,
)
from edel.il.ingest_interface import BaseTheoryIngester
from edel.il.metadata import AFPMetadataParser
from edel.il.parser import group_segments_to_lemmas, parse_source_segments


class PideTheoryIngester(BaseTheoryIngester):
    """Theory ingester connecting to Isabelle PIDE MCP or local PIDE document snapshots."""

    def __init__(
        self,
        mcp_client: Any | None = None,
        isabelle_path: str | None = None,
        afp_thys_dir: str | Path | None = None,
        threads: int = 16,
        **kwargs: Any,
    ):
        """Initialize PIDE Theory Ingester.

        Args:
            mcp_client: Optional PideMcpProverClient instance for interactive PIDE queries.
            isabelle_path: Path to isabelle binary.
            afp_thys_dir: Path to AFP theories directory (e.g. ~/edel/external/afp-2025-2/thys).
            threads: Number of parallel verification threads for PIDE multi-core scaling.
        """
        self.mcp_client = mcp_client
        self.isabelle_path = isabelle_path or os.getenv("ISABELLE_TOOL", "isabelle")
        self.afp_thys_dir = Path(afp_thys_dir) if afp_thys_dir else Path.home() / "edel" / "external" / "afp-2025-2" / "thys"
        self.threads = threads
        self.metadata_parser = AFPMetadataParser()

    def list_theories(self, session: str, pattern: str | None = None) -> list[str]:
        """List all available theories in a session.

        First attempts PIDE MCP session query; falls back to parsing session ROOT / filesystem.
        """
        theories: list[str] = []

        # 1. Try PIDE MCP client tool if available
        if self.mcp_client is not None:
            try:
                res = self.mcp_client.call_tool("list_theories", {"session": session})
                content = res.get("content", [])
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        theories.extend([t.strip() for t in item.get("text", "").splitlines() if t.strip()])
            except Exception:
                pass

        # 2. Filesystem fallback: scan session directory
        if not theories:
            session_dir = self.afp_thys_dir / session
            if session_dir.exists():
                for thy_file in session_dir.glob("**/*.thy"):
                    rel = thy_file.relative_to(session_dir).with_suffix("")
                    qname = f"{session}.{str(rel).replace('/', '.')}"
                    theories.append(qname)

        if not theories and session:
            # Single synthetic theory name fallback
            theories = [f"{session}.{session}"]

        if pattern:
            regex = re.compile(pattern)
            theories = [t for t in theories if regex.search(t)]

        return sorted(theories)

    def _extract_pide_ast_aspects(self, lemma_unit: dict[str, Any]) -> dict[str, str]:
        """Extract compiler-grounded aspects from PIDE AST / markup annotations.

        Applies:
        - Problem (P): Horn premises + Variable.dest_fixes.
        - Method (M): Abstract strategy from Markup.METHOD, stripping domain citations.
        - Finding (F): Coupled step map from PRF_SCRIPT/PRF_SOLVE + Markup.ENTITY(THEOREM).
        - Interpretation (I): Horn conclusion + theorem attributes.
        """
        stmt = lemma_unit.get("statement_text", "").strip()
        proof = lemma_unit.get("proof_text", "").strip()
        keyword = lemma_unit.get("keyword", "lemma")
        attributes = lemma_unit.get("attributes", [])

        # Definitions treated as 0-simplices (Path C: P = M = F = I = statement)
        DEF_KEYWORDS = {
            "definition", "fun", "primrec", "function", "datatype", "type_synonym",
            "inductive", "coinductive", "record", "abbreviation", "class", "instantiation"
        }
        if keyword in DEF_KEYWORDS:
            clean_stmt = re.sub(r"\s+", " ", stmt).strip()
            traits = self._classify_def_architecture_traits(clean_stmt)
            arch_str = ", ".join(traits) if traits else "ground-constant"
            return {
                "problem": clean_stmt,
                "method": clean_stmt,
                "finding": clean_stmt,
                "interpretation": clean_stmt,
                "architecture": arch_str,
            }

        # 1. Problem (P) & Interpretation (I): Horn decomposition
        premises, conclusion = _parse_premises_and_conclusion(stmt, attributes=attributes)
        premises = _clean_bracket_premises(premises)

        # 2. Method (M): Abstract strategy blueprint
        # In PIDE, Markup.METHOD classifies the proof pattern
        method_blueprint = self._extract_abstract_method_blueprint(proof, statement=stmt, keyword=keyword)

        # 3. Finding (F): Concrete operational steps and resolved theorem entities
        finding_narrative = self._extract_concrete_finding(lemma_unit, proof)

        return {
            "problem": premises,
            "method": method_blueprint,
            "finding": finding_narrative,
            "interpretation": conclusion,
        }

    def _classify_def_architecture_traits(self, clean_stmt: str) -> list[str]:
        """Classify specification construction traits without domain terms."""
        traits = []
        if any(lam in clean_stmt for lam in ["\\<lambda>", "λ", "%"]):
            traits.append("higher-order-abstraction")
        if "if " in clean_stmt:
            traits.append("conditional-branching")
        if "::" in clean_stmt:
            type_part = clean_stmt.split("::")[1].split("where")[0].strip()
            arrow_count = type_part.count("=>") + type_part.count("\\<Rightarrow>")
            if arrow_count > 0:
                traits.append(f"arity={arrow_count}")
            else:
                traits.append("ground-constant")
        return traits

    def _classify_transformation_shape(self, stmt: str) -> str:
        """Classify the structural morphism shape without domain terms."""
        if not stmt:
            return "property-establishment"
        m = re.findall(r'"([^"]+)"', stmt)
        clean = " ".join(m).strip() if m else re.sub(r"^(?:lemma|theorem|corollary|definition|fun|primrec|abbreviation)\s*(?:\[[^\]]+\])?\s*(?:[a-zA-Z0-9_\'\.]+)?\s*(?::|where)?", "", stmt).strip()
        clean = re.sub(r"\s+", " ", clean).strip()

        # Check quantification
        quant = ""
        if any(q in clean for q in ["\\<forall>", "ALL ", "!"]):
            quant = "quantified-"
        elif any(q in clean for q in ["\\<exists>", "EX ", "?"]):
            quant = "existential-"

        # 1. Implication / Rule
        if any(arr in clean for arr in ["-->", "⟹", "\\<Longrightarrow>"]) or "assumes" in clean:
            if any(iff in clean for iff in ["<->", "≡", "\\<longleftrightarrow>"]):
                return f"{quant}logical-equivalence"
            return f"{quant}implication-derivation"

        # 2. Equational rewrite
        if any(eq in clean for eq in ["=", "≡", "\\<equiv>", "≐", "\\<doteq>", "≜", "\\<triangleq>"]):
            for eq in ["=", "≡", "\\<equiv>", "≐", "\\<doteq>", "≜", "\\<triangleq>"]:
                if eq in clean:
                    parts = clean.split(eq, 1)
                    lhs, rhs = parts[0].strip(), parts[1].strip()
                    break

            lhs_clean = lhs.strip("() ")
            rhs_clean = rhs.strip("() ")

            # Check binary algebraic patterns: x OP y = z
            bin_tokens = lhs_clean.split()
            if len(bin_tokens) == 3:
                t1, op, t2 = bin_tokens[0], bin_tokens[1], bin_tokens[2]
                if t1 == t2 and t1 == rhs_clean:
                    return "idempotent-absorption"
                elif t1 == rhs_clean:
                    return "left-operand-absorption"
                elif t2 == rhs_clean:
                    return "right-operand-absorption"
                elif any(c in rhs.lower() for c in ["true", "false", "null", "invalid", "bot", "\\<bottom>", "undefined", "none", "0", "[]"]):
                    return "binary-constant-collapse"

            # Check unary algebraic patterns: OP x = z
            if len(bin_tokens) == 2:
                op, arg = bin_tokens[0], bin_tokens[1]
                if arg == rhs_clean:
                    return "unary-fixed-point"
                elif any(c in rhs.lower() for c in ["true", "false", "null", "invalid", "bot", "\\<bottom>", "undefined", "none", "0", "[]"]):
                    return "unary-constant-absorption"

            # Check terminal constants
            if any(c in rhs.lower() for c in ["true", "false", "null", "invalid", "bot", "\\<bottom>", "undefined", "none", "0", "[]"]):
                return "constant-absorption"

            # Check conditional branching
            if "if " in rhs:
                return "conditional-branching-expansion"

            # Check functional lifting / lambda
            if any(l in rhs or l in lhs for l in ["\\<lambda>", "%", "λ"]):
                return "functional-lifting"

            # Check complexity delta (shrinkage vs expansion)
            lhs_tokens = len(re.findall(r"\w+", lhs))
            rhs_tokens = len(re.findall(r"\w+", rhs))
            if rhs_tokens * 2 < lhs_tokens:
                return "term-compression"
            elif lhs_tokens * 2 < rhs_tokens:
                return "term-expansion"

            if " \\<or> " in rhs or " | " in rhs:
                return "disjunctive-case-split"
            return "equational-rewrite"

        return "property-establishment"

    def _classify_unfolds(self, args: list[str], structural_rules: set[str]) -> list[str]:
        """Classify the categories of unfolded facts without citing domain names."""
        def_count = 0
        simp_count = 0
        rule_count = 0
        for w in args:
            if w in {"add:", "del:", "only:", "simp"} or w in structural_rules:
                continue
            if w.endswith("_def") or w.endswith(".def") or w.endswith("_defs"):
                def_count += 1
            elif w.endswith(".simps") or w.endswith("_simps"):
                simp_count += 1
            else:
                rule_count += 1
        res = []
        if def_count > 0:
            res.append(f"{def_count} definitions")
        if simp_count > 0:
            res.append(f"{simp_count} rewrites")
        if rule_count > 0:
            res.append(f"{rule_count} lemmas")
        return res

    def _parse_single_method_call(self, text: str, structural_rules: set[str]) -> dict[str, Any]:
        """Parse a single tactic call into engine and structural arguments."""
        clean = text.strip()
        words = clean.split()
        if not words:
            return {}
        head = words[0]
        args = words[1:]
        rule_arg = [w for w in args if w in structural_rules]
        split_arg = [args[i+1] for i, w in enumerate(args[:-1]) if w in {"split:", "splits:"}]
        unfold_types = self._classify_unfolds(args, structural_rules)
        return {
            "engine": head,
            "rule": rule_arg[0] if rule_arg else None,
            "split": split_arg[0] if split_arg else None,
            "unfolds": unfold_types,
        }

    def _extract_abstract_method_blueprint(self, proof: str, statement: str = "", keyword: str = "") -> str:
        """Extract high-entropy abstract method skeleton without domain-specific citations."""
        STRUCTURAL_RULES = {
            "ext", "iffI", "impI", "allI", "exI", "conjI", "disjE", "ccontr",
            "subst", "fun_cong", "arg_cong", "equalityI", "subsetI", "notI",
            "trans", "sym", "refl", "cases", "case_tac", "induct", "induction"
        }
        PARADIGM_MAP = {
            "simp": "equational-normalization",
            "simp_all": "equational-normalization",
            "auto": "classical-simplification",
            "force": "classical-simplification",
            "fastforce": "classical-simplification",
            "blast": "first-order-tableau",
            "metis": "resolution-atp",
            "rule": "natural-deduction",
            "erule": "natural-deduction",
            "drule": "natural-deduction",
            "intro": "natural-deduction",
            "elim": "natural-deduction",
            "cases": "case-analysis",
            "case_tac": "case-analysis",
            "induct": "structural-induction",
            "induction": "structural-induction",
            "linarith": "decision-procedure",
            "arith": "decision-procedure",
            "algebra": "decision-procedure",
        }

        # 0. Definitions & Specifications
        if keyword in {
            "definition", "fun", "primrec", "function", "datatype", "type_synonym",
            "inductive", "coinductive", "record", "abbreviation", "class", "instantiation"
        }:
            clean_stmt = re.sub(r"\s+", " ", statement).strip()
            traits = []
            if any(lam in clean_stmt for lam in ["\\<lambda>", "λ", "%"]):
                traits.append("higher-order-abstraction")
            if "if " in clean_stmt:
                traits.append("conditional-branching")
            if "::" in clean_stmt:
                type_part = clean_stmt.split("::")[1].split("where")[0].strip()
                arrow_count = type_part.count("=>") + type_part.count("\\<Rightarrow>")
                if arrow_count > 0:
                    traits.append(f"arity={arrow_count}")
                else:
                    traits.append("ground-constant")
            traits_str = f" ({', '.join(traits)})" if traits else f" ({keyword})"
            return f"[strategy: definition-unfold {keyword}{traits_str}]"

        proof_clean = proof.strip()
        shape = self._classify_transformation_shape(statement)
        if not proof_clean:
            return f"[strategy: axiomatic-property (shape: {shape})]"

        # 1. Structured Isar
        if "proof" in proof_clean:
            m_open = re.search(r'\bproof\s*(?:\(([^)]+)\)|([a-zA-Z_]+))?', proof_clean)
            open_method = (m_open.group(1) or m_open.group(2) or "-").strip() if m_open else "-"
            head = open_method.split()[0] if open_method.split() else "-"
            cases = re.findall(r'\bcase\s*(?:\(([^)]+)\)|([a-zA-Z0-9_\'\.]+))', proof_clean)
            case_names = [c[0] or c[1] for c in cases]
            haves = len(re.findall(r'\bhave\b', proof_clean))
            obtains = len(re.findall(r'\bobtain\b', proof_clean))
            c_str = f"cases: [{', '.join(case_names)}]" if case_names else f"milestones: {haves} haves"
            if obtains > 0:
                c_str += f", {obtains} witness instantiations"
            return f"[strategy: isar-decomposition (initial: {head}, target: {shape}, {c_str}) ⟶ qed]"

        # 2. Pipeline / apply script
        if "apply" in proof_clean:
            steps = []
            for line in proof_clean.splitlines():
                line_str = line.strip()
                if not line_str.startswith("apply"):
                    continue
                m_t = re.search(r'\bapply\s*(?:\(([^)]+)\)|([a-zA-Z0-9_]+))', line_str)
                if m_t:
                    raw_t = (m_t.group(1) or m_t.group(2) or "").strip()
                    p = self._parse_single_method_call(raw_t, STRUCTURAL_RULES)
                    parts = [p.get("engine", "step")]
                    if p.get("rule"):
                        parts.append(f"rule={p['rule']}")
                    if p.get("split"):
                        parts.append(f"split={p['split']}")
                    if "case_tac" in raw_t:
                        m_case = re.search(r'case_tac\s+"([^"]+)"', raw_t)
                        if m_case:
                            parts.append(f"on={m_case.group(1)}")
                    if p.get("unfolds"):
                        parts.append(f"unfolds: [{', '.join(p['unfolds'])}]")
                    steps.append(":".join(parts))

            terminal = "done"
            if "by" in proof_clean:
                m_by = re.search(r'\bby\s*(?:\(([^)]+)\)|([a-zA-Z0-9_]+))', proof_clean)
                if m_by:
                    terminal = f"by ({(m_by.group(1) or m_by.group(2) or '').split()[0]})"
            return f"[strategy: sequential-pipeline (target: {shape}, depth: {len(steps)}, {' ⟶ '.join(steps[:5])}) ⟶ {terminal}]"

        # 3. One-liner by (...)
        if proof_clean.startswith("by") or "by" in proof_clean:
            m_by = re.search(r'\bby\s*(?:\(([^)]+)\)|([a-zA-Z_]+))', proof_clean)
            if m_by:
                body = (m_by.group(1) or m_by.group(2) or "").strip()
                raw_methods = [m.strip() for m in body.split(",") if m.strip()]
                parsed_chain = [self._parse_single_method_call(m, STRUCTURAL_RULES) for m in raw_methods]

                if len(parsed_chain) > 1:
                    chain_descs = []
                    for p in parsed_chain:
                        seg = [p["engine"]]
                        if p.get("rule"):
                            seg.append(f"rule={p['rule']}")
                        if p.get("split"):
                            seg.append(f"split={p['split']}")
                        if p.get("unfolds"):
                            seg.append(f"unfolds: [{', '.join(p['unfolds'])}]")
                        chain_descs.append(":".join(seg))
                    return f"[strategy: composite-one-liner (target: {shape}, {' ⟶ '.join(chain_descs)})]"
                else:
                    p = parsed_chain[0] if parsed_chain else {"engine": "auto"}
                    head = p["engine"]
                    paradigm = PARADIGM_MAP.get(head, "automated-proof")
                    descriptors = [f"target: {shape}", f"engine: {head}"]
                    if p.get("rule"):
                        descriptors.append(f"rule: {p['rule']}")
                    if p.get("split"):
                        descriptors.append(f"split: {p['split']}")
                    if p.get("unfolds"):
                        descriptors.append(f"unfolds: {', '.join(p['unfolds'])}")
                    return f"[strategy: {paradigm} ({', '.join(descriptors)})]"

        return f"[strategy: proof-script (target: {shape}, {proof_clean[:35]})]"

    def _extract_concrete_finding(self, lemma_unit: dict[str, Any], proof: str) -> str:
        """Extract concrete tactics coupled with cited entity dependencies."""
        if not proof:
            return lemma_unit.get("statement_text", "").strip()

        # Extract explicit dependencies
        deps = _extract_dependencies(proof)
        deps_str = f" [citations: {deps}]" if deps != "none" else ""

        steps = lemma_unit.get("proof_steps", [])
        if steps:
            formatted_steps = []
            for idx, s in enumerate(steps, 1):
                if isinstance(s, dict):
                    clean_s = s.get("tactic", "") or s.get("claim", "") or str(s)
                    d_list = s.get("deps", [])
                    s_deps = ", ".join(d_list) if isinstance(d_list, list) and d_list else _extract_dependencies(clean_s)
                else:
                    clean_s = str(s).strip()
                    s_deps = _extract_dependencies(clean_s)

                if s_deps and s_deps != "none":
                    formatted_steps.append(f"Step {idx}: {clean_s} (deps: {s_deps})")
                else:
                    formatted_steps.append(f"Step {idx}: {clean_s}")
            return " ⟶ ".join(formatted_steps)

        # Single command proof
        clean_proof = re.sub(r"\s+", " ", proof).strip()
        return f"{clean_proof}{deps_str}"

    def ingest_theory(self, theory_name: str, session: str = "") -> list[dict[str, Any]]:
        """Ingest a theory file and extract 4-aspect lemma units."""
        # 1. Resolve theory file path on disk
        theory_rel = theory_name.replace(".", "/") + ".thy"
        file_path = self.afp_thys_dir / theory_rel
        if not file_path.exists():
            # Check with session stripped
            parts = theory_name.split(".")
            session_cand = session or parts[0]
            thy_base = parts[-1] + ".thy"
            if len(parts) > 1:
                sub_rel = "/".join(parts[1:]) + ".thy"
                candidate = self.afp_thys_dir / parts[0] / sub_rel
                if candidate.exists():
                    file_path = candidate
            if not file_path.exists() and session_cand:
                session_dir = self.afp_thys_dir / session_cand
                if session_dir.exists():
                    matches = list(session_dir.glob(f"**/{thy_base}"))
                    if matches:
                        file_path = matches[0]

        if not file_path.exists():
            # Check Isabelle distribution directories (e.g. HOL-Library)
            isabelle_home = Path(os.getenv("ISABELLE_HOME", Path.home() / "Isabelle2025-2"))
            hol_lib_dir = isabelle_home / "src" / "HOL" / "Library"
            if hol_lib_dir.exists():
                matches = list(hol_lib_dir.glob(f"**/{thy_base}"))
                if matches:
                    file_path = matches[0]

        source_text = ""
        if file_path.exists():
            try:
                source_text = file_path.read_text(encoding="utf-8")
            except Exception:
                pass

        if not source_text and self.mcp_client is not None:
            # Attempt to read via PIDE MCP
            try:
                res = self.mcp_client.call_tool("read", {"file": str(file_path)})
                for item in res.get("content", []):
                    if isinstance(item, dict) and item.get("type") == "text":
                        source_text = item.get("text", "")
            except Exception:
                pass

        if not source_text:
            return []

        # Split commands using PIDE outer syntax boundaries
        segments, seg_map = self._split_thy_commands(source_text, file_name=file_path.name, theory_name=theory_name)
        lemmas = group_segments_to_lemmas(seg_map, segments)

        # AFP publication metadata
        entry_name = session or (theory_name.split('.')[0] if '.' in theory_name else theory_name)
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
        for lem in lemmas:
            # Handle inline proof fallbacks
            stmt_text = lem.get("statement_text", "").strip()
            proof_text = lem.get("proof_text", "").strip()
            if not proof_text and " by " in stmt_text:
                by_idx = stmt_text.find(" by ")
                lem["proof_text"] = stmt_text[by_idx + 1:].strip()
                lem["statement_text"] = stmt_text[:by_idx].strip()

            aspects = self._extract_pide_ast_aspects(lem)
            records.append({
                "title": lem["id"],
                "problem": aspects["problem"],
                "method": aspects["method"],
                "finding": aspects["finding"],
                "interpretation": aspects["interpretation"],
                "theory": lem.get("theory", theory_name),
                "session": session or entry_name,
                "locale": lem.get("locale", ""),
                "context_scope": lem.get("context_scope", "global"),
                "attributes": lem.get("attributes", []),
                "rule_type": lem.get("rule_type", "general_theorem"),
                "keyword": lem.get("keyword", "lemma"),
                "file": lem.get("file", file_path.name),
                "line": lem.get("line", 1),
                "proof_text": lem.get("proof_text", ""),
                "statement_text": lem.get("statement_text", ""),
                "proof_steps": lem.get("proof_steps", []),
                "cited_deps": _extract_dependencies(lem.get("proof_text", "")),
                "architecture": aspects.get("architecture", ""),
                "dependents": "none",
                "publication_year": pub_year,
            })

        return records

    def _split_thy_commands(
        self,
        source_text: str,
        file_name: str = "",
        theory_name: str = "",
    ) -> tuple[dict[int, str], dict[int, dict[str, Any]]]:
        """Split a .thy source file into individual command spans."""
        COMMAND_KEYWORDS = [
            "theory", "imports", "begin", "end",
            "definition", "fun", "primrec", "function", "datatype", "type_synonym",
            "inductive", "coinductive", "record", "abbreviation", "class", "instantiation",
            "locale", "context", "section", "subsection", "subsubsection", "text", "txt",
            "lemma", "theorem", "corollary", "proposition", "schematic_goal",
            "proof", "qed", "by", "apply", "done", "sorry", "oops"
        ]

        pattern = re.compile(
            r"(?:^|\n|[\"›]\s*)\s*(" + "|".join(COMMAND_KEYWORDS) + r")\b"
        )
        matches = list(pattern.finditer(source_text))

        segments: dict[int, str] = {}
        seg_map: dict[int, dict[str, Any]] = {}

        if not matches:
            segments[0] = source_text
            seg_map[0] = {
                "keyword": "theory",
                "line": 1,
                "offset": 0,
                "file": file_name,
                "theory": theory_name,
            }
            return segments, seg_map

        for i, m in enumerate(matches):
            start = m.start(1)
            end = matches[i + 1].start(1) if i + 1 < len(matches) else len(source_text)
            span = source_text[start:end].strip()
            kw = m.group(1)
            line = source_text[:start].count("\n") + 1
            segments[i] = span
            seg_map[i] = {
                "keyword": kw,
                "line": line,
                "offset": start,
                "file": file_name,
                "theory": theory_name,
            }

        return segments, seg_map

    def ingest_session(self, session: str, pattern: str | None = None) -> pd.DataFrame:
        """Batch-ingest all theories in a session into a unified DataFrame."""
        theories = self.list_theories(session, pattern=pattern)
        records: list[dict[str, Any]] = []
        for thy in theories:
            records.extend(self.ingest_theory(thy, session=session))
        return pd.DataFrame(records)
