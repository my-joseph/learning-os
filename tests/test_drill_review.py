"""Tests for scripts.drill_review: deterministic rule engine, cycle scoping, and zero-leak."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.drill_review import build_drill_review, format_drill_review, main


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _setup_fixture_repo(tmp_path: Path) -> Path:
    """Create a minimal isolated repo layout with two units, vault traps, drills, and variants."""
    _write(
        tmp_path / "id_map.json",
        {
            "MTH-T02-C01-U01": {"id": "page-u01", "title": "Complex Numbers"},
            "MTH-T02-C01-U02": {"id": "page-u02", "title": "Quadratic Equations"},
        },
    )
    _write(
        tmp_path / "math_engine/reasoning_vault/MTH-T02-C01-U01.json",
        {
            "unitCode": "MTH-T02-C01-U01",
            "archetypes": [
                {
                    "archetypeKey": "arch-l1",
                    "unitCode": "MTH-T02-C01-U01",
                    "level": 1,
                    "name": "Basic Complex Operations",
                    "coreConcept": "Apply i^2 = -1 to simplify powers and arithmetic.",
                    "cognitiveTraps": [
                        {
                            "trapTag": "trap-sign-flip",
                            "description": "Forgot that i squared equals minus one when simplifying.",
                        }
                    ],
                },
                {
                    "archetypeKey": "arch-l2",
                    "unitCode": "MTH-T02-C01-U01",
                    "level": 2,
                    "name": "Conjugate Equations",
                    "cognitiveTraps": [
                        {
                            "trapTag": "trap-conjugate-swap",
                            "description": "Combined z and its conjugate as identical terms.",
                        }
                    ],
                },
                {
                    "archetypeKey": "arch-l3",
                    "unitCode": "MTH-T02-C01-U01",
                    "level": 3,
                    "name": "Parameter Axis Conditions",
                    "cognitiveTraps": [
                        {
                            "trapTag": "trap-nonzero-check",
                            "description": "Missed checking that the imaginary part is nonzero.",
                        }
                    ],
                },
                {
                    "archetypeKey": "arch-l4",
                    "unitCode": "MTH-T02-C01-U01",
                    "level": 4,
                    "name": "Complex Impedance Synthesis",
                    "cognitiveTraps": [
                        {
                            "trapTag": "trap-modulus-square",
                            "description": "Forgot to square both components in modulus.",
                        }
                    ],
                },
            ],
        },
    )
    _write(
        tmp_path / "math_engine/reasoning_vault/MTH-T02-C01-U02.json",
        {
            "unitCode": "MTH-T02-C01-U02",
            "archetypes": [
                {
                    "archetypeKey": "quad-l1",
                    "unitCode": "MTH-T02-C01-U02",
                    "level": 1,
                    "name": "Factoring Monic Quadratics",
                    "cognitiveTraps": [{"trapTag": "trap-quad-sign", "description": "Sign not flipped."}],
                }
            ],
        },
    )

    _write(
        tmp_path / "drills/data/MTH-T02-C01-U01/DRL-MTH-T02-C01-U01-01.json",
        {
            "drillId": "DRL-MTH-T02-C01-U01-01",
            "unitCode": "MTH-T02-C01-U01",
            "unitTitle": "Complex Numbers",
            "title": "U01 Core Drill",
            "subject": "MATH",
            "problems": [
                {
                    "id": "Q01",
                    "level": 1,
                    "form": "direct",
                    "archetypeKey": "arch-l1",
                    "commonTrapTag": "trap-sign-flip",
                    "prompt": "SECRET_PROMPT_Q01 compute 4i^2 - 9",
                    "answerPlain": "SECRET_ANS_MINUS_13",
                    "answerDisplay": "SECRET_ANS_MINUS_13",
                    "trapValue": "SECRET_TRAP_MINUS_5",
                    "trapDerivation": "4 - 9",
                    "checkpointHint": "SECRET_HINT_Q01",
                    "display": "SECRET_DISPLAY_Q01",
                    "steps": [{"latex": "4(-1)-9", "explain": "SECRET_STEP_Q01"}],
                    "answerSpec": {"type": "number", "value": "-13"},
                },
                {
                    "id": "Q02",
                    "level": 2,
                    "form": "reverse",
                    "archetypeKey": "arch-l2",
                    "commonTrapTag": "trap-conjugate-swap",
                    "prompt": "SECRET_PROMPT_Q02 solve conjugate",
                    "answerPlain": "SECRET_ANS_7",
                    "answerDisplay": "SECRET_ANS_7",
                    "trapValue": "SECRET_TRAP_99",
                    "checkpointHint": "SECRET_HINT_Q02",
                    "display": "SECRET_DISPLAY_Q02",
                    "steps": [{"latex": "z+\\bar{z}=14", "explain": "SECRET_STEP_Q02"}],
                    "answerSpec": {"type": "number", "value": "7"},
                },
            ],
        },
    )

    _write(
        tmp_path / "drills/data/MTH-T02-C01-U01/DRL-MTH-T02-C01-U01-02.json",
        {
            "drillId": "DRL-MTH-T02-C01-U01-02",
            "unitCode": "MTH-T02-C01-U01",
            "unitTitle": "Complex Numbers",
            "title": "U01 Advanced Drill",
            "subject": "MATH",
            "problems": [
                {
                    "id": "Q01",
                    "level": 2,
                    "form": "direct",
                    "archetypeKey": "arch-l2",
                    "commonTrapTag": "trap-conjugate-swap",
                    "prompt": "SECRET_PROMPT_D2_Q01",
                    "answerPlain": "SECRET_ANS_D2_Q01",
                    "steps": [{"latex": "x=1", "explain": "SECRET_STEP_D2_Q01"}],
                    "answerSpec": {"type": "number", "value": "1"},
                },
                {
                    "id": "Q02",
                    "level": 3,
                    "form": "choose",
                    "archetypeKey": "arch-l3",
                    "commonTrapTag": "trap-nonzero-check",
                    "prompt": "SECRET_PROMPT_D2_Q02",
                    "answerPlain": "SECRET_ANS_D2_Q02",
                    "steps": [{"latex": "x=2", "explain": "SECRET_STEP_D2_Q02"}],
                    "answerSpec": {"type": "number", "value": "2"},
                },
                {
                    "id": "Q03",
                    "level": 4,
                    "form": "direct",
                    "archetypeKey": "arch-l4",
                    "commonTrapTag": "trap-modulus-square",
                    "prompt": "SECRET_PROMPT_D2_Q03",
                    "answerPlain": "SECRET_ANS_D2_Q03",
                    "steps": [{"latex": "x=5", "explain": "SECRET_STEP_D2_Q03"}],
                    "answerSpec": {"type": "number", "value": "5"},
                },
            ],
        },
    )

    _write(
        tmp_path / "drills/data/MTH-T02-C01-U02/DRL-MTH-T02-C01-U02-01.json",
        {
            "drillId": "DRL-MTH-T02-C01-U02-01",
            "unitCode": "MTH-T02-C01-U02",
            "unitTitle": "Quadratic Equations",
            "title": "U02 Starter",
            "subject": "MATH",
            "problems": [
                {
                    "id": "Q01",
                    "level": 1,
                    "form": "direct",
                    "archetypeKey": "quad-l1",
                    "commonTrapTag": "trap-quad-sign",
                    "prompt": "Solve x^2 - 1 = 0",
                    "answerPlain": "-1, 1",
                    "answerSpec": {"type": "solution_set", "values": ["-1", "1"]},
                }
            ],
        },
    )

    _write(
        tmp_path / "drills/variants/MTH-T02-C01-U01.json",
        {
            "unitCode": "MTH-T02-C01-U01",
            "variants": [
                {
                    "variantId": "VAR-MTH-T02-C01-U01-arch-l2-01",
                    "sourceArchetype": "arch-l2",
                    "archetypeKey": "arch-l2",
                    "level": 2,
                    "prompt": "SECRET_VARIANT_PROMPT_1",
                    "answerPlain": "SECRET_VARIANT_ANS_1",
                },
                {
                    "variantId": "VAR-MTH-T02-C01-U01-arch-l2-02",
                    "sourceArchetype": "arch-l2",
                    "archetypeKey": "arch-l2",
                    "level": 2,
                    "prompt": "SECRET_VARIANT_PROMPT_2",
                    "answerPlain": "SECRET_VARIANT_ANS_2",
                },
            ],
        },
    )
    return tmp_path


def _run_review(root: Path, drill_id: str, *, today: str = "2026-11-21") -> dict:
    return build_drill_review(
        drill_id,
        repo_root=str(root),
        data_root=str(root / "drills/data"),
        progress_dir=str(root / "progress"),
        variants_dir=str(root / "drills/variants"),
        vault_dir=str(root / "math_engine/reasoning_vault"),
        issue_log=str(root / "issues/log.jsonl"),
        today=today,
    )


def test_zero_leak_and_scoring_outcomes_and_cycle_scoping(tmp_path: Path):
    root = _setup_fixture_repo(tmp_path)
    _write(
        root / "progress/DRL-MTH-T02-C01-U01-02.json",
        {
            "drillId": "DRL-MTH-T02-C01-U01-02",
            "unitCode": "MTH-T02-C01-U01",
            "sessionSummary": {"attemptDate": "2026-11-21", "practiceStatus": "Needs Retry"},
            "problems": {
                # Prior cycle had hint/setup, current cycle is clean first-try -> 1.0 & 0 cycle reveals!
                "Q01": {
                    "cycleStartedAt": "2026-11-21T10:00:00Z",
                    "hintsRevealed": 2,
                    "setupRevealedBeforeAnswer": True,
                    "attempts": [
                        {"ts": "2026-11-19T10:00:00Z", "verdict": "incorrect", "matchedTrap": "trap-conjugate-swap"},
                        {"ts": "2026-11-21T10:01:00Z", "verdict": "correct"},
                    ],
                    "durationMs": 12000,
                },
                # Wrong with trapMatched + note + variant opened
                "Q02": {
                    "attempts": [
                        {"ts": "2026-11-21T10:05:00Z", "verdict": "incorrect", "matchedTrap": "trap-nonzero-check"}
                    ],
                    "mistakes": ["trap-nonzero-check"],
                    "mistakeNote": "ลืมเช็กว่าส่วนจินตภาพต้องไม่เป็นศูนย์",
                    "durationMs": 25000,
                },
                # Q03 intentionally unanswered (notTried)
            },
        },
    )

    rep = _run_review(root, "DRL-MTH-T02-C01-U01-02")
    text = format_drill_review(rep)
    dumped = json.dumps(rep, ensure_ascii=False)

    # Zero-leak: neither JSON nor text exposes prompts, answers, hints, display, or steps
    for secret in (
        "SECRET_PROMPT_D2_Q01",
        "SECRET_PROMPT_D2_Q02",
        "SECRET_PROMPT_D2_Q03",
        "SECRET_ANS_D2_Q01",
        "SECRET_ANS_D2_Q02",
        "SECRET_ANS_D2_Q03",
        "SECRET_STEP_D2_Q01",
        "SECRET_STEP_D2_Q02",
        "SECRET_STEP_D2_Q03",
        "SECRET_VARIANT_PROMPT_1",
        "SECRET_VARIANT_ANS_1",
    ):
        assert secret not in dumped
        assert secret not in text

    q1, q2, q3 = rep["items"]
    assert q1["score"] == 1.0 and q1["outcome"] == "correct"
    assert q1["reveals"] == {"hints": 0, "setup": False, "steps": False, "solution": False}
    assert q1["matchedTraps"] == []

    assert q2["score"] == 0.0 and q2["outcome"] == "wrong"
    assert q2["matchedTraps"][0]["tag"] == "trap-nonzero-check"
    assert "nonzero" in q2["matchedTraps"][0]["description"]
    assert q2["mistakeNote"] == "ลืมเช็กว่าส่วนจินตภาพต้องไม่เป็นศูนย์"

    assert q3["score"] is None and q3["outcome"] == "notTried"


def test_report_scopes_automatic_mistakes_to_the_current_cycle(tmp_path: Path):
    root = _setup_fixture_repo(tmp_path)
    drill_id = "DRL-MTH-T02-C01-U01-02"
    previous_skip = {"ts": "2026-11-19T10:00:00Z", "verdict": "skipped"}
    cycle = "2026-11-21T10:00:00Z"
    current_attempt = "2026-11-21T10:01:00Z"
    _write(
        root / "progress" / f"{drill_id}.json",
        {
            "drillId": drill_id,
            "problems": {
                "Q01": {
                    "cycleStartedAt": cycle,
                    "attempts": [previous_skip, {"ts": current_attempt, "verdict": "correct"}],
                    "mistakes": ["concept-gap", "old-auto", "learner-tag"],
                    "autoMistakes": {"old-auto": previous_skip["ts"]},
                },
                "Q02": {
                    "cycleStartedAt": cycle,
                    "attempts": [{"ts": current_attempt, "verdict": "skipped"}],
                    "mistakes": ["concept-gap"],
                },
                "Q03": {
                    "cycleStartedAt": cycle,
                    "attempts": [previous_skip],
                    "mistakes": ["concept-gap"],
                },
            },
        },
    )

    report = _run_review(root, drill_id)
    assert [item["mistakes"] for item in report["items"]] == [["learner-tag"], ["concept-gap"], []]
    assert report["totals"]["mistakesCategories"] == {"concept-gap": 1, "learner-tag": 1}
    assert report["items"][0]["outcomeBucket"] == "clean"


def test_clean_l1_l2_with_mastery_cap_recommends_l3_l4_lift(tmp_path: Path):
    root = _setup_fixture_repo(tmp_path)
    _write(
        root / "progress/DRL-MTH-T02-C01-U01-01.json",
        {
            "drillId": "DRL-MTH-T02-C01-U01-01",
            "unitCode": "MTH-T02-C01-U01",
            "sessionSummary": {"attemptDate": "2026-11-20", "practiceStatus": "Graded"},
            "problems": {
                "Q01": {"attempts": [{"ts": "2026-11-20T09:00:00Z", "verdict": "correct"}], "score": 1},
                "Q02": {"attempts": [{"ts": "2026-11-20T09:02:00Z", "verdict": "correct"}], "score": 1},
            },
        },
    )
    _write(
        root / "progress/_review_schedule.json",
        {
            "MTH-T02-C01-U01": {
                "mastery": 2,
                "lastReviewed": "2026-11-20",
                "nextReview": "2026-11-25",
                "masteryCap": {"capped": True, "reason": "needs one L4 challenge without hints"},
            }
        },
    )

    rep = _run_review(root, "DRL-MTH-T02-C01-U01-01")
    primary = rep["recommendation"]["primary"]
    assert primary["ruleId"] == "lift_mastery_cap_l3_l4"
    assert primary["params"]["levels"] == [3, 4]
    assert set(primary["params"]["archetypes"]) >= {"arch-l3", "arch-l4"}
    assert len(rep["unitContext"]["availableUntouchedDrills"]) == 1
    assert rep["unitContext"]["availableUntouchedDrills"][0]["drillId"] == "DRL-MTH-T02-C01-U01-02"
    assert len(rep["recommendation"]["alternatives"]) <= 2


def test_mixed_wrong_with_similar_available_recommends_similar_first(tmp_path: Path):
    root = _setup_fixture_repo(tmp_path)
    _write(
        root / "progress/DRL-MTH-T02-C01-U01-01.json",
        {
            "drillId": "DRL-MTH-T02-C01-U01-01",
            "unitCode": "MTH-T02-C01-U01",
            "problems": {
                "Q01": {"attempts": [{"ts": "2026-11-20T09:00:00Z", "verdict": "correct"}], "hintsRevealed": 1},
                "Q02": {
                    "attempts": [
                        {"ts": "2026-11-20T09:02:00Z", "verdict": "incorrect", "matchedTrap": "trap-conjugate-swap"}
                    ]
                },
            },
        },
    )
    rep = _run_review(root, "DRL-MTH-T02-C01-U01-01")
    primary = rep["recommendation"]["primary"]
    assert primary["ruleId"] == "retry_similar_then_targeted"
    assert primary["params"]["qids"] == ["Q02"]
    assert "trap-conjugate-swap" in primary["params"]["focusTags"]
    assert rep["unitContext"]["similarVariantsForMissed"][1]["unattemptedAtLevel"] == 2


def test_heavy_help_recommends_unassisted_fluency(tmp_path: Path):
    root = _setup_fixture_repo(tmp_path)
    _write(
        root / "progress/DRL-MTH-T02-C01-U01-01.json",
        {
            "drillId": "DRL-MTH-T02-C01-U01-01",
            "unitCode": "MTH-T02-C01-U01",
            "problems": {
                "Q01": {
                    "hintsRevealed": 2,
                    "setupRevealedBeforeAnswer": True,
                    "attempts": [{"ts": "2026-11-20T09:00:00Z", "verdict": "correct"}],
                },
                "Q02": {
                    "solutionRevealedBeforeAnswer": True,
                    "attempts": [{"ts": "2026-11-20T09:02:00Z", "verdict": "correct"}],
                },
            },
        },
    )
    rep = _run_review(root, "DRL-MTH-T02-C01-U01-01")
    primary = rep["recommendation"]["primary"]
    assert primary["ruleId"] == "consolidate_unassisted_fluency"
    assert set(primary["params"]["qids"]) == {"Q01", "Q02"}


def test_skipped_l3_l4_recommends_lowest_level_of_archetype(tmp_path: Path):
    root = _setup_fixture_repo(tmp_path)
    _write(
        root / "progress/DRL-MTH-T02-C01-U01-02.json",
        {
            "drillId": "DRL-MTH-T02-C01-U01-02",
            "unitCode": "MTH-T02-C01-U01",
            "problems": {
                "Q01": {"attempts": [{"ts": "2026-11-20T09:00:00Z", "verdict": "correct"}]},
                "Q02": {"skipped": True, "mistakes": ["concept-gap"]},
                "Q03": {"skipped": True, "mistakes": ["concept-gap"]},
            },
        },
    )
    rep = _run_review(root, "DRL-MTH-T02-C01-U01-02")
    primary = rep["recommendation"]["primary"]
    assert primary["ruleId"] == "skipped_items"
    # Q02 skipped at L3 (baseLevel 3) and Q03 skipped at L4 (baseLevel 4) step down to L2, L3 prerequisite skills
    assert primary["params"]["levels"] == [2, 3]
    assert primary["params"]["archetypes"] == ["arch-l1", "arch-l2", "arch-l3"]
    assert "unitPageSection" in primary["params"]


def test_refuses_prg_and_lab_ids_and_archetypeless_drills(tmp_path: Path, capsys):
    root = _setup_fixture_repo(tmp_path)
    _write(
        root / "drills/data/PRG-T01-C01-U01/DRL-PRG-T01-C01-U01-01.json",
        {
            "drillId": "DRL-PRG-T01-C01-U01-01",
            "unitCode": "PRG-T01-C01-U01",
            "subject": "PRG",
            "problems": [{"id": "Q01", "archetypeKey": "prg-arch", "level": 1}],
        },
    )
    _write(
        root / "drills/data/MTH-T02-C01-U01/DRL-MTH-T02-C01-U01-99.json",
        {
            "drillId": "DRL-MTH-T02-C01-U01-99",
            "unitCode": "MTH-T02-C01-U01",
            "subject": "MATH",
            "problems": [{"id": "Q01", "level": 2}],
        },
    )
    _write(
        root / "progress/DRL-MTH-T02-C01-U01-99.json",
        {
            "drillId": "DRL-MTH-T02-C01-U01-99",
            "unitCode": "MTH-T02-C01-U01",
            "problems": {"Q01": {"skipped": True, "mistakes": ["concept-gap"]}},
        },
    )

    for bad_id in ("DRL-PRG-T01-C01-U01-01", "LAB-PRG-T01-C01-01", "DRL-MTH-T02-C01-U01-99"):
        rc = main(
            [
                bad_id,
                "--data-root",
                str(root / "drills/data"),
                "--progress-dir",
                str(root / "progress"),
            ]
        )
        assert rc == 1
        err = capsys.readouterr().err
        assert "Error:" in err


def test_live_evidence_mastery_overrides_stale_l4_schedule_cap_and_suppresses_l4_challenge_on_needs_retry(
    tmp_path: Path,
):
    root = _setup_fixture_repo(tmp_path)
    # Learner completed Q03 (L4) clean, skipped Q02 (L3), and wrong on Q01 (L2)
    _write(
        root / "progress/DRL-MTH-T02-C01-U01-02.json",
        {
            "drillId": "DRL-MTH-T02-C01-U01-02",
            "unitCode": "MTH-T02-C01-U01",
            "sessionSummary": {"attemptDate": "2026-11-21", "practiceStatus": "Needs Retry"},
            "problems": {
                "Q01": {
                    "attempts": [
                        {"ts": "2026-11-21T09:00:00Z", "verdict": "incorrect", "matchedTrap": "trap-conjugate-swap"}
                    ],
                    "mistakeNote": "ลืมแยกส่วนจริงกับส่วนจินตภาพของสังยุค",
                },
                "Q02": {"skipped": True, "mistakes": ["concept-gap"]},
                "Q03": {"attempts": [{"ts": "2026-11-21T09:05:00Z", "verdict": "correct"}]},
            },
        },
    )
    # Stale schedule claims L4 challenge is still needed
    _write(
        root / "progress/_review_schedule.json",
        {
            "MTH-T02-C01-U01": {
                "mastery": 2,
                "lastReviewed": "2026-11-20",
                "nextReview": "2026-11-25",
                "masteryCap": {"capped": True, "reason": "needs one L4 challenge without hints"},
            }
        },
    )

    rep = _run_review(root, "DRL-MTH-T02-C01-U01-02")
    assert rep["unitContext"]["evidenceMastery"]["hasL4Challenge"] is True
    assert rep["unitContext"]["masteryCap"]["capped"] is False
    rule_ids = [rep["recommendation"]["primary"]["ruleId"]] + [
        a["ruleId"] for a in rep["recommendation"]["alternatives"]
    ]
    assert "mastery_cap_l4_challenge" not in rule_ids


def test_core_concept_exposed_and_unstarted_and_in_progress_drills_handled(tmp_path: Path):
    root = _setup_fixture_repo(tmp_path)
    # 1. Unstarted drill (no progress file) even with review due tomorrow -> Not started & start_current_drill
    _write(
        root / "progress/_review_schedule.json",
        {
            "MTH-T02-C01-U01": {
                "mastery": 2,
                "lastReviewed": "2026-11-17",
                "nextReview": "2026-11-22",
                "masteryCap": {"capped": True, "reason": "needs one L4 challenge without hints"},
            }
        },
    )
    rep_empty = _run_review(root, "DRL-MTH-T02-C01-U01-01", today="2026-11-21")
    assert rep_empty["totals"]["practiceStatus"] == "Not started"
    assert rep_empty["items"][0]["coreConcept"] == "Apply i^2 = -1 to simplify powers and arithmetic."
    assert rep_empty["recommendation"]["primary"]["ruleId"] == "start_current_drill"
    assert rep_empty["recommendation"]["alternatives"] == []

    # 2. In-progress drill with stale sessionSummary.practiceStatus="Needs Retry" -> reports "In progress"
    _write(
        root / "progress/DRL-MTH-T02-C01-U01-01.json",
        {
            "drillId": "DRL-MTH-T02-C01-U01-01",
            "unitCode": "MTH-T02-C01-U01",
            "sessionSummary": {"attemptDate": "2026-11-21", "practiceStatus": "Needs Retry"},
            "problems": {
                "Q01": {
                    "hintsRevealed": 1,
                    "attempts": [{"ts": "2026-11-21T09:00:00Z", "verdict": "correct"}],
                }
            },
        },
    )
    rep_inprog = _run_review(root, "DRL-MTH-T02-C01-U01-01", today="2026-11-21")
    assert rep_inprog["totals"]["practiceStatus"] == "In progress"


def test_repeated_trap_across_two_drills_recommends_recap_and_trap_drill(tmp_path: Path):
    root = _setup_fixture_repo(tmp_path)
    _write(
        root / "progress/DRL-MTH-T02-C01-U01-01.json",
        {
            "drillId": "DRL-MTH-T02-C01-U01-01",
            "unitCode": "MTH-T02-C01-U01",
            "problems": {
                "Q01": {"attempts": [{"ts": "2026-11-18T09:00:00Z", "verdict": "correct"}]},
                "Q02": {
                    "attempts": [
                        {"ts": "2026-11-18T09:02:00Z", "verdict": "incorrect", "matchedTrap": "trap-conjugate-swap"}
                    ]
                },
            },
        },
    )
    _write(
        root / "progress/DRL-MTH-T02-C01-U01-02.json",
        {
            "drillId": "DRL-MTH-T02-C01-U01-02",
            "unitCode": "MTH-T02-C01-U01",
            "problems": {
                "Q01": {
                    "attempts": [
                        {"ts": "2026-11-21T09:00:00Z", "verdict": "incorrect", "matchedTrap": "trap-conjugate-swap"}
                    ]
                },
                "Q02": {"attempts": [{"ts": "2026-11-21T09:02:00Z", "verdict": "correct"}]},
                "Q03": {"attempts": [{"ts": "2026-11-21T09:04:00Z", "verdict": "correct"}]},
            },
        },
    )
    rep = _run_review(root, "DRL-MTH-T02-C01-U01-02")
    assert len(rep["unitContext"]["weakSpots"]["repeatedAcrossDrills"]) == 1
    primary = rep["recommendation"]["primary"]
    assert primary["ruleId"] == "repeated_trap_across_drills"
    assert primary["params"]["focusTags"] == ["trap-conjugate-swap"]
    assert "Trap Contrast" in primary["params"]["unitPageSection"]


def test_review_due_tomorrow_with_half_drill_done_prioritizes_review(tmp_path: Path):
    root = _setup_fixture_repo(tmp_path)
    _write(
        root / "progress/DRL-MTH-T02-C01-U01-01.json",
        {
            "drillId": "DRL-MTH-T02-C01-U01-01",
            "unitCode": "MTH-T02-C01-U01",
            "problems": {
                "Q01": {"attempts": [{"ts": "2026-11-21T09:00:00Z", "verdict": "correct"}]},
            },
        },
    )
    _write(
        root / "progress/_review_schedule.json",
        {
            "MTH-T02-C01-U01": {
                "mastery": 2,
                "lastReviewed": "2026-11-17",
                "nextReview": "2026-11-22",
            }
        },
    )
    rep = _run_review(root, "DRL-MTH-T02-C01-U01-01", today="2026-11-21")
    primary = rep["recommendation"]["primary"]
    assert primary["ruleId"] == "review_due_soon"
    assert primary["params"]["daysUntilReview"] == 1
    assert primary["params"]["qids"] == ["Q02"]


def test_all_clean_including_l4_recommends_next_unit(tmp_path: Path):
    root = _setup_fixture_repo(tmp_path)
    _write(
        root / "progress/DRL-MTH-T02-C01-U01-02.json",
        {
            "drillId": "DRL-MTH-T02-C01-U01-02",
            "unitCode": "MTH-T02-C01-U01",
            "problems": {
                "Q01": {"attempts": [{"ts": "2026-11-21T09:00:00Z", "verdict": "correct"}]},
                "Q02": {"attempts": [{"ts": "2026-11-21T09:02:00Z", "verdict": "correct"}]},
                "Q03": {"attempts": [{"ts": "2026-11-21T09:04:00Z", "verdict": "correct"}]},
            },
        },
    )
    _write(
        root / "progress/_review_schedule.json",
        {
            "MTH-T02-C01-U01": {
                "mastery": 3,
                "lastReviewed": "2026-11-21",
                "nextReview": "2026-12-08",
                "masteryCap": {"capped": False, "reason": ""},
            }
        },
    )
    rep = _run_review(root, "DRL-MTH-T02-C01-U01-02", today="2026-11-21")
    primary = rep["recommendation"]["primary"]
    assert primary["ruleId"] == "ready_for_next_unit"
    assert primary["params"]["unit"] == "MTH-T02-C01-U02"
    assert primary["params"]["drillId"] == "DRL-MTH-T02-C01-U02-01"


def test_cli_honors_progress_dir_env_and_is_read_only(tmp_path: Path, monkeypatch, capsys):
    root = _setup_fixture_repo(tmp_path)
    prog_dir = root / "custom-progress"
    _write(
        prog_dir / "DRL-MTH-T02-C01-U01-01.json",
        {
            "drillId": "DRL-MTH-T02-C01-U01-01",
            "unitCode": "MTH-T02-C01-U01",
            "problems": {"Q01": {"attempts": [{"ts": "2026-11-21T09:00:00Z", "verdict": "correct"}]}},
        },
    )
    before = (prog_dir / "DRL-MTH-T02-C01-U01-01.json").read_text(encoding="utf-8")
    monkeypatch.setenv("PROGRESS_DIR", str(prog_dir))
    monkeypatch.setenv("DRILLS_DATA_DIR", str(root / "drills/data"))

    rc = main(["DRL-MTH-T02-C01-U01-01", "--json", "--today", "2026-11-21"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["totals"]["cleanCount"] == 1
    assert out["totals"]["notTriedCount"] == 1
    assert (prog_dir / "DRL-MTH-T02-C01-U01-01.json").read_text(encoding="utf-8") == before
