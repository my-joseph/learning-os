---
name: dispatch-worker
description: Delegate implementation, content, and audit jobs to worker models (Luna/Sol/Hydrogen/Neon/Carbon) through tools/agents/run-worker.sh with isolated worktrees, bounded prompts, and tracked completion.
---

# Dispatch worker

Use this skill for Claude's worker delegation. The learner does not need a trigger phrase. Keep ownership of scope, review, and delivery.

## 1. Prepare the job

- Read the applicable rules and task-specific instructions. Make the spec the concatenation of `.claude/skills/dispatch-worker/common.md` and a job file.
- Write the job file and `.prompt` with a quoted heredoc (`<<'EOF'`) so backticks and shell substitutions remain literal. Include scope, acceptance criteria, verification, report expectations, and absolute paths for main-checkout-only `sources/` or `pilot/` data.
- Keep each job to one concern. Split a spec that names multiple subsystems or more than about eight files to change into independent jobs; do not split tightly coupled work that cannot be reviewed or verified separately.
- Put exact file paths and the relevant evidence with line numbers near the start of the job spec. Give enough existing behavior and code context for the worker to make the change without repeating repository exploration.
- List concrete acceptance criteria and the exact tests to add or run. For UI or flow work, name the expected screens and states (including loading, empty, error, and success states when applicable) so review does not uncover an unplanned state late.
- Route each sub-slice to the lightest capable model in the model table below. Keep complex architecture or cross-cutting work on a capable model; narrow the slice when routing it to a lighter model.
- Keep the worker prompt concrete and bounded. Name shared files and conflicts to avoid.

## 2. Create an isolated worktree

From the main checkout run `git worktree add ../wt-<name> -b <branch> origin/main`. Give each independent job its own worktree and branch. `sources/` and `pilot/` are gitignored in the main checkout; pass their absolute paths because they do not appear in fresh worktrees. Do not copy learner `progress/` into a worktree.

## 3. Start and track the worker

- Pick the lightest capable model by sub-slice difficulty (learner policy, 2026-11-21):

  | Model | `MODELS` value | Use for |
  | :-- | :-- | :-- |
  | GPT Luna (cheapest, own Codex quota) | `gpt-6-luna` | High-volume or simple work: card extraction, source download/registry, docs, specs naming exact files, small single-file fixes, simple tests, read-only audits. |
  | GPT Sol (Codex pool) | `gpt-6.2-sol` | Medium coding and fixes when the agy pool is busy or out; second-opinion reviews of Gemini-authored PRs. |
  | Gemini Hydrogen (everyday coding) | `gemini-4-hydrogen-high` | A feature or UI component across a few files, focused bug hunts, new scripts with tests. |
  | Gemini Neon (hardest work) | `gemini-4-neon-high` | Architecture, multi-file refactors, cross-cutting bugs (scoring/save/sync parity), bugs other models failed on. |
  | Gemini Carbon (deepest thinking, slow) | `gemini-4-carbon-high` | Escalation tier: root-cause of hard cross-system bugs (races, concurrency), architecture/interface design, security audits, independent high-risk PR reviews, long background runs; or when Neon failed twice. Plan with Carbon, then hand the implementation to Hydrogen. |

  Quota pools (2026-11-24): Neon, Hydrogen and Carbon share ONE agy pool; Sol (gpt-6.2-sol) and Luna use the Codex pool. Argon is retired (weaker than Hydrogen, pricier than Neon) — do not route to it. Spread parallel jobs across pools. For an independent reviewer prefer a different model from the author (author Hydrogen/Neon -> reviewer Carbon for high-risk, Sol otherwise). When the agy pool is out, fall back to the Codex pool (Sol, then Luna); narrow the spec when dropping to Luna.
- Set `MODELS` in fallback order, `MAX_SECS`, and `IDLE_AFTER_PR` as needed. The runner falls back on quota limits; model availability changes, so check memory/learner settings and do not hard-code one account. For continued work on a branch with an existing PR, use a large `IDLE_AFTER_PR` (for example `1500`) so a quiet log does not stop the worker early. An existing PR counts as done only after this run advances its PR head; a fresh branch counts as done when its PR appears.
- Read-only jobs set a unique absolute `DONE_FILE` for each job. Code jobs on a fresh branch complete when their PR exists; continued jobs complete after this run pushes a new commit to the existing PR.
- Run `MODELS=... IDLE_AFTER_PR=... MAX_SECS=... tools/agents/run-worker.sh <wt> <branch> <prompt> <log>` through the Bash tool with `run_in_background: true`. Do not launch it with detached shell syntax such as `( ... &)`; that loses tracked completion.
- Split independent jobs in parallel, each with a separate worktree. Do not let two workers write the same file or vault at once; order dependent jobs sequentially (merge prerequisite PRs before starting follow-up jobs on overlapping files or tests).

## 4. Review and deliver

- When the worker finishes, report the result to the learner promptly in Thai. Review the complete PR diff and `gh pr checks`; verify scope, tests, zero-leak, and no secrets/progress data. Confirm the branch merged latest `origin/main` and reran clean-env CI-equivalent checks before opening/updating the PR, and verify `gh pr checks` shows CI actually started (GitHub silently skips `pull_request` CI while a PR has merge conflicts).
- If revisions are needed, continue on the same branch and increase `IDLE_AFTER_PR` as above. Whenever a worker PR needed revisions (review fixes, conflict/CI rework, or a re-run), log a proposal with `.venv/bin/python -m scripts.issues propose --target job:<type> --evidence "PR #<N> (<model>): <what needed fixing>" --proposal "<concrete change>"` (or `--target model:<model>` when model routing or capability was the cause).
- Merge only according to `rules/00_core.md` §10: drill/lab-only PRs may self-merge; other PRs require the learner's explicit "merge". After merge, run `git pull --ff-only` in the main checkout and remove the worktree and branch, unless the learner asked to keep them.
- Stop all servers/background processes started by the job. Once the PR is open and reported, finish; do not wait for anything after opening it.

## Final documentation check

- [ ] Each job has a combined prompt, isolated worktree, tracked completion, reviewed diff/checks, and one PR or read-only report.

## Self-review

After the run, compare the outcome against this skill's goal. For each friction (unclear step, missing tool, gate miss, rework, reviewer catch, or learner correction), log `.venv/bin/python -m scripts.issues propose --target skill:dispatch-worker --evidence "<what happened>" --proposal "<concrete change>"` (or `.venv/bin/python -m scripts.issues add --kind <kind> --severity batch --source author --where <where> --what "<what>" --target skill:dispatch-worker`). If the fix is a small, scoped edit to this `SKILL.md`, make it in the same PR.
