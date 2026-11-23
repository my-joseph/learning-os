# Practice Studio

Local web UI for LearningOS drills (math + programming).

## Run

```bash
npm install
npm run dev   # http://127.0.0.1:3000 (bound to localhost only)
```

## How it fits together

- Drill JSON lives in `../drills/data/<UNIT>/<DRILL_ID>.json` (`drills/data` here is a symlink to `../../drills/data`).
- API routes in `src/app/api/*` spawn the Python engines from the repo root
  (`math_engine/`, `code_engine/`, `notion_sync/drill_sync.py`) using `../.venv` if present.
- File access from the browser is restricted to the repo root (`src/lib/paths.ts`).
- Practice state is saved to `../progress/<DRILL_ID>.json` (gitignored), never into the drill file; `src/lib/progress.ts` merges it when a drill is loaded.
- `DELETE /api/drill?id=<DRILL_ID>` removes exactly one canonical local `DRL-(MTH|PHY|PRG)-…` JSON file. It returns `200` with `{ "ok": true, "deleted": true, "drillId": "…" }`, `400` for a missing/invalid ID, `404` when the drill is absent or ambiguous, and `500` for filesystem errors. It retains progress, workspaces, Labs, variants, Notion records, and all other drills. Autosaves for drills whose content has been deleted return `404`.
- Drill deletion is covered by `npm run test:telemetry` (`tests/drillDeletion.test.ts`) using temporary drill and progress directories.
