from __future__ import annotations

from notion_sync import client


def test_delete_failures_are_logged_to_stderr(monkeypatch, capsys):
    monkeypatch.setattr(client, "get_all_blocks", lambda *_: [{"id": "old-block"}])
    monkeypatch.setattr(client, "append_blocks", lambda *_args, **_kwargs: None)

    def fail_delete(method, endpoint, token, payload=None):
        raise RuntimeError("delete rejected")

    monkeypatch.setattr(client, "notion_request", fail_delete)
    failed = client.replace_page_content("page", [{"type": "divider"}], "token", "test page")

    captured = capsys.readouterr()
    assert failed == [("old-block", "delete rejected")]
    assert captured.out == ""
    assert "WARNING [test page]" in captured.err
    assert "old-block: delete rejected" in captured.err
