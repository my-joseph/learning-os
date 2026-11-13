---
name: new-math-drill
description: Create a new verified math drill (MTH-*) from a short brief — pick reasoning-vault archetypes, write the problems as a JSON draft, run every ingest gate with --check, show the learner a preview to approve, then ingest into drills/data. Use when asked to make, generate, write or add math problems, a math drill, or practice for a MTH unit or chapter.
---

# New math drill

Goal: a drill that matches what the learner asked for and passes every gate on the first ingest, with no hand-fixing afterwards. Run everything from the repo root with `.venv/bin/python` (or `python3` if that is the active venv). Talk to the learner in Thai; everything written into the drill is English.

## 1. Brief (confirm before writing anything)

Collect, asking only for what is missing:
- **Unit** code, e.g. `MTH-T01-C12` (must have `math_engine/reasoning_vault/<UNIT>.json`).
- **Levels** (L1–L5) and **count** (default 10).
- **Focus** (optional): specific archetypes, trap tags / weak spots, or contexts to use or avoid.

Restate the brief in one line and wait for a yes. A wrong brief is the main reason drills miss what the learner wanted.

## 2. Load only the rules this task needs

Read `rules/00_core.md` §5–§7, `rules/03_stem.md`, `rules/06_template_contract.md` and `rules/07_problem_generation.md` §4. Do not load the other modules.

## 3. Pick archetypes from the vault

```bash
.venv/bin/python -m math_engine.ai_drill_ingest --unit <UNIT> --list-vault
```

- Use only archetypes at the requested levels. If the brief needs one that is not in the vault, stop and propose the new archetype (key, level, coreConcept, governingRelation, cognitiveTraps) to the learner first.
- Choose a surface context per problem that is **not** in that archetype's `usedContexts`.
- Look at one recent drill in `drills/data/<UNIT>/` for the exact field shape (e.g. `DRL-MTH-T01-C12-04.json` Q01).

## 4. Write the draft as JSON

Write to `scratch/drafts/<UNIT>-<short-slug>.json` (gitignored). Never author problems as Python string literals: `"\frac"` in Python silently becomes form-feed + `rac`. In JSON, write LaTeX backslashes doubled (`"\\frac{1}{2}"`).

Top level: `unitCode`, `topicTitle`, `unitTitle`, `subject: "MATH"`, `problems: [...]`. No `drillId` (assigned on ingest).

Per problem, the rules that fail most often:

| Field | Rule |
|---|---|
| `prompt` | States the situation, **never the method**. No substituted formula (`using $P = 2(14) + 2(8)$`), no numbers re-listed by role (`with coefficient $5$, constant $15$`), no hand-over arithmetic (`using $90 - 34$`). The expression itself is fine when evaluating it *is* the task (`Solve $5x + 15 = 60$.`). Numbers in `$...$`. |
| `givens` | Every number in the prompt, and every given appears in the prompt. |
| `constants` | Numbers that belong to the method, not the story: formula constants (2 in `2L + 2W`, 1/3 in cone volume, 90, 180) and derived values. Never put them in the prompt just to satisfy a rule. |
| `trapDerivation` / `trapValue` | A real misconception; uses ≥ 2 values from `givens`/`constants`; evaluates exactly to `trapValue`; `trapValue` must be graded incorrect. `trapGivens` values appear in the prompt or `constants`. |
| `checkpointHint` | Zero digits. A relationship or self-check, not a number. |
| `steps` | One transformation per step, never `A = B = C`; each has `latex` and an action `explain`; at least one step has a machine check (`"val"` or `"eq"`). |
| `display` / `plainText` | Hidden behind "Show equation set-up" until the learner opens it or answers. For word problems prefer the general relation (`A = L \cdot W`) over the substituted one. |
| `verificationLevel` | `"partial"`. |
| `figure` | If the archetype declares `figureBuilders`, the figure is auto-attached; otherwise supply one or a `figureWaiver`. |

Also set `id` (`Q01`…), `level`, `archetype`, `archetypeKey`, `context`, `category`, `answerSpec`, `answerPlain`, `answerDisplay`, `commonTrapTag`, `references: ["<UNIT>"]`.

## 5. Check every gate (writes nothing)

```bash
.venv/bin/python -m math_engine.ai_drill_ingest --unit <UNIT> --ingest-file scratch/drafts/<file>.json --check
```

It lists every failing problem at once. Fix them all and re-run until it prints `OK`. Do not show the learner a draft that has not passed.

## 6. Preview and get approval

Show a compact table: id, level, archetype, prompt (short), answer, trap value. Point out anything that bends the brief. Wait for the learner's approval or edits; re-run step 5 after any edit.

Optional (recommended for L3+ or new archetypes, when the learner agrees): blind-solve each prompt in a separate subagent that sees only the prompt, and compare its answer with `answerSpec`. Any mismatch or "ambiguous" means fix or drop the problem.

## 7. Ingest

```bash
.venv/bin/python -m math_engine.ai_drill_ingest --unit <UNIT> --ingest-file scratch/drafts/<file>.json
.venv/bin/python -m pytest -q tests/test_quality_gates.py -k active_drills
```

Ingest assigns the drill ID, writes `drills/data/<UNIT>/<DRILL_ID>.json` and records the used contexts in the vault. Report the drill ID and path.

## 8. After ingest

- Commit the drill and the vault change on a branch (never on `main`); open a PR when the learner asks.
- Ingest fills `topicCode`, `chapterCode` and missing `levelLabel`s. Do not patch drill fields by hand to make a sync pass: if the sync reports missing fields, fix the cause (ingest or the draft) and say so.
- Sync to Notion only when the learner asks, and **after the PR is merged**, so Notion matches `main`. Run it from the main checkout that holds `.env` (Studio "Sync to Notion" or `notion_sync.drill_sync.sync_drill_to_notion`). Never copy `.env` into a worktree. A result with `degraded: true` means Notion was **not** updated; report it as not synced.
