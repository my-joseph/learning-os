---
name: health-check
description: Run a read-only LearningOS health audit, then prepare a ranked Thai fix plan. Use when the learner says "ตรวจสุขภาพระบบ" or "health check".
---

# Health check

Audit only. Never change application or curriculum files during this workflow. Speak to the learner in polite Thai; write the final report in Thai. Scope and report shape follow the read-only reviews in `pilot/code-review-2026-11-20/` and `pilot/structure-audit-2026-11-20/` in the main checkout.

## 1. Establish the audit folder

- Use the main checkout path from `git worktree list`; do not assume this worker worktree contains the ignored pilot reports.
- Create `pilot/health-<YYYY-MM-DD>/` in the main checkout. Do not inspect or modify `progress/`.
- Record the commit, date, commands, and each command's exit status. Never enable Notion writes; use `NOTION_DRY_RUN=1 LEARNINGOS_PILOT=1` if a command could sync.

## 2. Run automated checks (no AI)

Run from the main checkout where appropriate, save concise logs in the audit folder, and record skipped checks explicitly:

1. `.venv/bin/ruff check .` and `.venv/bin/ruff format --check .`.
2. `.venv/bin/python -m pytest -n auto -q`.
3. In `practice-studio/`: `npm run lint`, `npm run build`, `npm run test:telemetry`.
4. `.venv/bin/python -m code_engine.quality_checks --check-vaults` and `.venv/bin/python -m code_engine.lint_check --all`.
5. `.venv/bin/python scripts/audit_solution_leaks.py` (display findings separately as advisory).
6. `.venv/bin/python -m scripts.page_audit <UNIT>` for each unit whose Notion Status is `In progress`; if status cannot be read safely, list it as unavailable.
7. `.venv/bin/python -m scripts.issues list`.
8. `.venv/bin/python -m scripts.source_find <UNIT> --plan` for active units; capture unregistered-folder warnings without extracting or modifying sources.
9. Compare `id_map.json` drill/lab IDs with content on disk using read-only inspection; report missing/orphaned entries. Never edit `id_map.json`.
10. Inspect `git worktree list`, local branches, and merged branches (`git branch --merged main`) for stale worktrees/branches. Do not remove anything.

## 3. Launch parallel read-only worker audits

- Use one worker per area and one unique `DONE_FILE` per worker: `correctness.md` and `drift.md` under the dated folder. Worker findings include severity, file:line, evidence, and a suggested fix.
- Area A checks correctness by subsystem: drill state/scoring parity between TypeScript and Python, save/sync, review engine, Similar/variants, and UI. Use the hand-review files as the coverage map.
- Area B checks drift among `rules/*.md`, `docs/*.md`, `CLAUDE.md`, `.claude/skills/*`, memory notes, and implementation: contradictions, stale commands, and dead references. Use the structure-audit files as the coverage map.
- Make each job read-only and give the worker absolute paths to the main checkout and report folder. Set `DONE_FILE=<absolute path to its report>`.
- Start each `tools/agents/run-worker.sh <wt> <branch> <prompt> <log>` with the Bash tool's `run_in_background: true`. Never detach with `( ... &)`; wait for completion notifications and inspect both reports.
- Use available models in fallback order informed by current memory/learner settings; availability changes. Do not hard-code a single account or model.

## 4. Merge findings into a plan

Write `pilot/health-<date>/report.md` in Thai. Rank findings by severity, cite evidence and group them into small independent fix PRs sized for one worker each. Mark learner-owned decisions separately and explain what decision is needed. Keep confirmed issues separate from plausible risks and cleanup. Include automated-check outcomes and missing evidence.

Do not fix findings until the learner approves the plan, unless they explicitly said "แก้เลย". If approved, handle each fix as its own scoped job and follow the repo delivery rules.

## 5. Safety

- Read-only: never write Notion, `progress/`, drills, vaults, or source materials during audit.
- Never delete mock UI data or worktrees the learner asked to keep. Never delete worktrees or branches as part of this audit.
- Audit reports may quote file paths and evidence, but never include answers, hidden tests, `.env`, or learner data.

## Final documentation check

- [ ] Audit and worker reports are saved under the dated main-checkout folder; the Thai report includes ranked findings, grouped fix PRs, learner decisions, and check status.
