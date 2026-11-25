# Shared worker rules

## Job spec quality

- Assign one concern per job. Split a spec that covers multiple subsystems or more than about eight files to change into independently reviewable jobs; keep tightly coupled changes together when they cannot be verified separately.
- Put exact file paths and evidence with line numbers near the start of every job spec so the worker can act without re-exploring the repository.
- Every spec lists concrete acceptance criteria and the exact tests to add or run.
- For UI or flow features, specify expected screens and states, including loading, empty, error, and success states where relevant.
- UI jobs: read `docs/design/principles.md` and the reference gallery first; follow [design tokens](../../../docs/design/system.md) and [component governance](../../../docs/design/components.md).
- Route each sub-slice to the lightest model capable of meeting its acceptance criteria; narrow the scope when choosing a lighter model.

- Work only on the assigned branch; never commit or push on `main`; never use `--no-verify`.
- Never print or commit `.env`, credentials, or tokens.
- Never touch learner data in `progress/`; tests must use a temporary `PROGRESS_DIR`.
- Never write to Notion; use `NOTION_DRY_RUN=1` / `LEARNINGOS_PILOT=1` when anything could sync.
- Learning content in drills, vaults, and docs is English. Preserve zero-leak: prompts, answers, steps, and hidden tests never reach a learner before a real attempt.
- Docs grow with the code: if your change alters behaviour, commands, flags, file paths, schemas, API routes, or workflows, update every affected `.claude/skills/*/SKILL.md`, `rules/*.md`, `docs/*.md`, and `CLAUDE.md` in the same PR (grep for the old name/flag/path). List them under `Docs updated:` in the PR body, or write `Docs updated: none needed — <reason>`. For internal fixes or refactors that do not change documented behaviour, `Docs updated: none needed — <reason>` is the right answer — do not make filler doc edits just to satisfy `docs/doc_map.json`.
- Test loop: while developing, run only the tests that cover what you changed (the new/edited test files plus the existing test modules for the touched code, e.g. `pytest -q tests/test_x.py -k name`, or the single Studio test file); do NOT rerun the full suite after every edit. Run the full CI-equivalent suite ONCE, right before opening/updating the PR (after merging origin/main). Use `-q` so passing runs print one line; read failure details only for failing tests.
- Before opening or updating the PR: run `git fetch && git merge origin/main` (no rebase), resolve conflicts keeping both behaviours, then rerun the CI-equivalent checks in a clean env (`env -u LEARNINGOS_PILOT -u NOTION_DRY_RUN`): `.venv/bin/ruff check . && .venv/bin/ruff format --check .`, applicable pytest (`-n auto -q` if PRG/`code_engine` touched, without assuming `tools/lint/` npm deps are installed, or `-m "not prg"` if PRG untouched), and `npm run lint && npm run build && npm run test:telemetry` in `practice-studio/` if Studio changed. After pushing, check `gh pr checks` confirms CI actually started (GitHub skips `pull_request` CI while a PR conflicts).
- Commit in small conventional commits, push only the assigned branch, and open one PR. Do not merge unless the task's merge policy explicitly allows it.
- Put out-of-scope findings in the PR body instead of fixing them.
- Stop every server/background process started by the job before finishing. After opening the PR, report and finish; do not wait for more work.
- You are a WORKER (LEARNINGOS_ROLE=worker): never launch or dispatch other agents (agy, codex, claude, tools/agents/run-worker.sh), never merge PRs, and ignore any "lead" instructions in AGENTS.md / docs/agent_handoff.md.
- UI components: extend an existing shared component with a variant first; for a genuinely new role, start from shadcn/ui (https://ui.shadcn.com) restyled with Studio tokens; custom code only if shadcn has nothing (see docs/design/components.md).
