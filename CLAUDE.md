# CLAUDE.md (v0 — short on purpose; project is being refactored)

## Project Overview
- LearningOS: a Notion-hosted curriculum (Topic → Chapter → Unit) plus local-first generators for practice drills (`MTH`/`PHY` math, `PRG` code) and project labs.
- Python scripts generate/verify content and write to Notion; a Next.js "Practice Studio" shows drills; code is edited in the user's own VS Code/Cursor.
- Chat with the user in polite Thai. All content written to Notion/drills must be English.

## Rules (read first, do not copy here)
- Before any task: read @rules/README.md (task→module routing) and @rules/00_core.md, then the domain module.
- Rule edits: change `rules/*.md` and commit. Rules are local-only; they are **not** synced to Notion (old Notion rule pages are stale; never read rules from Notion).

## Tech Stack
- Python 3.14 (stdlib `urllib` for Notion REST; `sympy`, `numpy` for math engine). Deps: `requirements.txt` (runtime), `requirements-dev.txt` (+pytest, ruff). CI runs Python 3.12.
- Node 24 / npm 11. `practice-studio/`: Next.js 14.2.35, React 18, TypeScript (strict), Tailwind 3, KaTeX, three.js.
- Labs: TypeScript run via `node --experimental-strip-types` (no build step).

## Commands (verified 2026-11-13 unless marked)
- Studio (run in `practice-studio/`): `npm ci`, `npm run dev` (http://127.0.0.1:3000, bound to localhost only), `npm run lint`, `npm run build`.
- Generate drills (run from repo root): `python3 -m math_engine.generate --unit <UNIT> --count <N> --difficulty <D>` and `python3 -m code_engine.generate --unit <UNIT> --count <N>` (`--help` verified; full run not verified).
- Lab (run in `labs/LAB-PRG-T03-C01-01/`): `npm test` (21 tests pass). `npm run submit` writes to Notion — only on request.
- Python tests (repo root): `pip install -r requirements-dev.txt && python -m pytest` (164 pass, ~50 s; hermetic, no Notion/network). Studio unit tests: `npm run test:telemetry` in `practice-studio/`.
- CI: `.github/workflows/ci.yml` runs pytest, studio lint+build, lab tests. No Makefile/Dockerfile. TODO: verify any other command before using it.

## Conventions (target — apply to new/changed code)
- Python: ruff format + lint, type hints on public functions, one shared Notion client on stdlib `urllib` (no new deps), secrets only from env.
- TypeScript: strict per `practice-studio/tsconfig.json`; must pass `next lint`.
- Drill IDs: `DRL-<UNIT>-NN`; specs live in `drills/data/<UNIT>/`. Schema reference: @practice-studio/src/types/drill.ts.
- Lint/format (repo root): `ruff check .` and `ruff format --check .` (config `ruff.toml`; `archive/` excluded; do not strip trailing whitespace inside string literals — it is generated output). CI enforces both.
- Commits: conventional (`feat(scope):`, `fix:`, `refactor:`, `docs(rules):`).

## Workflow
- Work on a branch and open a PR; never push to `main` directly (this overrides `rules/00_core.md` §10 "push origin main").
- Before calling work done: run the commands above that apply (lint/build/tests) and report failures honestly, separating pre-existing ones from new ones.
- New drill/lab: sync its pristine record to Notion right after creating it, per `rules/00_core.md` §8 — no need to wait for a merge or ask first (user decision 2026-11-13). From a worktree this works without copying `.env`: `notion_sync.client.load_env` reads the main checkout's `.env`.

## Refactor in Progress
- Goals: (1) merge duplicated root vs `practice-studio/` files into one source; (2) Python cleanup: `archive/` for one-shot legacy (done), one Notion client + env loader (done for root modules), `requirements.txt` (done); a `scripts/` package layout is NOT done; (3) Next.js studio as the only UI (done); (4) add tests + CI (done: pytest, ruff, GitHub Actions; CI green on PRs #2–#4).
- Rules: preserve existing behavior; refactor commits separate from feature/bugfix commits; all tests pass at the end of every phase; no Notion writes while verifying.
- Status (update at the end of every phase):

| Phase | Scope | Status |
| :-- | :-- | :-- |
| P0 | Safety net: requirements, pytest, CI, lint baseline fixed | done (PR #1) |
| P1 | Move one-shot scripts to `archive/` | done (34 moved; 7 root modules kept because live code imports them) |
| P2 | Shared Notion client + env loader | done (`notion_sync/client.py`); `code_engine/submit.py` and `labs/common/submit_lab.py` keep their own variants (different retry/env-quote behavior) |
| P3 | Merge duplicated root/studio files | done (root is canonical; stale `practice-studio/` copies removed) |
| P4 | Retire `practice_hub.py` + `web/` | done (hub server and legacy UI deleted; `notion_sync/drill_sync.py` keeps validator, save and Notion sync) |
| P5 | ruff format/lint + type hints | done (ruff config, CI checks; hints on `notion_sync.client`/`notion_sync.drill_sync` public funcs only; `archive/`, studio excluded) |
| P6 | Notion layer as `notion_sync/` package; dead figure modules + one-shot page content to `archive/` | done (root keeps only shared `quality_rules.py`; `progress_store.py` added later for learner progress) |
| P7 | Retire Notion rules sync (rules local-only) | done (`rules_sync`, `md_blocks`, `page_audit`, `rules_map.json` moved to `archive/`) |

## Gotchas / Do-Not
- Never commit or print `.env` (`NOTION_TOKEN`, `NOTION_DATABASE_ID`). `.env`, `.venv`, `node_modules` are gitignored and absent in fresh worktrees; scripts read `.env` relative to the CWD, so run from repo root.
- Root is canonical for `math_engine/`, `code_engine/`, `drills/`, `id_map.json`, `notion_sync/`. `practice-studio/` has no copies (only a `code_engine` symlink to `../code_engine`); the Studio API routes read root via `src/lib/paths.ts`. Never recreate copies; `code_engine.generate` no longer mirrors into `practice-studio/`.
- 34 one-shot scripts (`*_builder.py`, `upgrade_*`, `create_*`, `fix_*`, `deploy_*`, `clean_*`, `patch_*`, ...) live in `archive/` and mostly write to Notion. Never run them unasked; if required: `PYTHONPATH=. python3 archive/<script>.py` from repo root (`archive/apply_rules_and_test_pages.py` re-exports the live helpers for them). All Notion code is in the `notion_sync/` package: `client` (REST client + `.env` loader; process-wide IPv4/timeout on import; TLS always verified; retries only network errors/409/429/5xx; raises `MissingNotionToken` before any request; `replace_page_content` appends before deleting), `blocks` (rich text/block builders), `drill_sync` (zero-leak validator + save + Notion sync; spawned by the studio `sync-notion` route). Root `.py` files: only `quality_rules.py` (shared quality gates; reads `skills_taxonomy.json`).
- Never hand-edit `id_map.json` (Notion page-ID registry, incl. `CON-*` concept keys).
- Drill files in `drills/data/` are **content only**. Learner progress (problem `state`, `sessionSummary`) lives in `progress/<DRILL_ID>.json` (gitignored; `progress_store.py` / `practice-studio/src/lib/progress.ts`). Never write practice results into a drill file; `tests/test_progress_store.py` enforces it.
- Drill hints/placeholders must never leak the answer (zero-leak rule, `rules/00_core.md` §6). AI-written math prompts must not give away the solution either (`rules/07` §4.7, enforced at ingest); audit with `python scripts/audit_solution_leaks.py [UNIT] [--display]`.
- Notion multi-select values cannot contain commas; use only whitelisted Notion icon names.
- `code_engine.generate` writes CWD-relative side effects (`drills/workspace/<ID>/`). Tests must `monkeypatch.chdir(tmp_path)`.

## Environment (names only)
- `NOTION_TOKEN`, `NOTION_DATABASE_ID`

## Keeping this file current
- If anything here is outdated, or you hit a new trap, propose an update to CLAUDE.md.
