"""Aspect extraction module for Isabelle lemmas (Format B: source-enriched)."""

from __future__ import annotations

import re
from typing import Any


# ---------------------------------------------------------------------------
# Tactic keyword vocabulary — lines containing these tokens belong to method
# ---------------------------------------------------------------------------
_TACTIC_KEYWORDS = {
    "apply", "by", "using", "unfolding", "proof", "qed", "done",
    "simp", "simp_all", "auto", "blast", "fastforce", "force", "metis",
    "induction", "induct", "coinduction", "cases", "case", "rule", "subst",
    "clarify", "clarsimp", "safe", "linarith", "arith", "presburger",
    "ring", "algebra", "have", "show", "obtain", "assume", "fix",
    "define", "let", "note", "then", "thus", "hence", "next",
    "defer", "prefer", "sorry", "oops", "intro", "elim", "fact",
}

# Keywords that introduce a cited identifier (dependency extraction).
_DEP_INTRODUCERS = re.compile(
    r'\b(?:using|unfolding|fact|rule|subst|metis|blast|insert)\s+'
    r'([\w\'.\[\] ,\-]+)',
    re.MULTILINE,
)
_SIMP_DEP_PATTERN = re.compile(
    r'\bsimp(?:\s+(?:add|del|only))?:\s*([\w\'., \[\]]+)',
)

# Identifiers that are tactics/common keywords — excluded from deps
_DEP_EXCLUSIONS = _TACTIC_KEYWORDS | {
    "of", "where", "in", "and", "or", "not", "if", "then", "else",
    "true", "false", "add", "del", "only", "intro", "elim", "dest",
    "no_types", "full_types", "standard", "this", "that", "goal",
}

# Isabelle construct keywords for interpretation aspect
_CONSTRUCT_KEYWORDS = {
    "lemma", "theorem", "corollary", "proposition", "schematic_goal",
    "definition", "fun", "primrec", "function", "datatype", "type_synonym",
    "inductive", "coinductive", "record", "abbreviation", "class", "instantiation",
}


def _strip_isabelle_markup(text: str) -> str:
    """Remove LaTeX commands and Isabelle antiquotations from text-block prose."""
    text = re.sub(r'@\{[^}]*\}', '', text)
    text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', text)
    text = re.sub(r'\$\$[^$]+\$\$', ' ', text)
    text = re.sub(r'\$[^$\n]+\$', ' ', text)
    text = re.sub(r'\\[a-zA-Z]+', ' ', text)
    text = re.sub(r'[‹›]', '"', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _extract_tactic_lines(proof: str) -> str:
    """Return the subset of proof lines that contain at least one tactic keyword."""
    if not proof.strip():
        return ""
    lines = proof.splitlines()
    tactic_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        tokens = set(re.findall(r'[a-zA-Z_]+', stripped))
        if tokens & _TACTIC_KEYWORDS:
            tactic_lines.append(stripped)
    return "\n".join(tactic_lines) if tactic_lines else proof.strip()


def _extract_dependencies(proof: str) -> str:
    """Extract cited dependency identifiers from the proof body."""
    if not proof.strip():
        return "none"

    deps: set[str] = set()

    for m in _DEP_INTRODUCERS.finditer(proof):
        raw = re.sub(r'[();\[\]]', ' ', m.group(1))
        for word in re.findall(r'[a-zA-Z][a-zA-Z0-9_\'.]+', raw):
            if word.lower() not in _DEP_EXCLUSIONS and len(word) > 2:
                deps.add(word)

    for m in _SIMP_DEP_PATTERN.finditer(proof):
        raw = re.sub(r'[();\[\]]', ' ', m.group(1))
        for word in re.findall(r'[a-zA-Z][a-zA-Z0-9_\'.]+', raw):
            if word.lower() not in _DEP_EXCLUSIONS and len(word) > 2:
                deps.add(word)

    return ", ".join(sorted(deps)) if deps else "none"


# ---------------------------------------------------------------------------
# Statement parsing helpers — four-rule cascade
# ---------------------------------------------------------------------------

def _split_on_top_level_implies(prop: str) -> list[str]:
    """Split a proposition on top-level ==> or ⟹, respecting bracket nesting."""
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    i = 0
    n = len(prop)
    while i < n:
        char = prop[i]
        if char in "([{‹⟦":
            depth += 1
            current.append(char)
            i += 1
        elif char in ")]}›⟧":
            depth = max(0, depth - 1)
            current.append(char)
            i += 1
        elif depth == 0 and prop[i] == "⟹":
            parts.append("".join(current).strip())
            current = []
            i += 1
        elif depth == 0 and prop[i:i+3] == "==>":
            parts.append("".join(current).strip())
            current = []
            i += 3
        else:
            current.append(char)
            i += 1
    if current:
        parts.append("".join(current).strip())
    return [p for p in parts if p]


def _split_on_top_level_iff(prop: str) -> list[str]:
    """Split on top-level ⟷ / <-> / ≡, respecting bracket nesting."""
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    i = 0
    n = len(prop)
    while i < n:
        char = prop[i]
        if char in "([{‹⟦":
            depth += 1
            current.append(char)
            i += 1
        elif char in ")]}›⟧":
            depth = max(0, depth - 1)
            current.append(char)
            i += 1
        elif depth == 0 and prop[i] in "⟷≡":
            parts.append("".join(current).strip())
            current = []
            i += 1
        elif depth == 0 and prop[i:i+3] == "<->":
            parts.append("".join(current).strip())
            current = []
            i += 3
        else:
            current.append(char)
            i += 1
    if current:
        parts.append("".join(current).strip())
    return [p for p in parts if p]


def _split_on_top_level_eq(prop: str) -> list[str]:
    """Split on the first top-level ASCII =, excluding <=, >=, =>, ==, !=."""
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    i = 0
    n = len(prop)
    while i < n:
        char = prop[i]
        if char in "([{‹⟦":
            depth += 1
            current.append(char)
            i += 1
        elif char in ")]}›⟧":
            depth = max(0, depth - 1)
            current.append(char)
            i += 1
        elif depth == 0 and char == "=":
            prev = prop[i - 1] if i > 0 else ""
            nxt  = prop[i + 1] if i + 1 < n else ""
            if prev not in "!<>=" and nxt not in "=>":
                parts.append("".join(current).strip())
                current = []
                i += 1
                continue
            current.append(char)
            i += 1
        else:
            current.append(char)
            i += 1
    if current:
        parts.append("".join(current).strip())
    return [p for p in parts if p]


def _is_complex_expr(s: str) -> bool:
    """Return True if expression is complex (operators, quantifiers, or function apps)."""
    s = s.strip()
    if " " in s:
        return True
    return bool(re.search(r"[∀∃∧∨¬⟹⟷≡≤≥≠∈⊆⊂∩∪⋃⋂+\-*/(){}⟦⟧|¦]", s))


def _clean_bracket_premises(premises: str) -> str:
    """Unwrap ⟦A; B; C⟧ or [| A; B; C |] bracket notation into a comma list."""
    p = premises.strip()
    if (p.startswith("⟦") and p.endswith("⟧")) or \
       (p.startswith("[|") and p.endswith("|]")):
        inner = p[1:-1] if p.startswith("⟦") else p[2:-2]
        sub = [x.strip() for x in inner.split(";") if x.strip()]
        return ", ".join(sub) if sub else "none"
    return premises


def _parse_obtains(stmt: str) -> tuple[str, str]:
    """Parse Isar obtains-form: [assumes ...] obtains x y where "P x" "Q y"."""
    obtains_idx = stmt.find("obtains")
    before = stmt[:obtains_idx]
    after  = stmt[obtains_idx + len("obtains"):]

    assumptions = re.findall(r'\bassumes\s*["‹]([^"›]+)["›]', before)
    if not assumptions:
        assumptions = re.findall(r'["‹]([^"›]+)["›]', before)

    where_idx     = after.find("where")
    where_section = after[where_idx + len("where"):] if where_idx >= 0 else after
    where_clauses = re.findall(r'["‹]([^"›]+)["›]', where_section)
    interpretation = ", ".join(where_clauses) if where_clauses else stmt.strip()

    if assumptions:
        return ", ".join(assumptions), interpretation
    return interpretation, interpretation


def normalize_isabelle_symbols(text: str) -> str:
    r"""Normalize Isabelle ASCII escape symbols (\<Longrightarrow>, \<lbrakk>, etc.) to canonical symbols."""
    replacements = [
        (r"\<lbrakk>", "⟦"),
        (r"\<rbrakk>", "⟧"),
        (r"\<Longrightarrow>", "⟹"),
        (r"\<longleftrightarrow>", "⟷"),
        (r"\<longrightarrow>", "⟶"),
        (r"\<equiv>", "≡"),
        (r"\<le>", "≤"),
        (r"\<ge>", "≥"),
        (r"\<and>", "∧"),
        (r"\<or>", "∨"),
        (r"\<not>", "¬"),
        (r"\<noteq>", "≠"),
        (r"\<in>", "∈"),
        (r"\<notin>", "∉"),
        (r"\<subseteq>", "⊆"),
        (r"\<forall>", "∀"),
        (r"\<exists>", "∃"),
        (r"\<And>", "⋀"),
        (r"\<lambda>", "λ"),
        (r"\<tau>", "τ"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def _parse_premises_and_conclusion(statement: str, attributes: list[str] | None = None) -> tuple[str, str]:
    """Parse a lemma/theorem statement to extract premises and conclusion.

    Preserves `fixes` variable annotations, eigenvariables `⋀`, and sort constraints.
    """
    stmt = normalize_isabelle_symbols(re.sub(r"\s+", " ", statement).strip())

    # ── Rule 3: obtains-form ───────────────────────────────────────────────────
    if "obtains" in stmt:
        return _parse_obtains(stmt)

    # ── Rule 1a: assumes / shows form ──────────────────────────────────────────
    if "shows" in stmt:
        shows_idx    = stmt.find("shows")
        assumes_part = stmt[:shows_idx]
        shows_part   = stmt[shows_idx + len("shows"):]

        # Extract fixes clauses if present
        fixes_matches = re.findall(r'\bfixes\s+([^"‹\n]+?)(?=\bassumes|\bshows|\bwhere|$)', assumes_part)
        fixes_clauses = []
        for f in fixes_matches:
            f_clean = re.sub(r'\s+and\s+', ', ', f).strip()
            if f_clean:
                fixes_clauses.append(f"fixes {f_clean}")

        assumptions = re.findall(r'\bassumes\s*["‹]([^"›]+)["›]', assumes_part)
        if not assumptions:
            assumptions = re.findall(r'["‹]([^"›]+)["›]', assumes_part)

        conclusion_match = re.search(r'["‹]([^"›]+)["›]', shows_part)
        shows_content    = conclusion_match.group(1) if conclusion_match else shows_part.strip()

        impl_parts = _split_on_top_level_implies(shows_content)
        if len(impl_parts) > 1:
            inner_premises = ", ".join(impl_parts[:-1])
            conclusion     = impl_parts[-1]
            all_premises   = fixes_clauses + assumptions + [inner_premises] if (fixes_clauses or assumptions) else [inner_premises]
            return ", ".join(all_premises), conclusion

        if assumptions or fixes_clauses:
            all_premises = fixes_clauses + assumptions if fixes_clauses else assumptions
            return ", ".join(all_premises), shows_content

        prop = shows_content

    else:
        # ── Rule 1b: standard quoted "A ⟹ B" form ─────────────────────────────
        m = re.search(r'["‹]([^"›]+)["›]', stmt)
        if not m:
            prop = re.sub(
                r'^(?:lemma|theorem|corollary|proposition|schematic_goal)\s+'
                r'(?:[a-zA-Z0-9_\'\.]+\s*(?:\[[^\]]*\])?\s*:)?\s*',
                '',
                stmt,
            )
        else:
            prop = m.group(1)

        impl_parts = _split_on_top_level_implies(prop)
        if len(impl_parts) > 1:
            premises_part = _clean_bracket_premises(", ".join(impl_parts[:-1]))
            return premises_part, impl_parts[-1]

    # ── Rule 2a: strict iff (⟷ / <-> / ≡) ───────────────────────────────────
    iff_parts = _split_on_top_level_iff(prop)
    if len(iff_parts) == 2:
        return iff_parts[0].strip(), iff_parts[1].strip()

    # ── Rule 2b: equality as rewrite — only when both sides are complex ────────
    eq_parts = _split_on_top_level_eq(prop)
    if len(eq_parts) == 2 and _is_complex_expr(eq_parts[0]) and _is_complex_expr(eq_parts[1]):
        return eq_parts[0].strip(), eq_parts[1].strip()

    # ── Rule 4: truly unconditional — fixed point ──────────────────────────────
    conclusion = prop.strip() or stmt
    return conclusion, conclusion


# ---------------------------------------------------------------------------
# Proof Strategy & Step Map Extraction (Unified across Isar & Apply)
# ---------------------------------------------------------------------------

def extract_proof_strategy(lemma: dict[str, Any]) -> str:
    """Extract high-level proof architecture and strategy roadmap.
    
    Guaranteed non-empty for 100% of units across:
      - Isar proofs (cases, inductions, milestone claims)
      - Apply scripts (structural pipeline)
      - One-liners by (...) (strategy paradigm)
      - Definitions (axiomatic specification)
    """
    keyword = lemma.get("keyword", "")
    DEF_KEYWORDS = {
        "definition", "fun", "primrec", "function", "datatype", "type_synonym",
        "inductive", "coinductive", "record", "abbreviation", "class", "instantiation"
    }
    if keyword in DEF_KEYWORDS:
        return f"[strategy: axiomatic-specification / {keyword}]"

    proof = lemma.get("proof_text", "").strip()
    skeleton_segs = lemma.get("skeleton_segments", [])
    
    # 1. Structured Isar proof
    if "proof" in proof or skeleton_segs:
        moves = []
        m_open = re.search(r'\bproof\s*(?:\(([^)]+)\))?', proof)
        if m_open:
            method = m_open.group(1)
            moves.append(f"proof ({method.strip()})" if method else "proof")
            
        for seg in skeleton_segs:
            s_clean = _strip_isabelle_markup(seg)
            if s_clean.startswith("case"):
                moves.append(s_clean)
            elif s_clean.startswith("have"):
                moves.append(f"[milestone: {s_clean[:40]}]")
            elif s_clean.startswith("show"):
                moves.append("show ?thesis")
                
        if not moves:
            moves = [_strip_isabelle_markup(s) for s in skeleton_segs[:5]]
            
        moves.append("qed")
        return " ⟶ ".join(moves)

    # 2. Procedural apply-script
    if "apply" in proof:
        structural_moves = []
        for line in proof.splitlines():
            line_str = line.strip()
            if line_str.startswith("apply"):
                if re.search(r'\b(?:induction|induct|coinduction|cases|case_tac|subgoal|rule_tac)\b', line_str):
                    structural_moves.append(_strip_isabelle_markup(line_str))
        if structural_moves:
            return f"pipeline: {' ⟶ '.join(structural_moves)} ⟶ terminal-automation"
        else:
            tactics = re.findall(r'\b(?:simp|auto|blast|fastforce|force|metis|linarith|arith)\b', proof)
            unique_t = sorted(list(set(tactics)))
            t_str = ", ".join(unique_t) if unique_t else "tactics"
            return f"sequential-rewriting: apply-script [{t_str}] ⟶ done"

    # 3. One-liner by (...)
    if proof.startswith("by") or "by" in proof:
        m_by = re.search(r'\bby\s*(?:\(([^)]+)\)|([a-zA-Z_]+))', proof)
        if m_by:
            first_m = (m_by.group(1) or m_by.group(2) or "").strip()
            head_word = first_m.split()[0] if first_m.split() else ""
            if head_word in {"induction", "induct"}:
                return f"[strategy: structural-induction ({first_m}) ⟶ auto-simplification]"
            elif head_word in {"cases", "case_tac"}:
                return f"[strategy: case-analysis ({first_m}) ⟶ terminal-automation]"
            elif head_word in {"coinduction", "coinduct"}:
                return f"[strategy: coinductive-bisimulation ({first_m})]"
            elif head_word in {"rule", "rule_tac", "intro"}:
                return f"[strategy: natural-deduction / resolution ({first_m})]"
            elif head_word in {"simp", "simp_all"}:
                return f"[strategy: equational-normalization ({first_m})]"
            elif head_word in {"auto", "fastforce", "force"}:
                return f"[strategy: classical-simplification ({first_m})]"
            elif head_word == "blast":
                return f"[strategy: first-order-tableau ({first_m})]"
            elif head_word == "metis":
                return f"[strategy: resolution-atp ({first_m})]"
            elif head_word in {"linarith", "arith", "algebra", "ring"}:
                return f"[strategy: decision-procedure ({first_m})]"
            else:
                return f"[strategy: automated-proof ({first_m})]"
        return f"[strategy: one-line-proof ({proof[:50]})]"

    if proof:
        return f"[strategy: proof-script ({proof[:50]})]"
        
    return "[strategy: axiomatic-property]"


def extract_proof_finding(lemma: dict[str, Any]) -> str:
    """Format coupled step map and execution content into a narrative.
    
    Guaranteed non-empty for 100% of lemmas.
    """
    keyword = lemma.get("keyword", "")
    DEF_KEYWORDS = {
        "definition", "fun", "primrec", "function", "datatype", "type_synonym",
        "inductive", "coinductive", "record", "abbreviation", "class", "instantiation"
    }
    if keyword in DEF_KEYWORDS:
        return lemma.get("statement_text", "").strip() or f"[definition: {keyword}]"

    proof_steps = lemma.get("proof_steps")
    if not proof_steps:
        from edel.il.parser import extract_proof_step_map
        proof_segments = lemma.get("proof_segments") or [lemma.get("proof_text", "")]
        proof_steps = extract_proof_step_map(proof_segments)

    if proof_steps:
        step_lines = []
        for s in proof_steps:
            s_type = s.get("type", "step")
            claim = s.get("claim", "")
            tactic = s.get("tactic", "")
            deps = s.get("deps", [])
            deps_str = f", deps: {deps}" if deps else ""
            
            if claim and tactic:
                step_lines.append(f"Step {s['index']} [{s_type}: claim=\"{claim}\", tactic=\"{tactic}\"{deps_str}]")
            elif claim:
                step_lines.append(f"Step {s['index']} [{s_type}: {claim}]")
            elif tactic:
                step_lines.append(f"Step {s['index']} [{s_type}: action=\"{tactic}\"{deps_str}]")
                
        if step_lines:
            return "\n".join(step_lines)

    proof = lemma.get("proof_text", "").strip()
    return proof or "[no proof body]"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_aspects(
    lemma: dict[str, Any],
    theory_header: str = "",
    entry_metadata: dict[str, Any] | None = None,
    text_comments: list[str] | None = None,
) -> dict[str, str]:
    """Extract source-enriched aspects from a parsed lemma.

    Aspects:
        aspect_statement    — Premises/hypotheses + fixes + sort constraints (Aspect 1: Problem).
        aspect_strategy     — Proof architecture & strategic roadmap (Aspect 2: Method).
        aspect_dependencies — Coupled step map & tactical content (Aspect 3: Finding).
        aspect_context      — Conclusion / consequent + attributes (Aspect 4: Interpretation).
    """
    statement = lemma.get("statement_text", "").strip()
    attrs = lemma.get("attributes", [])
    rule_type = lemma.get("rule_type", "")
    
    # ── Handle Definitions as 0-simplices ──────────────────────────────────
    DEF_KEYWORDS = {
        "definition", "fun", "primrec", "function", "datatype", "type_synonym",
        "inductive", "coinductive", "record", "abbreviation", "class", "instantiation"
    }
    if lemma.get("keyword") in DEF_KEYWORDS:
        return {
            "aspect_statement": statement,
            "aspect_context": statement,
            "aspect_strategy": statement,
            "aspect_dependencies": statement,
        }

    proof = lemma.get("proof_text", "").strip()
    comments = text_comments or lemma.get("text_comments", [])

    # 1. Parse statement into premises and conclusion
    premises, conclusion = _parse_premises_and_conclusion(statement, attributes=attrs)
    aspect_statement = premises
    aspect_context = conclusion

    # 2. Extract strategy (Aspect 2: Method)
    aspect_strategy = extract_proof_strategy(lemma)
    
    # Append narrative text comments to strategy if present
    if comments:
        comment_parts = []
        for raw_comment in comments:
            cleaned = _strip_isabelle_markup(raw_comment)
            if len(cleaned) > 20:
                comment_parts.append(cleaned)
        if comment_parts:
            aspect_strategy = "\n".join(comment_parts) + "\n" + aspect_strategy

    # 3. Extract step map (Aspect 3: Finding)
    aspect_dependencies = extract_proof_finding(lemma)

    # ── Simplex collapse rules for degenerate cases (axioms / sorry / oops) ────
    if not proof or proof in {"sorry", "oops"}:
        # Axiomatic or missing proof: collapse toward statement
        if not aspect_strategy or aspect_strategy.startswith("[strategy: axiomatic"):
            aspect_strategy = aspect_context
        if not aspect_dependencies or aspect_dependencies == "[no proof body]":
            aspect_dependencies = aspect_context

    return {
        "aspect_statement": aspect_statement,
        "aspect_context": aspect_context,
        "aspect_strategy": aspect_strategy,
        "aspect_dependencies": aspect_dependencies,
    }


def format_aspect_with_metadata(
    theory: str,
    lemma_title: str,
    aspect: str,
    aspect_text_dict: dict[str, str],
    locale: str = "",
    attributes: list[str] | None = None,
    rule_type: str = "",
    types: str = "",
    architecture: str = "",
) -> str:
    """Format an aspect value using the structured Contextual Envelope.
    
    Envelope:
      [Theory: {theory}] [Locale: {locale}] [Role: {label}] [Rule: {rule_type}] [Attributes: {attrs}] [Types: {types}]
      Lemma: {lemma_name} | {label}:
      {text}
    """
    lemma_name = lemma_title.split(".")[-1] if lemma_title else "unnamed"
    val = aspect_text_dict.get(aspect, "")
    text = str(val).strip()
    if not text or text == "none":
        return ""

    label_map = {
        "problem": "Premises",
        "method": "Strategy",
        "finding": "StepMap",
        "interpretation": "Conclusion"
    }
    label = label_map.get(aspect, "Content")

    p_text = aspect_text_dict.get("problem", "").strip()
    m_text = aspect_text_dict.get("method", "").strip()
    f_text = aspect_text_dict.get("finding", "").strip()
    i_text = aspect_text_dict.get("interpretation", "").strip()
    if p_text == m_text == f_text == i_text:
        label = "Statement"
    elif m_text == f_text and aspect in ["method", "finding"]:
        label = "Proof"

    attrs_str = ", ".join(attributes) if attributes else "none"
    loc_str = locale if locale else "global"
    rule_str = rule_type if rule_type else "theorem"
    types_str = types if types else "unspecified"
    arch_part = f" [Architecture: {architecture}]" if architecture else ""
    
    header = (
        f"[Theory: {theory}] [Locale: {loc_str}] [Role: {label}] "
        f"[Rule: {rule_str}] [Attributes: {attrs_str}] [Types: {types_str}]{arch_part}"
    )
    return f"{header}\nLemma: {lemma_name} | {label}:\n{text}"
