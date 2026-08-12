"""LeanVerifier: writes Lean source, attempts to run Lean/lake, captures results.

Phase-1 safe skeleton: if lake/lean not available, records that fact and still writes the source.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any
from pathlib import Path
import subprocess
import shutil
import uuid
import json
import sys


@dataclass
class VerificationResult:
    attempt_id: str
    conjecture_id: str
    status: str  # e.g., 'LEAN_NOT_AVAILABLE', 'COMPILE_SUCCESS', 'COMPILE_FAILURE', 'ERROR'
    stdout: str
    stderr: str
    exit_code: Optional[int]
    source_path: Optional[str]
    metadata: Dict[str, Any]


class LeanVerifier:
    def __init__(self, lean_project_dir: str | Path = Path("lean"), prefer_lake: bool = True, timeout_seconds: int = 30):
        self.lean_project_dir = Path(lean_project_dir)
        self.prefer_lake = prefer_lake
        self.timeout_seconds = timeout_seconds
        self.lean_src_dir = self.lean_project_dir / "Conjectures"
        self.lean_src_dir.mkdir(parents=True, exist_ok=True)

    def _find_runner(self) -> Optional[tuple[str, list[str]]]:
        """Return (command, args_list) to run a build/check, or None if not available."""
        lake = shutil.which("lake")
        if lake and self.prefer_lake:
            # use 'lake build' in the project dir
            return (lake, ["build"])
        lean = shutil.which("lean")
        if lean:
            # prefer lean --make (or lean --make <file>)
            return (lean, ["--make"])
        return None

    def write_source(self, conjecture_id: str, lean_source: str) -> str:
        """Write lean_source to a file named by conjecture_id and return path."""
        fname = f"{conjecture_id}.lean"
        p = self.lean_src_dir / fname
        p.write_text(lean_source, encoding="utf-8")
        return str(p)

    def _detect_versions(self) -> Dict[str, str]:
        """Attempt to detect lean/lake versions if available (best-effort)."""
        out = {}
        lake = shutil.which("lake")
        if lake:
            try:
                cp = subprocess.run([lake, "--version"], capture_output=True, text=True, timeout=5)
                out["lake"] = cp.stdout.strip() or cp.stderr.strip()
            except Exception:
                out["lake"] = "unknown"
        lean = shutil.which("lean")
        if lean:
            try:
                cp = subprocess.run([lean, "--version"], capture_output=True, text=True, timeout=5)
                out["lean"] = cp.stdout.strip() or cp.stderr.strip()
            except Exception:
                out["lean"] = "unknown"
        return out

    def check(self, conjecture_id: str, lean_source: str) -> VerificationResult:
        """Write source, attempt to run Lean/lake, capture outputs, and return VerificationResult.

        This is a conservative implementation:
        - always writes the source to lean/Conjectures/<conjecture_id>.lean
        - if no runtime is available, returns LEAN_NOT_AVAILABLE (but still records source)
        - otherwise invokes runner in lean_project_dir and captures stdout/stderr/exit code
        """
        attempt_id = str(uuid.uuid4())
        source_path = self.write_source(conjecture_id, lean_source)
        runner = self._find_runner()
        versions = self._detect_versions()
        if runner is None:
            return VerificationResult(
                attempt_id=attempt_id,
                conjecture_id=conjecture_id,
                status="LEAN_NOT_AVAILABLE",
                stdout="",
                stderr="",
                exit_code=None,
                source_path=source_path,
                metadata={"versions": versions},
            )

        cmd, args = runner
        # If running lean directly, use lean --make <source_path>
        full_cmd = [cmd] + args
        # If args contained '--make' (lean), append the source path
        if "--make" in args:
            full_cmd.append(source_path)
        # For lake build, run from the lean project directory
        try:
            cp = subprocess.run(full_cmd, cwd=str(self.lean_project_dir), capture_output=True, text=True, timeout=self.timeout_seconds)
            exit_code = cp.returncode
            stdout = cp.stdout or ""
            stderr = cp.stderr or ""
            status = "COMPILE_SUCCESS" if exit_code == 0 else "COMPILE_FAILURE"
            return VerificationResult(
                attempt_id=attempt_id,
                conjecture_id=conjecture_id,
                status=status,
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                source_path=source_path,
                metadata={"versions": versions},
            )
        except Exception as e:
            return VerificationResult(
                attempt_id=attempt_id,
                conjecture_id=conjecture_id,
                status="ERROR",
                stdout="",
                stderr=str(e),
                exit_code=None,
                source_path=source_path,
                metadata={"versions": versions},
            )
