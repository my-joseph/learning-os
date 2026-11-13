"""Guards for bugs that were found in the refactor audit (2026-11-13).

- LaTeX in normal Python strings: "\\frac" silently becomes form-feed + "rac".
- TLS verification must never be disabled.
- Notion client: no retry on non-transient 4xx; replace = append-then-delete.
"""

from __future__ import annotations

import ast
import io
import os
import subprocess
import unittest
import urllib.error
import warnings
from unittest import mock

import notion_client

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTROL_CHARS = "\f\b\x0b\a"
# Intentionally contains control chars: it repairs corrupted LaTeX.
CONTROL_CHAR_ALLOWLIST = {
    "math_engine/ai_drill_ingest.py",
    "tests/test_ai_drill_ingest.py",
    "tests/test_codebase_guards.py",  # defines CONTROL_CHARS itself
}


def tracked_python_files():
    out = subprocess.run(["git", "ls-files", "*.py"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [p for p in out.split() if os.path.isfile(os.path.join(ROOT, p))]


class LatexEscapeGuard(unittest.TestCase):
    def test_no_invalid_escapes_or_control_chars(self):
        problems = []
        for rel in tracked_python_files():
            with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
                src = f.read()
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                tree = ast.parse(src, filename=rel)
            for w in caught:
                if issubclass(w.category, (SyntaxWarning, DeprecationWarning)):
                    problems.append(f"{rel}:{w.lineno}: {w.message}")
            if rel in CONTROL_CHAR_ALLOWLIST:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    if any(c in node.value for c in CONTROL_CHARS):
                        problems.append(f"{rel}:{node.lineno}: control char in string (unescaped LaTeX like \\frac?)")
        self.assertEqual(problems, [], "\n".join(problems))

    def test_tls_verification_never_disabled(self):
        offenders = []
        for rel in tracked_python_files():
            if rel == "tests/test_codebase_guards.py":
                continue
            with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
                if "_create_unverified_context" in f.read():
                    offenders.append(rel)
        self.assertEqual(offenders, [])


def _http_error(code, headers=None):
    return urllib.error.HTTPError(
        "https://api.notion.com/v1/x", code, "err", headers or {}, io.BytesIO(b'{"message":"bad"}')
    )


class NotionRequestRetry(unittest.TestCase):
    @mock.patch("notion_client.time.sleep")
    @mock.patch("notion_client.urllib.request.urlopen")
    def test_400_fails_fast(self, urlopen, sleep):
        urlopen.side_effect = _http_error(400)
        with self.assertRaises(RuntimeError) as ctx:
            notion_client.notion_request("GET", "x", "tok")
        self.assertIn("HTTP 400", str(ctx.exception))
        self.assertEqual(urlopen.call_count, 1)
        sleep.assert_not_called()

    @mock.patch("notion_client.time.sleep")
    @mock.patch("notion_client.urllib.request.urlopen")
    def test_429_retries_with_retry_after(self, urlopen, sleep):
        ok = mock.MagicMock()
        ok.__enter__.return_value.read.return_value = b'{"ok": true}'
        urlopen.side_effect = [_http_error(429, {"Retry-After": "2"}), ok]
        self.assertEqual(notion_client.notion_request("GET", "x", "tok"), {"ok": True})
        sleep.assert_called_once_with(2.0)


class MissingToken(unittest.TestCase):
    @mock.patch("notion_client.urllib.request.urlopen")
    def test_missing_token_fails_before_any_request(self, urlopen):
        for token in (None, "", "None", "  "):
            with self.subTest(token=token):
                with self.assertRaisesRegex(notion_client.MissingNotionToken, "NOTION_TOKEN not found"):
                    notion_client.notion_request("GET", "x", token)
        urlopen.assert_not_called()


class ReplacePageContent(unittest.TestCase):
    def test_appends_before_deleting(self):
        calls = []

        def fake(method, endpoint, token, payload=None, **_):
            calls.append((method, endpoint))
            if method == "GET":
                return {"results": [{"id": "old1"}, {"id": "old2"}], "has_more": False}
            return {}

        with mock.patch("notion_client.notion_request", side_effect=fake):
            failed = notion_client.replace_page_content("page", [{"type": "divider"}], "tok")

        self.assertEqual(failed, [])
        methods = [m for m, _ in calls]
        self.assertLess(methods.index("PATCH"), methods.index("DELETE"))
        self.assertEqual(sorted(e for m, e in calls if m == "DELETE"), ["blocks/old1", "blocks/old2"])

    def test_old_content_kept_when_append_fails(self):
        def fake(method, endpoint, token, payload=None, **_):
            if method == "GET":
                return {"results": [{"id": "old1"}], "has_more": False}
            if method == "PATCH":
                raise RuntimeError("network down")
            raise AssertionError("must not delete when append failed")

        with mock.patch("notion_client.notion_request", side_effect=fake):
            with self.assertRaises(RuntimeError):
                notion_client.replace_page_content("page", [{"type": "divider"}], "tok")


if __name__ == "__main__":
    unittest.main()
