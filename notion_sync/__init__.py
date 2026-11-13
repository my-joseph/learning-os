"""Everything that talks to Notion.

- client: REST client, .env loader (verified TLS, retry policy, MissingNotionToken)
- blocks: rich-text / block builders and validated page replace
- drill_sync: drill save + zero-leak validation + Notion sync (used by the Studio)

Rules (rules/*.md) are local-only and are not synced to Notion.
"""
