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
    roots = _write(tmp_path, {"D1": [("Q1", 1, "direct", None, assisted)]})
    (item,) = ws.load_items(*roots)
    assert item.score == 0.5 and item.assisted


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
