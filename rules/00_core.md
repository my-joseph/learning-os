# 00_CORE — Universal Governance & Safety Invariants

**Module Code:** `RULES-CORE`  
**Applies To:** All implementation tasks, AI agents, scripts, and database operations  
**Priority:** Mandatory (Must be read before every task)  

---

## PART 1 — Mandatory Instructions

### 1. Read Applicable Rule Modules
Before starting any implementation task involving the Learning System:
1. Read this Core Rule Module (`rules/00_core.md`).
2. Read the specific domain module corresponding to the task (e.g., `01_arch.md` for schemas, `02_pedagogy.md` for content, `03_stem.md` for math/physics, `04_code.md` for programming, `05_qa.md` for audits, `06_template_contract.md` for problem templates & quality gates, `07_problem_generation.md` for drill composition, weak-spot targeting & progression).
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

### 5. Strict 100% English-Only Content & Web UI Invariant
- **Notion Learning Pages:** All generated content across Topic, Chapter, Unit, and Resource pages (including section headings, conceptual explanations, worked examples, `Practice Guide`, `Active Recall`, and `My Implementation & Mistake Log` prompts) must be written strictly in **100% English**.
- **Practice Studio Web Application (`practice-studio/src/**/*`):** Every UI element in the web application — including buttons, headers, badges, filter tabs, input placeholders, tooltips (`title` / `aria-label`), empty states, status banners, Pre-Sync Review labels, and code comments — **MUST be written strictly in 100% English**.
- **Zero Non-English UI Tolerance:** Never insert Thai (`[\u0E00-\u0E7F]`) or other non-English strings into React components, TypeScript files, or drill JSON metadata. *(Only direct conversational responses with the user in the chat interface remain in polite Thai).*
- **Lucide Icons Only (Zero Emoji UI Invariant):** Never use Unicode emojis inside Practice Studio UI components or Notion sync UI controls; always use semantic vector icons from `lucide-react`.
- **Mandatory `<FormattedText />` Rendering for Inline Math & Code Tokens:** Every dynamic text field rendered in Practice Studio (`problem.prompt`, `problem.context`, `answerSpec.options[].label`, `steps[].explain`, `checkpointHint`, and **especially `mistakeTags[].label`**) **MUST** be rendered via `<FormattedText text={...} />` (never raw `{t.label}` JSX interpolation) so that inline KaTeX math (`$...$`), code tokens (`` `...` ``), and Concept Vault mentions (`[[CON-...]]`) always render properly without leaking raw LaTeX delimiters.

### 6. Strict Zero-Leak Placeholder & Hint Policy (Anti-Spoiler Invariant)
- **Zero-Leak Invariant:** When authoring drills, interactive exercises, code tracing tasks, or active recall questions, `inputHint`, `placeholder`, and intermediate hints (`checkpointHint`) must **NEVER** contain the correct answer, any substring or synonym of the accepted answers, or an example (`e.g.`) that gives away the solution.
- **Contract & Syntax Only:** Placeholders and input hints are strictly confined to specifying data format, syntax, or contract boundaries (e.g., `Enter 3-digit HTTP status code`, `Enter sequence (e.g. AAA -> BBB -> CCC)`, `Enter integer angle measure in degrees`).
- **Strictly Disjoint Counter-Examples:** If an example is provided inside an input hint (using `e.g.`), it **MUST** be a counter-example, dummy token, or unrelated category value that is strictly disjoint from `answerSpec.accepted`, `answerPlain`, and `answerDisplay`. Using the correct answer as an example in a placeholder is a critical pedagogical failure.
- **Pre-Sync Validation Guard:** All generator scripts, player servers, and API endpoints must programmatically validate and sanitize drill specifications to eliminate leaks before saving to disk or synchronizing with Notion databases.

### 7. Granular Step-by-Step Derivation Standard (Photomath / Single-Transformation Standard)
When authoring or generating worked solutions and step-by-step derivations (`steps` array in Math and STEM problems):
- **Pedagogical Line-by-Line Integrity:** Every step must isolate a **single discrete algebraic or arithmetic transformation** (e.g. remove parentheses, simplify inner grouped arithmetic, reduce fractions, evaluate powers, simplify radicand, take principal square root, isolate variable).
- **Anti-Clumping & Zero Equality Chaining:** Never compress 3–4 mathematical operations into a single step (e.g., never write $\sqrt{15^2 - 12^2} = \sqrt{225 - 144} = \sqrt{81} = 9$ in one line). Multi-equality chaining ($A = B = C = D$) destroys the learner's ability to locate arithmetic divergences.
- **Action-Oriented Explanations:** Every step's `explain` string must state the specific mathematical action taken (e.g. *"Simplify 34 + 10 to 44."*, *"Evaluate 15^2 to 225."*) to empower the "Mark Diverged Step" telemetry in Practice Studio to pinpoint exact student misconceptions.

---

## PART 3 — Automation & Scale Principles

### 8. AI-Driven Implementation at Scale
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

### 8. Three-Phase Generation Workflow
Always separate analysis from generation and finalize with cross-referencing:

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

#### Phase C — Final-Pass: Concept Vault Cross-Referencing & Immediate Notion Sync
- After generating or updating any page, drill, or problem specification, cross-reference the generated text against the `Concept Vault` database and `id_map.json` (all keys prefixed with `CON-`).
- Detect matching domain terms and technical keywords (e.g., `TCP 3-Way Handshake`, `DNS`, `TLS`, `HTTP`, `WebSocket`).
- Automatically bind matching terms using native `@Page` mentions (`[[CON-<KEY>]]`), turning dry terminology into an interactive, Wikipedia-style knowledge graph.
- **Pristine Drill Sync Requirement:** Whenever a drill file (`drills/data/**/*.json`) or code lab is generated, immediately synchronize the initial pristine unattempted record (`Practice Status: "Ready"`, `Score: null/0`) into the `Learning Practice & Drills` Notion database with full question breakdown and learning focus. Never leave a newly authored drill existing only on local disk awaiting manual user sync.
- Verify that every technical prerequisite or specialized concept provides instantaneous 1-click lookup.

Do not skip analysis and immediately generate generic content.

### 9. Local-First Architecture
- **Canonical Source of Truth:** System implementation rules (`rules/*.md`), drill schemas (`drills/data/`), lab configs (`lab.config.json`), and parametric visual engines (`math_engine/`) are authored and maintained Local-First in the workspace repository.
- **Direct Agent Tooling & Zero-Latency Execution:** AI agents and subagents must read local Markdown and JSON files directly using standard file tools. This guarantees sub-millisecond retrieval, eliminates API network latency / rate limit hazards, and preserves LLM context window with 3–4x higher token density than raw Notion API JSON blocks.
- **Notion as Presentation & Review Dashboard:** Notion serves as the primary human-facing presentation layer, active recall interface, and spaced retention ledger.
- **Rules Are Local-Only:** Rule updates, additions, or refinements are made in `rules/*.md` and version-controlled with Git. Rules are not synced to Notion; any old rule pages in Notion are stale and must not be read or edited as a reference.

### 10. Version Control & Git Hygiene Protocol
- **Strict Secrets Invariant:** Never commit `.env`, private tokens, or credential files. Ensure `.gitignore` is always active and verified before staging.
- **Milestone Checkpoint Commits:** Create clean, semantic Git commits (`feat:`, `fix:`, `refactor:`) immediately upon completing significant batches, tool upgrades, or modular updates.
- **Isolated Branching for Experiments:** Whenever performing experimental UI overhauls, CSS styling changes, or architecture refactoring, AI must create an isolated branch (`experiment/<feature-name>`). Never perform high-risk UI/styling experiments directly on `main`.
- **Remote Synchronization:** Push verified commits to GitHub (`origin main`) after completing confirmed milestones so the remote repository remains a mirror of the local-first source of truth.

### 11. Issue Log (learner studies without interruptions)
The learner builds this system to study, not to supervise it. Mistakes are recorded and fixed in batches instead of interrupting study.
- **What to log:** any mistake an AI caught in its own work, or that a reviewer subagent, a gate or the learner caught, when it is one of these: a problem the reviewer sent back (`fix`) or dropped, even if already fixed; a stop-rule hit; a tool or engine gap; a rule or skill that was unclear or contradictory; a script or Studio bug; anything the learner reports ("log this: ..."). Do **not** log a gate rejection that was fixed on the next run of the same task; that is the normal workflow.
- **How:** `python -m scripts.issues add --kind <kind> --severity urgent|batch --source author|reviewer|gate|learner --where <drill/problem, file or command> --what "<one sentence>" --action open|auto-fixed|dropped`. The log is `issues/log.jsonl` in the main checkout (gitignored, local-only, append-only); the script finds it from any worktree.
- **Urgent** (also put a warning on the first line of the reply to the learner), only when: an ingested or synced drill has a wrong answer or an ambiguous prompt; a bad problem passed every gate; learner progress is lost or corrupted; Notion sync is broken; a secret leaked. Everything else is `batch`.
- **Clearing:** when the learner says "clear the issue log", run `python -m scripts.issues summary`, fix root causes by group (a kind that recurs points at a rule, skill or gate to change), and mark each record with `python -m scripts.issues resolve <id> ... --note "<PR or reason>"`.

---

## PART 4 — Final Governing Principle
The Learning System must be:
**Flexible in content, consistent in architecture, reliable in sources, measurable in progress, and sustainable at scale.**

Use this Core Rule as the universal operating standard for every task. These rules establish quality and safety boundaries, not rigid page layouts. The actual learning context, database information, connected Resources, and user's requested scope always determine the appropriate implementation.
