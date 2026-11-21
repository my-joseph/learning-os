# Shared worker rules

- Work only on the assigned branch; never commit or push on `main`; never use `--no-verify`.
- Never print or commit `.env`, credentials, or tokens.
- Never touch learner data in `progress/`; tests must use a temporary `PROGRESS_DIR`.
- Never write to Notion; use `NOTION_DRY_RUN=1` / `LEARNINGOS_PILOT=1` when anything could sync.
- Learning content in drills, vaults, and docs is English. Preserve zero-leak: prompts, answers, steps, and hidden tests never reach a learner before a real attempt.
- Docs grow with the code: if your change alters behaviour, commands, flags, file paths, schemas, API routes, or workflows, update every affected `.claude/skills/*/SKILL.md`, `rules/*.md`, `docs/*.md`, and `CLAUDE.md` in the same PR (grep for the old name/flag/path). List them under `Docs updated:` in the PR body, or write `Docs updated: none needed — <reason>`.
- Run `.venv/bin/ruff check . && .venv/bin/ruff format --check .` and applicable pytest (`-n auto -q`, or `-m "not prg"` if PRG untouched). If Studio changed, run `npm run lint && npm run build && npm run test:telemetry` in `practice-studio/`.
- Commit in small conventional commits, push only the assigned branch, and open one PR. Do not merge unless the task's merge policy explicitly allows it.
- Put out-of-scope findings in the PR body instead of fixing them.
- Stop every server/background process started by the job before finishing. After opening the PR, report and finish; do not wait for more work.
