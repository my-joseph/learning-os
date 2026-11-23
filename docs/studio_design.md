# Practice Studio — design guide (v2, 2026-11-18)

The learner's brief: clean, few tags, easy to work a problem, no confusing buttons, no visual noise or text that does not help, a clear hierarchy, and colour and type chosen for ease of use. Every Studio PR follows this file.

## Principles
1. **The problem is the page.** The current question (prompt, figure, answer) gets the most space and the strongest type. Everything else is quieter.
2. **One primary action per state.** Exactly one filled button is visible at a time (icon-only `=` inside the field, Open in VS Code, Copy review request, Next problem/milestone). Other actions are text/ghost buttons or compact dialogs.
3. **Say less.** No decorative badges, IDs, chips or status pills unless the learner acts on them. Drill IDs and metadata live in the switcher, not on the card or in toasts/dialogs. Helper text appears only when it changes what the learner does next.
4. **Empathy.** Wrong answers get calm, specific feedback in a light-tinted result card and a retry — never saturated alarm colours. Copy is short, second person, never blaming ("Not quite — check the sign in step 2"), and uses the item noun of the workspace (`Question` for math, `Problem` for code drills, `Milestone` for labs).
5. **No answers before an attempt.** Hidden content is not rendered or fetched until it is earned (see rules/00_core.md §6).

## UI proof of concept
- The source-owned Radix + Tailwind primitives under `practice-studio/src/components/ui/shadcn/` are demonstrated at `/ui-poc`; keep showcase cards and their contents shrinkable and wrapped so the page has no horizontal overflow at 390 px.
- `Button` supports compact controls with 44 px mobile targets and 32 px desktop height, plus compact icon controls with 44 px mobile targets and 36 px desktop targets. Native buttons default to `type="button"`; `asChild` links keep their element semantics. Primary buttons use indigo-600 with white text in both themes for AA contrast.
- `Badge` supports default, secondary, outline, destructive, success, ghost, and layout-only `status` variants. Status badges use `statusTone` or `warningTone` recipes through caller classes; do not add raw status palette classes.
- Tabs keep rounded corners on segmented/contained switchers (`TabsList` `rounded-lg`, `TabsTrigger` and active pill `rounded-md`, including the Programming Drills/Labs switcher), while outline/underline tab strips (`variant="underline"`, including the Math similar-question strip) use square corners (`rounded-none`).

## Layout
- Edge-to-edge flat hairline 3-pane desktop layout (`>=1024 px`) separated by `1 px` `zinc-200` / `zinc-800` hairlines:
  - **Left Sidebar**: `287 px` wide when open, collapsing smoothly to `0 px` via the sidebar toggle (`PanelLeft`) or `Cmd/Ctrl+B` (below `1024 px` opens as a mobile left Drawer). Contains the icon-only `Σ` / `</>` `WorkspaceSwitch` (height-matched to `PanelLeft`) and the persistent searchable `DrillSwitcher` tree (`Drills | Labs`). Collapsing hides `MTH/PRG` along with the sidebar, leaving only the expand button and active drill title in the Top Bar.
  - **Top Bar**: one slim row — left-aligned `PanelLeft` expand trigger (when collapsed) and active drill title; right-aligned `+` Generate, Reset all, Notion link, Theme toggle, and Lucide `List` Right Panel toggle.
  - **Pagination / Stepper sub-bar**: compact `QuizPaginationBar` / `Stepper` (`24 px` desktop / `22 px` mobile circles `Q1`, `Q2`, … for drills and `M1`, `M2`, … for labs, `Review` trailing clipboard step, `44 px` minimum tap targets, horizontal scroll on `<640 px`) is retained beneath the header and hidden by default via `showPaginationBar = false`.
  - **Center problem canvas**: frameless ~720 px max-width centered column (`MathWorkspace` / `CodeDashboard`; `/review` keeps its framed card).
  - **Right Panel (`Due today & weak spots`)**: collapsible `276 px` pane on `>=1024 px`, persistent across both Quiz and Review views, collapsing into a right Drawer below `1024 px`.

## Colour (Tailwind tokens; light / dark)
- Neutral base & surfaces: `zinc` with `1 px` `zinc-200` / `zinc-800` hairlines, muted text `zinc-500` / `zinc-400`. Top Bar, Center problem canvas, Right Panel, Equation set-up, and dark inputs share `white` / `zinc-900` (`#18181b` dark `--background`; zero `dark:bg-zinc-950` in `src/`); Left Sidebar, Steps, and secondary panels use `--surface-panel` (`bg-surface-panel`: `#fafafa` light / `#202023` dark). Segmented switchers (`WorkspaceSwitch`, `DrillSwitcher`, `Math input | Plain text`) share sliding `<m.span>` pills; expanded Math Palette keycaps use high-contrast `white` / `zinc-700/70` against `bg-surface-panel`; equation rows (`MathBlock`, `StepRow`) suppress scrollbars while preserving horizontal overflow.
- One accent for the primary action: `indigo-600` (both light and dark, `>= 4.5:1`), text white.
- Typography (learner decision 2026-11-22): **Geist** / **Geist Fallback** for all UI and prompt text (`font-sans`, locally loaded from `GeistVF.woff`); **Roboto Slab** remains the secondary/display accent (`font-display`) for every non-code label or number that used to be mono — scores, Q1/Q2 labels, counts, timers, curriculum IDs (`MTH-…`, `PRG-…`, `DRL-…`); **Geist Mono** (`font-mono`) remains only for code (snippets, examples, tests, function names, typed code answers); KaTeX fonts remain for math.
- Lists: every bulleted list uses the shared `ListDot`, centred on the first text line; no "•" glyphs or `list-disc`. Three kinds, picked from the heading above the list (`listKindForHeading`): **task** = filled indigo dot (Requirements, Your task, rules, Visible tests); **info** = filled zinc dot (Observed symptoms, notes, review findings, any other heading); **limit** = hollow indigo ring (Return contract, Constraints, Input shape).
- Focus indicators: keyboard `focus-visible` indigo rings only (`indigo-600` light / `indigo-400` dark); suppress mouse-click focus rings and browser default outlines.
- Status only, never decoration: **no yellow/amber for any answer status** (learner decision 2026-11-19). Clean first-try `correct` uses emerald green; any non-clean eventually-correct or partial answer (`assisted`: correct with help, correct on retry / score 0.5, partial / `equivalent_not_in_form`, self-score 0.5, result card `"almost"`, Review & Sync `"Assisted / partial"`) uses green outline (no fill); `wrong` uses rose; `skipped` uses a dashed zinc outline; `notTried` and unanswered `usedHelp` use a plain outline (no colour). Amber is reserved exclusively for non-status operational warnings via `warningTone` (degraded sync banner, paused timer, pending/warning toasts, hint and weak-spot trap left-borders). Status colour appears on stepper circles, tab status icons, unrounded left borders, or light status tints on result cards and selected choice states — never as a left-accent border on rounded boxes or saturated full-card fills.
- Default theme syncs live with `prefers-color-scheme`; the toggle acts as a temporary override that yields when OS preference changes or when toggled back. Contrast AA (`>= 4.5:1`) everywhere.

## Colour tokens
- **Rule (enforced by `practice-studio/tests/statusTokens.test.tsx`):** never hard-code a status colour (`emerald-*`, `amber-*`, `yellow-*`, `rose-*`); import recipes from `practice-studio/src/lib/statusTone.ts` (`statusTone` for answer/progress status, `warningTone` for non-status warnings). Diagram/figure palettes (`Interactive*`, `MathFigure/*`, `VisualRenderer`, `VSCodeBlock`) are out of scope.
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
- Geist / Geist Fallback (`font-sans`) for UI and prose, Roboto Slab (`font-display`) for non-code labels and numbers, Geist Mono (`font-mono`) only for code, and KaTeX for math (learner decision 2026-11-22).
- Scale: question prompt `text-base` (16 px) / `leading-relaxed`; body `text-base`; secondary `text-sm text-zinc-500`. One `h1` per page (drill/lab title or not-found heading, `text-lg font-semibold`, 18 px). No uppercase/all-caps labels; at most two font weights on screen.

## Spacing and motion
- 8 px rhythm (`gap-2/4/6/8`), generous padding inside the question card (`p-6`, `p-4` on mobile).
- Status toasts stack bottom-right (`>=640 px`) / bottom-centre (`<640 px`).
- Calm ease-out `motion/react` (`m.*` under `<LazyMotion features={domAnimation} strict>` and `<MotionConfig reducedMotion="user">`) via `practice-studio/src/lib/motion.ts` and `<Reveal>` across overlays (`Dialog`, `AlertDialog`, `Drawer`, `Popover`, `Tooltip`, `HoverCard`), `Collapsible` disclosures, `MathWorkspace` tab switches, and tactile `Button` / `ChoiceOptionGroup` press states, while static containers, badges, and inputs stay calm without extra Motion wrappers; respect `prefers-reduced-motion`.

## Sidebar tree
- Sidebar curriculum rows at every tree level are exactly `32 px` high at all breakpoints; labels remain `14 px`. Use full Topic titles such as `Prealgebra` as top-level expandable folders, with Chapters, Units, and drills nested below. Keep branch titles neutral, and show the current leaf with a neutral selected background plus `aria-current`; its expanded ancestor path stays visible.
- The sidebar tree has no vertical guide borders, count backgrounds, or global Expand all / Collapse all / View toolbar. Keep per-folder chevrons and the sidebar shell collapse control. Programming keeps its Drills / Labs tabs.
- Each node has a trailing ellipsis action button, available on hover, keyboard focus, and touch. Its menu stays separate from row selection and expansion and offers Copy ID for the node's canonical ID. Workspace controls use accessible `Math` and `Programming` names and navigate to the matching available workspace route.
- `/sidebar-fixture` is a review-only interactive page backed by synthetic drill and lab rows; it does not read or write learner progress.

## Workspaces
- **Math**: similar-question tab strip at the top of the card (always shown when variants exist, with locked muted ghost tabs until the first substantive attempt on the real question in the current cycle) → prompt → figure → answer input with `=` inside the field → feedback → Hint / equation set-up / steps available before answering on both real and similar questions (revealing before an answer marks that item as used help). Self-score buttons only after an attempt on the real question.
- **Programming** (dashboard, no editor): brief → visible tests → status line `Tests  Lint  Types  Review` (✓ / ✗ / –) → primary action (Open in VS Code, or Copy `ตรวจโค้ด <ID> <QID>` once tests pass) → review history and explain question in collapsible sections → reference locked until review = pass.
- **Labs**: same as Programming; the horizontal stepper shows each milestone's name, with a filled emerald check once every layer passes.

## Scoring rule
One canonical rule drives every score, status, stepper circle, result card, Review & Sync row, and Notion mastery update (`practice-studio/src/lib/scoring.ts` in TypeScript and `progress_store.score_problem` in Python, locked in parity by `tests/fixtures/scoring_cases.json`). All scoring reads the **current cycle** (`cycleStartedAt`) only:

1. **Math / choice**: first substantive check correct with no help → `1` (`correct`, filled emerald). Correct after any wrong/partial check or after help (hint, equation set-up, steps/solution revealed before answering, worked example) → `0.5` (`assisted`, green outline). Partial / `equivalent_not_in_form` only → `0.5` (`assisted`) when partial credit `> 0`, else `0` (`wrong`). Wrong only → `0` (`wrong`, rose). Skipped → `0` (`skipped`, dashed zinc). No substantive attempt (including help opened without answering or input/parse errors) → `null` (`notTried`); input/parse errors render a neutral card, never green.
2. **Lock after correct**: once a check is correct in the current cycle, the answer input is read-only, Check is disabled, and later checks are ignored. Press **Reset** to start a new cycle (keeping history).
3. **Self-score**: may only **lower** the computed score (e.g., guessed `1 → 0.5` or `0`), or set a score when no automatic score exists. It never raises a wrong or skipped item and never clears `skipped`; outcome follows the final score.
4. **Mark diverged step**: a learning note only — it never changes a `null` score into `0.5` and never lowers a first-try `1`.
5. **PRG drills and labs**: all tests passing **and** latest review in the cycle is `pass` → `1` only on a clean first passing run with no hints and no earlier failing run or `revise` review in the cycle; otherwise `0.5`. Passing tests with no review yet → `score: null`, shown as **Awaiting review** consistently across stepper, tiles, rows, and summary. Failing tests or latest review `revise` → `0` (`wrong`).
6. **Similar questions**: scored with the exact same rule as the main question (wrong → correct is `0.5` `assisted`, locked after correct), while remaining isolated from the main score and review schedule.
