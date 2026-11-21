#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify documentation references against the repository and enforce doc-map updates.

Usage:
    python -m scripts.doc_refs [--json]
    python -m scripts.doc_refs --changed origin/main [--json]
"""

from __future__ import annotations

import argparse
import dataclasses
import fnmatch
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

RUNTIME_GITIGNORED_PREFIXES = (
    "sources",
    "progress",
    "pilot",
    "scratch",
    "drills/workspace",
    "issues",
    "reports/samples",
    ".venv",
    "node_modules",
    "practice-studio/node_modules",
    "logs",
)

KNOWN_ROOT_PREFIXES = (
    "rules/",
    "docs/",
    "scripts/",
    "math_engine/",
    "code_engine/",
    "notion_sync/",
    "practice-studio/",
    "labs/",
    "tools/",
    "tests/",
    "drills/",
    "archive/",
    "assets/",
    "migrations/",
    "reports/",
    ".claude/",
    ".github/",
    ".githooks/",
    ".vscode/",
    "curriculum/",
)

KNOWN_ROOT_FILES = {
    "CLAUDE.md",
    "AGENTS.md",
    "GEMINI.md",
    "id_map.json",
    "skills_taxonomy.json",
    "quality_rules.py",
    "progress_store.py",
    "requirements.txt",
    "requirements-dev.txt",
    "ruff.toml",
    "pytest.ini",
    ".gitignore",
}

MEMORY_FREE_DOCS = (
    "CLAUDE.md",
    "AGENTS.md",
    "GEMINI.md",
    ".github/pull_request_template.md",
    "tools/agents/README.md",
    "practice-studio/README.md",
    "math_engine/templates/README.md",
)

BUILTIN_PYTHON_MODULES = {
    "...",
    "pip",
    "pytest",
    "ruff",
    "unittest",
    "venv",
    "json.tool",
    "http.server",
}

GENERATED_WORKSPACE_SCRIPTS = {
    "test",
    "test:watch",
    "lint",
    "typecheck",
    "check",
    "review",
    "submit",
}

_URL_SCHEMES = ("http://", "https://", "vscode://", "cursor://", "mailto:", "sha256:")
_FILE_EXT_RE = re.compile(r"\.(py|ts|tsx|js|mjs|json|md|sh|yml|yaml|toml|ini|txt|css|jsonl)$")
_BARE_SCRIPT_RE = re.compile(r"^[A-Za-z0-9_.-]+\.(py|sh)$")
_PY_MOD_CMD_RE = re.compile(
    r"(?:^|[\s\"'(\[])(?:env\s+[^\n]*?)?(?:\.venv/bin/python|python3?)\s+-m\s+([A-Za-z0-9_.]+)([^\n`&|;]*)"
)
_PY_FILE_CMD_RE = re.compile(r"(?:^|[\s\"'(\[])(?:\.venv/bin/python|python3?)\s+([A-Za-z0-9_./-]+\.py)\b([^\n`&|;]*)")
_NPM_RUN_RE = re.compile(r"\bnpm\s+run\s+([A-Za-z0-9_:<>*.-]+)")
_SKILL_REF_RE = re.compile(
    r"(?:`([a-z0-9-]+)`\s+skill\b|\bskill\s+`([a-z0-9-]+)`|\.claude/skills/([a-z0-9-]+)(?:/|\b))"
)
_FLAG_RE = re.compile(r"(?<![A-Za-z0-9_-])(--[A-Za-z0-9][A-Za-z0-9-]*)")
_HTML_COMMENT_RE = re.compile(r"<!--[\s\S]*?-->")
_DOCS_UPDATED_LINE_RE = re.compile(
    r"^\s*(?:[-*]\s*)?\*{0,2}docs\s+updated\*{0,2}\s*:\s*\S+",
    re.IGNORECASE | re.MULTILINE,
)

_OPTIONAL_BINARY_MARKERS = (
    "tesseract",
    "pdftoppm",
    "eslint",
    "tsc",
    "node",
    "no such file or directory",
    "not found",
)


@dataclasses.dataclass(frozen=True)
class DocIssue:
    file: str
    line: int
    reference: str
    problem: str

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    def format_line(self) -> str:
        return f"{self.file}:{self.line} | {self.reference} | {self.problem}"


def default_repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def discover_doc_files(root: Path) -> list[Path]:
    """Return sorted relative paths of documentation files to scan."""
    seen: set[Path] = set()
    patterns = (
        ".claude/skills/**/*.md",
        "rules/*.md",
        "docs/*.md",
    )
    for pat in patterns:
        for p in root.glob(pat):
            if p.is_file():
                seen.add(p.relative_to(root))
    for rel in MEMORY_FREE_DOCS:
        p = root / rel
        if p.is_file():
            seen.add(Path(rel))
    return sorted(seen)


def load_allowlist(root: Path) -> set[tuple[str | None, str]]:
    """Load intentional exceptions from scripts/doc_refs_allow.txt.

    Each non-empty, non-comment line holds `<reference>  # <reason>` or
    `<file>|<reference>  # <reason>`.
    """
    allow_path = root / "scripts" / "doc_refs_allow.txt"
    entries: set[tuple[str | None, str]] = set()
    if not allow_path.is_file():
        return entries
    for raw in allow_path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if "|" in line:
            doc_file, ref = line.split("|", 1)
            entries.add((doc_file.strip(), ref.strip()))
        else:
            entries.add((None, line))
    return entries


def _is_allowlisted(allowlist: set[tuple[str | None, str]], rel_file: str, ref: str) -> bool:
    return (None, ref) in allowlist or (rel_file, ref) in allowlist


def is_runtime_path(path_str: str) -> bool:
    cleaned = path_str.rstrip("/")
    return any(cleaned == p or cleaned.startswith(p + "/") for p in RUNTIME_GITIGNORED_PREFIXES)


def has_placeholder(token: str) -> bool:
    return any(ch in token for ch in ("<", ">", "*", "?", "{", "…")) or "..." in token


def _strip_anchor_or_line(token: str) -> str:
    p = token.rstrip("/")
    if "#" in p:
        p = p.split("#", 1)[0]
    if ":" in p:
        p = p.split(":", 1)[0]
    return p


def _resolve_repo_path(root: Path, doc_rel: Path, candidate: str) -> bool:
    """Return True if candidate resolves to an existing file/dir in root."""
    p = _strip_anchor_or_line(candidate)
    if not p:
        return True
    if is_runtime_path(p):
        return True
    if (root / p).exists():
        return True
    # Allow paths relative to the document's directory (e.g. practice-studio/README.md)
    doc_dir = (root / doc_rel).parent
    try:
        resolved = (doc_dir / p).resolve()
        if resolved.is_relative_to(root.resolve()):
            rel_posix = resolved.relative_to(root.resolve()).as_posix()
            if resolved.exists() or is_runtime_path(rel_posix):
                return True
    except OSError:
        pass
    # Shorthand rule section citation like `rules/07` §4
    if re.fullmatch(r"rules/\d{2}", p):
        if list((root / "rules").glob(f"{p.split('/', 1)[1]}_*.md")):
            return True
    return False


def _looks_like_repo_path_token(token: str) -> bool:
    if not token or " " in token or "\t" in token:
        return False
    if token.startswith(_URL_SCHEMES) or token.startswith(("/", "$", "@", "-")):
        return False
    if token in KNOWN_ROOT_FILES:
        return True
    if token.startswith(KNOWN_ROOT_PREFIXES):
        return True
    if token.startswith(("../", "./")) and "/" in token:
        return True
    if _BARE_SCRIPT_RE.fullmatch(token):
        return True
    if "/" in token and _FILE_EXT_RE.search(_strip_anchor_or_line(token)):
        first = token.split("/", 1)[0]
        # Skip domain-like URLs without scheme (e.g. mathsgenie.co.uk/terms)
        if "." in first and not first.startswith("."):
            return False
        return True
    return False


def _find_bare_script_in_repo(root: Path, filename: str) -> bool:
    if (root / filename).exists():
        return True
    for p in root.rglob(filename):
        parts = p.relative_to(root).parts
        if any(seg in ("node_modules", ".git", "archive", ".venv", "__pycache__") for seg in parts):
            continue
        return True
    return False


def _collect_npm_scripts(root: Path) -> dict[str, set[str]]:
    """Map package directory (relative posix path) -> set of script names."""
    packages: dict[str, set[str]] = {}
    candidates = [root / "practice-studio" / "package.json", root / "tools" / "lint" / "package.json"]
    labs_dir = root / "labs"
    if labs_dir.is_dir():
        for p in sorted(labs_dir.glob("*/package.json")):
            if p.parent.name.startswith("_"):
                continue
            candidates.append(p)
    for pkg in candidates:
        if not pkg.is_file():
            continue
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        scripts = data.get("scripts")
        if isinstance(scripts, dict):
            rel_dir = pkg.parent.relative_to(root).as_posix()
            packages[rel_dir] = set(scripts.keys())
    return packages


def _matching_npm_scopes(line: str, doc_rel: Path, packages: dict[str, set[str]]) -> set[str] | None:
    """Return allowed npm script names for the line's context, or None if not scoped."""
    if "practice-studio" in line or doc_rel.parts[0] == "practice-studio":
        return packages.get("practice-studio", set())
    lab_m = re.search(r"labs/(LAB-[A-Za-z0-9-]+)", line)
    if lab_m:
        key = f"labs/{lab_m.group(1)}"
        if key in packages:
            return packages[key]
    if "tools/lint" in line and "lab" not in line.lower() and "workspace" not in line.lower():
        return packages.get("tools/lint", set())
    return None


def _run_help(
    root: Path,
    python_exe: str,
    cmd_args: list[str],
    cache: dict[tuple[str, ...], tuple[str, str]],
) -> tuple[str, str]:
    """Run `<python> <cmd_args> --help` with timeout and caching.

    Returns (status, output) where status is 'ok', 'skip', or 'fail'.
    """
    key = tuple(cmd_args)
    if key in cache:
        return cache[key]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    try:
        proc = subprocess.run(
            [python_exe, *cmd_args, "--help"],
            cwd=str(root),
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        cache[key] = ("skip", str(exc))
        return cache[key]
    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    if proc.returncode == 0:
        cache[key] = ("ok", combined)
        return cache[key]
    lower = combined.lower()
    if "modulenotfounderror" in lower or any(marker in lower for marker in _OPTIONAL_BINARY_MARKERS):
        cache[key] = ("skip", combined)
        return cache[key]
    cache[key] = ("fail", combined)
    return cache[key]


def _detect_subcommand(rest: str, top_help: str) -> str | None:
    tokens = rest.strip().split()
    if not tokens:
        return None
    first = tokens[0]
    if not re.fullmatch(r"[a-z][a-z0-9_-]*", first):
        return None
    if re.search(r"\{[^}]*\b" + re.escape(first) + r"\b[^}]*\}", top_help):
        return first
    return None


def _flag_in_help(flag: str, help_text: str) -> bool:
    return bool(re.search(r"(?<![A-Za-z0-9_-])" + re.escape(flag) + r"(?![A-Za-z0-9_-])", help_text))


def _check_command_flags(
    *,
    root: Path,
    python_exe: str,
    base_args: list[str],
    display_cmd: str,
    rest: str,
    rel_file: str,
    lineno: int,
    allowlist: set[tuple[str | None, str]],
    help_cache: dict[tuple[str, ...], tuple[str, str]],
    issues: list[DocIssue],
) -> None:
    flags = _FLAG_RE.findall(rest)
    if not flags:
        return
    status, out = _run_help(root, python_exe, base_args, help_cache)
    if status == "skip":
        return
    if status == "fail":
        if not _is_allowlisted(allowlist, rel_file, display_cmd):
            issues.append(DocIssue(rel_file, lineno, display_cmd, "--help failed"))
        return
    subcmd = _detect_subcommand(rest, out)
    if subcmd:
        sub_status, sub_out = _run_help(root, python_exe, [*base_args, subcmd], help_cache)
        if sub_status == "skip":
            return
        if sub_status == "ok":
            out = sub_out
    for flag in flags:
        ref = f"{display_cmd} {flag}"
        if _is_allowlisted(allowlist, rel_file, ref) or _is_allowlisted(allowlist, rel_file, flag):
            continue
        if not _flag_in_help(flag, out):
            issues.append(DocIssue(rel_file, lineno, ref, f"unknown CLI flag {flag}"))


def check_doc_files(
    root: Path,
    files: list[Path] | None = None,
    python_exe: str | None = None,
) -> list[DocIssue]:
    """Scan documentation files under `root` and return all broken references."""
    root = root.resolve()
    py = python_exe or sys.executable
    allowlist = load_allowlist(root)
    doc_files = files if files is not None else discover_doc_files(root)
    packages = _collect_npm_scripts(root)
    all_npm_scripts = set(GENERATED_WORKSPACE_SCRIPTS)
    for sc in packages.values():
        all_npm_scripts.update(sc)
    skills_dir = root / ".claude" / "skills"
    known_skills = {p.parent.name for p in skills_dir.glob("*/SKILL.md")} if skills_dir.is_dir() else set()
    help_cache: dict[tuple[str, ...], tuple[str, str]] = {}
    issues: list[DocIssue] = []

    for doc_rel in doc_files:
        doc_path = root / doc_rel
        if not doc_path.is_file():
            continue
        rel_str = doc_rel.as_posix()
        lines = doc_path.read_text(encoding="utf-8").splitlines()
        in_fence = False
        idx = 0
        while idx < len(lines):
            raw_line = lines[idx]
            lineno = idx + 1
            if raw_line.strip().startswith("```"):
                in_fence = not in_fence
                idx += 1
                continue
            joined = raw_line
            while in_fence and joined.rstrip().endswith("\\") and idx + 1 < len(lines):
                idx += 1
                joined = joined.rstrip()[:-1] + " " + lines[idx].strip()

            spans = [joined] if in_fence else [m.group(1) for m in re.finditer(r"`([^`\n]+)`", joined)]

            # (a) Backticked paths (outside fenced code blocks)
            if not in_fence:
                for token_raw in spans:
                    token = token_raw.strip()
                    if has_placeholder(token):
                        continue
                    if "[" in token and not (root / _strip_anchor_or_line(token)).exists():
                        continue
                    if not _looks_like_repo_path_token(token):
                        continue
                    if _is_allowlisted(allowlist, rel_str, token):
                        continue
                    if _BARE_SCRIPT_RE.fullmatch(token):
                        if not _find_bare_script_in_repo(root, token):
                            issues.append(DocIssue(rel_str, lineno, token, "referenced script does not exist"))
                        continue
                    if not _resolve_repo_path(root, doc_rel, token):
                        issues.append(DocIssue(rel_str, lineno, token, "referenced path does not exist"))

            # (b) & (c) python -m <module> + flags, and python <script.py> + flags
            for text in spans:
                for m in _PY_MOD_CMD_RE.finditer(text):
                    mod, rest = m.group(1), m.group(2)
                    if mod in BUILTIN_PYTHON_MODULES or has_placeholder(mod):
                        continue
                    if _is_allowlisted(allowlist, rel_str, mod):
                        continue
                    mod_rel = Path(*mod.split("."))
                    exists = (root / mod_rel.with_suffix(".py")).is_file() or (root / mod_rel / "__main__.py").is_file()
                    if not exists:
                        issues.append(DocIssue(rel_str, lineno, f"python -m {mod}", "python module does not exist"))
                        continue
                    _check_command_flags(
                        root=root,
                        python_exe=py,
                        base_args=["-m", mod],
                        display_cmd=f"python -m {mod}",
                        rest=rest,
                        rel_file=rel_str,
                        lineno=lineno,
                        allowlist=allowlist,
                        help_cache=help_cache,
                        issues=issues,
                    )

                for m in _PY_FILE_CMD_RE.finditer(text):
                    script_rel, rest = m.group(1), m.group(2)
                    if has_placeholder(script_rel) or is_runtime_path(script_rel):
                        continue
                    if _is_allowlisted(allowlist, rel_str, script_rel):
                        continue
                    if not (root / script_rel).is_file():
                        issues.append(DocIssue(rel_str, lineno, script_rel, "python script does not exist"))
                        continue
                    _check_command_flags(
                        root=root,
                        python_exe=py,
                        base_args=[script_rel],
                        display_cmd=f"python {script_rel}",
                        rest=rest,
                        rel_file=rel_str,
                        lineno=lineno,
                        allowlist=allowlist,
                        help_cache=help_cache,
                        issues=issues,
                    )

            # (d) npm run <script>
            for text in spans:
                for m in _NPM_RUN_RE.finditer(text):
                    script_name = m.group(1)
                    if has_placeholder(script_name):
                        continue
                    if _is_allowlisted(allowlist, rel_str, f"npm run {script_name}"):
                        continue
                    scoped = _matching_npm_scopes(joined, doc_rel, packages)
                    allowed = scoped if scoped is not None else all_npm_scripts
                    # Generated drill workspaces define test:qNN / check:mN
                    if script_name not in allowed:
                        if scoped is None and re.fullmatch(r"(?:test|check):q\d+", script_name):
                            continue
                        issues.append(
                            DocIssue(rel_str, lineno, f"npm run {script_name}", "npm script missing in package.json")
                        )

            # (e) skill references (outside fenced code blocks)
            if not in_fence:
                for m in _SKILL_REF_RE.finditer(joined):
                    skill = m.group(1) or m.group(2) or m.group(3)
                    if not skill or has_placeholder(skill):
                        continue
                    if _is_allowlisted(allowlist, rel_str, skill):
                        continue
                    if skill not in known_skills:
                        issues.append(DocIssue(rel_str, lineno, skill, "skill missing from .claude/skills/"))

            idx += 1

    # Validate docs/doc_map.json targets if present
    doc_map_path = root / "docs" / "doc_map.json"
    if doc_map_path.is_file():
        try:
            doc_map = json.loads(doc_map_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            issues.append(DocIssue("docs/doc_map.json", 1, "docs/doc_map.json", f"invalid JSON: {exc}"))
        else:
            if isinstance(doc_map, dict):
                for idx_line, target_list in enumerate(doc_map.values(), 1):
                    if not isinstance(target_list, list):
                        continue
                    for target in target_list:
                        if not isinstance(target, str):
                            continue
                        if _is_allowlisted(allowlist, "docs/doc_map.json", target):
                            continue
                        if not (root / target).exists():
                            issues.append(
                                DocIssue("docs/doc_map.json", idx_line, target, "mapped doc path does not exist")
                            )

    return issues


def glob_match(path: str, pattern: str) -> bool:
    """Match a POSIX relative path against a glob pattern supporting `**`."""
    norm_path = path.lstrip("./")
    norm_pat = pattern.lstrip("./")
    if "**" not in norm_pat:
        return fnmatch.fnmatchcase(norm_path, norm_pat)
    # Translate glob to regex so `**` matches zero or more path segments cleanly on Python <3.13
    parts: list[str] = ["^"]
    i = 0
    n = len(norm_pat)
    while i < n:
        if norm_pat[i : i + 2] == "**":
            if i + 2 < n and norm_pat[i + 2] == "/":
                parts.append("(?:.*/)?")
                i += 3
            else:
                parts.append(".*")
                i += 2
        elif norm_pat[i] == "*":
            parts.append("[^/]*")
            i += 1
        elif norm_pat[i] == "?":
            parts.append("[^/]")
            i += 1
        else:
            parts.append(re.escape(norm_pat[i]))
            i += 1
    parts.append("$")
    return bool(re.match("".join(parts), norm_path))


def _git_changed_files(root: Path, base_ref: str) -> list[str]:
    for sep in ("...", ".."):
        proc = subprocess.run(
            ["git", "diff", "--name-only", f"{base_ref}{sep}HEAD"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=15,
        )
        if proc.returncode == 0:
            return [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    raise RuntimeError(f"git diff against {base_ref!r} failed: {proc.stderr.strip()}")


def has_docs_updated_ack(pr_body: str) -> bool:
    """Return True if PR body contains a non-empty `Docs updated:` line outside HTML comments."""
    if not pr_body:
        return False
    stripped = _HTML_COMMENT_RE.sub("", pr_body)
    return bool(_DOCS_UPDATED_LINE_RE.search(stripped))


def check_changed_docs(
    root: Path,
    base_ref: str,
    pr_body: str = "",
    changed_files: list[str] | None = None,
) -> dict[str, Any]:
    """Check whether changed files require doc updates or a `Docs updated:` PR acknowledgement."""
    root = root.resolve()
    doc_map_path = root / "docs" / "doc_map.json"
    if not doc_map_path.is_file():
        return {
            "ok": True,
            "changed_files": [],
            "mapped_docs": [],
            "updated_docs": [],
            "has_pr_body_ack": False,
            "reason": "docs/doc_map.json not found",
        }
    doc_map: dict[str, list[str]] = json.loads(doc_map_path.read_text(encoding="utf-8"))
    changed = changed_files if changed_files is not None else _git_changed_files(root, base_ref)
    changed_set = set(changed)

    mapped_docs: list[str] = []
    seen_docs: set[str] = set()
    for path in changed:
        for pattern, targets in doc_map.items():
            if glob_match(path, pattern):
                for doc in targets:
                    if doc not in seen_docs:
                        seen_docs.add(doc)
                        mapped_docs.append(doc)

    updated_docs = [doc for doc in mapped_docs if doc in changed_set]
    ack = has_docs_updated_ack(pr_body)
    ok = (not mapped_docs) or bool(updated_docs) or ack
    return {
        "ok": ok,
        "changed_files": changed,
        "mapped_docs": mapped_docs,
        "updated_docs": updated_docs,
        "has_pr_body_ack": ack,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true", help="emit JSON output")
    ap.add_argument(
        "--changed", metavar="BASE_REF", help="check docs/doc_map.json against files changed since BASE_REF"
    )
    ap.add_argument("--root", type=Path, default=None, help="repository root (defaults to auto-detected repo root)")
    args = ap.parse_args(argv)

    root = (args.root or default_repo_root()).resolve()

    if args.changed:
        pr_body = os.environ.get("PR_BODY", "")
        result = check_changed_docs(root, args.changed, pr_body=pr_body)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if not result["mapped_docs"]:
                print("doc-map: no mapped docs affected by changed files.")
            else:
                print("doc-map: mapped docs for changed files:")
                for doc in result["mapped_docs"]:
                    mark = "[updated]" if doc in result["updated_docs"] else "[missing]"
                    print(f"  {mark} {doc}")
                if not result["ok"]:
                    print(
                        "ERROR: mapped docs changed in code, none of those docs were updated, "
                        'and PR_BODY lacks a "Docs updated:" line.',
                        file=sys.stderr,
                    )
        return 0 if result["ok"] else 1

    issues = check_doc_files(root)
    if args.json:
        print(json.dumps({"ok": not issues, "count": len(issues), "issues": [i.to_dict() for i in issues]}, indent=2))
    else:
        for issue in issues:
            print(issue.format_line())
        print(f"\n{len(issues)} broken reference(s) found")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
