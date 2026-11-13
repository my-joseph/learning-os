# -*- coding: utf-8 -*-
"""Shared Notion REST client (stdlib only): .env loader, IPv4 patch, SSL context, retrying request.

Moved verbatim from apply_rules_and_test_pages.py (P2 refactor). Importing this module applies the
process-wide IPv4-only and 15s default socket timeout settings, exactly as before.
"""

import json
import os
import socket
import ssl
import time
import urllib.error
import urllib.request

socket.setdefaulttimeout(15)


def load_env(path=".env"):
    env = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    return env


# Force IPv4 to avoid macOS / Cloudflare IPv6 socket hang
orig_getaddrinfo = socket.getaddrinfo


def getaddrinfo_ipv4(host, port, family=0, type=0, proto=0, flags=0):
    return orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)


socket.getaddrinfo = getaddrinfo_ipv4

SSL_CTX = (
    ssl.create_default_context(cafile="/etc/ssl/cert.pem")
    if os.path.exists("/etc/ssl/cert.pem")
    else ssl._create_unverified_context()
)


def notion_request(method, endpoint, token, payload=None, max_retries=7):
    url = f"https://api.notion.com/v1/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
        "Connection": "close",
    }
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            ConnectionResetError,
            ssl.SSLError,
            TimeoutError,
            OSError,
        ) as e:
            if attempt < max_retries - 1:
                wait = 1.5 * (2**attempt)
                time.sleep(wait)
                continue
            if isinstance(e, urllib.error.HTTPError):
                body = e.read().decode("utf-8", errors="ignore")
                raise RuntimeError(f"HTTP {e.code} on {method} {endpoint}: {body}") from e
            raise e


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
