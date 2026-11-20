# -*- coding: utf-8 -*-
"""Code originality gate for PRG drills and project labs.

Combines:
1. Token-level code similarity against indexed source code (and fenced code blocks in Markdown):
   normalises comments, whitespace, optional semicolons, string/numeric literals, and all
   non-keyword identifiers to ``ID``, then compares deterministic k-gram hashes and Winnowing
   fingerprints (Schleimer, Wilkerson & Aiken 2003) per source file. Catches both verbatim copies
   and renamed-identifier / reformatted copies while letting original implementations pass.
2. Prompt / README / milestone-goal text checks (8-word shingle overlap and normalised
   SequenceMatcher similarity >= 0.6) reusing ``math_engine.source_cores.originality``.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from math_engine.source_cores import index_dir, resolve_sources_dir
from math_engine.source_cores.originality import (
    DEFAULT_SHINGLE_SIZE,
    DEFAULT_SIMILARITY_THRESHOLD,
    MIN_SIMILARITY_CHARS,
    MIN_WINDOW_CHARS,
    _option_texts,
    _PreparedSourceIndex,
    load_located_source_pages,
    normalize_text,
    word_shingles,
)

DEFAULT_KGRAM_SIZE = 12
DEFAULT_WINNOW_WINDOW = 4
DEFAULT_MIN_CODE_TOKENS = 20
DEFAULT_CODE_SIMILARITY_THRESHOLD = 0.45
DEFAULT_MIN_SHARED_FINGERPRINTS = 3

CODE_FILE_SUFFIXES: tuple[str, ...] = (".js", ".mjs", ".cjs", ".jsx", ".ts", ".mts", ".cts", ".tsx", ".py")

_CODE_KEYWORDS: frozenset[str] = frozenset(
    {
        # JS / TS
        "async",
        "await",
        "break",
        "case",
        "catch",
        "class",
        "const",
        "continue",
        "debugger",
        "default",
        "delete",
        "do",
        "else",
        "enum",
        "export",
        "extends",
        "false",
        "finally",
        "for",
        "from",
        "function",
        "if",
        "implements",
        "import",
        "in",
        "instanceof",
        "interface",
        "let",
        "new",
        "null",
        "of",
        "private",
        "protected",
        "public",
        "readonly",
        "return",
        "static",
        "super",
        "switch",
        "this",
        "throw",
        "true",
        "try",
        "type",
        "typeof",
        "undefined",
        "var",
        "void",
        "while",
        "yield",
        "as",
        "keyof",
        "never",
        "unknown",
        # Python
        "and",
        "assert",
        "def",
        "del",
        "elif",
        "except",
        "False",
        "global",
        "is",
        "lambda",
        "None",
        "nonlocal",
        "not",
        "or",
        "pass",
        "raise",
        "True",
        "with",
    }
)

_TOKEN_MASTER_RE = re.compile(
    r"""
    (?P<block_comment>/\*[\s\S]*?\*/)
    | (?P<line_comment>//[^\n]*)
    | (?P<py_comment>(?:^|(?<=\s))\#[^\n]*)
    | (?P<py_triple_dq>\"\"\"[\s\S]*?\"\"\")
    | (?P<py_triple_sq>'''[\s\S]*?''')
    | (?P<str_dq>\"(?:\\.|[^\"\\\n])*\")
    | (?P<str_sq>'(?:\\.|[^'\\\n])*')
    | (?P<str_tpl>`(?:\\.|[^`\\])*`)
    | (?P<num>\b(?:0[xXbBoO][0-9a-fA-F_]+|\d[\d_]*(?:\.\d[\d_]*)?(?:[eE][+-]?\d+)?n?)\b)
    | (?P<multi_op>===|!==|>>>=|<<=|>>=|\*\*=|\?\?=|&&=|\|\|=|\.\.\.|=>|<=|>=|==|!=|&&|\|\||\?\?|\?\.|\+=|-=|\*=|/=|%=|\*\*|\+\+|--|<<|>>|->|:=)
    | (?P<ident>[A-Za-z_$][A-Za-z0-9_$]*)
    | (?P<single_op>[(){}\[\],.:?+\-*/%=<>!&|^~@])
    """,
    re.VERBOSE,
)

_FENCED_CODE_BLOCK_RE = re.compile(
    r"```(?:js|jsx|ts|tsx|javascript|typescript|py|python|mjs|cjs)?\s*\n([\s\S]*?)```",
    re.IGNORECASE,
)


def tokenize_code(code: str) -> list[str]:
    """Normalize JS/TS/Python code into a whitespace- and identifier-invariant token stream.

    Comments, whitespace, and semicolons are stripped; all string literals become ``STR``,
    numeric literals become ``NUM``, language keywords stay ``KW:<word>``, operators/delimiters
    stay ``OP:<tok>``, and all user-defined identifiers become ``ID``.
    """
    tokens: list[str] = []
    for m in _TOKEN_MASTER_RE.finditer(code or ""):
        kind = m.lastgroup
        if kind in ("block_comment", "line_comment", "py_comment"):
            continue
        if kind in ("py_triple_dq", "py_triple_sq", "str_dq", "str_sq", "str_tpl"):
            tokens.append("STR")
        elif kind == "num":
            tokens.append("NUM")
        elif kind in ("multi_op", "single_op"):
            tokens.append(f"OP:{m.group(0)}")
        elif kind == "ident":
            word = m.group(0)
            if word in _CODE_KEYWORDS:
                tokens.append(f"KW:{word}")
            else:
                tokens.append("ID")
    return tokens


def kgram_hashes(tokens: list[str], k: int = DEFAULT_KGRAM_SIZE) -> list[int]:
    """Compute deterministic 64-bit ``blake2b`` hashes for every contiguous ``k``-gram of ``tokens``."""
    if len(tokens) < k or k <= 0:
        return []
    out: list[int] = []
    for idx in range(len(tokens) - k + 1):
        gram = " ".join(tokens[idx : idx + k]).encode("utf-8")
        digest = hashlib.blake2b(gram, digest_size=8).digest()
        out.append(int.from_bytes(digest, "big"))
    return out


def winnow_fingerprints(hashes: list[int], window: int = DEFAULT_WINNOW_WINDOW) -> set[int]:
    """Select Winnowing fingerprints (rightmost minimum hash per window of size ``window``)."""
    if not hashes:
        return set()
    if window <= 1 or len(hashes) < window:
        return set(hashes)
    selected: dict[int, int] = {}
    for start in range(len(hashes) - window + 1):
        best_pos = start
        best_val = hashes[start]
        for pos in range(start + 1, start + window):
            val = hashes[pos]
            if val <= best_val:
                best_val = val
                best_pos = pos
        selected[best_pos] = best_val
    return set(selected.values())


def extract_code_blocks_from_source(rel_path: str, text: str) -> list[str]:
    """Extract code strings to fingerprint from a cached source page (code file or Markdown fences)."""
    low = (rel_path or "").lower()
    if low.endswith((".md", ".markdown")):
        return [m.group(1) for m in _FENCED_CODE_BLOCK_RE.finditer(text or "") if m.group(1).strip()]
    if low.endswith(".json"):
        return []
    return [text] if (text or "").strip() else []


class _PreparedCodeSourceIndex:
    """Precomputed prompt text index + per-source-file winnowed code fingerprints."""

    def __init__(
        self,
        source_pages: list[dict[str, Any]],
        *,
        shingle_size: int = DEFAULT_SHINGLE_SIZE,
        kgram_size: int = DEFAULT_KGRAM_SIZE,
        winnow_window: int = DEFAULT_WINNOW_WINDOW,
        min_code_tokens: int = DEFAULT_MIN_CODE_TOKENS,
    ) -> None:
        self.shingle_size = shingle_size
        self.kgram_size = kgram_size
        self.winnow_window = winnow_window
        self.min_code_tokens = min_code_tokens
        self.text_index = _PreparedSourceIndex(source_pages, shingle_size=shingle_size)
        self.code_entries: list[tuple[str, set[int], set[int]]] = []

        for page in source_pages:
            rel = str(page.get("relPath") or "source")
            pnum = page.get("page", 1)
            loc = f"{rel} p.{pnum}"
            text = str(page.get("text") or "")
            if not text.strip():
                continue
            for idx, block in enumerate(extract_code_blocks_from_source(rel, text), 1):
                toks = tokenize_code(block)
                if len(toks) < min_code_tokens:
                    continue
                hashes = kgram_hashes(toks, k=kgram_size)
                if not hashes:
                    continue
                fps = winnow_fingerprints(hashes, window=winnow_window)
                block_loc = f"{loc}#code{idx}" if rel.lower().endswith((".md", ".markdown")) else loc
                self.code_entries.append((block_loc, fps, set(hashes)))


def _check_text_against_source(
    pid: str,
    label: str,
    text: str,
    prepared: _PreparedCodeSourceIndex,
    *,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> list[str]:
    errors: list[str] = []
    if not text or not text.strip():
        return errors

    # 1. Word shingle overlap (8-word default, same as math)
    for sh in word_shingles(text, size=prepared.shingle_size):
        if sh in prepared.text_index.shingles:
            loc = prepared.text_index.shingles[sh]
            errors.append(
                f"[{pid}] Originality gate failed ({label}): {prepared.shingle_size}-word shingle overlap "
                f'"{" ".join(sh)}" with {loc}.'
            )
            break

    # 2. Normalised similarity >= threshold to any source sentence window
    norm_cand = normalize_text(text)
    if len(norm_cand) < MIN_WINDOW_CHARS:
        return errors
    if len(norm_cand) < MIN_SIMILARITY_CHARS:
        hit = next((loc for win, loc in prepared.text_index.windows if norm_cand in win), "")
        if hit:
            errors.append(f"[{pid}] Originality gate failed ({label}): verbatim copy of a source sentence in {hit}.")
        return errors

    best_ratio = 0.0
    best_loc = ""
    for win, loc in prepared.text_index.windows:
        sm = difflib.SequenceMatcher(None, norm_cand, win)
        if sm.quick_ratio() < similarity_threshold:
            continue
        ratio = sm.ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_loc = loc
    if best_ratio >= similarity_threshold:
        errors.append(
            f"[{pid}] Originality gate failed ({label}): normalised similarity "
            f"{best_ratio:.2f} (>= {similarity_threshold:.2f}) to {best_loc}."
        )
    return errors


def check_code_snippet_originality(
    code: str,
    *,
    pid: str,
    label: str,
    prepared: _PreparedCodeSourceIndex,
    code_threshold: float = DEFAULT_CODE_SIMILARITY_THRESHOLD,
    min_shared_fps: int = DEFAULT_MIN_SHARED_FINGERPRINTS,
) -> list[str]:
    """Compare one code snippet against all indexed source code files via normalized k-gram Winnowing."""
    if not code or not code.strip() or not prepared.code_entries:
        return []
    tokens = tokenize_code(code)
    if len(tokens) < prepared.min_code_tokens:
        return []
    hashes = kgram_hashes(tokens, k=prepared.kgram_size)
    if not hashes:
        return []
    cand_fps = winnow_fingerprints(hashes, window=prepared.winnow_window)
    cand_kgrams = set(hashes)
    if not cand_fps:
        return []

    best_score = 0.0
    best_shared = 0
    best_loc = ""
    for loc, src_fps, src_kgrams in prepared.code_entries:
        shared_fps = cand_fps & src_fps
        if not shared_fps:
            continue
        fp_ratio = len(shared_fps) / len(cand_fps)
        kg_ratio = len(cand_kgrams & src_kgrams) / len(cand_kgrams)
        score = max(fp_ratio, kg_ratio)
        if score > best_score:
            best_score = score
            best_shared = len(shared_fps)
            best_loc = loc

    enough_fps = best_shared >= min_shared_fps or (len(cand_fps) < min_shared_fps and best_score >= 0.75)
    if best_score >= code_threshold and enough_fps:
        return [
            f"[{pid}] Code originality gate failed ({label}): token similarity {best_score:.2f} "
            f"(>= {code_threshold:.2f}; {best_shared}/{len(cand_fps)} winnowed fingerprints matched) "
            f"with {best_loc}."
        ]
    return []


def check_code_problem_originality(
    prob: dict[str, Any],
    source_pages: list[dict[str, Any]],
    *,
    shingle_size: int = DEFAULT_SHINGLE_SIZE,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    code_threshold: float = DEFAULT_CODE_SIMILARITY_THRESHOLD,
    kgram_size: int = DEFAULT_KGRAM_SIZE,
    winnow_window: int = DEFAULT_WINNOW_WINDOW,
    _prepared: _PreparedCodeSourceIndex | None = None,
) -> list[str]:
    """Check one PRG drill problem's prompt, options, solution, starter, snippet, and tests."""
    if not source_pages:
        return []
    prepared = _prepared or _PreparedCodeSourceIndex(
        source_pages,
        shingle_size=shingle_size,
        kgram_size=kgram_size,
        winnow_window=winnow_window,
    )
    pid = str(prob.get("id") or "?")
    errors: list[str] = []

    # 1. Prompt & choice options text checks
    prompt = str(prob.get("prompt") or "")
    errors.extend(
        _check_text_against_source(pid, "prompt", prompt, prepared, similarity_threshold=similarity_threshold)
    )
    for idx, opt in enumerate(_option_texts(prob), 1):
        errors.extend(
            _check_text_against_source(pid, f"option {idx}", opt, prepared, similarity_threshold=similarity_threshold)
        )

    # 2. Code similarity checks on solution, starter, snippet, multi-file snippets, and tests
    code_targets: list[tuple[str, str]] = []
    for field in ("solutionCode", "starterCode", "codeSnippet"):
        val = prob.get(field)
        if isinstance(val, str) and val.strip():
            code_targets.append((field, val))
    files_map = prob.get("files")
    if isinstance(files_map, dict):
        for fname, fcode in sorted(files_map.items()):
            if isinstance(fcode, str) and fcode.strip():
                code_targets.append((f"files[{fname}]", fcode))

    for test_field in ("visibleTests", "hiddenTests"):
        tests = prob.get(test_field) or []
        combined_parts: list[str] = []
        for idx, t in enumerate(tests, 1):
            if not isinstance(t, dict):
                continue
            tcode = str(t.get("testCode") or "")
            if tcode.strip():
                code_targets.append((f"{test_field}[{idx}]", tcode))
                combined_parts.append(tcode)
        if len(combined_parts) >= 2:
            code_targets.append((f"{test_field}(combined)", "\n".join(combined_parts)))

    for label, snippet in code_targets:
        errors.extend(
            check_code_snippet_originality(
                snippet,
                pid=pid,
                label=label,
                prepared=prepared,
                code_threshold=code_threshold,
            )
        )

    return errors


def _load_prg_source_pages_for_units(units: list[str], sources_dir: str) -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, int]] = set()
    for u in units:
        if not u:
            continue
        for p in load_located_source_pages(u, sources_dir=sources_dir):
            key = (str(p.get("relPath") or ""), int(p.get("page") or 0))
            if key not in seen_keys:
                seen_keys.add(key)
                pages.append(p)
    return pages


def check_code_drill_originality(
    doc: dict[str, Any],
    unit_code: str | None = None,
    sources_dir: str | None = None,
    *,
    source_pages: list[dict[str, Any]] | None = None,
    shingle_size: int = DEFAULT_SHINGLE_SIZE,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    code_threshold: float = DEFAULT_CODE_SIMILARITY_THRESHOLD,
) -> tuple[list[str], str | None]:
    """Check every problem in a PRG drill draft against indexed PRG sources.

    Returns ``(errors, skip_notice)``. Skips cleanly with a notice when ``sources/`` or cached
    located pages for the unit do not exist.
    """
    resolved_unit = unit_code or doc.get("unitCode")
    if not isinstance(resolved_unit, str) or not resolved_unit.strip():
        return (["Document must specify 'unitCode' (or pass --unit)."], None)

    items = doc.get("problems")
    if not isinstance(items, list):
        return (["Document must contain a 'problems' list."], None)

    if source_pages is None:
        sdir = resolve_sources_dir(sources_dir=sources_dir)
        if not os.path.isdir(sdir):
            return ([], f"Originality gate skipped: sources directory not found ({sdir}).")
        units_to_load: list[str] = [resolved_unit]
        for prob in items:
            if isinstance(prob, dict):
                pu = prob.get("unitCode")
                if isinstance(pu, str) and pu.strip() and pu.strip() not in units_to_load:
                    units_to_load.append(pu.strip())
        source_pages = _load_prg_source_pages_for_units(units_to_load, sdir)
        if not source_pages:
            return (
                [],
                f"Originality gate skipped: no cached located source pages for {resolved_unit} under {index_dir(sdir)}.",
            )

    prepared = _PreparedCodeSourceIndex(source_pages, shingle_size=shingle_size)
    errors: list[str] = []
    for idx, prob in enumerate(items, 1):
        if not isinstance(prob, dict):
            continue
        if "id" not in prob:
            prob = {**prob, "id": f"Q{idx:02d}"}
        errors.extend(
            check_code_problem_originality(
                prob,
                source_pages,
                shingle_size=shingle_size,
                similarity_threshold=similarity_threshold,
                code_threshold=code_threshold,
                _prepared=prepared,
            )
        )
    return (errors, None)


def _iter_code_files(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(
        p
        for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in CODE_FILE_SUFFIXES and "node_modules" not in p.parts
    )


def check_lab_originality(
    lab_dir: Path | str,
    *,
    ref_dir: Path | str | None = None,
    sources_dir: str | None = None,
    source_pages: list[dict[str, Any]] | None = None,
    shingle_size: int = DEFAULT_SHINGLE_SIZE,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    code_threshold: float = DEFAULT_CODE_SIMILARITY_THRESHOLD,
) -> tuple[list[str], str | None]:
    """Check a PRG project lab's README/goals, stubs, reference implementation, and visible/hidden tests."""
    lab_path = Path(lab_dir)
    resolved_ref = Path(ref_dir) if ref_dir is not None else lab_path.parent / "_reference" / lab_path.name
    cfg_path = lab_path / "lab.config.json"
    if not cfg_path.is_file():
        return ([f"Missing {cfg_path}"], None)
    try:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return ([f"Invalid JSON in {cfg_path}: {exc}"], None)

    lab_id = str(cfg.get("labId") or lab_path.name)
    units_to_load: list[str] = []
    for u in [cfg.get("chapterCode"), *(cfg.get("unitsUsed") or [])]:
        if isinstance(u, str) and u.strip() and u.strip() not in units_to_load:
            units_to_load.append(u.strip())

    if source_pages is None:
        sdir = resolve_sources_dir(sources_dir=sources_dir)
        if not os.path.isdir(sdir):
            return ([], f"Originality gate skipped: sources directory not found ({sdir}).")
        source_pages = _load_prg_source_pages_for_units(units_to_load, sdir)
        if not source_pages:
            scope_label = ", ".join(units_to_load) or lab_id
            return (
                [],
                f"Originality gate skipped: no cached located source pages for {scope_label} under {index_dir(sdir)}.",
            )

    prepared = _PreparedCodeSourceIndex(source_pages, shingle_size=shingle_size)
    errors: list[str] = []

    # 1. Text checks on scenario, milestone goals, and README.md
    scenario = str(cfg.get("scenario") or "")
    if scenario.strip():
        errors.extend(
            _check_text_against_source(
                lab_id, "scenario", scenario, prepared, similarity_threshold=similarity_threshold
            )
        )
    for ms in cfg.get("milestones") or []:
        if not isinstance(ms, dict):
            continue
        mid = str(ms.get("id") or "?")
        goal = str(ms.get("goal") or "")
        if goal.strip():
            errors.extend(
                _check_text_against_source(
                    f"{lab_id}/{mid}", "goal", goal, prepared, similarity_threshold=similarity_threshold
                )
            )
    readme_path = lab_path / "README.md"
    if readme_path.is_file():
        readme_text = readme_path.read_text(encoding="utf-8", errors="replace")
        for idx, para in enumerate(re.split(r"\n\s*\n+", readme_text), 1):
            cleaned = para.strip()
            if len(cleaned) >= MIN_WINDOW_CHARS and not cleaned.startswith("```"):
                errors.extend(
                    _check_text_against_source(
                        lab_id, f"README.md#p{idx}", cleaned, prepared, similarity_threshold=similarity_threshold
                    )
                )

    # 2. Code fingerprint checks on starter src/, visible tests/, reference src/, and hidden tests/
    scan_dirs: list[tuple[str, Path]] = [
        ("starter", lab_path / "src"),
        ("visibleTests", lab_path / "tests"),
        ("reference", resolved_ref / "src"),
        ("hiddenTests", resolved_ref / "hidden"),
    ]
    for group_label, folder in scan_dirs:
        for file_path in _iter_code_files(folder):
            rel_name = file_path.relative_to(folder).as_posix()
            code = file_path.read_text(encoding="utf-8", errors="replace")
            errors.extend(
                check_code_snippet_originality(
                    code,
                    pid=lab_id,
                    label=f"{group_label}:{rel_name}",
                    prepared=prepared,
                    code_threshold=code_threshold,
                )
            )

    return (errors, None)
