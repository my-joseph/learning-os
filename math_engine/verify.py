# -*- coding: utf-8 -*-
"""
Pre-output verification for Math drill problems. Nothing is written to disk unless every check passes.

Checks per problem:
 1. Mathematical correctness
    - every step `val` equals verify.source; every step `eq` pair is equal (SymPy)
    - answerSpec value equals verify.source (complex / number / expression), or verify.tuple (tuple)
    - find-the-flaw: lines before `firstWrong` equal the source, the flawed line does NOT
 2. Checker round-trip: check_answer(answerSpec, answerPlain) must return "correct"
 3. Render safety (Zero Unrendered Syntax): no Markdown (**, __, backticks), no [[ID]] tokens,
    no \\displaystyle, no Thai text, balanced $ delimiters, all references resolvable.
"""
import re

import sympy as sp

from math_engine.answer_check import check_answer, is_equal, to_expr
from quality_rules import QualityError, check_gate_g3_set, verify_quality_gates

BANNED = [
    (re.compile(r"\*\*"), "Markdown bold (**)"),
    (re.compile(r"__"), "Markdown underscore emphasis (__)"),
    (re.compile(r"`"), "Markdown code backtick"),
    (re.compile(r"\[\[[^\]]*\]\]"), "raw [[ID]] token"),
    (re.compile(r"\\displaystyle"), "\\displaystyle (block mode already uses display style)"),
    (re.compile(r"[\u0E00-\u0E7F]"), "non-English (Thai) text"),
]
TEXT_FIELDS = ["prompt", "checkpointHint", "context", "inputHint", "category"]
LATEX_FIELDS = ["display", "answerDisplay"]


class VerificationError(AssertionError):
    pass


def _fail(pid, msg):
    raise VerificationError(f"[{pid}] {msg}")


def check_text_safety(pid, label, text, is_latex=False):
    if not isinstance(text, str):
        return
    for rx, what in BANNED:
        if is_latex and what.startswith("Markdown underscore"):
            continue  # LaTeX subscripts may legitimately contain __ only in odd cases; skip
        if rx.search(text):
            _fail(pid, f"{label} contains {what}: {text[:120]}")
    if not is_latex:
        if text.count("$") % 2 != 0:
            _fail(pid, f"{label} has unbalanced $ delimiters: {text[:120]}")
    else:
        if "$" in text:
            _fail(pid, f"{label} is a LaTeX field and must not contain $ delimiters: {text[:120]}")


def verify_problem(p, id_map=None, rules=None):
    pid = p.get("id", p.get("templateKey", "?"))
    v = p.get("verify", {})
    vars_list = p.get("answerSpec", {}).get("variables") or p.get("variables") or ["x"]
    src = to_expr(v["source"], variables=vars_list) if "source" in v else None

    # 1. Steps
    if not p.get("steps"):
        _fail(pid, "no solution steps")
    checked = 0
    has_machine_tags = any(("val" in st or "eq" in st) for st in p["steps"])
    for i, st in enumerate(p["steps"], 1):
        if "val" in st:
            if src is None:
                _fail(pid, f"step {i} has val but problem has no verify.source")
            if not is_equal(to_expr(st["val"], variables=vars_list), src, variables=vars_list):
                _fail(pid, f"step {i} value {st['val']} != source {v['source']}")
            checked += 1
        if "eq" in st:
            l, r = st["eq"]
            if not is_equal(to_expr(l, variables=vars_list), to_expr(r, variables=vars_list), variables=vars_list):
                _fail(pid, f"step {i} equality fails: {l} != {r}")
            checked += 1
        check_text_safety(pid, f"step {i} explain", st["explain"])
        check_text_safety(pid, f"step {i} latex", st["latex"], is_latex=True)
    if ("verify" in p or has_machine_tags) and checked == 0:
        _fail(pid, "no step carries a machine check (val / eq)")

    # 2. Answer vs source
    spec = p["answerSpec"]
    t = spec["type"]
    if t in ("complex", "number", "expression") and src is not None:
        if not is_equal(to_expr(spec["value"], spec.get("variables")), src, spec.get("variables") if t == "expression" else None):
            _fail(pid, f"answer {spec['value']} != source {v['source']}")
    elif t == "tuple":
        exprs = [to_expr(e, variables=vars_list) for e in v["tuple"]]
        for got, want in zip(spec["values"], exprs):
            if not is_equal(to_expr(got, variables=vars_list), want, variables=vars_list):
                _fail(pid, f"tuple component {got} != {want}")
    elif t == "vector":
        expected_comps = spec.get("components") or spec.get("values") or []
        if "vector" in v:
            v_comps = [to_expr(e, variables=vars_list) for e in v["vector"]]
            for got, want in zip(expected_comps, v_comps):
                if not is_equal(to_expr(got, variables=vars_list), want, variables=vars_list):
                    _fail(pid, f"vector component {got} != {want}")
        elif src is not None:
            v_mat = to_expr(src)
            for i, got in enumerate(expected_comps):
                if not is_equal(to_expr(got, variables=vars_list), v_mat[i], variables=vars_list):
                    _fail(pid, f"vector component {got} != {v_mat[i]}")
    elif t == "choice" and "flaw" in v:
        fl = v["flaw"]
        k = fl["firstWrong"]
        for idx, val in enumerate(fl["values"], 1):
            if val is None:
                continue
            same = is_equal(to_expr(val, variables=vars_list), src, variables=vars_list)
            if idx < k and not same:
                _fail(pid, f"flaw line {idx} should be correct")
            if idx == k and same:
                _fail(pid, f"flaw line {idx} is supposed to be wrong but equals the source")
        if str(k) != str(spec["correct"]):
            _fail(pid, "choice answer does not match firstWrong")

    # 3. Checker round-trip
    res = check_answer(spec, p["answerPlain"])
    if res["verdict"] != "correct":
        _fail(pid, f"checker rejects canonical answer {p['answerPlain']!r}: {res}")

    # 4. Render safety
    for f in TEXT_FIELDS:
        check_text_safety(pid, f, p.get(f))
    for f in LATEX_FIELDS:
        check_text_safety(pid, f, p.get(f), is_latex=True)
    for ref in p.get("references", []):
        if id_map is not None and ref not in id_map:
            _fail(pid, f"reference {ref} not found in id_map.json")

    # 5. Anti-leakage: inputHint must never leak the exact answer value
    hint = p.get("inputHint") or ""
    ans_val = str(p.get("answerSpec", {}).get("value", "")).strip()
    ans_plain = str(p.get("answerPlain", "")).strip()
    if hint and (ans_val or ans_plain):
        for leaked in set([ans_val, ans_plain]):
            if leaked and leaked not in ["1", "i", "-1", "-i", "choice"]:
                if re.search(r'(?<![0-9a-zA-Z])' + re.escape(leaked) + r'(?![0-9a-zA-Z])', hint):
                    _fail(pid, f"inputHint leaks exact answer {leaked!r}: {hint!r}")

    # 6. Quality Gates (G1, G2, G4)
    verify_quality_gates(p, is_code=False, rules=rules)
    return True


def verify_set(problems, id_map=None, available_forms_count=None, rules=None):
    """Verify all problems in a drill set (including G1, G2, G4) plus set-level G3 deduplication."""
    for p in problems:
        verify_problem(p, id_map=id_map, rules=rules)
    g3_res = check_gate_g3_set(problems, available_forms_count=available_forms_count, rules=rules)
    for p in problems:
        p.setdefault("qualityGates", {})["G3"] = {
            "passed": True,
            "fingerprint": p.get("fingerprint"),
            "maxAllowedPerFingerprint": g3_res["maxAllowedPerFingerprint"],
        }
    return True


def verify_tags(tags):
    for t in tags:
        check_text_safety("mistakeTags", t["id"], t["label"])
        if "," in t["name"]:
            raise VerificationError(f"Notion multi-select name cannot contain commas: {t['name']}")
        check_text_safety("mistakeTags", t["id"] + ".name", t["name"])
