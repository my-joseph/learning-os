# 03_STEM — Mathematics, Physics & Parametric Visual Standards

**Module Code:** `RULES-STEM`  
**Applies To:** Mathematics (`MTH`), Physics (`PHY`), scientific derivations, LaTeX formatting, and educational diagram assets  
**Prerequisite:** Must adhere to `rules/00_core.md`, `rules/01_arch.md`, and `rules/02_pedagogy.md`  

---

## PART 1 — Mathematical Notation & Derivation Standards

### 1. Vertical Step-by-Step Derivation Rule
When showing mathematical equation solving, algebraic simplification, or worked examples in `MTH` and `PHY` pages:
- **Never** chain multiple `=` steps horizontally across a single line ($A = B = C = D$).
- **Always** format step-by-step mathematical working **vertically from top to bottom** using native Notion block `equation` elements with LaTeX:
  ```latex
  \begin{aligned}
    2x + 5 &= 15 \\
    2x &= 15 - 5 \\
    2x &= 10 \\
    x &= 5
  \end{aligned}
  ```
- (or sequential vertical `equation` blocks under each explanatory step) so every transformation step stacks downward clearly, exactly like real mathematical writing.

### 2. KaTeX Notation & UI Rendering Standards
- **Inline Math:** Use KaTeX inline syntax (`$expr$`) for isolated symbols, variables, units, and short expressions (e.g., $x \in \mathbb{R}$, $v = 10\text{ m/s}$, $a^2 + b^2 = c^2$).
- **Block Equations:** Use native Notion `equation` blocks for major formulas, theorems, multi-line systems, and formal derivations.
- **Annotated Steps:** Pair complex algebraic transformations with brief explanatory text preceding or following the equation block to explain *why* an operation was performed (e.g., *"Divide both sides by the non-zero coefficient"*).
- **Mandatory `<FormattedText />` for Mistake Tags & UI Pills:** Whenever a `mistakeTags[].label`, `context`, `option.label`, or diagnostic message in `practice-studio` contains inline LaTeX (`$...$`), it **MUST** be rendered through `<FormattedText text={label} />` (never raw string `{t.label}`), and its pill container must use flexible height (`min-h-[28px] py-1`) rather than rigid fixed height so fractions (e.g., `$\frac{1}{2}$`) and exponents never clip or display raw `$` delimiters.

---

## PART 2 — Parametric Educational Diagrams & Vector Engine

### 3. Mandatory Parametric Diagram Generation for Spatial & Physical Content
Whenever illustrating geometric configurations (triangles, angles, circles, polygons, 3D solids), coordinate graphs, or physics diagrams (force vectors, free-body diagrams):
- AI must generate visual assets **programmatically** using structured mathematical parameters (via `math_engine.diagram_generator`) rather than manually drawing static arbitrary coordinates.
- **Unified Design System Invariants:**
  - **Typography:** Clean system font (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto`) for labels, KaTeX math font for variables.
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
3. Block attachment: Attach to the Notion page as a native Notion-hosted file block:
   ```json
   {
     "object": "block",
     "type": "file_upload",
     "file_upload": {
       "id": "<file_upload_id>"
     }
   }
   ```
*(Notion automatically converts this into a permanent native AWS S3 hosted file with type `file`, guaranteeing instant loading, zero rate-limiting, and 100% vector sharpness).*

### 6. Strict Zero-Leak Placeholder & Hint Invariant in Math & Physics Drills
- When generating STEM drills (`math_engine.generate` or manual problem JSONs):
  - `inputHint` and `placeholder` must specify the expected unit or syntax (e.g., `Enter the integer angle measure in degrees`, `Enter leg length in meters`).
  - **Never** include the solution value in an example (e.g., writing `(e.g. 53)` when the solution is `53^\circ`, or `(e.g. 12)` when the solution is `12\text{ feet}`).
  - Intermediate hints (`checkpointHint`) must provide mathematical formulas or invariant identities (e.g., `Complementary angles sum to $90^\circ$`), never the numerical result of the current problem.
