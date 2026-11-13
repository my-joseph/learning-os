# archive/ — one-shot legacy scripts

Historical builders/upgraders/cleanup scripts. Most write to Notion. **Do not run unasked.**
Kept only for reference during the refactor (see Refactor in Progress in `../CLAUDE.md`).

Run (if ever required) from the repo root, so `.env` and `id_map.json` resolve and the
root-level shared modules (`apply_rules_and_test_pages`, `drill_sync`, ...) are importable:

    PYTHONPATH=. python3 archive/<script>.py
