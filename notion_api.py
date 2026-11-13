# -*- coding: utf-8 -*-
"""Shared Notion REST client used by every builder / sync script.

Kept dependency-free (urllib only) so it runs from any venv.

Behaviour notes:
- TLS is always verified. If the macOS system bundle exists it is used,
  otherwise Python's default trust store.
- Only transient failures are retried: network errors, 409 (conflict),
  429 (rate limit, honours Retry-After) and 5xx. A 400/401/403/404 fails
  immediately with Notion's error body, instead of sleeping ~95s first.
- `replace_page_blocks` appends the new content BEFORE deleting the old,
  so a network failure midway never leaves a page empty.
"""
import json
import os
import socket
import ssl
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

NOTION_VERSION = "2022-06-28"
RETRYABLE_STATUS = {409, 429, 500, 502, 503, 504}

socket.setdefaulttimeout(15)


def load_env(path=".env"):
    env = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    return env


# Force IPv4 to avoid macOS / Cloudflare IPv6 socket hang.
_orig_getaddrinfo = socket.getaddrinfo


def _getaddrinfo_ipv4(host, port, family=0, type=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)


socket.getaddrinfo = _getaddrinfo_ipv4


def make_ssl_context():
    if os.path.exists("/etc/ssl/cert.pem"):
        return ssl.create_default_context(cafile="/etc/ssl/cert.pem")
    return ssl.create_default_context()


SSL_CTX = make_ssl_context()


class MissingNotionToken(RuntimeError):
    """Raised before any network call when no Notion token was loaded."""


def require_token(token):
    if not token or str(token).strip() in ("", "None"):
        env_path = os.path.join(os.getcwd(), ".env")
        where = "exists but has no NOTION_TOKEN" if os.path.exists(env_path) else "does not exist"
        raise MissingNotionToken(
            f"NOTION_TOKEN not found: {env_path} {where}. "
            "Run this script from the repo root that holds your .env "
            "(git worktrees do not copy .env)."
        )
    return token


def notion_request(method, endpoint, token, payload=None, max_retries=7):
    require_token(token)
    url = f"https://api.notion.com/v1/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
        "Connection": "close",
    }
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    for attempt in range(max_retries):
        last = attempt == max_retries - 1
        try:
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            if e.code not in RETRYABLE_STATUS or last:
                raise RuntimeError(f"HTTP {e.code} on {method} {endpoint}: {body}") from e
            retry_after = e.headers.get("Retry-After") if e.headers else None
            try:
                wait = float(retry_after) if retry_after else 1.5 * (2 ** attempt)
            except ValueError:
                wait = 1.5 * (2 ** attempt)
            time.sleep(min(wait, 60))
        except (urllib.error.URLError, ConnectionResetError, ssl.SSLError, TimeoutError, OSError):
            if last:
                raise
            time.sleep(1.5 * (2 ** attempt))


def get_all_blocks(block_id, token):
    blocks = []
    cursor = None
    while True:
        ep = f"blocks/{block_id}/children?page_size=100"
        if cursor:
            ep += f"&start_cursor={cursor}"
        res = notion_request("GET", ep, token)
        blocks.extend(res.get("results", []))
        if not res.get("has_more"):
            break
        cursor = res.get("next_cursor")
    return blocks


def append_blocks(page_id, blocks, token, chunk_size=50):
    for i in range(0, len(blocks), chunk_size):
        notion_request("PATCH", f"blocks/{page_id}/children", token, {"children": blocks[i:i + chunk_size]})


def replace_page_content(page_id, new_blocks, token, label=""):
    """Append new blocks first, then delete the old ones.

    If appending fails, the old content is still there (plus a partial
    copy at the end), so nothing is lost. Delete failures are reported,
    not swallowed.
    """
    old_ids = [b["id"] for b in get_all_blocks(page_id, token)]
    append_blocks(page_id, new_blocks, token)

    failed = []

    def _delete(b_id):
        try:
            notion_request("DELETE", f"blocks/{b_id}", token)
        except Exception as exc:  # noqa: BLE001 - collect and report below
            failed.append((b_id, str(exc)[:200]))

    with ThreadPoolExecutor(max_workers=5) as pool:
        list(pool.map(_delete, old_ids))
    if failed:
        print(f"  WARNING [{label or page_id}]: {len(failed)} old block(s) could not be deleted:")
        for b_id, err in failed[:5]:
            print(f"    - {b_id}: {err}")
    return failed
