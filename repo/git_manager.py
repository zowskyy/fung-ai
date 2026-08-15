from __future__ import annotations

import subprocess
from pathlib import Path

RUN = subprocess.run


class GitError(RuntimeError):
    pass


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    try:
        return RUN(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except FileNotFoundError:
        raise GitError("Git is not installed on this computer.")
    except subprocess.TimeoutExpired:
        raise GitError("Git is taking too long. Please try again.")


class RepoManager:
    """A safe, plain-words wrapper around git for people who don't use git."""

    def __init__(self, project_dir: Path):
        self.dir = project_dir

    def ensure(self) -> None:
        if not (self.dir / ".git").exists():
            _run(["init"], self.dir)
        if not self._has_identity("user.name"):
            _run(["config", "user.name", "Creator User"], self.dir)
        if not self._has_identity("user.email"):
            _run(["config", "user.email", "creator@localhost"], self.dir)

    def _has_identity(self, key: str) -> bool:
        result = _run(["config", key], self.dir)
        return result.returncode == 0 and bool(result.stdout.strip())

    def status(self) -> list[str]:
        result = _run(["status", "--short"], self.dir)
        if result.returncode != 0:
            raise GitError(result.stderr.strip())
        return [line for line in result.stdout.splitlines() if line.strip()]

    def save_version(self, note: str) -> str:
        self.ensure()
        self._stage_all()
        result = _run(["commit", "-m", note or "Saved a version"], self.dir)
        if result.returncode != 0:
            if "nothing to commit" in (result.stdout + result.stderr):
                return self._head()
            raise GitError(result.stderr.strip())
        return self._head()

    def list_versions(self) -> list[dict]:
        self.ensure()
        result = _run(["log", "--oneline", "--no-decorate"], self.dir)
        versions = []
        for line in result.stdout.splitlines():
            parts = line.split(" ", 1)
            versions.append(
                {"hash": parts[0], "message": parts[1] if len(parts) > 1 else ""}
            )
        return versions

    def restore(self, revision: str) -> None:
        self._stage_all()
        result = _run(["checkout", revision, "--", "."], self.dir)
        if result.returncode != 0:
            raise GitError(result.stderr.strip())

    def what_changed(self, revision: str) -> str:
        result = _run(["show", "--stat", "--format=%s", revision], self.dir)
        if result.returncode != 0:
            return result.stderr.strip()
        return result.stdout.strip()

    def changed_files(self, revision: str) -> list[str]:
        result = _run(["diff-tree", "--no-commit-id", "--name-only", "-r", revision], self.dir)
        if result.returncode != 0:
            return []
        return [f for f in result.stdout.splitlines() if f.strip()]

    def show_file(self, revision: str, filepath: str) -> str:
        result = _run(["show", f"{revision}:{filepath}"], self.dir)
        if result.returncode != 0:
            raise GitError(result.stderr.strip())
        return result.stdout

    def _stage_all(self) -> None:
        result = _run(["add", "-A"], self.dir)
        if result.returncode != 0:
            raise GitError(result.stderr.strip())

    def _head(self) -> str:
        result = _run(["rev-parse", "--short", "HEAD"], self.dir)
        return result.stdout.strip()
