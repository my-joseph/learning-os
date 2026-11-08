"""Central Quality Gate Configuration and Verification Logic.

All thresholds and structural rules for G1-G4 are defined in `QUALITY_RULES`
(and `INITIAL_PROPOSAL_RULES` for pre-calibration audit comparison).
Adjusting thresholds in `QUALITY_RULES` requires no changes to gate logic.
"""

from __future__ import annotations

from collections import Counter
import json
import math
import os
import re
import subprocess
import tempfile
from typing import Any, Callable

from code_engine.answer_check import check_answer as code_check_answer
from math_engine.answer_check import check_answer as math_check_answer


def _dispatch_check_answer(spec: dict[str, Any], raw_val: str, is_code: bool = False) -> dict[str, Any]:
    spec_type = spec.get("type", "")
    if is_code or spec_type in {"sequence", "line_fix", "text", "choice", "code_output"}:
        return code_check_answer(spec, raw_val)
    return math_check_answer(spec, raw_val)


class QualityError(Exception):
    """Raised when a problem or drill set fails a Quality Gate (G1-G4).

    Kept separate from `VerificationError` (which checks mathematical/code
    answer correctness). The message always specifies:
      - Gate ID (G1, G2, G3, G4)
      - Problem ID (e.g. Q01, or SET)
      - Specific reason for failure
    """

    def __init__(
        self,
        gate: str,
        problem_id: str,
        reason: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.gate = gate
        self.problem_id = problem_id
        self.reason = reason
        self.details = details or {}
        super().__init__(f"[{gate}] ข้อ {problem_id}: {reason}")


# ---------------------------------------------------------------------------
# Central Quality Gate Rules Configuration
# ---------------------------------------------------------------------------

# Initial proposal from specification (used in G5 audit comparison before calibration)
INITIAL_PROPOSAL_RULES: dict[str, Any] = {
    "GENERATION": {
        "max_retries": 12,
    },
    "G1": {
        "allowed_archetypes": {
            "code-tracing": {
                "requires_executable_snippet": True,
                "disallowed_languages": {"plain text", "plaintext", "text", "markdown", "ascii"},
                "description": "Must have executable JS codeSnippet whose actual stdout matches answerSpec.",
            },
            "problem-solving": {
                "requires_executable_snippet": False,
                "required_any_fields": [("starterCode", "solutionCode"), ("answerSpec",)],
                "description": "Code implementation with test suite or math problem-solving.",
            },
            "debugging": {
                "requires_executable_snippet": False,
                "required_any_fields": [
                    ("starterCode", "solutionCode"),
                    ("codeSnippet", "flaw"),
                    ("codeSnippet", "correctLine"),
                ],
                "description": "Buggy code or flawed derivation that requires identifying/fixing a defect.",
            },
            "refactoring": {
                "requires_executable_snippet": False,
                "required_any_fields": [("starterCode", "solutionCode")],
                "description": "Legacy code restructuring while preserving behavior and adding features.",
            },
            "project-based": {
                "requires_executable_snippet": False,
                "required_any_fields": [("starterCode", "solutionCode", "visibleTests", "hiddenTests")],
                "description": "Multi-method class/subsystem implementation with visible and hidden tests.",
            },
            "recall": {
                "requires_executable_snippet": False,
                "forbid_code_tracing_label": True,
                "description": "Pure conceptual or protocol recall without executable code tracing.",
            },
            "concept": {
                "requires_executable_snippet": False,
                "forbid_code_tracing_label": True,
                "description": "Conceptual understanding question without executable code tracing.",
            },
        },
        "tracing_code_types": {"predict-output", "code-tracing"},
        "node_timeout_sec": 5,
    },
    "G2": {
        "levels": {
            1: {
                "min_steps": 1,
                "max_steps": 2,
                "require_trap_or_flaw": False,
                "min_concepts": 1,
            },
            2: {
                "min_steps": 2,
                "max_steps": 4,
                "require_trap_or_flaw": False,
                "min_concepts": 1,
            },
            3: {
                "min_steps": 1,
                "max_steps": 6,
                "require_trap_or_flaw": True,
                "allowed_l3_categories": {
                    "Trap & Edge Case",
                    "State Management & Concurrency",
                    "Refactoring & Clean Architecture",
                    "Core Skill",
                },
                "allowed_l3_archetypes": {"debugging", "refactoring", "code-tracing"},
                "min_concepts": 1,
            },
            4: {
                "min_steps": 2,
                "max_steps": 8,
                "require_trap_or_flaw": False,
                "min_concepts": 2,
                "allow_constraint_alternative": True,
            },
        },
    },
    "G3": {
        "default_form": "direct",
        "max_same_fingerprint_per_set": 1,
        "allow_form_pool_relaxation": True,
        "warn_single_form_template": True,
        "single_form_warning_msg": "template นี้ผลิตได้โครงเดียว",
    },
    "G4": {
        "require_trap_value_when_trap_tag_present": True,
        "choice_min_options": 2,
        "choice_min_provenance_distractors": 2,
    },
    "G6": {
        "disallowed_patterns": ["+ -", "- -", "+-", "--", "^1", "x^0", "*1", "1x"],
    },
}

# Calibrated rules after G5 Audit of existing Math & PRG drills:
# Existing Math Level 1 templates consistently write 3 pedagogical steps
# (Formula -> Substitution -> Evaluation), while Code katas write 2-3 steps.
QUALITY_RULES: dict[str, Any] = {
    "GENERATION": {
        "max_retries": 12,
    },
    "G1": {
        "allowed_archetypes": {
            "code-tracing": {
                "requires_executable_snippet": True,
                "disallowed_languages": {"plain text", "plaintext", "text", "markdown", "ascii"},
                "description": "Must have executable JS codeSnippet whose actual stdout matches answerSpec.",
            },
            "problem-solving": {
                "requires_executable_snippet": False,
                "required_any_fields": [("starterCode", "solutionCode"), ("answerSpec",)],
                "description": "Code implementation with test suite or math problem-solving.",
            },
            "debugging": {
                "requires_executable_snippet": False,
                "required_any_fields": [
                    ("starterCode", "solutionCode"),
                    ("codeSnippet", "flaw"),
                    ("codeSnippet", "correctLine"),
                ],
                "description": "Buggy code or flawed derivation that requires identifying/fixing a defect.",
            },
            "refactoring": {
                "requires_executable_snippet": False,
                "required_any_fields": [("starterCode", "solutionCode")],
                "description": "Legacy code restructuring while preserving behavior and adding features.",
            },
            "project-based": {
                "requires_executable_snippet": False,
                "required_any_fields": [("starterCode", "solutionCode", "visibleTests", "hiddenTests")],
                "description": "Multi-method class/subsystem implementation with visible and hidden tests.",
            },
            "recall": {
                "requires_executable_snippet": False,
                "forbid_code_tracing_label": True,
                "description": "Pure conceptual or protocol recall without executable code tracing.",
            },
            "concept": {
                "requires_executable_snippet": False,
                "forbid_code_tracing_label": True,
                "description": "Conceptual understanding question without executable code tracing.",
            },
        },
        "tracing_code_types": {"predict-output", "code-tracing"},
        "node_timeout_sec": 5,
    },
    "G2": {
        "levels": {
            1: {
                # Calibrated from (1, 2) -> (1, 3) because standard math/code L1 explanations
                # show 3 steps: (1) formula/invariant, (2) substitution, (3) final answer.
                "min_steps": 1,
                "max_steps": 3,
                "require_trap_or_flaw": False,
                "min_concepts": 1,
            },
            2: {
                "min_steps": 2,
                "max_steps": 4,
                "require_trap_or_flaw": False,
                "min_concepts": 1,
            },
            3: {
                "min_steps": 2,
                "max_steps": 5,
                "require_trap_or_flaw": True,
                "allowed_l3_categories": {
                    "Trap & Edge Case",
                    "State Management & Concurrency",
                    "Refactoring & Clean Architecture",
                    "Core Skill",
                },
                "allowed_l3_archetypes": {"debugging", "refactoring", "code-tracing"},
                "min_concepts": 1,
            },
            4: {
                "min_steps": 2,
                "max_steps": 6,
                "require_trap_or_flaw": False,
                "min_concepts": 2,
                "allow_constraint_alternative": True,
            },
        },
    },
    "G3": {
        "default_form": "direct",
        "max_same_fingerprint_per_set": 1,
        "allow_form_pool_relaxation": True,
        "warn_single_form_template": True,
        "single_form_warning_msg": "template นี้ผลิตได้โครงเดียว",
    },
    "G4": {
        "require_trap_value_when_trap_tag_present": True,
        "choice_min_options": 2,
        "choice_min_provenance_distractors": 2,
    },
    "G6": {
        "disallowed_patterns": ["+ -", "- -", "+-", "--", "^1", "x^0", "*1", "1x"],
    },
}


# ---------------------------------------------------------------------------
# Gate G1: Type-Content Alignment
# ---------------------------------------------------------------------------

def _has_executable_js_code(snippet: str) -> bool:
    """Return True if snippet has non-comment, non-empty executable JS code."""
    if not snippet or not snippet.strip():
        return False
    lines = []
    in_block_comment = False
    for raw_line in snippet.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if in_block_comment:
            if "*/" in line:
                in_block_comment = False
                line = line.split("*/", 1)[1].strip()
            else:
                continue
        if line.startswith("/*"):
            if "*/" in line:
                line = line.split("*/", 1)[1].strip()
            else:
                in_block_comment = True
                continue
        if line.startswith("//"):
            continue
        if line:
            lines.append(line)
    if not lines:
        return False
    joined = "\n".join(lines)
    # Reject ASCII-art diagrams like "Client --- [ Packet 1 ] ---> Server"
    if re.search(r"---+\s*\[.*\]\s*--->", joined):
        return False
    return True


def _run_js_snippet(snippet: str, timeout_sec: int = 5) -> tuple[bool, str, str]:
    """Check syntax and execute JS snippet with Node.js, returning (ok, stdout, err)."""
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(snippet)
        tmp_path = f.name

    try:
        chk = subprocess.run(
            ["node", "--check", tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        if chk.returncode != 0:
            return False, "", f"JS SyntaxError: {chk.stderr.strip()}"

        res = subprocess.run(
            ["node", tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        if res.returncode != 0:
            return False, "", f"JS Runtime error: {res.stderr.strip()}"
        return True, res.stdout.strip(), ""
    except subprocess.TimeoutExpired:
        return False, "", f"JS execution timed out after {timeout_sec}s"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def check_gate_g1(prob: dict[str, Any], is_code: bool = False, rules: dict[str, Any] | None = None) -> dict[str, Any]:
    """G1: Verify that problem archetype/codeType matches actual content."""
    cfg = (rules or QUALITY_RULES)["G1"]
    pid = prob.get("id", "UNKNOWN")
    archetype = prob.get("archetype")
    code_type = prob.get("codeType")
    allowed_archetypes = cfg["allowed_archetypes"]

    # If archetype is explicitly provided, it must be in allowed_archetypes
    if archetype is not None and archetype not in allowed_archetypes:
        raise QualityError(
            "G1",
            pid,
            f"archetype '{archetype}' ไม่อยู่ในรายการที่อนุญาต ({sorted(allowed_archetypes.keys())})",
        )

    is_tracing = (
        archetype == "code-tracing"
        or code_type in cfg["tracing_code_types"]
    )

    if is_tracing:
        snippet = prob.get("codeSnippet", "")
        lang = (prob.get("language") or "javascript").strip().lower()
        disallowed_langs = allowed_archetypes["code-tracing"]["disallowed_languages"]
        if lang in disallowed_langs:
            raise QualityError(
                "G1",
                pid,
                f"โจทย์ code-tracing/predict-output ใช้ language='{lang}' ซึ่งไม่ใช่โค้ดที่รันได้ (ควรใช้ archetype 'recall' หรือ 'concept')",
            )
        if not _has_executable_js_code(snippet):
            raise QualityError(
                "G1",
                pid,
                "โจทย์ระบุเป็น code-tracing/predict-output แต่ codeSnippet ไม่มีโค้ดที่รันได้จริง (มีแต่คอมเมนต์หรือแผนภาพข้อความ ควรใช้ archetype 'recall' หรือ 'concept')",
            )
        ok, actual_stdout, err_msg = _run_js_snippet(snippet, timeout_sec=cfg.get("node_timeout_sec", 5))
        if not ok:
            raise QualityError(
                "G1",
                pid,
                f"โจทย์ code-tracing รัน codeSnippet ด้วย Node.js ไม่ผ่าน: {err_msg}",
            )
        if not actual_stdout:
            raise QualityError(
                "G1",
                pid,
                "โจทย์ code-tracing รัน codeSnippet แล้วไม่มีเอาต์พุตออกมาทาง stdout (ต้องได้คำตอบจากการรันโค้ดจริง)",
            )
        spec = prob.get("answerSpec", {})
        # If choice question in code-tracing, verify that either the correct option label or id matches stdout
        if spec.get("type") == "choice":
            correct_id = str(spec.get("correct", "")).strip()
            options = spec.get("options", [])
            correct_opt = next((o for o in options if str(o.get("id")).strip() == correct_id), None)
            correct_label = str(correct_opt.get("label", "")).strip() if correct_opt else ""
            norm_out = " ".join(actual_stdout.split()).lower()
            if norm_out != correct_label.lower() and norm_out != correct_id.lower():
                raise QualityError(
                    "G1",
                    pid,
                    f"ผลรัน codeSnippet จริงได้ '{actual_stdout}' ไม่ตรงกับตัวเลือกที่ถูก '{correct_label}' (ห้ามตั้งคำตอบที่ไม่ตรงกับผลรันโค้ด)",
                )
        else:
            chk = _dispatch_check_answer(spec, actual_stdout, is_code=True)
            if chk.get("verdict") != "correct":
                raise QualityError(
                    "G1",
                    pid,
                    f"ผลรัน codeSnippet จริงได้ '{actual_stdout}' ซึ่งไม่ตรงกับ answerSpec ({spec})",
                )
        return {"passed": True, "archetype": archetype or code_type, "verifiedByExecution": True}

    # If code problem without archetype
    if is_code and not archetype and not code_type:
        raise QualityError("G1", pid, "โจทย์โปรแกรมมิ่งต้องระบุ archetype หรือ codeType ที่ชัดเจน")

    # Check required fields for other archetypes when archetype is specified
    if archetype in allowed_archetypes:
        arch_rule = allowed_archetypes[archetype]
        req_groups = arch_rule.get("required_any_fields", [])
        if req_groups:
            matched_group = False
            for group in req_groups:
                if all(bool(prob.get(field)) for field in group):
                    matched_group = True
                    break
            if not matched_group:
                raise QualityError(
                    "G1",
                    pid,
                    f"archetype '{archetype}' ขาดฟิลด์บังคับ ({req_groups})",
                )

    return {"passed": True, "archetype": archetype or "math-standard"}


# ---------------------------------------------------------------------------
# Gate G2: Level-Structure Alignment
# ---------------------------------------------------------------------------

def _has_verifiable_trap_or_flaw(prob: dict[str, Any]) -> bool:
    """Return True if problem has a verifiable flaw, debugging defect, or trap structure."""
    v = prob.get("verify") or {}
    # 1. Explicit flaw dict or divergedStep / wrongStep
    flaw = prob.get("flaw") or v.get("flaw")
    if isinstance(flaw, dict) and (
        flaw.get("wrongStep") is not None
        or flaw.get("divergedStep") is not None
        or flaw.get("flawed_value") is not None
        or flaw.get("correctLine") is not None
    ):
        return True
    if prob.get("divergedStep") is not None or prob.get("correctLine") is not None:
        return True
    if v.get("buggy_code") and v.get("fixed_code"):
        return True

    # 2. Code debugging / refactoring problem with starterCode != solutionCode and tests
    archetype = prob.get("archetype") or prob.get("codeType")
    if archetype in {"debugging", "refactoring"} and prob.get("starterCode") and prob.get("solutionCode"):
        if prob.get("starterCode", "").strip() != prob.get("solutionCode", "").strip():
            return True

    # 3. Trap category or trapValue explicitly verifiable
    trap_val = prob.get("trapValue") if "trapValue" in prob else v.get("trapValue")
    if trap_val is not None and prob.get("commonTrapTag"):
        return True

    if prob.get("category") == "Trap & Edge Case" and prob.get("commonTrapTag"):
        return True

    return False


def _count_concepts_or_constraints(prob: dict[str, Any]) -> tuple[int, bool]:
    """Return (concept_count, has_extra_constraint) for L4 verification."""
    refs = prob.get("references") or []
    comps = prob.get("competencies") or []
    concept_count = max(len(set(refs)), len(set(comps)), 1)

    has_constraint = (
        len(refs) >= 2
        or len(comps) >= 2
        or bool(prob.get("hiddenTests") and prob.get("visibleTests"))
        or prob.get("category") == "Interleaved Synthesis"
        or bool(prob.get("constraints"))
    )
    return concept_count, has_constraint


_TAXONOMY_CACHE: dict[str, Any] | None = None


def load_skills_taxonomy(path: str = "skills_taxonomy.json") -> dict[str, Any]:
    global _TAXONOMY_CACHE
    if _TAXONOMY_CACHE is not None:
        return _TAXONOMY_CACHE
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                _TAXONOMY_CACHE = data.get("skills", data)
                return _TAXONOMY_CACHE
        except Exception:
            pass
    return {}


def check_gate_g2(prob: dict[str, Any], rules: dict[str, Any] | None = None) -> dict[str, Any]:
    """G2: Verify that problem difficulty `level` aligns with its actual structure."""
    cfg = (rules or QUALITY_RULES)["G2"]
    pid = prob.get("id", "UNKNOWN")
    level = prob.get("level")
    if level not in cfg["levels"]:
        raise QualityError("G2", pid, f"ไม่พบเกณฑ์สำหรับระดับความยาก level={level}")

    l_rule = cfg["levels"][level]
    steps = prob.get("steps") or []
    step_count = len(steps)

    # Check skill-specific g2_profile if available, else default to calibrated levels
    skill_id = prob.get("skill")
    taxonomy = load_skills_taxonomy()
    skill_entry = taxonomy.get(skill_id) if skill_id else None

    if skill_entry and "g2_profile" in skill_entry:
        prof = skill_entry["g2_profile"].get(str(level)) or skill_entry["g2_profile"].get(level)
        if prof:
            min_s = prof["min_steps"]
            max_s = prof["max_steps"]
        else:
            min_s = l_rule["min_steps"]
            max_s = l_rule["max_steps"]
    else:
        min_s = l_rule["min_steps"]
        max_s = l_rule["max_steps"]

    # Check L3 trap/flaw requirement first if level == 3 so error message is comprehensive
    has_trap_flaw = _has_verifiable_trap_or_flaw(prob)
    if l_rule.get("require_trap_or_flaw") and not has_trap_flaw:
        raise QualityError(
            "G2",
            pid,
            f"ติดป้าย L{level} แต่โครงสร้างจริงไม่มี trap/flaw/debug หรือจุดผิดที่ตรวจได้ (steps={step_count}, has_trap=False)",
        )

    if not (min_s <= step_count <= max_s):
        source_note = f" (skill '{skill_id}')" if (skill_entry and "g2_profile" in skill_entry) else ""
        raise QualityError(
            "G2",
            pid,
            f"ติดป้าย L{level} แต่มี {step_count} steps ซึ่งไม่อยู่ในเกณฑ์ L{level}{source_note} ({min_s}-{max_s} steps)",
        )

    if level == 4:
        concept_count, has_constraint = _count_concepts_or_constraints(prob)
        min_c = l_rule.get("min_concepts", 2)
        allow_alt = l_rule.get("allow_constraint_alternative", True)
        if concept_count < min_c and not (allow_alt and has_constraint):
            raise QualityError(
                "G2",
                pid,
                f"ติดป้าย L4 แต่ใช้เพียง {concept_count} concept และไม่มี constraint เพิ่มเติม (ต้องใช้ >= {min_c} concepts หรือมี constraint เพิ่ม)",
            )

    return {
        "passed": True,
        "level": level,
        "stepCount": step_count,
        "hasTrapOrFlaw": has_trap_flaw,
        "skill": skill_id,
        "stepRange": (min_s, max_s),
    }


# ---------------------------------------------------------------------------
# Gate G3: Anti-Skeleton Duplication (Set-Level)
# ---------------------------------------------------------------------------

def normalize_skeleton_text(text: str) -> str:
    """Replace all numbers (integers, decimals) with '#' and normalize whitespace."""
    if not text:
        return ""
    # Replace floating point and integer numbers with '#'
    s = re.sub(r"\d+(?:\.\d+)?", "#", text)
    # Collapse multiple '#' separated only by spaces if any, and normalize whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s


def compute_fingerprint(prob: dict[str, Any], template_key: str | None = None, default_form: str = "direct") -> str:
    """Compute structural fingerprint = templateKey + form + normalized skeleton.

    Ensures problems from the same template/trap and form that only change numbers
    (e.g. `90 - 37` and `180 - 124` in DRL-MTH-T01-C12-04.json) produce the exact
    same fingerprint.
    """
    tpl_key = (
        template_key
        or prob.get("templateKey")
        or prob.get("commonTrapTag")
        or prob.get("category")
        or "unknown_tpl"
    )
    form = str(prob.get("form") or default_form).strip()

    # For math problems with `plainText`, `plainText` represents the mathematical expression skeleton
    # (e.g. "90 - 37" -> "# - #", "180 - 124" -> "# - #").
    # If `plainText` is missing, fall back to `codeSnippet` or `prompt`.
    raw_skeleton_source = (
        prob.get("plainText")
        or prob.get("codeSnippet")
        or prob.get("entryPoint")
        or prob.get("prompt")
        or ""
    )
    norm_skeleton = normalize_skeleton_text(str(raw_skeleton_source))
    return f"{tpl_key}|{form}|{norm_skeleton}"


def check_gate_g3_set(
    problems: list[dict[str, Any]],
    available_forms_count: int | None = None,
    rules: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """G3: Verify that no fingerprint repeats beyond the allowed quota within a single set."""
    cfg = (rules or QUALITY_RULES)["G3"]
    default_form = cfg.get("default_form", "direct")
    max_allowed = cfg.get("max_same_fingerprint_per_set", 1)

    if (
        cfg.get("allow_form_pool_relaxation", True)
        and available_forms_count is not None
        and available_forms_count > 0
        and len(problems) > available_forms_count
    ):
        max_allowed = max(max_allowed, math.ceil(len(problems) / available_forms_count))

    seen: dict[str, list[str]] = {}
    duplicates: list[tuple[str, str, str]] = []

    for prob in problems:
        pid = prob.get("id", "UNKNOWN")
        if not prob.get("form"):
            prob["form"] = default_form
        fp = prob.get("fingerprint") or compute_fingerprint(prob, default_form=default_form)
        prob["fingerprint"] = fp
        seen.setdefault(fp, []).append(pid)
        if len(seen[fp]) > max_allowed:
            first_pid = seen[fp][0]
            duplicates.append((pid, first_pid, fp))

    if duplicates:
        dup_pid, first_pid, dup_fp = duplicates[0]
        raise QualityError(
            "G3",
            dup_pid,
            f"โครงสร้างโจทย์ซ้ำกับข้อ {first_pid} ในชุดเดียวกัน (fingerprint='{dup_fp}' เกินโควตาสูงสุด {max_allowed} ครั้ง/ชุด)",
            details={"duplicates": duplicates, "maxAllowed": max_allowed},
        )

    return {
        "passed": True,
        "uniqueFingerprints": len(seen),
        "totalProblems": len(problems),
        "maxAllowedPerFingerprint": max_allowed,
    }


# ---------------------------------------------------------------------------
# Gate G4: Distractor / Trap Provenance
# ---------------------------------------------------------------------------

def _extract_correct_display_or_value(spec: dict[str, Any], prob: dict[str, Any]) -> str:
    t = spec.get("type")
    if t == "choice":
        return str(spec.get("correct", "")).strip()
    if t == "number":
        return str(spec.get("value", ""))
    if t == "pair":
        return f"{spec.get('re')},{spec.get('im')}"
    if t == "expression":
        return str(spec.get("value", ""))
    if t == "text":
        acc = spec.get("accepted") or []
        return str(acc[0]) if acc else str(prob.get("answerPlain", ""))
    if t == "vector":
        comps = spec.get("components") or spec.get("values")
        if comps:
            return f"<{', '.join(str(c) for c in comps)}>"
        return str(prob.get("answerPlain", ""))
    return str(prob.get("answerPlain", ""))


def check_gate_g4(prob: dict[str, Any], is_code: bool = False, rules: dict[str, Any] | None = None) -> dict[str, Any]:
    """G4: Verify that trapTags have real computed trapValues != correct answer, and MCQ distractors have provenance."""
    cfg = (rules or QUALITY_RULES)["G4"]
    pid = prob.get("id", "UNKNOWN")
    spec = prob.get("answerSpec") or {}
    v = prob.get("verify") or {}
    trap_tag = prob.get("commonTrapTag") or spec.get("commonTrapTag")

    weak_distractors = 0
    provenance_distractors = 0

    # 1. Multiple-Choice option checks
    if spec.get("type") == "choice":
        options = spec.get("options") or []
        if len(options) < cfg.get("choice_min_options", 2):
            raise QualityError("G4", pid, f"โจทย์ปรนัยต้องมีตัวเลือกอย่างน้อย {cfg.get('choice_min_options', 2)} ตัวเลือก")

        correct_id = str(spec.get("correct", "")).strip()
        seen_labels: dict[str, str] = {}
        correct_opt = next((o for o in options if str(o.get("id")).strip() == correct_id), None)
        if not correct_opt:
            raise QualityError("G4", pid, f"ไม่พบตัวเลือกที่ถูก '{correct_id}' ใน options")

        correct_label = str(correct_opt.get("label", "")).strip().lower()

        for opt in options:
            oid = str(opt.get("id", "")).strip()
            label = str(opt.get("label", "")).strip()
            norm_lbl = label.lower()
            if not label:
                raise QualityError("G4", pid, f"ตัวเลือก {oid} ไม่มีข้อความ label")
            if norm_lbl in seen_labels:
                raise QualityError(
                    "G4",
                    pid,
                    f"ตัวเลือก {oid} ซ้ำกับตัวเลือก {seen_labels[norm_lbl]} ('{label}')",
                )
            seen_labels[norm_lbl] = oid

            if oid != correct_id:
                if norm_lbl == correct_label:
                    raise QualityError(
                        "G4",
                        pid,
                        f"ตัวหลอก {oid} มีค่าตรงกับคำตอบที่ถูก ('{label}')",
                    )
                if opt.get("trapTag") or opt.get("mistakeTag") or opt.get("provenance"):
                    provenance_distractors += 1
                else:
                    weak_distractors += 1

        min_prov = cfg.get("choice_min_provenance_distractors", 2)
        if provenance_distractors < min_prov:
            raise QualityError(
                "G4",
                pid,
                f"โจทย์ปรนัยมีตัวหลอกที่ผูกกับ trapTag/ที่มาเพียง {provenance_distractors} ตัว (เกณฑ์กำหนดอย่างน้อย {min_prov} ตัว; weakDistractors={weak_distractors})",
                details={"weakDistractors": weak_distractors, "provenanceDistractors": provenance_distractors},
            )

    # 2. Trap Tag -> Trap Value provenance check
    trap_val = prob.get("trapValue") if "trapValue" in prob else v.get("trapValue")
    if trap_tag and cfg.get("require_trap_value_when_trap_tag_present", True):
        if spec.get("type") == "code_output":
            if trap_val is None and not v.get("trapCode"):
                raise QualityError(
                    "G4",
                    pid,
                    f"ระบุ commonTrapTag='{trap_tag}' แต่ไม่ได้ส่ง trapValue หรือ trapCode ที่คำนวณจากความผิดพลาดจริงมาให้ตรวจ",
                )
        else:
            if trap_val is None:
                raise QualityError(
                    "G4",
                    pid,
                    f"ระบุ commonTrapTag='{trap_tag}' แต่ไม่มี trapValue ที่คำนวณจากสูตรผิดพลาดของ trap นั้น",
                )

    if trap_val is not None:
        trap_str = str(trap_val).strip()
        correct_str = _extract_correct_display_or_value(spec, prob).strip()
        if trap_str.lower() == correct_str.lower():
            raise QualityError(
                "G4",
                pid,
                f"ค่า trapValue ('{trap_val}') ของ trap '{trap_tag or 'trap'}' เท่ากับคำตอบที่ถูก ('{correct_str}')",
            )
        chk = _dispatch_check_answer(spec, trap_str, is_code=is_code)
        if chk.get("verdict") == "correct":
            raise QualityError(
                "G4",
                pid,
                f"ค่า trapValue ('{trap_val}') ของ trap '{trap_tag or 'trap'}' ถูกตรวจด้วย check_answer แล้วได้ผลว่า 'correct' (ซ้ำกับคำตอบที่ถูก)",
            )

    return {
        "passed": True,
        "trapTag": trap_tag,
        "trapValueVerified": trap_val is not None,
        "weakDistractors": weak_distractors,
        "provenanceDistractors": provenance_distractors,
    }


# ---------------------------------------------------------------------------
# Gate G6: Presentation Formatting Quality (No Sloppy Signs or Unsimplified Exponents)
# ---------------------------------------------------------------------------

def check_gate_g6(
    prob: dict[str, Any],
    is_code: bool = False,
    rules: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """G6: Verify that learner-visible fields contain no sloppy math or unsimplified expressions.

    Checked fields:
      - prompt
      - display, plainText, answerDisplay, answerPlain, inputHint, checkpointHint
      - answerSpec.display
      - step.latex, step.explain (all steps)
      - opt.label, opt.latex, opt.display (all options)

    Disallowed formatting patterns:
      - "+ -", "+-" (unless parenthesized like + (-3))
      - "- -", "--" (unless parenthesized, markdown rules '---', or code decrement 'i--')
      - "^1" (unsimplified degree 1 exponent like x^1, i^1)
      - "x^0" (unsimplified degree 0 exponent)
      - "*1" (unsimplified multiplication by 1, e.g. x*1, excluding markdown bolding **1)
      - "1x" (unsimplified coefficient 1 on variable x, e.g. 1x, -1x)
    """
    pid = prob.get("id", "UNKNOWN")
    visible_fields: list[tuple[str, str]] = []

    def _add_field(name: str, val: Any) -> None:
        if isinstance(val, str) and val.strip():
            visible_fields.append((name, val))

    _add_field("prompt", prob.get("prompt"))
    _add_field("display", prob.get("display"))
    _add_field("plainText", prob.get("plainText"))
    _add_field("answerDisplay", prob.get("answerDisplay"))
    _add_field("answerPlain", prob.get("answerPlain"))
    _add_field("inputHint", prob.get("inputHint"))
    _add_field("checkpointHint", prob.get("checkpointHint"))

    spec = prob.get("answerSpec") or {}
    _add_field("answerSpec.display", spec.get("display"))

    for idx, st in enumerate(prob.get("steps") or []):
        _add_field(f"steps[{idx}].latex", st.get("latex"))
        _add_field(f"steps[{idx}].explain", st.get("explain"))

    for idx, opt in enumerate(spec.get("options") or []):
        _add_field(f"options[{idx}].label", opt.get("label"))
        _add_field(f"options[{idx}].latex", opt.get("latex"))
        _add_field(f"options[{idx}].display", opt.get("display"))

    defects: list[dict[str, str]] = []

    for fname, raw_text in visible_fields:
        # Pre-clean allowed symbols:
        # 1. Markdown tables / horizontal rules (3 or more dashes)
        s_clean = re.sub(r"-{3,}", " ", raw_text)

        # 2. In code, allowed decrement operators e.g. i--, count--, --i
        if is_code:
            s_clean = re.sub(r"\b[a-zA-Z_$][a-zA-Z0-9_$]*--", " ", s_clean)
            s_clean = re.sub(r"--[a-zA-Z_$][a-zA-Z0-9_$]*\b", " ", s_clean)

        # 3. Strip parenthesized subexpressions for +/- checks (e.g. + (-3), (- -))
        clean_paren = s_clean
        while "(" in clean_paren and ")" in clean_paren:
            new_s = re.sub(r"\([^()]*\)", "(PAREN)", clean_paren)
            if new_s == clean_paren:
                break
            clean_paren = new_s

        # Pattern 1: "+ -" or "+-"
        m = re.search(r"\+\s*-", clean_paren)
        if m:
            defects.append({"field": fname, "pattern": "+ -", "snippet": raw_text[:80]})
            continue

        # Pattern 2: "- -" or "--"
        m = re.search(r"-\s*-", clean_paren)
        if m:
            defects.append({"field": fname, "pattern": "- -", "snippet": raw_text[:80]})
            continue

        # Pattern 3: "^1" (unsimplified exponent 1: braced ^{1} or unbraced ^1 not followed by digit or letter)
        m = re.search(r"(\^\{\s*\+?1\s*\}|\^\+?1(?![0-9a-zA-Z_]))", raw_text)
        if m:
            defects.append({"field": fname, "pattern": "^1", "snippet": raw_text[:80]})
            continue

        # Pattern 4: "x^0" (unsimplified exponent 0 on x)
        m = re.search(r"(x\^\{\s*0\s*\}|x\^0(?![0-9a-zA-Z]))", raw_text)
        if m:
            defects.append({"field": fname, "pattern": "x^0", "snippet": raw_text[:80]})
            continue

        # Pattern 5: "*1" (multiplying by 1, excluding markdown bolding **1 and decimals like 2*1.5)
        m = re.search(r"(?<!\*)\*\s*1(?![0-9a-zA-Z]|\.\d)", raw_text)
        if m:
            defects.append({"field": fname, "pattern": "*1", "snippet": raw_text[:80]})
            continue

        # Pattern 6: "1x" (unsimplified coefficient 1 on x, excluding decimals like 0.1x)
        m = re.search(r"(?<![0-9a-zA-Z_.])1x(?![a-zA-Z0-9_])", raw_text)
        if m:
            defects.append({"field": fname, "pattern": "1x", "snippet": raw_text[:80]})
            continue

    if defects:
        first_d = defects[0]
        raise QualityError(
            "G6",
            pid,
            f"รูปแบบข้อความไม่ผ่านเกณฑ์: พบรูปแบบ '{first_d['pattern']}' ในฟิลด์ '{first_d['field']}' ({first_d['snippet']})",
            details={"defects": defects, "totalDefects": len(defects)},
        )

    return {
        "passed": True,
        "fieldsChecked": len(visible_fields),
    }


# ---------------------------------------------------------------------------
# Unified Problem & Set Quality Gate Runner
# ---------------------------------------------------------------------------

def verify_quality_gates(
    prob: dict[str, Any],
    is_code: bool = False,
    rules: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run G1, G2, G4, G6 on a single problem and attach `form`, `fingerprint`, and `qualityGates`."""
    active_rules = rules or QUALITY_RULES
    default_form = active_rules["G3"].get("default_form", "direct")
    if not prob.get("form"):
        prob["form"] = default_form
    prob["fingerprint"] = compute_fingerprint(prob, default_form=default_form)

    # Verification level (defaults to machine-verified)
    verif_level = prob.get("verificationLevel", "machine-verified")
    prob["verificationLevel"] = verif_level

    g1_res = check_gate_g1(prob, is_code=is_code, rules=active_rules)
    g2_res = check_gate_g2(prob, rules=active_rules)
    g4_res = check_gate_g4(prob, is_code=is_code, rules=active_rules)
    g6_res = check_gate_g6(prob, is_code=is_code, rules=active_rules)

    gates_report = {
        "G1": g1_res,
        "G2": g2_res,
        "G4": g4_res,
        "G6": g6_res,
        "verificationLevel": verif_level,
        "weakDistractors": g4_res.get("weakDistractors", 0),
    }
    prob["qualityGates"] = gates_report
    return gates_report
    prob["qualityGates"] = gates_report
    return gates_report


def generate_with_quality_retries(
    build_set_fn: Callable[[int], tuple[list[dict[str, Any]], int | None]],
    base_seed: int,
    rules: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Execute `build_set_fn(seed)` with up to `max_retries` (12) on QualityError.

    If all retries fail, raises QualityError reporting which gate failed most often.
    Never silently lowers quality thresholds.
    """
    active_rules = rules or QUALITY_RULES
    max_retries = active_rules.get("GENERATION", {}).get("max_retries", 12)
    gate_failures: Counter[str] = Counter()
    last_error: QualityError | None = None

    for attempt in range(max_retries):
        current_seed = base_seed + attempt * 9973
        try:
            problems, available_forms_count = build_set_fn(current_seed)
            g3_res = check_gate_g3_set(
                problems,
                available_forms_count=available_forms_count,
                rules=active_rules,
            )
            for p in problems:
                p.setdefault("qualityGates", {})["G3"] = {
                    "passed": True,
                    "fingerprint": p.get("fingerprint"),
                    "maxAllowedPerFingerprint": g3_res["maxAllowedPerFingerprint"],
                }
            return problems
        except QualityError as exc:
            gate_failures[exc.gate] += 1
            last_error = exc

    most_common_gate, most_common_count = gate_failures.most_common(1)[0]
    breakdown = ", ".join(f"{g}: {c} ครั้ง" for g, c in gate_failures.most_common())
    raise QualityError(
        most_common_gate,
        last_error.problem_id if last_error else "SET",
        f"ลองสุ่ม seed ใหม่ครบ {max_retries} ครั้งแล้วยังไม่ผ่าน Quality Gate "
        f"(ด่านที่ตกบ่อยสุดคือ {most_common_gate} [{most_common_count}/{max_retries} ครั้ง]; สถิติรวม: {breakdown}) — "
        f"สาเหตุล่าสุด: {last_error.reason if last_error else 'Unknown'}",
        details={"gateFailures": dict(gate_failures), "maxRetries": max_retries},
    )
