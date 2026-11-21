# Practice Studio UX assessment playbook

Assess one Studio journey at a time against `docs/studio_design.md`. Use pilot/mock data only (`LEARNINGOS_PILOT=1`); never show learner progress in screenshots and never write to Notion.

Use the `AUDIT_SHA` pinned by `improve/SKILL.md` for repository evidence and record any difference from current `origin/main`. If using git worktrees, resolve `$MAIN` to the main checkout for shared `pilot/` reports; do not assume those files or `.venv` exist in the worker worktree.

## Inspect

- Start the Studio locally on `127.0.0.1:3000` with `npm run dev` in `practice-studio/`, then use the browser tool (Puppeteer) to click through relevant key flows: drill, Similar, review, due today, weak spots, and lab. Record which flows were actually exercised.
- Capture desktop and phone-width screenshots. Compare spacing, hierarchy, interaction and status colors with `docs/studio_design.md` and `practice-studio/src/lib/statusTone.ts`.
- Check keyboard operation, visible focus, basic contrast, and loading, empty, and error states. Use only seeded mock content; never reveal prompts, answers, solution steps, or hidden tests before a real attempt.
- Read `/Users/Joseph/.claude/projects/<main-checkout-project>/memory/ux-build-loop.md` when available. Proposed UX execution follows the learner's loop: design-agent proposal → build → tester-agent click-through → adjustment.

## Better means

- Learners can complete the target flow without confusion or accidental spoiler exposure.
- The interface matches the documented design and status-tone tokens across desktop and phone widths.
- Keyboard/focus, contrast, and loading/empty/error states give usable feedback.
- Report screenshots by path, viewport, flow, and finding; tie each claim to a reproducible step and source location where possible.

## Lifecycle

Use a tracked foreground server process and stop it when browser inspection ends. Do not leave servers or browser-driven background tasks running. Keep findings read-only; build and tester work happens only after the learner approves roadmap items.
