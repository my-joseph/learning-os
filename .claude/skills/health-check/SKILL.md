---
name: health-check
description: Run a read-only LearningOS health audit, then prepare a ranked Thai fix plan. Use when the learner says "ตรวจสุขภาพระบบ" or "health check".
---

# Health check

Audit only. Do not change application or curriculum files during the audit. Speak to the learner in polite Thai; write worker reports in English and the final report in Thai. Follow `.claude/skills/dispatch-worker/SKILL.md` for worker setup, routing, and lifecycle.

## 1. Pin the audit

- Resolve `MAIN` from `git worktree list`, capture `AUDIT_SHA=$(git -C "$MAIN" rev-parse HEAD)` once, and pass it to every check and worker. Create `$MAIN/pilot/health-<YYYY-MM-DD>/logs/`; do not inspect or modify learner `progress/`.
- Record `AUDIT_SHA`, date, commands, exit statuses, and skipped checks in `checks.md`. Workers use isolated worktrees at `AUDIT_SHA`; do not audit a moving checkout or ephemeral sibling worktrees. Read-only references to main-checkout `.env`/`sources/` may be passed by absolute path when needed; never copy `.env` or learner data.
- Never write to Notion. Do not globally export `LEARNINGOS_PILOT=1` or `NOTION_DRY_RUN=1` into checks. In particular run pytest as `env -u LEARNINGOS_PILOT -u NOTION_DRY_RUN ...`; `tests/conftest.py` isolates `PROGRESS_DIR` and blocks network calls, while those flags can break non-pilot assertions.

## 2. Run automated checks (no AI)

Run in one clean, dedicated worktree at `AUDIT_SHA`, with required local dependencies linked read-only where practical (for example `.venv` and `practice-studio/node_modules`). Save category logs under `logs/`. Preserve full failure tracebacks and useful diagnostic metadata; never redact the error that explains a failure.

1. `.venv/bin/ruff check .` and `.venv/bin/ruff format --check .`.
2. `env -u LEARNINGOS_PILOT -u NOTION_DRY_RUN .venv/bin/python -m pytest -n auto -q --tb=long`.
3. In `practice-studio/`: `npm run lint`, `npm run build`, and `npm run test:telemetry`.
4. `.venv/bin/python -m code_engine.quality_checks --check-vaults` and `.venv/bin/python -m code_engine.lint_check --all`.
5. For every `labs/LAB-*/`, run `npm run check:reference`; report each lab result.
6. Run `.venv/bin/python -m math_engine.variant_bank --check <file> --no-originality` for every `drills/variants/*.json`; run `--coverage <active MTH unit>` for active math units. Summarize only failures and coverage gaps below three.
7. Run `.venv/bin/python scripts/audit_solution_leaks.py` and `.venv/bin/python scripts/audit_solution_leaks.py --display` separately. The default is the gate; display findings are advisory. Do not quote flagged prompt or answer text.
8. Query `UNITS_DB` read-only from `id_map.json` for `Status = In progress` (paginate), resolve each unit's parent chapter, and run `.venv/bin/python -m scripts.page_audit <CODE>` for every active unit and parent chapter. Aggregate output in one `logs/page-audit.log`; report counts and only FAIL/WARN pages. If Notion is unavailable, record the check as skipped.
9. Run `.venv/bin/python -m scripts.issues list`; retain open-issue `id`, `kind`, `severity`, `where`, and one-line `what` in logs. Never include learner progress contents.
10. Do not run `scripts.source_find <UNIT> --plan`: it writes to `sources/_index/`. Use `scripts.source_find.find_unregistered_source_folders("$MAIN/sources")` for the read-only registry/folder check, and validate existing `sources/_cores/*.jsonl` cards in memory with `math_engine.source_cores.validate_core_card`; report unregistered folders and invalid cards only.
11. Compare drill/lab IDs and active references against `id_map.json` using read-only inspection. Report missing/orphaned IDs, invalid unit/chapter/reference keys, duplicate Notion page IDs, and active references to `RETIRED-*`. Never edit `id_map.json`.
12. Read-only git hygiene: check `core.hooksPath`, tracked `.env*`, `progress/`, `pilot/`, `scratch/`, and `sources/` files; list worktrees and merged-branch candidates without removing anything.
13. Run `.venv/bin/python -m scripts.doc_refs` to verify paths, module commands, CLI flags, npm scripts, and skill references across skills, rules, and docs.

## 3. Launch read-only worker audits

- Use isolated worktrees pinned at `AUDIT_SHA`, one unique absolute `DONE_FILE` per report under the dated folder, and bounded prompts. Make reports English with severity, exact `file:line`, reproducible evidence, impact, suggested scoped fix, and a proposed fix-PR mapping.
- Make each area churn-aware: start with `git log --since=<last audit date> --stat` (use the latest dated health/review audit; state if none exists), then inspect changed/high-churn files plus subsystem coverage. Audit current code, not only the diff.
- **Area A — Runtime correctness** (`correctness.md`; Hydrogen or Neon): TypeScript/Python state and scoring parity; save/sync and server-owned field preservation; review, Similar/variants, bridge scope; source synthesis/originality and drill quality; PRG review/lab pipeline; `notion_sync` behavior and dry-run/pilot guards. Recheck open findings from prior audits as fixed/open/regressed.
- **Area B — Drift and delivery controls** (`drift.md`; Luna): `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `rules/`, `docs/`, `.claude/skills/`, relevant memory notes, CI workflows, `tests/conftest.py`, and `.githooks/`. Check test markers against CI path filters, lab coverage, env isolation, hooks, and secret/progress path hygiene. Use `location | doc says | current reality (file:line) | fix | learner decision?`.
- **Area C — Studio API security and zero-leak** (`api-security.md`; Hydrogen or Neon): inspect all 17 routes in `practice-studio/src/app/api/**` for `isSafeId` and path containment, response leaks of answers/steps/hidden test names, and preservation of server-owned fields. Include PRG review/lab pipeline, `notion_sync`, CI/hooks, and `conftest.py` boundaries where they intersect API behavior; coordinate overlaps with Areas A/B.
- Model routing follows `.claude/skills/dispatch-worker/SKILL.md`: Neon for cross-cutting correctness, Hydrogen for focused correctness/API review, Luna for documentation/drift. For **every** drift finding, verify it again against current `main` before reporting; drop findings disproved by current main and historical-design, stale-path, or timestamp-only noise (including recent verification dates whose commands still match). Record the verified current-main location/evidence.
- Never use detached shell backgrounding. Track workers to completion and inspect every report. Do not delete worktrees or branches during the audit.

## 4. Verify and merge findings into a plan

- Recheck surprising failures and every worker finding against its cited current source. Separate **confirmed** findings (reproduced or directly evidenced) from **plausible** risks (credible but unverified); keep new issues separate from prior-audit carryovers. Drop history/timestamp noise.
- Write `$MAIN/pilot/health-<date>/report.md` in polite Thai. Include `AUDIT_SHA`, date, concise automated-check totals with only failing/warning items, ranked findings with evidence and impact, skipped checks, and missing evidence.
- Map every finding to one bounded proposed fix PR (or explicitly state why no fix PR is proposed). Group only independent findings with non-overlapping scope; identify learner-owned decisions and the decision needed. Keep confirmed findings distinct from plausible risks and cleanup.
- Do not fix findings unless the learner explicitly says to fix them. After writing the report, remove only temporary audit worktrees created for this run; preserve all other worktrees and branches.

## 5. Safety and report boundary

- Read-only audit: never write to Notion, `progress/`, drills, vaults, `id_map.json`, or source materials, including `sources/_index/`. Write audit artifacts only under the dated `pilot/health-*` folder.
- Never log drill/variant answers, worked-solution steps, hidden test code/assertions, `.env` values, or learner progress contents. Keep full pytest failure tracebacks, CLI stderr/exit codes, page-audit FAIL/WARN lines, and issue metadata listed in §2; these diagnostics are not secrets.
- Preserve mock UI data and any worktree/branch the learner asked to keep.

## Final check

- [ ] `checks.md`, worker reports, and `report.md` refer to the same `AUDIT_SHA`.
- [ ] Report contains check outcomes, confirmed vs plausible findings, a fix-PR mapping for each finding, learner decisions, and skipped/missing checks.
- [ ] No Notion writes, learner data, answer/step/hidden-test content, or temporary audit processes remain.
