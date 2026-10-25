"""
HEX Autonomous Software Developer Subsystem
Enables HEX to inspect repositories, search symbols, reproduce bugs, apply atomic patches,
run pytest/linters in the sandbox, inspect test failures, and generate verifiable diffs.
"""

import os
import re
import difflib
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from sandbox.executor import SandboxEnvironment
from tools.artifacts import artifact_vault
from config.settings import settings


class HexDevEnvironment:
    """Autonomous software engineering toolkit for HEX."""

    def __init__(self, agent_id: str = "dot-hex-05"):
        self.agent_id = agent_id
        self.sandbox = SandboxEnvironment(agent_id)
        self.workspace_dir = self.sandbox.workspace_dir

    def search_code(
        self,
        query: str,
        file_pattern: str = "*.py",
        max_matches: int = 20
    ) -> Dict[str, Any]:
        """
        Searches workspace files for strings or regex patterns.
        """
        results = []
        try:
            pattern = re.compile(query, re.IGNORECASE)
            for file_path in self.workspace_dir.rglob(file_pattern):
                if file_path.is_file() and not file_path.name.startswith("."):
                    rel = file_path.relative_to(self.workspace_dir)
                    try:
                        content = file_path.read_text(encoding="utf-8", errors="replace")
                        for idx, line in enumerate(content.splitlines(), start=1):
                            if pattern.search(line):
                                results.append({
                                    "file": str(rel),
                                    "line_number": idx,
                                    "content": line.strip()
                                })
                                if len(results) >= max_matches:
                                    break
                    except Exception:
                        pass
                if len(results) >= max_matches:
                    break

            return {
                "success": True,
                "query": query,
                "matches_count": len(results),
                "matches": results,
            }
        except Exception as e:
            return {"success": False, "error": f"Search failed: {str(e)}"}

    def apply_patch(
        self,
        relative_path: str,
        target_content: str,
        replacement_content: str
    ) -> Dict[str, Any]:
        """
        Applies a precise, atomic patch to a file in the workspace.
        """
        target_file = (self.workspace_dir / relative_path).resolve()
        # Path traversal guard
        if not str(target_file).startswith(str(self.workspace_dir.resolve())):
            return {"success": False, "error": "Access denied: file outside workspace."}

        if not target_file.exists():
            return {"success": False, "error": f"File '{relative_path}' not found."}

        try:
            original_text = target_file.read_text(encoding="utf-8")
            if target_content not in original_text:
                return {
                    "success": False,
                    "error": "Target content not found in file. Patch could not be applied cleanly."
                }

            # Generate unified diff
            new_text = original_text.replace(target_content, replacement_content, 1)
            diff = "".join(difflib.unified_diff(
                original_text.splitlines(keepends=True),
                new_text.splitlines(keepends=True),
                fromfile=f"a/{relative_path}",
                tofile=f"b/{relative_path}",
            ))

            target_file.write_text(new_text, encoding="utf-8")

            return {
                "success": True,
                "file": relative_path,
                "diff": diff,
                "message": f"Successfully patched '{relative_path}'."
            }
        except Exception as e:
            return {"success": False, "error": f"Patch application failed: {str(e)}"}

    def run_tests(
        self,
        test_file: Optional[str] = None,
        timeout_seconds: int = 30
    ) -> Dict[str, Any]:
        """
        Runs automated tests inside the sandbox and inspects results.
        """
        cmd = f"python -m pytest {test_file if test_file else ''} -v --tb=short"
        res = self.sandbox.run_command(cmd, timeout_seconds=timeout_seconds)

        stdout = res.get("stdout", "")
        stderr = res.get("stderr", "")
        exit_code = res.get("exit_code", -1)

        # Parse test outcomes
        passed = 0
        failed = 0
        errors = 0

        match_passed = re.search(r"(\d+)\s+passed", stdout)
        if match_passed:
            passed = int(match_passed.group(1))

        match_failed = re.search(r"(\d+)\s+failed", stdout)
        if match_failed:
            failed = int(match_failed.group(1))

        match_errors = re.search(r"(\d+)\s+error", stdout)
        if match_errors:
            errors = int(match_errors.group(1))

        all_ok = (exit_code == 0) and (failed == 0) and (errors == 0)

        return {
            "success": all_ok,
            "exit_code": exit_code,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "stdout": stdout[-1500:] if len(stdout) > 1500 else stdout,
            "stderr": stderr[-1000:] if len(stderr) > 1000 else stderr,
            "summary": f"{passed} passed, {failed} failed, {errors} errors (exit code: {exit_code})"
        }

    def generate_patch_deliverable(
        self,
        title: str,
        diff_text: str,
        test_summary: str,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Saves a verified PR patch deliverable in the artifact vault."""
        clean_name = f"{title.lower().replace(' ', '_')[:30]}.patch"
        content = (
            f"# Verified Code Patch: {title}\n"
            f"# Test Outcome: {test_summary}\n"
            f"# Generated by ONE DOTS (HEX Autonomous Developer)\n\n"
            f"{diff_text}"
        )
        art = artifact_vault.save_bytes(
            agent_id=self.agent_id,
            name=clean_name,
            content=content.encode("utf-8"),
            task_id=task_id,
            file_type="patch",
            metadata={"title": title, "test_summary": test_summary}
        )
        return {
            "success": True,
            "artifact_id": art.id,
            "filename": clean_name,
            "download_url": f"/api/artifacts/{art.id}/download",
            "message": f"Code patch '{clean_name}' generated and registered."
        }
