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
| `constants` | Numbers that belong to the method, not the story: formula constants (2 in `2L + 2W`, 1/3 in cone volume, 90, 180), the `0` in a condition such as `= 0` or `> 0`, and derived values. Never put them in the prompt just to satisfy a rule. |
| `trapDerivation` / `trapValue` | A real misconception; uses ≥ 2 values from `givens`/`constants`; evaluates exactly to `trapValue`; `trapValue` must be graded incorrect. **Derive it from the `commonTrapTag`**: write down, in words, the wrong step the tag names (e.g. `c12-square-diameter-instead-of-radius-trap` → "squares the diameter"), apply only that mistake to the givens, and use the result. The tag **must be one of the archetype's `cognitiveTraps`** (the gate rejects anything else, including tags borrowed from another archetype); if no listed trap fits, propose a new trap for the vault to the learner first. If the number you get is not what a learner with that misconception would actually write, or the correct method also gives it, pick another tag. The gates check the arithmetic, not that the value matches the tag. |
| `trapGivens` | **Required for `MTH-T01-C01` and `MTH-T01-C12`** (G4 fails without it); add it everywhere. List the numbers used in `trapDerivation`; at least 2 must appear in it. Each must appear in the prompt or in `constants`. Exponents and formula numbers (the `2` in `r^2`, the `1/3` in cone volume, the `3` in `^(1/3)`) are not prompt givens: leave them out of `trapGivens`, or declare them in `constants` if you list them. |
| `checkpointHint` | Zero digits. A relationship or self-check, not a number. |
| `steps` | One transformation per step, never `A = B = C`; each has `latex` and an action `explain`; at least one step has a machine check. `"val"` must equal the final answer, so put it only on the last step; check intermediate results with `"eq"`. |
| `display` / `plainText` | Hidden behind "Show equation set-up" until the learner opens it or answers. For word problems prefer the general relation (`A = L \cdot W`) over the substituted one. |
| `level` | What solving the problem demands of a student at this stage (`rules/06` §2.3), not just what passes G2. For L3+ the hard rule is the floor: no problem the learner could do as direct computation or mental math. L4 means building a model from ≥ 2 relations the prompt does not state, plus choosing a method or checking a case; L5 needs an idea no taught method provides. Repeating an L2 calculation ×N, adding a `constraints` line, switching `category` to `Interleaved Synthesis`, or bolting on "if it fits report X, otherwise report 0" does not raise the level (the gate rejects that last one). A single-unit L4 keeps an honest `category`: its `blindSolve` satisfies G2. |
| L3 diagnose form | Ask *which line is wrong*, never *what the correct value is* (a value question is just recomputing → L1). Show the work in the prompt as `Line N: $...$` lines; `answerSpec` `choice` with options `"1"…"n"`; `verify.flaw` `{values, firstWrong}`; the last line equals `trapValue`; at least 4 lines. "Wrong" means the line's value is wrong, so a method error must change the value on that same line (write the wrong denominator there, not a value-preserving `(3+4i)/(3+4i)`). Use the archetype name `problem-solving`. Full spec: `rules/06` §2.3 "Diagnose form". |
| `blindSolve` | **Required for L3+** (the gate rejects the draft without it): `{"answer", "ambiguous", "setup", "strategy", "check", "task", "reverse", "steps"}` copied from the blind solve in step 5. The gate maps the tags to a level: L4/L5 must reach `level` exactly, L3 may be one below. Record what the solver said; never edit it to pass. |
| `answerSpec` `solution_set` | `trapValue` is the set the misconception produces, e.g. `"16"` when only the positive root is taken. Ask for all values directly; do not turn the question into "the sum of all values" to avoid it. |
| `prompt` vs. trap | Do not state in the prompt what the trap tests (e.g. saying the roots have the form `p ± qi` when the trap is missing the negative discriminant). |
| `verificationLevel` | `"partial"`. |
| `figure` | If the archetype declares `figureBuilders`, the figure is auto-attached **only when your `givens` keys match the builder's `args` names** in the vault JSON (e.g. `base_1`, `base_2`, `height`); check them before writing `givens`. Otherwise supply a figure or a `figureWaiver` with a reason. |

Also set `id` (`Q01`…), `level`, `archetype`, `archetypeKey`, `context`, `category`, `answerSpec`, `answerPlain`, `answerDisplay`, `commonTrapTag`, `references: ["<UNIT>"]`.

## 5. Blind solve (`rules/07` §4 V2)

Do it for every L3+ problem and every new archetype (L3+ cannot pass step 6 without it). In a separate subagent that sees only the prompt and `rules/06` §2.3, ask for (1) the final answer, (2) whether the prompt is ambiguous, (3) the six demand tags of its own solution (`setup`, `strategy`, `check`, `task`, `reverse`, `steps`, using the values in §2.3; do not ask it for a level), and (4) what a typical wrong answer would be. Then:
- Answer differs from `answerSpec`, or "ambiguous" → fix or drop the problem.
- The subagent changed its answer mid-reply → treat as ambiguous: tighten the wording and re-run.
- Its tags map below what the gate accepts (L4/L5: below `level`; L3: below L2; check with `--check` in step 6) → redesign **once** to add real demand (a relation the solver must build, a method to choose, a case to check), or relabel. If the redesign still fails, stop: show the learner the author's intent and the solver's tags in plain words and let them choose relabel or drop. Never change `category`, add `constraints` or add an "otherwise report 0" clause instead. If relabelling would leave the drill off the requested levels, ask the learner before relabelling.
- Its typical wrong answer differs from `trapValue` → re-check the trap against the tag (step 4). If `trapValue` is what that tag's mistake produces, keep it; the solver's guess may simply be a different mistake.
For L3+, copy the answer, ambiguity and the six tags into the problem's `blindSolve`. Re-run the blind solve after any change to the prompt.

## 6. Check every gate (writes nothing)

```bash
.venv/bin/python -m math_engine.ai_drill_ingest --unit <UNIT> --ingest-file scratch/drafts/<file>.json --check
```

It lists every failing problem at once. Fix them all and re-run until it prints `OK`. Do not show the learner a draft that has not passed.

## 7. Preview and get approval

Show a compact table: id, level, archetype, prompt (short), answer, trap value, and the blind-solve answer, ambiguity, tags and mapped level. Point out anything that bends the brief. Wait for the learner's approval or edits; re-run steps 5–6 after any edit.


## 8. Ingest

```bash
.venv/bin/python -m math_engine.ai_drill_ingest --unit <UNIT> --ingest-file scratch/drafts/<file>.json
.venv/bin/python -m pytest -q tests/test_quality_gates.py -k active_drills
```

Ingest assigns the drill ID, writes `drills/data/<UNIT>/<DRILL_ID>.json` and records the used contexts in the vault. Report the drill ID and path.

## 9. After ingest

- Commit the drill and the vault change on a branch (never on `main`); open a PR when the learner asks.
- Ingest fills `topicCode`, `chapterCode` and missing `levelLabel`s. Do not patch drill fields by hand to make a sync pass: if the sync reports missing fields, fix the cause (ingest or the draft) and say so.
- Sync the new drill's pristine record to Notion **right after ingest** (`rules/00_core.md` §8); no need to wait for the merge or ask. Use `notion_sync.drill_sync.sync_drill_to_notion` from the repo root; in a worktree it reads the main checkout's `.env` automatically, so never copy `.env`. A result with `degraded: true` means Notion was **not** updated; report it as not synced.
- Drill files are content only: never add `state` or `sessionSummary` to them (learner progress lives in `progress/`).
