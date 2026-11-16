"""The pre-commit hook refuses files under pilot/ and scratch/ (they hold drill answers)."""

import subprocess
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / ".githooks" / "pre-commit"


def _repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q", "-b", "work", str(tmp_path)], check=True)
    for k, v in (("user.email", "t@example.com"), ("user.name", "t")):
        subprocess.run(["git", "-C", str(tmp_path), "config", k, v], check=True)
    return tmp_path


def _staged_hook(repo: Path, rel: str) -> subprocess.CompletedProcess:
    f = repo / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("{}\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "-f", rel], check=True)
    return subprocess.run(["sh", str(HOOK)], cwd=repo, capture_output=True, text=True)


def test_hook_blocks_scratch_and_pilot_files(tmp_path):
    repo = _repo(tmp_path)
    assert _staged_hook(repo, "scratch/reviews/x-blind.json").returncode == 1
    repo2 = _repo(tmp_path / "b")
    assert _staged_hook(repo2, "pilot/labs/L/src/index.ts").returncode == 1


def test_hook_allows_normal_files(tmp_path):
    repo = _repo(tmp_path)
    assert _staged_hook(repo, "drills/data/U/D.json").returncode == 0
