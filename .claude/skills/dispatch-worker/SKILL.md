---
name: dispatch-worker
description: Delegate implementation, content, and audit jobs to worker models (Luna/Sol/Hydrogen/Neon/Carbon) through tools/agents/run-worker.sh with isolated worktrees, bounded prompts, and tracked completion.
---

# Dispatch worker

Use this skill for Claude's worker delegation. The learner does not need a trigger phrase. Keep ownership of scope, review, and delivery.

## 1. Prepare the job

- Read the applicable rules and task-specific instructions. Make the spec the concatenation of `.claude/skills/dispatch-worker/common.md` and a job file.
- UI jobs: read [design principles](../../../docs/design/principles.md) and the [reference gallery](../../../docs/design/references/README.md) first; build with shared components and their variants.
- Write the job file and `.prompt` with a quoted heredoc (`<<'EOF'`) so backticks and shell substitutions remain literal. Include scope, acceptance criteria, verification, report expectations, and absolute paths for main-checkout-only `sources/` or `pilot/` data.
- Keep each job to one concern. Split a spec that names multiple subsystems or more than about eight files to change into independent jobs; do not split tightly coupled work that cannot be reviewed or verified separately.
- Put exact file paths and the relevant evidence with line numbers near the start of the job spec. Give enough existing behavior and code context for the worker to make the change without repeating repository exploration.
- List concrete acceptance criteria and the exact tests to add or run. For UI or flow work, name the expected screens and states (including loading, empty, error, and success states when applicable) so review does not uncover an unplanned state late.
- **Spec checklist (fill applicable items; mark others N/A with a reason):** shared contracts: specify math and PRG behavior, including intentional differences; test legacy read/write with isolated fixtures and ensure mismatches are reported; matching/dedup: concrete false-match pairs as negative tests; anti-gaming gates: before first review, test risk-based bypass classes and valid near-misses, explain coverage and limits; normalization: define preserved/ignored syntax and test unknown syntax conservatively, using an allowlist only for bounded vocabularies; vault/archetype: for changed levels or boundaries, devise an original representative item and expected tags, check via independent blind-solve where applicable, and use canonical operation terms; git history: specify required history and test shallow/unavailable cases, fetching what's needed or returning explicit incomplete/unknown; audits: distinguish vault base level from vault_report earned level and exact tags from semantic aliases, checkpoint authorized reports periodically as partial then reconcile, and record pinned SHA plus actual assessor/verifier models (pending/unknown until confirmed). Use representative bounded samples and targeted development tests; set task-appropriate timeouts with headroom and cleanup, then run required full checks or report what was skipped.
- Cross-cutting: avoid giant generic specs; identify actual models after fallback and keep independent review on a different actual model; check file overlap before dispatch and recheck PR head and CI before merge; a completed checklist is not proof.
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

  Default (learner, 2026-11-25): the agy pool drains fast — route to the Codex pool first (Sol for coding/UI, Luna for simple work); use agy (Hydrogen/Neon/Carbon) only when a job clearly needs it (hardest cross-cutting work or a high-risk independent review). For Codex UI jobs, list every acceptance point, require self-verification screenshots (desktop + phone, light + dark, saved under pilot/, never committed) with a ✅ per point in the PR body, and review the screenshots and key component diff before merging.
  Quota pools (2026-11-24): Neon, Hydrogen and Carbon share ONE agy pool; Sol (gpt-6.2-sol) and Luna use the Codex pool. Argon is retired (weaker than Hydrogen, pricier than Neon) — do not route to it. Spread parallel jobs across pools. For an independent reviewer prefer a different model from the author (author Hydrogen/Neon -> reviewer Carbon for high-risk, Sol otherwise). When the agy pool is out, fall back to the Codex pool (Sol, then Luna); narrow the spec when dropping to Luna.
- Set `MODELS` in fallback order, `MAX_SECS`, and `IDLE_AFTER_PR` as needed. The runner falls back on quota limits; model availability changes, so check memory/learner settings and do not hard-code one account. For continued work on a branch with an existing PR, use a large `IDLE_AFTER_PR` (for example `1500`) so a quiet log does not stop the worker early. An existing PR counts as done only after this run advances its PR head; a fresh branch counts as done when its PR appears.
- Read-only jobs set a unique absolute `DONE_FILE` for each job. Code jobs on a fresh branch complete when their PR exists; continued jobs complete after this run pushes a new commit to the existing PR.
- For runner jobs that must survive the launching session, use the documented platform-supported detached launch, absolute prompt/log paths and a unique completion marker; record the process and monitor its exit, timeout and cleanup. Resolve relative paths before the runner changes directory.
- On macOS, launch with: `MODELS=... nohup perl -MPOSIX -e 'setsid; exec @ARGV' "$MAIN"/tools/agents/run-worker.sh <wt> <branch> <absolute-prompt> <absolute-log> </dev/null >"<absolute-log>.runner" 2>&1 &`
- Split independent jobs in parallel, each with a separate worktree. Do not let two workers write the same file or vault at once; order dependent jobs sequentially (merge prerequisite PRs before starting follow-up jobs on overlapping files or tests).
- Before dispatch, map overlapping files and dependencies; serialize jobs editing the same files or plan integration. For open overlapping PRs, merge current main and rerun affected checks after a relevant sibling merge and before final review/merge; recheck head and CI after later changes. Finish revision fixes before new lane items. Log friction as proposals and send each proposal, idea, issue, and non-none friction to Log Keeper.

## 4. Review and deliver

- When the worker finishes, report the result to the learner promptly in Thai. Review the complete PR diff and `gh pr checks`; verify scope, tests, zero-leak, and no secrets/progress data. Confirm the branch merged latest `origin/main` and reran clean-env CI-equivalent checks before opening/updating the PR, and verify `gh pr checks` shows CI actually started (GitHub silently skips `pull_request` CI while a PR has merge conflicts).
- If revisions are needed, continue on the same branch and increase `IDLE_AFTER_PR` as above. Whenever a worker PR needed revisions (review fixes, conflict/CI rework, or a re-run), log a proposal with `.venv/bin/python -m scripts.issues propose --target job:<type> --evidence "PR #<N> (<model>): <what needed fixing>" --proposal "<concrete change>"` (or `--target model:<model>` when model routing or capability was the cause).
- Merge only according to `rules/00_core.md` §10: drill/lab-only PRs may self-merge; other PRs require the learner's explicit "merge". After merge, run `git pull --ff-only` in the main checkout and remove the worktree and branch, unless the learner asked to keep them.
- Stop all servers/background processes started by the job. Once the PR is open and reported, finish; do not wait for anything after opening it.

## Final documentation check

- [ ] Each job has a combined prompt, isolated worktree, tracked completion, reviewed diff/checks, and one PR or read-only report.

## Self-review

After the run, compare the outcome against this skill's goal. For each friction (unclear step, missing tool, gate miss, rework, reviewer catch, or learner correction), log `.venv/bin/python -m scripts.issues propose --target skill:dispatch-worker --evidence "<what happened>" --proposal "<concrete change>"` (or `.venv/bin/python -m scripts.issues add --kind <kind> --severity batch --source author --where <where> --what "<what>" --target skill:dispatch-worker`). If the fix is a small, scoped edit to this `SKILL.md`, make it in the same PR.
