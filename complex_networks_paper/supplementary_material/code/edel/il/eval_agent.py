"""Interactive Multi-Turn Prover Agent & Evaluation Harness for I/L Experiments.

Supports 3 comparative evaluation arms:
1. Arm 0: Baseline (Zero-RAG direct interaction via parametric memory)
2. Arm 1: Control (Naive Monolithic RAG with flat text chunks)
3. Arm 2: Treatment (I/L Epistemic Landscape with 4 aspects, step maps & rule directives)
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from dotenv import load_dotenv

from edel.il.eel_tools import (
    build_expert_system_prompt,
    build_persistent_dossier_summary,
    format_epistemic_dossier,
    multi_channel_retrieve,
    weighted_merge,
)
from edel.il.flat_index import FlatRAGIndex
from edel.il.index import NumpyRAGIndex
from edel.il.ingest import EphemeralReplClient

load_dotenv()


@dataclass
class CompletionResult:
    """Detailed completion result including token breakdown and prompt caching telemetry."""
    text: str
    prompt_tokens: int
    completion_tokens: int
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0
    cost_usd: float = 0.0

    def __getitem__(self, idx):
        return (
            self.text,
            self.prompt_tokens,
            self.completion_tokens,
            self.cache_creation_tokens,
            self.cache_read_tokens,
            self.cost_usd,
        )[idx]


@dataclass
class EvalTrialResult:
    """Telemetry data captured for a single theorem evaluation trial."""
    trial_id: str
    arm: str
    session: str
    theory: str
    lemma_title: str
    difficulty_tier: str
    is_perturbed: bool
    success: bool
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    interaction_turns: int
    error_count: int
    elapsed_seconds: float
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0
    cost_usd: float = 0.0
    retrieved_lemmas: list[str] = field(default_factory=list)
    cited_dependencies: list[str] = field(default_factory=list)
    retrieval_utility: float = 0.0
    transcript: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def ml_str(s: str) -> str:
    """Escape a Python string as an ML string literal."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def ml_int(n: int) -> str:
    """Format a Python int as an ML int literal (negative = ~N)."""
    return f"~{-n}" if n < 0 else str(n)


def extract_isabelle_command(text: str) -> str:
    """Extract a single Isabelle proof step command from LLM response text."""
    # 1. Match enclosed code block
    m = re.search(r"```(?:isabelle|thy)?\s*\n?(.*?)\n?```", text, re.DOTALL | re.IGNORECASE)
    raw_cmd = ""
    if m:
        candidate = m.group(1).strip()
        # If code block contains multiple lines, take the first non-empty line or full 'by ...'
        lines = [line.strip() for line in candidate.splitlines() if line.strip() and not line.strip().startswith("(*")]
        if lines:
            raw_cmd = " ".join(lines) if candidate.startswith("by ") else lines[0]
        else:
            raw_cmd = candidate
    else:
        # 2. Fallback: line starting with known Isabelle tactic/isar keyword
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for line in lines:
            if any(line.startswith(kw) for kw in [
                "apply", "by", "proof", "qed", "done", "show", "have", "next",
                "case", "using", "with", "assume", "fix", "obtain", "moreover", "ultimately", "sorry"
            ]):
                raw_cmd = line
                break
        if not raw_cmd:
            raw_cmd = lines[0] if lines else "by auto"

    # Guard against accidental multi-command concatenations on one line (e.g. "apply (...) apply (...)")
    multi_m = re.match(r"^(apply\s*\([^)]+\))\s+(?:apply|by)\b", raw_cmd)
    if multi_m:
        return multi_m.group(1).strip()

    return raw_cmd


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


class BaseLLMProvider:
    """Base interface for LLM completion providers."""

    def complete(self, system_prompt: str, messages: list[dict[str, Any]]) -> CompletionResult:
        """Generate completion and return CompletionResult."""
        raise NotImplementedError


class AnthropicProvider(BaseLLMProvider):
    """Direct HTTP client for Anthropic Claude models with Prompt Caching support."""

    def __init__(
        self,
        model: str = "claude-sonnet-5",
        api_key: str | None = None,
        max_tokens: int = 512,
        enable_caching: bool = True,
    ):
        self.model = model
        if not api_key and not os.getenv("ANTHROPIC_API_KEY"):
            load_dotenv()
            repo_env = Path(__file__).resolve().parent.parent.parent / ".env"
            if repo_env.exists():
                load_dotenv(repo_env)
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.max_tokens = max_tokens
        self.enable_caching = enable_caching

    def complete(self, system_prompt: str, messages: list[dict[str, Any]]) -> CompletionResult:
        import requests
        import time

        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY environment variable not set.")

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
        }

        if self.enable_caching:
            payload["cache_control"] = {"type": "ephemeral"}
            payload["system"] = [
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ]
        else:
            payload["system"] = system_prompt

        payload["messages"] = messages

        data = {}
        for attempt in range(1, 6):
            try:
                resp = requests.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=payload,
                    timeout=60,
                )
                if resp.status_code in (429, 500, 502, 503, 504, 529):
                    time.sleep(2 ** attempt)
                    continue
                resp.raise_for_status()
                data = resp.json()
                break
            except (requests.RequestException, Exception) as e:
                if attempt == 5:
                    raise
                time.sleep(2 ** attempt)

        text = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                text += block.get("text", "")

        usage = data.get("usage", {})
        uncached_input_tokens = usage.get("input_tokens", len(system_prompt) // 4)
        cache_creation_tokens = usage.get("cache_creation_input_tokens", 0)
        cache_read_tokens = usage.get("cache_read_input_tokens", 0)
        completion_tokens = usage.get("output_tokens", len(text) // 4)
        total_prompt_tokens = uncached_input_tokens + cache_creation_tokens + cache_read_tokens

        # Claude Sonnet 5 Pricing:
        # Base input: $2.00 / M
        # Cache write: $2.50 / M
        # Cache read (hit): $0.20 / M
        # Completion (output): $10.00 / M
        cost_usd = (
            uncached_input_tokens * 2.00
            + cache_creation_tokens * 2.50
            + cache_read_tokens * 0.20
            + completion_tokens * 10.00
        ) / 1_000_000.0

        return CompletionResult(
            text=text.strip(),
            prompt_tokens=total_prompt_tokens,
            completion_tokens=completion_tokens,
            cache_creation_tokens=cache_creation_tokens,
            cache_read_tokens=cache_read_tokens,
            cost_usd=cost_usd,
        )


class MockProvider(BaseLLMProvider):
    """Deterministic mock provider for offline integration testing."""

    def __init__(self, ground_truth_steps: list[str] | None = None):
        self.ground_truth_steps = ground_truth_steps or ["by auto"]
        self.step_idx = 0

    def complete(self, system_prompt: str, messages: list[dict[str, Any]]) -> CompletionResult:
        if self.step_idx < len(self.ground_truth_steps):
            cmd = self.ground_truth_steps[self.step_idx]
            self.step_idx += 1
            text = f"```isabelle\n{cmd}\n```"
        else:
            text = "```isabelle\nby auto\n```"
        return CompletionResult(
            text=text,
            prompt_tokens=100,
            completion_tokens=20,
            cache_creation_tokens=0,
            cache_read_tokens=0,
            cost_usd=0.0,
        )


def get_query_embedding(
    text: str,
    api_key: str = "",
    model: str = "voyage-code-3",
    mock: bool = False,
    dim: int = 1024,
) -> list[float]:
    """Obtain a query embedding vector for dense RAG retrieval."""
    if mock:
        # Deterministic pseudo-vector for testing
        np.random.seed(abs(hash(text)) % (2**32))
        vec = np.random.randn(dim).astype(np.float32)
        norm = np.linalg.norm(vec)
        return (vec / (norm if norm > 1e-10 else 1.0)).tolist()

    key = api_key or os.getenv("VOYAGE_API_KEY", "")
    if not key:
        # Fallback to pseudo-vector if no key available
        np.random.seed(abs(hash(text)) % (2**32))
        vec = np.random.randn(dim).astype(np.float32)
        return vec.tolist()

    import requests
    import time

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    payload = {
        "input": [text],
        "model": model,
        "input_type": "query",
    }
    for attempt in range(1, 6):
        try:
            resp = requests.post(
                "https://api.voyageai.com/v1/embeddings",
                headers=headers,
                json=payload,
                timeout=60,
            )
            if resp.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 ** attempt)
                continue
            resp.raise_for_status()
            data = resp.json()
            return data["data"][0]["embedding"]
        except (requests.RequestException, Exception) as e:
            if attempt == 5:
                # Fallback to pseudo-vector rather than crashing entire benchmark run
                print(f"Warning: Voyage embedding failed after 5 retries ({e}). Falling back to pseudo-vector.")
                np.random.seed(abs(hash(text)) % (2**32))
                vec = np.random.randn(dim).astype(np.float32)
                return vec.tolist()
            time.sleep(2 ** attempt)

    np.random.seed(abs(hash(text)) % (2**32))
    return np.random.randn(dim).astype(np.float32).tolist()


def format_il_treatment_context(candidates: list[dict[str, Any]]) -> str:
    """Format retrieved I/L lemmas as a 3-dossier Epistemic Context Dossier."""
    return format_epistemic_dossier(candidates=candidates)


def format_control_rag_context(candidates: list[dict[str, Any]]) -> str:
    """Format retrieved lemmas into standard monolithic text chunks."""
    blocks = ["### Retrieved Relevant Lemmas (Monolithic Baseline RAG):"]
    for idx, c in enumerate(candidates, 1):
        monolithic = c.get("monolithic_text", "")
        blocks.append(f"[{idx}]\n{monolithic}")
    return "\n\n".join(blocks)


class ProverAgent:
    """Interactive Theorem Proving Agent supporting Baseline, Control RAG, and I/L Treatment."""

    def __init__(
        self,
        arm: str = "baseline",
        repl_client: EphemeralReplClient | None = None,
        llm_provider: BaseLLMProvider | None = None,
        flat_index: FlatRAGIndex | None = None,
        il_index: NumpyRAGIndex | None = None,
        max_turns: int = 15,
        max_tokens: int = 32000,
        history_window: int = 4,
        hop1_score_threshold: float = 0.60,
    ):
        self.arm = arm
        self.repl_client = repl_client
        self.llm_provider = llm_provider or MockProvider()
        self.flat_index = flat_index
        self.il_index = il_index
        self.max_turns = max_turns
        self.max_tokens = max_tokens
        self.history_window = history_window
        self.hop1_score_threshold = hop1_score_threshold

    def build_system_prompt(self) -> str:
        if self.arm == "il_treatment":
            return build_expert_system_prompt()
        return (
            "You are an expert Isabelle/HOL interactive theorem prover — think like Achim Brucker "
            "or a senior AFP contributor: methodical, strategic, and precise.\n\n"
            "## Output Format (STRICT)\n"
            "- Output EXACTLY ONE Isabelle command per turn in a ```isabelle ... ``` code block.\n"
            "- Valid commands: `apply (...)`, `by (...)`, `proof (...)`, `qed`, `done`, `next`, `have ... by ...`, etc.\n"
            "- Enclose only the Isabelle command in the block — no explanatory text inside the block.\n"
            "- NEVER output `sorry`. Do NOT use `done` or `qed` unless all subgoals are genuinely discharged.\n"
            "- If a step fails, the REPL state is unchanged; re-read the error and try a different approach.\n"
        )

    def retrieve_context(self, theorem: dict[str, Any], mock_embedding: bool = False) -> tuple[str, list[str]]:
        """Retrieve external knowledge for Control RAG or I/L Treatment arms."""
        if self.arm == "baseline":
            return "", []

        query_text = theorem.get("statement_text", "")
        title = theorem.get("title", "")
        theory = theorem.get("theory", "")
        line = theorem.get("line", 0)

        # 1. Control Monolithic RAG
        if self.arm == "control_rag":
            if self.flat_index is None or self.flat_index.embeddings is None:
                return "", []

            q_vec = get_query_embedding(
                query_text,
                mock=mock_embedding,
                dim=self.flat_index.embeddings.shape[1] if self.flat_index.embeddings is not None else 1024
            )
            results = self.flat_index.search(
                query_vector=q_vec,
                top_k=3,
                exclude_titles=[title],
                theory=theory,
                max_line=line,
            )
            retrieved_titles = [r["title"] for r in results]
            formatted_text = format_control_rag_context(results)
            return formatted_text, retrieved_titles

        # 2. Treatment I/L Epistemic Landscape — multi-channel retrieval
        if self.arm == "il_treatment":
            if self.il_index is None:
                return "", []

            # Determine embedding dimension from any available aspect matrix
            dim = 1024
            for asp in ("problem", "interpretation", "method", "finding"):
                mat = self.il_index.embeddings.get(asp)
                if mat is not None and mat.shape[0] > 0:
                    dim = mat.shape[1]
                    break

            q_vec = get_query_embedding(query_text, mock=mock_embedding, dim=dim)

            channel_a, channel_b, channel_c = multi_channel_retrieve(
                il_index=self.il_index,
                query_vector=q_vec,
                title=title,
                theory=theory,
                line=line,
                n_direct=5,
                n_twohop=5,
                min_hop1_score=self.hop1_score_threshold,
            )

            merged_candidates = weighted_merge(
                channel_a=channel_a,
                channel_b=channel_b,
                channel_c=channel_c,
                w_a=0.35,
                w_b=0.40,
                w_c=0.25,
                top_k=5,
            )

            retrieved_titles = [c["title"] for c in merged_candidates]
            formatted_text = format_epistemic_dossier(
                candidates=merged_candidates,
                channel_a=channel_a,
                channel_b=channel_b,
                channel_c=channel_c,
            )
            self.persistent_context = build_persistent_dossier_summary(candidates=merged_candidates)
            return formatted_text, retrieved_titles

        return "", []

    def prove_theorem(
        self,
        theorem: dict[str, Any],
        trial_id: str,
        mock_embedding: bool = False,
    ) -> EvalTrialResult:
        """Execute the interactive proof attempt state machine."""
        t_start = time.time()

        title = theorem.get("title", "target_lemma")
        theory = theorem.get("theory", "Main")
        statement = theorem.get("statement_text", "").strip()
        tier = theorem.get("difficulty_tier", "tier_1_terminal")
        is_perturbed = theorem.get("is_perturbed", False)
        cited_str = theorem.get("cited_deps", "")
        cited_deps = [d.strip() for d in cited_str.split(",") if d.strip() and d != "none"]

        # Step 1: Retrieve context
        retrieved_context, retrieved_titles = self.retrieve_context(theorem, mock_embedding=mock_embedding)

        # Calculate retrieval utility: fraction of retrieved items that are cited dependencies
        if retrieved_titles:
            hits = sum(1 for r in retrieved_titles if r in cited_deps or r.split(".")[-1] in cited_deps)
            utility = hits / len(retrieved_titles)
        else:
            utility = 0.0

        # Step 2: Initialize REPL session
        repl_id = f"eval_{int(time.time()*1000) % 100000}_{self.arm}"
        transcript: list[dict[str, Any]] = []
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_cache_creation_tokens = 0
        total_cache_read_tokens = 0
        total_cost_usd = 0.0
        error_count = 0
        success = False

        if self.repl_client is not None:
            try:
                init_out = self.repl_client.send(f"Ir.init {ml_str(repl_id)} [{ml_str(theory)}];")
                if init_out.startswith("ERR") or "undefined entry for theory" in init_out:
                    # Dynamically load theory if not in initial heap
                    self.repl_client.send(f"Ir.load_theory {ml_str(theory)};")
                    init_out = self.repl_client.send(f"Ir.init {ml_str(repl_id)} [{ml_str(theory)}];")
                if init_out.startswith("ERR") or "ERR:" in init_out:
                    raise RuntimeError(f"Failed to initialize REPL session for theory {theory}: {init_out}")

                # Open the lemma goal
                step_init_out = self.repl_client.send(f"Ir.step {ml_str(repl_id)} {ml_str(statement)};")
                if step_init_out.startswith("ERR") or "ERR:" in step_init_out:
                    raise RuntimeError(f"Failed to open lemma statement in REPL: {step_init_out}")
            except Exception as e:

                # If initialization failed, clean and return failure
                try:
                    self.repl_client.send(f"Ir.remove {ml_str(repl_id)};")
                except Exception:
                    pass
                return EvalTrialResult(
                    trial_id=trial_id,
                    arm=self.arm,
                    session=theorem.get("session", ""),
                    theory=theory,
                    lemma_title=title,
                    difficulty_tier=tier,
                    is_perturbed=is_perturbed,
                    success=False,
                    total_tokens=0,
                    prompt_tokens=0,
                    completion_tokens=0,
                    interaction_turns=0,
                    error_count=1,
                    elapsed_seconds=time.time() - t_start,
                    retrieved_lemmas=retrieved_titles,
                    cited_dependencies=cited_deps,
                    retrieval_utility=utility,
                    transcript=[{"turn": 0, "action": "init", "error": str(e)}],
                )

        current_state = ""
        if self.repl_client is not None:
            try:
                current_state = self.repl_client.send(f"Ir.state {ml_str(repl_id)} ~1;")
            except Exception:
                current_state = f"goal (1 subgoal):\n 1. {statement}"
        else:
            current_state = f"goal (1 subgoal):\n 1. {statement}"

        history: list[dict[str, Any]] = []
        system_prompt = self.build_system_prompt()

        # Step 3: Interactive proving loop
        for turn in range(1, self.max_turns + 1):
            if (total_prompt_tokens + total_completion_tokens) >= self.max_tokens:
                transcript.append({"turn": turn, "error": "Max token budget exceeded."})
                break

            # Build sliding-window messages
            messages = []

            # Context header: full dossier on Turn 1, concise goal on Turn 2+
            if turn == 1:
                initial_content = (
                    f"Theory Context: {theory}\n"
                    f"Target Lemma: {title}\n"
                    f"Statement:\n{statement}\n"
                )
                if retrieved_context:
                    initial_content += f"\n{retrieved_context}\n"

                if self.arm == "il_treatment" and retrieved_context:
                    initial_content += (
                        "\n" + "-" * 60 + "\n"
                        "TASK: Consult the Proof Intelligence Dossier above.\n"
                        "- Match your strategy to Dossier A.\n"
                        "- Extract relevant lemmas, tactic steps & directives from Dossier B & C.\n"
                        "Output your FIRST tactic informed by this epistemic context — NOT bare `by auto`.\n"
                        + "-" * 60 + "\n"
                    )
                messages.append({"role": "user", "content": initial_content})
            else:
                last_step = history[-1]["step"] if history else ""
                last_res = history[-1]["result"] if history else ""
                
                context = (
                    f"Target Lemma: {title}\n"
                    f"Statement:\n{statement}\n"
                )
                if self.arm == "il_treatment" and getattr(self, "persistent_context", ""):
                    context += f"\n{self.persistent_context}\n"
                elif retrieved_titles:
                    context += f"Key Lemmas: {', '.join(retrieved_titles[:5])}\n"
                
                query = (
                    f"{context}\n"
                    f"Previous Isabelle command executed:\n```isabelle\n{last_step}\n```\n\n"
                    f"Result / Diagnostics from Kernel:\n{last_res}\n\n"
                    f"Current Proof State:\n{current_state}\n\n"
                    "Provide the next single Isabelle step to advance or close this proof in an ```isabelle ... ``` block."
                )
                messages.append({"role": "user", "content": query})

            # Query LLM provider
            try:
                res = self.llm_provider.complete(system_prompt, messages)
                comp_text = res.text
                p_tok = res.prompt_tokens
                c_tok = res.completion_tokens
                cc_tok = res.cache_creation_tokens
                cr_tok = res.cache_read_tokens
                c_usd = res.cost_usd

                total_prompt_tokens += p_tok
                total_completion_tokens += c_tok
                total_cache_creation_tokens += cc_tok
                total_cache_read_tokens += cr_tok
                total_cost_usd += c_usd
            except Exception as e:
                error_count += 1
                transcript.append({"turn": turn, "error": f"LLM error: {e}"})
                break

            step_cmd = extract_isabelle_command(comp_text)

            # Execute in REPL
            if self.repl_client is not None:
                try:
                    step_out = self.repl_client.send(f"Ir.step {ml_str(repl_id)} {ml_str(step_cmd)};")
                    if step_out.startswith("ERR\n") or "ERR:" in step_out:
                        is_error = True
                        error_count += 1
                        step_result = f"ERR: {step_out}"
                    else:
                        is_error = False
                        step_result = step_out
                        # Get new proof state
                        try:
                            new_state = self.repl_client.send(f"Ir.state {ml_str(repl_id)} ~1;")
                            current_state = new_state if new_state else step_out
                        except Exception:
                            current_state = step_out

                    # Check if closed
                    if not is_error and is_proof_closed(step_cmd, step_out, current_state):
                        success = True
                        history.append({"step": step_cmd, "result": step_result, "state": current_state})
                        transcript.append({
                            "turn": turn,
                            "state": current_state,
                            "step": step_cmd,
                            "status": "OK",
                            "closed": True,
                        })
                        break
                except Exception as e:
                    is_error = True
                    error_count += 1
                    step_result = f"ERR: {e}"
            else:
                # Mock execution: if step is by/done/qed, close
                is_error = False
                step_result = "OK: goal closed"
                if any(step_cmd.startswith(kw) for kw in ["by", "done", "qed"]):
                    success = True
                    transcript.append({"turn": turn, "state": "0 subgoals", "step": step_cmd, "status": "OK", "closed": True})
                    break

            history.append({"step": step_cmd, "result": step_result, "state": current_state})
            transcript.append({
                "turn": turn,
                "state": current_state,
                "step": step_cmd,
                "status": "ERR" if is_error else "OK",
                "closed": success,
            })

        # Step 4: Cleanup REPL
        if self.repl_client is not None:
            try:
                self.repl_client.send(f"Ir.remove {ml_str(repl_id)};")
            except Exception:
                pass

        total_tokens = total_prompt_tokens + total_completion_tokens
        elapsed = time.time() - t_start

        return EvalTrialResult(
            trial_id=trial_id,
            arm=self.arm,
            session=theorem.get("session", ""),
            theory=theory,
            lemma_title=title,
            difficulty_tier=tier,
            is_perturbed=is_perturbed,
            success=success,
            total_tokens=total_tokens,
            prompt_tokens=total_prompt_tokens,
            completion_tokens=total_completion_tokens,
            interaction_turns=len(transcript),
            error_count=error_count,
            elapsed_seconds=elapsed,
            cache_creation_tokens=total_cache_creation_tokens,
            cache_read_tokens=total_cache_read_tokens,
            cost_usd=total_cost_usd,
            retrieved_lemmas=retrieved_titles,
            cited_dependencies=cited_deps,
            retrieval_utility=utility,
            transcript=transcript,
        )
