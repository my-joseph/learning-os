"""Everything that talks to Notion.

- client: REST client, .env loader (verified TLS, retry policy, MissingNotionToken)
- blocks: rich-text / block builders and validated page replace
- md_blocks: rules Markdown -> Notion blocks
- page_audit: unlinked-code audit of a written page
- rules_sync: `python3 -m notion_sync.rules_sync [--dry-run]` syncs rules/*.md to Notion
- drill_sync: drill save + zero-leak validation + Notion sync (used by the Studio)
"""
