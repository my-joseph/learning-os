# Agent instructions

Read `CLAUDE.md`, `rules/README.md`, and `rules/00_core.md` before working. The canonical branch, PR, and merge policy is `rules/00_core.md` §10; do not duplicate or override it here. Task-specific instructions may narrow that policy.

Follow the Notion write and audit routes in `rules/00_core.md` and `rules/02_pedagogy.md`. Speak with the learner in polite Thai. Write learning content in English. Never expose drill prompts, answers, steps, or hidden tests before a real attempt.

## Role: worker or lead?

- You are a **WORKER** if you were started by `tools/agents/run-worker.sh` (env `LEARNINGOS_ROLE=worker`) or your prompt is a job spec. A worker does only its job: never launch or dispatch other agents (`agy`, `codex`, `claude`, `tools/agents/run-worker.sh`), never act as lead, never merge PRs. `docs/agent_handoff.md` is background for you, not your role.
- You are the **LEAD** only when the learner explicitly says so in the conversation (e.g. "you are the interim lead"). Only then read `docs/agent_handoff.md` and follow its lead rules, including the TOKEN BUDGET section.
