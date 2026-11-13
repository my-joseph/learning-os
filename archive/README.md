# archive/ — one-shot legacy scripts

Historical builders/upgraders/cleanup scripts. Most write to Notion. **Do not run unasked.**
Kept only for reference during the refactor (see Refactor in Progress in `../CLAUDE.md`).

Run (if ever required) from the repo root, so `.env` and `id_map.json` resolve and the
`notion_sync` package is importable. `archive/apply_rules_and_test_pages.py` re-exports
`notion_sync.blocks` + `notion_sync.client`, so old `from apply_rules_and_test_pages import ...`
lines keep working:

    PYTHONPATH=. python3 archive/<script>.py

Also archived here (not used by live code): `apply_rules_and_test_pages.py` page builders,
`upgrade_mth_t01_batch2.py` + `mth_t01_batch2_{data,units}.py`, `visual_builder.py`,
`diagram_generator.py` (former `math_engine/` figure modules), `uploaded_{image,param}_ids.json`.
