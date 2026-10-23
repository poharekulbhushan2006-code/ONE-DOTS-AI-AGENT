"""
ONE: Always-On Autonomous AI Agent System
Isolated Sandbox & Cloud Computer Environment
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from config.settings import settings


class SandboxEnvironment:
    """
    Provides each agent with its own dedicated sandbox workspace,
    isolated filesystem, and script execution engine.
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.workspace_dir = settings.SANDBOX_BASE_DIR / agent_id
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, relative_path: str) -> Path:
        """Ensures that paths cannot traverse outside the agent's sandbox."""
        resolved = (self.workspace_dir / relative_path).resolve()
        if not str(resolved).startswith(str(self.workspace_dir.resolve())):
            raise PermissionError(f"Access denied: path '{relative_path}' traverses outside sandbox.")
        return resolved

    def run_command(self, command: str, timeout_seconds: int = 30, stdin: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes a shell command inside the agent's sandbox directory.
        """
        try:
            process = subprocess.run(
                command,
                cwd=str(self.workspace_dir),
                shell=True,
                input=stdin if stdin is not None else "",
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            return {
                "exit_code": process.returncode,
                "stdout": process.stdout,
                "stderr": process.stderr,
                "success": process.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Execution timed out after {timeout_seconds} seconds.",
                "success": False,
            }
        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "success": False,
            }

    def run_python(self, code: str, timeout_seconds: int = 30, stdin: Optional[str] = None) -> Dict[str, Any]:
        """
        Runs Python code within the agent sandbox context with non-interactive safe input handling.
        """
        script_file = self.workspace_dir / "_run_tmp.py"
        try:
            # Inject safe input handler to prevent input() from hanging on standard input
            shim = (
                "# --- DOTS Cloud Computer Safe Input Shim ---\n"
                "import builtins\n"
                "_orig_input = builtins.input\n"
                "def _dots_safe_input(prompt=''):\n"
                "    try:\n"
                "        return _orig_input(prompt)\n"
                "    except (EOFError, OSError):\n"
                "        return 'User'\n"
                "builtins.input = _dots_safe_input\n"
                "# --- End Shim ---\n\n"
            )
            script_file.write_text(shim + code, encoding="utf-8")
            python_executable = sys.executable

            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            env["PYTHONIOENCODING"] = "utf-8"

            process = subprocess.run(
                [python_executable, str(script_file)],
                cwd=str(self.workspace_dir),
                input=stdin if stdin is not None else "",
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                env=env,
            )
            return {
                "exit_code": process.returncode,
                "stdout": process.stdout,
                "stderr": process.stderr,
                "success": process.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Execution timed out after {timeout_seconds}s.",
                "success": False,
            }
        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "success": False,
            }
        finally:
            if script_file.exists():
                try:
                    script_file.unlink()
                except Exception:
                    pass

    def write_file(self, filename: str, content: str) -> str:
        safe_path = self._resolve_safe_path(filename)
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_text(content, encoding="utf-8")
        return f"File '{filename}' successfully written ({len(content)} bytes)."

    def read_file(self, filename: str) -> str:
        safe_path = self._resolve_safe_path(filename)
        if not safe_path.exists():
            raise FileNotFoundError(f"File '{filename}' does not exist.")
        return safe_path.read_text(encoding="utf-8")

    def delete_file(self, filename: str) -> bool:
        safe_path = self._resolve_safe_path(filename)
        if safe_path.exists() and safe_path.is_file():
            safe_path.unlink()
            return True
        return False

    def list_files(self) -> List[Dict[str, Any]]:
        results = []
        for root, dirs, files in os.walk(self.workspace_dir):
            rel_root = Path(root).relative_to(self.workspace_dir)
            for f in files:
                p = Path(root) / f
                results.append({
                    "path": str(rel_root / f if str(rel_root) != "." else f),
                    "size_bytes": p.stat().st_size,
                })
        return results
