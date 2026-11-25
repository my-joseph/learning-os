# Practice Studio component catalog

Use this catalog with the [design tokens](system.md) and the [reference gallery](references/README.md) whenever a Studio surface needs a control or pattern.

## Extend before create

Learner decision, 2026-11-25.

1. Identify the role of the requested UI. Look for the shared button, icon button, row, section header, chip or segmented switcher, menu, dialog or overlay, badge, or input that already serves this role.
2. Use its existing variant if it fits. For a new need within that role, add a named variant to the shared component. Use design tokens exclusively for its visual values. Keep the behavior, keyboard affordances, and responsive states in the shared implementation.
3. For a change to an existing component's size, weight, or colour, determine how broadly the learner wants it applied. For a global change, update the shared token or base and verify its callers. For a single surface, add a variant and opt in there. If the intended reach is unclear, ask the learner before changing the shared default.
4. Create a shared component only for a genuinely new role. Explain the role and why existing components cannot serve it in the PR. Add the export and its props or variants to this catalog in the same change. Get learner approval before introducing a colour.
5. Source a new role from shadcn/ui first (https://ui.shadcn.com, the Studio's base library — learner decision 2026-11-22/25): if the shadcn registry has a component for the role, add it into `practice-studio/src/components/ui/shadcn/` (shadcn CLI or its published source), keep its Radix behaviour and accessibility, restyle it only with Studio tokens, express differences as variants, and add it to this catalog. Write a custom component only when shadcn/ui has nothing for the role; say so in the PR body with the shadcn components you checked.

## External libraries

Learner decision, 2026-11-25.

- Allowed categories are shadcn-ecosystem registries that distribute Tailwind and Radix copy-paste components, headless libraries, and domain libraries for charts, code editors, math input (MathLive), or 3D rendering (three.js).
- Themed UI kits such as MUI, Mantine, Chakra, and Ant Design are excluded.
- Get learner approval for every new library and reuse one library per role. Wrap external UI in a Studio component, restyle it with Studio tokens, and add it to this catalog. Check the bundle size impact and lazy-load heavy libraries.

### Approved libraries

The dates record policy approval for these existing Studio choices and the Code Block integration.

| Library | Role | Reason | Approved date |
| :--- | :--- | :--- | :--- |
| Radix / shadcn/ui | Headless primitives and component registry | Accessible controls with local source styled by Studio tokens. Includes the Code Block registry item and shared Button. | 2026-11-25 |
| `cmdk` | Command palette | Keyboard navigation and command selection for Studio Search. | 2026-11-25 |
| `motion` | Motion | Shared animation and reduced-motion support. | 2026-11-25 |
| `lucide-react` | Icons | Shared semantic icons, including Code Block copy feedback. | 2026-11-25 |
| `shiki` | Syntax highlighting | Code Block uses Studio's existing lazy language loader and GitHub themes. | 2026-11-25 |
| `katex` | Math display | Renders mathematical notation in learning content. | 2026-11-25 |
| `mathlive` | Math input | Provides structured math editing and the virtual keyboard. | 2026-11-25 |
| `three`, `@react-three/fiber`, `@react-three/drei` | 3D figures | Renders interactive geometry in lazy-loaded views. | 2026-11-25 |
| `class-variance-authority` | Component variants | Defines shared variants, including Code Block surfaces and lines. | 2026-11-25 |
| `clsx`, `tailwind-merge` | Class composition | Power Studio's `cn` helper, which supplies the Code Block registry's `cn` dependency. | 2026-11-25 |

## Shared UI exports

Paths are relative to `practice-studio/src/components/ui/`. Radix parts accept the underlying primitive props unless the catalog says otherwise. DOM parts accept the native element props and support `className`. forwarded refs follow their rendered elements.

| File | Exports | Variants, props and use |
| :--- | :--- | :--- |
| `CodeBlock.tsx` | `CodeBlock` | Use `variant="full-file"` for a filename, line numbers, and optional highlighted or selectable lines. Use `terminal` for CLI transcripts and Run checks output, with an optional `title`, `status`, or `exitCode`. Terminal preserves `$ ` command markers and omits line numbers; pass styled `children` (with `code` as the Copy text) for coloured ✓ / ✗ rows. The PRG Run checks area is one terminal: `$ npm run check`, one ✓ / ✗ / – row each for Tests (Vitest-style `1 failed | 13 passed (14)`), Lint, Types and Review, then failure lines, then the passed/failed footer. Both headers offer Wrap lines and Copy. Use `snippet` (default) for headerless code, `inline-example` for paired Input and Output, or `wrapped` for short assertions and diagnostic output. Pass `language` to highlight supported code with Studio's Shiki themes. |
| `ConfirmDialog.tsx` | `ConfirmDialog` | `open`, `title`, `description`, `onConfirm`, `onCancel`. Optional `confirmLabel`, `cancelLabel`, `destructive` (defaults to true). Focus starts on Cancel. |
| `CopyButton.tsx` | `CopyButton` | `text`, `className`, `children`, `copiedContent`. Optional `timeoutMs`, `title`, `ariaLabel`, `requireClipboard`. Switches to copied feedback. |
| `Heading.tsx` | `Heading` | Use `variant="page"` (default) for the page h1 and `variant="section"` for a prominent h2 or empty-state title. Do not put the curriculum ID above the title; the learner copies IDs from the row menu. |
| `Numeral.tsx` | `Numeral` | Use `variant="sm"` (default) for Geist tabular figures at the surrounding text size. Use `variant="lg"` for Roboto Slab tabular figures at 14 px or larger, including scores, mastery, Due today and the question timer. |
| `ListDot.tsx` | `ListDot`, `listKindForHeading` | `kind` is `task` (default), `info`, or `limit` with optional `className`. Use the heading helper to select a kind. |
| `ListRow.tsx` | `ListRow` | Sidebar button with `leading`, a single-line `label`, and a reserved `trailing` slot. The slot appears on hover, keyboard focus, or selection. Use `variant="tree"` and `treeDepth={1 | 2 | 3 | 4}` for fixed 32 px curriculum rows. The tree row keeps its full-width surface and indents its contents. Use weight 400 at every tree level and medium (500) for the current row. Topic uses `foreground`; deeper rows use `foreground-control`. Pass `treeRow` with an independent `action` and optional `preview`. The action keeps its space and appears on hover, focus, selection, or while its menu is open. The title uses ellipsis at rest and fades over the final 28 px beside visible actions on desktop. `actionOpen` keeps the surface highlighted, `highlighted` marks a search target, and `surfaceProps` applies attributes to the wrapper. Use `CommandItem` for the cmdk adapter. |
| `SectionHeader.tsx` | `SectionHeader` | Compact disclosure button. Pass `expanded`, the controlled panel ID in `controls`, and `onClick`. The trailing chevron follows the expanded state. Pair with a panel managed by the caller. |
| `ThemeToggleButton.tsx` | `ThemeToggleButton` | `theme` is `light` or `dark`. pass `onToggle` and optional `className`. |
| `ToastStack.tsx` | `ToastStack` | `status` message or null and `onClearStatus`. Renders and dismisses status, warning and error feedback. |
| `shadcn/AlertDialog.tsx` | `AlertDialog`, `AlertDialogTrigger`, `AlertDialogPortal`, `AlertDialogOverlay`, `AlertDialogContent`, `AlertDialogHeader`, `AlertDialogFooter`, `AlertDialogTitle`, `AlertDialogDescription`, `AlertDialogAction`, `AlertDialogCancel` | Modal confirmation parts. Header and footer take div props. Action and Cancel each accept Button `variant` and `size`, defaulting to `destructive` and `secondary` respectively. |
| `shadcn/Badge.tsx` | `Badge`, `badgeVariants` | `variant` accepts `default`, `status`, `secondary`, `outline`, `destructive`, `success` or `ghost`. Use `choice` for a fixed 24 px option marker and `answerPart` for a result breakdown. Supports `asChild` and span props. Use status recipes for verdict colours. |
| `shadcn/Button.tsx` | `Button`, `buttonVariants`, `IconButton` | `variant` accepts `primary` (default), `secondary`, `outline`, `ghost` or `destructive`. `size` accepts `default`, `sm`, `compact`, `lg`, `icon` or `iconSm`. Supports `asChild` and native button props. Use `IconButton` for a labelled icon-only action. Its `hitArea` is `expanded` (uses surrounding padding) or `padded` (an inset highlight inside the touch box). Use `sidebarToggle` for the 44 px mobile and 32 px desktop navigation toggle, or `sidebarAction` for a tree row’s 44 px mobile and 28 px desktop action trigger. See the math answer variants below for answer fields, palette keys and feedback actions. |
| `shadcn/Card.tsx` | `Card`, `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter` | Framed surface with `variant="default"` or `variant="feedback"`. Pair feedback geometry with a status recipe. Card accepts `asChild`. Parts take div, heading or paragraph props as appropriate. |
| `shadcn/CodeBlock.tsx` | `CodeBlock`, `CodeBlockHeader`, `CodeBlockTitle`, `CodeBlockActions`, `CodeBlockContent`, `CodeBlockLine`, `CodeBlockFooter` | Local adaptation of the shadcn Code Block registry parts. Feature code uses the Studio `CodeBlock` wrapper for highlighting, wrap preference, copy feedback, and named variants. |
| `shadcn/Collapsible.tsx` | `Collapsible`, `CollapsibleTrigger`, `CollapsibleContent` | In-place disclosure. Use the root's controlled `open` and `onOpenChange`, or `defaultOpen`. |
| `shadcn/Command.tsx` | `Command`, `CommandLoading`, `CommandInput`, `CommandList`, `CommandGroup`, `CommandItem` | cmdk parts for command menus. Pass cmdk props such as `shouldFilter`, input `value` and `onValueChange`, group `heading`, and item `onSelect`. CommandItem adds the ListRow slots and defaults to size `md` and tone `secondary`. A trailing action sits next to the option in the DOM to keep it independently focusable. Pass `selected` to show that action while the option or its menu is active. |
| `shadcn/Dialog.tsx` | `Dialog`, `DialogTrigger`, `DialogClose`, `DialogPortal`, `DialogOverlay`, `DialogContent`, `DialogTitle`, `DialogDescription` | DialogContent takes `position` (`center` or `top`), `closeButtonSize`, `closeButtonClassName`, `overlayPreset` and `overlayClassName`. DialogOverlay has `preset="default"` or `preset="search"`. Use `top` with the `search` scrim for command search. The search scrim has no blur. |
| `shadcn/Drawer.tsx` | `Drawer`, `DrawerTrigger`, `DrawerClose`, `DrawerPortal`, `DrawerContent`, `DrawerTitle`, `DrawerDescription` | DrawerContent takes `overlayClassName` and `side` (`right` by default, `left` for navigation). Right opens as a bottom sheet below `md`. |
| `shadcn/HoverCard.tsx` | `HoverCard`, `HoverCardTrigger`, `HoverCardRowTrigger`, `HoverCardContent`, `useWarmHoverCard` | Supplemental preview using the raised surface, border, and medium shadow tokens, with `p-space-3` padding. It opens with the shared popover motion; `side="right"` slides in from the left (`popoverFromLeft`). In a list, wrap each card with `useWarmHoverCard(delay)`: the first card waits for the delay; while one is open, or for 400 ms after it closes, the next opens at once so the learner can sweep down the list. Use `HoverCardRowTrigger` for fine-pointer row hover with native touch activation. Sidebar previews open to the right after 500 ms and show a wrapping title and muted monospace ID. Content defaults to `align="center"` and `sideOffset={4}`. Pass Radix delay props to the root. |
| `shadcn/Input.tsx` | `Input`, `inputVariants` | Native input props with `type="text"` by default. `variant` is `default` (framed), `embedded` (inside a shared field), or `answer` (inside the shared answer field). |
| `shadcn/Popover.tsx` | `Popover`, `PopoverTrigger`, `PopoverAnchor`, `PopoverClose`, `PopoverContent`, `RowMenu`, `RowMenuTrigger`, `RowMenuContent`, `RowMenuItem` | PopoverContent defaults to `align="center"` and `sideOffset={6}`. Use RowMenu for secondary actions anchored to a row. RowMenuContent accepts `placement="sidebar"` (right) or `"search"` (below, above the dialog layer). RowMenuItem uses `density="touch"` by default. Use `"compact"` only to preserve the existing Search and sidebar menu geometry. |
| `shadcn/Skeleton.tsx` | `Skeleton` | Loading placeholder. Pass div props and size utilities through `className`. |
| `shadcn/Tabs.tsx` | `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent`, `SegmentedChips`, `SegmentedNav`, `SegmentedNavItem` | TabsList sets `variant` to `default` (segmented) or `underline`. TabsTrigger inherits it and accepts an override. Root and parts take Radix selection, value and orientation props. Use `SegmentedChips` for a single-select filter group with `label`, `options`, `value` and `onValueChange`. Chips use pressed-button semantics. Use `variant="answerMode"` with two labelled options and optional icons for the sliding answer mode switch. Use `SegmentedNav` for two navigation links with a sliding indicator. It takes `variant="sidebar" | "header" | "rail"` and `activeIndex={0 | 1}`. Wrap each link or unavailable segment in `SegmentedNavItem` and pass its visual `selected` state. Keep `aria-current` on the active link. |
| `shadcn/Tooltip.tsx` | `TooltipProvider`, `Tooltip`, `TooltipTrigger`, `TooltipPortal`, `TooltipContent` | Brief contextual labels. Provider defaults to `delayDuration={300}`. Trigger accepts `asChild` and `title` for the hydration fallback. Content defaults to `sideOffset={6}` and `collisionPadding={8}`. |

## Markdown code fences

Use ```` ```js {3,7-9} title="app.js" ```` for a numbered code block with a filename. Line numbers start at 1 and ranges include both ends. The attributes are optional and can appear in either order. Unrecognized metadata is ignored.

Use ```` ```terminal ```` for shell transcripts. The aliases `console` and `shell-session` use the same variant. Start command lines with `$ ` and keep output on its own lines. The title defaults to Terminal and can be set with `title="…"`.

## Control variants

- `IconButton`, `SegmentedChips`, `ListRow`, and `RowMenuItem` share `size="xs" | "sm" | "md"` for 28, 32, and 36 px, and `tone="default" | "secondary" | "primary" | "destructive"`. The defaults are `md` for IconButton, `xs` for SegmentedChips, and `sm` for ListRow and RowMenuItem.
- `selected` sets `data-selected`. SegmentedChips derives it from `value` and also sets `aria-pressed`. cmdk owns the option's selection and arrow navigation.
- `disabled` blocks activation. `loading` adds `aria-busy` and disables the same control in place. Keep the icon, label and action slots mounted so states preserve their box size.
- `ListRow` defaults to a larger touch box when needed. Use `touchTarget="expanded"` when the visual row must stay compact and the surrounding layout has space for the hit area. Reserve the space around expanded targets.

## Studio shell patterns

Use these shared controls when working on the Studio shell.

| Role | Existing implementation | Options |
| :--- | :--- | :--- |
| Curriculum row and section header | `DrillSwitcher` in `components/shell/DrillSwitcher.tsx` | ListRow tree rows and SectionHeader disclosures for Programming Labs and Drills. |
| Search row and search icon | `StudioSearchTrigger` in `components/shell/StudioSearchPalette.tsx` | Full-width ListRow in the sidebar and a compact toolbar icon. |
| Search overlay and filter chip | `StudioSearchPalette` in `components/shell/StudioSearchPalette.tsx` | Dialog search preset, SegmentedChips, and CommandItem rows. |
| Row menu | `DrillRowActions` in `components/shell/DrillRowActions.tsx` | RowMenu with sidebar and search placements. |
| Segmented workspace control | `WorkspaceSwitch` in `components/workspace/WorkspaceSwitch.tsx` | Math and Programming links use SegmentedNav from the shared Tabs module. |

## Math answer variants

| Role | Shared variant | Geometry and state |
| :--- | :--- | :--- |
| Check answer | IconButton with `hitArea="answer"`, `size="sm"` and `tone="answerCheck"` | 44 px on phones and 32 px on desktop. Pass `loading` to disable the control and announce that the check is in progress. |
| Math template keys and palette toggle | IconButton with `hitArea="answer"` | Use `paletteQuick` or `paletteDisclosure` with `size="xs"` (28 px desktop), and `paletteKey` with `size="sm"` (32 px desktop). All are 44 px on phones. Pass `selected` to the disclosure and retain `aria-expanded`. |
| Math input and plain text | SegmentedChips with `variant="answerMode"` | Two equally sized segments with a sliding indicator. Height is 44 px on phones and 28 px on desktop. |
| Choice option | Button with `variant="choice"`, `size="choiceWrap"` or `size="choiceStack"`, and Badge with `variant="choice"` | Keep the radio semantics on the button. Use the status recipes for the option and its label badge. The touch height is at least 44 px. |
| Previous, Next, Review & sync | Button with `size="answerNav"`, `variant="answerNav"` or `variant="answerNavReview"` | The quiet navigation controls are 44 px tall on phones and 32 px on desktop. |
| Result card and actions | Card with `variant="feedback"`, Button with `variant="resultOutline"`, `variant="resultPrimary"` or `variant="resultLink"`, Badge with `variant="answerPart"` | Use `size="resultAction"` for the outline and primary variants and `size="resultLink"` for secondary actions. All have 44 px targets on phones. |

## Math assist variants

| Role | Shared variant | Geometry and state |
| :--- | :--- | :--- |
| Reset, Hint, equation set-up and Show steps | Button with `variant="assist"` and `size="assistInline"` | Use Collapsible for disclosures. Buttons are at least 44 px square on phones and size to their labels on desktop. |
| Skip | Button with `variant="assist"` and `size="assistSkip"` | Keeps a 44 px phone target and a 36 px desktop height. |
| Solution or worked example steps | Card with `variant="assistPanel"` for a group and `variant="assistStep"` for each row | The panel uses the secondary surface and the rows use the raised surface. |
| Flag a diverged step | Button with `variant="assistFlag"` and `size="assistFlag"` | The quiet flag appears on row hover or focus. Use the wrong-status recipe on the active row. |
| Self-score and mistake tags | Button with matching `variant` and `size` of `assistScore` or `assistTag` | Keep `aria-pressed`, the appropriate status recipe, and the existing disabled opacity. Both use 44 px phone targets and a 28 px desktop minimum. |
| Similar questions | TabsList with `variant="similar"`, inherited by TabsTrigger, and Badge with `variant="tabMark"` | A scrolling underline tab list with manual activation. Tabs are 44 px tall on phones and 36 px on desktop. Use a status recipe for the 16 px marker. |
| Similar list retry | Button with `variant="assistRetry"` and `size="assistRetry"` | Compact text action with a 44 px phone target. |
| Timer pause and resume | IconButton with `hitArea="timer"`, `size="timer"`, and `tone="timer"` or `"timerPaused"` | The toggle is 44 px on phones and 24 px on desktop. Keep the accessible label and pressed state. |
| Pagination and Review | Button with `variant="stepper"`, `size="stepper"` or `"stepperCompact"`, and Badge with `variant="stepMarker"` | Use navigation semantics and the status recipes on the circles. Both densities preserve the 44 px phone target. The marker can use `asChild` for its scale animation. |
| Worked example navigation | Button with matching `variant` and `size` of `exampleBack`, `exampleQuiet`, or `examplePrimary` | Breadcrumb, text disclosure and filled action share the worked example's text scale and preserve 44 px phone heights. |
