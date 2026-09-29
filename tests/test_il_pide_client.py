"""Unit tests for PideMcpProverClient and PIDE MCP integration."""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from edel.il.pide_client import PideMcpProverClient
from edel.il.prover_interface import get_prover_client, StepResult


class MockPideMcpTransport:
    """In-memory mock transport simulating Sheffield PIDE MCP responses."""

    def __init__(self):
        self.files: dict[str, str] = {}
        self.call_history: list[tuple[str, dict]] = []
        self.state_responses: list[dict] = []
        self.error_on_next_step: str | None = None

    def call_tool(self, name: str, arguments: dict) -> dict:
        self.call_history.append((name, arguments))
        if name == "read":
            file_path = arguments["file"]
            content = Path(file_path).read_text(encoding="utf-8") if Path(file_path).exists() else ""
            self.files[file_path] = content
            return {"content": [{"type": "text", "text": f"Loaded file {file_path}"}]}

        elif name == "edit":
            file_path = arguments["file"]
            match_str = arguments["match"]
            rep_str = arguments["replacement"]
            if file_path in self.files:
                self.files[file_path] = self.files[file_path].replace(match_str, rep_str, 1)
            return {"content": [{"type": "text", "text": "Edit applied successfully"}]}

        elif name == "get_state":
            if self.error_on_next_step:
                err = self.error_on_next_step
                self.error_on_next_step = None
                return {
                    "content": [{"type": "text", "text": f"Error: {err}"}],
                    "diagnostics": f"Error: {err}",
                }

            if self.state_responses:
                return self.state_responses.pop(0)

            # Default goal state
            file_path = arguments.get("file", "")
            content = self.files.get(file_path, "")
            if "by simp" in content or "qed" in content:
                return {"content": [{"type": "text", "text": "No subgoals!\nlemma proved"}]}
            elif "apply auto" in content:
                return {"content": [{"type": "text", "text": "proof (state)\ngoal (1 subgoal):\n 1. A = A"}]}
            return {"content": [{"type": "text", "text": "proof (state)\ngoal (1 subgoal):\n 1. target_goal"}]}

        elif name == "start_session":
            return {"content": [{"type": "text", "text": "Session started"}]}

        return {"content": []}


def test_factory_get_prover_client():
    client_ir = get_prover_client("ir")
    from edel.il.ir_client import ReplProverClient
    assert isinstance(client_ir, ReplProverClient)

    client_pide = get_prover_client("pide")
    assert isinstance(client_pide, PideMcpProverClient)

    with pytest.raises(ValueError):
        get_prover_client("unsupported_backend")


def test_pide_init_session_and_scratch_file(tmp_path):
    mock_transport = MockPideMcpTransport()
    client = PideMcpProverClient(
        scratch_dir=tmp_path,
        mock_transport=mock_transport,
        convergence_timeout=0.5,
    )

    scratch_path = client.init_session(
        theory_import="HOL-Library.Multiset",
        lemma_name="test_lemma",
        statement="x + 0 = x",
    )

    assert Path(scratch_path).exists()
    content = Path(scratch_path).read_text(encoding="utf-8")
    assert 'imports "HOL-Library.Multiset"' in content
    assert 'lemma test_lemma: "x + 0 = x"' in content
    assert "sorry" in content
    assert any(c[0] == "read" for c in mock_transport.call_history)

    client.close_session()
    assert not Path(scratch_path).exists()


def test_pide_step_terminal_tactic(tmp_path):
    mock_transport = MockPideMcpTransport()
    client = PideMcpProverClient(
        scratch_dir=tmp_path,
        mock_transport=mock_transport,
        convergence_timeout=0.5,
    )

    client.init_session(
        theory_import="Main",
        lemma_name="add_0",
        statement="x + 0 = (x::nat)",
    )

    res = client.step("by simp")
    assert isinstance(res, StepResult)
    assert res.is_closed is True
    assert res.is_error is False
    assert "no subgoals" in res.state_text.lower()

    client.close_session()


def test_pide_step_intermediate_apply_tactic(tmp_path):
    mock_transport = MockPideMcpTransport()
    client = PideMcpProverClient(
        scratch_dir=tmp_path,
        mock_transport=mock_transport,
        convergence_timeout=0.5,
    )

    client.init_session(
        theory_import="Main",
        lemma_name="goal_step",
        statement="A & B --> A",
    )

    res = client.step("apply auto")
    assert isinstance(res, StepResult)
    assert res.is_closed is False
    assert res.is_error is False
    assert "goal (1 subgoal)" in res.state_text

    client.close_session()


def test_pide_step_error_handling(tmp_path):
    mock_transport = MockPideMcpTransport()
    mock_transport.error_on_next_step = "Failed to apply proof method: simp"

    client = PideMcpProverClient(
        scratch_dir=tmp_path,
        mock_transport=mock_transport,
        convergence_timeout=0.5,
    )

    client.init_session(
        theory_import="Main",
        lemma_name="bad_step",
        statement="False",
    )

    res = client.step("by simp")
    assert isinstance(res, StepResult)
    assert res.is_closed is False
    assert res.is_error is True
    assert "Failed to apply proof method" in res.diagnostics

    client.close_session()


def test_pide_step_isar_block(tmp_path):
    mock_transport = MockPideMcpTransport()
    client = PideMcpProverClient(
        scratch_dir=tmp_path,
        mock_transport=mock_transport,
        convergence_timeout=0.5,
    )

    client.init_session(
        theory_import="Main",
        lemma_name="isar_lemma",
        statement="x = x",
    )

    isar_proof = "proof -\n  show ?thesis by simp\nqed"
    res = client.step(isar_proof)
    assert isinstance(res, StepResult)
    assert res.is_closed is True
    assert res.is_error is False

    client.close_session()
