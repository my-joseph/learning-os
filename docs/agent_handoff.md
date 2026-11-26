# Interim Agent Handoff

## Purpose

Give an interim lead agent the learner decisions and boundaries Claude otherwise holds in private memory. This handoff supplements the repository rules; it does not replace them. Claude maintains this file in the same PR/turn when learner decisions change.

## Read first

Read these in order before acting:

1. `CLAUDE.md`
2. `rules/README.md`
3. `rules/00_core.md`
4. `.claude/skills/dispatch-worker/SKILL.md`

For any Studio UI work, also read [design principles](design/principles.md) and the [reference gallery](design/references/README.md) before planning or implementation.

## Learner decisions

### Completed

- Studio Generate button and **C08** `/api/generate-drill` route: approved and removed in Phase 2 (2026-11-26).
- Math and PRG template engines, template generators, and template-only scripts/tests removed and `rules/06` renamed to `rules/06_quality_contract.md` in Phase 3 (2026-11-26); drills and Similar variants are AI-only.

### Working style

- Speak with the learner in polite Thai; write learning content in English.
- Report promptly when a job finishes. Track background worker jobs to completion.
- Ask only about learner-owned decisions; proceed on routine implementation choices.
- The learner's Claude quota is low. The lead plans, writes bounded specs, reviews, and delivers; delegate implementation to workers when appropriate.
- Docs grow with code: when behavior, commands, paths, schemas, routes, or workflows change, update affected skills, rules, docs, and `CLAUDE.md` in the same PR. Include `Docs updated:` in the PR body. Consider `self_review` proposals, but act on them only when the lead agrees; explain disagreements.

### Models and workers

- Use `tools/agents/run-worker.sh`, the `dispatch-worker` skill, and `.claude/skills/dispatch-worker/common.md`.
- Route simple, high-volume, documentation, and read-only audit work to Luna (`gpt-6-luna`, Codex quota); everyday coding to Hydrogen (`gemini-4-hydrogen-high`); hard cross-cutting work to Neon (`gemini-4-neon-high`); independent review, blind-solve, skill trials, or parallel work to Argon (`gemini-4-argon-high`). Neon, Hydrogen and Argon share one `agy` quota pool (since 2026-11-24); Luna and Sol use the Codex pool.
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

### UI library (decided 2026-11-22)

- Practice Studio standardises on **shadcn/ui** (source copied into the repo, Radix primitives) on the CURRENT stack: Tailwind 3.4, React 18, Next 14 — no framework/Tailwind upgrades as part of this work. FlyonUI, daisyUI, HeroUI, Mantine were considered and rejected (research: `pilot/ui-library-research-2026-11-22/report.md`).
- Order: one-day proof of concept on a throwaway route (Button, Tabs, Dialog, Popover/Tooltip, Drawer) → learner looks at the real screen → then migrate one component family per PR (buttons → tabs/popovers → dialogs/drawers → tooltips/toasts); delete old local primitives only after parity.
- Keep behaviour identical (zero-leak, progress/reset flows, keyboard/focus, 44 px targets, reduced motion); existing Studio tests must pass; each UI PR includes before/after screenshots (desktop + phone width) for the learner.
- Use the [design tokens](design/system.md) and [component catalog](design/components.md). Follow the learner's 2026-11-25 extend-before-create decision and get approval for new colours.

### ON HOLD — do not start without the learner

- The Similar “+” button refactor and PRG Similar/variant bank remain on hold.
- **A10**: fix the case where a Worked Example can serve the same variant as an unopened Similar tab (including single-variant bank behavior); waits for the Similar “+” refactor.
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

These rules apply only to an agent the learner has explicitly named the interim lead. Workers started by `tools/agents/run-worker.sh` (`LEARNINGOS_ROLE=worker`) are never leads and must not dispatch other agents.

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

### TOKEN BUDGET — the lead thinks, workers do

The lead's tokens are the scarcest resource. Spend them on decisions, short specs, verdicts and learner messages; push everything else to workers (whose usage is logged in `pilot/agent-usage.jsonl`).

**The lead DOES (cheap):**
- Decide what to do next and which model does it (dispatch-worker routing).
- Write short job specs (aim ≤ 40 lines): goal, file paths + evidence lines, acceptance criteria, tests, "Docs updated".
- Review a finished PR from its summary: `gh pr view <N> --json body`, `gh pr diff <N> --name-only`, `gh pr checks <N>`; then spot-check 1–3 risky hunks with `gh pr diff <N> | grep`/`sed -n` (never the whole diff).
- Verify a claim with ONE targeted command (a grep, a single test, one file range of ≤ 60 lines).
- Merge, pull the main checkout, clean worktrees, report to the learner in a few lines.

**The lead does NOT (delegate instead):**
- Explore or read the codebase broadly, or read whole files > ~150 lines → send a read-only worker with a `DONE_FILE` report.
- Write or edit code, tests, vaults or long docs → worker job (only one-line doc fixes may be done directly).
- Run full suites (pytest, Studio build/tests) → workers run them before the PR; CI runs them again.
- Read worker logs or full reports → read only the PR body / report summary; use `tail -3`, `grep`, `head` with small limits.
- Poll in loops or re-check status repeatedly → launch jobs so completion is notified; wait.
- Re-derive known facts, re-read files already summarised, or narrate options it will not pursue.
- Write long replies: learner reports are short (results, what's next, decisions needed).

**Hard limits for the lead per task:** if it has used more than ~10 tool calls or read more than ~400 lines of output on one task without dispatching a worker, stop and delegate the rest. Cap every shell output (`| head -40`, `--name-only`, `grep -c`). Never paste large outputs into the conversation.

**Self-check before each action:** "Could a worker do this and give me a 10-line answer?" If yes, dispatch.

### LOG and Claude return

- Append each decision, merge, and worker launch to the local, gitignored `pilot/handoff-log.md`, recording date, action, reason, and PR/issue. Do not commit this log.
- Log friction with `python -m scripts.issues propose --target ...`.
- When Claude returns, Claude reads `pilot/handoff-log.md` and `python -m scripts.self_review`, then audits merged PRs.
