# Interim Agent Handoff

## Purpose

Give an interim lead agent the learner decisions and boundaries Claude otherwise holds in private memory. This handoff supplements the repository rules; it does not replace them. Claude maintains this file in the same PR/turn when learner decisions change.

## Read first

Read these in order before acting:

1. `CLAUDE.md`
2. `rules/README.md`
3. `rules/00_core.md`
4. `.claude/skills/dispatch-worker/SKILL.md`

## Learner decisions

### Working style

- Speak with the learner in polite Thai; write learning content in English.
- Report promptly when a job finishes. Track background worker jobs to completion.
- Ask only about learner-owned decisions; proceed on routine implementation choices.
- The learner's Claude quota is low. The lead plans, writes bounded specs, reviews, and delivers; delegate implementation to workers when appropriate.
- Docs grow with code: when behavior, commands, paths, schemas, routes, or workflows change, update affected skills, rules, docs, and `CLAUDE.md` in the same PR. Include `Docs updated:` in the PR body. Consider `self_review` proposals, but act on them only when the lead agrees; explain disagreements.

### Models and workers

- Use `tools/agents/run-worker.sh`, the `dispatch-worker` skill, and `.claude/skills/dispatch-worker/common.md`.
- Route simple, high-volume, documentation, and read-only audit work to Luna (`gpt-6-luna`, Codex quota); everyday coding to Hydrogen (`gemini-4-hydrogen-high`); hard cross-cutting work to Neon (`gemini-4-neon-high`); independent review, blind-solve, skill trials, or parallel work to Argon (`gemini-4-argon-high`, separate pool). Hydrogen and Neon share one `agy` quota pool.
- The learner switches the `agy` account themselves between jobs and will tell the agent which account is active. Do not change or check-and-block on a specific account; if an `agy` run fails on login or quota, report it and fall back per the routing above.
- Keep each job to one concern, put file paths and line evidence first, name acceptance criteria and tests, and merge `origin/main` with a merge (never rebase) before clean-environment checks.
- Run no more than two workers in parallel and allow no more than two revision rounds per job. After that, stop and report.

### Merge and safety

- Never commit or push on `main`; use a branch and one PR. Never use `--no-verify`. Keep secrets out of output and commits.
- An interim lead may merge only when CI is green and the PR is docs/tests-only or changes at most three files, and it touches none of: scoring; progress, sync, or save; `math_engine` or `code_engine`; CI workflows; `rules/*.md` contracts; `id_map.json`. Leave every other PR open for the learner or Claude.
- Never touch learner data in `progress/`; never hand-edit `id_map.json`. Tests use a temporary `PROGRESS_DIR`. Never write to Notion; use `NOTION_DRY_RUN=1` / `LEARNINGOS_PILOT=1` when an operation could sync.
- Preserve zero-leak: prompts, answers, steps, and hidden tests stay hidden until a real attempt.
- Do not change accounts, permissions, branch protection, or required CI checks; force-push; delete files, branches, or worktrees the learner keeps; or start work on anything in the ON HOLD list.
- Use Studio colors from the design system (`statusTone` tokens; figure colors indigo, emerald, amber, and rose). Never use amber/yellow for answer status. Get learner approval for any new color.

### ON HOLD — do not start without the learner

- Similar “+” button refactor; removal of math and PRG templates and the Studio Generate button (including `/api/generate-drill` validation); rename of `rules/06`; PRG Similar/variant bank.
- Fix the case where a Worked Example can serve the same variant as an unopened Similar tab; this is tied to the “+” refactor.
- Retire/rebuild `DRL-PRG-T00-C03-02` and `LAB-PRG-T01-C04-02` (issues `a96ca5`, `7b2db0`, `f8bd76`).
- PR B, PR C (including issue `0852fe`, Weak spots trap-name leak), Example redesign, and learning-feature Phases 3–5.
- Engine roadmap Phase 2 (`pilot/improve-engine-2026-11-21/roadmap.md`, items 2.1–2.3): wait for quota reset and learner go-ahead.
- Scheduled/automatic jobs: wait until the system is stable.
- Ideas noted, not started: Skills Status mastery overview page; Skip-reason prompt; Review & Sync page “back to drill” button; slow `npm run dev`; flaky sync (partly in `fix/sync-stamps-persist`).

## Current state and how to refresh it

The following snapshot came from the learner-decision digest dated 2026-11-21. Treat it as historical context; refresh live state before choosing work.

- Digest snapshot: health-check fixes #278–#284, worker/health/drill-quality/review skills, doc guards #287, engine Phase 1 #288–#291, self-improvement loop #292–#293, distractor-provenance gate #295, and synced-green stepper #296 were recently merged.
- Digest snapshot: `fix/sync-stamps-persist` was in flight for lost sync stamps on autosave and a possible sync hang.
- Issues named for batch handling: `python -m scripts.issues list`; digest called out `56deb3` (eight existing MTH problems flagged by the distractor gate). Other ON HOLD issue IDs are listed above.
- Learner study snapshot in the digest: MTH-T02-C01, Complex Numbers U01 at mastery 2 with next review 2026-11-26; Quadratic U02 drill 01 ready; PRG-T00 next.
- Refresh open PRs with `gh pr list`; issue state with `python -m scripts.issues list`; ranked signals with `python -m scripts.self_review`; local worktrees with `git worktree list`.

## Interim lead rules

### ALLOWED

- Dispatch workers through `.claude/skills/dispatch-worker/SKILL.md`.
- Review PRs.
- Run `health-check`, `review-drill`, `drill-quality`, and `improve` for assessment only.
- Fix bugs that already have an issue.
- Answer the learner in Thai.

### MERGE

Merge only a PR with green CI that is docs/tests-only or small (at most three files) **and** does not touch scoring, progress/sync/save, `math_engine`/`code_engine`, CI workflows, `rules/*.md` contracts, or `id_map.json`. Everything else stays open for the learner or Claude.

### FORBIDDEN

- Starting ON HOLD work; editing `rules/*.md` contracts; Notion writes other than normal drill/lab sync; touching `progress/` or `id_map.json`.
- Deleting files, worktrees, or branches the learner keeps; changing accounts, permissions, branch protection, or required CI checks; force-pushing.
- Running more than two parallel workers or more than two revision rounds per job. At the limit, stop and report.

### LOG and Claude return

- Append each decision, merge, and worker launch to the local, gitignored `pilot/handoff-log.md`, recording date, action, reason, and PR/issue. Do not commit this log.
- Log friction with `python -m scripts.issues propose --target ...`.
- When Claude returns, Claude reads `pilot/handoff-log.md` and `python -m scripts.self_review`, then audits merged PRs.
