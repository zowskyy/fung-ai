from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

import repo.git_manager as gm
from repo.git_manager import RepoManager


class FakeGit:
    """An in-memory stand-in for the git binary that still touches the real
    working tree, so the wrapper's status/restore/what-changed logic is real."""

    def __init__(self) -> None:
        self.commits: list[tuple[str, str, dict[str, str]]] = []
        self.head = -1
        self.counter = 0
        self.cwd: str | None = None
        self._staged: dict[str, str] = {}

    def __call__(self, args, cwd, capture_output=True, text=True, encoding=None,
                 errors=None, timeout=None) -> subprocess.CompletedProcess:
        self.cwd = str(cwd)
        rest = list(args[1:])  # args[0] is the "git" executable added by _run
        cmd = rest[0]
        if cmd == "init":
            return self._ok("")
        if cmd == "config":
            return self._ok("")
        if cmd == "status":
            return self._ok("\n".join(self._status_lines()))
        if cmd == "add":
            self._staged = self._snapshot()
            return self._ok("")
        if cmd == "commit":
            return self._commit(rest[2])
        if cmd == "log":
            out = "\n".join(f"{h} {m}" for h, m, _ in self.commits)
            return self._ok(out)
        if cmd == "checkout":
            return self._restore(rest[1])
        if cmd == "reset":
            if "--hard" in rest:
                rev = rest[rest.index("--hard") + 1]
                return self._restore(rev)
            return self._ok("")
        if cmd == "clean":
            return self._ok("")
        if cmd == "show":
            return self._show(rest[-1])
        if cmd == "rev-parse":
            if self.head < 0:
                return self._fail("")
            return self._ok(self.commits[self.head][0])
        return self._ok("")

    def _snapshot(self) -> dict[str, str]:
        snap: dict[str, str] = {}
        base = Path(self.cwd)
        for p in base.rglob("*"):
            if p.is_file() and ".git" not in p.parts:
                rel = str(p.relative_to(base)).replace("\\", "/")
                snap[rel] = p.read_text(encoding="utf-8", errors="replace")
        return snap

    def _status_lines(self) -> list[str]:
        cur = self._snapshot()
        base = self.commits[self.head][2] if self.head >= 0 else {}
        lines = []
        for rel in set(cur) | set(base):
            if cur.get(rel) != base.get(rel):
                lines.append(f" M {rel}" if rel in base else f"?? {rel}")
        return lines

    def _commit(self, message: str) -> subprocess.CompletedProcess:
        staged = self._staged or self._snapshot()
        base = self.commits[self.head][2] if self.head >= 0 else {}
        if staged == base:
            return self._fail("nothing to commit, working tree clean")
        self.counter += 1
        self.commits.append((f"abc{self.counter}", message, dict(staged)))
        self.head = len(self.commits) - 1
        return self._ok("")

    def _restore(self, rev: str) -> subprocess.CompletedProcess:
        target = next((c for c in self.commits if c[0] == rev), None)
        if target is None:
            return self._fail("unknown revision")
        snap = target[2]
        base = Path(self.cwd)
        for p in list(base.rglob("*")):
            if p.is_file() and ".git" not in p.parts:
                rel = str(p.relative_to(base)).replace("\\", "/")
                if rel not in snap:
                    p.unlink()
        for rel, content in snap.items():
            dest = base / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
        self.head = self.commits.index(target)
        return self._ok("")

    def _show(self, rev: str) -> subprocess.CompletedProcess:
        target = next((c for c in self.commits if c[0] == rev), None)
        if target is None:
            return self._fail("unknown revision")
        files = " ".join(target[2].keys())
        return self._ok(f"{target[1]}\n {files} | ...")

    @staticmethod
    def _ok(out: str) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess(["git"], 0, out, "")

    @staticmethod
    def _fail(err: str) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess(["git"], 1, "", err)


@pytest.fixture
def fake_git(monkeypatch):
    fake = FakeGit()
    monkeypatch.setattr(gm, "RUN", fake)
    return fake


def test_save_restore_what_changed(tmp_path, fake_git):
    repo = RepoManager(tmp_path)
    repo.ensure()
    (tmp_path / "game.py").write_text("v1", encoding="utf-8")
    repo.save_version("First")
    (tmp_path / "game.py").write_text("v2", encoding="utf-8")
    repo.save_version("Second")

    versions = repo.list_versions()
    assert len(versions) == 2

    repo.restore(versions[0]["hash"])
    assert (tmp_path / "game.py").read_text(encoding="utf-8") == "v1"
    assert "game.py" in repo.what_changed(versions[1]["hash"])


def test_status_after_change(tmp_path, fake_git):
    repo = RepoManager(tmp_path)
    repo.ensure()
    (tmp_path / "game.py").write_text("v1", encoding="utf-8")
    repo.save_version("First")
    (tmp_path / "game.py").write_text("v2", encoding="utf-8")
    assert repo.status()
