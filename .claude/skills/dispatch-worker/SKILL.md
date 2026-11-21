---
name: dispatch-worker
description: Delegate implementation, content, and audit jobs to worker models (Luna/Hydrogen/Neon) through tools/agents/run-worker.sh with isolated worktrees, bounded prompts, and tracked completion.
---

# Dispatch worker

Use this skill for Claude's worker delegation. The learner does not need a trigger phrase. Keep ownership of scope, review, and delivery.

## 1. Prepare the job

- Read the applicable rules and task-specific instructions. Make the spec the concatenation of `.claude/skills/dispatch-worker/common.md` and a job file.
- Write the job file and `.prompt` with a quoted heredoc (`<<'EOF'`) so backticks and shell substitutions remain literal. Include scope, acceptance criteria, verification, report expectations, and absolute paths for main-checkout-only `sources/` or `pilot/` data.
- Keep the worker prompt concrete and bounded. Name shared files and conflicts to avoid.

## 2. Create an isolated worktree

From the main checkout run `git worktree add ../wt-<name> -b <branch> origin/main`. Give each independent job its own worktree and branch. `sources/` and `pilot/` are gitignored in the main checkout; pass their absolute paths because they do not appear in fresh worktrees. Do not copy learner `progress/` into a worktree.

## 3. Start and track the worker

- Pick the model by job difficulty (learner policy, 2026-11-21):

  | Model | `MODELS` value | Use for |
  | :-- | :-- | :-- |
  | GPT Luna (cheapest, own Codex quota) | `gpt-6-luna` | High-volume or simple work: card extraction, source download/registry, docs, specs naming exact files, small single-file fixes, simple tests, read-only audits. |
  | Gemini Hydrogen (everyday coding) | `gemini-4-hydrogen-high` | A feature or UI component across a few files, focused bug hunts, new scripts with tests. |
  | Gemini Neon (hardest work) | `gemini-4-neon-high` | Architecture, multi-file refactors, cross-cutting bugs (scoring/save/sync parity), bugs other models failed on. |
  | Gemini Argon (strong, separate quota) | `gemini-4-argon-high` | Independent second opinion: blind solves, reviewing another worker's PR, skill trials; parallel medium/hard jobs when the Neon/Hydrogen pool is busy or low. |

  Quota pools: Neon + Hydrogen share one agy pool; Argon has its own pool; Luna has its own Codex pool. Spread parallel jobs across pools. For a reviewer/verifier, prefer a different model from the author (author Neon/Hydrogen -> reviewer Argon). Fall back across pools before dropping to Luna (e.g. Neon -> Argon -> Hydrogen -> Luna); narrow the spec when dropping to Luna.
- Set `MODELS` in fallback order, `MAX_SECS`, and `IDLE_AFTER_PR` as needed. The runner falls back on quota limits; model availability changes, so check memory/learner settings and do not hard-code one account. For continued work on a branch with an existing PR, use a large `IDLE_AFTER_PR` (for example `1500`) so a quiet log does not stop the worker early.
- Read-only jobs set a unique absolute `DONE_FILE` for each job. Code jobs complete when their PR exists.
- Run `MODELS=... IDLE_AFTER_PR=... MAX_SECS=... tools/agents/run-worker.sh <wt> <branch> <prompt> <log>` through the Bash tool with `run_in_background: true`. Do not launch it with detached shell syntax such as `( ... &)`; that loses tracked completion.
- Split independent jobs in parallel, each with a separate worktree. Do not let two workers write the same file or vault at once.

## 4. Review and deliver

- When the worker finishes, report the result to the learner promptly in Thai. Review the complete PR diff and `gh pr checks`; verify scope, tests, zero-leak, and no secrets/progress data.
- If revisions are needed, continue on the same branch and increase `IDLE_AFTER_PR` as above.
- Merge only according to `rules/00_core.md` §10: drill/lab-only PRs may self-merge; other PRs require the learner's explicit "merge". After merge, run `git pull --ff-only` in the main checkout and remove the worktree and branch, unless the learner asked to keep them.
- Stop all servers/background processes started by the job. Once the PR is open and reported, finish; do not wait for anything after opening it.

## Final documentation check

- [ ] Each job has a combined prompt, isolated worktree, tracked completion, reviewed diff/checks, and one PR or read-only report.
