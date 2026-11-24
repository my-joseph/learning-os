"""Test-wide isolation for progress and in-process urllib requests.

The health audit applies a separate OS guard to protect learner paths and block
network access in subprocesses.
"""

import os
import tempfile
import urllib.request
from pathlib import Path

import pytest


def _require_external_temp(source: str, value: str) -> None:
    path = Path(os.path.abspath(value))
    for candidate in {path, path.resolve()}:
        # Some tests clear PROGRESS_DIR and let the application walk up to a repo.
        if any(
            (parent / "id_map.json").is_file() or (parent / ".git").exists()
            for parent in (candidate, *candidate.parents)
        ):
            raise pytest.UsageError(f"{source} must point outside repository checkouts: {value}")


def pytest_configure(config: pytest.Config) -> None:
    # Check environment paths before tempfile probes them for writability.
    for name in ("TMPDIR", "TEMP", "TMP"):
        if value := os.environ.get(name):
            _require_external_temp(name, value)
    if basetemp := config.option.basetemp:
        _require_external_temp("--basetemp", basetemp)
    elif temproot := os.environ.get("PYTEST_DEBUG_TEMPROOT"):
        _require_external_temp("PYTEST_DEBUG_TEMPROOT", temproot)
    else:
        _require_external_temp("default temp directory", tempfile.gettempdir())


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Use default modes and synthetic credentials unless a test sets its own."""
    monkeypatch.delenv("LEARNINGOS_PILOT", raising=False)
    monkeypatch.delenv("NOTION_DRY_RUN", raising=False)
    monkeypatch.delenv("NOTION_TOKEN", raising=False)


@pytest.fixture(autouse=True)
def _isolated_progress(monkeypatch, tmp_path):
    """Learner progress written by code under test goes to a temp dir, never the repo's progress/."""
    monkeypatch.setenv("PROGRESS_DIR", str(tmp_path / "progress"))


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    def blocked(*args, **kwargs):
        raise RuntimeError("Network access is disabled in tests (patch urlopen in the test if needed).")

    monkeypatch.setattr(urllib.request, "urlopen", blocked)


# PRG test files run ESLint/tsc/node for many cases and take ~3/4 of the suite's time.
# They carry the `prg` marker so CI can run them only when PRG code or content changes
# (`pytest -m "not prg"` / `pytest -m prg`); a plain `pytest` still runs everything.
_PRG_TEST_PREFIXES = (
    "test_new_code_drill",
    "test_prg_",
    "test_new_project",
    "test_ai_code_ingest",
    "test_lab_ingest",
)


def pytest_collection_modifyitems(config, items):
    for item in items:
        if item.path.name.startswith(_PRG_TEST_PREFIXES):
            item.add_marker(pytest.mark.prg)
