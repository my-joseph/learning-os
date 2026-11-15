# 03_STEM — Mathematics, Physics & Parametric Visual Standards

**Module Code:** `RULES-STEM`  
**Applies To:** Mathematics (`MTH`), Physics (`PHY`), scientific derivations, LaTeX formatting, and educational diagram assets  
**Prerequisite:** Must adhere to `rules/00_core.md`, `rules/01_arch.md`, and `rules/02_pedagogy.md`  

---

## PART 1 — Mathematical Notation & Derivation Standards

### 1. Vertical Step-by-Step Derivation & Anti-Clumping Rule
When showing mathematical equation solving, algebraic simplification, worked examples, or drill problem derivations:
- **Never** chain multiple `=` steps horizontally across a single line ($A = B = C = D$).
- **Always** format step-by-step mathematical working **vertically from top to bottom** with each row representing a **single discrete transformation**:
  ```latex
  \begin{aligned}
    \left(\frac{34 + 10}{2}\right) \sqrt{15^2 - \left(\frac{34 - 10}{2}\right)^2} &= A \\
    \frac{34 + 10}{2} \sqrt{15^2 - \left(\frac{34 - 10}{2}\right)^2} &= A \\
    \frac{44}{2} \sqrt{15^2 - \left(\frac{34 - 10}{2}\right)^2} &= A \\
    \frac{44}{2} \sqrt{15^2 - 12^2} &= A \\
    \frac{44}{2} \sqrt{225 - 144} &= A \\
    \frac{44}{2} \sqrt{81} &= A \\
    22 \times 9 &= A \\
    A &= 198
  \end{aligned}
  ```
- **Granular Derivation Invariant (Photomath / Line-by-Line Standard):** Each row in the drill `steps` array must represent a single calculation step. Smashing multiple operations together (e.g. $\sqrt{15^2 - 12^2} = \sqrt{225 - 144} = \sqrt{81} = 9$) is strictly forbidden because it breaks the learner's ability to click "Mark Diverged Step" on the exact operation where their scratchpad calculation diverged.

### 2. KaTeX Notation & UI Rendering Standards
- **Inline Math:** Use KaTeX inline syntax (`$expr$`) for isolated symbols, variables, units, and short expressions (e.g., $x \in \mathbb{R}$, $v = 10\text{ m/s}$, $a^2 + b^2 = c^2$).
- **Block Equations:** Use native Notion `equation` blocks for major formulas, theorems, multi-line systems, and formal derivations.
- **Annotated Steps:** Pair complex algebraic transformations with brief explanatory text preceding or following the equation block to explain *why* an operation was performed (e.g., *"Divide both sides by the non-zero coefficient"*).
- **Mandatory `<FormattedText />` for Mistake Tags & UI Pills:** Whenever a `mistakeTags[].label`, `context`, `option.label`, or diagnostic message in `practice-studio` contains inline LaTeX (`$...$`), it **MUST** be rendered through `<FormattedText text={label} />` (never raw string `{t.label}`), and its pill container must use flexible height (`min-h-[28px] py-1`) rather than rigid fixed height so fractions (e.g., `$\frac{1}{2}$`) and exponents never clip or display raw `$` delimiters.

---

## PART 2 — Parametric Educational Diagrams & Vector Engine

### 3. Mandatory Parametric Diagram Generation for Spatial & Physical Content
Whenever illustrating geometric configurations (triangles, angles, circles, polygons, 3D solids), coordinate graphs, or physics diagrams (force vectors, free-body diagrams):
- AI must generate visual assets **programmatically** using structured mathematical parameters (via `math_engine.figure_builder`, attached automatically from the archetype's `figureBuilders` in the reasoning vault by `math_engine.figure_autofill`) rather than manually drawing static arbitrary coordinates.
- **Unified Design System Invariants:**
  - **Typography:** math in KaTeX's own fonts, as in Notion equations and the Studio: numbers, operators and function names upright (`KaTeX_Main`), single-letter variables italic (`KaTeX_Math`), a real minus sign (−). Prose words (titles, notes, "true root") in the sans-serif UI font. `math_engine/figure_svg.py` embeds the two KaTeX fonts (`math_engine/fonts/`, MIT) in every SVG, so Notion shows them on any machine. Write figure titles and labels in sentence case with math in `$...$`.
  - **Background & Card:** Subtle pastel card background (`#f8fafc`, rounded corners `rx="12"`).
  - **Color Palette:** Standardized 6-theme semantic palettes (`emerald`, `amber`, `indigo`, `purple`, `blue`, `rose`).
  - **Crisp Geometry:** Explicit right-angle markers, proportional side lengths, distinct color-coded vertices, and dedicated formula/trap alert badges.

---

## PART 3 — Native Asset Hosting & Hotlink Elimination

### 4. Strict Prohibition of External Image Hotlinking (Error 429 & 403 Prevention)
- AI must **NEVER** hotlink external third-party image URLs (such as `upload.wikimedia.org`, Wikipedia, or unauthenticated web servers) inside Notion image blocks.
- **Root Cause:** External hotlinks trigger aggressive automated rate-limiting (`HTTP 429 Too Many Requests`) and anti-hotlinking permission blocks (`HTTP 403 Forbidden`) on Notion clients, causing broken image placeholders for users.

### 5. Mandatory Native Notion File Upload API (`/v1/file_uploads`)
All visual assets (SVGs, diagrams, charts) must be uploaded directly to Notion's official cloud storage:
1. Initialize upload: `POST https://api.notion.com/v1/file_uploads` with payload `{"mode": "single_part"}`.
2. Binary upload: Send `multipart/form-data` with form field strictly named `file` containing the binary payload to the provided `upload_url`.
3. Block attachment: attach it as an image block:
   ```json
   {"object": "block", "type": "image", "image": {"type": "file_upload", "file_upload": {"id": "<file_upload_id>"}}}
   ```
   This is implemented in `notion_sync/figures.py` (`upload_svg`, `figure_block`); unit and chapter pages get figures through `figure` blocks in the `notion_sync.unit_page` spec, rendered from the same builders as drills.
*(Notion automatically converts this into a permanent native AWS S3 hosted file with type `file`, guaranteeing instant loading, zero rate-limiting, and 100% vector sharpness).*

### 6. Strict Zero-Leak Placeholder & Hint Invariant in Math & Physics Drills
- When generating STEM drills (`math_engine.generate` or manual problem JSONs):
  - `inputHint` and `placeholder` must specify the expected unit or syntax (e.g., `Enter the integer angle measure in degrees`, `Enter leg length in meters`).
  - **Never** include the solution value in an example (e.g., writing `(e.g. 53)` when the solution is `53^\circ`, or `(e.g. 12)` when the solution is `12\text{ feet}`).
  - Intermediate hints (`checkpointHint`) must provide mathematical formulas or invariant identities (e.g., `Complementary angles sum to $90^\circ$`), never the numerical result of the current problem.

### 3.1 Automatic Figure Attachment (Rule 11)
- **Every archetype decides about figures.** It declares either `figureBuilders` or `"figureNone": "<why a picture adds nothing>"`. Geometry, graphs of functions, number lines (inequalities, intervals), the complex plane, vectors, and anything a learner would sketch to understand the problem get `figureBuilders`. **Guard:** ingest and `--check` reject a problem whose archetype has neither (`require_figure_decision`). Older archetypes get the field the first time a drill uses them. The learner never has to ask for a picture.
- `figureBuilders`: `fn` from `math_engine/figure_builder.py`; `args` are numeric expressions over `givens` keys (`math_engine.safe_expr`: `+ - * / ^`, `sqrt`, `abs`, `exp`, `ln`, `log`, `sin`, `cos`, `tan`, `pi`); `labels` are string arguments as format strings over givens (`"{base:g} m"`), including the curve itself for `build_function_graph_figure` (`"expr": "{a:g}*(x-{h:g})^2+{k:g}"`). List several builders when drills name their givens differently; the first that builds is used.
- `ai_drill_ingest.ingest_ai_drill` calls `math_engine/figure_autofill.py` to attach `figure` automatically from `givens`, so the figure always matches the numbers in the prompt.
- **Unknowns are labelled `?`, not hidden.** For a reverse or multi-step problem, compute the unknown's size from the givens in `args` (e.g. `"radius": "sqrt(V/(pi*h))"`) and label it `"r = ?"`. A `?` label adds the note "Not to scale" automatically. Never plot the unknown on a grid where it could be read off (a point whose coordinates are the answer, the roots of the equation being solved); there, use `figureNone`/`figureWaiver` or show only the givens.
- `figureWaiver` (a reason) on a single problem is only for a figure that would give the answer away even with `?` labels. **Guard:** if an archetype declares `figureBuilders` and no figure can be built from `givens` (and no `figureWaiver`), ingestion raises `AiContractError`.
- Builders for T02: `build_function_graph_figure` (any `safe_expr` function including piecewise `a if x < c else b` and `cbrt`; marked points on either curve; free and hollow points, so a relation given as ordered pairs needs no curve; dashed `vlines`/`hlines` for asymptotes and line tests; a second curve), `build_mapping_diagram_figure` (domain and range ovals with an arrow per pair), `build_number_line_figure` (interval notation, open/closed ends, rays), `build_complex_plane_figure` (points as arrows from 0, conjugate, modulus). A shape no builder draws: add a builder (code change) before writing archetypes for it.
- The Studio (`practice-studio/src/components/MathFigure`) and the SVG export (`math_engine/figure_svg.py`, used for Notion) draw the same spec; a new shape, marker or plot type goes into both.
