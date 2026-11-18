# -*- coding: utf-8 -*-
"""Detect and safely wrap bare English prose words inside LaTeX strings.

KaTeX / Notion math mode renders unescaped multi-letter words as italicised
products of variables without spaces (e.g. ``exchange the variables`` becomes
``exchangethevariables``). This module provides the canonical detector used by
math ingest/verification gates and the Notion LaTeX safety net.

Keep the detection rules in sync with ``practice-studio/src/lib/mathText.ts``.
"""

from __future__ import annotations

import re

# Known mathematical function / operator names that may appear bare (without \)
# in LaTeX or CAS-style display expressions.
KNOWN_MATH_FUNCTIONS: frozenset[str] = frozenset(
    {
        "sin",
        "cos",
        "tan",
        "cot",
        "sec",
        "csc",
        "arcsin",
        "arccos",
        "arctan",
        "arccot",
        "arcsec",
        "arccsc",
        "sinh",
        "cosh",
        "tanh",
        "coth",
        "sech",
        "csch",
        "asinh",
        "acosh",
        "atanh",
        "log",
        "ln",
        "lg",
        "exp",
        "min",
        "max",
        "inf",
        "sup",
        "lim",
        "limsup",
        "liminf",
        "gcd",
        "lcm",
        "deg",
        "det",
        "dim",
        "ker",
        "im",
        "arg",
        "mod",
        "bmod",
        "pmod",
        "sgn",
        "floor",
        "ceil",
        "round",
        "abs",
        "sqrt",
        "cbrt",
        "Re",
        "Im",
        "Pr",
        "hom",
    }
)

# Common 3-letter English words so isolated 3-letter prose tokens (e.g. "iff",
# "for", "and") are caught while 3-letter algebraic products like "abc" or
# "xyz" are not falsely flagged.
THREE_LETTER_WORDS: frozenset[str] = frozenset(
    {
        "add",
        "age",
        "air",
        "all",
        "and",
        "any",
        "are",
        "arm",
        "ask",
        "bad",
        "bar",
        "bed",
        "big",
        "bit",
        "box",
        "bus",
        "but",
        "buy",
        "can",
        "car",
        "cat",
        "col",
        "cup",
        "cut",
        "day",
        "did",
        "div",
        "dog",
        "dot",
        "due",
        "end",
        "era",
        "far",
        "fee",
        "few",
        "fit",
        "fix",
        "for",
        "gap",
        "gas",
        "get",
        "had",
        "has",
        "her",
        "hex",
        "him",
        "his",
        "hot",
        "how",
        "hrs",
        "ice",
        "iff",
        "ill",
        "its",
        "job",
        "key",
        "law",
        "lay",
        "led",
        "leg",
        "let",
        "lie",
        "lot",
        "low",
        "map",
        "may",
        "men",
        "met",
        "mid",
        "mix",
        "net",
        "new",
        "non",
        "nor",
        "not",
        "now",
        "odd",
        "off",
        "oil",
        "old",
        "one",
        "our",
        "out",
        "own",
        "pay",
        "per",
        "put",
        "raw",
        "ray",
        "red",
        "row",
        "run",
        "sat",
        "saw",
        "say",
        "sea",
        "see",
        "set",
        "she",
        "six",
        "sky",
        "sub",
        "sum",
        "sun",
        "tax",
        "ten",
        "the",
        "til",
        "tip",
        "too",
        "top",
        "try",
        "two",
        "use",
        "val",
        "van",
        "var",
        "via",
        "was",
        "way",
        "who",
        "why",
        "won",
        "yes",
        "yet",
        "you",
    }
)

# Commands whose braced argument {...} is already text/operator/env metadata
# and must not be scanned for bare words.
_SKIP_BRACE_ARG_COMMANDS: frozenset[str] = frozenset(
    {
        "text",
        "textrm",
        "textit",
        "textbf",
        "textsf",
        "texttt",
        "mathrm",
        "mathbf",
        "mathit",
        "mathsf",
        "mathtt",
        "mathcal",
        "mathbb",
        "mathfrak",
        "operatorname",
        "mbox",
        "hbox",
        "label",
        "ref",
        "tag",
        "color",
        "textcolor",
        "begin",
        "end",
    }
)

_WORD_TOKEN_RE = re.compile(r"[A-Za-z]{2,}(?:['\u2019][A-Za-z]+)?|[A-Za-z]")
_PROSE_GAP_RE = re.compile(r"^[ \t\n\r,;:!?\u2019'.-]+$")


def _consume_balanced_braces(tex: str, idx: int) -> int:
    """Assuming tex[idx] == '{', return the index right after its matching '}'."""
    n = len(tex)
    depth = 0
    i = idx
    while i < n:
        ch = tex[i]
        if ch == "\\" and i + 1 < n:
            i += 2
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return n


def _unprotected_slices(tex: str) -> list[tuple[int, int]]:
    """Return [(start, end), ...] spans outside backslash commands and text-like braces."""
    n = len(tex)
    slices: list[tuple[int, int]] = []
    cur_start: int | None = None
    i = 0
    while i < n:
        if tex[i] == "\\":
            if cur_start is not None:
                slices.append((cur_start, i))
                cur_start = None
            if i + 1 < n and tex[i + 1].isalpha():
                j = i + 1
                while j < n and tex[j].isalpha():
                    j += 1
                cmd = tex[i + 1 : j]
                i = j
                if cmd in _SKIP_BRACE_ARG_COMMANDS:
                    k = i
                    if k < n and tex[k] == "*":
                        k += 1
                    while k < n and tex[k] in " \t":
                        k += 1
                    if k < n and tex[k] == "{":
                        i = _consume_balanced_braces(tex, k)
            else:
                i = min(i + 2, n)
        else:
            if cur_start is None:
                cur_start = i
            i += 1
    if cur_start is not None:
        slices.append((cur_start, n))
    return slices


def _is_prose_gap(gap: str, prev_len: int, curr_len: int) -> bool:
    if not gap or not _PROSE_GAP_RE.match(gap):
        return False
    # Never treat "a - b" (spaced minus) as a prose hyphen.
    if "-" in gap and gap != "-":
        return False
    # Two 2-letter tokens separated by punctuation like "mx, ny" are math lists,
    # whereas pure whitespace like "is it" or "to be" is prose.
    if prev_len == 2 and curr_len == 2 and not gap.isspace() and gap != "-":
        return False
    return True


def _token_info(raw: str) -> tuple[str, bool, bool, bool]:
    base = re.split(r"['\u2019]", raw, maxsplit=1)[0]
    is_single = len(base) == 1
    is_all_caps = len(base) >= 2 and base.isupper()
    is_known_fn = base in KNOWN_MATH_FUNCTIONS
    is_bridge = base in ("a", "I")
    is_candidate = (not is_single) and (not is_all_caps) and (not is_known_fn)
    is_strong = is_candidate and (len(base) >= 4 or (len(base) == 3 and base.lower() in THREE_LETTER_WORDS))
    return base, is_candidate, is_strong, is_bridge


def find_bare_word_spans(tex: str) -> list[tuple[int, int, str]]:
    """Return ``[(start, end, snippet), ...]`` for bare English word runs in ``tex``."""
    if not isinstance(tex, str) or not tex:
        return []

    results: list[tuple[int, int, str]] = []
    for s_start, s_end in _unprotected_slices(tex):
        segment = tex[s_start:s_end]
        tokens: list[tuple[int, int, str, str, bool, bool, bool]] = []
        for m in _WORD_TOKEN_RE.finditer(segment):
            raw = m.group(0)
            base, is_cand, is_strong, is_bridge = _token_info(raw)
            tokens.append((s_start + m.start(), s_start + m.end(), raw, base, is_cand, is_strong, is_bridge))

        n = len(tokens)
        i = 0
        while i < n:
            _, _, _, base, is_cand, is_strong, is_bridge = tokens[i]
            if not (is_cand or is_bridge):
                i += 1
                continue

            run = [tokens[i]]
            j = i + 1
            while j < n:
                prev_tok = run[-1]
                curr_tok = tokens[j]
                gap = tex[prev_tok[1] : curr_tok[0]]
                curr_is_cand, curr_is_bridge = curr_tok[4], curr_tok[6]
                # Allow a known function name (e.g. "max") to bridge two prose words,
                # or a single-letter article ("a", "I") to bridge inside a phrase.
                curr_is_fn_bridge = curr_tok[3] in KNOWN_MATH_FUNCTIONS and (
                    j + 1 < n
                    and (tokens[j + 1][4] or tokens[j + 1][6])
                    and _is_prose_gap(
                        tex[curr_tok[1] : tokens[j + 1][0]],
                        len(curr_tok[3]),
                        len(tokens[j + 1][3]),
                    )
                )
                if not (curr_is_cand or curr_is_bridge or curr_is_fn_bridge):
                    break
                if not _is_prose_gap(gap, len(prev_tok[3]), len(curr_tok[3])):
                    break
                run.append(curr_tok)
                j += 1

            # Trim leading/trailing single-letter bridges ("a", "I") unless adjacent to a strong word
            while run and not run[0][4]:
                if len(run) >= 2 and run[1][5]:
                    break
                run.pop(0)
            while run and not run[-1][4]:
                run.pop()

            cand_count = sum(1 for t in run if t[4])
            has_strong = any(t[5] for t in run)
            if run and (has_strong or cand_count >= 2):
                r_start, r_end = run[0][0], run[-1][1]
                results.append((r_start, r_end, tex[r_start:r_end]))
                i = j
            else:
                i += 1

    return results


def find_bare_words(tex: str) -> list[str]:
    """Return bare English word runs found outside ``\\text{...}`` in ``tex``."""
    return [snippet for _, _, snippet in find_bare_word_spans(tex)]


def _is_escaped_space(tex: str, space_idx: int) -> bool:
    bs = 0
    k = space_idx - 1
    while k >= 0 and tex[k] == "\\":
        bs += 1
        k -= 1
    return bs % 2 == 1


def wrap_bare_words_in_latex(tex: str) -> str:
    """Wrap detected bare English word runs in ``\\text{...}`` for safe KaTeX rendering."""
    if not isinstance(tex, str) or not tex:
        return tex
    spans = find_bare_word_spans(tex)
    if not spans:
        return tex

    expanded: list[list[int]] = []
    n = len(tex)
    for start, end, _ in spans:
        if start > 0 and tex[start - 1] == " " and not _is_escaped_space(tex, start - 1):
            start -= 1
        if end < n and tex[end] == " ":
            end += 1
        if expanded and start <= expanded[-1][1]:
            expanded[-1][1] = max(expanded[-1][1], end)
        else:
            expanded.append([start, end])

    parts: list[str] = []
    pos = 0
    for start, end in expanded:
        if start > pos:
            parts.append(tex[pos:start])
        parts.append(f"\\text{{{tex[start:end]}}}")
        pos = end
    if pos < n:
        parts.append(tex[pos:])
    return "".join(parts)
