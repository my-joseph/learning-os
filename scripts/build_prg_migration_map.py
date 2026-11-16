"""Generate docs/prg_migration_map.json from docs/prg_curriculum_v2.md and id_map.json."""

from __future__ import annotations

import json
import re
from pathlib import Path

DOC_PATH = Path("docs/prg_curriculum_v2.md")
ID_MAP_PATH = Path("id_map.json")
OUT_PATH = Path("docs/prg_migration_map.json")

# Decision §8.4: no unit's Expected Output is "Lab N"; each unit has its own concrete artefact.
UNIT_EXPECTED_OUTPUT_OVERRIDES: dict[str, str] = {
    "PRG-T01-C01-U09": "Abortable async task module + tests",
    "PRG-T01-C02-U09": "Typed API response parser + tests",
    "PRG-T01-C03-U07": "Graph cycle & BFS shortest-path module",
    "PRG-T01-C04-U05": "Regression fixtures & error-path test suite",
    "PRG-T02-C01-U07": "Typed custom hook + unit tests",
    "PRG-T02-C02-U07": "Bounded retry & fallback UI handler",
    "PRG-T02-C03-U07": "Accessible error-summary & focus-on-error form",
    "PRG-T02-C04-U06": "ARIA-compliant interactive widget + tests",
    "PRG-T02-C05-U04": "Profiler trace + virtualized list optimization",
    "PRG-T03-C01-U03": "Raw node:http JSON/URL handler",
    "PRG-T03-C02-U03": "Ordered middleware chain + short-circuit tests",
    "PRG-T03-C03-U06": "Constructor-injected service module",
    "PRG-T04-C02-U05": "Parameterized pg Pool query module",
    "PRG-T04-C03-U03": "Non-destructive schema migration scripts",
    "PRG-T05-C01-U03": "Server-side session & rotation handler",
    "PRG-T05-C02-U08": "Deterministic token-bucket limiter + tests",
    "PRG-T06-C01-U05": "Dynamic [slug]/[...rest] route handler",
    "PRG-T08-C01-U05": "Namespaced cache key & TTL helper",
    "PRG-T08-C02-U06": "Idempotent retry & backoff worker",
}

# Topic-level mapping (v2 order)
TOPIC_MAP: list[dict] = [
    {
        "newCode": "PRG-T00",
        "oldCodes": ["PRG-T00"],
        "action": "keep",
        "title": "Foundation Audit & Developer Workflow",
        "objective": "Audit web fundamentals, developer workflow/Git, and baseline JS/TS readiness.",
        "extended": False,
    },
    {
        "newCode": "PRG-T01",
        "oldCodes": ["PRG-T01"],
        "action": "keep",
        "title": "JavaScript, TypeScript, Data Structures & Unit Testing",
        "objective": "Master JS execution internals, TypeScript, Big-O/data structures, and unit testing.",
        "extended": False,
    },
    {
        "newCode": "PRG-T02",
        "oldCodes": ["PRG-T02"],
        "action": "keep",
        "title": "Frontend Engineering with React & Component Testing",
        "objective": "Build accessible, performant React applications with server-state management and component tests.",
        "extended": False,
    },
    {
        "newCode": "PRG-T03",
        "oldCodes": ["PRG-T04"],
        "action": "renumber",
        "title": "Backend Engineering: Node.js, HTTP & Express 5",
        "objective": "Design and test layered Node.js and Express 5 REST APIs with validation and structured logging.",
        "extended": False,
    },
    {
        "newCode": "PRG-T04",
        "oldCodes": ["PRG-T05"],
        "action": "renumber",
        "title": "Database Engineering: PostgreSQL, pg & Prisma",
        "objective": "Model relational schemas, write raw pg queries and transactions, and manage Prisma migrations.",
        "extended": False,
    },
    {
        "newCode": "PRG-T05",
        "oldCodes": ["PRG-T06"],
        "action": "renumber",
        "title": "Authentication, Authorization & Web Security",
        "objective": "Implement Argon2id auth, opaque sessions, RBAC/ownership checks, CSRF/XSS defenses, and rate limiting.",
        "extended": False,
    },
    {
        "newCode": "PRG-T06",
        "oldCodes": ["PRG-T03"],
        "action": "renumber",
        "title": "Next.js & Full-Stack React",
        "objective": "Build full-stack Next.js App Router apps with Server/Client boundaries, caching, and Server Actions.",
        "extended": False,
    },
    {
        "newCode": "PRG-T07",
        "oldCodes": ["PRG-T07"],
        "action": "keep",
        "title": "E2E Testing & DevVault Capstone Track",
        "objective": "Verify end-to-end user journeys with Playwright and ship the DevVault v1.0 release candidate.",
        "extended": False,
    },
    {
        "newCode": "PRG-T08",
        "oldCodes": ["PRG-T09"],
        "action": "renumber",
        "title": "System Design, Redis & Realtime",
        "objective": "Identify bottlenecks, apply Redis caching, and build WebSocket/SSE realtime and background job pipelines.",
        "extended": True,
    },
    {
        "newCode": "PRG-T09",
        "oldCodes": ["PRG-T10"],
        "action": "renumber",
        "title": "Deployment, Docker & Cloud",
        "objective": "Containerize multi-service stacks with Docker Compose v2, automate CI/CD, and deploy to production.",
        "extended": True,
    },
    {
        "newCode": None,
        "oldCodes": ["PRG-T08"],
        "action": "retire",
        "title": "Testing & Software Quality (Distributed into T01-C04, T02-C06, T07-C01)",
        "objective": "Testing units moved into PRG-T01-C04, PRG-T02-C06, and PRG-T07-C01.",
        "extended": False,
        "retireTarget": "PRG-T01-C04, PRG-T02-C06, PRG-T07-C01",
    },
]

# Chapter-level oldCodes mapping (keyed by v2 chapter code)
CHAPTER_OLD_CODES: dict[str, list[str]] = {
    "PRG-T00-C01": ["PRG-T00-C01"],
    "PRG-T00-C02": ["PRG-T00-C03"],
    "PRG-T00-C03": ["PRG-T00-C02"],
    "PRG-T01-C01": ["PRG-T01-C01"],
    "PRG-T01-C02": ["PRG-T01-C02"],
    "PRG-T01-C03": [],
    "PRG-T01-C04": ["PRG-T01-C03", "PRG-T08-C01"],
    "PRG-T02-C01": ["PRG-T02-C01"],
    "PRG-T02-C02": ["PRG-T02-C02"],
    "PRG-T02-C03": ["PRG-T02-C03"],
    "PRG-T02-C04": ["PRG-T02-C04"],
    "PRG-T02-C05": ["PRG-T02-C05"],
    "PRG-T02-C06": ["PRG-T08-C02"],
    "PRG-T03-C01": ["PRG-T04-C01"],
    "PRG-T03-C02": ["PRG-T04-C02"],
    "PRG-T03-C03": ["PRG-T04-C03"],
    "PRG-T04-C01": ["PRG-T05-C01"],
    "PRG-T04-C02": ["PRG-T05-C02"],
    "PRG-T04-C03": ["PRG-T05-C03"],
    "PRG-T05-C01": ["PRG-T06-C01"],
    "PRG-T05-C02": ["PRG-T06-C02"],
    "PRG-T06-C01": ["PRG-T03-C01"],
    "PRG-T06-C02": ["PRG-T03-C02"],
    "PRG-T06-C03": ["PRG-T03-C03"],
    "PRG-T07-C01": ["PRG-T08-C03"],
    "PRG-T07-C02": ["PRG-T07-C02", "PRG-T07-C01", "PRG-T07-C03", "PRG-T07-C04"],
    "PRG-T08-C01": ["PRG-T09-C01"],
    "PRG-T08-C02": ["PRG-T09-C02"],
    "PRG-T09-C01": ["PRG-T10-C01"],
    "PRG-T09-C02": ["PRG-T10-C02"],
    "PRG-T09-C03": ["PRG-T10-C03"],
}


def expand_code_expr(expr: str, default_topic: str | None = None, default_chap: str | None = None) -> list[str]:
    """Expand shorthand/range expressions like `PRG-T01-C03-U01..U03` or `PRG-T05-C01-U03, U05`."""
    expr = expr.strip().replace("`", "")
    if not expr or expr == "—":
        return []
    out: list[str] = []
    cur_topic = default_topic
    cur_chap = default_chap
    for raw_part in expr.split(","):
        part = raw_part.strip()
        if not part:
            continue
        # Range with .. e.g. PRG-T01-C03-U01..U03 or PRG-T05-C02-U02..U08 or PRG-T07-C03-U01..U05
        m_range = re.fullmatch(r"(?:PRG-)?(?:(T\d{2})-)?(?:(C\d{2})-)?U(\d{2})\.\.U(\d{2})", part)
        if m_range:
            t = m_range.group(1) or cur_topic
            c = m_range.group(2) or cur_chap
            assert t and c, f"Missing topic/chap for range {part!r}"
            cur_topic, cur_chap = t, c
            u1, u2 = int(m_range.group(3)), int(m_range.group(4))
            for u in range(u1, u2 + 1):
                out.append(f"PRG-{t}-{c}-U{u:02d}")
            continue
        # Full or partial unit code: (PRG-)?(Txx-)?(Cyy-)?Uzz
        m_unit = re.fullmatch(r"(?:PRG-)?(?:(T\d{2})-)?(?:(C\d{2})-)?U(\d{2})", part)
        if m_unit:
            t = m_unit.group(1) or cur_topic
            c = m_unit.group(2) or cur_chap
            assert t and c, f"Missing topic/chap for unit {part!r}"
            cur_topic, cur_chap = t, c
            out.append(f"PRG-{t}-{c}-U{int(m_unit.group(3)):02d}")
            continue
        # Chapter code: (PRG-)?Txx-Cyy (used for T07-C01 / T07-C02 merged units)
        m_chap = re.fullmatch(r"(?:PRG-)?(T\d{2})-(C\d{2})", part)
        if m_chap:
            cur_topic, cur_chap = m_chap.group(1), m_chap.group(2)
            out.append(f"PRG-{cur_topic}-{cur_chap}")
            continue
        raise ValueError(f"Unrecognized code expression: {part!r} (from {expr!r})")
    return out


def parse_old_codes(raw: str, new_code: str, id_map: dict) -> tuple[str, list[str], dict]:
    """Parse the 'Old Code / Status' column into (action, oldCodes, extra)."""
    clean = raw.strip()
    extra: dict = {}
    if clean == "`NEW`":
        return "new", [], extra

    # Extract status tags like [KEPT], [MOVED], [MERGED], [MOVED, SPLIT], [Done], [Skip]
    tags_m = re.search(r"`\[([^\]]+)\]`", clean)
    tags = [t.strip().upper() for t in tags_m.group(1).split(",")] if tags_m else []
    code_part = re.sub(r"`\[[^\]]+\]`", "", clean).strip()

    # Split on '+'
    tokens = [tok.strip() for tok in code_part.split("+") if tok.strip()]
    m_new = re.fullmatch(r"PRG-(T\d{2})-(C\d{2})-U\d{2}", new_code)
    assert m_new
    cur_t, cur_c = m_new.group(1), m_new.group(2)

    old_codes: list[str] = []
    for tok in tokens:
        expanded = expand_code_expr(tok, cur_t, cur_c)
        for item in expanded:
            if re.fullmatch(r"PRG-T\d{2}-C\d{2}", item):
                # Chapter-level merge (e.g. PRG-T07-C01, PRG-T07-C02): expand to all v1 units in that chapter
                chap_units = sorted(k for k in id_map if re.fullmatch(rf"{re.escape(item)}-U\d{{2}}", k))
                old_codes.extend(chap_units)
            else:
                old_codes.append(item)
            # Update context for subsequent '+' tokens (e.g. `PRG-T01-C03-U05` + `U06`)
            m_last = re.search(r"PRG-(T\d{2})-(C\d{2})", item)
            if m_last:
                cur_t, cur_c = m_last.group(1), m_last.group(2)

    if "SPLIT" in tags:
        # PRG-T06-C02-U06 splits into PRG-T05-C02-U06 and PRG-T05-C02-U07.
        # Only the first keeps oldCodes=["PRG-T06-C02-U06"] so each v1 code appears exactly once.
        if new_code == "PRG-T05-C02-U07":
            extra["splitFrom"] = old_codes[0]
            return "split", [], extra
        return "split", old_codes, extra

    if len(old_codes) > 1 or "MERGED" in tags:
        return "merge", old_codes, extra
    if old_codes == [new_code]:
        return "keep", old_codes, extra
    return "renumber", old_codes, extra


def build_map() -> list[dict]:
    lines = DOC_PATH.read_text(encoding="utf-8").splitlines()
    id_map = json.loads(ID_MAP_PATH.read_text(encoding="utf-8"))

    entries: list[dict] = []

    # 1. Topics
    for idx, t in enumerate(TOPIC_MAP):
        entries.append(
            {
                "level": "topic",
                "order": idx,
                "newCode": t["newCode"],
                "oldCodes": t["oldCodes"],
                "action": t["action"],
                "title": t["title"],
                "objective": t["objective"],
                "expectedOutput": None,
                "practiceType": None,
                "prereqs": [],
                "parent": None,
                "extended": t["extended"],
                **({"retireTarget": t["retireTarget"]} if "retireTarget" in t else {}),
            }
        )

    # 2. Chapters & Units from markdown tables
    current_topic: str | None = None
    current_chap: str | None = None
    chap_order = 0
    unit_order = 0
    topic_extended = {t["newCode"]: t["extended"] for t in TOPIC_MAP if t["newCode"]}

    for line in lines:
        m_chap = re.match(r"^####\s+(PRG-T\d{2}-C\d{2})\s+—\s+(.+?)(?:\s+\*\(.*\)\*)?$", line.strip())
        if m_chap:
            chap_code = m_chap.group(1)
            chap_title = m_chap.group(2).strip()
            topic_code = chap_code.rsplit("-", 1)[0]
            if topic_code != current_topic:
                current_topic = topic_code
                chap_order = 0
            chap_order += 1
            current_chap = chap_code
            unit_order = 0

            old_c = CHAPTER_OLD_CODES[chap_code]
            if not old_c:
                c_action = "new"
            elif len(old_c) > 1:
                c_action = "merge"
            elif old_c == [chap_code]:
                c_action = "keep"
            else:
                c_action = "renumber"

            entries.append(
                {
                    "level": "chapter",
                    "order": chap_order,
                    "newCode": chap_code,
                    "oldCodes": old_c,
                    "action": c_action,
                    "title": chap_title,
                    "objective": "",
                    "expectedOutput": None,
                    "practiceType": None,
                    "prereqs": [],
                    "parent": topic_code,
                    "extended": topic_extended[topic_code],
                }
            )
            continue

        m_unit = re.match(r"^\|\s*`(PRG-T\d{2}-C\d{2}-U\d{2})`\s*\|", line)
        if m_unit:
            assert current_chap is not None
            cols = [c.strip() for c in line.strip().strip("|").split("|")]
            assert len(cols) == 7, f"Expected 7 columns in {line!r}"
            code = cols[0].strip("`")
            title = cols[1]
            objective = cols[2]
            expected_output = UNIT_EXPECTED_OUTPUT_OVERRIDES.get(code, cols[3])
            practice_type = cols[4].strip("`")
            prereqs_raw = cols[5]
            old_raw = cols[6]

            unit_order += 1
            m_u = re.fullmatch(r"PRG-(T\d{2})-(C\d{2})-U\d{2}", code)
            assert m_u
            prereqs = expand_code_expr(prereqs_raw, m_u.group(1), m_u.group(2))
            action, old_codes, extra = parse_old_codes(old_raw, code, id_map)

            entries.append(
                {
                    "level": "unit",
                    "order": unit_order,
                    "newCode": code,
                    "oldCodes": old_codes,
                    "action": action,
                    "title": title,
                    "objective": objective,
                    "expectedOutput": expected_output,
                    "practiceType": practice_type,
                    "prereqs": prereqs,
                    "parent": current_chap,
                    "extended": topic_extended[f"PRG-{m_u.group(1)}"],
                    **extra,
                }
            )

    # Validate completeness against v1 id_map.json
    v1_prg = sorted(k for k in id_map if k.startswith("PRG-"))
    seen_old: list[str] = []
    for e in entries:
        seen_old.extend(e["oldCodes"])

    missing = sorted(set(v1_prg) - set(seen_old))
    extra_old = sorted(set(seen_old) - set(v1_prg))
    dups = sorted({c for c in seen_old if seen_old.count(c) > 1})
    assert not missing, f"Missing v1 codes: {missing}"
    assert not extra_old, f"Unknown old codes not in id_map.json: {extra_old}"
    assert not dups, f"Duplicate old codes: {dups}"

    return entries


def main() -> int:
    entries = build_map()
    OUT_PATH.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    by_level = {}
    by_action = {}
    for e in entries:
        by_level[e["level"]] = by_level.get(e["level"], 0) + 1
        by_action[e["action"]] = by_action.get(e["action"], 0) + 1
    print(f"Wrote {len(entries)} entries to {OUT_PATH}")
    print("By level:", by_level)
    print("By action:", by_action)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
