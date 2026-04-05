"""Safe git operations for Phase 3 autoresearch sessions."""

from __future__ import annotations

import subprocess
from pathlib import Path


class GitWorkspaceManager:
    """Wrap git commands with conservative safety checks."""

    _IGNORED_PREFIXES = ("autoresearch/", "logs/")

    def __init__(self, root: Path) -> None:
        self.root = root

    def current_branch(self) -> str:
        return self._run("git", "rev-parse", "--abbrev-ref", "HEAD")

    def head_commit(self) -> str:
        return self._run("git", "rev-parse", "--short", "HEAD")

    def ensure_clean(self) -> None:
        """Raise if the worktree contains non-artifact changes."""
        dirty = [
            line.split(maxsplit=1)[1]
            for line in self._run("git", "status", "--short").splitlines()
            if line.strip()
        ]
        relevant = [path for path in dirty if not path.startswith(self._IGNORED_PREFIXES)]
        if relevant:
            raise RuntimeError(
                "Phase 3 requires a clean git tree aside from autoresearch/log artifacts. "
                f"Found: {', '.join(relevant)}"
            )

    def create_branch(self, tag: str) -> str:
        branch = f"autoresearch/{tag}"
        self._run("git", "switch", "-c", branch)
        return branch

    def commit_all(self, message: str) -> str:
        self._run("git", "add", "-A")
        self._run("git", "commit", "-m", message)
        return self.head_commit()

    def hard_reset(self, commit: str) -> None:
        self._run("git", "reset", "--hard", commit)

    def _run(self, *args: str) -> str:
        completed = subprocess.run(
            args,
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            stderr = completed.stderr.strip() or completed.stdout.strip()
            raise RuntimeError(stderr or "git command failed")
        return completed.stdout.strip()
