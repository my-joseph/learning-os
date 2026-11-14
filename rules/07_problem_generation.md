# 07_PROBLEM_GENERATION — Drill Composition, Weak-Spot Targeting, Progression & AI-Written Problem Verification

**Module Code:** `RULES-PROBLEM-GEN`
**Applies To:** Deciding which drills to generate, and verifying problems not produced by a tested template
**Prerequisite:** `rules/00_core.md`, `rules/02_pedagogy.md`, `rules/06_template_contract.md`
**Does not redefine:** levels L1–L4, trap provenance, gates G1–G6, reporting (see 06 §2, §3, §4, §9)
**Labels:** `[code]` = enforced by tooling today. `[manual]` = procedure for the agent or learner; no tooling yet.

## 1. Scope and composition
- `[code]` A standard drill's scope is one Unit (`--unit`), or a Synthesis Drill (`MTH-SYNTHESIS`) for multi-topic cross-domain practice.
- `[code]` Default count is 5. `--difficulty` takes one level (1-5) or ALL; any other value, or a level the Unit has no templates for, raises ValueError (06 §2.1).
- Composition follows the Unit Practice Guide (02 §8) as a sequence of drills, not a mix inside one drill. `[manual]` Per study session on a Unit:
  1. Core drill: `--difficulty 1` or `2` (or `ALL`), including at least one reverse form.
  2. Trap drill: `--difficulty 3`, or a weak-spot drill (section 2).
  3. Prior-unit review drill: a separate drill on an earlier Unit (no cross-Unit mixing).
  4. Applied drill: `--difficulty 4` when the Unit has L4 templates.
  5. Synthesis drill: `--difficulty 5` for cross-topic interleaving and non-routine problem solving.
- If the Unit lacks enough distinct problems for the requested count, the generator must raise an error; never duplicate (06 §2.1, G3).

## 2. Weak-spot targeting
- Sources, most to least reliable: (1) mistake tags with `trapMatched` in >= 2 attempts, (2) `concept-gap` skips, (3) the learner's Mistake & Pitfall Log (02 §7), (4) learner statement. `unclassified` wrong answers are data to inspect, not a weakness label. `durationMs` and `hintsRevealed` are supporting signals only.
- `[manual]` Counting tags: on request, the agent counts `mistakes[]` and `attempts[].matchedTrap` across `drills/data`. No script exists yet.
- [code] A weak-spot drill is a separate drill using --focus-tag <tag[,tag]>; the whole drill is drawn from templates and forms matching the tags, and a tag that matches no template raises an error. [manual] Prefer 1–2 tags per drill, and check in the sample sheet that at least one reverse form is included; if not, generate another drill.
- `[manual]` A weak spot closes after 2 consecutive weak-spot drills with all items correct; any `trapMatched` for that tag reopens it. With no data, run the core and trap drills and collect data first.

## 3. Progression
- `[manual]` Starting level from `Mastery (0-4)` (01 §7): 0–1 -> level 1 then 2; 2 -> level 2 then 3; 3 -> level 3 then 4; 4 -> level 4 plus spaced review. A range means consecutive drills, one level each.
- `[manual]` Move up when the last 5 items at a level score >= 80% including >= 1 reverse; move down when < 50%.
- Difficulty comes from reasoning, not arithmetic size.

## 4. Problems not produced by a tested template (AI Generation & Reasoning Vault)
- `[manual]` **Curriculum Baseline (OpenStax) and Original Problems**: when a Unit starts, its OpenStax section sets the scope. Read the section's title and learning objectives and turn them into a skill list; vault archetypes cite the section (`"source": "OpenStax <Book> 2e §x.y"`). Every problem is written from scratch: never copy, translate or paraphrase OpenStax exercises or examples, never change only the numbers or names of one, and never bulk-download or scrape OpenStax pages (2e books are CC BY-NC-SA 4.0, and OpenStax restricts automated and AI ingestion). OpenStax is the floor, not the ceiling: archetypes may go beyond the book (reverse forms, diagnose, synthesis) and may draw on ideas from other sources (AoPS, AMC, LibreTexts; RFCs, MDN and language specs for PRG) under the same no-copying rule. The AI finds these sources itself and never requires the learner to upload material, unless the learner offers a specific problem.
- `[code]` **Reasoning Vault & Gap Analysis**:
  - **Math Vault (`math_engine/reasoning_vault/<unit_code>.json`)**: Novel mathematical structures are extracted into mental models, governing relations, and cognitive traps.
  - **Code Vault (`code_engine/reasoning_vault/<unit_code>.json`)**: Software engineering patterns are recorded with `archetypeKey`, `level`, `coreConcept`, `mentalModel`, `cognitiveTraps` (Bug/Smell Patterns with reproducers), `realWorldDomains`, and `usedContexts`.
  - When a problem does use a story (§4 item 8), the AI rotates contexts across domains and updates `usedContexts` to prevent repetition.
- `[code]` **Mandatory AI Contract Guard for Math (`validate_ai_problem_contract`)**:
  1. **Typed Givens**: Every numeric literal appearing in `prompt` (excluding standard year tokens) must map directly to an entry in `givens` or `constants`, and every entry in `givens` must appear in `prompt` (exponents such as the `3` in `$2^3$` count as appearing).
     - **`constants`** holds numbers that belong to the method, not the story: formula constants (the `2` in $P = 2L + 2W$, the $\frac{1}{3}$ in a cone volume, $90$ for complementary angles, $180$ for a triangle) and values the learner must derive. They never have to appear in `prompt`. A key may not be in both `givens` and `constants`.
     - Never mention a number in `prompt` only to satisfy this rule. If a number is part of the method, put it in `constants`.
  2. **Zero-Number Hint (00_core §6)**: `checkpointHint` must contain strictly ZERO numbers from the problem. It must express only abstract mathematical relationships, formulas, or self-monitoring process verification steps (06 §3.4).
  3. **Trap Derivation (06 §3)**: `trapDerivation` must be an operational expression referencing at least 2 distinct values from `givens` or `constants` (misusing a formula constant, e.g. $2 + r$ instead of $2r$, is a valid trap), evaluate exactly to `trapValue`, and satisfy `check_answer(trapValue) == incorrect` with `trapMatched: True`.
  4. **Strict Verification Level**: All AI-written problems must carry `verificationLevel: "partial"` until verified by a blind solve.
  5. **Granular Step-by-Step Derivation Standard (00_core §7, 03_STEM §1, 06 §2.1)**: Every math problem must provide vertical, line-by-line derivation steps where each step represents a single mathematical transformation. Never chain multiple equalities horizontally ($A = B = C = D$). Every step must include an action-oriented `explain` string.
  6. **Zero-Corrupted-LaTeX Guard (00_core §5)**: Automatically heal and reject any LaTeX escape artifact collisions (`\x0c` / `\f` formfeed, `\r` carriage return, `\x08` backspace).
  7. **No Solution in the Prompt (`check_prompt_does_not_leak_solution`)**: `prompt` states the situation, never the method. Rejected:
     - an unknown set equal to a worked computation: `using $P = 2(14) + 2(8)$`;
     - numbers re-listed by their algebraic role: `..., with coefficient $5$, constant $15$, and target value $60$`;
     - arithmetic handed over: `using $90 - 34$`, `by evaluating $(4 + 16) \div 2$`, or a second `calculate $7 \times 4 + 15$` after the real question.
     Allowed: the expression or equation that *is* the task (`Solve $5x + 15 = 60$.`, `Evaluate $2^3 \times 2^4$.`) and general formulas without substituted numbers (`$A = \pi r^2$`). Audit any unit with `python scripts/audit_solution_leaks.py [UNIT] [--display]`. Drills ingested before this gate are not re-checked.
  8. **Real-world context must be real (`validate_context_check`)**: plain prompts are the default and leave `context` empty. A story is used only for word problems or when the level needs the solver to model a situation, and then a separate reviewer (the blind solver, or its own subagent for L1–L2) judges it on three criteria:
     - **Domain law**: the operation in the problem is the law that domain really uses (series impedances add; complex power is $S = V\bar{I}$; a quantum phase factor has modulus 1). Wrong law = fail.
     - **Units and bounds**: like terms share a unit, products and quotients give the right unit, and given values and the answer are physically possible (resistance ≥ 0, a passive reflection coefficient ≤ 1 in magnitude, a probability in $[0, 1]$).
     - **Removal test**: strip the domain words. If the problem means exactly the same thing, the story is only a label. A label is ok when it is literally true (the area of a triangular gable panel is the triangle's area) and fails when it gives the number a meaning it does not have (calling $4i^2 - 9$ a phase factor, calling a product of two reactances a coupling coefficient).
     The result is stored as `contextCheck: {"verdict": "ok" | "fail", "note"}`; a non-empty `context` without it, or with `fail`, is rejected. On `fail`, fix the story or make the problem plain; never edit the verdict.
- `[code]` **Mandatory AI Contract Guard for Code (`validate_ai_code_contract`)**:
  1. **Zero Toy Code Guard (04_CODE §5.3)**: Reject `foo`, `bar`, `baz`, `test1`, `funcA`, or meaningless variables in prompt, code, and test suites. Must model realistic production domains.
  2. **Zero Wall-of-Text Guard (04_CODE §4)**: Prompt > 250 characters must be structured with Markdown sections (`**` or `###`), bullet points (`- `), and code identifiers in backticks (`` ` ``).
  3. **Zero-Leak Hint Guard (04_CODE §7)**: `inputHint` and `placeholder` must not leak answer tokens, accepted values, HTTP status codes/methods, or flawed line numbers.
  4. **Dual Pre-Execution Verification**:
     - Canonical solution (`solutionCode`) must run 100% Green on test suites.
     - Starter code (`starterCode`) for debugging problems must fail at least one reproducer test (Red before Green).
  5. **100% Local IDE Scaffolding**: `ingest_ai_code_drill` automatically materializes `drills/workspace/<drillId>/` with `package.json`, `README.md`, and sets `vscodeFolderUrl` / `cursorFolderUrl` pointing to the workspace folder.
- `[code]` V1 automatic: `verify_problem` (G1–G6 item gates) and `validate_ai_problem_contract` / `validate_ai_code_contract`.
- `[code]` Vault gate (`validate_against_vault`, run by `--check` and ingest): `archetypeKey` must be in the unit's vault and `commonTrapTag` must be one of that archetype's `cognitiveTraps`, so `trapMatched` only reports misconceptions the vault defines. A new trap is added to the vault (with the learner's approval) before it is used.
- `[manual]` + `[code]` V2 blind solve: a separate session receives only the prompt (plus 06 §2.3) and returns an answer, whether the prompt is ambiguous, the six demand tags of 06 §2.3 (`setup`, `strategy`, `check`, `task`, `reverse`, `steps`) and the most likely wrong answer; it does not pick a level. Compare the answer through `check_answer`. Mismatch, "ambiguous", or an answer changed mid-reply = reject or reword. For every L3+ problem the result is recorded as `blindSolve` and the vault gate maps the tags to a level (`demand_level`) and rejects the problem if that level is below `level`, if `check: edge` names nothing it ruled out (`edgeRejected`), or if the prompt bolts on a sentinel answer ("otherwise report 0"), so a direct-computation problem can never pass as L3+ (G2 counts steps, concepts, `constraints` and `category` but cannot judge demand, so a single-unit L4/L5 with a passing `blindSolve` satisfies G2; changing `category` or adding `constraints` to get past it is not allowed). One redesign at most, then drop the problem and log it (06 §2.3 stop rule). A likely wrong answer that differs from `trapValue` = re-check that the trap matches `commonTrapTag` (G4 checks the arithmetic, not the misconception). Without V1 and V2 the problem remains `verificationLevel: "partial"`, never `machine-verified`.
- `[manual]` + `[code]` V3 automated review (`validate_review`, required by ingest): the learner studies these drills, so they never preview or approve them (a preview would show the answers). Instead a separate reviewer subagent sees the whole draft (prompt, answer, steps, hints) and the brief, re-solves every problem (L1–L2 included) and checks: the answer; ambiguity (units and conventions, rounding, wording); that the problem exercises its archetype and trap; that the drill fits the brief (levels, count, plain vs. word problems, the diagnose cap, variety); and that hints help without leaking. It records `review: {"verdict": "pass" | "fix", "note"}` on each problem. On `fix`, the author fixes the problem once and the reviewer re-checks it; if it still fails, drop it and write one replacement. Every `fix` or drop is logged (`rules/00_core.md` §11). The learner reports problems found while studying the same way.

## 5. Test drills and Notion
- `[code]` The generator never calls Notion; it writes the local file with `syncedToNotionAt: null`. Notion sync happens only from the Practice Studio sync action.
- A throwaway drill (telemetry or UI testing) is never synced and is deleted after the test. Use `NOTION_DRY_RUN=1` for any sync code run during testing.
