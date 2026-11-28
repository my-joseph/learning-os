---
name: improve
description: Assess one LearningOS area deeply and prepare a learner-approved phased improvement roadmap. Use when the learner says "ปรับปรุง <area>" or "improve <area>" for engine, ux, pipeline, or content.
---

# Improve one area

Health-check asks what is broken now (broad and shallow). Improve asks how one area should get better (focused and deep). Assess first, propose a phased roadmap, wait for the learner's decision, then execute approved items as small PRs. Speak to the learner in polite Thai; write reports and learning content in English. Keep the skill read-only until roadmap approval.

## 1. Brief and pin context

- Parse `area` (`engine`, `ux`, `pipeline`, or `content`) and optional focus. If no valid area is named, ask which area; do not start a broad audit.
- Resolve `MAIN` from `git worktree list --porcelain`. Run `git -C "$MAIN" fetch origin main`, then capture `AUDIT_SHA=$(git -C "$MAIN" rev-parse origin/main)` once. Record that SHA plus `$MAIN` HEAD and the active worktree HEAD when they differ. Create `$MAIN/pilot/improve-<area>-<YYYY-MM-DD>/` and save `context.md`, `assessment.md`, and `roadmap.md` there.
- Use `"$MAIN/.venv/bin/python"` for Python commands; `.venv` is gitignored and absent in fresh worktrees. Inspect source at `AUDIT_SHA` and compare relevant findings with current `origin/main`.
- Do not read or modify learner `progress/`. Never write to Notion; use isolated pilot data for any UI work. Never expose drill prompts, answers, steps, or hidden tests before a real attempt.

## 2. Gather context before proposing (mandatory)

Record sources, pinned SHA, and freshness in `context.md`.

- Read the latest `$MAIN/pilot/health-*/report.md` and relevant checks/findings; inspect both `gh pr list --state open --base main` and `gh pr list --state merged --base main --limit 20`. Mark findings fixed on main or covered by an open PR, and note overlapping open-PR files.
- Run `"$MAIN/.venv/bin/python" -m scripts.issues list` and `"$MAIN/.venv/bin/python" -m scripts.self_review --no-progress --compare-at <YYYY-MM-DD> --target <area>` (read-only) to include recurring issues, open proposals, auto-signals, and before/after worker deltas for `<area>` in `context.md`. If no date is supplied, the self-review uses the latest `since` date in `docs/self_review_addressed.json`. Also inspect `docs/backlog.md`, relevant project memory notes, and learner decisions. Find memory via the main checkout's Claude project memory directory; read its `MEMORY.md` index and linked notes. Record missing inputs.
- Explicitly check ON HOLD decisions, including the Similar “+” refactor, legacy PRG drill/lab retire-and-rebuild, scheduled jobs, **Due-review tree and drill review mode**, **Engine clean-up (unify PRG runners, split math answer checker, shared ingest core)**, and **Question-jump shortcut**. The **What I get wrong list** is implemented and awaiting visual review. Studio Generate / `/api/generate-drill` removal (Phase 2) and math/PRG template removal (Phase 3) are completed. Do not revive deferred work unless the learner has since approved it.
- Read `rules/00_core.md` §10 and refactor invariants: characterize behavior first, separate refactor commits from features, and keep tests green at each step. Treat learner-pasted/external reports as leads and verify claims against the pinned source and current main.

- Use `python -m scripts.source_gap <UNIT> --no-progress` for any source gap audit. This leaves bridge eligibility unassessed.

## 3. Assess one area

- Read `areas/<area>.md`. As coordinator, delegate bounded read-only assessments through `.claude/skills/dispatch-worker/SKILL.md`, pinned to `AUDIT_SHA`, using isolated worktrees, unique reports, and English output. If already in an isolated read-only worker or doing a focused single-area verification, inspect directly; do not spawn nested worktrees. Use a different model from the original assessor as the independent verifier (Carbon for high-risk areas, Sol otherwise; Argon is retired). Workers must not edit product files.
- Save `assessment.md` with current state, strengths worth preserving, exact `file:line` evidence, and relevant measurements (size, complexity, duplication, coverage, timings, or per-stage cost). Separate measured facts from hypotheses.
- Each improve report records the pinned audit SHA and the actual model that performed it; record the other role as pending or unknown until independently confirmed, then update the report with both actual models and the reviewed artifact revision.

## 4. Verify findings and filter stale or deferred items

- Verify every finding and every claim in an external report against the pinned source and current `main`, yourself or with an independent verifier.
- Exclude items fixed on `main`, covered by an open PR, outside `<area>` (route them to the right area), or marked ON HOLD/deferred. Add a verification-disposition table to `assessment.md` so dropped leads are accounted for and not presented as facts.

## 5. Propose the roadmap and stop for the learner

- Write `roadmap.md` with phases as useful: quick wins/debt, structural improvements, and new or topic-gated capability. Each item states goal, exact evidence, measurable expected benefit, risk, size (`S`/`M`/`L`), model (`Luna`, `Sol`, `Hydrogen`, `Neon`, or `Carbon` per dispatch-worker), dependencies (including open PRs touching the files), and a test-first plan. Refactors start with characterization tests and before/after measures.
- List learner decisions, open-PR exclusions, and standing ON HOLD/deferred items separately; distinguish decisions needed now from standing decisions. Do not execute roadmap items before approval.
- Give the learner a concise Thai summary of evidence, phases, trade-offs, and decisions needed. **Stop after read-only steps 1–5.** Continue to step 6 only with approved scope.

## 6. Execute approved items and close the cycle

- Implement each approved item in its own small PR via `dispatch-worker`. For refactors, add characterization tests first, preserve behavior, measure before/after, and keep refactor changes separate from feature changes. Run applicable checks and report failures honestly.
- Never combine refactor and feature work. Do not write to Notion or learner progress. Keep drill content English and enforce zero-leak gates.
- Update roadmap status after each PR. If behavior or commands change, update `CLAUDE.md` and relevant docs in the same scoped PR. Log follow-up issues with `"$MAIN/.venv/bin/python" -m scripts.issues add` when required by `rules/00_core.md` §11.
- Review each PR and checks, follow `rules/00_core.md` §10, and stop after approved work is delivered. Stop every server or background process started during UX work.

## Final check

- [ ] `context.md`, `assessment.md`, and `roadmap.md` exist in the dated folder and cite the same `AUDIT_SHA`.
- [ ] Fixed, open-PR, out-of-area, and ON HOLD/deferred items are excluded from execution and documented in the verification/deferral table.
- [ ] Execution stops after step 5 until approval; approved step 6 items each have a small PR and applicable verification, with no learner progress, Notion writes, or leaked exercise material.

## Self-review

After the run, compare the outcome against this skill's goal. For each friction (unclear step, missing tool, gate miss, rework, reviewer catch, or learner correction), log `.venv/bin/python -m scripts.issues propose --target skill:improve --evidence "<what happened>" --proposal "<concrete change>"` (or `.venv/bin/python -m scripts.issues add --kind <kind> --severity batch --source author --where <where> --what "<what>" --target skill:improve`). If the fix is a small, scoped edit to this `SKILL.md`, make it in the same PR.
