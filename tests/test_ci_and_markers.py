"""Guards for pytest conftest isolation/markers and CI workflow coverage."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests import conftest

ROOT = Path(__file__).resolve().parents[1]


def test_conftest_scrubs_pilot_and_dry_run_env_for_subprocesses():
    env = {**os.environ, "LEARNINGOS_PILOT": "1", "NOTION_DRY_RUN": "1"}
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_zero_leak.py",
            "-k",
            "test_save_drill_doc_writes_progress_not_content",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr


@pytest.mark.parametrize("source", ["--basetemp", "PYTEST_DEBUG_TEMPROOT", "TMPDIR"])
def test_conftest_rejects_temp_paths_in_a_checkout(tmp_path, source):
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    (checkout / "id_map.json").write_text("{}", encoding="utf-8")
    # The path supplied to pytest is outside the checkout lexically.
    alias = tmp_path / "alias"
    alias.symlink_to(checkout, target_is_directory=True)
    base = alias / "audit-tmp"
    base.mkdir()

    env = os.environ.copy()
    env.pop("PYTEST_DEBUG_TEMPROOT", None)
    cmd = [sys.executable, "-m", "pytest", "--collect-only", "-q", "tests/test_zero_leak.py"]
    if source == "--basetemp":
        cmd += [source, str(base)]
    else:
        env[source] = str(base)

    proc = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)
    assert proc.returncode == pytest.ExitCode.USAGE_ERROR, proc.stdout + "\n" + proc.stderr
    assert f"{source} must point outside repository checkouts" in proc.stderr
    assert list(base.iterdir()) == []


def test_prg_marker_does_not_swallow_non_prg_file_tests():
    fast_item = SimpleNamespace(
        path=ROOT / "tests" / "test_page_audit.py",
        name="test_prg_unit_page_passes_without_figure_warning",
        markers=[],
        add_marker=lambda m: fast_item.markers.append(m.name),
    )
    prg_file_item = SimpleNamespace(
        path=ROOT / "tests" / "test_prg_lint_layer.py",
        name="test_lint_check",
        markers=[],
        add_marker=lambda m: prg_file_item.markers.append(m.name),
    )
    conftest.pytest_collection_modifyitems(None, [fast_item, prg_file_item])
    assert "prg" not in fast_item.markers
    assert "prg" in prg_file_item.markers


def test_test_unit_scope_prg_ingest_test_carries_explicit_prg_marker():
    from tests import test_unit_scope

    marks = [
        m.name for m in getattr(test_unit_scope.test_prg_load_scope_archetypes_and_ingest_unit_stamp, "pytestmark", [])
    ]
    assert "prg" in marks
    vault_marks = [m.name for m in getattr(test_unit_scope.test_prg_vaults_all_have_valid_unit_codes, "pytestmark", [])]
    assert "prg" not in vault_marks


def test_ci_workflow_checks_all_labs_and_preserves_required_job_names():
    ci_text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    for job_name in ("changes:", "python:", "prg:", "studio:", "lab:"):
        assert f"\n  {job_name}\n" in ci_text
    assert "labs/LAB-*/" in ci_text
    assert "npm run check:reference" in ci_text
    assert "LAB-PRG-T01-C04-02" not in ci_text
    assert "needs.changes.outputs.lab == 'true'" in ci_text
    assert "tools/lint/" in ci_text
    assert "test_unit_scope" in ci_text


def _extract_ci_detect_script() -> str:
    ci_text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    match = re.search(r"- id: detect\n\s+run: \|\n(.*?)\n  python:", ci_text, re.DOTALL)
    assert match is not None, "detect step script not found in .github/workflows/ci.yml"
    return textwrap.dedent(match.group(1))


def _run_ci_detect(
    tmp_path: Path,
    *,
    modify: tuple[str, ...] = (),
    delete: tuple[str, ...] = (),
    rename: tuple[tuple[str, str], ...] = (),
) -> dict[str, str]:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "ci-test@example.com"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "CI Test"], check=True)

    seed_files = (
        *modify,
        *delete,
        *(src for src, _ in rename),
        "practice-studio/src/components/math/MathWorkspace.tsx",
    )
    for rel in sorted(set(seed_files)):
        target = repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "base"], check=True)
    base_sha = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=True)

    for rel in modify:
        target = repo / rel
        target.write_text("changed\n", encoding="utf-8")
    for rel in delete:
        subprocess.run(["git", "-C", str(repo), "rm", "-q", rel], check=True)
    for src, dst in rename:
        (repo / dst).parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "-C", str(repo), "mv", src, dst], check=True)

    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "pr"], check=True)
    head_sha = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=True)

    script = (
        _extract_ci_detect_script()
        .replace("${{ github.event_name }}", "pull_request")
        .replace("${{ github.event.pull_request.base.sha }}", base_sha.stdout.strip())
        .replace("${{ github.event.pull_request.head.sha }}", head_sha.stdout.strip())
    )
    out_file = tmp_path / "github_output"
    env = {**os.environ, "GITHUB_OUTPUT": str(out_file)}
    proc = subprocess.run(["bash", "-e", "-c", script], cwd=repo, env=env, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr
    return dict(line.split("=", 1) for line in out_file.read_text(encoding="utf-8").splitlines() if "=" in line)


@pytest.mark.parametrize(
    "changed_path",
    [
        "scripts/prg_migrate.py",
        "docs/prg_migration_map.json",
        "docs/prg_v1_codes.json",
        "math_engine/source_cores/code_originality.py",
        "math_engine/source_cores/originality.py",
        "math_engine/source_cores/__init__.py",
    ],
)
def test_ci_detect_triggers_prg_for_migration_and_shared_originality(tmp_path: Path, changed_path: str) -> None:
    outputs = _run_ci_detect(tmp_path, modify=(changed_path,))
    assert outputs == {"prg": "true", "lab": "false", "python": "true"}


@pytest.mark.parametrize(
    "changed_path",
    [
        "math_engine/generate.py",
        "drills/data/MTH-T01-C01-U01/DRL-MTH-T01-C01-U01-01.json",
        "math_engine/source_cores/schema.json",
    ],
)
def test_ci_detect_keeps_non_prg_python_changes_out_of_prg_job(tmp_path: Path, changed_path: str) -> None:
    outputs = _run_ci_detect(tmp_path, modify=(changed_path,))
    assert outputs == {"prg": "false", "lab": "false", "python": "true"}


@pytest.mark.parametrize(
    "changed_path",
    [
        "practice-studio/src/types/drill.ts",
        "practice-studio/src/types/figure.ts",
        "practice-studio/src/lib/redact.ts",
        "practice-studio/src/components/MathFigure/GeometryRenderer.tsx",
        "practice-studio/src/components/MathFigure/CartesianRenderer.tsx",
    ],
)
def test_ci_detect_triggers_python_for_studio_contract_files(tmp_path: Path, changed_path: str) -> None:
    outputs = _run_ci_detect(tmp_path, modify=(changed_path,))
    assert outputs == {"prg": "false", "lab": "false", "python": "true"}


@pytest.mark.parametrize(
    "changed_path",
    [
        "practice-studio/src/components/math/MathWorkspace.tsx",
        "practice-studio/src/app/page.tsx",
        "docs/studio_design.md",
    ],
)
def test_ci_detect_skips_python_for_pure_studio_ui_and_design_doc(tmp_path: Path, changed_path: str) -> None:
    outputs = _run_ci_detect(tmp_path, modify=(changed_path,))
    assert outputs == {"prg": "false", "lab": "false", "python": "false"}


def test_ci_detect_triggers_all_jobs_on_studio_deletion_or_rename(tmp_path: Path) -> None:
    del_outputs = _run_ci_detect(tmp_path / "del", delete=("practice-studio/src/components/math/MathWorkspace.tsx",))
    assert del_outputs == {"prg": "true", "lab": "true", "python": "true"}

    ren_outputs = _run_ci_detect(
        tmp_path / "ren",
        rename=(
            (
                "practice-studio/src/components/math/MathWorkspace.tsx",
                "practice-studio/src/components/math/MathWorkspaceNew.tsx",
            ),
        ),
    )
    assert ren_outputs == {"prg": "true", "lab": "true", "python": "true"}
