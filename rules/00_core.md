# 00_CORE — Universal Governance & Safety Invariants

**Module Code:** `RULES-CORE`  
**Applies To:** All implementation tasks, AI agents, scripts, and database operations  
**Priority:** Mandatory (Must be read before every task)  

---

## PART 1 — Mandatory Instructions

### 1. Read Applicable Rule Modules
Before starting any implementation task involving the Learning System:
1. Read this Core Rule Module (`rules/00_core.md`).
2. Read the specific domain module corresponding to the task (e.g., `01_arch.md` for schemas, `02_pedagogy.md` for content, `03_stem.md` for math/physics, `04_code.md` for programming, `05_qa.md` for audits).
3. Understand the current task and its requested scope.
4. Inspect the existing Notion databases, properties, relations, views, and page structures relevant to the task.
5. Identify existing conventions and dependencies.
6. Check whether the requested changes could affect other Topics, Tracks, or shared databases.
7. Plan the implementation before modifying anything.

These rules apply to every implementation task, including creating, editing, restructuring, generating content, modifying properties, and configuring database views. Do not assume that previous implementation decisions are still accurate without checking the current state.

### 2. Scope Protection
- Only modify the scope explicitly authorized by the user.
- Do not modify unrelated Topics, Tracks, Chapters, Units, or Resources.
- Reuse existing databases and relations whenever possible.
- Do not create duplicate databases, properties, records, or relations unnecessarily.
- Check whether a database or property is shared before changing its structure or default behavior.
- Never make global changes that affect other learning tracks without explicit authorization.
- Preserve existing data and page content.
- If a requested change cannot be implemented safely within the specified scope, explain the limitation before proceeding.

### 3. Source of Truth
Use the following priority when interpreting the Learning System:
1. Actual Notion database properties.
2. Actual database relations and linked records.
3. Existing page content.
4. Connected Resources and their accessible source content.
5. Relevant learning dependencies and roadmap context.
6. External references, only when appropriate and authorized.

Never invent property values, relationships, learning progress, resource contents, or completion states. If information is missing or contradictory, identify the issue instead of silently making assumptions.

---

## PART 2 — Core Content & Language Integrity

### 4. Preserve User Content (Rule 11)
- Never overwrite meaningful user-written notes without authorization.
- Never replace completed learning content with generic placeholders.
- Preserve useful examples and explanations.
- Avoid unnecessary restructuring.
- Do not delete existing sections without authorization.
- Add or improve content while respecting the existing design system.
- Generated content must remain editable by the user.

### 5. Strict English-Only Content Rule
All generated content across Topic, Chapter, Unit, and Resource pages (including section headings, conceptual explanations, worked examples, `Practice Guide`, `Active Recall`, and `My Implementation & Mistake Log` prompts) must be written strictly in **English**. Never leave non-English (e.g., Thai) text inside Notion learning pages. *(Conversations with the user in chat remain in polite Thai).*

---

## PART 3 — Automation & Scale Principles

### 6. AI-Driven Implementation at Scale
The system is intended to support hundreds of learning Units without requiring the user to manually write every page. AI should:
- Read existing database records.
- Understand relations and learning context.
- Identify relevant Resources.
- Generate appropriate learning structures.
- Generate instructional content.
- Create relevant exercises and Active Recall questions.
- Verify content and references.

Do not require the user to manually create the initial content structure for every Unit. However:
- Generated content must remain editable.
- Source attribution must be preserved.
- Unverified information must be identified.
- Existing user content must be protected.

### 7. Two-Phase Generation Workflow
Always separate analysis from generation:

#### Phase A — Analyze
- Inspect database properties.
- Read relations.
- Review existing content.
- Inspect Resources.
- Identify learning objectives.
- Determine prerequisites.
- Select an appropriate page structure.
- Identify missing information.

#### Phase B — Generate
- Create or improve the page content.
- Add subject-appropriate explanations.
- Include examples and practice.
- Create relevant Active Recall questions.
- Add source attribution.
- Verify completeness and consistency.

Do not skip analysis and immediately generate generic content.

### 8. Local-First Architecture & Notion Auto-Sync Protocol
- **Canonical Source of Truth:** System implementation rules (`rules/*.md`), drill schemas (`drills/data/`), lab configs (`lab.config.json`), and parametric visual engines (`math_engine/`) are authored and maintained Local-First in the workspace repository.
- **Direct Agent Tooling & Zero-Latency Execution:** AI agents and subagents must read local Markdown and JSON files directly using standard file tools. This guarantees sub-millisecond retrieval, eliminates API network latency / rate limit hazards, and preserves LLM context window with 3–4x higher token density than raw Notion API JSON blocks.
- **Notion as Presentation & Review Dashboard:** Notion serves as the primary human-facing presentation layer, active recall interface, and spaced retention ledger.
- **Mandatory Synchronization:** All rule updates, additions, or refinements must be made in local Markdown files first, version-controlled with Git, and synchronized to the Notion Master Rule Hub and Sub-Pages via `python3 sync_rules_to_notion.py`. Manual edits on Notion rule pages that diverge from local files are strictly prohibited.

---

## PART 4 — Final Governing Principle
The Learning System must be:
**Flexible in content, consistent in architecture, reliable in sources, measurable in progress, and sustainable at scale.**

Use this Core Rule as the universal operating standard for every task. These rules establish quality and safety boundaries, not rigid page layouts. The actual learning context, database information, connected Resources, and user's requested scope always determine the appropriate implementation.
