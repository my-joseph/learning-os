"""Unit vs chapter scope: a unit drill uses only its unit's archetypes; a chapter drill covers all its units."""

import json

from math_engine.ai_drill_ingest import load_scope_archetypes, mark_context_used
from notion_sync.drill_sync import unit_relation_ids


def _vault(tmp_path):
    (tmp_path / "MTH-T09-C01.json").write_text(
        json.dumps(
            {
                "archetypes": [
                    {"archetypeKey": "a-u1", "unitCode": "MTH-T09-C01-U01", "level": 1},
                    {"archetypeKey": "a-u2", "unitCode": "MTH-T09-C01-U02", "level": 2},
                    {"archetypeKey": "a-chapter", "level": 4},
                    {"archetypeKey": "a-misplaced", "unitCode": "MTH-T09-C02-U01", "level": 2},
                ]
            }
        )
    )
    (tmp_path / "MTH-T09-C01-U03.json").write_text(json.dumps({"archetypes": [{"archetypeKey": "a-u3", "level": 1}]}))
    return str(tmp_path)


def _keys(code, vd):
    return sorted(a["archetypeKey"] for a in load_scope_archetypes(code, vd))


def test_unit_scope_is_exclusive(tmp_path):
    vd = _vault(tmp_path)
    assert _keys("MTH-T09-C01-U01", vd) == ["a-u1"]
    assert _keys("MTH-T09-C01-U03", vd) == ["a-u3"]  # a unit vault file
    assert _keys("MTH-T09-C02-U01", vd) == ["a-misplaced"]  # tagged to another chapter's unit


def test_chapter_scope_covers_its_units_only(tmp_path):
    vd = _vault(tmp_path)
    assert _keys("MTH-T09-C01", vd) == ["a-chapter", "a-u1", "a-u2", "a-u3"]
    assert _keys("MTH-T09-C02", vd) == ["a-misplaced"]


def test_used_context_is_written_where_the_archetype_lives(tmp_path):
    vd = _vault(tmp_path)
    mark_context_used("MTH-T09-C01-U01", "a-u1", "bakery", vault_dir=vd)
    chapter = json.loads((tmp_path / "MTH-T09-C01.json").read_text())
    assert next(a for a in chapter["archetypes"] if a["archetypeKey"] == "a-u1")["usedContexts"] == ["bakery"]
    assert not (tmp_path / "MTH-T09-C01-U01.json").exists()
    assert "_vaultFile" not in json.dumps(chapter)


def test_sync_links_every_unit_a_drill_covers():
    id_map = {"MTH-T09-C01-U01": {"id": "p1"}, "MTH-T09-C01-U02": {"id": "p2"}}
    chapter_drill = {"problems": [{"unitCode": "MTH-T09-C01-U02"}, {"unitCode": "MTH-T09-C01-U01"}, {}]}
    assert unit_relation_ids(chapter_drill, "MTH-T09-C01", id_map) == ["p2", "p1"]
    assert unit_relation_ids({"problems": [{}]}, "MTH-T09-C01-U01", id_map) == ["p1"]


def test_update_unit_reviews_writes_only_pages_with_review_fields(monkeypatch):
    from notion_sync import drill_sync

    calls = []

    def fake_request(method, endpoint, token, payload=None):
        calls.append((method, endpoint, payload))
        if method == "GET":
            has = endpoint.endswith("p1")
            return {
                "properties": {"Mastery (0-4)": {"number": None}, "Last Reviewed": {}, "Next Review": {}} if has else {}
            }
        return {}

    monkeypatch.setattr(drill_sync, "notion_request", fake_request)
    import scripts.weak_spots as ws

    monkeypatch.setattr(
        ws, "review_update", lambda unit, cur, d: {"mastery": 2, "lastReviewed": d, "nextReview": "2026-11-15"}
    )
    id_map = {"U1": {"id": "p1"}, "U2": {"id": "p2"}}
    out = drill_sync.update_unit_reviews(["U1", "U2"], "2026-11-10", id_map, "tok")
    assert out == {"U1": {"mastery": 2, "lastReviewed": "2026-11-10", "nextReview": "2026-11-15"}}
    patch = [c for c in calls if c[0] == "PATCH"]
    assert len(patch) == 1 and patch[0][2]["properties"]["Mastery (0-4)"] == {"number": 2}


def test_prg_vaults_all_have_valid_unit_codes():
    import glob
    import re

    vaults = sorted(glob.glob("code_engine/reasoning_vault/PRG-*.json"))
    assert len(vaults) >= 3
    for path in vaults:
        data = json.loads(open(path, encoding="utf-8").read())
        for arch in data["archetypes"]:
            uc = arch.get("unitCode", "")
            assert re.match(r"^PRG-T\d{2}-C\d{2}-U\d{2}$", uc), (
                f"{path}: {arch.get('archetypeKey')} bad unitCode {uc!r}"
            )


def test_prg_load_scope_archetypes_and_ingest_unit_stamp(tmp_path):
    from code_engine import ai_drill_ingest as cai

    vault_dir = tmp_path / "vault"
    vault_dir.mkdir()
    (vault_dir / "PRG-T09-C01.json").write_text(
        json.dumps(
            {
                "unitCode": "PRG-T09-C01",
                "archetypes": [
                    {
                        "archetypeKey": "a-u1",
                        "unitCode": "PRG-T09-C01-U01",
                        "level": 1,
                        "cognitiveTraps": [{"trapTag": "empty-list-nan"}],
                        "qualityChecks": [
                            {
                                "id": "QC-test-u1",
                                "check": "Returns a fresh value",
                                "why": "Avoids shared state",
                                "severity": "must",
                                "knownBad": {"code": "const x = 1;", "caughtBy": "review"},
                            }
                        ],
                    },
                    {"archetypeKey": "a-u2", "unitCode": "PRG-T09-C01-U02", "level": 2},
                ],
            }
        ),
        encoding="utf-8",
    )
    assert [a["archetypeKey"] for a in cai.load_scope_archetypes("PRG-T09-C01-U01", str(vault_dir))] == ["a-u1"]
    assert sorted(a["archetypeKey"] for a in cai.load_scope_archetypes("PRG-T09-C01", str(vault_dir))) == [
        "a-u1",
        "a-u2",
    ]

    drill_doc = {
        "unitCode": "PRG-T09-C01",
        "drillId": "DRL-PRG-T09-C01-99",
        "blindSolve": [{"problemId": "Q01", "passed": True}],
        "review": {"verdict": "pass", "note": "Scope and trap verified."},
        "problems": [
            {
                "id": "Q01",
                "archetype": "problem-solving",
                "archetypeKey": "a-u1",
                "commonTrapTag": "empty-list-nan",
                "context": "order_totals",
                "level": 1,
                "entryPoint": "sumPrices",
                "prompt": "Implement `sumPrices(items)`.",
                "starterCode": "function sumPrices(_items) {\n  return 0;\n}\nmodule.exports = { sumPrices };\n",
                "solutionCode": "function sumPrices(items) {\n  return items.reduce((acc, n) => acc + n, 0);\n}\nmodule.exports = { sumPrices };\n",
                "trapMutant": "function sumPrices(items) {\n  return items.length ? items.reduce((acc, n) => acc + n, 0) : NaN;\n}\nmodule.exports = { sumPrices };\n",
                "visibleTests": [
                    {"name": "sums positive prices", "testCode": "assert.strictEqual(sumPrices([2, 3]), 5);"}
                ],
                "hiddenTests": [{"name": "handles empty list", "testCode": "assert.strictEqual(sumPrices([]), 0);"}],
                "steps": [{"explain": "Accumulate item prices starting from zero."}],
            }
        ],
    }
    saved = cai.ingest_ai_code_drill(
        drill_doc,
        data_root=str(tmp_path / "data"),
        workspace_root=str(tmp_path / "ws"),
        vault_dir=str(vault_dir),
    )
    assert saved["problems"][0]["unitCode"] == "PRG-T09-C01-U01"
    chapter_vault = json.loads((vault_dir / "PRG-T09-C01.json").read_text(encoding="utf-8"))
    assert chapter_vault["archetypes"][0]["usedContexts"] == ["order_totals"]
    assert not (vault_dir / "PRG-T09-C01-U01.json").exists()
