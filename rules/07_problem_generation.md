# 07_PROBLEM_GENERATION — Drill Composition, Weak-Spot Targeting, Progression & AI-Written Problem Verification

**Module Code:** `RULES-PROBLEM-GEN`
**Applies To:** Deciding which drills to generate, and verifying problems not produced by a tested template
**Prerequisite:** `rules/00_core.md`, `rules/02_pedagogy.md`, `rules/06_template_contract.md`
**Does not redefine:** levels L1–L4, trap provenance, gates G1–G6, reporting (see 06 §2, §3, §4, §9)
**Labels:** `[code]` = enforced by tooling today. `[manual]` = procedure for the agent or learner; no tooling yet.

## 1. Scope and composition
- `[code]` A drill's scope is one Unit (`--unit`). The generator draws only from that Unit.
- [code] Default count is 5. --difficulty takes one level (1-4) or ALL; any other value, or a level the Unit has no templates for, raises ValueError (06 §2.1).
- Composition follows the Unit Practice Guide (02 §8) as a sequence of drills, not a mix inside one drill. `[manual]` Per study session on a Unit:
  1. Core drill: `--difficulty 1` or `2` (or `ALL`), including at least one reverse form.
  2. Trap drill: `--difficulty 3`, or a weak-spot drill (section 2).
  3. Prior-unit review drill: a separate drill on an earlier Unit (no cross-Unit mixing).
  4. Applied drill: `--difficulty 4` when the Unit has L4 templates.
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
- `[manual]` **Autonomous Source Discovery Mandate**: When asked to expand problem archetypes or generate novel problems for a Unit, the AI assistant **must autonomously search, retrieve, and parse authoritative external curricula** (e.g., OpenStax, LibreTexts, AoPS, AMC 8/10, Singapore Math for STEM; RFCs, MDN Web Docs, official language specifications for PRG) via web search or curriculum scrapers. The AI **must never require the learner to provide or upload source materials** unless the learner explicitly offers their own specific problem.
- `[code]` **Reasoning Vault & Gap Analysis**:
  - **Math Vault (`math_engine/reasoning_vault/<unit_code>.json`)**: Novel mathematical structures are extracted into mental models, governing relations, and cognitive traps.
  - **Code Vault (`code_engine/reasoning_vault/<unit_code>.json`)**: Software engineering patterns are recorded with `archetypeKey`, `level`, `coreConcept`, `mentalModel`, `cognitiveTraps` (Bug/Smell Patterns with reproducers), `realWorldDomains`, and `usedContexts`.
  - The AI rotates surface contexts across real-world domains and updates `usedContexts` to prevent context repetition.
- `[code]` **Mandatory AI Contract Guard for Math (`validate_ai_problem_contract`)**:
  1. **Typed Givens**: Every numeric literal appearing in `prompt` (excluding standard year tokens) must map directly to an entry in `givens`.
  2. **Zero-Number Hint (00_core §6)**: `checkpointHint` must contain strictly ZERO numbers from the problem. It must express only abstract mathematical relationships, formulas, or self-monitoring process verification steps (06 §3.4).
  3. **Trap Derivation (06 §3)**: `trapDerivation` must be an operational expression referencing at least 2 distinct givens, evaluate exactly to `trapValue`, and satisfy `check_answer(trapValue) == incorrect` with `trapMatched: True`.
  4. **Strict Verification Level**: All AI-written problems must carry `verificationLevel: "partial"` until verified by a blind solve.
- `[code]` **Mandatory AI Contract Guard for Code (`validate_ai_code_contract`)**:
  1. **Zero Toy Code Guard (04_CODE §5.3)**: Reject `foo`, `bar`, `baz`, `test1`, `funcA`, or meaningless variables in prompt, code, and test suites. Must model realistic production domains.
  2. **Zero Wall-of-Text Guard (04_CODE §4)**: Prompt > 250 characters must be structured with Markdown sections (`**` or `###`), bullet points (`- `), and code identifiers in backticks (`` ` ``).
  3. **Zero-Leak Hint Guard (04_CODE §7)**: `inputHint` and `placeholder` must not leak answer tokens, accepted values, HTTP status codes/methods, or flawed line numbers.
  4. **Dual Pre-Execution Verification**:
     - Canonical solution (`solutionCode`) must run 100% Green on test suites.
     - Starter code (`starterCode`) for debugging problems must fail at least one reproducer test (Red before Green).
  5. **100% Local IDE Scaffolding**: `ingest_ai_code_drill` automatically materializes `drills/workspace/<drillId>/` with `package.json`, `README.md`, and sets `vscodeFolderUrl` / `cursorFolderUrl` pointing to the workspace folder.
- `[code]` V1 automatic: `verify_problem` (G1–G6 item gates) and `validate_ai_problem_contract` / `validate_ai_code_contract`.
- `[manual]` V2 blind solve: a separate session receives only the prompt and returns an answer; compare through `check_answer`. Mismatch or "ambiguous" = reject. Without V1 and V2 the problem remains `verificationLevel: "partial"`, never `machine-verified`.
- `[manual]` V3 human: the learner reads the first 3 items of every new AI-written type (06 §8 checklist).

## 5. Test drills and Notion
- `[code]` The generator never calls Notion; it writes the local file with `syncedToNotionAt: null`. Notion sync happens only from the Practice Studio sync action.
- A throwaway drill (telemetry or UI testing) is never synced and is deleted after the test. Use `NOTION_DRY_RUN=1` for any sync code run during testing.
