"""Isabelle segment parser, metadata extraction, and grouping logic."""

from __future__ import annotations

import re
from typing import Any


_DEP_INTRODUCERS = re.compile(
    r'\b(?:using|unfolding|fact|rule|subst|metis|blast|insert)\s+'
    r'([\w\'.\[\] ,\-]+)',
    re.MULTILINE,
)
_SIMP_DEP_PATTERN = re.compile(
    r'\bsimp(?:\s+(?:add|del|only))?:\s*([\w\'., \[\]]+)',
)
_DEP_EXCLUSIONS = {
    "apply", "by", "using", "unfolding", "proof", "qed", "done",
    "simp", "simp_all", "auto", "blast", "fastforce", "force", "metis",
    "induction", "induct", "coinduction", "cases", "case", "rule", "subst",
    "clarify", "clarsimp", "safe", "linarith", "arith", "presburger",
    "ring", "algebra", "have", "show", "obtain", "assume", "fix",
    "define", "let", "note", "then", "thus", "hence", "next",
    "defer", "prefer", "sorry", "oops", "intro", "elim", "fact",
    "of", "where", "in", "and", "or", "not", "if", "then", "else",
    "true", "false", "add", "del", "only", "dest",
    "no_types", "full_types", "standard", "this", "that", "goal",
}


def _extract_deps_from_text(text: str) -> list[str]:
    """Extract cited dependency identifiers from a segment or tactic line."""
    if not text.strip():
        return []
    deps = set()
    for m in _DEP_INTRODUCERS.finditer(text):
        raw = re.sub(r'[();\[\]]', ' ', m.group(1))
        for word in re.findall(r'[a-zA-Z][a-zA-Z0-9_\'.]+', raw):
            if word.lower() not in _DEP_EXCLUSIONS and len(word) > 2:
                deps.add(word)
    for m in _SIMP_DEP_PATTERN.finditer(text):
        raw = re.sub(r'[();\[\]]', ' ', m.group(1))
        for word in re.findall(r'[a-zA-Z][a-zA-Z0-9_\'.]+', raw):
            if word.lower() not in _DEP_EXCLUSIONS and len(word) > 2:
                deps.add(word)
    return sorted(list(deps))


def _clean_markup(text: str) -> str:
    """Remove basic Isabelle antiquotations and normalize whitespace."""
    text = re.sub(r'@\{[^}]*\}', '', text)
    text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', text)
    text = re.sub(r'[‹›]', '"', text)
    return re.sub(r'\s+', ' ', text).strip()


def parse_source_segments(raw_source: str) -> dict[int, str]:
    """Parse raw Ir.source output (which may contain YXML markup) into segment texts.
    
    Handles multi-line continuation of segments.
    """
    segments = {}
    current_idx = None
    current_lines = []
    
    def clean_yxml(t):
        return t.replace("\x05", "").replace("\x06", "")
        
    for line in raw_source.splitlines():
        plain = clean_yxml(line).lstrip()
        idx_match = re.match(r'^(\d+)\s', plain)
        if idx_match:
            if current_idx is not None:
                segments[current_idx] = "\n".join(current_lines).strip()
            current_idx = int(idx_match.group(1))
            content = re.sub(r'^\s*\d+\s{1,2}', '', clean_yxml(line).lstrip())
            current_lines = [content]
        else:
            if current_idx is not None:
                current_lines.append(line)
                
    if current_idx is not None:
        segments[current_idx] = "\n".join(current_lines).strip()
        
    return segments


def extract_lemma_name_and_attributes(stmt: str) -> tuple[str, list[str], str]:
    """Extract lemma name, attributes list, and explicit locale qualifier.
    
    Matches forms like:
      lemma (in loc) name [simp, intro!]:
      lemma name [simp]:
      theorem complex_thm:
      lemma "True"
    
    Returns:
        (name, attributes, locale_qualifier)
    """
    stmt = stmt.strip()
    stmt_clean = re.sub(r'\s+', ' ', stmt)
    m = re.match(
        r'^(?:lemma|theorem|corollary|proposition|schematic_goal)\s+'
        r'(?:\(in\s+([a-zA-Z0-9_\'\.]+)\)\s+)?'
        r'([a-zA-Z0-9_\'\.]+)?'
        r'(?:\s+\[([^\]]*)\])?\s*:',
        stmt_clean,
    )
    if m:
        loc = m.group(1) or ""
        name = m.group(2) or ""
        attrs_raw = m.group(3) or ""
        attrs = [a.strip() for a in re.split(r'[, ]+', attrs_raw) if a.strip()]
        return name, attrs, loc
    return "", [], ""


def extract_lemma_name(stmt: str) -> str:
    """Extract the formal name of a lemma from its declaration statement."""
    name, _, _ = extract_lemma_name_and_attributes(stmt)
    return name


def extract_definition_name_and_attributes(stmt: str, keyword: str) -> tuple[str, list[str], str]:
    """Extract formal name, attributes, and locale qualifier of a definition/function."""
    stmt = stmt.strip()
    stmt_clean = re.sub(r'\s+', ' ', stmt)
    m = re.match(
        rf'^(?:{keyword})\s+(?:\(in\s+([a-zA-Z0-9_\'\.]+)\)\s+)?([a-zA-Z0-9_\'\.]+)(?:\s+\[([^\]]*)\])?',
        stmt_clean,
    )
    if m:
        loc = m.group(1) or ""
        name = m.group(2) or ""
        attrs_raw = m.group(3) or ""
        attrs = [a.strip() for a in re.split(r'[, ]+', attrs_raw) if a.strip()]
        return name, attrs, loc
    return "", [], ""


def extract_definition_name(stmt: str, keyword: str) -> str:
    """Extract the formal name of a definition/function from its declaration statement."""
    name, _, _ = extract_definition_name_and_attributes(stmt, keyword)
    return name


def classify_rule_type(name: str, attrs: list[str], stmt: str) -> str:
    """Classify the rule type of a lemma based on attributes, naming conventions, and syntax."""
    for a in attrs:
        if a.startswith("induct"):
            return "induction_rule"
        if a.startswith("cases"):
            return "cases_rule"
        if a.startswith("coinduct"):
            return "coinduction_rule"
        if a in {"intro", "intro!"}:
            return "introduction_rule"
        if a in {"elim", "elim!"}:
            return "elimination_rule"
        if a in {"dest", "dest!"}:
            return "destruction_rule"
    if "simp" in attrs:
        return "simplification_rule"
        
    name_clean = name.split(".")[-1]
    if name_clean in {"induct", "induction"} or name_clean.endswith(("_induct", ".induct")):
        return "induction_rule"
    if name_clean in {"cases", "case"} or name_clean.endswith(("_cases", ".cases")):
        return "cases_rule"
    if name_clean in {"coinduct", "coinduction"} or name_clean.endswith(("_coinduct", ".coinduct")):
        return "coinduction_rule"
    if name_clean.endswith(("_elims", ".elims")) or (name_clean.endswith("E") and not name_clean.endswith(("LE", "GE")) and len(name_clean) > 2):
        return "elimination_rule"
    if name_clean.endswith(("_intros", ".intros")) or (name_clean.endswith("I") and len(name_clean) > 2):
        return "introduction_rule"
    if name_clean.endswith("D") and len(name_clean) > 2:
        return "destruction_rule"
    if name_clean.endswith(("_def", ".def", "_defs")):
        return "definition_rule"
        
    return "general_theorem"


def extract_proof_step_map(proof_segments: list[str]) -> list[dict[str, Any]]:
    """Extract a coupled step map from proof segments, linking claims with tactics and cited dependencies.
    
    Handles:
      - Structured Isar proofs (have ... by ..., show ... using ... by ..., proof ..., case ...)
      - Procedural apply scripts (apply ...)
      - One-liners (by ...)
    """
    steps = []
    step_idx = 1
    
    ISAR_CLAIM_KEYWORDS = {"have", "show", "also", "finally", "obtain", "assume", "fix", "case", "let", "define"}
    
    pending_claim = None
    pending_type = None
    
    for seg in proof_segments:
        stripped = seg.strip()
        if not stripped:
            continue
            
        first_word = stripped.split()[0] if stripped.split() else ""
        
        # 1. Isar Opening: proof (...) or proof
        if first_word == "proof":
            steps.append({
                "index": step_idx,
                "type": "proof_opening",
                "claim": _clean_markup(stripped),
                "tactic": "",
                "deps": _extract_deps_from_text(stripped)
            })
            step_idx += 1
            continue
            
        # 2. Isar Closing: qed / done
        if first_word in {"qed", "done"}:
            steps.append({
                "index": step_idx,
                "type": "proof_closing",
                "claim": stripped,
                "tactic": "",
                "deps": []
            })
            step_idx += 1
            continue

        # 3. Next case separator
        if first_word == "next":
            steps.append({
                "index": step_idx,
                "type": "proof_separator",
                "claim": "next",
                "tactic": "",
                "deps": []
            })
            step_idx += 1
            continue
            
        # 4. Apply steps
        if first_word == "apply":
            steps.append({
                "index": step_idx,
                "type": "apply_step",
                "claim": "",
                "tactic": _clean_markup(stripped),
                "deps": _extract_deps_from_text(stripped)
            })
            step_idx += 1
            continue
            
        # 5. One-liner 'by' or terminal 'by'
        if first_word == "by":
            if pending_claim:
                steps.append({
                    "index": step_idx,
                    "type": pending_type or "claim",
                    "claim": pending_claim,
                    "tactic": _clean_markup(stripped),
                    "deps": _extract_deps_from_text(stripped)
                })
                step_idx += 1
                pending_claim = None
                pending_type = None
            else:
                steps.append({
                    "index": step_idx,
                    "type": "by_terminal",
                    "claim": "",
                    "tactic": _clean_markup(stripped),
                    "deps": _extract_deps_from_text(stripped)
                })
                step_idx += 1
            continue
            
        # 6. Case branch
        if first_word == "case":
            steps.append({
                "index": step_idx,
                "type": "case_branch",
                "claim": _clean_markup(stripped),
                "tactic": "",
                "deps": []
            })
            step_idx += 1
            continue
            
        # 7. Isar claims: have, show, etc.
        if first_word in ISAR_CLAIM_KEYWORDS:
            by_idx = stripped.find(" by ")
            if by_idx > 0:
                claim_part = stripped[:by_idx].strip()
                tactic_part = stripped[by_idx + 1:].strip()
                steps.append({
                    "index": step_idx,
                    "type": first_word,
                    "claim": _clean_markup(claim_part),
                    "tactic": _clean_markup(tactic_part),
                    "deps": _extract_deps_from_text(tactic_part)
                })
                step_idx += 1
            else:
                if pending_claim:
                    steps.append({
                        "index": step_idx,
                        "type": pending_type or "claim",
                        "claim": pending_claim,
                        "tactic": "",
                        "deps": []
                    })
                    step_idx += 1
                pending_claim = _clean_markup(stripped)
                pending_type = first_word
            continue
            
        # 8. Operational modifiers like 'using ...', 'with ...', 'from ...'
        if first_word in {"using", "with", "from", "unfolding"}:
            if pending_claim:
                pending_claim += " " + _clean_markup(stripped)
            else:
                steps.append({
                    "index": step_idx,
                    "type": "justification_directive",
                    "claim": "",
                    "tactic": _clean_markup(stripped),
                    "deps": _extract_deps_from_text(stripped)
                })
                step_idx += 1
            continue
            
        # Fallback
        if pending_claim:
            steps.append({
                "index": step_idx,
                "type": pending_type or "claim",
                "claim": pending_claim,
                "tactic": _clean_markup(stripped),
                "deps": _extract_deps_from_text(stripped)
            })
            step_idx += 1
            pending_claim = None
            pending_type = None
        else:
            steps.append({
                "index": step_idx,
                "type": "other_step",
                "claim": "",
                "tactic": _clean_markup(stripped),
                "deps": _extract_deps_from_text(stripped)
            })
            step_idx += 1

    if pending_claim:
        steps.append({
            "index": step_idx,
            "type": pending_type or "claim",
            "claim": pending_claim,
            "tactic": "",
            "deps": []
        })
        
    return steps


def group_segments_to_lemmas(seg_map: dict[int, dict], segments: dict[int, str]) -> list[dict[str, Any]]:
    """Group sequential segments into logical lemma and definition units with metadata and proof.
    
    Tracks lexical scope stacks (locale, context, class, instantiation).
    
    Args:
        seg_map: Dict of {idx: {keyword, line, offset, file, theory}}
        segments: Dict of {idx: segment_text}
    """
    units = []
    current_unit = None
    scope_stack: list[tuple[str, str]] = []
    
    indices = sorted(segments.keys())
    
    LEMMA_KEYWORDS = {"lemma", "theorem", "corollary", "proposition", "schematic_goal"}
    DEF_KEYWORDS = {
        "definition", "fun", "primrec", "function", "datatype", "type_synonym",
        "inductive", "coinductive", "record", "abbreviation"
    }
    ALL_INGEST_KEYWORDS = LEMMA_KEYWORDS | DEF_KEYWORDS

    TEXT_COMMENT_KEYWORDS = {
        "text", "txt", "section", "subsection", "subsubsection",
        "paragraph", "chapter", "notepad"
    }

    ISAR_SKELETON_KEYWORDS = {
        "proof", "qed", "have", "show", "also", "finally", "next",
        "case", "assume", "fix", "obtain", "define", "let", "presume", "suppose"
    }
    ISAR_TACTIC_KEYWORDS = {
        "apply", "by", "using", "unfolding", "with", "from",
        "then", "hence", "thus", "note", "done", "defer", "prefer", "sorry", "oops"
    }
    DECL_KEYWORDS = {
        "lemma", "theorem", "corollary", "proposition", "schematic_goal",
        "definition", "fun", "primrec", "function", "datatype", "type_synonym",
        "inductive", "coinductive", "record", "abbreviation", "class", "instantiation",
        "locale", "context", "end", "theory"
    }
    PROOF_KEYWORDS = {"by", "apply", "proof", "qed", "sorry", "oops", "done", "defer", "prefer", "using", "unfolding"}
    
    for idx in indices:
        seg_info = seg_map.get(idx, {})
        keyword = seg_info.get("keyword", "")
        text = segments[idx]
        
        # Track scope blocks opening outside of a current lemma
        if not current_unit:
            if keyword in {"context", "locale", "class", "instantiation"}:
                if "begin" in text:
                    m_scope = re.search(rf'\b(?:{keyword})\s+(?:bundle\s+)?([a-zA-Z0-9_\'\.]+)', text)
                    scope_name = m_scope.group(1) if m_scope else keyword
                    scope_stack.append((keyword, scope_name))
            elif keyword == "end" and scope_stack:
                scope_stack.pop()

        if keyword in ALL_INGEST_KEYWORDS:
            if current_unit:
                units.append(current_unit)
                
            active_locale = ""
            for sk, sn in reversed(scope_stack):
                if sn:
                    active_locale = sn
                    break
                    
            if keyword in LEMMA_KEYWORDS:
                name, attrs, loc_qual = extract_lemma_name_and_attributes(text)
                if loc_qual:
                    active_locale = loc_qual
                rule_t = classify_rule_type(name, attrs, text)
            else:
                name, attrs, loc_qual = extract_definition_name_and_attributes(text, keyword)
                if loc_qual:
                    active_locale = loc_qual
                rule_t = "definition_rule"
                
            current_unit = {
                "name": name,
                "keyword": keyword,
                "theory": seg_info.get("theory", ""),
                "locale": active_locale,
                "context_scope": " -> ".join([s[1] for s in scope_stack]) if scope_stack else "global",
                "attributes": attrs,
                "rule_type": rule_t,
                "file": seg_info.get("file", ""),
                "start_line": seg_info.get("line"),
                "segment_start": idx,
                "segment_end": idx,
                "statement_text": text,
                "proof_segments": [],
                "skeleton_segments": [],
                "tactic_segments": [],
                "text_comments": [],
                "proof_depth": 0,
            }
        elif current_unit:
            if keyword in TEXT_COMMENT_KEYWORDS:
                current_unit["text_comments"].append(text)
            elif keyword in DECL_KEYWORDS and keyword not in PROOF_KEYWORDS:
                units.append(current_unit)
                current_unit = None
                # Check if this terminating segment opens or closes a scope block
                if keyword in {"context", "locale", "class", "instantiation"} and "begin" in text:
                    m_scope = re.search(rf'\b(?:{keyword})\s+(?:bundle\s+)?([a-zA-Z0-9_\'\.]+)', text)
                    scope_name = m_scope.group(1) if m_scope else keyword
                    scope_stack.append((keyword, scope_name))
                elif keyword == "end" and scope_stack:
                    scope_stack.pop()
            else:
                current_unit["proof_segments"].append(text)
                current_unit["segment_end"] = idx

                if keyword in ISAR_SKELETON_KEYWORDS:
                    current_unit["skeleton_segments"].append(text)
                else:
                    current_unit["tactic_segments"].append(text)

                if keyword == "proof":
                    current_unit["proof_depth"] += 1
                elif keyword == "qed":
                    current_unit["proof_depth"] = max(0, current_unit["proof_depth"] - 1)

                is_terminal = (
                    (current_unit["proof_depth"] == 0 and keyword in {"by", "qed", "done", "sorry", "oops"})
                    or keyword in {"sorry", "oops"}
                )
                if is_terminal:
                    units.append(current_unit)
                    current_unit = None
                    
    if current_unit:
        units.append(current_unit)
        
    final_units = []
    for u in units:
        proof_text = "\n".join(u["proof_segments"]).strip()
        name_placeholder = f"{u['keyword']}_{u['segment_start']}"
        proof_steps = extract_proof_step_map(u["proof_segments"])
        final_units.append({
            "id": f"{u['theory']}.{u['name']}" if u['name'] else f"{u['theory']}.{name_placeholder}",
            "name": u["name"],
            "keyword": u["keyword"],
            "theory": u["theory"],
            "locale": u.get("locale", ""),
            "context_scope": u.get("context_scope", "global"),
            "attributes": u.get("attributes", []),
            "rule_type": u.get("rule_type", "general_theorem"),
            "file": u["file"],
            "line": u["start_line"],
            "segment_start": u["segment_start"],
            "segment_end": u["segment_end"],
            "statement_text": u["statement_text"],
            "proof_text": proof_text,
            "proof_steps": proof_steps,
            "skeleton_segments": u.get("skeleton_segments", []),
            "tactic_segments": u.get("tactic_segments", []),
            "text_comments": u.get("text_comments", []),
        })
    return final_units
