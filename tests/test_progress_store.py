"""Learner progress lives in progress/<DRILL_ID>.json, never in drill content files."""

import glob
import json

import pytest

import progress_store as ps


def _doc():
    return {
        "drillId": "DRL-MTH-X-01",
        "unitCode": "MTH-X",
        "problems": [{"id": "Q01", "prompt": "p1"}, {"id": "Q02", "prompt": "p2"}],
    }


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("PROGRESS_DIR", str(tmp_path / "progress"))
    return tmp_path


def test_round_trip_overlays_state_and_summary():
    doc = _doc()
    doc["problems"][0]["state"] = {"userInput": "42", "score": 1, "attempts": [{"input": "41"}]}
    doc["sessionSummary"] = {"score": 1, "attemptDate": "2026-11-13"}
    ps.save_progress(doc)

    fresh = ps.apply_progress(_doc(), ps.load_progress("DRL-MTH-X-01"))
    assert fresh["problems"][0]["state"]["attempts"] == [{"input": "41"}]
    assert "state" not in fresh["problems"][1]
    assert fresh["sessionSummary"]["attemptDate"] == "2026-11-13"


def test_strip_removes_only_learner_fields():
    doc = _doc()
    doc["problems"][0]["state"] = {"score": 0}
    doc["sessionSummary"] = {}
    ps.strip_progress(doc)
    assert doc == _doc()


def test_pristine_defaults_are_not_practice():
    doc = _doc()
    doc["problems"][0]["state"] = {"userInput": "", "score": None, "mistakes": [], "lastCheck": None}
    doc["sessionSummary"] = {"practiceStatus": "Ready", "score": 0, "attemptDate": None}
    assert not ps.has_practice(doc)
    doc["problems"][1]["state"] = {"skipped": True}
    assert ps.has_practice(doc)
    peek = _doc()
    peek["problems"][0]["state"] = {"userInput": "", "setupRevealedBeforeAnswer": True}
    assert ps.has_practice(peek), "opening the set-up is learner activity too"
    peek_sol = _doc()
    peek_sol["problems"][0]["state"] = {"userInput": "", "solutionRevealedBeforeAnswer": True}
    assert ps.has_practice(peek_sol), "opening the solution steps is learner activity too"


def test_migration_moves_practice_and_strips_content(tmp_path):
    from scripts.migrate_progress import migrate

    unit = tmp_path / "data" / "MTH-X"
    unit.mkdir(parents=True)
    practised = _doc()
    practised["problems"][0]["state"] = {"userInput": "7", "score": 1}
    (unit / "DRL-MTH-X-01.json").write_text(json.dumps(practised, indent=2), encoding="utf-8")
    pristine = dict(_doc(), drillId="DRL-MTH-X-02")
    pristine["sessionSummary"] = {"practiceStatus": "Ready", "score": 0}
    (unit / "DRL-MTH-X-02.json").write_text(json.dumps(pristine, indent=2) + "\n", encoding="utf-8")

    rep = migrate(str(tmp_path / "data"))
    assert rep["saved"] == ["DRL-MTH-X-01"] and len(rep["stripped"]) == 2
    assert ps.load_progress("DRL-MTH-X-01")["problems"]["Q01"]["userInput"] == "7"
    assert ps.load_progress("DRL-MTH-X-02") is None
    for f in unit.iterdir():
        content = f.read_text(encoding="utf-8")
        assert '"state"' not in content and "sessionSummary" not in content
    assert (unit / "DRL-MTH-X-02.json").read_text(encoding="utf-8").endswith("\n"), "trailing newline kept"


def test_committed_drills_hold_content_only():
    offenders = []
    for path in glob.glob("drills/data/*/DRL-*.json"):
        doc = json.load(open(path, encoding="utf-8"))
        if "sessionSummary" in doc or any("state" in p for p in doc.get("problems", [])):
            offenders.append(path)
    assert offenders == [], "practice state belongs in progress/, run scripts/migrate_progress.py"


def test_item_score_matches_studio_rules():
    assert ps.item_score({"attempts": [{"verdict": "correct", "ts": "2026-11-16"}], "score": 1}) == (1.0, False)
    # Wrong -> open solution -> correct => 0.5, assisted
    assert ps.item_score(
        {
            "attempts": [
                {"verdict": "incorrect", "ts": "2026-11-16"},
                {"verdict": "correct", "ts": "2026-11-16", "solutionRevealed": True},
            ],
            "solutionRevealedBeforeAnswer": True,
            "score": 0.5,
        }
    ) == (0.5, True)
    # Wrong -> retry correct (unassisted) => 0.5, unassisted
    assert ps.item_score(
        {
            "attempts": [
                {"verdict": "incorrect", "ts": "2026-11-16"},
                {"verdict": "correct", "ts": "2026-11-16"},
            ],
            "score": 1,
        }
    ) == (0.5, False)
    # Format typo before first-try correct does not penalize
    assert ps.item_score(
        {
            "attempts": [
                {"verdict": "invalid input", "ts": "2026-11-16"},
                {"verdict": "correct", "ts": "2026-11-16"},
            ],
            "score": 1,
        }
    ) == (1.0, False)


def test_save_progress_refuses_to_blank_practised_progress():
    practised = _doc()
    practised["problems"][0]["state"] = {"userInput": "42", "score": 1, "attempts": [{"input": "42"}]}
    practised["sessionSummary"] = {"score": 1, "attemptDate": "2026-11-17", "practiceStatus": "Graded"}
    ps.save_progress(practised)

    saved = ps.load_progress("DRL-MTH-X-01")
    assert saved is not None and ps.has_practice(saved)

    # Attempting to overwrite with an empty or pristine-defaults doc must raise and preserve disk state
    with pytest.raises(ValueError, match="allow_reset=True"):
        ps.save_progress(_doc())

    pristine_defaults = _doc()
    pristine_defaults["problems"][0]["state"] = {"userInput": "", "score": None, "mistakes": []}
    pristine_defaults["sessionSummary"] = {"practiceStatus": "Ready", "score": 0, "attemptDate": None}
    with pytest.raises(ValueError, match="allow_reset=True"):
        ps.save_progress(pristine_defaults)

    still_there = ps.load_progress("DRL-MTH-X-01")
    assert still_there["problems"]["Q01"]["userInput"] == "42"
    assert still_there["sessionSummary"]["attemptDate"] == "2026-11-17"

    # Explicit reset is allowed
    ps.save_progress(_doc(), allow_reset=True)
    reset_prog = ps.load_progress("DRL-MTH-X-01")
    assert reset_prog is not None and not ps.has_practice(reset_prog)

    # Overwriting a pristine (non-practised) progress file does not require allow_reset
    ps.save_progress(_doc())


def test_revisit_note_persists_in_progress_without_touching_drill_content(tmp_path):
    drill_dir = tmp_path / "drills" / "data" / "MTH-X"
    drill_dir.mkdir(parents=True)
    drill_file = drill_dir / "DRL-MTH-X-01.json"
    content_doc = _doc()
    original_json = json.dumps(content_doc, indent=2)
    drill_file.write_text(original_json, encoding="utf-8")

    working = json.loads(original_json)
    working["problems"][0]["state"] = {
        "userInput": "42",
        "score": 1,
        "attempts": [{"input": "42", "verdict": "correct", "ts": "2026-11-18T10:00:00Z"}],
        "revisitNote": "Next time check the reciprocal sign before multiplying.",
    }
    assert ps.has_practice(working)
    ps.save_progress(working)

    # Drill content on disk is completely untouched
    assert drill_file.read_text(encoding="utf-8") == original_json
    assert "revisitNote" not in drill_file.read_text(encoding="utf-8")

    # Progress file stores and restores revisitNote
    loaded = ps.load_progress("DRL-MTH-X-01")
    assert loaded["problems"]["Q01"]["revisitNote"] == "Next time check the reciprocal sign before multiplying."
    merged = ps.apply_progress(_doc(), loaded)
    assert merged["problems"][0]["state"]["revisitNote"] == "Next time check the reciprocal sign before multiplying."

    # A problem state with only revisitNote is also recognized as learner practice
    note_only = _doc()
    note_only["problems"][0]["state"] = {"userInput": "", "revisitNote": "Invert divisor first"}
    assert ps.has_practice(note_only)


def test_save_progress_writes_atomically_and_preserves_existing_on_failure(tmp_path, monkeypatch):
    progress_dir = tmp_path / "progress"
    first = _doc()
    first["problems"][0]["state"] = {"userInput": "42", "score": 1, "attempts": [{"input": "42", "verdict": "correct"}]}
    first["sessionSummary"] = {"score": 1, "attemptDate": "2026-11-20", "practiceStatus": "Graded"}

    replace_calls: list[tuple[str, str]] = []
    real_replace = ps.os.replace

    def spy_replace(src: str, dst: str) -> None:
        replace_calls.append((src, dst))
        real_replace(src, dst)

    monkeypatch.setattr(ps.os, "replace", spy_replace)
    saved_path = ps.save_progress(first)
    assert len(replace_calls) == 1
    assert replace_calls[0][1] == saved_path
    assert list(progress_dir.glob("*.tmp")) == []

    # Failed serialization leaves the prior progress file intact and cleans up its temp file
    broken = _doc()
    broken["problems"][0]["state"] = {"userInput": "99", "score": 1, "bad": object()}
    with pytest.raises(TypeError):
        ps.save_progress(broken)
    assert list(progress_dir.glob("*.tmp")) == []
    assert ps.load_progress("DRL-MTH-X-01")["problems"]["Q01"]["userInput"] == "42"

    # Simulated os.replace failure also preserves the prior file and cleans up the temp file
    def fail_replace(src: str, dst: str) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(ps.os, "replace", fail_replace)
    second = _doc()
    second["problems"][0]["state"] = {"userInput": "100", "score": 0.5}
    with pytest.raises(OSError, match="disk full"):
        ps.save_progress(second)
    assert list(progress_dir.glob("*.tmp")) == []
    assert ps.load_progress("DRL-MTH-X-01")["problems"]["Q01"]["userInput"] == "42"


def test_is_locked_after_correct_respects_cycle_and_variant():
    assert ps.is_locked_after_correct(None) is False
    assert ps.is_locked_after_correct({}) is False

    # Normal correct attempt locks
    correct_state = {
        "attempts": [{"input": "5", "ts": "2026-11-20T10:00:00Z", "verdict": "correct"}],
    }
    assert ps.is_locked_after_correct(correct_state) is True

    # New cycle unlocks prior-cycle correct attempt
    assert ps.is_locked_after_correct({**correct_state, "cycleStartedAt": "2026-11-20T12:00:00Z"}) is False

    # Variant correct attempt does NOT lock original problem, but DOES lock when is_variant=True
    variant_only = {
        "attempts": [{"input": "5", "ts": "2026-11-20T10:00:00Z", "verdict": "correct", "kind": "variant"}],
    }
    assert ps.is_locked_after_correct(variant_only) is False
    assert ps.is_locked_after_correct(variant_only, is_variant=True) is True

    # Lightweight legacy state with lastCheck and no attempts
    assert ps.is_locked_after_correct({"lastCheck": {"verdict": "correct"}}) is True
    assert ps.is_locked_after_correct({"lastCheck": {"verdict": "incorrect"}}) is False


def test_save_progress_merges_server_owned_fields_and_concurrent_records():
    """Saving a redacted/stale client doc must preserve variantId, variant matchedTrap,
    variantsSeen/Attempted, similarSlots, exampleViewedAt, cycle timestamps, and concurrent
    reviews/attempts/testRuns/lastTestReport while accepting learner-editable fields."""
    initial = _doc()
    initial["problems"][0]["state"] = {
        "userInput": "5",
        "score": 0.5,
        "divergedStep": 0,
        "mistakes": ["sign-error"],
        "mistakeNote": "Old note",
        "revisitNote": "Old revisit",
        "attempts": [
            {"input": "-5", "ts": "2026-11-20T09:00:00Z", "verdict": "incorrect", "matchedTrap": "sign-flip"},
            {"input": "5", "ts": "2026-11-20T09:02:00Z", "verdict": "correct"},
            {"input": "5", "ts": "2026-11-20T11:30:00Z", "verdict": "correct"},
        ],
        "reviews": [
            {
                "at": "2026-11-20T11:00:00Z",
                "attempt": 1,
                "codeHash": "sha256:disk",
                "code": "x",
                "tests": {"passed": 2, "total": 2, "failed": []},
                "lint": [],
                "typecheck": [],
                "findings": [
                    {
                        "check": "QC-1",
                        "severity": "must",
                        "line": 1,
                        "note": "Check edge case",
                        "disputed": {"reason": "Already guarded", "issueId": "ISS-1"},
                    }
                ],
                "verdict": "pass",
                "explain": "Server-recorded explanation",
            }
        ],
        "testRuns": [{"ts": "2026-11-20T11:00:00Z", "allPassed": True, "passedCount": 2, "totalCount": 2}],
        "lastTestReport": {
            "allPassed": True,
            "score": 1,
            "passedCount": 2,
            "totalCount": 2,
            "visibleResults": [],
            "hiddenPassed": 1,
            "hiddenTotal": 1,
            "executionTimeMs": 12,
            "ts": "2026-11-20T11:00:00Z",
        },
        "variants": {
            "vabc123": {
                "variantId": "VAR-MTH-X-linear-01",
                "role": "try",
                "attempts": [
                    {
                        "input": "-3",
                        "ts": "2026-11-20T09:05:00Z",
                        "verdict": "incorrect",
                        "matchedTrap": "sign-flip",
                        "kind": "variant",
                    },
                    {"input": "3", "ts": "2026-11-20T09:06:00Z", "verdict": "correct", "kind": "variant"},
                ],
                "hintsRevealed": 1,
                "setupRevealed": True,
                "stepsRevealed": False,
                "durationMs": 4200,
                "servedAt": "2026-11-20T09:04:00Z",
            },
            "vdef456": {
                "variantId": "VAR-MTH-X-linear-02",
                "role": "try",
                "attempts": [],
                "hintsRevealed": 0,
                "setupRevealed": False,
                "stepsRevealed": False,
                "durationMs": 0,
                "servedAt": "",
            },
        },
        "similarSlots": ["vabc123", "vdef456"],
        "variantsSeen": ["VAR-MTH-X-linear-01"],
        "variantsAttempted": ["VAR-MTH-X-linear-01"],
        "exampleViewedAt": "2026-11-20T09:03:00Z",
        "cycleStartedAt": "2026-11-20T11:25:00Z",
        "reviewHintRevealedAt": "2026-11-20T11:25:30Z",
        "reviewSetupRevealedAt": "2026-11-20T11:26:00Z",
        "reviewStepsRevealedAt": "2026-11-20T11:27:00Z",
    }
    initial["problems"][1]["state"] = {"userInput": "4", "score": 1}
    initial["sessionSummary"] = {"practiceStatus": "In Progress", "score": 1.5}
    ps.save_progress(initial)

    # Now save a redacted, stale client doc missing variantId, variant matchedTrap,
    # variantsSeen/Attempted, concurrent review/attempt/testRuns/lastTestReport, and Q02.
    stale_redacted = {
        "drillId": "DRL-MTH-X-01",
        "unitCode": "MTH-X",
        "sessionSummary": {"practiceStatus": "Graded", "score": 1.5, "attemptDate": "2026-11-20"},
        "problems": [
            {
                "id": "Q01",
                "prompt": "p1",
                "state": {
                    "userInput": "5",
                    "score": 0.5,
                    "divergedStep": 0,
                    "mistakes": ["sign-error", "arithmetic"],
                    "mistakeNote": "Updated in Review & Sync",
                    "revisitNote": "Check sign before dividing",
                    # Stale: only first two attempts (and first missing matchedTrap)
                    "attempts": [
                        {"input": "-5", "ts": "2026-11-20T09:00:00Z", "verdict": "incorrect"},
                        {"input": "5", "ts": "2026-11-20T09:02:00Z", "verdict": "correct"},
                    ],
                    # Stale pre-dispute/empty review list
                    "reviews": [],
                    "testRuns": [],
                    "lastTestReport": None,
                    # Redacted variants without variantId or matchedTrap
                    "variants": {
                        "vabc123": {
                            "role": "try",
                            "attempts": [
                                {
                                    "input": "-3",
                                    "ts": "2026-11-20T09:05:00Z",
                                    "verdict": "incorrect",
                                    "kind": "variant",
                                },
                                {"input": "3", "ts": "2026-11-20T09:06:00Z", "verdict": "correct", "kind": "variant"},
                            ],
                            "servedAt": "2026-11-20T09:04:00Z",
                        }
                    },
                    "similarSlots": ["vabc123"],
                },
            }
        ],
    }
    ps.save_progress(stale_redacted)

    saved = ps.load_progress("DRL-MTH-X-01")
    assert saved is not None
    q1 = saved["problems"]["Q01"]
    assert q1["variants"]["vabc123"]["variantId"] == "VAR-MTH-X-linear-01"
    assert q1["variants"]["vdef456"]["variantId"] == "VAR-MTH-X-linear-02"
    assert q1["variants"]["vabc123"]["attempts"][0]["matchedTrap"] == "sign-flip"
    assert q1["similarSlots"] == ["vabc123", "vdef456"]
    assert q1["variantsSeen"] == ["VAR-MTH-X-linear-01"]
    assert q1["variantsAttempted"] == ["VAR-MTH-X-linear-01"]
    assert q1["exampleViewedAt"] == "2026-11-20T09:03:00Z"
    assert q1["cycleStartedAt"] == "2026-11-20T11:25:00Z"
    assert q1["reviewHintRevealedAt"] == "2026-11-20T11:25:30Z"
    assert q1["reviewSetupRevealedAt"] == "2026-11-20T11:26:00Z"
    assert q1["reviewStepsRevealedAt"] == "2026-11-20T11:27:00Z"
    assert len(q1["reviews"]) == 1
    assert q1["reviews"][0]["explain"] == "Server-recorded explanation"
    assert q1["reviews"][0]["findings"][0]["disputed"]["issueId"] == "ISS-1"
    assert len(q1["attempts"]) == 3
    assert q1["attempts"][0]["matchedTrap"] == "sign-flip"
    assert len(q1["testRuns"]) == 1
    assert q1["lastTestReport"]["allPassed"] is True
    # Untouched Q02 on disk is preserved
    assert saved["problems"]["Q02"]["userInput"] == "4"
    # Learner-editable fields and sessionSummary from client are applied
    assert q1["mistakeNote"] == "Updated in Review & Sync"
    assert q1["revisitNote"] == "Check sign before dividing"
    assert q1["mistakes"] == ["sign-error", "arithmetic"]
    assert saved["sessionSummary"]["practiceStatus"] == "Graded"
    assert saved["sessionSummary"]["attemptDate"] == "2026-11-20"


def test_save_progress_allows_review_explain_and_dispute_updates_without_duplicating():
    """review_record.set_explain and dispute_finding mutate an existing review record in place
    and call save_progress; merge logic must persist those updates without duplicating the review,
    while still blocking a stale client from reverting them."""
    doc = _doc()
    base_review = {
        "at": "2026-11-20T10:00:00Z",
        "attempt": 1,
        "codeHash": "sha256:abc",
        "code": "function f() {}",
        "tests": {"passed": 2, "total": 2, "failed": []},
        "lint": [],
        "typecheck": [],
        "findings": [{"check": "QC-1", "severity": "must", "line": 1, "note": "Check input"}],
        "verdict": "revise",
        "explain": None,
    }
    doc["problems"][0]["state"] = {"userInput": "", "score": 0, "reviews": [base_review]}
    ps.save_progress(doc)

    # 1. dispute_finding adds disputed metadata and flips verdict to pass
    disputed = _doc()
    disputed["problems"][0]["state"] = {
        "userInput": "",
        "score": 1,
        "reviews": [
            {
                **base_review,
                "findings": [
                    {
                        "check": "QC-1",
                        "severity": "must",
                        "line": 1,
                        "note": "Check input",
                        "disputed": {"reason": "Handled upstream", "issueId": "ISS-42"},
                    }
                ],
                "verdict": "pass",
            }
        ],
    }
    ps.save_progress(disputed)
    after_dispute = ps.load_progress("DRL-MTH-X-01")["problems"]["Q01"]["reviews"]
    assert len(after_dispute) == 1
    assert after_dispute[0]["verdict"] == "pass"
    assert after_dispute[0]["findings"][0]["disputed"]["issueId"] == "ISS-42"

    # 2. set_explain fills explain on that passing review
    explained = _doc()
    explained["problems"][0]["state"] = {
        "userInput": "",
        "score": 1,
        "reviews": [{**after_dispute[0], "explain": "Uses a linear scan with O(1) space."}],
    }
    ps.save_progress(explained)
    after_explain = ps.load_progress("DRL-MTH-X-01")["problems"]["Q01"]["reviews"]
    assert len(after_explain) == 1
    assert after_explain[0]["explain"] == "Uses a linear scan with O(1) space."

    # 3. Stale browser client sends pre-dispute, unexplained copy -> server copy wins, no duplicate
    stale = _doc()
    stale["problems"][0]["state"] = {"userInput": "", "score": 0, "reviews": [base_review]}
    ps.save_progress(stale)
    after_stale = ps.load_progress("DRL-MTH-X-01")["problems"]["Q01"]["reviews"]
    assert len(after_stale) == 1
    assert after_stale[0]["verdict"] == "pass"
    assert after_stale[0]["explain"] == "Uses a linear scan with O(1) space."
    assert after_stale[0]["findings"][0]["disputed"]["issueId"] == "ISS-42"


def test_save_progress_merges_session_summary_and_preserves_sync_stamps():
    """Python parity with TS writeProgress: field-wise sessionSummary merge preserves
    syncedToNotionAt / notionPageId / syncedFingerprint against later autosaves lacking them,
    explicit None/empty clears, or older timestamps; only a newer stamp replaces them."""
    synced = _doc()
    synced["problems"][0]["state"] = {"userInput": "5", "score": 1}
    synced["sessionSummary"] = {
        "practiceStatus": "Graded",
        "score": 1,
        "maxScore": 2,
        "accuracyPct": 50,
        "attemptDate": "2026-11-21",
        "divergedStepsSummary": "No diverged steps logged.",
        "syncedToNotionAt": "2026-11-21T16:40:00.000Z",
        "notionPageId": "page-123",
        "syncedFingerprint": "fp-v1",
    }
    ps.save_progress(synced)

    # 1. Later autosave with summary lacking stamps keeps all three stamps and omitted fields
    autosave = _doc()
    autosave["problems"][0]["state"] = {"userInput": "5", "score": 1, "revisitNote": "Check sign"}
    autosave["sessionSummary"] = {
        "practiceStatus": "Graded",
        "score": 1,
        "divergedStepsSummary": "Q01 (Note: edited)",
    }
    ps.save_progress(autosave)
    after_auto = ps.load_progress("DRL-MTH-X-01")["sessionSummary"]
    assert after_auto["syncedToNotionAt"] == "2026-11-21T16:40:00.000Z"
    assert after_auto["notionPageId"] == "page-123"
    assert after_auto["syncedFingerprint"] == "fp-v1"
    assert after_auto["attemptDate"] == "2026-11-21"
    assert after_auto["divergedStepsSummary"] == "Q01 (Note: edited)"

    # 2. Incoming None / empty strings cannot clear stamps
    clear_attempt = _doc()
    clear_attempt["problems"][0]["state"] = {"userInput": "5", "score": 1}
    clear_attempt["sessionSummary"] = {
        "practiceStatus": "Ready",
        "score": 0,
        "syncedToNotionAt": None,
        "notionPageId": "",
        "syncedFingerprint": None,
    }
    ps.save_progress(clear_attempt)
    after_clear = ps.load_progress("DRL-MTH-X-01")["sessionSummary"]
    assert after_clear["syncedToNotionAt"] == "2026-11-21T16:40:00.000Z"
    assert after_clear["notionPageId"] == "page-123"
    assert after_clear["syncedFingerprint"] == "fp-v1"

    # 3. Older stamp cannot downgrade newer stamp
    older = _doc()
    older["problems"][0]["state"] = {"userInput": "5", "score": 1}
    older["sessionSummary"] = {
        "syncedToNotionAt": "2026-11-21T15:00:00.000Z",
        "notionPageId": "page-old",
        "syncedFingerprint": "fp-old",
    }
    ps.save_progress(older)
    after_older = ps.load_progress("DRL-MTH-X-01")["sessionSummary"]
    assert after_older["syncedToNotionAt"] == "2026-11-21T16:40:00.000Z"
    assert after_older["notionPageId"] == "page-123"
    assert after_older["syncedFingerprint"] == "fp-v1"

    # 4. Newer server stamp replaces them
    newer = _doc()
    newer["problems"][0]["state"] = {"userInput": "5", "score": 1}
    newer["sessionSummary"] = {
        "syncedToNotionAt": "2026-11-21T16:45:00.000Z",
        "notionPageId": "page-456",
        "syncedFingerprint": "fp-v2",
    }
    ps.save_progress(newer)
    after_newer = ps.load_progress("DRL-MTH-X-01")["sessionSummary"]
    assert after_newer["syncedToNotionAt"] == "2026-11-21T16:45:00.000Z"
    assert after_newer["notionPageId"] == "page-456"
    assert after_newer["syncedFingerprint"] == "fp-v2"


def test_is_timestamp_in_cycle_handles_mixed_precision_and_zones():
    assert ps.is_timestamp_in_cycle("2026-11-20T10:00:00Z", "2026-11-20T10:00:00.900Z") is False
    assert ps.is_timestamp_in_cycle("2026-11-20T10:00:00Z", "2026-11-20T10:00:00.000Z") is True
    assert ps.is_timestamp_in_cycle("2026-11-20T17:00:00+07:00", "2026-11-20T10:00:00.000Z") is True
    assert ps.is_timestamp_in_cycle("2026-11-20T10:00:00+07:00", "2026-11-20T04:00:00Z") is False
    assert ps.is_timestamp_in_cycle("2026-11-20T10:00:00.123Z", "2026-11-20T10:00:00.123456Z") is True
    assert ps.is_timestamp_in_cycle("not-a-timestamp", "2026-11-20T10:00:00Z") is False
