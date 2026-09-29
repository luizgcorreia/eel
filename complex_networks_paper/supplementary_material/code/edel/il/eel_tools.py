"""EEL (Embedding-driven Epistemic Landscape) Operators and Proof Engineering Tools for I/L.

Single source of truth for:
- Canonical aspect definitions and Isabelle-friendly agent display names
- Conditional displacement operators D(X|Y) and 2-hop composition D(F|M) ∘ D(M|P)
- Multi-channel retrieval and weighted merging
- 3-Dossier Epistemic formatting (Dossier A, B, C)
- Expert Proof Guidance prompts and tactic execution ladder
"""

from __future__ import annotations

import re
from typing import Any

import numpy as np

# ── Aspect Naming Layer ────────────────────────────────────────────────────────

# Canonical internal aspect names -> Isabelle-domain display names for agents
ASPECT_DISPLAY: dict[str, str] = {
    "problem": "Premises & Hypotheses",
    "method": "Proof Strategy",
    "finding": "Tactic Step Map",
    "interpretation": "Conclusion & Rule Class",
}

# Human-readable D-operator display names
D_DISPLAY: dict[tuple[str, str], str] = {
    ("method", "problem"): "D(Proof-Strategy | Premises)",
    ("finding", "problem"): "D(Tactic-Map | Premises)",
    ("method", "interpretation"): "D(Proof-Strategy | Conclusion)",
    ("finding", "interpretation"): "D(Tactic-Map | Conclusion)",
    ("finding", "method"): "D(Tactic-Map | Proof-Strategy)",  # hop-2
}

# Isabelle server alias map -> canonical internal name
ASPECT_ALIASES: dict[str, str] = {
    "premises": "problem",
    "hypothesis": "problem",
    "hypotheses": "problem",
    "problem": "problem",
    "proof-strategy": "method",
    "strategy": "method",
    "method": "method",
    "tactics": "finding",
    "tactic-map": "finding",
    "steps": "finding",
    "finding": "finding",
    "conclusion": "interpretation",
    "goal": "interpretation",
    "interpretation": "interpretation",
}


def normalize_aspect_name(name: str) -> str:
    """Normalize any alias or user input to canonical aspect name."""
    norm = name.strip().lower().replace("_", "-")
    if norm in ASPECT_ALIASES:
        return ASPECT_ALIASES[norm]
    norm_underscore = name.strip().lower().replace("-", "_")
    if norm_underscore in ("problem", "method", "finding", "interpretation"):
        return norm_underscore
    return "problem"


def _dedup_and_sort_by_score(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate hits by lemma title (keeping the highest score) and sort descending by score."""
    seen: dict[str, dict[str, Any]] = {}
    for h in hits:
        meta = h.get("lemma", h)
        t = meta.get("title", "")
        if not t:
            continue
        s = float(h.get("score", 0.0))
        if t not in seen or s > float(seen[t].get("score", 0.0)):
            seen[t] = h
    return sorted(seen.values(), key=lambda x: float(x.get("score", 0.0)), reverse=True)


# ── Multi-Channel Retrieval & Fusion ──────────────────────────────────────────

def multi_channel_retrieve(
    il_index: Any,
    query_vector: list[float],
    title: str = "",
    theory: str = "",
    line: int = 0,
    n_direct: int = 5,
    n_twohop: int = 5,
    min_hop1_score: float = 0.60,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Execute multi-channel retrieval across EEL aspect spaces.

    Channels:
      Channel A: D(Proof-Strategy + Tactic-Map | Premises)
                 Searches problem (premise) space.
      Channel B: D(Proof-Strategy + Tactic-Map | Conclusion)
                 Searches interpretation (conclusion) space.
      Channel C: D(Tactic-Map | Proof-Strategy) ∘ D(Proof-Strategy | Premises)
                 2-hop chain: infers strategy from premises, then retrieves
                 tactics from proofs with that same strategy architecture.

    Returns:
      (channel_a, channel_b, channel_c) where each channel is a list of hit dicts
      sorted descending by cosine similarity score.
    """
    if il_index is None:
        return [], [], []

    # Channel A: Premises (problem space)
    raw_a = il_index.conditional_search(
        query_vector=query_vector,
        search_aspect="problem",
        return_aspect="method",
        max_results=50,
        exclude_definitions=True,
    )
    channel_a = _filter_temporal_and_self(raw_a, title=title, theory=theory, line=line)

    # Channel B: Conclusion (interpretation space) — include definitions & inductive rules!
    raw_b = il_index.conditional_search(
        query_vector=query_vector,
        search_aspect="interpretation",
        return_aspect="finding",
        max_results=50,
        exclude_definitions=False,
    )
    channel_b = _filter_temporal_and_self(raw_b, title=title, theory=theory, line=line)

    # Retrieve explicit definitions matching query to support inductive predicates and functions
    if hasattr(il_index, "search_definitions"):
        try:
            raw_defs = il_index.search_definitions(query_vector=query_vector, max_results=5)
            for d in raw_defs:
                d_meta = d.get("definition", d)
                if d_meta.get("title") != title and float(d.get("score", 0.0)) >= 0.50:
                    channel_b.append({
                        "lemma": d_meta,
                        "score": float(d.get("score", 0.0)),
                        "d_operator": "D(Definition|Conclusion)",
                        "search_aspect": "interpretation",
                        "return_aspect": "problem",
                    })
        except Exception:
            pass

    # Channel C: 2-hop strategy-calibrated tactics
    raw_c = il_index.two_hop_search(
        query_vector=query_vector,
        hop1_aspect="problem",
        hop2_aspect="method",
        return_aspect="finding",
        max_results=n_twohop,
        min_hop1_score=min_hop1_score,
    )
    channel_c = _filter_temporal_and_self(raw_c, title=title, theory=theory, line=line)

    # Sort all channels strictly by cosine similarity score descending
    channel_a = _dedup_and_sort_by_score(channel_a)[:n_direct]
    channel_b = _dedup_and_sort_by_score(channel_b)[:n_direct]
    channel_c = _dedup_and_sort_by_score(channel_c)[:n_twohop]

    return channel_a, channel_b, channel_c



def _filter_temporal_and_self(
    hits: list[dict[str, Any]],
    title: str = "",
    theory: str = "",
    line: int = 0,
) -> list[dict[str, Any]]:
    """Filter out the query theorem itself and any lemmas occurring later in the file."""
    filtered = []
    for h in hits:
        meta = h.get("lemma", h)
        if meta.get("title") == title:
            continue
        if theory and line and meta.get("theory") == theory and meta.get("line", 0) >= line:
            continue
        filtered.append(h)
    return filtered


def weighted_merge(
    channel_a: list[dict[str, Any]],
    channel_b: list[dict[str, Any]],
    channel_c: list[dict[str, Any]],
    w_a: float = 0.35,
    w_b: float = 0.40,
    w_c: float = 0.25,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Deduplicate candidates across channels and compute combined ranking.

    combined_score = w_a * score_a + w_b * score_b + w_c * score_c
    """
    merged: dict[str, dict[str, Any]] = {}

    for item in channel_a:
        meta = item.get("lemma", item)
        t = meta.get("title", "")
        if not t:
            continue
        entry = merged.setdefault(t, {
            "lemma": meta,
            "title": t,
            "score_a": 0.0,
            "score_b": 0.0,
            "score_c": 0.0,
            "channels": [],
            "hop1_anchor": item.get("hop1_anchor"),
            "hop1_score": item.get("hop1_score"),
        })
        entry["score_a"] = max(entry["score_a"], float(item.get("score", 0.0)))
        if "A" not in entry["channels"]:
            entry["channels"].append("A")

    for item in channel_b:
        meta = item.get("lemma", item)
        t = meta.get("title", "")
        if not t:
            continue
        entry = merged.setdefault(t, {
            "lemma": meta,
            "title": t,
            "score_a": 0.0,
            "score_b": 0.0,
            "score_c": 0.0,
            "channels": [],
            "hop1_anchor": item.get("hop1_anchor"),
            "hop1_score": item.get("hop1_score"),
        })
        entry["score_b"] = max(entry["score_b"], float(item.get("score", 0.0)))
        if "B" not in entry["channels"]:
            entry["channels"].append("B")

    for item in channel_c:
        meta = item.get("lemma", item)
        t = meta.get("title", "")
        if not t:
            continue
        entry = merged.setdefault(t, {
            "lemma": meta,
            "title": t,
            "score_a": 0.0,
            "score_b": 0.0,
            "score_c": 0.0,
            "channels": [],
            "hop1_anchor": item.get("hop1_anchor"),
            "hop1_score": item.get("hop1_score"),
        })
        entry["score_c"] = max(entry["score_c"], float(item.get("score", 0.0)))
        if item.get("hop1_anchor"):
            entry["hop1_anchor"] = item["hop1_anchor"]
            entry["hop1_score"] = item.get("hop1_score")
        if "C" not in entry["channels"]:
            entry["channels"].append("C")

    for entry in merged.values():
        score = (
            w_a * entry["score_a"]
            + w_b * entry["score_b"]
            + w_c * entry["score_c"]
        )
        entry["combined_score"] = score

    ranked = sorted(merged.values(), key=lambda x: x["combined_score"], reverse=True)
    return ranked[:top_k]


# ── Actionable Directive & Tactic Extraction ──────────────────────────────────

def extract_rule_directive(meta: dict[str, Any]) -> str:
    """Generate precise proof directive based on rule attributes and type."""
    short_name = meta.get("title", "").split(".")[-1]
    keyword = meta.get("keyword", "")
    rule_type = meta.get("rule_type", "general_theorem")
    attributes = str(meta.get("attributes", "none")).lower()
    proof_text = meta.get("proof_text", "")

    if keyword == "inductive":
        return f"apply (induction rule: {short_name}.induct)  or  by (induction rule: {short_name}.induct) (auto intro: {short_name}.intros)"
    if keyword in ("definition", "fun", "primrec"):
        return f"simp add: {short_name}_def {short_name}.simps"
    if "simp" in attributes:
        return f"simp add: {short_name}"
    if "intro" in attributes and "!" in attributes:
        return f"apply (rule {short_name})  [strong intro!]"
    if "intro" in attributes:
        return f"intro: {short_name}  or  apply (rule {short_name})"
    if "elim" in attributes:
        return f"erule {short_name}"
    if "dest" in attributes:
        return f"drule {short_name}"
    if rule_type in ("simplification_rule", "definition_rule"):
        return f"simp add: {short_name}"
    if rule_type == "introduction_rule":
        return f"apply (rule {short_name})"
    if rule_type == "induction_rule":
        return f"apply (induction rule: {short_name})  or  by (induction rule: {short_name}) auto"

    # Check if proof uses a concise using ... clause
    if isinstance(proof_text, str) and proof_text.strip():
        proof_lines = [l.strip() for l in proof_text.strip().splitlines() if l.strip()]
        if len(proof_lines) <= 3 and proof_lines[0].startswith("using "):
            combined = " ".join(proof_lines)
            if len(combined) < 250:
                return f"{combined}  or  using {short_name}"

    return f"simp add: {short_name}"


def extract_cited_dependencies(
    finding_text: str,
    proof_steps: Any,
    proof_text: str = "",
) -> list[str]:
    """Extract lemma names cited in tactic finding, proof steps, or proof text."""
    deps: set[str] = set()

    # Look for deps: [...] in finding text
    for match in re.finditer(r"deps:\s*\[(.*?)\]", finding_text or ""):
        content = match.group(1)
        for token in content.split(","):
            t = re.sub(r"^['\"\\\\]+|['\"\\\\]+$", "", token.strip())
            if t and not t.isdigit():
                deps.add(t)

    sources = [finding_text or ""]
    if isinstance(proof_steps, (list, np.ndarray)):
        for s in proof_steps:
            if isinstance(s, dict):
                sources.append(s.get("tactic", ""))
                s_deps = s.get("deps")
                if s_deps is not None and len(s_deps) > 0:
                    for d in s_deps:
                        t = re.sub(r"^['\"\\\\]+|['\"\\\\]+$", "", str(d).strip())
                        if t and not t.isdigit():
                            deps.add(t)
            else:
                sources.append(str(s))
    if proof_text:
        sources.append(proof_text)

    STOPWORDS = {
        "by", "apply", "proof", "qed", "using", "simp", "add", "intro", "elim", "dest",
        "rule", "metis", "meson", "blast", "fastforce", "force", "auto", "cases",
        "induction", "induct", "arbitrary", "unfolding", "then", "of", "where",
        "show", "have", "assume", "obtain", "from", "also", "finally",
        "presburger", "smt", "linarith", "algebra", "arith", "simp_all", "subgoal_tac",
        "ext", "iffi", "conji", "disji1", "disji2", "refl", "sym", "trans", "assms",
        "that", "this", "truei", "falsee", "noti", "note", "impi", "mp", "alli", "spec",
        "exi", "exe", "action", "type", "index", "claim", "deps", "none", "step",
        "by_terminal", "justification_directive"
    }

    ident_pattern = re.compile(r"^[a-zA-Z0-9_\\\\<\^>\.\-\u0080-\uffff]+$")

    for raw_src in sources:
        src = raw_src.replace("\\n", " ").replace("\n", " ").replace("\\r", " ").replace("\r", " ")
        for match in re.finditer(r"(?:using|simp\s+add:|intro:|elim:|dest:|metis|meson|rule|unfolding)\s+([^;\n\)\(]+)", src):
            chunk = match.group(1)
            cleaned = re.sub(r"[\[\],()]", " ", chunk)
            for tok in cleaned.split():
                t = re.sub(r"^['\"\\\\:\.]+|['\"\\\\:\.]+$", "", tok.strip())
                if t.lower() in STOPWORDS or t.startswith("?") or t.isdigit() or t.startswith("step_"):
                    continue
                if "_directive" in t.lower() or "_terminal" in t.lower():
                    continue
                if ident_pattern.match(t) and len(t) > 1:
                    deps.add(t)

        for m in re.finditer(r"([a-zA-Z0-9_]+\.[a-zA-Z0-9_]+)", src):
            cand = m.group(1)
            if cand.lower() not in STOPWORDS and not cand.startswith("step_"):
                deps.add(cand)

    return sorted(deps)


def extract_tactic_summary(meta: dict[str, Any], max_steps: int = 3) -> list[str]:
    """Extract actionable tactic sequence from proof_steps, finding, or proof_text."""
    steps = meta.get("proof_steps")
    tactics: list[str] = []
    if isinstance(steps, (list, np.ndarray)):
        for s in steps:
            if isinstance(s, dict) and s.get("tactic"):
                tactics.append(s["tactic"].strip())
            elif isinstance(s, str) and s.strip():
                tactics.append(s.strip())
            if len(tactics) >= max_steps:
                break
    if not tactics:
        finding = meta.get("finding", "")
        if isinstance(finding, str):
            for match in re.finditer(r'action="([^"]+)"', finding):
                tactics.append(match.group(1).strip())
                if len(tactics) >= max_steps:
                    break
    if not tactics:
        p_text = meta.get("proof_text", "")
        if isinstance(p_text, str) and p_text.strip():
            for line in p_text.splitlines():
                l = line.strip()
                if l and not l.startswith("(*") and len(l) < 200:
                    tactics.append(l)
                if len(tactics) >= max_steps:
                    break
    return tactics


def build_persistent_dossier_summary(candidates: list[dict[str, Any]], top_k: int = 3) -> str:
    """Construct a compact persistent strategic summary to retain across interaction turns."""
    if not candidates:
        return ""

    top_lemmas: list[str] = []
    top_tactics: list[str] = []
    top_deps: list[str] = []
    top_methods: list[str] = []

    for c in candidates[:top_k]:
        meta = c.get("lemma", c)
        title = meta.get("title", "")
        if title:
            top_lemmas.append(title.split(".")[-1])
        method = meta.get("method", "").strip()
        if method and method != "equational-normalization" and method not in top_methods:
            top_methods.append(method.splitlines()[0][:40])
        tactics = extract_tactic_summary(meta, max_steps=2)
        for t in tactics:
            if t not in top_tactics and len(t) < 250:
                top_tactics.append(t)
        finding = meta.get("finding", "")
        deps = extract_cited_dependencies(finding, meta.get("proof_steps"), meta.get("proof_text", ""))
        for d in deps:
            if d not in top_deps:
                top_deps.append(d)

    lines = [
        "━━━ PERSISTENT PROOF CONTEXT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]
    if top_methods:
        lines.append(f"• Inferred Strategy: {', '.join(top_methods[:2])}")
    if top_lemmas:
        lines.append(f"• Key Analogues:     {', '.join(top_lemmas[:4])}")
    if top_tactics:
        lines.append(f"• Tactic Guidance:   {' ⟶ '.join(top_tactics[:2])}")
    if top_deps:
        lines.append(f"• Useful Citations:  {', '.join(top_deps[:6])}")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)


# ── Epistemic Dossier Formatting (3 Dossiers: A, B, C) ────────────────────────

def format_epistemic_dossier(
    candidates: list[dict[str, Any]] | None = None,
    channel_a: list[dict[str, Any]] | None = None,
    channel_b: list[dict[str, Any]] | None = None,
    channel_c: list[dict[str, Any]] | None = None,
) -> str:
    """Format retrieved lemmas as a 3-Dossier Epistemic Intelligence package.

    Dossier A: D(Proof-Strategy | Premises) — hypothesis alignment & strategy selection
    Dossier B: D(Tactic-Map | Conclusion) — conclusion similarity & closing lemma citations
    Dossier C: D(Tactic-Map|Proof-Strategy)∘D(Proof-Strategy|Premises) — strategy-calibrated tactics
    """
    ch_a = list(channel_a) if channel_a is not None else []
    ch_b = list(channel_b) if channel_b is not None else []
    ch_c = list(channel_c) if channel_c is not None else []

    # If channel lists were not passed separately but merged candidates were:
    if not ch_a and not ch_b and not ch_c and candidates:
        for c in candidates:
            channels = c.get("channels", [])
            if "A" in channels or c.get("score_a", 0) > 0:
                ch_a.append(c)
            if "B" in channels or c.get("score_b", 0) > 0:
                ch_b.append(c)
            if "C" in channels or c.get("score_c", 0) > 0 or c.get("hop1_anchor"):
                ch_c.append(c)
        if not ch_a and not ch_b and not ch_c:
            ch_a = list(candidates)

    # Sort each channel strictly descending by cosine similarity score
    ch_a = sorted(ch_a, key=lambda x: float(x.get("score_a") or x.get("score") or 0.0), reverse=True)
    ch_b = sorted(ch_b, key=lambda x: float(x.get("score_b") or x.get("score") or 0.0), reverse=True)
    ch_c = sorted(ch_c, key=lambda x: float(x.get("score_c") or x.get("score") or 0.0), reverse=True)

    total_count = len({
        (c.get("lemma", c).get("title", ""))
        for c in (ch_a + ch_b + ch_c)
        if (c.get("lemma", c).get("title", ""))
    })

    header = (
        f"{'='*60}\n"
        f"  PROOF INTELLIGENCE DOSSIER  —  {total_count} analogue(s) retrieved\n"
        f"  Operators: D(Proof-Strategy|Premises) · D(Tactic-Map|Conclusion)\n"
        f"             · D(Tactic-Map|Proof-Strategy)∘D(Proof-Strategy|Premises)\n"
        f"{'='*60}"
    )

    sections = [header]

    # ── Dossier A: D(Proof-Strategy | Premises) ──────────────────────────────
    lines_a = [
        "\n━━━ DOSSIER A — D(Proof-Strategy | Premises) ━━━━━━━━━━━━━━━━━━━━",
        "What: Lemmas with hypothesis types similar to yours.",
        "Use:  Adopt the Proof Strategy of the top match (Step 1).\n",
    ]
    if ch_a:
        for idx, item in enumerate(ch_a[:3], 1):
            meta = item.get("lemma", item)
            title = meta.get("title", "?")
            problem = meta.get("problem", "").strip()
            method = meta.get("method", "").strip() or "equational-normalization"
            score = float(item.get("score_a") or item.get("score") or 0.0)
            rule_type = meta.get("rule_type", "general_theorem")
            attrs = meta.get("attributes", "none")
            directive = extract_rule_directive(meta)

            lines_a.append(f"[{f'A{idx}'}] {title}  [premise-sim: {score:.3f}]")
            if problem and problem != "none":
                lines_a.append(f"     Premises:       {problem.splitlines()[0][:90]}")
            lines_a.append(f"     Proof Strategy: {method.splitlines()[0][:90]}")
            lines_a.append(f"     Rule Class:     {rule_type} [{attrs}]")
            lines_a.append(f"     → DIRECTIVE:    {directive}\n")
    else:
        lines_a.append("  (No direct premise matches above confidence threshold)\n")
    sections.extend(lines_a)

    # ── Dossier B: D(Tactic-Map | Conclusion) ────────────────────────────────
    lines_b = [
        "\n━━━ DOSSIER B — D(Tactic-Map | Conclusion) ━━━━━━━━━━━━━━━━━━━━━━",
        "What: Lemmas with conclusions similar to your target goal.",
        "Use:  Extract cited lemma names and tactic sequences for your closing tactics (Step 2).\n",
    ]
    if ch_b:
        for idx, item in enumerate(ch_b[:3], 1):
            meta = item.get("lemma", item)
            title = meta.get("title", "?")
            interp = meta.get("interpretation", "").strip() or meta.get("problem", "").strip()
            finding = meta.get("finding", "").strip()
            score = float(item.get("score_b") or item.get("score") or 0.0)
            rule_type = meta.get("rule_type", meta.get("keyword", "general_theorem"))
            attrs = meta.get("attributes", "none")
            directive = extract_rule_directive(meta)
            deps = extract_cited_dependencies(finding, meta.get("proof_steps"), meta.get("proof_text", ""))
            tactics = extract_tactic_summary(meta)

            lines_b.append(f"[{f'B{idx}'}] {title}  [conclusion-sim: {score:.3f}]")
            if interp and interp != "none":
                lines_b.append(f"     Conclusion:     {interp.splitlines()[0][:90]}")
            if tactics:
                lines_b.append(f"     Tactic Steps:   {' ⟶ '.join(tactics)}")
            if deps:
                lines_b.append(f"     Cited Deps:     {', '.join(deps[:6])}")
            lines_b.append(f"     Rule Class:     {rule_type} [{attrs}]")
            lines_b.append(f"     → DIRECTIVE:    {directive}\n")
    else:
        lines_b.append("  (No direct conclusion matches above confidence threshold)\n")
    sections.extend(lines_b)

    # ── Dossier C: 2-Hop Strategy-Calibrated Tactics ──────────────────────────
    lines_c = [
        "\n━━━ DOSSIER C — D(Tactic-Map|Proof-Strategy)∘D(Proof-Strategy|Premises) ━━━",
        "What: 2-hop retrieval. Strategy-calibrated tactics from proofs sharing your architecture.",
        "Use:  Extract deps from lemmas that share your inferred proof architecture (Step 3).\n",
    ]
    if ch_c:
        for idx, item in enumerate(ch_c[:3], 1):
            meta = item.get("lemma", item)
            title = meta.get("title", "?")
            method = meta.get("method", "").strip() or "equational-normalization"
            score = float(item.get("score_c") or item.get("score") or 0.0)
            anchor = item.get("hop1_anchor", "premise-match")
            directive = extract_rule_directive(meta)

            lines_c.append(f"[{f'C{idx}'}] {title}  [strategy-sim: {score:.3f} | anchor: {anchor}]")
            lines_c.append(f"     Proof Strategy: {method.splitlines()[0][:90]}")
            lines_c.append(f"     → TRY SEQUENCE / TACTIC: {directive}\n")
    else:
        lines_c.append("  (Hop-1 premise confidence gate not met or no 2-hop tactics found)\n")
    sections.extend(lines_c)

    return "\n".join(sections)


def format_conditional_transition_result(
    hits: list[dict[str, Any]],
    d_label: str,
    search_aspect: str = "",
    return_aspect: str = "",
) -> str:
    """Format conditional transition search results for interactive MCP tools."""
    if not hits:
        return f"No analogues found for operator {d_label}."

    search_disp = ASPECT_DISPLAY.get(search_aspect, search_aspect or "query")
    return_disp = ASPECT_DISPLAY.get(return_aspect, return_aspect or "all")

    # Sort hits descending by cosine similarity score
    sorted_hits = sorted(hits, key=lambda x: float(x.get("score", 0.0)), reverse=True)

    lines = [
        f"════════════════════════════════════════════════════════════",
        f"  EEL CONDITIONAL TRANSITION: {d_label}",
        f"  Search Space: {search_disp}  →  Highlighted Aspect: {return_disp}",
        f"════════════════════════════════════════════════════════════\n",
    ]

    for idx, h in enumerate(sorted_hits, 1):
        meta = h.get("lemma", h)
        title = meta.get("title", "?")
        score = h.get("score", 0.0)
        anchor = h.get("hop1_anchor")
        header_tag = f"sim: {score:.3f}"
        if anchor:
            header_tag += f" | anchor: {anchor}"

        lines.append(f"[{idx}] {title}  [{header_tag}]")

        # Display relevant content fields
        if return_aspect in ("method", "all", None):
            method = meta.get("method", "").strip()
            if method:
                lines.append("    Proof Strategy:")
                for ml in method.splitlines()[:3]:
                    lines.append(f"        {ml.strip()}")

        if return_aspect in ("finding", "all", None):
            finding = meta.get("finding", "").strip()
            if finding:
                lines.append("    Tactic Step Map:")
                for fl in finding.splitlines()[:4]:
                    lines.append(f"        {fl.strip()}")

        if return_aspect in ("problem", "all", None):
            prob = meta.get("problem", "").strip()
            if prob:
                lines.append("    Premises:")
                for pl in prob.splitlines()[:2]:
                    lines.append(f"        {pl.strip()}")

        if return_aspect in ("interpretation", "all", None):
            interp = meta.get("interpretation", "").strip()
            if interp:
                lines.append("    Conclusion:")
                for il in interp.splitlines()[:2]:
                    lines.append(f"        {il.strip()}")

        directive = extract_rule_directive(meta)
        lines.append(f"    → DIRECTIVE: {directive}\n")

    return "\n".join(lines)


# ── Expert Proof Guidance System Prompt ────────────────────────────────────────

def build_expert_system_prompt() -> str:
    """Build the comprehensive, expert-calibrated system prompt for I/L Treatment."""
    return (
        "You are an expert Isabelle/HOL interactive theorem prover — methodical, strategic, and precise.\n\n"
        "## Output Format (STRICT)\n"
        "- Output EXACTLY ONE Isabelle command per turn in a ```isabelle ... ``` code block.\n"
        "- Valid commands: `apply (...)`, `by (...)`, `proof (...)`, `qed`, `done`, `next`, `have ... by ...`, `show ... by ...`.\n"
        "- Enclose only the Isabelle command in the block — no explanatory text inside the block.\n"
        "- NEVER output multiple commands on one line (e.g. NEVER write `apply (...) apply (...)`). Use ONE command per turn.\n"
        "- NEVER output `sorry`. Do NOT use `done` or `qed` unless all subgoals are genuinely discharged.\n"
        "- If a step fails, the REPL state is unchanged; re-read the error and try a different approach.\n\n"
        "## Expert EEL Proof Formula (Epistemic Reasoning Protocol)\n"
        "You receive an Epistemic Proof Intelligence Dossier built via EEL conditional operators:\n"
        "- DOSSIER A: D(Proof-Strategy | Premises) — hypothesis matching & strategy selection.\n"
        "  * structural-induction: start with `by (induction <var>) auto` or `apply (induction <var> [rule: ...])`\n"
        "  * equational-normalization: open with `apply (simp add: <deps>)` or `by (auto simp: <deps>)`\n"
        "  * resolution-atp: try `by (metis <deps>)` or `by (meson <deps>)`\n"
        "  * classical-tableau: try `by (blast intro: <deps> dest: <deps>)` or `by fastforce`\n"
        "- DOSSIER B: D(Tactic-Map | Conclusion) — conclusion similarity & closing lemma citations (e.g. definitions, rules).\n"
        "  * Read 'Tactic Steps' and cited deps to replicate successful tactic sequences.\n"
        "  * Use `using <deps> by blast` or `using <deps> by auto` when implication dependencies are present.\n"
        "- DOSSIER C: D(Tactic-Map|Proof-Strategy)∘D(Proof-Strategy|Premises) — 2-hop strategy-calibrated tactics.\n\n"
        "## Expert Tactic Execution Ladder\n"
        "1. STRUCTURAL DECOMPOSITION & EXTENSIONALITY:\n"
        "   - If the goal is an equality of functions/relations (`f = g`): open with `apply (intro ext)` or `proof (intro ext)` to work pointwise.\n"
        "   - If the goal is an equivalence (`P ⟷ Q` or `P = Q`): open with `apply (intro iffI)` or use `proof (rule iffI) ... next ... qed` to separate forward and reverse directions if single-step induction fails.\n"
        "   - If the goal relates order relations (`multp r = multp\\<^sub>H\\<^sub>O r`): use cyclic implication facts from Dossier B, e.g. `using multp_imp_multp\\<^sub>H\\<^sub>O multp\\<^sub>H\\<^sub>O_imp_multp\\<^sub>D\\<^sub>M multp\\<^sub>D\\<^sub>M_imp_multp by blast` or `apply (intro ext iffI)`.\n"
        "   - For inductive proofs: prefer `by (induction <var>) auto` to discharge base and step in one step, or `apply (induction <var>)`.\n"
        "   - If goal involves an inductive predicate P: use `apply (induction rule: P.induct)` or `by (induction rule: P.induct) auto`.\n"
        "2. NAMED LEMMA CITATIONS: `using <deps> by blast`, `apply (simp add: <deps>)`, `apply (auto simp: <deps>)`, `by (metis <deps>)`.\n"
        "   Always prefer named lemmas and directives from the dossier over bare automation.\n"
        "3. SUBPROOF DISCHARGE: When in an Isar proof block, prove the active subgoal. Once all subgoals show 'No subgoals', close with `qed`.\n"
        "4. LAST-RESORT AUTOMATION: `by blast` / `by fastforce` / `by auto` only after targeted lemmas fail.\n\n"
        "Rules: NEVER output `sorry`. NEVER use bare `by auto` on turn 1 when dossier provides strategy or deps.\n"
    )



