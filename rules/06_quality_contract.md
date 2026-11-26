# 06_QUALITY_CONTRACT — Problem Quality Contract

**Module Code:** `RULES-QUALITY-CONTRACT`  
**Applies To:** Math & Code AI Drills, Variant Banks, Quality Gates G1–G6, Checker Parsers, Taxonomy & Verification  
**Priority:** Mandatory for authoring, modifying, or auditing drills, variant banks, and engine quality gates  
**Linked From:** `rules/00_core.md` (Part 1, Section 1), `rules/02_pedagogy.md` (Part 4), `rules/07_problem_generation.md`

---

## 1. Taxonomy & Workspace Contracts

### 1.1 Skills Taxonomy (`skills_taxonomy.json`)
When adding a new domain skill entry under `skills` in `skills_taxonomy.json`, specify `name`, `domain`, `tier`, `prerequisites` (each with `skill` and `strength`: `"hard"` or `"soft"`), and `g2_profile`. The prerequisite graph must remain a cycle-free DAG.

### 1.2 Coding Kata Workspace Contract
For coding problems (`codeType` in `kata`, `implement`, `refactor`, `fix-bug`, or problems with `visibleTests`/`starterCode`):
1. **Materializing the workspace on disk:** Call `code_engine.workspace.materialize_drill_workspace` (invoked automatically by `code_engine.ai_drill_ingest`) to generate `drills/workspace/<DRILL_ID>/` containing `package.json`, `README.md`, starter source files, and test files.
2. **Folder-Level vs. File-Level Deep Links:**
   - **Folder-Level:** `workspaceDir` (absolute path) and `vscodeFolderUrl` (`vscode://file/<abs_ws>`) computed at runtime by Studio API (do not emit `cursor://` or `cursorFolderUrl`).
   - **File-Level:** `workspaceFile` (relative path in drill JSON) and `vscodeUrl` (`vscode://file/<abs_src>`) computed at runtime (do not emit `cursorUrl`).
   - Workspace source paths must use the drill-relative manifest format and an allowed source extension. The materializer validates output paths before opening files.
3. **Non-Negotiable Invariants:**
   - The primary "Open in VS Code" button in Practice Studio **must always open the workspace folder** (`vscodeFolderUrl`) and never fall back to a single file, so VS Code discovers `package.json`, npm scripts, and the workspace terminal directory. Do not render an "Open in Cursor" button (code is edited in the learner's own editor).
   - Opening a single file (`vscodeUrl`) is allowed only as a secondary "Open File" action.

---

## 2. L1–L5 Levels, Tiers & `g2_profile`

> [!IMPORTANT]
> **Relationship to the core learning framework:**
> - **Pedagogy Reference:** See curriculum practice levels in `rules/02_pedagogy.md` §8 and mastery tracking in `rules/01_arch.md` §7 (`Mastery (0-4)`).
> - **Level (`L1–L5`):** Defines the **cognitive task type** of a problem and governs its step structure and verification floor via `g2_profile` in `skills_taxonomy.json` and the L3+ blind-solve demand gate (§2.3).
> - **Tier:** In `skills_taxonomy.json` (`foundational`, `intermediate`, `advanced`, `expert`), indicates curriculum progression depth rather than locking a skill to a single level.

| Level | Cognitive Task Type | Structural Characteristics | G2 Step Bounds | Granular Steps Target (Mandatory L1–L5) |
| :---: | :--- | :--- | :---: | :--- |
| **L1** | **Direct Computation / Recall** | Direct application of a core formula or definition | 1–10 steps | 2–5 micro-steps (2–3 steps is valid and complete for simple L1 items) |
| **L2** | **Reverse Solve / Multi-step Synthesis** | Solve backwards for an input parameter or combine multiple algebraic steps | 2–15 steps | 3–8 micro-steps |
| **L3** | **Trap, Flaw Diagnosis & Edge Cases** | Diagnose a flawed derivation, choose among taught methods, or check domain/edge cases | 2–20 steps | 5–12 micro-steps |
| **L4** | **Applied / Multi-concept Constraint** | Model a situation from multiple relations plus method choice or edge/constraint verification | 2–25 steps | 7–20 micro-steps |
| **L5** | **Non-Routine Synthesis & Multi-Domain Interleaving** | Combine concepts across topics/domains with no taught formula or routine method | 3–50 steps | 10–25+ micro-steps |

### 2.1 Granular Step Derivation Standard (Mandatory across L1–L5)
> [!IMPORTANT]
> The Photomath Single-Transformation Standard applies to **every math problem at every level (L1–L5)**, not only L5. Step counts scale naturally with complexity (typically 1–25 steps, up to 50 for L5; 2–3 steps is complete for a straightforward L1 item).

1. **One Transformation per Step (Universal Anti-Clumping):** Each entry in `steps` must isolate a single discrete mathematical transformation (e.g. substitute values → distribute → isolate variable → combine like terms → reduce fraction → take principal square root → final result).
2. **No Chained Equalities (Universal Anti-Chaining Invariant):** Never write $A = B = C = D$ or pack multiple equations into one step (e.g. never write $\sqrt{15^2 - 12^2} = \sqrt{225 - 144} = \sqrt{81} = 9$ on one line), so Practice Studio's "Mark Diverged Step" telemetry can pinpoint the exact step where a learner diverged.
3. **Action-Oriented Explanations (`explain`):** Every step must clearly state the mathematical action taken, with math notation wrapped in `$...$`.

### 2.2 Strict Difficulty Level Invariant
When authoring a drill for a requested difficulty level (`difficulty` in `1..5`):
1. **No Silent Fallback:** Never silently substitute lower-level problems when a unit or archetype cannot meet the requested level. Follow the §2.3 stop rule and log the gap in `scripts.issues`.
2. **Header-to-Problem Parity:** Every problem's `level` must match the requested difficulty when a single level is specified (or accurately reflect its earned level in `ALL` mixed drills).

### 2.3 Demand floor for AI-written L3+ problems (blind-solve tags)

Goal: when the learner asks for hard problems, no problem may be solvable as direct computation or mental math. Every L3+ label must be reached exactly.

**Level meaning** (aligned with published frameworks so it holds from middle school to university):

| Level | Webb DOK | NAEP complexity | Stein & Smith task | TIMSS G8 anchor (intl. % correct) |
| :---: | :--- | :--- | :--- | :--- |
| L1 | 1 Recall / simple procedure | Low | Memorization / procedures without connections | ≥ 55% (e.g. 2019 Exh. 3.11.2) |
| L2 | 2 Skill/concept: several steps, reverse use of a formula | Moderate (lower) | Procedures without connections, multi-step | 40–55% (Exh. 3.12.1) |
| L3 | 2 upper: choose a method, check edge cases, diagnose an error | Moderate | Procedures with connections | 30–45% (Exh. 3.12.2, 3.12.5) |
| L4 | 3 Strategic thinking: build a model from several relations and plan | High | Procedures with connections / doing mathematics | ≤ 30% (Exh. 3.13.2, 3.13.3) |
| L5 | 3–4 Non-algorithmic: no taught method fits | High | Doing mathematics | beyond Advanced |

The verb does not set the level ("explain" or "prove" alone does not raise it); the thinking the problem demands of a student at the target stage does. Material taught in earlier chapters of the same course counts as a tool.

**Blind-solve tags.** The blind solver (`rules/07_problem_generation.md` §4 V2) does not pick a level. It reports facts about its own solution:

| Tag | Values (low → high) | Meaning |
| :--- | :--- | :--- |
| `setup` | `given` / `translate` / `model` | expression or equation given / words → one standard model / combine ≥ 2 relations into an equation the prompt does not state |
| `strategy` | `prescribed` / `choose` / `invent` | method obvious from the topic / pick among taught methods / no taught method fits (key idea needed) |
| `check` | `none` / `edge` / `justify` | none / domain, extraneous root, endpoint or ± case must be checked / argument or proof required |
| `task` | `compute` / `diagnose` | solve / find the error in given work |
| `reverse` | true / false | the unknown is an input of the governing formula |
| `steps` | integer | real solution steps (one transformation each) |

**Mapping** (`math_engine.ai_drill_ingest.demand_level`): `invent` → L5; `model` with (`choose` or `check` ≠ none) → L4; `model`, `choose`, `check` ≠ none or `diagnose` → L3; `translate`, `reverse` or `steps` ≥ 4 → L2; otherwise L1.

**Gate** (`validate_blind_solve`, every L3+ problem): `blindSolve` must hold `answer`, `ambiguous` and all six tags; the answer must match `answerSpec`; the prompt must not be ambiguous; and the mapped level must reach `level`. Tags that give L1 never pass as L3+.

**No bolted-on checks.** `check = edge` must come from the problem itself (a domain, a ± case, a limit the question asks you to respect). A fits/doesn't-fit clause added only to earn it ("If it fits, report $d$; otherwise report $0$") is computation plus one comparison, not a check; the gate rejects sentinel answers like this. Ask for what the limit decides instead, e.g. the largest width within the budget.

**The check must decide something.** `check = edge` only counts when the check rules out at least one candidate (a root, a ± branch, a case, a value past a limit). The solver records it in `blindSolve.edgeRejected`, and the gate rejects `edge` without it. If every candidate passes (e.g. $X_L > 0$ when both roots are positive), the check decided nothing and the tag is `none`.

**Diagnose form (find the flaw).** An L3 diagnose problem must ask *which line is wrong*, not *what the correct value is*: a value question lets the learner just recompute, and the solver then tags it `compute` (L1). Write it like this:
- Show the work in the prompt as `Line N: $...$` lines, one per line. `display` stays hidden until the learner asks, so it cannot hold the work.
- Use `answerSpec` `{"type": "choice", "options": [{"id": "1", "label": "Line 1"}, ...], "correct": "<first wrong line>"}`.
- Put `verify.flaw` = `{"values": [value of each line], "firstWrong": k}`.
- `trapDerivation`/`trapValue` are the tagged mistake's result, and the last shown line must equal `trapValue`.
- Show at least 4 lines, and make the error something the learner has to find, not the only step.
- "Wrong" means the line's **value** differs from the problem's value (`verify.flaw` checks values). A method error must change the value on the line where it happens: multiplying top and bottom by $(3+4i)$ instead of the conjugate leaves the value unchanged, so write the wrong denominator ($3^2 + 4^2$) on that same line.
- Options after the flaw carry `trapTag` = `commonTrapTag`. Options before it carry a `provenance` note.

The shown-work lines are exempt from the givens and leak gates (`story_text` in `math_engine/ai_drill_ingest.py`).

**Stop rule:** at most one redesign per failing problem. If it still fails, drop the problem and record it in the issue log (`rules/00_core.md` §11, kind `level`, naming the archetype) so its vault level is fixed in the next batch. Do not interrupt the learner mid-run (they study these drills and do not approve them). Never relabel, change `category`, add `constraints` or bolt on a check to make it pass.

Trap tags (`commonTrapTag`) stay as metadata for diagnosis and telemetry; they do not raise the level on their own.

Sources: Webb's Depth of Knowledge (math descriptors); NAEP mathematical complexity (nces.ed.gov/nationsreportcard/mathematics/complexity2005.aspx); Stein & Smith Mathematical Tasks Framework; TIMSS 2019 grade 8 benchmark example items (timss2019.org/reports). University problems have no public % correct anchors; use the DOK descriptors only.

---

## 3. Trap Provenance & Flaw Diagnosis

1. **Real Human Misconceptions:** `trapTag` and `trapValue` must reflect a genuine cognitive trap from the reasoning vault (Distractor Provenance), never an arbitrary wrong number.
2. **Choice Distractor Telemetry:**
   - Every distractor option in `answerSpec.options` carries a vault `trapTag` from the archetype's `cognitiveTraps` and a `provenance` derivation/note (or, for L3 diagnose problems, options before the flaw carry `provenance` and options after carry `trapTag = commonTrapTag`).
   - When a learner selects a wrong option, telemetry records the selected option's `trapTag` rather than blindly overwriting it with `commonTrapTag`.
3. **Flaw Step Explanations (Find-the-Flaw):**
   - The solution step identifying the flawed line must state the student's flawed LaTeX expression alongside the correct line and mathematical reason.
4. **Process-Oriented Hints for L3 Flaw Problems (`§3.4`):**
   - `checkpointHint` for find-the-flaw problems **must never reveal the flaw location or error category** (e.g., never mention `distribute`, `inner derivative`, `sign`, `Line 2`, `second step`).
   - Use process-oriented guidance only, e.g.: *"Work through the derivation step-by-step on scratch paper, then compare your solution line by line with the student's work to identify where they diverge."*

---

## 4. Quality Gates Specification (G1–G6)

| Gate | Name | Pass Criteria | Failure Examples |
| :---: | :--- | :--- | :--- |
| **G1** | Archetype Integrity & Anti-Leak | 1. Code/math problem matches its archetype<br>2. Learner hints (`inputHint`, `checkpointHint`) **never leak the answer**<br>3. L3 flaw hints are strictly process-oriented (no error keyword or line-number spoiler) | - `checkpointHint` contains `$(1+2i)^2 = -3+4i$` when the answer is `2i`<br>- `inputHint` example equals the accepted answer<br>- L3 hint says *"Check line 2 for missing inner derivative"* |
| **G2** | Level-Structure Alignment | Step count and trap/flaw/demand structure match `level` and `g2_profile` (with `blindSolve` floor for AI L3+ problems) | - L3 problem with no `verify.flaw` and no `trapValue`<br>- L1 problem violating step-count bounds |
| **G3** | Diversity & Non-Duplication | Distinct structural fingerprints within a drill set; no near-duplicate skeletons that only swap numbers | - Two problems in one drill sharing the same `(templateKey/archetypeKey, form, skeleton)` fingerprint |
| **G4** | Distractor Provenance & Trap Validity | 1. `trapValue != answerPlain` and `trapDerivation` evaluates with SymPy from `givens`/`constants` to `trapValue` (matching `trapGivens` / vault `trapFormula` when declared)<br>2. For `choice` problems: every distractor carries a vault `trapTag` and `provenance` (SymPy-evaluable expressions must match the option value and differ from the correct answer; prose-only provenance emits an `unverifiable` warning) | Distractor missing vault `trapTag` or `provenance`, `provenance` evaluates to a different value, or `trapValue` equals the canonical answer |
| **G5** | Audit Mode (Batch Quality Audit) | Non-destructive scan across all drill JSON files in `drills/data/` (`python -m math_engine.audit`), separating actual violations from legacy missing fields | Legacy drill has malformed `answerSpec` or mismatched canonical answer |
| **G6** | Mathematical Typography | Zero sloppy operators or unsimplified formatting in learner-visible math fields | `+ -`, `- -`, `+-`, `--`, `^1`, `x^0`, `*1`, `1x` in LaTeX or plain text |

---

## 5. Verification CLI Commands & Filesystem Safety

### 5.1 Core Verification Commands
- **Check a math drill draft:** `.venv/bin/python -m math_engine.ai_drill_ingest --unit <UNIT> --ingest-file <draft.json> --check`
- **Check a PRG drill draft:** `.venv/bin/python -m code_engine.ai_drill_ingest --check <draft.json>`
- **Check a math variant bank / coverage:** `.venv/bin/python -m math_engine.variant_bank --check <UNIT>` and `.venv/bin/python -m math_engine.variant_bank --coverage <UNIT>`
- **Verify CI coverage for math drills** with `.venv/bin/python -m math_engine.variant_bank --coverage-gate`.
- **Batch quality audit (G5):** `.venv/bin/python -m math_engine.audit`
- **Skills taxonomy & drill coverage report:** `.venv/bin/python -m scripts.coverage_report`
- **Run the Python test suite:** `.venv/bin/python -m pytest -n auto -q`

### 5.2 Filesystem & Data Safety
> [!CAUTION]
> **Tests must never mutate real learner or repository content files.**
> 1. Drill ingestion tests must point `DRILLS_DATA_DIR` and `PROGRESS_DIR` to temporary directories outside checkouts (never write to `drills/data/` or `progress/`).
> 2. Notion tests must set `NOTION_DRY_RUN=1` or mock `notion_request` (never hit the live Notion API).
> 3. Tests calling `scripts.coverage_report.generate_coverage_report` must pass a temporary `output_path` (or `output_path=None`) and never overwrite `reports/coverage.md`.

---

## 6. Safe Parse Security Invariants

1. **Math Function Whitelist Policy:**
   - `WHITELIST_FUNCS` in `math_engine/answer_check.py` is restricted to standard math functions:
     `sqrt`, `sin`, `cos`, `tan`, `ln`, `log`, `exp`, `abs`, `Abs`, `re`, `im`, `conjugate`.
   - Trusted internal evaluation (`trapDerivation`, `verify.source`, step checks) also allows `TRUSTED_INTERNAL_FUNCS`, which adds `diff`, `floor`, and `round` (e.g., for rounded-down trap values).
   - **Never add CAS/calculus solvers** (`diff`, `integrate`, `solve`, `limit`) to `WHITELIST_FUNCS`, so learners cannot submit symbolic commands that compute the answer for them.
   - Pass problem variables explicitly via `variables=["x"]`.
2. **Bounded Exponent Policy:**
   - **Internal/Trusted Path (`trusted=True`):** capped at $\le 1000$.
   - **User Input — Imaginary Base ($i^N$):** reduced mod 4 in $O(1)$, capped at $\le 1000$.
   - **User Input — Numeric Constant Base ($2^N$):** capped at $\le 1000$.
   - **User Input — Symbolic Base ($(x+1)^N$):** capped strictly at $\le 100$ to avoid exponential polynomial expansion DoS.
   - Nested exponentiation (`9**9**9`, `(9**9)**9`) and out-of-bounds exponents must return `invalid input`.

---

## 7. New Answer Types Checklist

When adding a new `answerSpec` type (e.g., `vector`, `matrix`), update every layer that validates, checks, or redacts answer specs:
1. **`math_engine/answer_spec_registry.py`:** Register the type in `ANSWER_SPEC_TYPES` with required/optional fields and examples.
2. **`math_engine/answer_check.py`:** Add the type-specific checker, bracket/Unicode normalizers, deterministic timeout-bounded diagnostics, and dispatch in `check_answer()`.
   - Keep diagnostics domain-aware: whole-sign hints mention `$i^2 = -1$` only for complex expressions; solution-set hints mention both signs only for symmetric roots.
3. **`math_engine/verify.py`:** Add verification against `verify.source` (analytical SymPy + numerical fallback).
4. **`quality_rules.py`:** Update G1 (anti-leak token extraction), G2, G4, and G6 for the new spec shape.
5. **`practice-studio/src/types/drill.ts`:** Declare the matching TypeScript `AnswerSpec` interface.
6. **`practice-studio/src/lib/redact.ts`:** Update `STRIPPED_ANSWER_SPEC_FIELDS` and `collectSecretAnswerTokens` so answers never leak to the browser.
7. **`math_engine/ai_drill_ingest.py`:** Update `_trap_matches_spec` and ingest contract checks for the new type.
8. **`code_engine/answer_check.py`:** Update the checker and dispatch when the answer type is used by PRG.
9. **`practice-studio/src/components/math/MathWorkspace.tsx`:** Add input UI when the type needs a new control.
10. **Tests:** Add parity, parser bounds, edge cases, Unicode normalization, redaction, and ingest/checker tests.

---

## 8. Reporting Protocol

1. **Report only what changed in this run:** Name the exact files modified and deleted.
2. **Never silently relax thresholds:** Keep gate criteria, parser limits, and timeouts intact.
3. **Separate verified facts from assumptions:** Clearly distinguish commands actually executed and their raw outcomes from static code inspection.
4. **Be concise:** Summarize results directly without filler.
