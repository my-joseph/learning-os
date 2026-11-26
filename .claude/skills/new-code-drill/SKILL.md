---
name: new-code-drill
description: Create a new verified programming drill (PRG-*) from a short brief — inspect the unit page, vault_report and weak_spots, pick reasoning-vault archetypes, write the draft JSON, run --check, run a blind-solve subagent and a reviewer subagent, ingest into drills/data and workspace, run pytest, sync pristine record to Notion, and ship a drill-only PR with branch and PR handling per `rules/00_core.md` §10. Use when asked to make, generate, write or add code problems, a programming drill, or practice for a PRG unit or chapter.
---

# New code drill

Goal: a PRG drill that matches what the learner asked for and passes every gate on the first ingest, with no hand-fixing afterwards. The learner studies these drills, so they never see drafts, prompts, hidden tests or solutions before practising: do not show them drafts, answers or previews, and do not ask them to approve. Mistakes you, the blind solver, or the reviewer catch go into the issue log (`rules/00_core.md` §11), not into questions to the learner. Run everything from the repo root with `.venv/bin/python` and call tools as modules (`.venv/bin/python -m pytest`, `-m ruff`; `.venv/bin/pip` is broken). **Keep answers and code out of the terminal**: subagents write their results to files and reply only `done`, because their replies are shown to the learner. Talk to the learner in polite Thai; everything written into drills and vaults is English. Never edit `drills/workspace/` or `progress/` by hand.

## 1. Brief

Take the brief from the request; ask only if the unit is missing or no vault exists for it.
- **Scope**: a unit (`PRG-T01-C01-U01`) or a chapter (`PRG-T01-C01`). A **unit drill** uses only that unit's archetypes, never another unit's. A **chapter drill** mixes the archetypes of all its units. Use the scope code as the draft's `unitCode`.
- **Context to inspect first**:
  1. Read the unit's Notion page via `id_map.json` (`from notion_sync.client import load_env, require_token, get_all_blocks; token = require_token(load_env().get("NOTION_TOKEN")); blocks = get_all_blocks(page_id, token)`) and its curriculum row in `docs/prg_curriculum_v2.md` (`Learning Objective`, `Expected Output`, `Practice Type`, `Prereqs`).
  2. Run `.venv/bin/python -m scripts.vault_report <UNIT> --log` to see proven vs. failing levels; `(vault)` records are counted at the archetype's base level.
  3. Run `.venv/bin/python -m scripts.weak_spots <UNIT>` to see open weak spots (`matchedTrap >= 2`, ESLint rules, `QC-*` findings, and the `NEXT` line). Target open weak spots when present.
- **Count, levels & mix**: default 4–6 problems across the levels the vault supports (e.g. L1–L3/L4/L5), or matching the requested `difficulty`. Per `rules/07_problem_generation.md`, any drill of `>= 4` problems must include level spread (when `difficulty` is `ALL`) and at least one non-implement item (`fix-bug`, `refactor`, `predict-output`, or `trace-explain`).
- **Environment preset**: `node-vanilla` (JS) or `typescript-strict` / `backend-sqlite` / `react-dom` (TS) per the curriculum row.

State the brief in one line and continue without waiting.

## 2. Load only the rules this task needs

Read `rules/00_core.md` §5–§6, §8, §11; `rules/04_code.md` (Part 1, Part 2, Part 5, Part 10); `rules/06_quality_contract.md` §1.2, §2.2; `rules/07_problem_generation.md` §4; and `docs/prg_reviewer_spec.md`.

## 3. Pick archetypes from the vault

```bash
.venv/bin/python -m code_engine.ai_drill_ingest --unit <UNIT> --list-vault
.venv/bin/python -m scripts.vault_report <UNIT> --log
```

- Every archetype used must be in scope for `<UNIT>` and have valid `qualityChecks` (`R2` rubric). If you add or update an archetype in `code_engine/reasoning_vault/<CHAPTER>.json`, run `.venv/bin/python -m code_engine.quality_checks --check-vaults` before continuing.
- Pick a `commonTrapTag` from each archetype's `cognitiveTraps`.
- Rotate `context` domains: avoid anything in `usedContexts`, and never use two problems with the same `(archetypeKey, context)` in one drill. Never use toy identifiers (`foo`, `bar`, `baz`, `test1`, `funcA`).

## 4. Write the draft as JSON

Write to `scratch/drafts/<UNIT>-<short-slug>.json` (gitignored).

Top level: `unitCode`, `unitTitle`, `environment`, `sourceAttribution`, `config` (`{"questionCount": N, "difficulty": "ALL" | "1".."5", "difficultyMode": "AI Synthesized Engineering Mode"}`), `problems: [...]`. No `drillId` (assigned on ingest).

Per problem:
- `id`: `"Q01"`, `"Q02"`, ...
- `level`: integer (`1`–`5`), `category`: e.g. `"Core Skill"`, `"Trap & Edge Case"`, `"Refactor & Design"`.
- `archetype`: `"problem-solving"` | `"debugging"` | `"refactoring"` | `"code-tracing"`.
- `codeType`: `"implement"` | `"fix-bug"` | `"refactor"` | `"predict-output"` | `"trace-explain"` (match the curriculum row's `Practice Type`, and include `>= 1` non-implement item when `count >= 4`).
- `archetypeKey`, `commonTrapTag` (must exist in that archetype's `cognitiveTraps`), `context` (realistic production domain), `entryPoint`.
- `prompt`: structured Markdown (> 250 chars requires sections `**...**`/`###`, bullets `- `, and backticks `` ` ``; zero wall-of-text; no `Defect Analysis:`/`Root Cause:` spoon-feeding). Choice prompts never list the options; options live only in `answerSpec.options` (Studio and Notion render them).
- `inputHint` / `checkpointHint`: zero-leak (`rules/00_core.md` §6, `rules/04_code.md` §7) — never reveal the answer, bug line, or internal data structures (`secondary Map`, `use closure`).
- `starterCode`: compiles/parses cleanly, passes Layer 2 ESLint with the drill's config (stubs must not import unused modules), has stub bodies (or realistic buggy code for `fix-bug`) that **fail at least one visible test**, and does not contain `solutionCode` or `// BUG:` / `// FIX HERE:` comments. Fix-bug/refactor starters with intentional lint issues must declare per-problem `starterLintExpected: [{rule, reason}]` and state in `prompt` that the structure must be improved too (`refactor`, `simplify`, `split`, `complexity`).
- `solutionCode`: passes all `visibleTests` + `hiddenTests`, and passes Layer 2 ESLint (`tools/lint/base.js`) + `tsc --noEmit` (for TS presets).
- For multi-file `predict-output` ESM snippets, put imported local modules in an optional `files` map (`filename` → source text); the gate writes these beside the runnable `codeSnippet` in a temporary directory.
- `trapMutant`: a plausible wrong solution embodying `commonTrapTag` that compiles/parses cleanly and **FAILS `hiddenTests`**.
- `visibleTests`, `hiddenTests`: every problem must have at least one visible edge case suited to its contract (empty, `0`, `null`, negative, or an equivalent boundary/remaining-input case); hidden tests add further coverage. `--check` prints a warning when public tests contain no recognizable edge input. Any test with `setTimeout > 50ms` must use an injectable clock (`options.now`). Visible test names must not leak the solution.
- `examples`: 2–3 LeetCode-style I/O examples `[{"input": "...", "output": "...", "explanation": "...", "call": "..."}]` (**normal cases only** — never reuse `hiddenTests` inputs or the problem's `commonTrapTag` trap case). `input` and `output` are JS/TS literal display strings; `explanation` is optional body prose; `call` is an executable JS/TS expression (e.g. `"searchInsert([1,3,5,6], 5)"`) verified against `solutionCode` by `--check` (stripped before browser delivery). (Pure `code-tracing`/`predict-output`/`trace-explain` problems with a fixed `codeSnippet`, or without `solutionCode`/`visibleTests`, are exempt from `examples` to avoid spoiling the answer.)
- `constraints` (optional): `string[]` listing input bounds/limits whenever the input has limits (e.g. `["1 <= items.length <= 10^4"]`).
- `steps`: concise explanation steps (`[{"explain": "..."}]`); `verificationLevel: "partial"`.

### Code fences in Studio

- Use `{lines}` to point a worked step at the line it explains. Use 1-based line numbers and inclusive ranges. In a prompt, highlight only details the learner is already given. Keep the bug location, answers, and hidden cases out of the prompt.
- Use `title="…"` on each file in a multi-file example so the learner can tell which snippet belongs to which file. Combine it with line highlighting when both are useful.
- Use a `terminal` fence for expected CLI output. Prefix command lines with `$ `. In a prompt, use CLI examples only when the output is already part of the public contract and does not give away the answer.

````markdown
```js {2}
const options = { format: "text" };
printOptions(options);
```

```js title="app.js"
import { settings } from "./settings.js";
```
```js title="settings.js"
export const settings = { format: "text" };
```

```terminal
$ node app.js --version
1.2.0
```
````

## 5. Pre-flight check (`--check`)

```bash
.venv/bin/python -m code_engine.ai_drill_ingest --check scratch/drafts/<file>.json
```

Run this before spawning subagents to catch any scope, contract, no-leak, starter, solution, `trapMutant`, lint/`tsc`, rubric, or mix errors early. At this stage, only `blindSolve` and `review` should be reported missing. Fix everything else first.

## 6. Blind solve (independent subagent)

Spawn **one** fresh subagent. Give it **ONLY** each problem's `id`, `prompt`, `starterCode`, and `visibleTests` (never `solutionCode`, `hiddenTests`, `trapMutant`, `commonTrapTag`, or `level`). Tell it to write its solutions to `scratch/reviews/<draft-name>-blind.json` as a JSON list `[{"problemId": "Q01", "solutionCode": "...", "ambiguous": false, "note": "..."}]` and reply only `done`.

Copy that JSON list directly into `draft["blindSolve"]` (never show the code to the learner). The `--check` script runs each `solutionCode` against both `visibleTests` and `hiddenTests` with `code_engine.test_runner`, rejects `ambiguous: true` or any solution byte-identical (after whitespace normalisation) to the reference `solutionCode`, and decides pass/fail. On `--ingest-file`, the script strips all blind-solver `solutionCode` and keeps only `[{"problemId": "Q01", "passed": true}, ...]` as provenance.
- If `--check` fails blind solve or flags `ambiguous: true`, tighten the prompt/starter/visible tests once and re-run blind solve.
- If it still fails, drop the problem, log it with `.venv/bin/python -m scripts.issues add --kind level|prompt --source gate --action dropped --where <UNIT>/<id> --what "..."`, and replace it.

## 7. Automated review (reviewer subagent)

Spawn **one** fresh reviewer subagent for the whole draft. Give it the brief, the draft path, `rules/04_code.md`, `rules/07_problem_generation.md` §4, and `docs/prg_reviewer_spec.md`. Tell it to write its verdict to `scratch/reviews/<draft-name>-review.json` and reply only `done`.

Ask it to check the whole draft for:
1. **No leaks**: `prompt`, `starterCode`, `inputHint`, `checkpointHint`, `examples`, and `visibleTests[].name` never reveal the solution, bug location, hidden-test inputs, or `commonTrapTag` cases (`examples` must show 2–3 normal cases only for coding problems — tracing/predict-output with a fixed `codeSnippet` may omit them — plus `constraints` when the input has limits).
2. **Realistic domains**: production domains, no `foo`/`bar`/`test1`, no duplicate `(archetypeKey, context)`.
3. **Rubric & Layer 3**: every archetype's `qualityChecks` fits the problem, and `solutionCode` has zero `must` findings.
4. **Mix & levels**: matches the brief, level spread, and `>= 1` non-implement item when `count >= 4`.
5. **Unit scope & traps**: `archetypeKey` in unit scope, `commonTrapTag` in `cognitiveTraps`, `trapMutant` genuinely embodies `commonTrapTag`.

It writes `{"verdict": "pass" | "fix", "note": "<one sentence>"}` (plus optional per-problem notes). Copy `{"verdict": ..., "note": ...}` into `draft["review"]`.
- On `fix`, fix once, re-run `--check` (and blind solve if any prompt changed), and ask the same reviewer to re-check.
- Log every `fix` and drop with `.venv/bin/python -m scripts.issues add ... --source reviewer --action auto-fixed|dropped`.

## 8. Final `--check`, ingest, and test

```bash
.venv/bin/python -m code_engine.ai_drill_ingest --check scratch/drafts/<file>.json
.venv/bin/python -m code_engine.ai_drill_ingest --ingest-file scratch/drafts/<file>.json
.venv/bin/python -m pytest -q
```

`--check` must print `OK` and exit `0`. Ingest assigns `DRL-<UNIT>-NN`, stamps `unitCode`/`chapterCode`/`topicCode`, updates `usedContexts` in the vault, materialises `drills/workspace/<DRILL_ID>/`, and writes `drills/data/<UNIT>/<DRILL_ID>.json`.

Run the **full** `pytest` suite after ingest. Never sync or push a drill with a failing test.

Log every friction item from the run with `.venv/bin/python -m scripts.issues add ...`.

Report to the learner in polite Thai in a few lines, **without prompts, code, or answers**: drill ID, number of problems per level/type, and any issue-log IDs.

## 9. Sync, then ship (in this order)

1. Register the pristine drill overview and Practice Studio link in Notion from the repo root. Question and solution blocks require saved attempt evidence.
   ```bash
   .venv/bin/python -m notion_sync.drill_sync drills/data/<UNIT>/<DRILL_ID>.json
   ```
   Report a partial sync with the steps listed in `failedSteps`. A degraded result means registration could not be confirmed.
2. Create a branch `drill/<DRILL_ID>` (never on `main`), commit **only** the new drill file under `drills/data/<UNIT>/`, its unit/chapter vault file, and `id_map.json`, push, and open a PR (`gh pr create`).
3. Verify the PR diff and CI result, then follow `rules/00_core.md` §10 for delivery. Do not repeat or expand the policy here.

## Final documentation check

- [ ] If this PR changes system behaviour, the matching rules/*.md, docs/*.md, CLAUDE.md and skills are updated in the same PR.

## Self-review

After the run, compare the outcome against this skill's goal. For each friction (unclear step, missing tool, gate miss, rework, reviewer catch, or learner correction), log `.venv/bin/python -m scripts.issues propose --target skill:new-code-drill --evidence "<what happened>" --proposal "<concrete change>"` (or `.venv/bin/python -m scripts.issues add --kind <kind> --severity batch --source author --where <where> --what "<what>" --target skill:new-code-drill`). If the fix is a small, scoped edit to this `SKILL.md`, make it in the same PR.
