# -*- coding: utf-8 -*-
"""Source-core card schema validation, storage, and local sources directory resolution.

Raw study materials live under ``sources/`` in the main checkout (gitignored; override with
``LEARNINGOS_SOURCES_DIR``). Core cards are stored as JSONL in ``sources/_cores/<UNIT>.jsonl``
and hold only abstract, source-free problem structures — never source wording, numbers,
code snippets, identifiers, test names, or strings.

Supports both Math core cards (``schema.json``) and PRG core cards (``prg_schema.json``).
"""

from __future__ import annotations

import json
import os
import re
import warnings
from typing import Any, Iterable

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(PACKAGE_DIR))
ID_MAP_PATH = os.path.join(REPO_ROOT, "id_map.json")
DOCS_SOURCES_PATH = os.path.join(REPO_ROOT, "docs", "sources.md")
SCHEMA_PATH = os.path.join(PACKAGE_DIR, "schema.json")
PRG_SCHEMA_PATH = os.path.join(PACKAGE_DIR, "prg_schema.json")
UNIT_TERMS_PATH = os.path.join(PACKAGE_DIR, "unit_terms.json")

MAX_FIELD_LENGTH = 200
WORD_SHINGLE_SIZE = 6
UNMAPPED_PREFIX = "UNMAPPED:"
_UNIT_OR_CHAPTER_RE = re.compile(r"^(?:MTH|PHY|PRG)-T\d+-C\d+(?:-U\d+)?$")
_VALID_CODES_CACHE: dict[tuple[str, float], dict[str, str]] = {}
_REGISTRY_FAMILIES_CACHE: dict[tuple[str, float], dict[str, dict[str, Any]]] = {}

ALLOWED_USE_MODES: tuple[str, ...] = ("scope", "cores", "reuse", "no-automation")

REASONING_MOVES: tuple[str, ...] = (
    "direct",
    "chain",
    "reverse",
    "translate",
    "diagnose",
    "multi-relation",
    "case-check",
    "generalise",
    "model",
)
FORMAT_KINDS: tuple[str, ...] = ("choice", "numeric", "expression", "proof-lite")
REPRESENTATIONS: tuple[str, ...] = ("symbolic", "graph/plane", "table", "verbal")

PRG_LANGUAGES: tuple[str, ...] = (
    "javascript",
    "typescript",
    "python",
    "sql",
    "html-css",
    "shell",
    "agnostic",
)
PRG_ARCHETYPE_KINDS: tuple[str, ...] = (
    "implement",
    "predict-output",
    "find-the-bug",
    "refactor",
    "project-milestone",
)
QC_ID_RE = re.compile(r"^QC-[a-z0-9][a-z0-9-]*$")

SOURCE_FAMILIES: dict[str, dict[str, Any]] = {
    "openstax": {
        "mode": "scope",
        "priority": 0,
        "thaiExam": False,
        "label": "OpenStax textbooks (TOC & learning objectives only)",
    },
    "smartmathpro": {
        "mode": "cores",
        "priority": 100,
        "thaiExam": True,
        "label": "SmartMathPro Thai past papers",
    },
    "thai-exams": {
        "mode": "cores",
        "priority": 95,
        "thaiExam": True,
        "label": "Thai O-NET & TCAS A-Level exams",
    },
    "illustrative-math": {
        "mode": "cores",
        "priority": 70,
        "thaiExam": False,
        "label": "Illustrative Mathematics",
    },
    "mathsgenie": {
        "mode": "cores",
        "priority": 50,
        "thaiExam": False,
        "label": "MathsGenie GCSE worksheets & exam questions",
    },
    # Registered PRG source families under sources/prg/<family>/
    "prg/exercism-typescript": {
        "mode": "reuse",
        "priority": 95,
        "thaiExam": False,
        "license": "MIT",
        "label": "Exercism TypeScript track",
    },
    "prg/exercism-javascript": {
        "mode": "reuse",
        "priority": 92,
        "thaiExam": False,
        "license": "MIT",
        "label": "Exercism JavaScript track",
    },
    "prg/typescript-exercises": {
        "mode": "reuse",
        "priority": 90,
        "thaiExam": False,
        "license": "MIT",
        "label": "TypeScript Exercises (narrowing, unions, generics)",
    },
    "prg/eslint": {
        "mode": "reuse",
        "priority": 85,
        "thaiExam": False,
        "license": "MIT",
        "label": "ESLint rule docs (incorrect/correct pairs)",
    },
    "prg/javascript-questions": {
        "mode": "reuse",
        "priority": 82,
        "thaiExam": False,
        "license": "MIT",
        "label": "Lydia Hallie JavaScript Questions (predict-output)",
    },
    "prg/javascript-koans": {
        "mode": "reuse",
        "priority": 75,
        "thaiExam": False,
        "license": "MIT",
        "label": "JavaScript Koans",
    },
    "prg/wtfjs": {
        "mode": "reuse",
        "priority": 70,
        "thaiExam": False,
        "license": "WTFPL",
        "label": "wtfjs coercion and runtime edge cases",
    },
}

DEFAULT_FAMILY_PRIORITY = 50

_REQUIRED_TOP_KEYS: tuple[str, ...] = (
    "id",
    "unitCode",
    "sourceRef",
    "skill",
    "reasoningMove",
    "difficultyDriver",
    "level",
    "traps",
    "format",
    "representation",
)
_ALLOWED_TOP_KEYS: frozenset[str] = frozenset((*_REQUIRED_TOP_KEYS, "laterUnit", "notes", "units", "operations"))

_PRG_REQUIRED_TOP_KEYS: tuple[str, ...] = (
    "id",
    "unitCode",
    "sourceRef",
    "language",
    "archetypeKind",
    "skill",
    "concept",
    "bugPattern",
    "testsCatch",
    "difficultyDriver",
    "level",
    "traps",
    "qualityCheckIdeas",
)
_PRG_ALLOWED_TOP_KEYS: frozenset[str] = frozenset(
    (*_PRG_REQUIRED_TOP_KEYS, "profile", "smell", "laterUnit", "units", "notes", "reuse")
)
_PRG_HINT_KEYS: frozenset[str] = frozenset(
    ("language", "archetypeKind", "concept", "bugPattern", "smell", "testsCatch", "qualityCheckIdeas", "reuse")
)

_ALLOWED_SOURCE_REF_KEYS: frozenset[str] = frozenset(("family", "file", "page", "item"))
_ALLOWED_TRAP_KEYS: frozenset[str] = frozenset(("tag", "description"))
_ALLOWED_FORMAT_KEYS: frozenset[str] = frozenset(("kind", "optionCount", "distractorPatterns"))
_ALLOWED_QC_IDEA_KEYS: frozenset[str] = frozenset(("id", "check", "severity"))
_ALLOWED_REUSE_KEYS: frozenset[str] = frozenset(("license", "attribution", "adaptedIdea"))

_DIGIT_RUN_RE = re.compile(r"(?<![A-Za-z0-9_])\d+(?:\.\d+)?")
_WORD_TOKEN_RE = re.compile(r"[a-z0-9]+|[\u0e00-\u0e7f]+")
_TABLE_FAMILY_RE = re.compile(r"^\|\s*`([^`]+)`")

# Patterns for PRG no-copy enforcement
_CODE_SYNTAX_RE = re.compile(
    r"```|"
    r"\b(?:export\s+)?(?:async\s+)?function\s+[A-Za-z_$]\w*\s*\(|"
    r"\b(?:const|let|var)\s+[A-Za-z_$]\w*\s*=\s*[^=]|\bdef\s+[A-Za-z_]\w*\s*\(|"
    r"=>\s*\{|"
    r"\b(?:expect|assert\.\w+)\s*\(|"
    r"\bimport\s+[\w{*\s,]+\s+from\s+['\"]"
)
_DECLARED_IDENT_RE = re.compile(
    r"\b(?:function|class|const|let|var|interface|type|enum|def)\s+([A-Za-z_$][A-Za-z0-9_$]*)"
)
_TEST_NAME_RE = re.compile(r"\b(?:describe|it|test|xit|xtest|fit|suite)\s*\(\s*(['\"`])([^'\"`\n]{4,180})\1")
_STRING_LITERAL_RE = re.compile(r"(['\"`])([^'\"`\n\\]{6,180})\1")
_CAMEL_BOUNDARY_RE = re.compile(r"[a-z][A-Z]")

_GENERIC_CODE_IDENTIFIERS: frozenset[str] = frozenset(
    {
        # JS/TS/Py standard built-ins & testing helpers
        "array",
        "object",
        "string",
        "number",
        "boolean",
        "symbol",
        "bigint",
        "promise",
        "error",
        "typeerror",
        "rangeerror",
        "syntaxerror",
        "referenceerror",
        "regexp",
        "date",
        "math",
        "json",
        "map",
        "set",
        "weakmap",
        "weakset",
        "console",
        "window",
        "document",
        "global",
        "process",
        "buffer",
        "abortcontroller",
        "abortsignal",
        "settimeout",
        "cleartimeout",
        "setinterval",
        "clearinterval",
        "addeventlistener",
        "removeeventlistener",
        "usestate",
        "useeffect",
        "usecallback",
        "usememo",
        "useref",
        "usecontext",
        "usereducer",
        "toequal",
        "tobe",
        "tothrow",
        "tostrictequal",
        "tohavebeencalled",
        "describe",
        "expect",
        "assert",
        "strict",
        "equal",
        "deepequal",
        # Generic CS/programming words that legitimately describe abstract concepts
        "value",
        "values",
        "result",
        "results",
        "input",
        "inputs",
        "output",
        "outputs",
        "index",
        "items",
        "item",
        "count",
        "counter",
        "total",
        "state",
        "data",
        "config",
        "options",
        "option",
        "params",
        "param",
        "args",
        "callback",
        "handler",
        "listener",
        "factory",
        "helper",
        "runner",
        "worker",
        "queue",
        "stack",
        "cache",
        "store",
        "node",
        "nodes",
        "tree",
        "graph",
        "edge",
        "edges",
        "path",
        "route",
        "router",
        "client",
        "server",
        "request",
        "response",
        "query",
        "schema",
        "model",
        "record",
        "entry",
        "entries",
        "field",
        "fields",
        "label",
        "title",
        "status",
        "level",
        "scope",
        "closure",
        "async",
        "await",
        "timer",
        "clock",
        "delay",
        "timeout",
        "retry",
        "limit",
        "token",
        "tokens",
        "cookie",
        "session",
        "header",
        "headers",
        "payload",
        "target",
        "source",
        "default",
        "fallback",
        "initial",
        "current",
        "previous",
        "next",
        "first",
        "last",
        "start",
        "check",
        "parse",
        "format",
        "filter",
        "reduce",
        "sort",
        "search",
        "match",
        "merge",
        "clone",
        "copy",
        "create",
        "update",
        "delete",
        "remove",
        "insert",
        "append",
        "fetch",
        "render",
        "submit",
        "reset",
        "clear",
        "close",
        "open",
        "read",
        "write",
        "load",
        "save",
        "valid",
        "invalid",
        "empty",
        "length",
        "size",
        "name",
        "names",
        "type",
        "types",
        "kind",
        "list",
        "arraybuffer",
        "undefined",
        "nullish",
        "falsy",
        "truthy",
    }
)

_TRIVIAL_STRING_LITERALS: frozenset[str] = frozenset(
    {
        "utf-8",
        "utf8",
        "string",
        "number",
        "boolean",
        "object",
        "function",
        "undefined",
        "symbol",
        "bigint",
        "node:test",
        "node:assert",
        "node:assert/strict",
        "use strict",
        "use client",
        "application/json",
        "text/plain",
        "text/html",
        "localhost",
    }
)


class CoreCardError(ValueError):
    """Raised when a source core card violates schema or source-free invariants."""


def is_prg_unit(unit_code: str) -> bool:
    """Return True if ``unit_code`` belongs to the PRG track."""
    return str(unit_code or "").strip().upper().startswith("PRG")


def is_prg_card(card: Any) -> bool:
    """Return True if ``card`` uses the PRG core-card profile."""
    if not isinstance(card, dict):
        return False
    if card.get("profile") == "prg":
        return True
    if is_prg_unit(str(card.get("unitCode") or "")):
        return True
    if any(k in card for k in _PRG_HINT_KEYS) and "reasoningMove" not in card:
        return True
    return False


def main_checkout_root(cwd: str = ".") -> str:
    """Return the main checkout root, resolving git worktrees via their ``.git`` file."""
    root = os.path.abspath(cwd)
    git_path = os.path.join(root, ".git")
    if os.path.isfile(git_path):
        try:
            with open(git_path, "r", encoding="utf-8") as fh:
                text = fh.read().strip()
        except OSError:
            return root
        if text.startswith("gitdir:"):
            gitdir = os.path.abspath(os.path.join(root, text.split(":", 1)[1].strip()))
            worktrees_dir = os.path.dirname(gitdir)
            if os.path.basename(worktrees_dir) == "worktrees":
                return os.path.dirname(os.path.dirname(worktrees_dir))
    return root


def resolve_sources_dir(cwd: str = ".", sources_dir: str | None = None) -> str:
    """Resolve the local ``sources/`` directory.

    Priority: explicit ``sources_dir`` > ``LEARNINGOS_SOURCES_DIR`` env var > ``<main checkout>/sources``.
    """
    if sources_dir:
        return os.path.abspath(sources_dir)
    env_dir = os.environ.get("LEARNINGOS_SOURCES_DIR")
    if env_dir and env_dir.strip():
        return os.path.abspath(env_dir.strip())
    return os.path.join(main_checkout_root(cwd), "sources")


def cores_path(unit_code: str, sources_dir: str | None = None) -> str:
    """Return ``<sources_dir>/_cores/<unit_code>.jsonl``."""
    return os.path.join(resolve_sources_dir(sources_dir=sources_dir), "_cores", f"{unit_code}.jsonl")


def index_dir(sources_dir: str | None = None) -> str:
    """Return ``<sources_dir>/_index``."""
    return os.path.join(resolve_sources_dir(sources_dir=sources_dir), "_index")


def _clean_registry_prefix(raw_token: str) -> str:
    """Strip wildcard/placeholder segments from a ``docs/sources.md`` family path."""
    parts = [p for p in raw_token.replace("\\", "/").strip("/").split("/") if p]
    cleaned: list[str] = []
    for part in parts:
        if any(ch in part for ch in ("*", "<", ">", "{", "}", "…", "...")):
            break
        if part.lower().startswith("grade_") and part[6:].upper() == "N":
            break
        cleaned.append(part.lower())
    return "/".join(cleaned)


def normalize_allowed_use(raw: str) -> str | None:
    """Normalize an ``Allowed use`` cell from ``docs/sources.md`` to a canonical mode."""
    cleaned = raw.strip("` *").strip().lower().replace("_", "-").replace(" ", "-")
    if cleaned in ("scope", "scope-only"):
        return "scope"
    if cleaned == "cores":
        return "cores"
    if cleaned == "reuse":
        return "reuse"
    if cleaned in ("no-automation", "noautomation"):
        return "no-automation"
    return None


def load_registry_families(registry_path: str | None = None) -> dict[str, dict[str, Any]]:
    """Parse registered families, allowed-use modes, licences, and priorities from ``docs/sources.md``.

    Recognises both the top-level ``sources/`` table and the ``## PRG Source Families (under sources/prg/)``
    section (prefixing PRG family keys with ``prg/``).
    """
    target = os.path.abspath(registry_path or DOCS_SOURCES_PATH)
    if not os.path.isfile(target):
        return {}
    mtime = os.path.getmtime(target)
    cache_key = (target, mtime)
    cached = _REGISTRY_FAMILIES_CACHE.get(cache_key)
    if cached is not None:
        return {k: dict(v) for k, v in cached.items()}

    entries: dict[str, dict[str, Any]] = {}
    in_prg_section = False
    col_map: dict[str, int] = {}

    with open(target, "r", encoding="utf-8") as fh:
        for line in fh:
            stripped = line.strip()
            if stripped.startswith("#"):
                low_h = stripped.lower()
                in_prg_section = "sources/prg" in low_h or "prg source" in low_h
                col_map = {}
                continue
            if not stripped.startswith("|"):
                col_map = {}
                continue
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if not cells:
                continue
            if all(re.fullmatch(r":?-{2,}:?", c.replace(" ", "")) for c in cells if c):
                continue
            lower_cells = [c.lower() for c in cells]
            if any("allowed use" in c for c in lower_cells) or any(c.startswith("family") for c in lower_cells):
                col_map = {}
                for idx, val in enumerate(lower_cells):
                    if val.startswith("family"):
                        col_map["family"] = idx
                    elif "allowed use" in val:
                        col_map["mode"] = idx
                    elif val == "priority" or val.startswith("priority "):
                        col_map["priority"] = idx
                    elif "licence" in val or "license" in val:
                        col_map["license"] = idx
                    elif "upstream" in val:
                        col_map["upstream"] = idx
                continue
            m = _TABLE_FAMILY_RE.match(stripped)
            if not m:
                continue
            prefix = _clean_registry_prefix(m.group(1))
            if not prefix:
                continue
            if in_prg_section and not prefix.startswith("prg/"):
                prefix = f"prg/{prefix}"

            meta: dict[str, Any] = {}
            if "mode" in col_map and col_map["mode"] < len(cells):
                mode = normalize_allowed_use(cells[col_map["mode"]])
                if mode:
                    meta["mode"] = mode
            if "priority" in col_map and col_map["priority"] < len(cells):
                raw_prio = cells[col_map["priority"]].strip("` ").strip()
                if re.fullmatch(r"\d+", raw_prio):
                    meta["priority"] = int(raw_prio)
            if "license" in col_map and col_map["license"] < len(cells):
                lic = cells[col_map["license"]].strip("` ").strip()
                if lic:
                    meta["license"] = lic
            if "upstream" in col_map and col_map["upstream"] < len(cells):
                up = cells[col_map["upstream"]].strip("` ").strip()
                if up:
                    meta["upstream"] = up

            entries[prefix] = meta
            if not prefix.startswith("prg/"):
                top = prefix.split("/", 1)[0]
                if top not in entries:
                    entries[top] = dict(meta)
                elif "priority" in meta:
                    prev_p = entries[top].get("priority", -1)
                    if isinstance(prev_p, int) and meta["priority"] > prev_p:
                        entries[top]["priority"] = meta["priority"]

    _REGISTRY_FAMILIES_CACHE[cache_key] = entries
    return {k: dict(v) for k, v in entries.items()}


def family_root(family_or_relpath: str) -> str:
    """Return the canonical family key (lowercased POSIX).

    For ``prg/<family>/...`` paths returns ``prg/<family>``; for other paths returns the
    top-level directory name.
    """
    norm = family_or_relpath.replace("\\", "/").strip("/")
    if not norm:
        return ""
    parts = norm.split("/")
    first = parts[0].lower()
    if first == "prg" and len(parts) >= 2 and parts[1]:
        return f"prg/{parts[1].lower()}"
    return first


def _lookup_registry_entry(
    family_or_relpath: str,
    registry_path: str | None = None,
) -> dict[str, Any] | None:
    reg = load_registry_families(registry_path=registry_path)
    if not reg:
        return None
    norm = family_or_relpath.replace("\\", "/").split("::", 1)[0].strip("/").lower()
    if not norm:
        return None
    parts = [p for p in norm.split("/") if p]
    for depth in range(len(parts), 0, -1):
        cand = "/".join(parts[:depth])
        if cand in reg:
            return reg[cand]
    if not norm.startswith("prg/"):
        prg_cand = f"prg/{parts[0]}"
        if prg_cand in reg:
            return reg[prg_cand]
    return None


def family_mode(family_or_relpath: str, registry_path: str | None = None) -> str:
    """Return the allowed-use mode (``'scope'``, ``'cores'``, ``'reuse'``, or ``'no-automation'``)."""
    reg_entry = _lookup_registry_entry(family_or_relpath, registry_path=registry_path)
    if reg_entry and isinstance(reg_entry.get("mode"), str):
        return str(reg_entry["mode"])
    root = family_root(family_or_relpath)
    meta = SOURCE_FAMILIES.get(root) or (SOURCE_FAMILIES.get(f"prg/{root}") if not root.startswith("prg/") else None)
    if meta:
        return str(meta["mode"])
    return "scope" if root.startswith("openstax") else "cores"


def family_license(family_or_relpath: str, registry_path: str | None = None) -> str | None:
    """Return the registered licence string for ``family_or_relpath``, if known."""
    reg_entry = _lookup_registry_entry(family_or_relpath, registry_path=registry_path)
    if reg_entry and isinstance(reg_entry.get("license"), str):
        return str(reg_entry["license"])
    root = family_root(family_or_relpath)
    meta = SOURCE_FAMILIES.get(root) or (SOURCE_FAMILIES.get(f"prg/{root}") if not root.startswith("prg/") else None)
    if meta and isinstance(meta.get("license"), str):
        return str(meta["license"])
    return None


def family_priority(family_or_relpath: str, registry_path: str | None = None) -> int:
    """Return the default numeric priority for ``family_or_relpath`` (0 for scope / no-automation)."""
    mode = family_mode(family_or_relpath, registry_path=registry_path)
    if mode in ("scope", "no-automation"):
        return 0
    reg_entry = _lookup_registry_entry(family_or_relpath, registry_path=registry_path)
    if reg_entry and isinstance(reg_entry.get("priority"), int):
        return int(reg_entry["priority"])
    root = family_root(family_or_relpath)
    meta = SOURCE_FAMILIES.get(root) or (SOURCE_FAMILIES.get(f"prg/{root}") if not root.startswith("prg/") else None)
    if meta and isinstance(meta.get("priority"), int):
        return int(meta["priority"])
    return DEFAULT_FAMILY_PRIORITY


def is_thai_exam_family(family_or_relpath: str) -> bool:
    """Return True if ``family_or_relpath`` belongs to a Thai-exam-aligned source family."""
    root = family_root(family_or_relpath)
    meta = SOURCE_FAMILIES.get(root)
    if meta is not None:
        return bool(meta.get("thaiExam"))
    low = family_or_relpath.replace("\\", "/").lower()
    return any(tok in low for tok in ("smartmathpro", "thai-exam", "tcas", "a-level", "onet", "o-net", "pat1", "pat 1"))


def load_schema(profile: str = "math") -> dict[str, Any]:
    """Load the core-card JSON Schema (``profile='math'`` or ``profile='prg'``)."""
    target = PRG_SCHEMA_PATH if str(profile).lower() == "prg" else SCHEMA_PATH
    with open(target, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_prg_schema() -> dict[str, Any]:
    """Load the PRG core-card JSON Schema from ``math_engine/source_cores/prg_schema.json``."""
    return load_schema("prg")


def load_unit_terms_map(path: str | None = None) -> dict[str, dict[str, Any]]:
    """Load the per-unit search-terms map from ``unit_terms.json``."""
    target = path or UNIT_TERMS_PATH
    with open(target, "r", encoding="utf-8") as fh:
        return json.load(fh)


def get_unit_terms(unit_code: str, path: str | None = None) -> list[str]:
    """Return seeded search terms for ``unit_code`` (or merged child units for a chapter code)."""
    data = load_unit_terms_map(path=path)
    if unit_code in data:
        return list(data[unit_code].get("terms") or [])
    merged: list[str] = []
    prefix = f"{unit_code}-U"
    for code, entry in sorted(data.items()):
        if code.startswith(prefix):
            for term in entry.get("terms") or []:
                if term not in merged:
                    merged.append(term)
    return merged


_OP_STOPWORDS: frozenset[str] = frozenset(
    {
        "the",
        "a",
        "an",
        "by",
        "of",
        "via",
        "to",
        "in",
        "on",
        "for",
        "with",
        "from",
        "into",
        "using",
        "and",
        "or",
    }
)

_OP_TOKEN_ALIASES: dict[str, str] = {
    "multiplication": "multiply",
    "multiplying": "multiply",
    "multiplied": "multiply",
    "product": "multiply",
    "products": "multiply",
    "division": "divide",
    "dividing": "divide",
    "divided": "divide",
    "quotient": "divide",
    "quotients": "divide",
    "addition": "add",
    "adding": "add",
    "added": "add",
    "subtraction": "subtract",
    "subtracting": "subtract",
    "subtracted": "subtract",
    "expanding": "expand",
    "expansion": "expand",
    "expanded": "expand",
    "simplifying": "simplify",
    "simplification": "simplify",
    "simplified": "simplify",
    "factoring": "factor",
    "factorization": "factor",
    "factorisation": "factor",
    "factorize": "factor",
    "factorise": "factor",
    "factored": "factor",
    "squaring": "square",
    "squared": "square",
    "conjugation": "conjugate",
    "conjugating": "conjugate",
    "conjugated": "conjugate",
    "rationalization": "rationalize",
    "rationalisation": "rationalize",
    "rationalizing": "rationalize",
    "rationalising": "rationalize",
    "rationalized": "rationalize",
    "rationalised": "rationalize",
    "rationalise": "rationalize",
    "completing": "complete",
    "completed": "complete",
    "substituting": "substitute",
    "substitution": "substitute",
    "substituted": "substitute",
    "distributing": "distribute",
    "distribution": "distribute",
    "distributed": "distribute",
    "combining": "combine",
    "combination": "combine",
    "combined": "combine",
    "evaluating": "evaluate",
    "evaluation": "evaluate",
    "evaluated": "evaluate",
    "solving": "solve",
    "solved": "solve",
    "isolating": "isolate",
    "isolation": "isolate",
    "isolated": "isolate",
    "rearranging": "rearrange",
    "rearrangement": "rearrange",
    "rearranged": "rearrange",
    "reducing": "reduce",
    "reduction": "reduce",
    "reduced": "reduce",
    "cancelling": "cancel",
    "canceling": "cancel",
    "cancellation": "cancel",
    "cancelled": "cancel",
    "canceled": "cancel",
    "inverting": "invert",
    "inversion": "invert",
    "inverted": "invert",
    "converting": "convert",
    "conversion": "convert",
    "converted": "convert",
}


def _lemmatize_op_token(token: str) -> str:
    if token in _OP_TOKEN_ALIASES:
        return _OP_TOKEN_ALIASES[token]
    stem = token
    if len(stem) >= 5 and stem.endswith("ies"):
        stem = stem[:-3] + "y"
    elif len(stem) >= 4 and stem.endswith("s") and not stem.endswith(("ss", "us", "is")):
        stem = stem[:-1]
    elif len(stem) >= 6 and stem.endswith("ing"):
        stem = stem[:-3]
    elif len(stem) >= 5 and stem.endswith("ed"):
        stem = stem[:-2]
    return _OP_TOKEN_ALIASES.get(stem, stem)


def normalize_operation(op: str) -> str:
    """Normalize a math sub-skill operation name for exact equality and set comparison."""
    raw_tokens = re.findall(r"[a-z0-9]+", (op or "").lower())
    if not raw_tokens:
        return (op or "").strip().lower()
    kept = [_lemmatize_op_token(tok) for tok in raw_tokens if tok not in _OP_STOPWORDS]
    if not kept:
        kept = [_lemmatize_op_token(tok) for tok in raw_tokens]
    return " ".join(kept)


def _normalize_digit_run(token: str) -> str:
    if "." in token:
        whole, frac = token.split(".", 1)
        whole = whole.lstrip("0") or "0"
        frac = frac.rstrip("0")
        return f"{whole}.{frac}" if frac else whole
    return token.lstrip("0") or "0"


def extract_digit_runs(text: str) -> list[str]:
    """Extract normalized numeric digit runs from ``text`` (ignoring identifier suffixes like ``t02``)."""
    return [_normalize_digit_run(m.group(0)) for m in _DIGIT_RUN_RE.finditer(text or "")]


def _word_shingles(text: str, size: int = WORD_SHINGLE_SIZE) -> set[tuple[str, ...]]:
    tokens = _WORD_TOKEN_RE.findall((text or "").lower())
    if len(tokens) < size:
        return set()
    return {tuple(tokens[i : i + size]) for i in range(len(tokens) - size + 1)}


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _walk_strings(obj: Any, prefix: str = "") -> Iterable[tuple[str, str]]:
    if isinstance(obj, str):
        yield prefix, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else str(k)
            yield from _walk_strings(v, path)
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            yield from _walk_strings(item, f"{prefix}[{idx}]")


def _content_string_fields(card: dict[str, Any]) -> list[tuple[str, str]]:
    fields: list[tuple[str, str]] = []
    for key in ("skill", "difficultyDriver", "notes"):
        val = card.get(key)
        if isinstance(val, str):
            fields.append((key, val))
    if isinstance(card.get("operations"), list):
        for idx, op in enumerate(card["operations"]):
            if isinstance(op, str):
                fields.append((f"operations[{idx}]", op))
    for idx, trap in enumerate(card.get("traps") or []):
        if isinstance(trap, dict):
            for sub in ("tag", "description"):
                val = trap.get(sub)
                if isinstance(val, str):
                    fields.append((f"traps[{idx}].{sub}", val))
    fmt = card.get("format")
    if isinstance(fmt, dict):
        for idx, pat in enumerate(fmt.get("distractorPatterns") or []):
            if isinstance(pat, str):
                fields.append((f"format.distractorPatterns[{idx}]", pat))
    return fields


def _prg_content_string_fields(card: dict[str, Any]) -> list[tuple[str, str]]:
    fields: list[tuple[str, str]] = []
    for key in ("skill", "concept", "bugPattern", "smell", "testsCatch", "difficultyDriver", "notes"):
        val = card.get(key)
        if isinstance(val, str):
            fields.append((key, val))
    for idx, trap in enumerate(card.get("traps") or []):
        if isinstance(trap, dict):
            for sub in ("tag", "description"):
                val = trap.get(sub)
                if isinstance(val, str):
                    fields.append((f"traps[{idx}].{sub}", val))
    for idx, qc in enumerate(card.get("qualityCheckIdeas") or []):
        if isinstance(qc, dict):
            val = qc.get("check")
            if isinstance(val, str):
                fields.append((f"qualityCheckIdeas[{idx}].check", val))
    reuse = card.get("reuse")
    if isinstance(reuse, dict) and isinstance(reuse.get("adaptedIdea"), str):
        fields.append(("reuse.adaptedIdea", reuse["adaptedIdea"]))
    return fields


def _extract_distinctive_source_identifiers(source_text: str) -> set[str]:
    """Extract distinctive declared identifiers (functions, classes, consts, types) from source code."""
    found: set[str] = set()
    for m in _DECLARED_IDENT_RE.finditer(source_text or ""):
        ident = m.group(1)
        low = ident.lower()
        if len(ident) < 5 or low in _GENERIC_CODE_IDENTIFIERS:
            continue
        is_compound = bool(_CAMEL_BOUNDARY_RE.search(ident)) or ("_" in ident)
        if is_compound or len(ident) >= 7:
            found.add(ident)
    return found


def _extract_distinctive_source_strings(source_text: str) -> set[str]:
    """Extract distinctive test names and string literals from source code."""
    found: set[str] = set()
    for m in _TEST_NAME_RE.finditer(source_text or ""):
        val = m.group(2).strip()
        if len(val) >= 6 and val.lower() not in _TRIVIAL_STRING_LITERALS:
            found.add(val)
    for m in _STRING_LITERAL_RE.finditer(source_text or ""):
        val = m.group(2).strip()
        if len(val) < 6 or val.lower() in _TRIVIAL_STRING_LITERALS:
            continue
        # Ignore relative module import paths like './two-fer' or '../src/foo'
        if val.startswith(("./", "../", "/", "@")) and " " not in val:
            continue
        if " " in val or len(val) >= 8:
            found.add(val)
    return found


def load_valid_unit_codes(id_map_path: str | None = None) -> dict[str, str]:
    """Return ``{code: title}`` for every unit/chapter code registered in ``id_map.json``."""
    target = os.path.abspath(id_map_path or ID_MAP_PATH)
    if not os.path.isfile(target):
        return {}
    mtime = os.path.getmtime(target)
    cache_key = (target, mtime)
    cached = _VALID_CODES_CACHE.get(cache_key)
    if cached is not None:
        return dict(cached)
    with open(target, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    codes: dict[str, str] = {}
    if isinstance(raw, dict):
        for key, entry in raw.items():
            if not isinstance(key, str) or not _UNIT_OR_CHAPTER_RE.match(key):
                continue
            title = entry.get("title", "") if isinstance(entry, dict) else ""
            codes[key] = str(title or "")
    _VALID_CODES_CACHE[cache_key] = codes
    return dict(codes)


def _validate_shared_unit_refs(
    card: dict[str, Any],
    errors: list[str],
    valid_unit_codes: Iterable[str] | None,
) -> None:
    known_codes: set[str] | None = None

    def _get_known_codes() -> set[str]:
        nonlocal known_codes
        if known_codes is None:
            known_codes = (
                {str(c).strip() for c in valid_unit_codes if isinstance(c, str) and c.strip()}
                if valid_unit_codes is not None
                else set(load_valid_unit_codes())
            )
        return known_codes

    if "laterUnit" in card and card["laterUnit"] is not None:
        if not isinstance(card["laterUnit"], str) or not card["laterUnit"].strip():
            errors.append("laterUnit: must be a non-empty string or null.")
        else:
            later = card["laterUnit"].strip()
            if later.startswith(UNMAPPED_PREFIX):
                if not later[len(UNMAPPED_PREFIX) :].strip():
                    errors.append("laterUnit: 'UNMAPPED:' prefix must be followed by a non-empty label.")
            else:
                known = _get_known_codes()
                if known and later not in known:
                    warnings.warn(
                        f"Unknown laterUnit '{later}' is not in id_map.json unit/chapter codes.",
                        UserWarning,
                        stacklevel=3,
                    )
                    errors.append(
                        f"laterUnit: unknown unit/chapter code '{later}' (not in id_map.json; "
                        f"use a real unit/chapter code or prefix with '{UNMAPPED_PREFIX}')."
                    )

    if "units" in card:
        units = card["units"]
        if not isinstance(units, list) or len(units) < 2:
            errors.append("units: must be a list of at least 2 distinct unit codes.")
        else:
            seen_u: set[str] = set()
            for idx, u in enumerate(units):
                if not isinstance(u, str) or not u.strip():
                    errors.append(f"units[{idx}]: must be a non-empty string.")
                else:
                    cleaned = u.strip()
                    if cleaned in seen_u:
                        errors.append(f"units[{idx}]: duplicate unit code '{cleaned}'.")
                    seen_u.add(cleaned)
                    if cleaned.startswith(UNMAPPED_PREFIX):
                        if not cleaned[len(UNMAPPED_PREFIX) :].strip():
                            errors.append(f"units[{idx}]: 'UNMAPPED:' prefix must be followed by a non-empty label.")
                    else:
                        known = _get_known_codes()
                        if known and cleaned not in known:
                            warnings.warn(
                                f"Unknown units[{idx}] '{cleaned}' is not in id_map.json unit/chapter codes.",
                                UserWarning,
                                stacklevel=3,
                            )
                            errors.append(
                                f"units[{idx}]: unknown unit/chapter code '{cleaned}' (not in id_map.json; "
                                f"use a real unit/chapter code or prefix with '{UNMAPPED_PREFIX}')."
                            )


def _validate_source_ref(
    card: dict[str, Any],
    errors: list[str],
    registry_path: str | None = None,
) -> str | None:
    """Validate ``card['sourceRef']`` and return the resolved family mode (or None)."""
    if "sourceRef" not in card:
        return None
    ref = card["sourceRef"]
    if not isinstance(ref, dict):
        errors.append("sourceRef: must be an object.")
        return None
    unknown_ref = sorted(set(ref) - _ALLOWED_SOURCE_REF_KEYS)
    if unknown_ref:
        errors.append(f"sourceRef: unknown field(s) {unknown_ref}.")
    for rkey in ("family", "file", "item"):
        if rkey not in ref:
            errors.append(f"sourceRef: missing required field '{rkey}'.")
        elif not isinstance(ref[rkey], str) or not ref[rkey].strip():
            errors.append(f"sourceRef.{rkey}: must be a non-empty string.")
    resolved_mode: str | None = None
    if "family" in ref and isinstance(ref["family"], str) and ref["family"].strip():
        resolved_mode = family_mode(ref["family"], registry_path=registry_path)
        if resolved_mode == "scope":
            errors.append(
                f"sourceRef.family: '{ref['family']}' is scope-only (TOC/learning objectives); "
                "never extract core cards from OpenStax."
            )
        elif resolved_mode == "no-automation":
            errors.append(
                f"sourceRef.family: '{ref['family']}' is NO-AUTOMATION; "
                "never index or extract core cards automatically from NO-AUTOMATION sources."
            )
    if "page" not in ref:
        errors.append("sourceRef: missing required field 'page'.")
    else:
        page = ref["page"]
        valid_page = (_is_int(page) and page >= 1) or (isinstance(page, str) and bool(page.strip()))
        if not valid_page:
            errors.append(f"sourceRef.page: must be a positive integer or non-empty string, got {page!r}.")
    return resolved_mode


def _validate_traps(card: dict[str, Any], errors: list[str]) -> None:
    if "traps" not in card:
        return
    traps = card["traps"]
    if not isinstance(traps, list):
        errors.append("traps: must be a list of {tag, description} objects.")
        return
    for idx, trap in enumerate(traps):
        if not isinstance(trap, dict):
            errors.append(f"traps[{idx}]: must be an object.")
            continue
        unknown_t = sorted(set(trap) - _ALLOWED_TRAP_KEYS)
        if unknown_t:
            errors.append(f"traps[{idx}]: unknown field(s) {unknown_t}.")
        for tkey in ("tag", "description"):
            if tkey not in trap or not isinstance(trap[tkey], str) or not trap[tkey].strip():
                errors.append(f"traps[{idx}].{tkey}: must be a non-empty string.")


def _validate_prg_core_card(
    card: dict[str, Any],
    source_item_text: str | None = None,
    valid_unit_codes: Iterable[str] | None = None,
    registry_path: str | None = None,
) -> list[str]:
    errors: list[str] = []

    unknown_top = sorted(set(card) - _PRG_ALLOWED_TOP_KEYS)
    if unknown_top:
        errors.append(f"Unknown top-level field(s): {unknown_top}.")

    for req in _PRG_REQUIRED_TOP_KEYS:
        if req not in card:
            errors.append(f"Missing required field '{req}'.")

    if "profile" in card and card["profile"] != "prg":
        errors.append(f"profile: must be 'prg' for PRG core cards, got {card['profile']!r}.")

    # Enforce 200-char limit across every string field in the card.
    for path, text in _walk_strings(card):
        if len(text) > MAX_FIELD_LENGTH:
            errors.append(f"{path}: exceeds {MAX_FIELD_LENGTH}-char limit ({len(text)} chars).")

    for key in ("id", "unitCode", "skill", "concept", "bugPattern", "testsCatch", "difficultyDriver"):
        if key in card and (not isinstance(card[key], str) or not card[key].strip()):
            errors.append(f"{key}: must be a non-empty string.")

    if "smell" in card and (not isinstance(card["smell"], str) or not card["smell"].strip()):
        errors.append("smell: must be a non-empty string.")

    if "notes" in card and not isinstance(card["notes"], str):
        errors.append("notes: must be a string.")

    if "language" in card and card["language"] not in PRG_LANGUAGES:
        errors.append(f"language: must be one of {list(PRG_LANGUAGES)}, got {card['language']!r}.")

    if "archetypeKind" in card and card["archetypeKind"] not in PRG_ARCHETYPE_KINDS:
        errors.append(f"archetypeKind: must be one of {list(PRG_ARCHETYPE_KINDS)}, got {card['archetypeKind']!r}.")

    if "level" in card:
        lvl = card["level"]
        if not _is_int(lvl) or not (1 <= lvl <= 5):
            errors.append(f"level: must be an integer 1..5, got {lvl!r}.")

    _validate_shared_unit_refs(card, errors, valid_unit_codes)
    ref_mode = _validate_source_ref(card, errors, registry_path=registry_path)
    _validate_traps(card, errors)

    # qualityCheckIdeas validation
    if "qualityCheckIdeas" in card:
        qcs = card["qualityCheckIdeas"]
        if not isinstance(qcs, list):
            errors.append("qualityCheckIdeas: must be a list of {id, check, severity?} objects.")
        else:
            for idx, qc in enumerate(qcs):
                if not isinstance(qc, dict):
                    errors.append(f"qualityCheckIdeas[{idx}]: must be an object.")
                    continue
                unknown_q = sorted(set(qc) - _ALLOWED_QC_IDEA_KEYS)
                if unknown_q:
                    errors.append(f"qualityCheckIdeas[{idx}]: unknown field(s) {unknown_q}.")
                qid = qc.get("id")
                if not isinstance(qid, str) or not QC_ID_RE.match(qid):
                    errors.append(f"qualityCheckIdeas[{idx}].id: must match 'QC-<kebab-case>', got {qid!r}.")
                chk = qc.get("check")
                if not isinstance(chk, str) or not chk.strip():
                    errors.append(f"qualityCheckIdeas[{idx}].check: must be a non-empty string.")
                if "severity" in qc and qc["severity"] not in ("must", "should"):
                    errors.append(
                        f"qualityCheckIdeas[{idx}].severity: must be 'must' or 'should', got {qc['severity']!r}."
                    )

    # Optional reuse attribution block (allowed ONLY for REUSE families)
    if "reuse" in card and card["reuse"] is not None:
        reuse = card["reuse"]
        if not isinstance(reuse, dict):
            errors.append("reuse: must be an object with 'license' and 'attribution'.")
        else:
            unknown_r = sorted(set(reuse) - _ALLOWED_REUSE_KEYS)
            if unknown_r:
                errors.append(f"reuse: unknown field(s) {unknown_r}.")
            for rkey in ("license", "attribution"):
                if rkey not in reuse or not isinstance(reuse[rkey], str) or not reuse[rkey].strip():
                    errors.append(f"reuse.{rkey}: must be a non-empty string.")
            if "adaptedIdea" in reuse and (
                not isinstance(reuse["adaptedIdea"], str) or not reuse["adaptedIdea"].strip()
            ):
                errors.append("reuse.adaptedIdea: must be a non-empty string.")
            if ref_mode is not None and ref_mode != "reuse":
                fam = (card.get("sourceRef") or {}).get("family", "?")
                errors.append(
                    f"reuse: attribution block is only allowed for REUSE families "
                    f"('{fam}' has allowed use '{ref_mode}')."
                )

    # PRG no-copy guard: never paste code snippets into card content fields
    content_fields = _prg_content_string_fields(card)
    for path, text in content_fields:
        if "\n" in text or _CODE_SYNTAX_RE.search(text):
            errors.append(
                f"{path}: contains source code syntax or multi-line snippet; "
                "describe the abstract concept/pattern without pasting code."
            )

    # Source-free check against raw source_item_text (wording, identifiers, test names/strings, verbatim lines)
    if source_item_text and isinstance(source_item_text, str) and source_item_text.strip():
        src_shingles = _word_shingles(source_item_text)
        src_idents = _extract_distinctive_source_identifiers(source_item_text)
        src_strings = _extract_distinctive_source_strings(source_item_text)
        src_lines = [ln.strip() for ln in source_item_text.splitlines() if len(ln.strip()) >= 24]

        for path, text in content_fields:
            low_text = text.lower()
            if src_shingles:
                overlap = _word_shingles(text) & src_shingles
                if overlap:
                    sample = " ".join(sorted(overlap)[0])
                    errors.append(
                        f"{path}: contains source wording overlap ('{sample}'); "
                        "abstract the core without copying source phrasing."
                    )
            for ident in sorted(src_idents):
                if re.search(rf"(?<![A-Za-z0-9_$]){re.escape(ident)}(?![A-Za-z0-9_$])", text):
                    errors.append(
                        f"{path}: copies source identifier '{ident}'; "
                        "abstract the programming core without source identifiers."
                    )
                    break
            for lit in sorted(src_strings):
                if lit.lower() in low_text:
                    errors.append(
                        f"{path}: copies source test name or string literal '{lit[:60]}'; "
                        "abstract the behavior without copying source strings."
                    )
                    break
            for line in src_lines:
                if line in text:
                    errors.append(
                        f"{path}: contains verbatim source line '{line[:60]}'; "
                        "abstract the core without copying source code."
                    )
                    break

    return errors


def validate_core_card(
    card: Any,
    source_item_text: str | None = None,
    valid_unit_codes: Iterable[str] | None = None,
    registry_path: str | None = None,
) -> list[str]:
    """Validate a core card against ``schema.json`` (Math) or ``prg_schema.json`` (PRG) and source-free invariants.

    Returns a list of error strings (empty list means valid).
    """
    if not isinstance(card, dict):
        return ["Card must be a JSON object."]

    if is_prg_card(card):
        return _validate_prg_core_card(
            card,
            source_item_text=source_item_text,
            valid_unit_codes=valid_unit_codes,
            registry_path=registry_path,
        )

    errors: list[str] = []

    unknown_top = sorted(set(card) - _ALLOWED_TOP_KEYS)
    if unknown_top:
        errors.append(f"Unknown top-level field(s): {unknown_top}.")

    for req in _REQUIRED_TOP_KEYS:
        if req not in card:
            errors.append(f"Missing required field '{req}'.")

    # Enforce 200-char limit across every string field in the card.
    for path, text in _walk_strings(card):
        if len(text) > MAX_FIELD_LENGTH:
            errors.append(f"{path}: exceeds {MAX_FIELD_LENGTH}-char limit ({len(text)} chars).")

    for key in ("id", "unitCode", "skill", "difficultyDriver"):
        if key in card and (not isinstance(card[key], str) or not card[key].strip()):
            errors.append(f"{key}: must be a non-empty string.")

    _validate_shared_unit_refs(card, errors, valid_unit_codes)

    if "notes" in card and not isinstance(card["notes"], str):
        errors.append("notes: must be a string.")

    if "reasoningMove" in card and card["reasoningMove"] not in REASONING_MOVES:
        errors.append(f"reasoningMove: must be one of {list(REASONING_MOVES)}, got {card['reasoningMove']!r}.")

    if "operations" in card:
        ops = card["operations"]
        if not isinstance(ops, list) or len(ops) < 2:
            errors.append("operations: must be a list of at least 2 ordered sub-skill names.")
        else:
            seen_ops: set[str] = set()
            for idx, op in enumerate(ops):
                if not isinstance(op, str) or not op.strip():
                    errors.append(f"operations[{idx}]: must be a non-empty string.")
                else:
                    norm_op = normalize_operation(op)
                    if norm_op in seen_ops:
                        errors.append(
                            f"operations[{idx}]: duplicate operation {op!r} after normalisation ({norm_op!r})."
                        )
                    seen_ops.add(norm_op)
    elif card.get("reasoningMove") == "chain":
        errors.append(
            "operations: required when reasoningMove is 'chain' (list of at least 2 ordered sub-skill names)."
        )

    if "level" in card:
        lvl = card["level"]
        if not _is_int(lvl) or not (1 <= lvl <= 5):
            errors.append(f"level: must be an integer 1..5, got {lvl!r}.")
        elif card.get("reasoningMove") == "chain" and lvl != 2:
            errors.append(f"level: reasoningMove 'chain' must have level 2, got {lvl!r}.")

    if "representation" in card and card["representation"] not in REPRESENTATIONS:
        errors.append(f"representation: must be one of {list(REPRESENTATIONS)}, got {card['representation']!r}.")

    _validate_source_ref(card, errors, registry_path=registry_path)
    _validate_traps(card, errors)

    # format validation
    if "format" in card:
        fmt = card["format"]
        if not isinstance(fmt, dict):
            errors.append("format: must be an object.")
        else:
            unknown_f = sorted(set(fmt) - _ALLOWED_FORMAT_KEYS)
            if unknown_f:
                errors.append(f"format: unknown field(s) {unknown_f}.")
            if "kind" not in fmt:
                errors.append("format: missing required field 'kind'.")
            elif fmt["kind"] not in FORMAT_KINDS:
                errors.append(f"format.kind: must be one of {list(FORMAT_KINDS)}, got {fmt['kind']!r}.")
            if "optionCount" in fmt:
                oc = fmt["optionCount"]
                if not _is_int(oc) or not (2 <= oc <= 20):
                    errors.append(f"format.optionCount: must be an integer 2..20, got {oc!r}.")
            if "distractorPatterns" in fmt:
                dp = fmt["distractorPatterns"]
                if not isinstance(dp, list) or not all(isinstance(x, str) and x.strip() for x in dp):
                    errors.append("format.distractorPatterns: must be a list of non-empty strings.")

    # Source-free check when source_item_text is supplied
    if source_item_text and isinstance(source_item_text, str) and source_item_text.strip():
        src_digits = set(extract_digit_runs(source_item_text))
        src_shingles = _word_shingles(source_item_text)
        for path, text in _content_string_fields(card):
            if src_digits:
                copied = sorted(set(extract_digit_runs(text)) & src_digits)
                if copied:
                    errors.append(
                        f"{path}: contains digit run(s) {copied} copied from source item text; "
                        "abstract the core without source numbers."
                    )
            if src_shingles:
                overlap = _word_shingles(text) & src_shingles
                if overlap:
                    sample = " ".join(sorted(overlap)[0])
                    errors.append(
                        f"{path}: contains source wording overlap ('{sample}'); "
                        "abstract the core without copying source phrasing."
                    )

    return errors


def _iter_jsonl_cards(path: str) -> Iterable[tuple[int, dict[str, Any]]]:
    with open(path, "r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, 1):
            line = raw.strip()
            if not line:
                continue
            try:
                card = json.loads(line)
            except ValueError as exc:
                raise CoreCardError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
            if not isinstance(card, dict):
                raise CoreCardError(f"{path}:{line_no}: invalid core card: Card must be a JSON object.")
            yield line_no, card


def _card_targets_unit(card: dict[str, Any], unit_code: str) -> bool:
    later = card.get("laterUnit")
    if isinstance(later, str) and later.strip() == unit_code:
        return True
    units = card.get("units")
    if isinstance(units, list) and any(isinstance(u, str) and u.strip() == unit_code for u in units):
        return True
    return False


def load_core_cards(
    unit_code: str,
    sources_dir: str | None = None,
    validate: bool = True,
    *,
    include_carried: bool = True,
    valid_unit_codes: Iterable[str] | None = None,
    registry_path: str | None = None,
) -> list[dict[str, Any]]:
    """Load core cards for ``unit_code`` from ``sources/_cores/<unit_code>.jsonl``.

    When ``include_carried`` is True (default), also scans other ``sources/_cores/*.jsonl``
    files for cards whose ``laterUnit == unit_code`` or whose ``units`` contains ``unit_code``,
    deduplicating by ``id`` and annotating carried-forward cards with ``carriedFrom``.
    """
    cards: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    path = cores_path(unit_code, sources_dir=sources_dir)
    if os.path.exists(path):
        for line_no, card in _iter_jsonl_cards(path):
            if validate:
                errs = validate_core_card(card, valid_unit_codes=valid_unit_codes, registry_path=registry_path)
                if errs:
                    raise CoreCardError(f"{path}:{line_no}: invalid core card: " + "; ".join(errs))
            cid = card.get("id")
            if isinstance(cid, str):
                if cid in seen_ids:
                    continue
                seen_ids.add(cid)
            cards.append(card)

    if include_carried:
        cores_dir = os.path.dirname(path)
        if os.path.isdir(cores_dir):
            for fname in sorted(os.listdir(cores_dir)):
                if not fname.endswith(".jsonl"):
                    continue
                other_unit = fname[:-6]
                if other_unit == unit_code:
                    continue
                other_path = os.path.join(cores_dir, fname)
                if not os.path.isfile(other_path):
                    continue
                for line_no, card in _iter_jsonl_cards(other_path):
                    if not _card_targets_unit(card, unit_code):
                        continue
                    cid = card.get("id")
                    if isinstance(cid, str) and cid in seen_ids:
                        continue
                    if validate:
                        errs = validate_core_card(card, valid_unit_codes=valid_unit_codes, registry_path=registry_path)
                        if errs:
                            raise CoreCardError(f"{other_path}:{line_no}: invalid core card: " + "; ".join(errs))
                    if isinstance(cid, str):
                        seen_ids.add(cid)
                    cards.append({**card, "carriedFrom": other_unit})

    return cards


def save_core_cards(
    unit_code: str,
    cards: list[dict[str, Any]],
    sources_dir: str | None = None,
    source_texts: dict[str, str] | None = None,
    *,
    valid_unit_codes: Iterable[str] | None = None,
    registry_path: str | None = None,
) -> str:
    """Validate and write ``cards`` to ``sources/_cores/<unit_code>.jsonl``."""
    source_texts = source_texts or {}
    for idx, card in enumerate(cards, 1):
        cid = card.get("id", f"#{idx}") if isinstance(card, dict) else f"#{idx}"
        errs = validate_core_card(
            card,
            source_item_text=source_texts.get(cid),
            valid_unit_codes=valid_unit_codes,
            registry_path=registry_path,
        )
        if errs:
            raise CoreCardError(f"[{cid}] invalid core card: " + "; ".join(errs))
    path = cores_path(unit_code, sources_dir=sources_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for card in cards:
            fh.write(json.dumps(card, ensure_ascii=False) + "\n")
    return path


def append_core_card(
    unit_code: str,
    card: dict[str, Any],
    sources_dir: str | None = None,
    source_item_text: str | None = None,
    *,
    valid_unit_codes: Iterable[str] | None = None,
    registry_path: str | None = None,
) -> str:
    """Validate and append one core card to ``sources/_cores/<unit_code>.jsonl``."""
    errs = validate_core_card(
        card,
        source_item_text=source_item_text,
        valid_unit_codes=valid_unit_codes,
        registry_path=registry_path,
    )
    if errs:
        raise CoreCardError("Invalid core card: " + "; ".join(errs))
    path = cores_path(unit_code, sources_dir=sources_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(card, ensure_ascii=False) + "\n")
    return path
