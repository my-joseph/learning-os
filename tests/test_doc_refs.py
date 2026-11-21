"""Tests for scripts/doc_refs.py using isolated temporary repo fixtures."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.doc_refs import (
    check_changed_docs,
    check_doc_files,
    glob_match,
    has_docs_updated_ack,
    main,
)


def _init_min_repo(root: Path) -> None:
    """Create minimal directory layout for doc_refs fixture tests."""
    (root / ".claude" / "skills" / "demo-skill").mkdir(parents=True)
    (root / ".claude" / "skills" / "demo-skill" / "SKILL.md").write_text("# Demo skill\n", encoding="utf-8")
    (root / "rules").mkdir()
    (root / "docs").mkdir()
    (root / "scripts").mkdir()
    (root / "practice-studio").mkdir()
    (root / "practice-studio" / "package.json").write_text(
        json.dumps({"name": "practice-studio", "scripts": {"lint": "next lint", "build": "next build"}}),
        encoding="utf-8",
    )
    (root / "scripts" / "__init__.py").write_text("", encoding="utf-8")
    (root / "scripts" / "sample_cli.py").write_text(
        "import argparse\n"
        "ap = argparse.ArgumentParser()\n"
        "ap.add_argument('--check', action='store_true')\n"
        "ap.add_argument('--unit', default='')\n"
        "if __name__ == '__main__':\n"
        "    ap.parse_args()\n",
        encoding="utf-8",
    )


def test_valid_references_and_ignored_placeholders(tmp_path: Path) -> None:
    _init_min_repo(tmp_path)
    (tmp_path / "CLAUDE.md").write_text(
        "- Read `rules/*.md`, `scripts/sample_cli.py`, and `sources/<UNIT>/notes.md`.\n"
        "- Ignored runtime dirs: `progress/run.json`, `pilot/out.txt`, `scratch/tmp.json`, `drills/workspace/D1/`.\n"
        "- Run `python -m scripts.sample_cli --check --unit <UNIT>`.\n"
        "- Studio: in `practice-studio/`, run `npm run lint` and `npm run build`.\n"
        "- Use the `demo-skill` skill.\n",
        encoding="utf-8",
    )
    issues = check_doc_files(tmp_path, python_exe=sys.executable)
    assert issues == []


def test_broken_path_detected(tmp_path: Path) -> None:
    _init_min_repo(tmp_path)
    (tmp_path / "rules" / "01_test.md").write_text(
        "See `scripts/does_not_exist.py` and `practice-studio/src/missing.ts`.\n",
        encoding="utf-8",
    )
    issues = check_doc_files(tmp_path, python_exe=sys.executable)
    refs = {(i.file, i.line, i.reference) for i in issues}
    assert ("rules/01_test.md", 1, "scripts/does_not_exist.py") in refs
    assert ("rules/01_test.md", 1, "practice-studio/src/missing.ts") in refs


def test_missing_python_module_detected(tmp_path: Path) -> None:
    _init_min_repo(tmp_path)
    (tmp_path / "CLAUDE.md").write_text(
        "Run `.venv/bin/python -m scripts.no_such_module --check`.\n",
        encoding="utf-8",
    )
    issues = check_doc_files(tmp_path, python_exe=sys.executable)
    assert len(issues) == 1
    assert issues[0].reference == "python -m scripts.no_such_module"
    assert "does not exist" in issues[0].problem


def test_missing_cli_flag_detected(tmp_path: Path) -> None:
    _init_min_repo(tmp_path)
    (tmp_path / "CLAUDE.md").write_text(
        "Run `python -m scripts.sample_cli --check --bogus-flag`.\n",
        encoding="utf-8",
    )
    issues = check_doc_files(tmp_path, python_exe=sys.executable)
    assert len(issues) == 1
    assert issues[0].reference == "python -m scripts.sample_cli --bogus-flag"
    assert "--bogus-flag" in issues[0].problem


def test_subcommand_cli_flags_checked(tmp_path: Path) -> None:
    _init_min_repo(tmp_path)
    (tmp_path / "scripts" / "sub_cli.py").write_text(
        "import argparse\n"
        "ap = argparse.ArgumentParser()\n"
        "sub = ap.add_subparsers(dest='cmd')\n"
        "p_add = sub.add_parser('add')\n"
        "p_add.add_argument('--kind')\n"
        "if __name__ == '__main__':\n"
        "    ap.parse_args()\n",
        encoding="utf-8",
    )
    (tmp_path / "CLAUDE.md").write_text(
        "Good: `python -m scripts.sub_cli add --kind bug`.\nBad: `python -m scripts.sub_cli add --unknown`.\n",
        encoding="utf-8",
    )
    issues = check_doc_files(tmp_path, python_exe=sys.executable)
    assert len(issues) == 1
    assert issues[0].line == 2
    assert "--unknown" in issues[0].reference


def test_missing_optional_binary_skips_help_gracefully(tmp_path: Path) -> None:
    _init_min_repo(tmp_path)
    (tmp_path / "scripts" / "needs_tesseract.py").write_text(
        "import sys\nprint('tesseract binary not found', file=sys.stderr)\nsys.exit(1)\n",
        encoding="utf-8",
    )
    (tmp_path / "CLAUDE.md").write_text(
        "Run `python -m scripts.needs_tesseract --ocr`.\n",
        encoding="utf-8",
    )
    issues = check_doc_files(tmp_path, python_exe=sys.executable)
    assert issues == []


def test_missing_npm_script_and_missing_skill_detected(tmp_path: Path) -> None:
    _init_min_repo(tmp_path)
    (tmp_path / "CLAUDE.md").write_text(
        "In `practice-studio/`: run `npm run nonexistent-script`.\nUse the `ghost-skill` skill.\n",
        encoding="utf-8",
    )
    issues = check_doc_files(tmp_path, python_exe=sys.executable)
    refs = {i.reference for i in issues}
    assert "npm run nonexistent-script" in refs
    assert "ghost-skill" in refs


def test_allowlisted_items_are_ignored(tmp_path: Path) -> None:
    _init_min_repo(tmp_path)
    (tmp_path / "scripts" / "doc_refs_allow.txt").write_text(
        "# Allowlist comments are ignored\n"
        "CLAUDE.md|archive/retired.py  # Historical reference\n"
        "npm run legacy-script  # Removed script kept in historical note\n",
        encoding="utf-8",
    )
    (tmp_path / "CLAUDE.md").write_text(
        "Retired: `archive/retired.py` and `npm run legacy-script`.\n",
        encoding="utf-8",
    )
    (tmp_path / "rules" / "01_other.md").write_text(
        "Not allowlisted in this file: `archive/retired.py`.\n",
        encoding="utf-8",
    )
    issues = check_doc_files(tmp_path, python_exe=sys.executable)
    assert len(issues) == 1
    assert issues[0].file == "rules/01_other.md"
    assert issues[0].reference == "archive/retired.py"


def test_glob_match_supports_double_star() -> None:
    assert glob_match("practice-studio/src/app/api/variant/route.ts", "practice-studio/src/app/api/**")
    assert glob_match("scripts/source_find.py", "scripts/source_*.py")
    assert not glob_match("scripts/weak_spots.py", "scripts/source_*.py")


def test_has_docs_updated_ack_ignores_html_comments() -> None:
    comment_only = "<!-- Docs updated: none needed — template -->\n## What changed\nStuff\n"
    assert not has_docs_updated_ack(comment_only)
    assert has_docs_updated_ack("Docs updated: none needed — internal test refactor")
    assert has_docs_updated_ack("- **Docs updated:** `CLAUDE.md`")


def test_changed_mapping_cli_and_pr_body(tmp_path: Path, monkeypatch, capsys) -> None:
    _init_min_repo(tmp_path)
    (tmp_path / "docs" / "doc_map.json").write_text(
        json.dumps(
            {
                "scripts/sample_cli.py": ["CLAUDE.md", "rules/01_sample.md"],
                "practice-studio/src/app/api/**": ["docs/studio_design.md"],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "CLAUDE.md").write_text("# Root\n", encoding="utf-8")
    (tmp_path / "rules" / "01_sample.md").write_text("# Rule\n", encoding="utf-8")
    (tmp_path / "docs" / "studio_design.md").write_text("# Studio\n", encoding="utf-8")

    # Initialize a real git repo with main branch
    def git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=str(tmp_path), check=True, capture_output=True, text=True)

    git("init", "-b", "main")
    git("config", "user.email", "test@example.com")
    git("config", "user.name", "Test")
    git("add", ".")
    git("commit", "-m", "init")

    git("checkout", "-b", "feat/change")
    (tmp_path / "scripts" / "sample_cli.py").write_text("# modified\n", encoding="utf-8")
    git("add", "scripts/sample_cli.py")
    git("commit", "-m", "feat: touch sample_cli")

    # Fails when no mapped doc updated and PR_BODY has no Docs updated line
    monkeypatch.setenv("PR_BODY", "## What changed\nUpdated sample_cli")
    rc = main(["--changed", "main", "--root", str(tmp_path), "--json"])
    assert rc == 1
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is False
    assert out["mapped_docs"] == ["CLAUDE.md", "rules/01_sample.md"]

    # Passes when PR_BODY has a Docs updated line
    monkeypatch.setenv("PR_BODY", "## Docs updated\nDocs updated: none needed — internal cleanup")
    rc = main(["--changed", "main", "--root", str(tmp_path)])
    assert rc == 0
    capsys.readouterr()

    # Passes without PR_BODY when one of the mapped docs is updated in the branch
    monkeypatch.delenv("PR_BODY", raising=False)
    (tmp_path / "rules" / "01_sample.md").write_text("# Rule updated\n", encoding="utf-8")
    git("add", "rules/01_sample.md")
    git("commit", "-m", "docs: update rule")
    res = check_changed_docs(tmp_path, "main", pr_body="")
    assert res["ok"] is True
    assert res["updated_docs"] == ["rules/01_sample.md"]
