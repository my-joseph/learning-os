"""Notion client behavior (fully mocked: no network, no Notion writes)."""

import io
import json
import urllib.error

import pytest

import notion_client
from notion_client import load_env, notion_request


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


def test_old_import_path_still_works():
    import apply_rules_and_test_pages as a

    assert a.notion_request is notion_request and a.load_env is load_env
