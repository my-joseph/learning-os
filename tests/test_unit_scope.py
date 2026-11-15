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
