"""rebuild_id_map never drops the static database keys or CON-* concept keys (issue ac0b1f)."""

import json

import notion_sync.id_map as id_map


def test_rebuild_keeps_static_and_concept_keys(tmp_path, monkeypatch):
    disk = {"CON-DNS": {"id": "abc-123", "title": "DNS"}}
    (tmp_path / "id_map.json").write_text(json.dumps(disk), encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    def fake_query(db_id, token, filter_obj=None):
        if db_id == id_map.CONCEPT_VAULT_DB:
            return [{"id": "abc-123", "properties": {"Name": {"type": "title", "title": [{"plain_text": "DNS"}]}}}]
        return []

    monkeypatch.setattr(id_map, "query_all", fake_query)
    out = id_map.rebuild_id_map("token", {})
    assert out["DRILLS_DB"]["id"] == id_map.DRILLS_DB
    assert out["CONCEPT_VAULT_DB"]["id"] == id_map.CONCEPT_VAULT_DB
    assert out["CON-DNS"]["id"] == "abc-123"
