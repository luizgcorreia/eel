"""I/L (Isabelle/Landscape) MCP server for Isabelle/AFP proof assistance."""

from __future__ import annotations

import os
from pathlib import Path

try:
    from fastmcp import FastMCP, Context
except (ImportError, ModuleNotFoundError):
    try:
        from mcp.server.fastmcp import FastMCP, Context
    except (ImportError, ModuleNotFoundError):
        from mcp.server.mcpserver import MCPServer as FastMCP
        from mcp.server.mcpserver import Context

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from edel.il.eel_tools import (
    ASPECT_DISPLAY,
    build_expert_system_prompt,
    format_conditional_transition_result,
    normalize_aspect_name,
)
from edel.il.index import NumpyRAGIndex
from edel.io.llm import get_llm_client

# Initialize MCP Server
mcp = FastMCP("I/L")

# Load Index
index = NumpyRAGIndex()
INDEX_DIR = os.getenv("IL_INDEX_DIR", "artifacts/rag_index")

try:
    index.load(INDEX_DIR)
except Exception as e:
    print(f"Warning: Could not load static RAG index from {INDEX_DIR}: {e}")
    print("I/L will operate in session-only mode unless a static index is loaded.")


def get_embedding_client():
    """Build the embedding client from environment configuration."""
    provider = os.getenv("IL_EMBEDDING_PROVIDER", "voyage")
    model = os.getenv("IL_EMBEDDING_MODEL", "voyage-code-3")
    api_key = os.getenv("VOYAGE_API_KEY" if provider == "voyage" else "OPENAI_API_KEY", "")
    
    config = {
        "provider": provider,
        "model": model,
        "api_key": api_key,
    }
    if provider == "voyage":
        config["input_type"] = "query"
        
    return get_llm_client(config)


def format_search_results(hits: list[dict]) -> str:
    """Format index hits into a readable Markdown block."""
    if not hits:
        return "No matching lemmas found."
        
    lines = []
    for i, hit in enumerate(hits):
        meta = hit["lemma"]
        lines.append(f"### {i+1}. `{meta['title']}` (Score: {hit['score']:.3f})")
        if meta.get("problem") and meta["problem"] != "none":
            lines.append(f"- **Premises**: `{meta['problem']}`")
        if meta.get("interpretation"):
            lines.append(f"- **Conclusion**: `{meta['interpretation']}`")
        if meta.get("method"):
            lines.append(f"- **Skeleton**:\n```isabelle\n{meta['method']}\n```")
        if meta.get("finding"):
            lines.append(f"- **Tactics**:\n```isabelle\n{meta['finding']}\n```")
        if meta.get("proof_text"):
            lines.append(f"- **Proof**:\n```isabelle\n{meta['proof_text']}\n```")
        
        # Source location
        location = f"{meta.get('theory', '')}"
        if meta.get("file"):
            location += f" ({meta['file']}:{meta.get('line', '')})"
        lines.append(f"- **Location**: {location}")
        if meta.get("cited_deps") and meta["cited_deps"] != "none":
            lines.append(f"- **Cited Dependencies**: `{meta['cited_deps']}`")
        if meta.get("dependents_count") is not None:
            lines.append(f"- **Landscape Dependents Count**: `{meta['dependents_count']}`")
        lines.append("")
        
    return "\n".join(lines)


def format_definition_results(hits: list[dict]) -> str:
    """Format definition index hits into a readable Markdown block."""
    if not hits:
        return "No matching definitions found."
        
    lines = []
    for i, hit in enumerate(hits):
        meta = hit["definition"]
        lines.append(f"### {i+1}. `{meta['title']}` (Score: {hit['score']:.3f})")
        lines.append(f"- **Statement**: `{meta['problem']}`")
        
        location = f"{meta.get('theory', '')}"
        if meta.get("file"):
            location += f" ({meta['file']}:{meta.get('line', '')})"
        lines.append(f"- **Location**: {location}")
        if meta.get("dependents") and meta["dependents"] != "none":
            lines.append(f"- **Used in Lemmas**: `{meta['dependents']}`")
        if meta.get("dependents_count") is not None:
            lines.append(f"- **Landscape Dependents Count**: `{meta['dependents_count']}`")
        lines.append("")
        
    return "\n".join(lines)


@mcp.tool(description=(
    "Search for lemmas semantically similar to a query term or pattern across EEL aspect spaces.\n"
    "aspect='premises'       → D(X | Premises): search by hypothesis types.\n"
    "                          Read 'Skeleton' (Proof Strategy) field → D(Proof-Strategy|Premises)\n"
    "                          Read 'Tactics' (Tactic Step Map) field → D(Tactic-Map|Premises)\n"
    "aspect='skeleton'       → D(X | Proof-Strategy): search by proof architecture.\n"
    "                          Read 'Tactics' → D(Tactic-Map|Proof-Strategy)\n"
    "aspect='tactics'        → D(X | Tactic-Map): search by operational tactic pattern.\n"
    "aspect='conclusion'     → D(X | Conclusion): search by final proven statement.\n"
    "                          Read 'Skeleton' → D(Proof-Strategy|Conclusion)\n"
    "                          Read 'Tactics' → D(Tactic-Map|Conclusion)\n"
    "aspect='all'            → Hybrid multi-aspect search.\n\n"
    "Set sort_by_significance=True to bias search results toward widely cited, foundational lemmas.\n"
    "Set min_dependents=K to filter out obscure helper lemmas with fewer than K direct/transitive dependents."
))
async def search_lemmas(
    query: str,
    aspect: str = "conclusion",  # "premises" | "skeleton" | "tactics" | "conclusion" | "all"
    theory_filter: str = "",
    max_results: int = 10,
    sort_by_significance: bool = False,
    min_dependents: int = 0,
) -> str:
    """Perform semantic search on static and live session indices."""
    client = get_embedding_client()
    query_emb = client.generate_embedding(query)

    aspect_map = {
        "premises":     "problem",
        "skeleton":     "method",
        "tactics":      "finding",
        "conclusion":   "interpretation",
    }
    
    if aspect == "all":
        all_results = {}
        for asp_name, idx_asp in aspect_map.items():
            hits = index.search(
                query_emb,
                aspect=idx_asp,
                max_results=max_results,
                theory_filter=theory_filter,
                sort_by_significance=sort_by_significance,
                min_dependents=min_dependents
            )
            for h in hits:
                lemma_id = h["lemma"]["title"]
                if lemma_id not in all_results or h["score"] > all_results[lemma_id]["score"]:
                    all_results[lemma_id] = h
        
        sorted_hits = sorted(all_results.values(), key=lambda x: x["score"], reverse=True)
        hits = sorted_hits[:max_results]
    else:
        idx_asp = aspect_map.get(aspect, "interpretation")
        hits = index.search(
            query_emb,
            aspect=idx_asp,
            max_results=max_results,
            theory_filter=theory_filter,
            sort_by_significance=sort_by_significance,
            min_dependents=min_dependents
        )
        
    return format_search_results(hits)


@mcp.tool(description=(
    "Execute an EEL conditional transition operator D(return_aspect | search_aspect).\n"
    "Searches 'search_aspect' space and returns 'return_aspect' content of nearest neighbors.\n\n"
    "Key uses for Isabelle proof assistance:\n"
    "  D(Proof-Strategy | Premises):   What proof strategies solved similar hypothesis types?\n"
    "  D(Tactic-Map | Premises):       What tactic templates + cited deps were used?\n"
    "  D(Proof-Strategy | Conclusion): What strategies produce similar proven statements?\n"
    "  D(Tactic-Map | Conclusion):     What tactics closed similar goals? (best for closing moves)\n"
    "  D(Tactic-Map | Proof-Strategy): What tactics accompany a specific proof architecture?\n\n"
    "Set chain=True for 2-hop D(Tactic-Map|Proof-Strategy)∘D(Proof-Strategy|Premises):\n"
    "  Infers proof strategy from your premises, then retrieves tactics calibrated to it.\n"
    "  This is the most targeted retrieval for 'I know my hypothesis types but not which lemmas to cite'."
))
async def conditional_transition(
    query: str,
    search_aspect: str = "premises",   # premises | proof-strategy | tactics | conclusion
    return_aspect: str = "tactics",    # premises | proof-strategy | tactics | conclusion
    chain: bool = False,
    max_results: int = 5,
    min_hop1_score: float = 0.60,
) -> str:
    """Execute EEL conditional displacement operator."""
    client = get_embedding_client()
    query_emb = client.generate_embedding(query)

    canonical_search = normalize_aspect_name(search_aspect)
    canonical_return = normalize_aspect_name(return_aspect)

    if chain:
        hits = index.two_hop_search(
            query_vector=query_emb,
            hop1_aspect=canonical_search,
            hop2_aspect="method",
            return_aspect=canonical_return,
            max_results=max_results,
            min_hop1_score=min_hop1_score,
        )
        d_label = f"D({ASPECT_DISPLAY.get(canonical_return, canonical_return)}|Proof-Strategy) ∘ D(Proof-Strategy|{ASPECT_DISPLAY.get(canonical_search, canonical_search)})"
    else:
        hits = index.conditional_search(
            query_vector=query_emb,
            search_aspect=canonical_search,
            return_aspect=canonical_return,
            max_results=max_results,
        )
        d_label = f"D({ASPECT_DISPLAY.get(canonical_return, canonical_return)} | {ASPECT_DISPLAY.get(canonical_search, canonical_search)})"

    return format_conditional_transition_result(
        hits=hits,
        d_label=d_label,
        search_aspect=canonical_search,
        return_aspect=canonical_return,
    )


@mcp.tool(description=(
    "Search for definitions, types, or abbreviations in the dedicated Definition Space. "
    "Returns matching definitions by statement similarity. "
    "Set sort_by_significance=True to bias search results toward foundational/frequently cited entities. "
    "Set min_dependents=K to filter out obscure items used by fewer than K lemmas."
))
async def search_definitions(
    query: str,
    theory_filter: str = "",
    max_results: int = 10,
    sort_by_significance: bool = False,
    min_dependents: int = 0,
) -> str:
    """Perform semantic search on definitions in the Definition Space."""
    client = get_embedding_client()
    query_emb = client.generate_embedding(query)
    hits = index.search_definitions(
        query_emb,
        max_results=max_results,
        theory_filter=theory_filter,
        sort_by_significance=sort_by_significance,
        min_dependents=min_dependents
    )
    return format_definition_results(hits)


@mcp.tool(description=(
    "Find lemmas semantically similar to a known lemma by its title (e.g. 'HOL.List.append_Nil')."
))
async def related_lemmas(
    lemma_name: str,
    max_results: int = 10,
) -> str:
    """Retrieve similar lemmas using the target lemma's pre-computed conclusion embedding."""
    target_idx = None
    for idx, meta in enumerate(index.metadata):
        if meta["title"].lower() == lemma_name.lower():
            target_idx = idx
            break
            
    if target_idx is None:
        return f"Lemma '{lemma_name}' not found in static RAG index."
        
    # Query using conclusion embedding for related lemmas
    vector = index.embeddings["interpretation"][target_idx]
    hits = index.search(vector.tolist(), aspect="interpretation", max_results=max_results + 1)
    
    # Filter out target lemma itself
    hits = [h for h in hits if h["lemma"]["title"].lower() != lemma_name.lower()]
    return format_search_results(hits[:max_results])


@mcp.tool(description=(
    "Store a newly proven lemma in the session index. "
    "Call this after every successful proof to keep the agent's context fresh."
))
async def store_lemma(
    name: str,
    statement: str,
    proof_text: str,
    theory: str,
    cited_deps: list[str] = [],
) -> str:
    """Parse and embed a new lemma, adding it to the runtime session index."""
    from edel.il.aspects import extract_aspects, format_aspect_with_metadata
    
    lemma_dict = {
        "statement_text": f'lemma {name}: "{statement}"',
        "proof_text": proof_text,
        "theory": theory,
        "keyword": "lemma"
    }
    
    aspects = extract_aspects(lemma_dict, text_comments=[])
    aspect_text_dict = {
        "problem":         aspects["aspect_statement"],
        "method":          aspects["aspect_strategy"],
        "finding":         aspects["aspect_dependencies"],
        "interpretation":  aspects["aspect_context"],
    }
    
    client = get_embedding_client()
    embeddings_dict = {}
    
    # Embed aspects using collapse-aware metadata prefixing
    for aspect_name in ["problem", "method", "finding", "interpretation"]:
        formatted = format_aspect_with_metadata(
            theory=theory,
            lemma_title=name,
            aspect=aspect_name,
            aspect_text_dict=aspect_text_dict
        )
        if formatted:
            embeddings_dict[aspect_name] = client.generate_embedding(formatted)
            
    # Set default zero embeddings for any empty aspects
    valid_emb = next((v for v in embeddings_dict.values() if v), None)
    dim = len(valid_emb) if valid_emb else 1536
    for k in ["problem", "method", "finding", "interpretation"]:
        if k not in embeddings_dict:
            embeddings_dict[k] = [0.0] * dim
            
    index.add_live_lemma(
        name=name,
        aspect_text_dict=aspect_text_dict,
        embeddings_dict=embeddings_dict,
        theory=theory,
        proof_text=proof_text,
        cited_deps=cited_deps
    )
    
    return f"Successfully stored lemma '{theory}.{name}' in RAG session index. It is now searchable."


@mcp.tool(description=(
    "Store a newly defined construct (e.g. definition, fun, primrec, datatype) "
    "in the session definition index."
))
async def store_definition(
    name: str,
    statement: str,
    theory: str,
    dependents: list[str] = [],
) -> str:
    """Embed and store a new definition in the session Definition Space."""
    client = get_embedding_client()
    embedding = client.generate_embedding(statement)
    
    index.add_live_definition(
        name=name,
        statement_text=statement,
        embedding=embedding,
        theory=theory,
        dependents=", ".join(dependents) if dependents else "none"
    )
    return f"Successfully stored definition '{theory}.{name}' in the RAG session definition index."


@mcp.tool(description="Permanently persist all dynamically stored session lemmas and definitions to the on-disk static index.")
async def persist_session_lemmas() -> str:
    """Merge the in-memory session index into the on-disk index."""
    num_items = len(index.live_metadata)
    if num_items == 0:
        return "No new session items to persist."
        
    try:
        index.persist_live_lemmas(INDEX_DIR)
        return f"Successfully persisted {num_items} session items to the static index at '{INDEX_DIR}'."
    except Exception as e:
        return f"Failed to persist session items: {str(e)}"


@mcp.tool(description="List all lemmas and definitions added to the RAG session index during this session.")
async def session_lemmas() -> str:
    """Return all session lemmas and definitions."""
    lines = []
    DEF_KEYWORDS = {
        "definition", "fun", "primrec", "function", "datatype", "type_synonym",
        "inductive", "coinductive", "record", "abbreviation"
    }
    
    live_lemmas = [m for m in index.live_metadata if m.get("keyword") not in DEF_KEYWORDS]
    live_defs = [m for m in index.live_metadata if m.get("keyword") in DEF_KEYWORDS]
    
    if live_lemmas:
        lines.append("### Session Lemmas")
        lines.append("")
        for i, meta in enumerate(live_lemmas):
            lines.append(f"{i+1}. `{meta['title']}`")
            if meta.get("problem") and meta["problem"] != "none":
                lines.append(f"   - **Premises**: `{meta['problem']}`")
            lines.append(f"   - **Conclusion**: `{meta['interpretation']}`")
            lines.append("")
            
    if live_defs:
        lines.append("### Session Definitions")
        lines.append("")
        for i, meta in enumerate(live_defs):
            lines.append(f"{i+1}. `{meta['title']}`")
            lines.append(f"   - **Statement**: `{meta['problem']}`")
            lines.append("")
            
    if not lines:
        return "No lemmas or definitions have been stored in this session yet."
        
    return "\n".join(lines)


@mcp.prompt(name="il_proof_strategy", description="Expert guidelines on using I/L conditional displacement operators during an interactive proof session.")
def il_proof_strategy() -> str:
    """Provide structured expert guidelines for using I/L (Isabelle/Landscape)."""
    return (
        "You are an expert Isabelle/Isar assistant — methodical, strategic, and precise.\n"
        "You have access to the I/L (Isabelle/Landscape) vector index and EEL conditional displacement operators.\n\n"
        "## Interactive EEL Proof Construction Protocol\n\n"
        "### Step 0 — Classify the Goal\n"
        "Analyze the conclusion form (Equation, Implication, Membership, Subset/Order, Existence) and variable types.\n\n"
        "### Step 1 — Call D(Proof-Strategy | Premises)\n"
        "Invoke `conditional_transition(query=<premises_and_types>, search_aspect='premises', return_aspect='proof-strategy')`.\n"
        "Adopt the strategy of the top-ranked analogue:\n"
        "  - structural-induction     → `apply (induction <var>)`\n"
        "  - equational-normalization → `simp add: <deps>` or `auto simp: <deps>`\n"
        "  - resolution-atp           → `by (metis <deps>)`\n"
        "  - classical-tableau        → `by (blast intro: <deps>)`\n"
        "  - decision-procedure       → `by linarith` / `by presburger` / `by algebra`\n\n"
        "### Step 2 — Call D(Tactic-Map | Conclusion)\n"
        "Invoke `conditional_transition(query=<goal_statement>, search_aspect='conclusion', return_aspect='tactics')`.\n"
        "Extract cited lemma names from the results and add them to your `simp add:` or `intro:` lemma sets.\n\n"
        "### Step 3 — Strategy-Calibrated Tactics (2-hop chain)\n"
        "Invoke `conditional_transition(query=<premises_and_types>, search_aspect='premises', return_aspect='tactics', chain=True)`.\n"
        "This infers the strategy from your premises and retrieves tactics from other proofs sharing that exact architecture.\n\n"
        "### Tactic Execution Ladder\n"
        "1. Structural decomposition (induction / cases)\n"
        "2. Named lemma citations from Step 2 and 3\n"
        "3. Augmented automation with cited deps (`auto simp: <deps> intro: <deps>`)\n"
        "4. Last-resort automation (`by auto` / `by blast`) only when targeted steps fail\n\n"
        "### Definitions Lookup\n"
        "Use `search_definitions(query=...)` to retrieve relevant datatype, function, or predicate definitions and their dependents.\n"
    )


if __name__ == "__main__":
    mcp.run()
