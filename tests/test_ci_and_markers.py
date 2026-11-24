"""Guards for pytest conftest isolation/markers and CI workflow coverage."""

from __future__ import annotations

import os
import subprocess
import sys
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
