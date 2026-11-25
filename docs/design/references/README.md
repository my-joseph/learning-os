# Practice Studio reference gallery

These references capture the learner's preferred interaction feel. Use them to understand behavior and hierarchy; each Studio surface has its own job, so do not copy pixels mechanically. The shared design guide and current component variants remain the implementation source of truth.

## Gallery

| Image | What it shows | What the learner wanted | Studio component / variant |
| :--- | :--- | :--- | :--- |
| [PRG sidebar chevron](prg-sidebar-chevron.png) | A muted collapsible section heading with a trailing chevron. | Keep section controls quiet; put the chevron after the label and make the whole heading reveal a tree. | `DrillSwitcher` — collapsible Labs / Drills section header. |
| [PRG sidebar sections](prg-sidebar-sections.png) | Labs and Drills as sections in one sidebar list, with nested folders. | Use a tree, not a flat list; preserve a single scrolling surface with collapsible sections. | `DrillSwitcher` — Programming sidebar tree and section-header variant. |
| [Search row hover](search-row-hover.png) | The sidebar Search row with its shortcut hint visible in its hover state. | Make Search easy to find without leaving a permanent shortcut label in a quiet sidebar. | `StudioSearchTrigger` — sidebar row, default and hover/focus states. |
| [Search palette](search-palette.png) | A command palette with type chips and grouped results. | Keep the palette compact and scannable, with tight chip spacing and a clear result hierarchy. | `StudioSearchPalette` — Dialog/cmdk palette and filter-chip variants. |
| [Search row menu](search-row-menu.png) | A row-level ellipsis menu opened from a sidebar item. | Keep secondary actions out of the way until hover or focus, and attach them to the row they affect. | `DrillSwitcher` — drill leaf row and trailing `⋯` action-menu variant. |
| [Approved Studio search palette](studio-search-palette-approved.png) | The approved Studio search palette in the light theme. | Keep the palette focused and readable while the rest of the interface recedes. | `StudioSearchPalette` — open, light-theme state. |
| [Approved Studio search hover](studio-search-hover-approved.png) | The approved Studio sidebar with Search highlighted on hover. | Use a quiet row highlight and expose the shortcut only when the user is engaging with Search. | `StudioSearchTrigger` — hovered sidebar-row state. |
| [Approved Studio row menu](studio-row-menu-approved.png) | The approved Studio sidebar with a drill's row menu open. | Reveal row actions in context without adding persistent toolbar clutter. | `DrillSwitcher` — hovered drill leaf with its action menu open. |

## Adding a reference

1. Save the image in this folder as an optimized PNG or WebP under 300 KB.
2. Add a gallery entry describing what it shows, the behavior or feel the learner wanted, and the Studio component/variant it maps to.
3. Update [design principles](../principles.md) when the image adds a new reusable pattern.
