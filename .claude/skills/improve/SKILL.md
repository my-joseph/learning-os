---
name: improve
description: Assess one LearningOS area deeply and prepare a learner-approved phased improvement roadmap. Use when the learner says "ปรับปรุง <area>" or "improve <area>" for engine, ux, pipeline, or content.
---

# Improve one area

Health-check asks what is broken now (broad and shallow). Improve asks how one area should get better (focused and deep). Assess first, propose a phased roadmap, wait for the learner's decision, then execute approved items as small PRs. Speak to the learner in polite Thai; write reports and learning content in English. Keep this skill read-only until roadmap approval.

## 1. Brief and pin context

- Parse `area` (`engine`, `ux`, `pipeline`, or `content`) and optional focus. If no valid area is named, ask which area; do not start a broad audit.
- Resolve `MAIN` from `git worktree list`; capture `AUDIT_SHA=$(git -C "$MAIN" rev-parse HEAD)` once. Create `$MAIN/pilot/improve-<area>-<YYYY-MM-DD>/` and put all reports there. This folder belongs to the main checkout even when the skill runs in another worktree.
- Do not read or modify learner `progress/`. Never write to Notion; use isolated pilot data for any UI work. Never expose drill prompts, answers, steps, or hidden tests before a real attempt.

## 2. Gather context before proposing (mandatory)

Read context at the pinned `AUDIT_SHA` before making recommendations. Record sources and freshness in `context.md`.

- Read the latest `$MAIN/pilot/health-*/report.md` (and relevant checks/findings) plus `gh pr list --state open --base main`; mark findings already fixed on main or covered by an open PR.
- Run `.venv/bin/python -m scripts.issues list`; inspect `docs/backlog.md` and relevant project memory notes and learner decisions. Find memory via the main checkout's Claude project memory directory; read its `MEMORY.md` index and relevant linked notes. If an input is missing, record that limitation.
- Explicitly check decisions marked ON HOLD, including Similar “+” refactor and template removal, legacy PRG drill/lab retire-and-rebuild, scheduled jobs, and `/api/generate-drill` removal. Do not revive deferred work in a roadmap unless the learner has since approved it.
- Read `rules/00_core.md` §10 and its refactor invariants: characterize existing behavior first, keep refactor commits separate from features, and keep tests green at every step.
- Treat learner-pasted/external reports as leads, not current truth. Verify each claim against pinned source and current main before proposing work.

## 3. Assess one area

- Read `areas/<area>.md` and delegate a bounded, read-only assessment to worker(s) using `.claude/skills/dispatch-worker/SKILL.md`. Pin every worker to `AUDIT_SHA`; use isolated worktrees, unique reports, and English output. Do not let workers edit product files.
- Save `assessment.md` in the dated folder. Include current state, strengths worth preserving, evidence with exact `file:line`, and relevant measurements (size, complexity, duplication, coverage, timings, or per-stage cost as applicable). Separate measured facts from hypotheses.
- Verify every finding yourself or with a second worker. Drop items fixed on main, already in an open PR, or deferred by the learner. Note stale or unverified inputs instead of treating them as facts.

## 4. Propose the roadmap and stop for the learner

- Write `roadmap.md` with phases only where useful: Phase 1 quick wins/debt, Phase 2 structural improvements, Phase 3 new capability. Each item must state goal, evidence, measurable expected benefit, risk, size, model (`Luna`, `Hydrogen`, or `Neon` per dispatch-worker), dependencies, and a test-first plan. For refactors, the plan starts with characterization tests and a before/after measure.
- List learner decisions and deferred items in a separate section; distinguish choices needed now from approved standing decisions. Do not execute roadmap items before approval.
- Give the learner a concise Thai summary of evidence, phases, trade-offs, and decisions needed. Stop for the learner to select/approve items. Continue only with the approved scope.

## 5. Execute approved items

- Implement each approved item in its own small PR via `dispatch-worker`; one PR per item. For refactors, add characterization tests first, preserve behavior, measure before/after, and keep refactor changes separate from feature changes. Run applicable checks and report failures honestly.
- Never combine refactor and feature work. Do not write to Notion or learner progress. Keep drill content English and enforce zero-leak gates.

## 6. Close the improvement cycle

- Update roadmap item status after each PR. If behavior or commands changed, update `CLAUDE.md` and relevant docs in the same scoped PR. Log follow-up issues with `python -m scripts.issues add` when required by `rules/00_core.md` §11.
- Review each PR and checks, then stop after the approved work is delivered. Do not merge unless the learner explicitly says “merge”. Stop every server or background process started during UX work.

## Final check

- [ ] Assessment and roadmap use the same `AUDIT_SHA`; evidence was checked against current main.
- [ ] Fixed, open-PR, and deferred items are excluded or clearly identified; learner approval is recorded before execution.
- [ ] Each approved item has its own PR and applicable verification; no learner progress, Notion writes, or leaked exercise material was used.
