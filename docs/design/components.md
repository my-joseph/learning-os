# Practice Studio component catalog

Use this catalog with the [design tokens](system.md) and the [reference gallery](references/README.md) whenever a Studio surface needs a control or pattern.

## Extend before create

Learner decision, 2026-11-25.

1. Identify the role of the requested UI. Look for the shared button, icon button, row, section header, chip or segmented switcher, menu, dialog or overlay, badge, or input that already serves this role.
2. Use its existing variant if it fits. For a new need within that role, add a named variant to the shared component. Use design tokens exclusively for its visual values. Keep the behavior, keyboard affordances, and responsive states in the shared implementation.
3. For a change to an existing component's size, weight, or colour, determine how broadly the learner wants it applied. For a global change, update the shared token or base and verify its callers. For a single surface, add a variant and opt in there. If the intended reach is unclear, ask the learner before changing the shared default.
4. Create a shared component only for a genuinely new role. Explain the role and why existing components cannot serve it in the PR. Add the export and its props or variants to this catalog in the same change. Get learner approval before introducing a colour.

## Shared UI exports

Paths are relative to `practice-studio/src/components/ui/`. Radix parts accept the underlying primitive props unless the catalog says otherwise. DOM parts accept the native element props and support `className`. forwarded refs follow their rendered elements.

| File | Exports | Variants, props and use |
| :--- | :--- | :--- |
| `ConfirmDialog.tsx` | `ConfirmDialog` | `open`, `title`, `description`, `onConfirm`, `onCancel`. Optional `confirmLabel`, `cancelLabel`, `destructive` (defaults to true). Focus starts on Cancel. |
| `CopyButton.tsx` | `CopyButton` | `text`, `className`, `children`, `copiedContent`. Optional `timeoutMs`, `title`, `ariaLabel`, `requireClipboard`. Switches to copied feedback. |
| `ListDot.tsx` | `ListDot`, `listKindForHeading` | `kind` is `task` (default), `info`, or `limit` with optional `className`. Use the heading helper to select a kind. |
| `ThemeToggleButton.tsx` | `ThemeToggleButton` | `theme` is `light` or `dark`. pass `onToggle` and optional `className`. |
| `ToastStack.tsx` | `ToastStack` | `status` message or null and `onClearStatus`. Renders and dismisses status, warning and error feedback. |
| `shadcn/AlertDialog.tsx` | `AlertDialog`, `AlertDialogTrigger`, `AlertDialogPortal`, `AlertDialogOverlay`, `AlertDialogContent`, `AlertDialogHeader`, `AlertDialogFooter`, `AlertDialogTitle`, `AlertDialogDescription`, `AlertDialogAction`, `AlertDialogCancel` | Modal confirmation parts. Header and footer take div props. Action and Cancel each accept Button `variant` and `size`, defaulting to `destructive` and `secondary` respectively. |
| `shadcn/Badge.tsx` | `Badge`, `badgeVariants` | `variant` accepts `default`, `status`, `secondary`, `outline`, `destructive`, `success` or `ghost`. Supports `asChild` and span props. Use status recipes with the layout-only `status` variant. |
| `shadcn/Button.tsx` | `Button`, `buttonVariants` | `variant` accepts `primary` (default), `secondary`, `outline`, `ghost` or `destructive`. `size` accepts `default`, `sm`, `compact`, `lg`, `icon` or `iconSm`. Supports `asChild` and native button props. |
| `shadcn/Card.tsx` | `Card`, `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter` | Framed surface. Card accepts `asChild`. Parts take div, heading or paragraph props as appropriate. |
| `shadcn/Collapsible.tsx` | `Collapsible`, `CollapsibleTrigger`, `CollapsibleContent` | In-place disclosure. Use the root's controlled `open` and `onOpenChange`, or `defaultOpen`. |
| `shadcn/Command.tsx` | `Command`, `CommandLoading`, `CommandInput`, `CommandList`, `CommandGroup`, `CommandItem` | cmdk parts for command menus. Pass cmdk props such as `shouldFilter`, input `value` and `onValueChange`, group `heading`, and item `onSelect`. |
| `shadcn/Dialog.tsx` | `Dialog`, `DialogTrigger`, `DialogClose`, `DialogPortal`, `DialogOverlay`, `DialogContent`, `DialogTitle`, `DialogDescription` | DialogContent takes `position` (`center` or `top`), `closeButtonClassName` and `overlayClassName`. Use `top` for command search. |
| `shadcn/Drawer.tsx` | `Drawer`, `DrawerTrigger`, `DrawerClose`, `DrawerPortal`, `DrawerContent`, `DrawerTitle`, `DrawerDescription` | DrawerContent takes `overlayClassName` and `side` (`right` by default, `left` for navigation). Right opens as a bottom sheet below `md`. |
| `shadcn/HoverCard.tsx` | `HoverCard`, `HoverCardTrigger`, `HoverCardContent` | Supplemental preview. Content defaults to `align="center"` and `sideOffset={4}`. Radix open and close delay props live on the root. |
| `shadcn/Input.tsx` | `Input`, `inputVariants` | Native input props with `type="text"` by default. `variant` is `default` (framed) or `embedded` (inside a shared field). |
| `shadcn/Popover.tsx` | `Popover`, `PopoverTrigger`, `PopoverAnchor`, `PopoverClose`, `PopoverContent` | Anchored surface for controls and row menus. Content defaults to `align="center"` and `sideOffset={6}`. |
| `shadcn/Skeleton.tsx` | `Skeleton` | Loading placeholder. Pass div props and size utilities through `className`. |
| `shadcn/Tabs.tsx` | `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent` | TabsList sets `variant` to `default` (segmented) or `underline`. TabsTrigger inherits it and accepts an override. Root and parts take Radix selection, value and orientation props. |
| `shadcn/Tooltip.tsx` | `TooltipProvider`, `Tooltip`, `TooltipTrigger`, `TooltipPortal`, `TooltipContent` | Brief contextual labels. Provider defaults to `delayDuration={300}`. Trigger accepts `asChild` and `title` for the hydration fallback. Content defaults to `sideOffset={6}` and `collisionPadding={8}`. |

## Studio shell patterns

These existing patterns are the starting point for the next component migration.

| Role | Existing implementation | Options |
| :--- | :--- | :--- |
| Curriculum row and section header | `DrillSwitcher` in `components/shell/DrillSwitcher.tsx` | Workspace-specific tree, collapsible sections, expandable folder and selectable leaf. |
| Search row and search icon | `StudioSearchTrigger` in `components/shell/StudioSearchPalette.tsx` | Full-width sidebar row and compact toolbar icon. |
| Search overlay and filter chip | `StudioSearchPalette` in `components/shell/StudioSearchPalette.tsx` | Dialog and command parts with result rows and selectable type chips. |
| Row menu | `DrillRowActions` in `components/shell/DrillRowActions.tsx` | Anchored row menu with sidebar and search placements. |
| Segmented workspace control | `WorkspaceSwitch` in `components/workspace/WorkspaceSwitch.tsx` | Math and Programming switcher. Start with `Tabs` when the need is a shared tab strip. |
