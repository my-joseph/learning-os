# -*- coding: utf-8 -*-
import json
import os
import ssl
import time
import urllib.error
import urllib.request

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
    }
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (409, 429, 500, 502, 503, 504) and attempt < max_retries - 1:
                wait = 1.5 * (2 ** attempt)
                time.sleep(wait)
                continue
            body = e.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"HTTP {e.code} on {method} {endpoint}: {body}") from e

def prop_val(prop):
    if not prop:
        return None
    ptype = prop.get("type")
    val = prop.get(ptype)
    if val is None:
        return None
    if ptype in ("title", "rich_text"):
        return "".join(t.get("plain_text", "") for t in val)
    if ptype in ("select", "status"):
        return val.get("name")
    if ptype == "relation":
        return [x.get("id") for x in val]
    return val

def query_all(db_id, filter_obj, token):
    results = []
    cursor = None
    while True:
        payload = {"filter": filter_obj} if filter_obj else {}
        if cursor:
            payload["start_cursor"] = cursor
        res = notion_request("POST", f"databases/{db_id}/query", token, payload)
        results.extend(res.get("results", []))
        if not res.get("has_more"):
            break
        cursor = res.get("next_cursor")
    return results

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

def get_title_prop(props):
    for k, v in props.items():
        if v.get("type") == "title":
            return k, prop_val(v)
    return None, None

def main():
    env = load_env()
    token = env.get("NOTION_TOKEN")

    topics_db = "4003818f-8ba0-8029-b434-e25399e46ef0"
    chapters_db = "4003818f-8ba0-8031-8336-f7852e0de01b"
    units_db = "4003818f-8ba0-804e-a812-f0251efb8978"
    resources_db = "40c3818f-8ba0-8098-93cf-c2fcb655f510"
    rules_id = "40c3818f-8ba0-8002-92f1-e971793125e3"

    print("=== 1. Rules Page Blocks (Detailed around key sections) ===")
    r_blocks = get_all_blocks(rules_id, token)
    for i, b in enumerate(r_blocks):
        btype = b["type"]
        txt = ""
        if btype in b and "rich_text" in b[btype]:
            txt = "".join(t.get("plain_text", "") for t in b[btype]["rich_text"])
        if (35 <= i <= 145) or (200 <= i <= 265) or (345 <= i <= 390):
            print(f"[{i:03d}] {b['id']} ({btype}): {txt}")

    print("\n=== 2. All Learning Resources (including any blank Resource ID) ===")
    resources = query_all(resources_db, None, token)
    for r in resources:
        p = r["properties"]
        tk, tv = get_title_prop(p)
        print(f"  id={r['id']} | RID='{prop_val(p.get('Resource ID'))}' | {tk}='{tv}' | URL='{prop_val(p.get('URL'))}'")

    print("\n=== 3. MTH-T02 & PRG-T03 Chapters with True Title Property ===")
    for prefix in ("MTH-T02-", "PRG-T03-"):
        chaps = query_all(chapters_db, {"property": "Full ID", "rich_text": {"starts_with": prefix}}, token)
        chaps.sort(key=lambda x: prop_val(x["properties"].get("Order")) or 999)
        for c in chaps:
            p = c["properties"]
            tk, tv = get_title_prop(p)
            print(f"  {prop_val(p.get('Full ID'))}: id={c['id']} | {tk}='{tv}' | Obj='{prop_val(p.get('Objective'))}' | Crit='{prop_val(p.get('Completion Criteria'))}' | Res={prop_val(p.get('Resources'))}")

    print("\n=== 4. Existing Page Blocks of MTH-T02, MTH-T02-C01, MTH-T02-C01-U01, PRG-T03, PRG-T03-C01, PRG-T03-C01-U01 ===")
    with open("id_map.json", "r", encoding="utf-8") as f:
        id_map = json.load(f)
    all_chaps = query_all(chapters_db, None, token)
    for c in all_chaps:
        fid = prop_val(c["properties"].get("Full ID"))
        _, tv = get_title_prop(c["properties"])
        if fid and fid in id_map:
            id_map[fid]["title"] = tv
    with open("id_map.json", "w", encoding="utf-8") as f:
        json.dump(id_map, f, ensure_ascii=False, indent=2)

    for target_fid in ("MTH-T02", "MTH-T02-C01", "MTH-T02-C01-U01", "PRG-T03", "PRG-T03-C01", "PRG-T03-C01-U01"):
        pid = id_map[target_fid]["id"]
        blks = get_all_blocks(pid, token)
        print(f"  {target_fid} ({id_map[target_fid]['title']}): {len(blks)} existing blocks")
        for b in blks[:10]:
            bt = b["type"]
            txt = "".join(t.get("plain_text", "") for t in b.get(bt, {}).get("rich_text", [])) if bt in b else ""
            print(f"    - ({bt}) {txt[:90]}")

if __name__ == "__main__":
    main()
