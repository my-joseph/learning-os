# Practice Studio — design guide (v2, 2026-11-18)

The learner's brief: clean, few tags, easy to work a problem, no confusing buttons, no visual noise or text that does not help, a clear hierarchy, and colour and type chosen for ease of use. Every Studio PR follows this file.

## Principles
1. **The problem is the page.** The current question (prompt, figure, answer) gets the most space and the strongest type. Everything else is quieter.
2. **One primary action per state.** Exactly one filled button is visible at a time (icon-only `=` inside the field, Open in VS Code, Copy review request, Next problem/milestone). Other actions are text/ghost buttons or compact dialogs.
3. **Say less.** No decorative badges, IDs, chips or status pills unless the learner acts on them. Drill IDs and metadata live in the switcher, not on the card or in toasts/dialogs. Helper text appears only when it changes what the learner does next.
4. **Empathy.** Wrong answers get calm, specific feedback in a light-tinted result card and a retry — never saturated alarm colours. Copy is short, second person, never blaming ("Not quite — check the sign in step 2"), and uses the item noun of the workspace (`Question` for math, `Problem` for code drills, `Milestone` for labs).
5. **No answers before an attempt.** Hidden content is not rendered or fetched until it is earned (see rules/00_core.md §6).

## Layout
- Workspace switch (`Math` / `Programming`, icon-only): fixed vertical rail on the left-middle edge on `>=1024 px`, and an inline icon-only switch in the header below `1024 px`.
- Shell: one slim header row — drill switcher + Generate button, then right-aligned mobile side-drawer icon (`<1024 px`), theme toggle, Notion link, and Reset all icon button.
- Tiles row under the header: centred horizontally inside the header card (scrolls from the left when overflowing on narrow screens); one small square per question/milestone plus an icon-only Review tile.
- Main column max-width ~720 px, centred. Side panel (Due today & weak spots) collapses into a drawer below `1024 px` and is closed by default while answering.

## Colour (Tailwind tokens; light / dark)
- Neutral base: `zinc` (bg `zinc-50` / `zinc-950`, surface `white` / `zinc-900`, border `zinc-200` / `zinc-800`, muted text `zinc-500` / `zinc-400`).
- One accent for the primary action: `indigo-600` (both light and dark, `>= 4.5:1`), text white.
- Lists: every bulleted list uses the shared `ListDot` (6px indigo-600 / dark indigo-400 dot, centred on the first text line); no "•" glyphs or `list-disc`.
- Focus indicators: keyboard `focus-visible` indigo rings only (`indigo-600` light / `indigo-400` dark); suppress mouse-click focus rings and browser default outlines.
- Status only, never decoration: correct `emerald-700`/`emerald-400`, assisted/partial `amber-700`/`amber-400`, wrong `rose-600`/`rose-400`. Status colour appears on tiles, icons, unrounded left borders, or light status tints (`bg-*-50` / `dark:bg-*-500/10`) on result cards and selected choice states — never as a left-accent border on rounded boxes or saturated full-card fills.
- Default theme follows `prefers-color-scheme`; the toggle overrides it. Contrast AA (`>= 4.5:1`) everywhere.

## Type
- Geist Sans for UI and prose, Geist Mono for code and IDs, KaTeX for math.
- Scale: question prompt `text-base` (16 px) / `leading-relaxed`; body `text-base`; secondary `text-sm text-zinc-500`. One `h1` per page (drill/lab title or not-found heading, `text-lg font-semibold`, 18 px). No uppercase/all-caps labels; at most two font weights on screen.

## Spacing and motion
- 8 px rhythm (`gap-2/4/6/8`), generous padding inside the question card (`p-6`, `p-4` on mobile).
- Status toasts stack bottom-right (`>=640 px`) / bottom-centre (`<640 px`).
- Calm ease-out motion via `src/lib/motion.ts` and `<Reveal>` for disclosures, dialogs, and the mobile drawer; respect `prefers-reduced-motion`.

## Workspaces
- **Math**: prompt → figure → answer input with `=` inside the field → feedback → (Try again | Hint / set-up / steps after reveal). Self-score buttons only after an attempt.
- **Programming** (dashboard, no editor): brief → visible tests → status line `Tests  Lint  Types  Review` (✓ / ✗ / –) → primary action (Open in VS Code, or Copy `ตรวจโค้ด <ID> <QID>` once tests pass) → review history and explain question in collapsible sections → reference locked until review = pass.
- **Labs**: same as Programming, tiles are milestones M1…Mn.
