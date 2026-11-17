"""scripts/weak_spots.py: weak spots, closing and level advice from learner progress (rules/07 §2-3)."""

import json

from scripts import weak_spots as ws

TRAP = "c04-divide-not-invert-trap"


def _write(tmp_path, drills):
    """drills: {drill_id: [(pid, level, form, trap, state), ...]}"""
    data, prog = tmp_path / "data" / "MTH-T09-C01-U01", tmp_path / "progress"
    data.mkdir(parents=True)
    prog.mkdir()
    for did, probs in drills.items():
        (data / f"{did}.json").write_text(
            json.dumps(
                {
                    "drillId": did,
                    "unitCode": "MTH-T09-C01-U01",
                    "problems": [
                        {"id": p, "level": lv, "form": form, "commonTrapTag": trap, "archetypeKey": "arch"}
                        for p, lv, form, trap, _ in probs
                    ],
                }
            )
        )
        (prog / f"{did}.json").write_text(json.dumps({"drillId": did, "problems": {p: st for p, *_, st in probs}}))
    return str(tmp_path / "data"), str(prog)


def _att(verdict, ts, trap=None, **kw):
    a = {"verdict": verdict, "ts": ts, **kw}
    if trap:
        a["matchedTrap"] = trap
    return a


def _wrong(ts):
    return {"attempts": [_att("incorrect", ts, TRAP), _att("correct", ts + "z")], "score": 1}


def _right(ts, **kw):
    return {"attempts": [_att("correct", ts)], "score": 1, **kw}


def test_trap_matched_twice_is_open_weak_spot(tmp_path):
    roots = _write(
        tmp_path,
        {"D1": [("Q1", 2, "direct", TRAP, _wrong("2026-11-01")), ("Q2", 2, "direct", TRAP, _wrong("2026-11-02"))]},
    )
    out = ws.report(None, *roots)
    assert f"WEAK     {TRAP}: matched 2x in 1 drill(s)" in out
    assert f"NEXT     new drill for MTH-T09-C01-U01 focused on {TRAP}" in out


def test_weak_spot_closes_after_two_clean_drills_and_reopens(tmp_path):
    hits = [("Q1", 2, "direct", TRAP, _wrong("2026-11-01")), ("Q2", 2, "direct", TRAP, _wrong("2026-11-02"))]
    clean = {
        "D2": [("Q1", 2, "direct", TRAP, _right("2026-11-03"))],
        "D3": [("Q1", 2, "direct", TRAP, _right("2026-11-04"))],
    }
    roots = _write(tmp_path / "a", {"D1": hits, **clean})
    assert f"closed   {TRAP}" in ws.report(None, *roots)
    roots = _write(tmp_path / "b", {"D1": hits, **clean, "D4": [("Q1", 2, "direct", TRAP, _wrong("2026-11-05"))]})
    assert f"WEAK     {TRAP}: matched 3x" in ws.report(None, *roots)


def test_assisted_answers_do_not_count_as_full_marks(tmp_path):
    assisted = _right("2026-11-01", setupRevealedBeforeAnswer=True)
    roots = _write(tmp_path / "setup", {"D1": [("Q1", 1, "direct", None, assisted)]})
    (item,) = ws.load_items(*roots)
    assert item.score == 0.5 and item.assisted

    sol_state = _right("2026-11-01", solutionRevealedBeforeAnswer=True)
    roots_sol = _write(tmp_path / "sol_state", {"D1": [("Q1", 1, "direct", None, sol_state)]})
    (item_sol,) = ws.load_items(*roots_sol)
    assert item_sol.score == 0.5 and item_sol.assisted

    sol_attempt = {"attempts": [{"verdict": "correct", "ts": "2026-11-01", "solutionRevealed": True}], "score": 1}
    roots_att = _write(tmp_path / "sol_attempt", {"D1": [("Q1", 1, "direct", None, sol_attempt)]})
    (item_att,) = ws.load_items(*roots_att)
    assert item_att.score == 0.5 and item_att.assisted


def test_level_advice_needs_80_percent_with_a_reverse_item(tmp_path):
    probs = [(f"Q{i}", 3, "reverse" if i == 1 else "direct", None, _right(f"2026-11-0{i}")) for i in range(1, 6)]
    roots = _write(tmp_path / "up", {"D1": probs})
    assert ws.level_advice(ws.load_items(*roots))[3]["move"] == "up"
    no_reverse = [(p, lv, "direct", t, st) for p, lv, _, t, st in probs]
    roots = _write(tmp_path / "stay", {"D1": no_reverse})
    assert ws.level_advice(ws.load_items(*roots))[3]["move"] == "stay"
    wrong = [
        (p, lv, f, t, {"attempts": [_att("incorrect", st["attempts"][0]["ts"])], "score": 0})
        for p, lv, f, t, st in probs
    ]
    roots = _write(tmp_path / "down", {"D1": wrong})
    assert ws.level_advice(ws.load_items(*roots))[3]["move"] == "down"


def test_unattempted_problems_and_scope_filter(tmp_path):
    roots = _write(tmp_path, {"D1": [("Q1", 1, "direct", None, {}), ("Q2", 1, "direct", None, _right("2026-11-01"))]})
    assert [i.pid for i in ws.load_items(*roots)] == ["Q2"]
    assert "No practice data yet for MTH-T09-C02" in ws.report("MTH-T09-C02", *roots)
    assert "MTH-T09-C01-U01" in ws.report("MTH-T09-C01", *roots)


def test_unit_comes_from_the_archetype_when_the_problem_has_none(tmp_path, monkeypatch):
    vault = tmp_path / "math_engine" / "reasoning_vault"
    vault.mkdir(parents=True)
    (vault / "MTH-T09-C01.json").write_text(
        json.dumps({"archetypes": [{"archetypeKey": "arch", "unitCode": "MTH-T09-C01-U04"}]})
    )
    data, prog = tmp_path / "data" / "MTH-T09-C01", tmp_path / "progress"
    data.mkdir(parents=True)
    prog.mkdir()
    (data / "D1.json").write_text(
        json.dumps(
            {"drillId": "D1", "unitCode": "MTH-T09-C01", "problems": [{"id": "Q1", "level": 1, "archetypeKey": "arch"}]}
        )
    )
    (prog / "D1.json").write_text(json.dumps({"drillId": "D1", "problems": {"Q1": _right("2026-11-01")}}))
    monkeypatch.chdir(tmp_path)
    (item,) = ws.load_items(str(tmp_path / "data"), str(prog))
    assert item.unit == "MTH-T09-C01-U04"


def _items(scores_levels):
    return [
        ws.Item("D", "U", f"Q{n}", lv, "direct", None, None, f"2026-11-{n + 1:02d}", sc, False, False)
        for n, (sc, lv) in enumerate(scores_levels)
    ]


def test_suggest_mastery_ladder():
    assert ws.suggest_mastery([], False) is None
    assert ws.suggest_mastery(_items([(0, 1), (0.5, 1), (0, 2)]), False) == 1
    assert ws.suggest_mastery(_items([(1, 1), (1, 2), (0.5, 3)]), False) == 2
    strong = _items([(1, 1), (1, 2), (1, 3), (1, 3), (0.5, 4)])
    assert ws.suggest_mastery(strong, False) == 3
    assert ws.suggest_mastery(strong, True) == 2  # an open weak spot caps it


def test_review_update_keeps_learner_set_4_and_schedules(tmp_path):
    roots = _write(tmp_path, {"D1": [(f"Q{i}", 3, "direct", None, _right(f"2026-11-0{i}")) for i in range(1, 5)]})
    upd = ws.review_update("MTH-T09-C01-U01", None, "2026-11-10T09:00:00Z", *roots)
    assert upd == {"mastery": 3, "lastReviewed": "2026-11-10", "nextReview": "2026-11-27"}
    assert ws.review_update("MTH-T09-C01-U01", 4, "2026-11-10", *roots)["mastery"] == 4
    assert ws.review_update("MTH-T09-C02-U01", None, "2026-11-10", *roots) is None


def test_cli_json_flag_outputs_math_traps_and_empty_scope(tmp_path, capsys):
    roots = _write(
        tmp_path,
        {"D1": [("Q1", 2, "direct", TRAP, _wrong("2026-11-01")), ("Q2", 2, "direct", TRAP, _wrong("2026-11-02"))]},
    )
    rc = ws.main(["MTH-T09-C01-U01", "--data-root", roots[0], "--progress-dir", roots[1], "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["scope"] == "MTH-T09-C01-U01"
    assert len(payload["units"]) == 1
    unit = payload["units"][0]
    assert unit["unitCode"] == "MTH-T09-C01-U01"
    assert unit["subject"] == "MTH"
    assert [t["id"] for t in unit["open"]] == [TRAP]
    assert unit["open"][0]["matches"] == 2

    rc_empty = ws.main(["MTH-T09-C99-U01", "--data-root", roots[0], "--progress-dir", roots[1], "--json"])
    assert rc_empty == 0
    empty_payload = json.loads(capsys.readouterr().out)
    assert empty_payload == {"scope": "MTH-T09-C99-U01", "units": []}
