from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools/agents/run-worker.sh"
BRANCH = "fix/worker-test"


def run(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=True)


@pytest.fixture
def worker_env(tmp_path: Path) -> dict[str, Path | str]:
    bare = tmp_path / "remote.git"
    repo = tmp_path / "repo"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    run(["git", "init", "--bare", str(bare)])
    run(["git", "init", "-b", BRANCH, str(repo)])
    run(["git", "config", "user.name", "Worker Test"], cwd=repo)
    run(["git", "config", "user.email", "worker@example.test"], cwd=repo)
    (repo / "tracked.txt").write_text("base\n")
    run(["git", "add", "tracked.txt"], cwd=repo)
    run(["git", "commit", "-m", "test base"], cwd=repo)
    run(["git", "remote", "add", "origin", str(bare)], cwd=repo)
    run(["git", "push", "-u", "origin", BRANCH], cwd=repo)

    pr_open = tmp_path / "pr-open"
    gh = bin_dir / "gh"
    gh.write_text(
        "#!/bin/sh\n"
        'if [ "$1 $2" = \'pr list\' ] && [ -f "$PR_OPEN" ]; then\n'
        '  query=; while [ $# -gt 0 ]; do if [ "$1" = -q ]; then query=$2; shift 2; else shift; fi; done\n'
        '  oid=$(git --git-dir="$BARE_REPO" rev-parse "refs/heads/$BRANCH" 2>/dev/null || true)\n'
        '  if [ -n "$oid" ]; then\n'
        "    case $query in *headRefOid*) printf '%s\\n' \"$oid\";;\n"
        "      *number*) printf '1\\n';;\n"
        '      *) printf \'[{"number":1,"headRefOid":"%s"}]\\n\' "$oid";; esac\n'
        "  else printf '[]\\n'; fi\n"
        "else printf '[]\\n'; fi\n"
    )
    gh.chmod(0o755)

    agy = bin_dir / "agy"
    agy.write_text(
        "#!/bin/sh\n"
        "model=\n"
        'while [ $# -gt 0 ]; do if [ "$1" = --model ]; then model=$2; shift 2; else shift; fi; done\n'
        'if [ "$model" = model2 ]; then\n'
        "  printf 'model two commit\\n' >> tracked.txt\n"
        "  git add -A && git commit -m 'worker model two' && git push origin HEAD:$BRANCH\n"
        "  exit $?\n"
        "fi\n"
        "case $MODEL1_ACTION in\n"
        "  uncommitted_rc3) printf 'left uncommitted\\n' > uncommitted.txt; exit 3;;\n"
        "  quota_text) printf 'quota exceeded\\n' >&2; exit 7;;\n"
        "  nonquota) printf 'ordinary failure\\n' >&2; exit 1;;\n"
        '  create_pr) touch "$PR_OPEN"; exit 0;;\n'
        "  readonly) exit 0;;\n"
        "esac\n"
        "exit 0\n"
    )
    agy.chmod(0o755)
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("worker prompt")
    return {
        "repo": repo,
        "bare": bare,
        "bin": bin_dir,
        "pr_open": pr_open,
        "prompt": prompt,
        "tmp": tmp_path,
    }


def invoke(
    env_info: dict[str, Path | str], action: str, *, models: str = "model1 model2", done_file: Path | None = None
) -> subprocess.CompletedProcess[str]:
    tmp_path = Path(env_info["tmp"])
    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{env_info['bin']}:{env['PATH']}",
            "BRANCH": BRANCH,
            "BARE_REPO": str(env_info["bare"]),
            "PR_OPEN": str(env_info["pr_open"]),
            "MODEL1_ACTION": action,
            "MODELS": models,
            "POLL": "1",
            "IDLE_AFTER_PR": "1",
            "MAX_SECS": "20",
            "USAGE_LOG": str(tmp_path / "usage.jsonl"),
        }
    )
    env.pop("LEARNINGOS_PILOT", None)
    env.pop("NOTION_DRY_RUN", None)
    env.pop("LEARNINGOS_ROLE", None)
    env.pop("AGY_BIN", None)
    env.pop("CODEX_BIN", None)
    if done_file:
        env["DONE_FILE"] = str(done_file)
    else:
        env.pop("DONE_FILE", None)
    return subprocess.run(
        ["bash", str(RUNNER), str(env_info["repo"]), BRANCH, str(env_info["prompt"]), str(tmp_path / "worker.log")],
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
    )


def test_existing_pr_rc3_falls_back_and_finishes_on_new_push(worker_env: dict[str, Path | str]) -> None:
    Path(worker_env["pr_open"]).touch()
    initial_head = run(
        ["git", "--git-dir", str(worker_env["bare"]), "rev-parse", f"refs/heads/{BRANCH}"]
    ).stdout.strip()
    result = invoke(worker_env, "uncommitted_rc3")
    log = (Path(worker_env["tmp"]) / "worker.log").read_text()
    assert result.returncode == 0, result.stderr
    assert "done: PR exists" in log
    assert "model model1 hit a limit (rc=3)" in log
    assert "start model=model2" in log
    updated_head = run(
        ["git", "--git-dir", str(worker_env["bare"]), "rev-parse", f"refs/heads/{BRANCH}"]
    ).stdout.strip()
    assert updated_head != initial_head


def test_existing_pr_quota_text_falls_back(worker_env: dict[str, Path | str]) -> None:
    Path(worker_env["pr_open"]).touch()
    result = invoke(worker_env, "quota_text")
    log = (Path(worker_env["tmp"]) / "worker.log").read_text()
    assert result.returncode == 0, result.stderr
    assert "model model1 hit a limit (rc=7)" in log
    assert "start model=model2" in log


def test_existing_pr_nonquota_failure_does_not_fall_back(worker_env: dict[str, Path | str]) -> None:
    Path(worker_env["pr_open"]).touch()
    result = invoke(worker_env, "nonquota")
    log = (Path(worker_env["tmp"]) / "worker.log").read_text()
    assert result.returncode == 1
    assert "failed rc=1 (not a quota error)" in log
    assert "start model=model2" not in log
    assert "done: PR exists" not in log


def test_existing_pr_rc0_without_push_is_not_done_or_retried(worker_env: dict[str, Path | str]) -> None:
    Path(worker_env["pr_open"]).touch()
    result = invoke(worker_env, "readonly")
    log = (Path(worker_env["tmp"]) / "worker.log").read_text()
    assert result.returncode == 1
    assert "finished rc=0 without advancing the existing PR" in log
    assert "start model=model2" not in log
    assert "done: PR exists" not in log


def test_fresh_branch_completes_when_model_creates_pr(worker_env: dict[str, Path | str]) -> None:
    result = invoke(worker_env, "create_pr", models="model1")
    log = (Path(worker_env["tmp"]) / "worker.log").read_text()
    assert result.returncode == 0, result.stderr
    assert "done: PR exists" in log


def test_read_only_done_file_completion_is_unchanged(worker_env: dict[str, Path | str]) -> None:
    done_file = Path(worker_env["tmp"]) / "done.txt"
    done_file.write_text("report complete\n")
    result = invoke(worker_env, "readonly", models="model1", done_file=done_file)
    log = (Path(worker_env["tmp"]) / "worker.log").read_text()
    assert result.returncode == 0, result.stderr
    assert "done: PR exists" in log
