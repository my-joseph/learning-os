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
    res1 = _staged_hook(repo, "scratch/reviews/x-blind.json")
    assert res1.returncode == 1
    assert "BLOCKED" in res1.stderr
    repo2 = _repo(tmp_path / "b")
    res2 = _staged_hook(repo2, "pilot/labs/L/src/index.ts")
    assert res2.returncode == 1
    assert "BLOCKED" in res2.stderr


def test_hook_blocks_env_and_local_data_dirs(tmp_path):
    for idx, rel in enumerate(
        (
            ".env",
            ".env.local",
            "practice-studio/.env.production",
            "progress/DRL-MTH-T01-C01-U01-01.json",
            "sources/raw/exam.pdf",
            "issues/log.jsonl",
        )
    ):
        repo = _repo(tmp_path / f"repo_{idx}")
        res = _staged_hook(repo, rel)
        assert res.returncode == 1, f"expected hook to block {rel}"
        assert "BLOCKED" in res.stderr
        assert "git restore --staged" in res.stderr


def test_hook_allows_normal_files(tmp_path):
    repo = _repo(tmp_path)
    assert _staged_hook(repo, "drills/data/U/D.json").returncode == 0
    assert _staged_hook(repo, "scripts/env_helper.py").returncode == 0
