"""Native PIDE MCP Prover Client Implementation.

Communicates with Sheffield PIDE MCP (Kevin Kappelmann, 2026) via JSON-RPC stdio or HTTP streaming.
Manages ephemeral scratch theories, Isar proof edits, and non-blocking state convergence.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

from edel.il.prover_interface import BaseProverClient, StepResult


class PideMcpProverClient(BaseProverClient):
    """Prover client interacting with Isabelle PIDE via the Model Context Protocol (MCP)."""

    def __init__(
        self,
        command: str | None = None,
        args: list[str] | None = None,
        mcp_url: str | None = None,
        session_name: str = "HOL",
        scratch_dir: str | Path | None = None,
        timeout: float = 30.0,
        convergence_timeout: float = 5.0,
        mock_transport: Any = None,
        **kwargs: Any,
    ):
        """Initialize PIDE MCP client.

        Args:
            command: Executable to launch PIDE MCP server (defaults to PIDE_MCP_COMMAND or 'isabelle').
            args: CLI arguments for PIDE MCP server (defaults to PIDE_MCP_ARGS or ['pide_mcp']).
            mcp_url: Optional HTTP/SSE URL for remote MCP server (overrides stdio).
            session_name: Base Isabelle session (e.g. 'HOL', 'HOL-Library', 'Featherweight_OCL').
            scratch_dir: Directory where ephemeral scratch theories are created.
            timeout: Subprocess and tool call timeout in seconds.
            convergence_timeout: Time to wait for PIDE document processing to stabilize.
            mock_transport: Optional mock transport object for offline unit testing.
        """
        self.command = command or os.getenv("PIDE_MCP_COMMAND", "isabelle")
        if args is not None:
            self.args = args
        else:
            args_env = os.getenv("PIDE_MCP_ARGS", "pide_mcp")
            self.args = args_env.split()

        self.mcp_url = mcp_url or os.getenv("PIDE_MCP_URL", "")
        self.session_name = session_name
        self.timeout = timeout
        self.convergence_timeout = convergence_timeout
        self.mock_transport = mock_transport

        # Scratch theory tracking
        self.scratch_dir = Path(scratch_dir) if scratch_dir else Path(tempfile.gettempdir()) / "pide_scratch"
        self.scratch_dir.mkdir(parents=True, exist_ok=True)
        self.scratch_file: Path | None = None
        self.current_proof_text = "sorry"
        self.theory_id = ""

        # Stdio process tracking
        self.proc: subprocess.Popen | None = None
        self._req_id = 0
        self._session_started = False

    def _next_id(self) -> int:
        self._req_id += 1
        return self._req_id

    def _ensure_connected(self) -> None:
        """Start the MCP server subprocess if not already connected."""
        if self.mock_transport is not None:
            return

        if self.proc is not None and self.proc.poll() is None:
            return

        full_cmd = [self.command, *self.args]
        try:
            self.proc = subprocess.Popen(
                full_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to launch PIDE MCP server with command {full_cmd}: {e}. "
                "Ensure isabelle-pide-mcp component is registered or provide a mock transport."
            )

        # Send initialize request
        init_req = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "edel-il-pide-client", "version": "1.0"},
            },
        }
        resp = self._send_json(init_req)
        if "error" in resp:
            raise RuntimeError(f"PIDE MCP initialization rejected: {resp['error']}")

        # Send initialized notification
        notif = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }
        self._write_line(json.dumps(notif))

    def _write_line(self, line: str) -> None:
        if self.proc and self.proc.stdin:
            self.proc.stdin.write(line + "\n")
            self.proc.stdin.flush()

    def _read_line(self) -> str:
        if self.proc and self.proc.stdout:
            line = self.proc.stdout.readline()
            return line.strip()
        return ""

    def _send_json(self, req: dict[str, Any]) -> dict[str, Any]:
        """Send JSON-RPC request and wait for matching response."""
        self._write_line(json.dumps(req))
        req_id = req.get("id")

        start = time.time()
        while time.time() - start < self.timeout:
            raw = self._read_line()
            if not raw:
                if self.proc and self.proc.poll() is not None:
                    err = self.proc.stderr.read() if self.proc.stderr else ""
                    raise RuntimeError(f"PIDE MCP process exited prematurely: {err}")
                time.sleep(0.01)
                continue

            try:
                resp = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if resp.get("id") == req_id:
                return resp

        raise TimeoutError(f"Timed out waiting for response to JSON-RPC request {req_id}")

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Invoke a tool on the PIDE MCP server."""
        if self.mock_transport is not None:
            return self.mock_transport.call_tool(name, arguments)

        self._ensure_connected()
        req = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        }
        resp = self._send_json(req)
        if "error" in resp:
            return {"is_error": True, "error": resp["error"], "content": []}
        return resp.get("result", {})

    def init_session(self, theory_import: str, lemma_name: str, statement: str) -> str:
        """Create ephemeral scratch theory and register it with PIDE MCP."""
        self.theory_id = f"Scratch_Eval_{uuid.uuid4().hex[:8]}"
        self.scratch_file = self.scratch_dir / f"{self.theory_id}.thy"
        self.current_proof_text = "sorry"

        # Format statement line
        cleaned_stmt = statement.strip()
        if cleaned_stmt.startswith("lemma ") or cleaned_stmt.startswith("theorem "):
            stmt_line = cleaned_stmt
        else:
            safe_name = lemma_name.strip() if lemma_name.strip() else "target_goal"
            stmt_line = f'lemma {safe_name}: "{cleaned_stmt}"'

        # Import cleanup
        safe_import = theory_import.strip() if theory_import.strip() else "Main"

        scratch_content = (
            f"theory {self.theory_id}\n"
            f'  imports "{safe_import}"\n'
            f"begin\n\n"
            f"{stmt_line}\n"
            f"  sorry\n\n"
            f"end\n"
        )

        with open(self.scratch_file, "w", encoding="utf-8") as f:
            f.write(scratch_content)

        # Notify PIDE of file via read
        self.call_tool("read", {"file": str(self.scratch_file)})
        return str(self.scratch_file)

    def step(self, command_or_edit: str) -> StepResult:
        """Execute tactic step or document replacement against active scratch file."""
        if not self.scratch_file or not self.scratch_file.exists():
            return StepResult(
                is_closed=False,
                is_error=True,
                state_text="",
                diagnostics="No active scratch theory initialized.",
            )

        cmd = command_or_edit.strip()
        # Formulate new proof replacement
        if cmd.startswith("by ") or cmd == "done" or cmd.endswith("qed") or "sorry" in cmd:
            new_proof = cmd
        elif cmd.startswith("apply ") or cmd.startswith("proof") or cmd.startswith("have "):
            new_proof = f"{cmd}\n  sorry"
        else:
            # Assume single tactic passed without 'apply'
            new_proof = f"apply ({cmd})\n  sorry"

        # Apply edit via PIDE MCP
        edit_res = self.call_tool(
            "edit",
            {
                "file": str(self.scratch_file),
                "match": self.current_proof_text,
                "replacement": new_proof,
            },
        )

        if edit_res.get("is_error"):
            return StepResult(
                is_closed=False,
                is_error=True,
                state_text="",
                diagnostics=str(edit_res.get("error", "Edit failed")),
                raw_response=json.dumps(edit_res),
            )

        # Update local file on disk to stay in sync with editor state
        try:
            content = self.scratch_file.read_text(encoding="utf-8")
            if self.current_proof_text in content:
                updated = content.replace(self.current_proof_text, new_proof, 1)
                self.scratch_file.write_text(updated, encoding="utf-8")
        except Exception:
            pass

        self.current_proof_text = new_proof

        # Poll for convergence
        return self._poll_convergence()

    def _poll_convergence(self) -> StepResult:
        """Poll PIDE state until subgoals stabilize or errors are detected."""
        start = time.time()
        last_state = ""
        last_diag = ""

        while time.time() - start < self.convergence_timeout:
            res = self.call_tool("get_state", {"file": str(self.scratch_file)})
            content = res.get("content", [])
            text_payload = ""
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_payload += item.get("text", "") + "\n"
                elif isinstance(item, str):
                    text_payload += item + "\n"

            # Check diagnostics / errors in result
            diagnostics = res.get("diagnostics", "") or ""
            if not diagnostics and "error" in text_payload.lower():
                # Extract error lines
                err_lines = [l for l in text_payload.splitlines() if "error" in l.lower() or "failed" in l.lower()]
                diagnostics = "\n".join(err_lines)

            is_error = bool(diagnostics and any(w in diagnostics.lower() for w in ["error", "failed", "cannot"]))

            # Check proof closure
            # In Isabelle PIDE, goal state contains "No subgoals!" or subgoals list is empty
            is_closed = False
            if not is_error:
                if "no subgoals" in text_payload.lower() or "goal: (0 subgoals)" in text_payload.lower():
                    is_closed = True
                elif "sorry" not in self.current_proof_text and (
                    self.current_proof_text.startswith("by ") or self.current_proof_text.endswith("qed")
                ):
                    # Finished proof block with no errors
                    is_closed = True

            last_state = text_payload.strip()
            last_diag = diagnostics.strip()

            if is_error or is_closed:
                return StepResult(
                    is_closed=is_closed,
                    is_error=is_error,
                    state_text=last_state,
                    diagnostics=last_diag,
                    raw_response=json.dumps(res),
                )

            time.sleep(0.05)

        # Timeout reached: return latest state
        return StepResult(
            is_closed=False,
            is_error=False,
            state_text=last_state,
            diagnostics=last_diag,
            raw_response="Convergence timeout elapsed",
        )

    def get_state(self) -> str:
        """Query current proof state from PIDE MCP."""
        if not self.scratch_file:
            return ""
        res = self.call_tool("get_state", {"file": str(self.scratch_file)})
        content = res.get("content", [])
        text_payload = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_payload.append(item.get("text", ""))
            elif isinstance(item, str):
                text_payload.append(item)
        return "\n".join(text_payload).strip()

    def close_session(self) -> None:
        """Clean up ephemeral scratch files and shutdown subprocess."""
        if self.scratch_file and self.scratch_file.exists():
            try:
                self.scratch_file.unlink()
            except Exception:
                pass
            self.scratch_file = None

        if self.proc is not None:
            try:
                if self.proc.stdin:
                    self.proc.stdin.close()
                self.proc.terminate()
                self.proc.wait(timeout=2.0)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass
            self.proc = None
