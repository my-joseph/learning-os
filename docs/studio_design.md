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
- Stepper row under the header: centred horizontally inside the header card; compact 24 px desktop / 22 px mobile circles use `Q1`, `Q2`, … for drills and `M1`, `M2`, … for labs. Connector lines are indigo up to the current step and zinc after it. Small desktop labels show only `Level N` for drills, the milestone name for labs, and `Review` on the trailing clipboard step. Buttons keep 44 px minimum tap targets, while keyboard focus outlines hug the circle outside the current-step halo. On mobile (`<640 px`) labels hide and the strip scrolls horizontally with the current step centred and edge fades.
- Main column max-width ~720 px, centred. Side panel (Due today & weak spots) collapses into a drawer below `1024 px` and is closed by default while answering.

## Colour (Tailwind tokens; light / dark)
- Neutral base: `zinc` (bg `zinc-50` / `zinc-950`, surface `white` / `zinc-900`, border `zinc-200` / `zinc-800`, muted text `zinc-500` / `zinc-400`).
- One accent for the primary action: `indigo-600` (both light and dark, `>= 4.5:1`), text white.
- Typography (learner decision 2026-11-19): **Source Sans Pro** for all UI and prompt text (`font-sans`, weights 400/600/700 — no 500, so `font-medium` renders as 400); **Roboto Slab** as the secondary/display accent (`font-display`) for every non-code label or number that used to be mono — scores, Q1/Q2 labels, counts, timers, curriculum IDs (`MTH-…`, `PRG-…`, `DRL-…`); **Geist Mono** (`font-mono`) only for code (snippets, examples, tests, function names, typed code answers); KaTeX fonts for math.
- Lists: every bulleted list uses the shared `ListDot`, centred on the first text line; no "•" glyphs or `list-disc`. Three kinds, picked from the heading above the list (`listKindForHeading`): **task** = filled indigo dot (Requirements, Your task, rules, Visible tests); **info** = filled zinc dot (Observed symptoms, notes, review findings, any other heading); **limit** = hollow indigo ring (Return contract, Constraints, Input shape).
- Focus indicators: keyboard `focus-visible` indigo rings only (`indigo-600` light / `indigo-400` dark); suppress mouse-click focus rings and browser default outlines.
- Status only, never decoration: **no yellow/amber for any answer status** (learner decision 2026-11-19). Clean first-try `correct` uses emerald green; any non-clean eventually-correct or partial answer (`assisted`: correct with help, correct on retry / score 0.5, partial / `equivalent_not_in_form`, self-score 0.5, result card `"almost"`, Review & Sync `"Assisted / partial"`) uses green outline (no fill); `wrong` uses rose; `skipped` uses a dashed zinc outline; `notTried` and unanswered `usedHelp` use a plain outline (no colour). Amber is reserved exclusively for non-status operational warnings via `warningTone` (degraded sync banner, paused timer, pending/warning toasts, hint and weak-spot trap left-borders). Status colour appears on stepper circles, tab status icons, unrounded left borders, or light status tints on result cards and selected choice states — never as a left-accent border on rounded boxes or saturated full-card fills.
- Default theme follows `prefers-color-scheme`; the toggle overrides it. Contrast AA (`>= 4.5:1`) everywhere.

## Colour tokens
- **Rule (enforced by `tests/statusTokens.test.tsx`):** never hard-code a status colour (`emerald-*`, `amber-*`, `yellow-*`, `rose-*`); import recipes from `src/lib/statusTone.ts` (`statusTone` for answer/progress status, `warningTone` for non-status warnings). Diagram/figure palettes (`Interactive*`, `MathFigure/*`, `VisualRenderer`, `VSCodeBlock`) are out of scope.
- Single source of truth: RGB channel custom properties in `practice-studio/src/app/globals.css` (`:root, html.light` and `html.dark, .dark`), exposed in `practice-studio/tailwind.config.ts` with `rgb(var(--x) / <alpha-value>)` so opacity modifiers work. Changing a colour requires editing one variable in `globals.css`.

| CSS token | Tailwind key | Meaning | Light (RGB / hex) | Dark (RGB / hex) |
| :--- | :--- | :--- | :--- | :--- |
| `--status-correct` | `status-correct` | Clean first-try correct fill (stepper, tab mark, tile, dot, choice badge) | `5 150 105` (`#059669`, emerald-600) | `16 185 129` (`#10b981`, emerald-500) |
| `--status-correct-text` | `status-correct-text` | Clean correct text, icons, and left-borders (`>= 4.5:1` AA) | `4 120 87` (`#047857`, emerald-700) | `52 211 153` (`#34d399`, emerald-400) |
| `--status-correct-soft` | `status-correct-soft` | Soft tint for correct result cards, synced banner, selected choices | `236 253 245` (`#ecfdf5`, emerald-50) | `23 40 37` (`#172825`, ~emerald-500/10) |
| `--status-on-correct` | `status-on-correct` | Icon/text colour on `status-correct` fills | `255 255 255` (`#ffffff`, white) | `9 9 11` (`#09090b`, zinc-950) |
| `--status-assisted` | `status-assisted` | Assisted / partial / score-0.5: same green as correct but an **outline, no fill** (never amber) | `5 150 105` (`#059669`, emerald-600) | `16 185 129` (`#10b981`, emerald-500) |
| `--status-assisted-soft` | `status-assisted-soft` | Reserved (assisted has no fill) | `236 253 245` | `23 40 37` |
| `--status-on-assisted` | `status-on-assisted` | Assisted text/icon colour (AA) | `4 120 87` (`#047857`, emerald-700) | `52 211 153` (`#34d399`, emerald-400) |
| `--status-wrong` | `status-wrong` | Wrong / failing / regressed fill, border, and AA text | `225 29 72` (`#e11d48`, rose-600) | `251 113 133` (`#fb7185`, rose-400) |
| `--status-wrong-soft` | `status-wrong-soft` | Soft tint for wrong result cards, error sync card, wrong choices | `255 241 242` (`#fff1f2`, rose-50) | `46 28 34` (`#2e1c22`, ~rose-500/10) |
| `--status-on-wrong` | `status-on-wrong` | Icon/text colour on `status-wrong` fills | `255 255 255` (`#ffffff`, white) | `9 9 11` (`#09090b`, zinc-950) |
| `--status-skipped` | `status-skipped` | Dashed outline for skipped items and active untried tab border | `161 161 170` (`#a1a1aa`, zinc-400) | `113 113 122` (`#71717a`, zinc-500) |
| `--status-neutral` | `status-neutral` | Plain outline and neutral dot for untried / unanswered items | `212 212 216` (`#d4d4d8`, zinc-300) | `63 63 70` (`#3f3f46`, zinc-700) |
| `--warning` | `warning` | Non-status warning text/icon (paused timer, pending/warn toast, degraded sync) | `180 83 9` (`#b45309`, amber-700) | `251 191 36` (`#fbbf24`, amber-400) |
| `--warning-soft` | `warning-soft` | Soft banner tint for degraded sync warning card | `255 251 235` (`#fffbeb`, amber-50) | `46 37 22` (`#2e2516`, ~amber-500/10) |
| `--warning-border` | `warning-border` | Left-border accent for checkpoint hints and weak-spot trap notes | `217 119 6` (`#d97706`, amber-600) | `251 191 36` (`#fbbf24`, amber-400) |
| `--accent` | `accent` | Brand primary accent (exposed for gradual migration; used on active step highlight) | `79 70 229` (`#4f46e5`, indigo-600) | `129 140 248` (`#818cf8`, indigo-400) |

## Type
- Geist Sans for UI and prose, Geist Mono for code and IDs, KaTeX for math.
- Scale: question prompt `text-base` (16 px) / `leading-relaxed`; body `text-base`; secondary `text-sm text-zinc-500`. One `h1` per page (drill/lab title or not-found heading, `text-lg font-semibold`, 18 px). No uppercase/all-caps labels; at most two font weights on screen.

## Spacing and motion
- 8 px rhythm (`gap-2/4/6/8`), generous padding inside the question card (`p-6`, `p-4` on mobile).
- Status toasts stack bottom-right (`>=640 px`) / bottom-centre (`<640 px`).
- Calm ease-out motion via `src/lib/motion.ts` and `<Reveal>` for disclosures, dialogs, and the mobile drawer; respect `prefers-reduced-motion`.

## Workspaces
- **Math**: similar-question tab strip at the top of the card (always shown when variants exist, with locked muted ghost tabs until the first substantive attempt on the real question in the current cycle) → prompt → figure → answer input with `=` inside the field → feedback → Hint / equation set-up / steps available before answering on both real and similar questions (revealing before an answer marks that item as used help). Self-score buttons only after an attempt on the real question.
- **Programming** (dashboard, no editor): brief → visible tests → status line `Tests  Lint  Types  Review` (✓ / ✗ / –) → primary action (Open in VS Code, or Copy `ตรวจโค้ด <ID> <QID>` once tests pass) → review history and explain question in collapsible sections → reference locked until review = pass.
- **Labs**: same as Programming; the horizontal stepper shows each milestone's name, with a filled emerald check once every layer passes.
