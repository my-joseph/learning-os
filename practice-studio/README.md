# Practice Studio

Local web UI for LearningOS drills (math + programming).

## Run

```bash
npm install
npm run dev   # http://127.0.0.1:3000 (bound to localhost only)
```

## How it fits together

- Drill JSON lives in `../drills/data/<UNIT>/<DRILL_ID>.json` (`drills/` here is a symlink).
- API routes in `src/app/api/*` spawn the Python engines from the repo root
  (`math_engine/`, `code_engine/`, `practice_hub.py`) using `../.venv` if present.
- File access from the browser is restricted to the repo root (`src/lib/paths.ts`).
