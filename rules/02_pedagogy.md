# 02_PEDAGOGY — Curriculum Design, Active Recall & Practice Guides

**Module Code:** `RULES-PEDAGOGY`  
**Applies To:** Content authoring, curriculum architecture, instructional design, practice guides, and active recall  
**Prerequisite:** Must adhere to `rules/00_core.md` and `rules/01_arch.md`  

---

## PART 1 — Pedagogical Philosophy & Reference Structures

### 1. Core Principle: Reference Structure, Not Rigid Templates
Existing Topic, Chapter, and Unit pages are reference examples, not rigid templates. Use them to understand:
- Information architecture.
- Content organization.
- Expected learning quality.
- Design conventions.
- Appropriate learning activities.

Do not force every page to use identical sections. AI must adapt the page structure to the actual subject, learning objectives, difficulty, and available Resources. Sections may be added, removed, renamed, merged, reordered, or expanded. The final structure must serve the learning objective rather than blindly follow an example.

### 2. Separation Rule
Each page type must have independent content-generation logic:
- **Topic:** Overall learning context, roadmap integration, and coordination of Chapters.
- **Chapter:** Role in parent topic, structural invariants, and explanation of related Units.
- **Unit:** Detailed instructional learning content, definitions, worked examples, and specific practice guides.
*Never copy the Topic structure directly into Chapter or Unit pages.*

### 3. Subject-Adaptive Learning Design
Choose content formats dynamically based on the subject domain:
- **Conceptual Subjects:** Conceptual models, mental analogies, comparisons, diagrams, and relationship trees.
- **Programming Subjects:** Concise mental models, type signatures, runnable code examples, runtime traces, debugging tasks, and test suites.
- **Mathematical & Physical Subjects:** Axiomatic foundations, rigorous vertical derivations, geometric/vector visual diagrams, and multi-step worked examples.
- **Workflow & Engineering Subjects:** Procedures, checklists, architectural diagrams, and practical deliverables.

---

## PART 2 — Research, Resources & Context Analysis

### 4. Required Analysis Before Content Generation
Before generating or modifying any page, inspect:
1. Current page properties.
2. Parent and child relations.
3. Related Topic, Chapter, and Unit records.
4. Existing page content.
5. Connected Resources.
6. Resource availability and accessible source content.
7. Completeness of database properties and Resource relations.
8. Relevant prerequisites and dependencies.

Use actual Notion database records rather than relying only on page titles. Understand what the learner should know before deciding what content to generate.

### 5. Resource-Based Learning & Access Verification
Resources are the knowledge sources used to support AI-generated learning content. Prioritize:
1. Official documentation and reference manuals.
2. Academic publications and textbooks.
3. Reliable technical books.
4. Reputable technical community resources.

**Resource Access Verification:** A URL existing does not mean its content is accessible. Distinguish between:
- URL Accessible
- Content Accessible
- Content Verified  
*Do not claim to have read or verified a Resource if only its title or URL is available. Preserve original source links and attribute claims accurately.*

---

## PART 3 — Active Recall & Learner Personal Workspace

### 6. Active Recall Design
Active Recall questions must be adapted to the actual Unit. Questions should evaluate:
- Direct recall of definitions and invariant properties.
- First-principles conceptual explanation.
- Application in unseen problems.
- Trap and edge case detection.
- Connections with previously learned concepts.

*Format:* Questions are presented with collapsible toggles hiding the step-by-step Reference Solution, enabling the learner to attempt mental retrieval or scratch-paper solution before expanding.

### 7. Hybrid Learning Workspace — My Implementation & Mistake Log
Every Unit page must include a dedicated personal workspace section titled `My Implementation & Mistake Log` for the learner to record their own work after hands-on practice:
- **Feynman One-Liner:** A 1–2 sentence synthesis of the core concept written in the learner's own words.
- **My Solution / Working / Code:** Dedicated space for the learner's own code implementation, mathematical derivation, or worked exercise solution.
- **Mistake & Pitfall Log:** Specific bugs, calculation errors, or misconceptions encountered during practice, used as the primary focus during subsequent Spaced Reviews.

---

### 7a. Default Page Structure for `MTH` / `PHY` Units and Chapters (v4)
This is the default for new and upgraded math and physics pages (§1 still allows adapting it to the material). The `start-unit` skill builds pages from it.

**Unit page**
- **Callout:** Learning Objective, Expected Output, prerequisites (`@Page`), next Unit (`@Page`), Resource (the book's `R0xx` page as `@Page`, plus the section number). The page's `Resources` relation links the same `R0xx`.
- **1. Core Concepts & Intuition:** definitions and the mental model, with at least one `figure` block (`rules/03` §3.1, §5) unless the unit is pure symbol manipulation: geometry, graphs, number lines, the complex plane, and **equations whose number of solutions or extraneous roots a graph explains** (a V-shaped graph against a horizontal line, `y = √x` against a line). A worked example about a shape or graph shows it too. **Page figures are decided apart from the drills:** an archetype's `figureNone` ("a graph would show the roots") protects drill answers, but a page teaches and its worked examples show answers anyway.
- **2. Key Formulas & Decision Rules:** each formula with a collapsed toggle **"Why this works"** (3–5 lines from first principles). Add a short **"Which method when"** rule only when the Unit has two or more methods.
- **3. Worked Examples (graduated, vertical `\begin{aligned}`):** headings `Example 1 (L1 — Direct): …`, `Example 2 (L2 — Reverse): …` or `(L2 — Translation)`, `Example 3 (L3 — Trap Contrast): …`. A longer procedure ("Multi-Step") is not L2.
  - Example 1, L1: direct procedure.
  - Example 2, L2: reverse (find an input from the result) or a short translation of a situation.
  - Example 3, L3, trap contrast: the Unit vault's most important `cognitiveTraps` entry, shown as the wrong line (❌) next to the right line (✅) with one sentence on why. Use the vault's trap, so the page and the drills teach the same trap.
  Worked examples are explanations, not an exercise list; the Anti-Dump Rule (§8) still applies.
- **4. Unit Practice Guide:** the 4 categories of §8.
- **5. Active Recall Questions:** 3–4 toggles with vertical reference solutions (§6).
- **6. My Implementation & Mistake Log:** the learner's workspace (§7). Drill results synced from the Studio are inserted at the end of this section. **Agents never edit, move or delete anything in this section.**
- **7. Completion Checklist & Mastery Review.**

**Chapter page**
- **Callout:** Objective, completion criteria, parent Topic, prerequisites, Resource.
- **1. Chapter Role:** what the chapter is for, and the unit sequence in one line (`U01 → U02 → …`).
- **2. Core Invariants & Key Formulas** of the whole chapter.
- **3. Look-Alike Problems Across Units:** a table of problems that look similar but belong to different Units (for example a fraction *expression* to simplify vs. a fraction *equation* to solve), with the cue that tells them apart. This is what chapter mixed drills test.
- **4. Chapter Practice Guide:** the 4 categories of §8.
- **5. Cross-Unit Active Recall:** 3–4 toggles that compare or combine Units (not repeats of Unit questions).
- **6. Summary & Spaced Review Guide.**

**Upgrading an existing page:** never rewrite it. Add the missing v4 parts by inserting blocks after the right heading, delete nothing, and leave section 6 untouched (`rules/00_core.md` §4).

**Checking pages:** `python -m scripts.page_audit <TOPIC|CHAPTER|UNIT>` (read-only) reports every page against this structure: FAIL for a missing part, WARN for a judgement call (e.g. no figure). "Is this page up to standard?" is answered by this script, not by counting blocks.

**Writing pages:** agents write learning pages only with `python -m notion_sync.unit_page` (`--mode new`, `--mode add`, `--set`; it renders and uploads figures) and drill results only through drill sync. No direct Notion API calls that create, edit or delete blocks or properties on learning pages: they bypass the guards (no rewrite, section 6 untouched). Math in any page text, figure captions included, is written as `$...$` (it renders as a Notion equation); the tool refuses `sqrt(x)` or `x^2` outside `$`. A figure caption that needs fixing is replaced with `--recaption N="..."`, and a figure itself is redrawn in place with `--refigure N=figure.json` (the page's N-th image; never in section 6; the caption is kept). If the tool cannot do what is needed (e.g. fix the text of an existing block), log a `tool-gap` (`rules/00_core.md` §11) and leave the page as it is.

---

## PART 4 — Multi-Level Practice Guides (No Static Problem Dump)

### 8. The Anti-Dump Rule
**Core Principle:** Do **not** embed static exercise lists or fixed problem sets directly inside Topic, Chapter, or Unit page bodies. Static problems lose replay value after the first completion and cannot scale with the learner's evolving `Mastery (0-4)` score.

Instead, every Unit, Chapter, and Topic must provide a **thorough, content-specific, scannable Practice Guide** in **English**, structured into **4 clear categories with indented sub-bullets** and **clickable `@Page` mentions** to all referenced Topics, Chapters, Units, and Resources.

#### Level 1 — Unit Practice Guide (4 Required Categories):
1. **Core Skills to Drill:** Specify the exact calculations, algebraic manipulations, runtime traces, type-narrowing patterns, or architectural mechanics the learner must practice until fluent in this Unit, broken down into concrete sub-skills and progression tiers.
2. **Combine with Prior Units:** Explicitly name and link (via clickable `@Page` mentions) 2–4 specific prior Units or Chapters that should be blended into practice problems, explaining the exact combined scenario.
3. **Common Traps & Edge Cases to Test:** List the exact sign traps, zero/null boundary conditions, invalid algebraic steps, or compiler/runtime pitfalls unique to this Unit that practice problems must test.
4. **Cross-Subject & Real-World Connection (Math ↔ Physics ↔ Code):** For `MTH` and `PHY`, explicitly explain which Physics formulas/phenomena and Programming algorithms rely on this Unit's concept (with clickable `@Page` mentions). For `PRG`, explain the exact production architecture scenario and adjacent `PRG` chapters/topics where this skill is applied.

#### Level 2 — Chapter Practice Guide (4 Required Categories):
1. **Chapter Mixed Practice:** Guide the learner on practicing all Units in the Chapter together (with clickable `@Page` mentions to every Unit) via an unlabeled mixed problem set (where problems do not announce which Unit's formula applies) or a cohesive 60–100 line Mini-Lab/Module.
2. **Combine with Prior Chapters:** Identify and link specific prior Chapters/Topics (`@Page` mentions) to integrate into chapter-level practice.
3. **Chapter-Wide Traps:** Detail the cross-unit confusion points, formula mix-ups, or architectural boundary mistakes that arise when combining multiple Units from the Chapter.
4. **Cross-Subject & Real-World Connection:** Explain how the Chapter as a whole powers Physics (`PHY`), advanced Mathematics (`MTH`), or production Software Engineering (`PRG`), with clickable `@Page` mentions.

#### Level 3 — Topic Practice & Synthesis Guide (4 Required Categories):
1. **Topic-Wide Synthesis / Capstone Project:** Define a comprehensive cross-chapter diagnostic exam (for `MTH`/`PHY`) or an end-to-end Capstone Project (for `PRG`) that integrates all Chapters of the Topic (linked via `@Page` mentions).
2. **Must-Be-Automatic Foundations:** Specify the non-negotiable core skills across the Topic that must become effortless before advancing.
3. **Cross-Chapter Traps:** Highlight systemic misconceptions or integration bugs that span multiple Chapters.
4. **Bridge to Next Topics in Roadmap:** Map out how this Topic directly feeds into upcoming Topics in `MTH`, `PHY`, and `PRG` using clickable `@Page` mentions.

---

### 9. Wikipedia-Style Concept Vault & Final-Pass Auto-Linking Protocol
- **Concept Retention Invariant:** Technical terms, foundational protocols, and architectural models (e.g. `TCP 3-Way Handshake`, `DNS`, `TLS`, `HTTP`, `WebSocket`, `Event Loop`, `Closures`) are indexed centrally in the `Concept Vault` (`id_map.json` under `CON-*`).
- **Mandatory Final-Pass Cross-Reference:** During the final step of generating or updating any Unit, Chapter, Topic, or Practice problem:
  1. AI must inspect the generated text against all registered `Concept Vault` records in `id_map.json`.
  2. Any technical term that matches a registered Concept Vault record must be linked natively using `@Page` mentions (`[[CON-<KEY>]]`).
  3. This ensures the student can hover/click any unfamiliar term to open a 60-second recovery note (What is it, Analogy, How it works, Comparison, Gotchas) without breaking their reading flow.
  4. If a fundamental concept appears frequently but has no existing Concept Vault entry, AI should proactively register a concise Concept Note to expand the vault continuously.

---

### 10. Strict Invariant: Zero Answer Leakage in Exercise Placeholders & Hints
- **Pedagogical Integrity of Active Recall:** The entire educational purpose of drills and active recall exercises is **effortful cognitive retrieval**. If the answer or an exact solution example is leaked in the placeholder, the task collapses into mindless mechanical typing, destroying learning retention.
- **The Placeholder Leak Trap:** Authors and AI generators must **NEVER** write examples that reveal the answer (e.g. writing `(e.g. 401)` when the answer is `401`, or `(e.g. 53)` when the solution is `53^\circ`, or `SYN -> SYN-ACK -> ACK` in the placeholder when that is the sequence to deduce).
- **Format Contracts vs. Solutions:**
  - *Permitted:* Syntax boundaries, data types, and formatting conventions (e.g., `Enter 3-digit HTTP status code`, `Enter integer in degrees`, `Enter 3-packet sequence (e.g. AAA -> BBB -> CCC)`).
  - *Strictly Forbidden:* Providing the correct answer as an example or giving hints that reduce the search space to a trivial copy-paste.
- **Disjoint Examples Mandate:** Any example used in `inputHint`, `placeholder`, or `checkpointHint` must be strictly disjoint from `answerSpec.accepted`, `answerPlain`, and `answerDisplay`.

---

### 11. Adaptive Interaction Modes: Multiple Choice vs. Direct Input
- **Decision Engine (`interactionMode: "adaptive"`):** AI problem generators dynamically determine whether each problem should be **Multiple Choice (`type: "choice"`)** or **Direct Input (`type: "text"` / `"predict-output"` / `"number"`)** based on pedagogical effectiveness:
  - **When to choose Multiple Choice (`choice`):**
    - Conceptual discrimination between closely related entities (e.g., 401 Unauthorized vs. 403 Forbidden; 502 Bad Gateway vs. 504 Gateway Timeout).
    - Identifying the correct architectural statement or edge-case trade-off among plausible system designs.
    - **High-Quality Distractors Rule:** All 3 wrong options (distractors) must represent actual, prevalent student misconceptions or common failure modes—never silly, trivial, or joke answers. Distractors must force rigorous conceptual precision.
  - **When to choose Direct Input (`text` / `predict-output`):**
    - Tracing execution order or exact sequence (e.g., Call Stack, Event Loop microtasks, TCP 3-Way Handshake flag sequence).
    - Numerical calculations, exact HTTP status code recall, or formula outputs where multiple choice would spoil the answer space.

---

### 12. Skip Option & Concept Gap Telemetry
- **No Penalized Guessing:** When a learner genuinely does not know a concept, blind guessing corrupts error telemetry and promotes false confidence.
- **Skip Protocol:**
  - The UI provides an explicit **"Skip (Don't Know)"** action on every problem.
  - Skipping sets score to `0`, flags `skipped: true`, and assigns a `concept-gap` mistake tag.
  - **Instant Learning Loop:** Skipping immediately unrolls the mental model hint and vertical step-by-step solution, allowing the learner to immediately learn the missing prerequisite without frustration.
  - **Notion Spaced Repetition Ledger:** Skipped questions are logged specifically as **Concept Gaps** in Notion (`Skipped Questions for Review`), surfacing them as the highest priority items for subsequent review sessions.
