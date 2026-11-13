"""Notion client behavior (fully mocked: no network, no Notion writes)."""

import io
import json
import urllib.error

import pytest

from notion_sync import client as notion_client
from notion_sync.client import load_env, notion_request


class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_load_env_parses_comments_and_values(tmp_path):
    f = tmp_path / ".env"
    f.write_text("# c\nNOTION_TOKEN=abc=def\n\nBAD LINE\nX = y \n", encoding="utf-8")
    assert load_env(str(f)) == {"NOTION_TOKEN": "abc=def", "X": "y"}


def test_load_env_missing_file_is_empty(tmp_path):
    assert load_env(str(tmp_path / "nope")) == {}


def test_request_sends_headers_and_json(monkeypatch):
    seen = {}

    def fake_urlopen(req, context=None, timeout=None):
        seen["url"], seen["method"] = req.full_url, req.get_method()
        seen["auth"] = req.get_header("Authorization")
        seen["body"] = json.loads(req.data)
        return FakeResp(b'{"ok": true}')

    monkeypatch.setattr(notion_client.urllib.request, "urlopen", fake_urlopen)
    assert notion_request("POST", "pages", "tok", {"a": 1}) == {"ok": True}
    assert seen == {"url": "https://api.notion.com/v1/pages", "method": "POST", "auth": "Bearer tok", "body": {"a": 1}}


def test_request_retries_then_succeeds(monkeypatch):
    calls = {"n": 0}
    monkeypatch.setattr(notion_client.time, "sleep", lambda s: None)

    def flaky(req, context=None, timeout=None):
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionResetError()
        return FakeResp(b"{}")

    monkeypatch.setattr(notion_client.urllib.request, "urlopen", flaky)
    assert notion_request("GET", "x", "t") == {}
    assert calls["n"] == 3


def test_request_http_error_after_retries_raises_runtime_error(monkeypatch):
    monkeypatch.setattr(notion_client.time, "sleep", lambda s: None)

    def boom(req, context=None, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 400, "bad", {}, io.BytesIO(b"nope"))

    monkeypatch.setattr(notion_client.urllib.request, "urlopen", boom)
    with pytest.raises(RuntimeError, match="HTTP 400"):
        notion_request("GET", "x", "t", max_retries=2)


def test_archived_scripts_keep_their_import_path(monkeypatch):
    # Archived scripts run as `python3 archive/<script>.py`, so archive/ is on sys.path and they
    # import `apply_rules_and_test_pages`; it must hand them the live client and block helpers.
    import os
    import sys

    from notion_sync import blocks

    monkeypatch.syspath_prepend(os.path.join(os.path.dirname(os.path.dirname(__file__)), "archive"))
    sys.modules.pop("apply_rules_and_test_pages", None)
    import apply_rules_and_test_pages as a

    assert a.notion_request is notion_request and a.load_env is load_env
    assert a.parse_rt is blocks.parse_rt and a.callout_block is blocks.callout_block


def test_worktree_reads_main_checkout_env(tmp_path, monkeypatch):
    main = tmp_path / "main"
    (main / ".git" / "worktrees" / "wt").mkdir(parents=True)
    (main / ".env").write_text("NOTION_TOKEN=from-main\n", encoding="utf-8")
    wt = tmp_path / "wt"
    wt.mkdir()
    (wt / ".git").write_text(f"gitdir: {main / '.git' / 'worktrees' / 'wt'}\n", encoding="utf-8")
    monkeypatch.chdir(wt)
    assert load_env() == {"NOTION_TOKEN": "from-main"}
    (wt / ".env").write_text("NOTION_TOKEN=local\n", encoding="utf-8")
    assert load_env() == {"NOTION_TOKEN": "local"}, "a worktree's own .env still wins"


def test_plain_checkout_without_env_is_empty(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()
    monkeypatch.chdir(tmp_path)
    assert load_env() == {}
