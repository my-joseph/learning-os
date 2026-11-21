# -*- coding: utf-8 -*-
"""Shared Notion REST client (stdlib only): .env loader, IPv4 patch, SSL context, retrying request.

Importing this module applies the process-wide IPv4-only and 15s default socket timeout settings.

Behaviour notes:
- TLS is always verified. If the macOS system bundle exists it is used,
  otherwise Python's default trust store.
- Only transient failures are retried: network errors, 409 (conflict),
  429 (rate limit, honours Retry-After) and 5xx. A 400/401/403/404 fails
  immediately with Notion's error body, instead of sleeping ~95s first.
- `replace_page_blocks` appends the new content BEFORE deleting the old,
  so a network failure midway never leaves a page empty.
"""

import contextvars
import json
import os
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

NOTION_VERSION = "2022-06-28"
RETRYABLE_STATUS = {409, 429, 500, 502, 503, 504}
_sync_deadline: contextvars.ContextVar[float | None] = contextvars.ContextVar("notion_sync_deadline", default=None)


@contextmanager
def sync_deadline(timeout_s: float):
    """Set a thread/task-local monotonic deadline for a complete Notion sync."""
    deadline = time.monotonic() + max(0.0, float(timeout_s))
    token = _sync_deadline.set(deadline)
    try:
        yield
    finally:
        _sync_deadline.reset(token)


def remaining_sync_seconds() -> float | None:
    """Return the active sync budget, or ``None`` when no deadline is active."""
    deadline = _sync_deadline.get()
    return None if deadline is None else deadline - time.monotonic()


def _ensure_sync_time() -> float | None:
    remaining = remaining_sync_seconds()
    if remaining is not None and remaining <= 0:
        raise TimeoutError("Notion sync deadline exceeded")
    return remaining


socket.setdefaulttimeout(15)


def main_checkout_env(cwd: str = ".") -> str | None:
    """In a git worktree `.git` is a file (`gitdir: <main>/.git/worktrees/<name>`).
    Return `<main>/.env` if it exists, so worktrees use the main checkout's secrets without copying them."""
    try:
        with open(os.path.join(cwd, ".git"), "r", encoding="utf-8") as f:
            text = f.read().strip()
    except OSError:
        return None
    if not text.startswith("gitdir:"):
        return None
    gitdir = os.path.abspath(os.path.join(cwd, text.split(":", 1)[1].strip()))
    worktrees_dir = os.path.dirname(gitdir)
    if os.path.basename(worktrees_dir) != "worktrees":
        return None
    candidate = os.path.join(os.path.dirname(os.path.dirname(worktrees_dir)), ".env")
    return candidate if os.path.exists(candidate) else None


def load_env(path: str = ".env") -> dict[str, str]:
    """Read KEY=VALUE pairs. With the default path, a git worktree falls back to the main checkout's .env."""
    env = {}
    if path == ".env" and not os.path.exists(path):
        path = main_checkout_env() or path
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    return env


# Force IPv4 to avoid macOS / Cloudflare IPv6 socket hang.
orig_getaddrinfo = socket.getaddrinfo


def getaddrinfo_ipv4(host, port, family=0, type=0, proto=0, flags=0):
    return orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)


socket.getaddrinfo = getaddrinfo_ipv4


def make_ssl_context():
    if os.path.exists("/etc/ssl/cert.pem"):
        return ssl.create_default_context(cafile="/etc/ssl/cert.pem")
    return ssl.create_default_context()


SSL_CTX = make_ssl_context()


class MissingNotionToken(RuntimeError):
    """Raised before any network call when no Notion token was loaded."""


def require_token(token: str | None) -> str:
    if not token or str(token).strip() in ("", "None"):
        env_path = os.path.join(os.getcwd(), ".env")
        where = "exists but has no NOTION_TOKEN" if os.path.exists(env_path) else "does not exist"
        raise MissingNotionToken(
            f"NOTION_TOKEN not found: {env_path} {where}. "
            "Run from the repo root (or a git worktree of it) whose main checkout holds .env."
        )
    return token


def notion_request(method: str, endpoint: str, token: str, payload: dict | None = None, max_retries: int = 7) -> dict:
    require_token(token)
    url = f"https://api.notion.com/v1/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
        "Connection": "close",
    }
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    retry_limit = min(max_retries, 4) if remaining_sync_seconds() is not None else max_retries
    for attempt in range(retry_limit):
        remaining = _ensure_sync_time()
        last = attempt == retry_limit - 1
        try:
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            timeout = min(30.0, remaining) if remaining is not None else 30.0
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            if e.code not in RETRYABLE_STATUS or last:
                raise RuntimeError(f"HTTP {e.code} on {method} {endpoint}: {body}") from e
            retry_after = e.headers.get("Retry-After") if e.headers else None
            try:
                wait = float(retry_after) if retry_after else 1.5 * (2**attempt)
            except ValueError:
                wait = 1.5 * (2**attempt)
            wait = min(wait, 60)
        except (urllib.error.URLError, ConnectionResetError, ssl.SSLError, TimeoutError, OSError):
            if last:
                raise
            wait = 1.5 * (2**attempt)
        remaining = _ensure_sync_time()
        if remaining is not None and wait >= remaining:
            raise TimeoutError("Notion sync deadline exceeded")
        time.sleep(wait)


def get_all_blocks(block_id: str, token: str) -> list[dict]:
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


def append_blocks(page_id: str, blocks: list[dict], token: str, chunk_size: int = 50) -> None:
    for i in range(0, len(blocks), chunk_size):
        _ensure_sync_time()
        notion_request("PATCH", f"blocks/{page_id}/children", token, {"children": blocks[i : i + chunk_size]})


def replace_page_content(page_id: str, new_blocks: list[dict], token: str, label: str = "") -> list[tuple[str, str]]:
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
            _ensure_sync_time()
            notion_request("DELETE", f"blocks/{b_id}", token)
        except TimeoutError:
            raise
        except Exception as exc:  # noqa: BLE001 - collect and report below
            failed.append((b_id, str(exc)[:200]))

    if remaining_sync_seconds() is not None:
        for b_id in old_ids:
            _delete(b_id)
    else:
        with ThreadPoolExecutor(max_workers=5) as pool:
            list(pool.map(_delete, old_ids))
    if failed:
        print(
            f"  WARNING [{label or page_id}]: {len(failed)} old block(s) could not be deleted:",
            file=sys.stderr,
        )
        for b_id, err in failed[:5]:
            print(f"    - {b_id}: {err}", file=sys.stderr)
    return failed
