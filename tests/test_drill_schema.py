"""Committed drill JSON files must match the documented schema in `practice-studio/src/types/drill.ts`."""

from __future__ import annotations

import glob
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DRILL_TS_PATH = ROOT / "practice-studio" / "src" / "types" / "drill.ts"
REDACT_TS_PATH = ROOT / "practice-studio" / "src" / "lib" / "redact.ts"
PATHS = sorted(glob.glob("drills/data/*/DRL-*.json"))


def _extract_ts_interface_fields(ts_text: str, interface_name: str) -> set[str]:
    """Extract top-level property names from a TypeScript `export interface <Name> ... { ... }`."""
    header_re = re.compile(rf"export\s+interface\s+{re.escape(interface_name)}\b[^{{]*\{{", re.DOTALL)
    match = header_re.search(ts_text)
    assert match is not None, f"Interface '{interface_name}' not found in {DRILL_TS_PATH}"

    start = match.end()
    depth = 1
    idx = start
    while idx < len(ts_text) and depth > 0:
        ch = ts_text[idx]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        idx += 1
    body = ts_text[start : idx - 1]

    fields: set[str] = set()
    nested = 0
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if nested == 0:
            prop_match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\??\s*:", line)
            if prop_match:
                fields.add(prop_match.group(1))
        nested += line.count("{") - line.count("}")
    return fields


def _extract_always_stripped_fields(redact_text: str) -> set[str]:
    match = re.search(
        r"export\s+const\s+ALWAYS_STRIPPED_PROBLEM_FIELDS\s*=\s*\[(.*?)\]\s*as\s+const", redact_text, re.DOTALL
    )
    assert match is not None, f"ALWAYS_STRIPPED_PROBLEM_FIELDS not found in {REDACT_TS_PATH}"
    return set(re.findall(r'"([A-Za-z_][A-Za-z0-9_]*)"', match.group(1)))


_DRILL_TS = DRILL_TS_PATH.read_text(encoding="utf-8")
_REDACT_TS = REDACT_TS_PATH.read_text(encoding="utf-8")

DOCUMENTED_DRILL_FIELDS = _extract_ts_interface_fields(_DRILL_TS, "DrillDocument") | _extract_ts_interface_fields(
    _DRILL_TS, "RawDrillDocument"
)
DOCUMENTED_PROBLEM_FIELDS = _extract_ts_interface_fields(_DRILL_TS, "Problem") | _extract_ts_interface_fields(
    _DRILL_TS, "RawProblem"
)
DOCUMENTED_SPEC_FIELDS = _extract_ts_interface_fields(_DRILL_TS, "AnswerSpec") | _extract_ts_interface_fields(
    _DRILL_TS, "RawAnswerSpec"
)
DOCUMENTED_OPTION_FIELDS = _extract_ts_interface_fields(_DRILL_TS, "ChoiceOption") | _extract_ts_interface_fields(
    _DRILL_TS, "RawChoiceOption"
)
DOCUMENTED_STEP_FIELDS = _extract_ts_interface_fields(_DRILL_TS, "Step")


def test_drill_ts_exports_raw_and_redacted_types_and_covers_stripped_fields() -> None:
    for type_name in (
        "RawDrillDocument",
        "RedactedDrillDocument",
        "RawProblem",
        "RedactedProblem",
        "RawAnswerSpec",
        "RedactedAnswerSpec",
        "RawChoiceOption",
        "RedactedChoiceOption",
    ):
        assert re.search(rf"export\s+(?:interface|type)\s+{type_name}\b", _DRILL_TS), (
            f"{type_name} must be exported from practice-studio/src/types/drill.ts"
        )

    stripped = _extract_always_stripped_fields(_REDACT_TS)
    undocumented_stripped = sorted(stripped - DOCUMENTED_PROBLEM_FIELDS)
    assert undocumented_stripped == [], (
        f"redact.ts strips fields missing from RawProblem/Problem in drill.ts: {undocumented_stripped}"
    )


@pytest.mark.parametrize("path", PATHS)
def test_drill_has_core_fields(path: str) -> None:
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    for key in ("drillId", "unitCode", "problems"):
        assert key in doc, f"{path} missing {key}"
    assert doc["problems"], f"{path} has no problems"

    unknown_doc = sorted(set(doc.keys()) - DOCUMENTED_DRILL_FIELDS)
    assert unknown_doc == [], f"{path} has undocumented top-level keys (update drill.ts): {unknown_doc}"

    for p in doc["problems"]:
        assert "id" in p and "prompt" in p
        unknown_prob = sorted(set(p.keys()) - DOCUMENTED_PROBLEM_FIELDS)
        assert unknown_prob == [], f"{path} {p['id']} has undocumented problem keys (update drill.ts): {unknown_prob}"

        for idx, st in enumerate(p.get("steps") or []):
            if isinstance(st, dict):
                unknown_step = sorted(set(st.keys()) - DOCUMENTED_STEP_FIELDS)
                assert unknown_step == [], (
                    f"{path} {p['id']} steps[{idx}] has undocumented keys (update drill.ts): {unknown_step}"
                )

        spec = p.get("answerSpec")
        if isinstance(spec, dict):
            unknown_spec = sorted(set(spec.keys()) - DOCUMENTED_SPEC_FIELDS)
            assert unknown_spec == [], (
                f"{path} {p['id']} answerSpec has undocumented keys (update drill.ts): {unknown_spec}"
            )
            for idx, opt in enumerate(spec.get("options") or []):
                if isinstance(opt, dict):
                    unknown_opt = sorted(set(opt.keys()) - DOCUMENTED_OPTION_FIELDS)
                    assert unknown_opt == [], (
                        f"{path} {p['id']} options[{idx}] has undocumented keys (update drill.ts): {unknown_opt}"
                    )

        # Test-graded code problems are checked by visible/hidden tests, not an answerSpec.
        if p.get("visibleTests") or p.get("hiddenTests"):
            continue
        assert "answerSpec" in p, f"{path} {p['id']} has neither answerSpec nor tests"
        assert "type" in p["answerSpec"]
