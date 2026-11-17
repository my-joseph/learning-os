# Practice Studio — design guide (v1, 2026-11-17)

The learner's brief: clean, few tags, easy to work a problem, no confusing buttons, no visual noise or text that does not help, a clear hierarchy, and colour and type chosen for ease of use. Every Studio PR follows this file.

## Principles
1. **The problem is the page.** The current question (prompt, figure, answer) gets the most space and the strongest type. Everything else is quieter.
2. **One primary action per state.** Exactly one filled button is visible at a time (Check, Try again, Run tests, Copy review command). Other actions are text/ghost buttons or live in a `⋯` menu.
3. **Say less.** No decorative badges, IDs, chips or status pills unless the learner acts on them. Drill IDs and metadata live in the switcher, not on the card. Helper text appears only when it changes what the learner does next.
4. **Empathy.** Wrong answers get calm, specific feedback and a retry, never alarm colours across the whole card. Copy is short, second person, never blaming ("Not quite — check the sign in step 2").
5. **No answers before an attempt.** Hidden content is not rendered or fetched until it is earned (see rules/00_core.md §6).

## Layout
- Shell: one slim header row — workspace switch (`Math` / `Programming`), drill switcher with search, then right-aligned theme toggle and Notion link. Below 640 px, everything except the switcher goes into a menu.
- Tiles row under the header: one small square per question/milestone, colour = first attempt.
- Main column max-width ~720 px, centred. Side panel (weak spots, due today) collapses into a drawer below 1024 px and is closed by default while answering.

## Colour (Tailwind tokens; light / dark)
- Neutral base: `zinc` (bg `zinc-50` / `zinc-950`, surface `white` / `zinc-900`, border `zinc-200` / `zinc-800`, muted text `zinc-500` / `zinc-400`).
- One accent for the primary action: `indigo-600` (dark `indigo-500`), text white.
- Status only, never decoration: correct `emerald-700`/`emerald-400`, assisted/partial `amber-600`/`amber-400`, wrong `rose-600`/`rose-400`. Status colour appears on tiles, a thin left border or an icon — not full-card fills.
- Default theme follows `prefers-color-scheme`; the toggle overrides it. Contrast AA at least.

## Type
- Geist Sans for UI and prose, Geist Mono for code and IDs, KaTeX for math.
- Scale: question prompt `text-lg`/`leading-relaxed`; body `text-base`; secondary `text-sm text-zinc-500`. One `h1` per page (drill title, `text-xl font-semibold`). Avoid all-caps labels and more than two weights on screen.

## Spacing and motion
- 8 px rhythm (`gap-2/4/6/8`), generous padding inside the question card (`p-6`, `p-4` on mobile).
- Motion only for disclosure (150 ms fade/slide); respect `prefers-reduced-motion`.

## Workspaces
- **Math**: prompt → figure → answer input + Check → feedback → (Try again | set-up / steps after reveal). Self-score buttons only after an attempt.
- **Programming** (dashboard, no editor): brief → visible tests → status line `tests · lint · types · review` (✓ / ✗ / –) → primary action (Open in VS Code, or Copy `ตรวจโค้ด <ID> <QID>` once tests pass) → review history and explain question in collapsible sections → reference locked until review = pass.
- **Labs**: same as Programming, tiles are milestones M1…Mn.
