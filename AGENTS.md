# Instructions for AI agents (Gemini / Antigravity and others)

**Never commit or push on `main`.** Before the first edit, create a branch (`git switch -c fix/<short-name>`); commit there, `git push -u origin <branch>`, `gh pr create`, and stop: the learner reads the PR and says "merge". The only exception is a PR that changes just a new drill file, its unit's vault and `id_map.json`, which you may merge yourself. A small UI fix is not an exception. Git hooks in `.githooks/` block commits and pushes on `main`; if one blocks you, make a branch, never use `--no-verify`.

Then read `CLAUDE.md` (project facts, commands, do-nots) and `rules/README.md` (which rule module to load for your task). Talk to the learner in Thai; everything written to Notion and drills is English. The learner studies the drills: never show them prompts' answers.
