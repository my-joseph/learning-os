"""Test-wide safety: no test may reach the network (Notion included) or write real progress.

Worktrees now read the main checkout's .env, so a real NOTION_TOKEN can be present
while tests run. Tests that exercise the client patch `urlopen` themselves; anything
else that tries to open a URL fails loudly instead of writing to Notion.
"""

import urllib.request

import pytest


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
        if item.path.name.startswith(_PRG_TEST_PREFIXES) or item.name.startswith("test_prg"):
            item.add_marker(pytest.mark.prg)
