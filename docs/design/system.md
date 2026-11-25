# Practice Studio design system

Use the token roles below when adding a [component variant](components.md). Existing utility values and recipes are captured in the audit. Migrate a component by matching its current role and values in both themes. Get learner approval before introducing a colour.

## Using tokens

- The CSS custom properties live in `practice-studio/src/app/globals.css`. Tailwind keys below are under `theme.extend` in `practice-studio/tailwind.config.ts`. Values written once in CSS apply to both themes.
- Use semantic utilities such as `text-foreground`, `text-foreground-secondary`, `bg-surface-raised`, `border-border` and `bg-overlay-scrim`. RGB channel triples support Tailwind alpha modifiers. Scrim tokens include their existing alpha.
- Use `min-h-touch` and `min-w-touch` for the interactive target, with a smaller visual control when the pattern calls for it. Use `h-control-sm` for a 32 px compact row and `gap-space-2` for the 0.5 rem spacing step.
- Keep answer and warning states on the recipes in `practice-studio/src/lib/statusTone.ts`. Use shared Motion variants in `practice-studio/src/lib/motion.ts` for Motion components and the duration and easing utilities for CSS transitions. The existing Motion recipes express times in seconds. Media queries use literal breakpoints, mirrored by the screen tokens.
- Use Geist (`font-sans`, 400 or 600) for prompts, prose, controls, menus and labels. Use `tabular-nums` for counters, question labels and other numeric UI text smaller than 14 px.
- Reserve Roboto Slab (`font-heading`, 500 or 600, `tracking-heading`) for page titles, large section headings and empty-state titles at 18 px or larger, and prominent numerals at 14 px or larger. Use `Heading` and `Numeral` to apply these roles.
- Use Geist Mono (`font-mono`) for code, terminal output, function names, typed code answers and curriculum IDs such as `MTH-…`, `PRG-…`, `DRL-…` and `LAB-…`. KaTeX and MathLive keep their math fonts.

## Rendered prose

`FormattedText` uses the local shadcn Typeset port in `practice-studio/src/styles/typeset.css`. Body text and semibold content headings use `--font-sans`. Inline code uses `--font-mono`, `--surface-hover` and `--radius-base`. List markers use `--foreground-secondary`, and table rules use `--border-control`.

| Preset | `--typeset-size` | `--typeset-leading` | `--typeset-flow` |
| :--- | :--- | :--- | :--- |
| `.typeset-studio` | `--text-base` (15 px) | `--leading-relaxed` (1.625) | `--space-4` (16 px) |
| `.typeset-compact` | Inherited | `--leading-body` (1.6) | `--space-2` (8 px) |

Single-line labels inherit the surrounding size and line height. Compact prose inherits the size set by the surrounding card or panel.

## Token reference

### Colour

| CSS token | Tailwind group and key | Light | Dark | When to use |
| :--- | :--- | :--- | :--- | :--- |
| `--background` | `colors.background` | `#fafafa` | `#18181b` | Page canvas and inset focus-ring offsets. |
| `--foreground` | `colors.foreground` | `#18181b` | `#f4f4f5` | Default headings, body text and active controls. |
| `--foreground-secondary` | `colors.foreground-secondary` | `113 113 122` | `138 138 147` | Secondary labels using the existing contrast-tuned foreground. |
| `--surface-panel` | `colors.surface.panel` | `250 250 250` | `32 32 35` | Sidebar, steps and secondary panels. |
| `--muted` | `colors.muted` | `113 113 122` | `161 161 170` | Legacy muted labels where that exact light/dark pair is needed. |
| `--foreground-control` | `colors.foreground-control` | `63 63 70` | `212 212 216` | Neutral labels on sidebar controls. |
| `--foreground-menu` | `colors.foreground-menu` | `var(--foreground-control)` | `228 228 231` | Menu action labels. |
| `--foreground-answer` | `colors.foreground-answer` | `39 39 42` | `var(--foreground-menu)` | Answer fields, unselected choices and result actions. |
| `--foreground-answer-detail` | `colors.foreground-answer-detail` | `var(--foreground-control)` | `var(--foreground-control)` | Answer details, palette keys and quiet actions. |
| `--foreground-action-hover` | `colors.foreground-action-hover` | `9 9 11` | `244 244 245` | Hover text for a quiet result action. |
| `--accent-field` | `colors.accent-field` | `var(--accent-primary)` | `var(--accent-primary-hover)` | Selected choice and focused answer-field border. |
| `--accent-strong` | `colors.accent-strong` | `67 56 202` | `67 56 202` | Filled answer action hover in both themes. |
| `--accent-tint` | `colors.accent-tint` | `238 242 255` | `30 27 75` | Pressed or selected palette control background. |
| `--accent-on-primary-muted` | `colors.accent-on-primary-muted` | `224 231 255` | `224 231 255` | Secondary text on a filled action. |
| `--accent-current` | `colors.accent-current` | `var(--accent)` | `165 180 252` | Number on the current stepper marker. |
| `--foreground-faint` | `colors.foreground-faint` | `161 161 170` | `113 113 122` | Secondary tree glyphs and empty section labels. |
| `--foreground-section-hover` | `colors.foreground-section-hover` | `39 39 42` | `var(--foreground-menu)` | Section header label on hover. |
| `--foreground-subtle` | `colors.foreground-subtle` | `82 82 91` | `161 161 170` | Descriptions and supporting labels currently using zinc-600 and zinc-400. |
| `--border` | `colors.border` | `228 228 231` | `39 39 42` | Hairline dividers and card framing. |
| `--border-control` | `colors.border-control` | `212 212 216` | `63 63 70` | Form and outline-control borders. |
| `--surface-raised` | `colors.surface-raised` | `255 255 255` | `24 24 27` | White light-theme cards and input surfaces. |
| `--surface-hover` | `colors.surface-hover` | `244 244 245` | `39 39 42` | Quiet hover and neutral segmented backgrounds. |
| `--surface-hover-strong` | `colors.surface-hover-strong` | `var(--border-control)` | `82 82 91` | Hover highlight for an inset row action. |
| `--surface-selected` | `colors.surface-selected` | `228 228 231` | `63 63 70` | Selected search and sidebar controls using this neutral pair. |
| `--accent-primary` | `colors.accent-primary` | `79 70 229` | `79 70 229` | Filled primary action shared by both themes. |
| `--accent-primary-hover` | `colors.accent-primary-hover` | `67 56 202` | `99 102 241` | Hover for the filled primary action. |
| `--accent-on-primary` | `colors.accent-on-primary` | `255 255 255` | `255 255 255` | Text and icons on the filled primary action. |
| `--accent` | `colors.accent` | `79 70 229` | `129 140 248` | Brand accent, active step and accent focus ring. |
| `--status-correct` | `colors.status.correct` | `5 150 105` | `16 185 129` | Clean first-try correct fill. |
| `--status-correct-text` | `colors.status.correct-text` | `4 120 87` | `52 211 153` | Correct text, icons and accent borders. |
| `--status-correct-soft` | `colors.status.correct-soft` | `236 253 245` | `23 40 37` | Correct result tint. |
| `--status-on-correct` | `colors.status.on-correct` | `255 255 255` | `9 9 11` | Ink on the correct fill. |
| `--status-assisted` | `colors.status.assisted` | `5 150 105` | `16 185 129` | Assisted or partial outline. |
| `--status-assisted-soft` | `colors.status.assisted-soft` | `236 253 245` | `23 40 37` | Reserved assisted tint. |
| `--status-on-assisted` | `colors.status.on-assisted` | `4 120 87` | `52 211 153` | Assisted text and icons. |
| `--status-wrong` | `colors.status.wrong` | `225 29 72` | `251 113 133` | Wrong result or destructive action. |
| `--status-wrong-soft` | `colors.status.wrong-soft` | `255 241 242` | `46 28 34` | Wrong result or error tint. |
| `--status-on-wrong` | `colors.status.on-wrong` | `255 255 255` | `9 9 11` | Ink on the wrong fill. |
| `--status-skipped` | `colors.status.skipped` | `161 161 170` | `113 113 122` | Dashed skipped outline and active untried tab border. |
| `--status-neutral` | `colors.status.neutral` | `212 212 216` | `63 63 70` | Plain untried outline or dot. |
| `--warning` | `colors.warning` | `180 83 9` | `251 191 36` | Operational warning text and icons. |
| `--warning-soft` | `colors.warning.soft` | `255 251 235` | `46 37 22` | Operational warning tint. |
| `--warning-border` | `colors.warning.border` | `217 119 6` | `251 191 36` | Hint and trap accent borders. |
| `--overlay-scrim` | `colors.overlay-scrim` | `rgb(9 9 11 / 70%)` | `rgb(9 9 11 / 70%)` | Dialog, alert dialog and drawer scrims. |
| `--overlay-scrim-search` | `colors.overlay-scrim-search` | `rgb(0 0 0 / 40%)` | `rgb(0 0 0 / 50%)` | Search palette scrim. |

### Space and controls

| CSS token | Tailwind group and key | Light | Dark | When to use |
| :--- | :--- | :--- | :--- | :--- |
| `--space-0` | `spacing.space-0` | `0px` | `0px` | Use the matching step for padding, gaps, offsets and object sizes. |
| `--space-px` | `spacing.space-px` | `1px` | `1px` | Use the matching step for padding, gaps, offsets and object sizes. |
| `--space-0-5` | `spacing.space-0_5` | `0.125rem` | `0.125rem` | Use the matching step for padding, gaps, offsets and object sizes. |
| `--space-1` | `spacing.space-1` | `0.25rem` | `0.25rem` | Use the matching step for padding, gaps, offsets and object sizes. |
| `--space-1-5` | `spacing.space-1_5` | `0.375rem` | `0.375rem` | Use the matching step for padding, gaps, offsets and object sizes. |
| `--space-2` | `spacing.space-2` | `0.5rem` | `0.5rem` | Use the matching step for padding, gaps, offsets and object sizes. |
| `--space-2-5` | `spacing.space-2_5` | `0.625rem` | `0.625rem` | Use the matching step for padding, gaps, offsets and object sizes. |
| `--space-3` | `spacing.space-3` | `0.75rem` | `0.75rem` | Use the matching step for padding, gaps, offsets and object sizes. |
| `--space-3-5` | `spacing.space-3_5` | `0.875rem` | `0.875rem` | Use the matching step for padding, gaps, offsets and object sizes. |
| `--space-4` | `spacing.space-4` | `1rem` | `1rem` | Use the matching step for padding, gaps, offsets and object sizes. |
| `--space-5` | `spacing.space-5` | `1.25rem` | `1.25rem` | Use the matching step for padding, gaps, offsets and object sizes. |
| `--space-6` | `spacing.space-6` | `1.5rem` | `1.5rem` | Use the matching step for padding, gaps, offsets and object sizes. |
| `--space-7` | `spacing.space-7` | `1.75rem` | `1.75rem` | Use the matching step for padding, gaps, offsets and object sizes. |
| `--space-8` | `spacing.space-8` | `2rem` | `2rem` | Use the matching step for padding, gaps, offsets and object sizes. |
| `--space-9` | `spacing.space-9` | `2.25rem` | `2.25rem` | Use the matching step for padding, gaps, offsets and object sizes. |
| `--space-10` | `spacing.space-10` | `2.5rem` | `2.5rem` | Use the matching step for padding, gaps, offsets and object sizes. |
| `--space-11` | `spacing.space-11` | `2.75rem` | `2.75rem` | Use the matching step for padding, gaps, offsets and object sizes. |
| `--space-12` | `spacing.space-12` | `3rem` | `3rem` | Use the matching step for padding, gaps, offsets and object sizes. |
| `--space-14` | `spacing.space-14` | `3.5rem` | `3.5rem` | Use the matching step for padding, gaps, offsets and object sizes. |
| `--space-16` | `spacing.space-16` | `4rem` | `4rem` | Use the matching step for padding, gaps, offsets and object sizes. |
| `--space-20` | `spacing.space-20` | `5rem` | `5rem` | Use the matching step for padding, gaps, offsets and object sizes. |
| `--space-24` | `spacing.space-24` | `6rem` | `6rem` | Use the matching step for padding, gaps, offsets and object sizes. |
| `--space-28` | `spacing.space-28` | `7rem` | `7rem` | Minimum height for the Search results area. |
| `--space-40` | `spacing.space-40` | `10rem` | `10rem` | Use the matching step for padding, gaps, offsets and object sizes. |
| `--space-52` | `spacing.space-52` | `13rem` | `13rem` | Use the matching step for padding, gaps, offsets and object sizes. |
| `--control-xs` | `spacing.control-xs` | `28px` | `28px` | Compact filter chips and desktop search close control. |
| `--control-sm` | `spacing.control-sm` | `32px` | `32px` | Sidebar rows and compact desktop controls. |
| `--control-md` | `spacing.control-md` | `36px` | `36px` | Desktop action icons and roomy search result rows. |
| `--tree-depth-3` | `spacing.tree-depth-3` | `calc(var(--space-4) + var(--space-2-5))` | `calc(var(--space-4) + var(--space-2-5))` | Content inset at the third depth of a tree row. |
| `--touch` | `spacing.touch` | `44px` | `44px` | Minimum touch targets. |
| `--control-answer` | `spacing.control-answer` | `calc(var(--touch) + 2 * var(--space-px))` | `calc(var(--touch) + 2 * var(--space-px))` | Mobile answer field including the two hairlines. |
| `--icon-math-quick` | `spacing.icon-math-quick` | `22px` | `22px` | Quick math template glyph height. |
| `--icon-math-quick-max` | `spacing.icon-math-quick-max` | `26px` | `26px` | Maximum width of a quick math template glyph. |
| `--stepper-marker` | `spacing.stepper-marker` | `22px` | `22px` | Regular stepper marker on phones. |
| `--stepper-marker-compact` | `spacing.stepper-marker-compact` | `18px` | `18px` | Compact stepper marker on phones. |
| `--panel-left` | `spacing.panel-left` | `287px` | `287px` | Open desktop navigation pane. |
| `--panel-right` | `spacing.panel-right` | `276px` | `276px` | Open desktop review pane. |
| `--control-lg` | `spacing.control-lg` | `48px` | `48px` | Large buttons. |
| `--width-search` | `maxWidth.search` | `671px` | `671px` | Search palette maximum width. |
| `--height-search` | `maxHeight.search` | `40rem` | `40rem` | Search palette maximum height, capped by the available space. |
| `--width-picker` | `maxWidth.picker` | `460px` | `460px` | Drill picker dropdown maximum width. |
| `--height-picker` | `maxHeight.picker` | `72vh` | `72vh` | Drill picker dropdown maximum height. |
| `--width-picker-title-sm` | `maxWidth.picker-title-sm` | `220px` | `220px` | Base width limit for the drill picker trigger title. |
| `--width-picker-title-md` | `maxWidth.picker-title-md` | `300px` | `300px` | Drill picker trigger title width limit from the `sm` breakpoint. |
| `--width-picker-title-lg` | `maxWidth.picker-title-lg` | `360px` | `360px` | Drill picker trigger title width limit from the `md` breakpoint. |
| `--width-practice` | `maxWidth.practice` | `720px` | `720px` | Centered practice and review canvas. |

### Type

| CSS token | Tailwind group and key | Light | Dark | When to use |
| :--- | :--- | :--- | :--- | :--- |
| `--font-sans` | `fontFamily.sans` | `var(--font-geist-sans), "Geist", "Geist Fallback", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif` | `var(--font-geist-sans), "Geist", "Geist Fallback", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif` | UI text, prompts, prose and small numerals. |
| `--font-heading` | `fontFamily.heading` | `"Roboto Slab Variable", "Roboto Slab", Georgia, serif` | `"Roboto Slab Variable", "Roboto Slab", Georgia, serif` | Prominent headings and numerals. |
| `--font-mono` | `fontFamily.mono` | `var(--font-geist-mono), ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace` | `var(--font-geist-mono), ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace` | Code, terminals, typed code answers and curriculum IDs. |
| `--text-2xs` | `fontSize.2xs` | `11px` | `11px` | Compact metadata and secondary chips. |
| `--text-micro` | `fontSize.micro` | `10px` | `10px` | Stepper numerals and compact labels. |
| `--text-micro-compact` | `fontSize.micro-compact` | `9px` | `9px` | Compact stepper numerals on phones. |
| `--text-caption` | `fontSize.caption` | `13px` | `13px` | Compact link and helper copy where the 13 px size is already used. |
| `--text-xs` | `fontSize.xs` | `0.75rem` | `0.75rem` | Metadata, badges and compact labels. |
| `--text-xs-leading` | `fontSize.xs (line height)` | `1rem` | `1rem` | Default line height paired with text-xs. |
| `--text-sm` | `fontSize.sm` | `0.875rem` | `0.875rem` | Secondary text and controls. |
| `--text-sm-leading` | `fontSize.sm (line height)` | `1.25rem` | `1.25rem` | Default line height paired with text-sm. |
| `--text-base` | `fontSize.base` | `0.9375rem` | `0.9375rem` | Body and question text. |
| `--text-base-leading` | `fontSize.base (line height)` | `1.5rem` | `1.5rem` | Default line height paired with text-base. |
| `--text-lg` | `fontSize.lg` | `1.125rem` | `1.125rem` | Page and dialog titles. |
| `--text-lg-leading` | `fontSize.lg (line height)` | `1.75rem` | `1.75rem` | Default line height paired with text-lg. |
| `--text-3xl` | `fontSize.3xl` | `1.875rem` | `1.875rem` | Showcase heading. |
| `--text-3xl-leading` | `fontSize.3xl (line height)` | `2.25rem` | `2.25rem` | Default line height paired with text-3xl. |
| `--text-4xl` | `fontSize.4xl` | `2.25rem` | `2.25rem` | Showcase heading at wider widths. |
| `--text-4xl-leading` | `fontSize.4xl (line height)` | `2.5rem` | `2.5rem` | Default line height paired with text-4xl. |
| `--weight-normal` | `fontWeight.normal` | `400` | `400` | Regular Geist and Geist Mono text. |
| `--weight-heading-medium` | `fontWeight.heading-medium` | `500` | `500` | Roboto Slab section headings. |
| `--weight-semibold` | `fontWeight.semibold` | `600` | `600` | Emphasized Geist text, page headings and prominent numerals. |
| `--tracking-heading` | `letterSpacing.heading` | `-0.01em` | `-0.01em` | Roboto Slab headings and prominent numerals. |
| `--leading-none` | `lineHeight.none` | `1` | `1` | Use for the matching line spacing. |
| `--leading-tight` | `lineHeight.tight` | `1.25` | `1.25` | Use for the matching line spacing. |
| `--leading-snug` | `lineHeight.snug` | `1.375` | `1.375` | Use for the matching line spacing. |
| `--leading-relaxed` | `lineHeight.relaxed` | `1.625` | `1.625` | Use for the matching line spacing. |
| `--leading-body` | `lineHeight.body` | `1.6` | `1.6` | Global body line height. |

### Edges and elevation

| CSS token | Tailwind group and key | Light | Dark | When to use |
| :--- | :--- | :--- | :--- | :--- |
| `--radius-indicator` | `borderRadius.indicator` | `3px` | `3px` | Compact review result marker. |
| `--radius-answer-action` | `borderRadius.answer-action` | `11px` | `11px` | Mobile plain-answer check button. |
| `--radius-none` | `borderRadius.none` | `0px` | `0px` | Square tabs and flush edges. |
| `--radius-sm` | `borderRadius.sm` | `0.125rem` | `0.125rem` | Small marks. |
| `--radius-base` | `borderRadius.DEFAULT` | `0.25rem` | `0.25rem` | Compact inline marks and controls. |
| `--radius-md` | `borderRadius.md` | `0.375rem` | `0.375rem` | Controls, sidebar rows and tab pills. |
| `--radius-lg` | `borderRadius.lg` | `0.5rem` | `0.5rem` | Segmented lists and small overlays. |
| `--radius-xl` | `borderRadius.xl` | `0.75rem` | `0.75rem` | Dialogs and larger controls. |
| `--radius-2xl` | `borderRadius.2xl` | `1rem` | `1rem` | Cards and drawers. |
| `--radius-full` | `borderRadius.full` | `9999px` | `9999px` | Round indicators and fully rounded badges. |
| `--border-width-0` | `borderWidth.0` | `0px` | `0px` | Borderless state. |
| `--border-width-hairline` | `borderWidth.DEFAULT` | `1px` | `1px` | Hairline border. |
| `--border-width-2` | `borderWidth.2` / `ringWidth.2` | `2px` | `2px` | Underline, accent border, and focus ring. |
| `--border-width-status` | `borderWidth.status` / `ringWidth.status` | `1.5px` | `1.5px` | Fine status outline. |
| `--shadow-none` | `boxShadow.ui-none` | `0 0 #0000` | `0 0 #0000` | Explicit flat surfaces. |
| `--shadow-sm` | `boxShadow.ui-sm` | `0 1px 2px 0 rgb(0 0 0 / 0.05)` | `0 1px 2px 0 rgb(0 0 0 / 0.05)` | Cards and subtle active states. |
| `--shadow-md` | `boxShadow.ui-md` | `0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)` | `0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)` | Tooltips and hover cards. |
| `--shadow-lg` | `boxShadow.ui-lg` | `0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)` | `0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)` | Popovers and menus. |
| `--shadow-xl` | `boxShadow.ui-xl` | `0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)` | `0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)` | Dialogs and drawers. |
| `--shadow-inner` | `boxShadow.ui-inner` | `inset 0 2px 4px 0 rgb(0 0 0 / 0.05)` | `inset 0 2px 4px 0 rgb(0 0 0 / 0.05)` | Inset fields and wells. |
| `--blur-scrim` | `backdropBlur.scrim` | `2px` | `2px` | Thin backdrop blur on figure labels. |
| `--blur-glass` | `backdropBlur.glass` | `12px` | `12px` | Translucent review header and panel backdrop. |
| `--opacity-hidden` | `opacity.hidden` | `0` | `0` | Hidden affordance. |
| `--opacity-quiet` | `opacity.quiet` | `0.3` | `0.3` | Quiet affordance. |
| `--opacity-subtle` | `opacity.subtle` | `0.4` | `0.4` | Muted affordance. |
| `--opacity-step-dim` | `opacity.step-dim` | `0.45` | `0.45` | Dim siblings of a hovered step. |
| `--opacity-disabled` | `opacity.disabled` | `0.5` | `0.5` | Disabled controls. |
| `--opacity-secondary` | `opacity.secondary` | `0.6` | `0.6` | Secondary metadata. |
| `--opacity-soft` | `opacity.soft` | `0.7` | `0.7` | Low-emphasis hint or icon. |
| `--opacity-muted` | `opacity.muted` | `0.75` | `0.75` | Muted helper text. |
| `--opacity-hover` | `opacity.hover` | `0.8` | `0.8` | Quiet hover feedback. |
| `--opacity-visible` | `opacity.visible` | `1` | `1` | Fully visible affordance. |

### Motion and layers

| CSS token | Tailwind group and key | Light | Dark | When to use |
| :--- | :--- | :--- | :--- | :--- |
| `--duration-reduced` | `transitionDuration.reduced` | `0.01ms` | `0.01ms` | Reduced-motion CSS override. |
| `--duration-tab-exit` | `transitionDuration.tab-exit` | `100ms` | `100ms` | Tab panel exit. |
| `--duration-popover-exit` | `transitionDuration.popover-exit` | `120ms` | `120ms` | Menus, tooltip entry and sidebar exit. |
| `--duration-modal-exit` | `transitionDuration.modal-exit` | `140ms` | `140ms` | Dialog and toast exit. |
| `--duration-color` | `transitionDuration.color` | `150ms` | `150ms` | Tailwind default and body colour transitions. |
| `--duration-quick` | `transitionDuration.quick` | `160ms` | `160ms` | Press, entry and disclosure exit. |
| `--duration-panel` | `transitionDuration.panel` | `200ms` | `200ms` | Overlay fades, drawer exits and layout transitions. |
| `--duration-reveal` | `transitionDuration.reveal` | `220ms` | `220ms` | Disclosure entry. |
| `--duration-settle` | `transitionDuration.settle` | `240ms` | `240ms` | Workspace transitions and mobile drawer entry. |
| `--duration-drawer` | `transitionDuration.drawer` | `260ms` | `260ms` | Right desktop drawer entry. |
| `--duration-tooltip-delay` | `transitionDuration.tooltip-delay` | `300ms` | `300ms` | Default waiting time before tooltip opens. |
| `--ease-settle` | `transitionTimingFunction.settle` | `cubic-bezier(0.16, 1, 0.3, 1)` | `cubic-bezier(0.16, 1, 0.3, 1)` | Shared Motion ease-out curve. |
| `--ease-standard` | `transitionTimingFunction.standard` | `cubic-bezier(0.4, 0, 0.2, 1)` | `cubic-bezier(0.4, 0, 0.2, 1)` | Tailwind default easing. |
| `--ease-out` | `transitionTimingFunction.out` | `cubic-bezier(0, 0, 0.2, 1)` | `cubic-bezier(0, 0, 0.2, 1)` | Tailwind ease-out. |
| `--ease-theme` | `transitionTimingFunction.theme` | `ease` | `ease` | Body colour transition easing. |
| `--z-base` | `zIndex.base` | `0` | `0` | Local stacking baseline. |
| `--z-local` | `zIndex.local` | `10` | `10` | Floating controls and local headers. |
| `--z-sticky` | `zIndex.sticky` | `40` | `40` | Sticky shell and progress UI. |
| `--z-overlay` | `zIndex.overlay` | `50` | `50` | Root overlays and popovers. |
| `--z-overlay-menu` | `zIndex.overlay-menu` | `55` | `55` | Menu inside search overlay. |
| `--z-tooltip` | `zIndex.tooltip` | `60` | `60` | Tooltips and sidebar menus above overlays. |

### Breakpoints

| CSS token | Tailwind group and key | Light | Dark | When to use |
| :--- | :--- | :--- | :--- | :--- |
| `--screen-sm` | `screens.sm` | `640px` | `640px` | Compact desktop controls and wider layouts. |
| `--screen-md` | `screens.md` | `768px` | `768px` | Drawer side layout and intermediate grids. |
| `--screen-lg` | `screens.lg` | `1024px` | `1024px` | Desktop sidebar and right panel. |

## Source audit at the foundation baseline

The inventory scans authored code and CSS under `practice-studio/src`, including component recipes, responsive and state utilities, figure and MathLive styling, and the values from generated Tailwind rules that those sources use. Counts are source occurrences. Shared recipes count where defined. One utility can contribute to multiple rows. Units and token references are shown as authored or emitted. Third-party stylesheets and runtime values from drill data or rendering libraries are outside the source inventory.

| Category | Existing values × source occurrences |
| :--- | :--- |
| Colour | `#000000` × 3, `#3f3f46` × 18, `#4f46e5` × 15, `#27c93f` × 1, `#34d399` × 22, `#818cf8` × 31, `#3178c6` × 3, `#3730a3` × 3, `#3776ab` × 1, `#6366f1` × 3 |
|  | `#09090b` × 26, `#18181b` × 23, `#24292e` × 1, `#27272a` × 22, `#047857` × 5, `#52525b` × 2, `#059669` × 1, `#71717a` × 4, `#a1a1aa` × 24, `#a5b4fc` × 2 |
|  | `#b45309` × 6, `#d4d4d8` × 3, `#d97706` × 3, `#e1e4e8` × 1, `#e4e4e7` × 22, `#f4f4f5` × 20, `#f7df1e` × 2, `#fafafa` × 1, `#fbbf24` × 24, `#ff5f56` × 1 |
|  | `#ffbd2e` × 1, `#fff` × 28, `239` × 2, `defaultColor: currentColor` × 1, `fill: currentColor` × 27, `fill: none` × 20, `fill: transparent` × 7, `rgb(0 0 0 / 0.4)` × 1, `rgb(0 0 0 / 0.5)` × 17, `rgb(0 0 0 / 1)` × 2 |
|  | `rgb(2 44 34 / 0.7)` × 1, `rgb(4 120 87 / 1)` × 21, `rgb(5 150 105 / 1)` × 7, `rgb(6 95 70 / 0.5)` × 1, `rgb(9 9 11 / 0.7)` × 3, `rgb(9 9 11 / 0.85)` × 1, `rgb(9 9 11 / 1)` × 19, `rgb(16 185 129 / 0.1)` × 1, `rgb(16 185 129 / 0.2)` × 2, `rgb(16 185 129 / 0.05)` × 1 |
|  | `rgb(16 185 129 / 0.15)` × 1, `rgb(16 185 129 / 0.25)` × 1, `rgb(16 185 129 / 1)` × 1, `rgb(24 24 27 / 0.5)` × 17, `rgb(24 24 27 / 0.6)` × 19, `rgb(24 24 27 / 0.7)` × 17, `rgb(24 24 27 / 0.8)` × 18, `rgb(24 24 27 / 0.75)` × 18, `rgb(24 24 27 / 0.85)` × 17, `rgb(24 24 27 / 0.95)` × 17 |
|  | `rgb(24 24 27 / 1)` × 251, `rgb(30 27 75 / 0.5)` × 17, `rgb(30 27 75 / 0.6)` × 19, `rgb(30 27 75 / 0.7)` × 2, `rgb(30 27 75 / 0.25)` × 17, `rgb(36 41 46 / 1)` × 1, `rgb(39 39 42 / 0.4)` × 17, `rgb(39 39 42 / 0.5)` × 18, `rgb(39 39 42 / 0.6)` × 20, `rgb(39 39 42 / 0.7)` × 22 |
|  | `rgb(39 39 42 / 0.8)` × 29, `rgb(39 39 42 / 1)` × 234, `rgb(39 201 63 / 1)` × 1, `rgb(49 120 198 / 1)` × 3, `rgb(52 211 153 / 0.6)` × 17, `rgb(52 211 153 / 1)` × 43, `rgb(55 48 163 / 0.5)` × 2, `rgb(55 118 171 / 1)` × 1, `rgb(63 63 70 / 0.4)` × 22, `rgb(63 63 70 / 0.5)` × 18 |
|  | `rgb(63 63 70 / 0.6)` × 21, `rgb(63 63 70 / 0.7)` × 19, `rgb(63 63 70 / 0.8)` × 19, `rgb(63 63 70 / 1)` × 147, `rgb(67 56 202 / 1)` × 50, `rgb(69 26 3 / 0.4)` × 1, `rgb(69 26 3 / 0.8)` × 17, `rgb(79 70 229 / 0.2)` × 5, `rgb(79 70 229 / 0.5)` × 2, `rgb(79 70 229 / 0.7)` × 1 |
|  | `rgb(79 70 229 / 0.15)` × 1, `rgb(79 70 229 / 0.25)` × 3, `rgb(79 70 229 / 1)` × 235, `rgb(82 82 91 / 0.6)` × 18, `rgb(82 82 91 / 0.7)` × 17, `rgb(82 82 91 / 1)` × 90, `rgb(99 102 241 / 0.1)` × 25, `rgb(99 102 241 / 0.2)` × 2, `rgb(99 102 241 / 0.4)` × 2, `rgb(99 102 241 / 0.5)` × 2 |
|  | `rgb(99 102 241 / 0.05)` × 1, `rgb(99 102 241 / 0.7)` × 3, `rgb(99 102 241 / 0.15)` × 19, `rgb(99 102 241 / 0.25)` × 21, `rgb(99 102 241 / 1)` × 36, `rgb(113 113 122 / 1)` × 271, `rgb(129 140 248 / 0.4)` × 17, `rgb(129 140 248 / 0.5)` × 17, `rgb(129 140 248 / 0.6)` × 19, `rgb(129 140 248 / 0.7)` × 20 |
|  | `rgb(129 140 248 / 0.25)` × 21, `rgb(129 140 248 / 0.35)` × 19, `rgb(129 140 248 / 1)` × 176, `rgb(161 161 170 / 1)` × 341, `rgb(165 180 252 / 1)` × 20, `rgb(180 83 9 / 0.6)` × 17, `rgb(180 83 9 / 1)` × 23, `rgb(212 212 216 / 0.7)` × 2, `rgb(212 212 216 / 1)` × 134, `rgb(217 119 6 / 0.3)` × 1 |
|  | `rgb(217 119 6 / 1)` × 1, `rgb(224 231 255 / 0.8)` × 1, `rgb(225 29 72 / 1)` × 2, `rgb(225 228 232 / 1)` × 17, `rgb(228 228 231 / 0.5)` × 5, `rgb(228 228 231 / 0.6)` × 9, `rgb(228 228 231 / 0.7)` × 8, `rgb(228 228 231 / 0.8)` × 8, `rgb(228 228 231 / 0.9)` × 2, `rgb(228 228 231 / 1)` × 203 |
|  | `rgb(238 242 255 / 0.7)` × 2, `rgb(238 242 255 / 0.9)` × 1, `rgb(238 242 255 / 1)` × 6, `rgb(244 244 245 / 0.7)` × 1, `rgb(244 244 245 / 0.8)` × 4, `rgb(244 244 245 / 0.95)` × 1, `rgb(244 244 245 / 1)` × 242, `rgb(245 158 11 / 0.1)` × 1, `rgb(245 158 11 / 1)` × 1, `rgb(247 223 30 / 1)` × 2 |
|  | `rgb(250 250 250 / 0.7)` × 1, `rgb(250 250 250 / 0.8)` × 1, `rgb(250 250 250 / 1)` × 15, `rgb(251 113 133 / 1)` × 18, `rgb(251 191 36 / 1)` × 39, `rgb(252 211 77 / 1)` × 18, `rgb(254 243 199 / 0.9)` × 1, `rgb(255 95 86 / 1)` × 1, `rgb(255 189 46 / 1)` × 1, `rgb(255 255 255 / 0.7)` × 2 |
|  | `rgb(255 255 255 / 0.8)` × 2, `rgb(255 255 255 / 0.9)` × 2, `rgb(255 255 255 / 0.85)` × 1, `rgb(255 255 255 / 0.95)` × 1, `rgb(255 255 255 / 1)` × 124, `rgb(var(--accent) / 1)` × 25, `rgb(var(--foreground-secondary) / 1)` × 1, `rgb(var(--status-assisted) / 0.1)` × 25, `rgb(var(--status-assisted) / 0.5)` × 1, `rgb(var(--status-assisted) / 1)` × 12 |
|  | `rgb(var(--status-correct-soft) / 1)` × 2, `rgb(var(--status-correct-text) / 1)` × 5, `rgb(var(--status-correct) / 0.6)` × 1, `rgb(var(--status-correct) / 0.15)` × 1, `rgb(var(--status-correct) / 0.25)` × 1, `rgb(var(--status-correct) / 1)` × 7, `rgb(var(--status-neutral) / 1)` × 3, `rgb(var(--status-on-assisted) / 1)` × 3, `rgb(var(--status-on-correct) / 1)` × 4, `rgb(var(--status-on-wrong) / 1)` × 5 |
|  | `rgb(var(--status-skipped) / 1)` × 5, `rgb(var(--status-wrong-soft) / 1)` × 2, `rgb(var(--status-wrong) / 0.4)` × 2, `rgb(var(--status-wrong) / 0.6)` × 1, `rgb(var(--status-wrong) / 0.15)` × 1, `rgb(var(--status-wrong) / 0.25)` × 1, `rgb(var(--status-wrong) / 1)` × 14, `rgb(var(--surface-panel) / 0.6)` × 1, `rgb(var(--surface-panel) / 0.7)` × 2, `rgb(var(--surface-panel) / 0.8)` × 18 |
|  | `rgb(var(--surface-panel) / 1)` × 65, `rgb(var(--warning-border) / 0.7)` × 1, `rgb(var(--warning-border) / 1)` × 1, `rgb(var(--warning-soft) / 1)` × 1, `rgb(var(--warning) / 0.25)` × 2, `rgb(var(--warning) / 1)` × 2, `rgba(99, 102, 241, 0.08)` × 1, `rgba(99, 102, 241, 0.12)` × 1, `rgba(99, 102, 241, 0.16)` × 1, `rgba(99, 102, 241, 0.18)` × 1 |
|  | `rgba(99, 102, 241, 0.22)` × 1, `rgba(99, 102, 241, 0.28)` × 1, `rgba(245, 158, 11, 0.25)` × 1, `rgba(250, 204, 21, 0.3)` × 1, `rgba(250, 204, 21, 0.4)` × 1, `stroke: currentColor` × 45, `stroke: none` × 4, `stroke: transparent` × 7, `strokeColor: currentColor` × 2, `transparent` × 56 |
|  | `var(--background)` × 24, `var(--foreground)` × 44, `var(--shiki-dark)` × 1, `var(--shiki-light)` × 1 |
| Spacing and size | `-0.5rem` × 1, `-0.25rem` × 1, `-0.125rem` × 1, `-0.375rem` × 1, `-0.625rem` × 3, `-1px` × 17, `-1rem` × 1, `-50%` × 5, `0` × 14, `0.5rem` × 197 |
|  | `0.25rem` × 158, `0.35em 0` × 1, `0.75rem` × 147, `0.125rem` × 85, `0.375rem` × 125, `0.625rem` × 102, `0.875rem` × 198, `0px` × 249, `1.5rem` × 36, `1.25rem` × 28 |
|  | `1.75rem` × 19, `1lh` × 1, `1px` × 16, `1rem` × 240, `2.5rem` × 29, `2.25rem` × 15, `2.75rem` × 35, `2px 2px` × 1, `2px 4px` × 1, `2rem` × 47 |
|  | `3.5rem` × 1, `3rem` × 11, `4rem` × 3, `5rem` × 3, `6rem` × 1, `7px` × 2, `7rem` × 1, `8rem` × 1, `10rem` × 2, `12px` × 1 |
|  | `13px` × 1, `13rem` × 1, `15px` × 1, `16rem` × 1, `18px` × 2, `18rem` × 1, `20rem` × 1, `22px` × 3, `24px` × 1, `24rem` × 3 |
|  | `25%` × 1, `26px` × 3, `28px` × 8, `28rem` × 2, `30px` × 1, `32px` × 12, `32rem` × 2, `33.333333%` × 3, `34px` × 1, `36px` × 15 |
|  | `40px` × 1, `42rem` × 1, `44px` × 148, `46px` × 1, `48px` × 4, `50%` × 6, `56px` × 1, `64rem` × 1, `66.666667%` × 4, `72px` × 2 |
|  | `72vh` × 1, `75%` × 1, `85vh` × 1, `100%` × 139, `100dvh` × 1, `100vh` × 6, `100vw` × 1, `160px` × 1, `220px` × 1, `240px` × 1 |
|  | `276px` × 1, `280px` × 1, `287px` × 1, `300px` × 1, `360px` × 1, `400px` × 3, `460px` × 1, `671px` × 1, `720px` × 5, `auto` × 34 |
|  | `calc(0.5rem * calc(1 - var(--tw-space-y-reverse)))` × 11, `calc(0.5rem * var(--tw-space-y-reverse))` × 11, `calc(0.25rem * calc(1 - var(--tw-space-y-reverse)))` × 17, `calc(0.25rem * var(--tw-space-y-reverse))` × 17, `calc(0.75rem * calc(1 - var(--tw-space-y-reverse)))` × 24, `calc(0.75rem * var(--tw-space-y-reverse))` × 24, `calc(0.125rem * calc(1 - var(--tw-space-y-reverse)))` × 15, `calc(0.125rem * var(--tw-space-y-reverse))` × 15, `calc(0.375rem * calc(1 - var(--tw-space-y-reverse)))` × 17, `calc(0.375rem * var(--tw-space-y-reverse))` × 17 |
|  | `calc(0.625rem * calc(1 - var(--tw-space-y-reverse)))` × 14, `calc(0.625rem * var(--tw-space-y-reverse))` × 14, `calc(1.5rem * calc(1 - var(--tw-space-y-reverse)))` × 9, `calc(1.5rem * var(--tw-space-y-reverse))` × 9, `calc(1.25rem * calc(1 - var(--tw-space-y-reverse)))` × 2, `calc(1.25rem * var(--tw-space-y-reverse))` × 2, `calc(1rem * calc(1 - var(--tw-space-y-reverse)))` × 18, `calc(1rem * var(--tw-space-y-reverse))` × 18, `calc(50% - 2px)` × 4, `calc(50% - 4px)` × 1 |
|  | `calc(50% + 13px)` × 1, `calc(50% + 14px)` × 1, `calc(50% + 15px)` × 1, `calc(50% + 18px)` × 1, `calc(100% - 28px)` × 1, `calc(100% - 36px)` × 1, `height: 0` × 2, `height: 14` × 1, `height: 24` × 1, `height: 26` × 1 |
|  | `height: 28` × 3, `height: 30` × 1, `height: 140%` × 4, `height: 200` × 1, `height: auto` × 2, `maxHeight: 240px` × 2, `maxHeight: 250px` × 1, `maxHeight: 380px` × 3, `none` × 2, `size: 4.5` × 1 |
|  | `size: 5` × 1, `size: 5.5` × 3, `size: 5.25` × 1, `size: 6.5` × 10, `size: 7` × 3, `size: 7.5` × 5, `size: 8` × 2, `width: 0` × 4, `width: 14` × 1, `width: 24` × 1 |
|  | `width: 27` × 2, `width: 28` × 4, `width: 29` × 1, `width: 34` × 1, `width: 70` × 2, `width: 110` × 2, `width: 120` × 1, `width: 140%` × 4, `width: 276` × 1, `width: 287` × 1 |
|  | `width: 320` × 1, `width: auto` × 1, `x: -6` × 2, `x: -100%` × 1, `x: 0` × 3, `x: 100%` × 1, `y: -2` × 1, `y: -4` × 1, `y: 0` × 6, `y: 2` × 1 |
|  | `y: 4` × 1, `y: 6` × 1, `y: 8` × 1, `y: 100%` × 1 |
| Font family | `fontFamily: KaTeX_Main, 'Times New Roman', serif` × 1, `fontFamily: KaTeX_Math, 'Times New Roman', serif` × 1, `var(--font-heading)` × 3, `var(--font-mono)` × 28, `var(--font-sans)` × 102 |
| Font size | `0.85em` × 1, `0.88em` × 3, `10px` × 8, `11px` × 7, `13px` × 2, `1rem` × 1, `fontSize: 0.32` × 1, `fontSize: 0.35` × 1, `fontSize: 11.5` × 1, `fontSize: 11px` × 3 |
|  | `fontSize: 12` × 5, `fontSize: 13` × 1, `fontSize: 6.25` × 1, `fontSize: 7` × 1, `fontSize: 8` × 1, `fontSize: 9` × 1, `fontSize: 9.5` × 4, `var(--text-2xs)` × 14, `var(--text-3xl)` × 1, `var(--text-4xl)` × 1 |
|  | `var(--text-base)` × 12, `var(--text-lg)` × 5, `var(--text-micro)` × 4, `var(--text-micro-compact)` × 2, `var(--text-sm)` × 110, `var(--text-xs)` × 199 |
| Font weight | `fontWeight: 500` × 1, `var(--shiki-dark-font-weight, inherit)` × 1, `var(--shiki-light-font-weight, inherit)` × 1, `var(--weight-heading-medium)` × 2, `var(--weight-normal)` × 86, `var(--weight-semibold)` × 121 |
| Line height | `1.4` × 1, `var(--leading-body)` × 1, `var(--leading-none)` × 9, `var(--leading-relaxed)` × 28, `var(--leading-snug)` × 9, `var(--leading-tight)` × 2, `var(--text-3xl-leading)` × 1, `var(--text-4xl-leading)` × 1, `var(--text-base-leading)` × 12, `var(--text-lg-leading)` × 5 |
|  | `var(--text-sm-leading)` × 110, `var(--text-xs-leading)` × 199 |
| Radius | `3px` × 1, `11px` × 1, `var(--radius-2xl)` × 15, `var(--radius-base)` × 35, `var(--radius-full)` × 38, `var(--radius-lg)` × 67, `var(--radius-md)` × 55, `var(--radius-none)` × 8, `var(--radius-sm)` × 3, `var(--radius-xl)` × 85 |
| Border and stroke width | `0` × 14, `1.5px` × 8, `1px` × 6, `2px` × 194, `4px` × 1, `calc(var(--border-width-hairline) * calc(1 - var(--tw-divide-y-reverse)))` × 6, `calc(var(--border-width-hairline) * var(--tw-divide-y-reverse))` × 6, `strokeWidth: 0.8` × 3, `strokeWidth: 1` × 2, `strokeWidth: 1.2` × 5 |
|  | `strokeWidth: 1.3` × 1, `strokeWidth: 1.4` × 1, `strokeWidth: 1.5` × 10, `strokeWidth: 1.6` × 2, `strokeWidth: 1.8` × 3, `strokeWidth: 1.25` × 6, `strokeWidth: 2` × 19, `strokeWidth: 2.2` × 1, `strokeWidth: 2.4` × 2, `strokeWidth: 2.5` × 8 |
|  | `strokeWidth: 3` × 8, `strokeWidth: 3.5` × 6, `strokeWidth: 4.5` × 1, `strokeWidth: 5` × 5, `strokeWidth: 24` × 7, `var(--border-width-2)` × 12, `var(--border-width-hairline)` × 147 |
| Shadow | `0 0 #0000` × 23, `0 1px 2px 0 rgb(0 0 0 / 0.05)` × 19, `0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)` × 3, `0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)` × 4, `0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)` × 3, `inset 0 2px 4px 0 rgb(0 0 0 / 0.05)` × 1 |
| Opacity | `0` × 4, `0.1` × 52, `0.2` × 9, `0.3` × 5, `0.4` × 38, `0.5` × 45, `0.05` × 2, `0.6` × 54, `0.7` × 64, `0.08` × 1 |
|  | `0.8` × 56, `0.9` × 6, `0.12` × 1, `0.15` × 23, `0.16` × 1, `0.18` × 1, `0.22` × 1, `0.25` × 35, `0.28` × 1, `0.35` × 19 |
|  | `0.45` × 1, `0.65` × 1, `0.75` × 19, `0.85` × 19, `0.95` × 19, `1` × 38, `fillOpacity: 0.09` × 3, `floodOpacity: 0.1` × 1, `opacity: 0` × 20, `opacity: 0.9` × 2 |
|  | `opacity: 0.75` × 1, `opacity: 1` × 16, `strokeOpacity: 0.85` × 1 |
| Blur | `blur(2px)` × 1, `blur(8px)` × 11, `blur(12px)` × 2, `stdDeviation: 1.5` × 1, `stdDeviation: 3.5` × 3 |
| Motion duration | `0.01ms` × 2, `0.15s` × 2, `1s` × 12, `2s` × 3, `150ms` × 178, `200ms` × 15, `delayDuration: 150` × 1, `delayDuration: 300` × 3, `duration: 0.1` × 1, `duration: 0.2` × 4 |
|  | `duration: 0.12` × 3, `duration: 0.14` × 3, `duration: 0.16` × 3, `duration: 0.22` × 2, `duration: 0.24` × 3, `duration: 0.26` × 1 |
| Motion easing | `[0.16, 1, 0.3, 1]` × 1, `cubic-bezier(0.4, 0, 0.2, 1)` × 166, `cubic-bezier(0.4, 0, 0.6, 1)` × 3, `ease` × 2 |
| Stacking layer | `0` × 2, `10` × 7, `40` × 2, `50` × 10, `55` × 1, `60` × 2 |
| Breakpoint | `min-width: 640px` × 324, `min-width: 768px` × 16, `min-width: 1024px` × 90 |

### Current hard-coded value baseline

| Category | Occurrences | Examples |
| :--- | ---: | :--- |
| arbitrary utilities | 179 | `min-h-[44px]`, `min-w-[44px]`, `text-[11px]` |
| raw neutral text utilities | 654 | `text-zinc-400`, `text-zinc-500`, `text-zinc-100`, `text-zinc-900` |
| raw hex colours | 39 | `#818cf8`, `#4f46e5`, `#a1a1aa`, `#18181b` |
| other raw colours | 13 | `239`, `rgba(250, 204, 21, 0.4)`, `rgba(250, 204, 21, 0.3)`, `rgba(245, 158, 11, 0.25)` |
| inline values | 386 | `stroke: currentColor`, `fill: currentColor`, `opacity: 0`, `fill: none` |
| CSS literals | 38 | `outline: 2px solid #4f46e5`, `transition: background-color 0.15s ease, color 0.15s ease`, `animation-duration: 0.01ms`, `transition-duration: 0.01ms` |
| **Total** | **1309** | |

The ratchet counts arbitrary Tailwind values, raw neutral text palette utilities, literal colours, and literal inline styles, CSS and Motion values. Token definitions, CSS variable references, and standard Tailwind scale utilities are excluded. A hex or colour function inside an arbitrary utility counts under literal colours. Existing uses are reported by the Studio test suite. A higher total fails the test. Lower the committed baseline as migrations remove literals.
