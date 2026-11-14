---
name: new-math-drill
description: Create a new verified math drill (MTH-*) from a short brief — pick reasoning-vault archetypes, write the problems as a JSON draft, run every ingest gate with --check, have a reviewer subagent check the whole draft, then ingest into drills/data and sync to Notion with no learner approval step. Use when asked to make, generate, write or add math problems, a math drill, or practice for a MTH unit or chapter.
---

# New math drill

Goal: a drill that matches what the learner asked for and passes every gate on the first ingest, with no hand-fixing afterwards. The learner studies these drills, so they never see answers before practising: do not show them drafts, answers or previews, and do not ask them to approve. Mistakes you or the reviewer catch go into the issue log (`rules/00_core.md` §11), not into questions to the learner. Run everything from the repo root with `.venv/bin/python` and call tools as modules (`.venv/bin/python -m pytest`, `-m ruff`, `-m pip`; the `.venv/bin/pip` launcher is broken). **Keep answers out of the terminal**: subagents write their results to files and reply only `done`, because their replies are shown to the learner. Talk to the learner in Thai; everything written into the drill is English.

## 1. Brief

Take the brief from the request; ask only if the unit is missing or no vault exists for it. Defaults:
- **Unit** code, e.g. `MTH-T01-C12` (must have `math_engine/reasoning_vault/<UNIT>.json`).
- **Levels** and **count**: every level the vault has (usually L1–L4), 2 problems each, unless the request says otherwise. Plain prompts unless word problems are asked for.
- **Focus** (optional): specific archetypes, trap tags / weak spots, or contexts to use or avoid.

State the brief in one line and continue without waiting. Do not stop to ask during the run. If part of the brief cannot be met (a level the vault lacks, an archetype that never reaches its level), ship what can be made, log the gap (`--kind level --action open`) and say so in the final report.

## 2. Load only the rules this task needs

Read `rules/00_core.md` §5–§7, `rules/03_stem.md`, `rules/06_template_contract.md` and `rules/07_problem_generation.md` §4. Do not load the other modules.

## 3. Pick archetypes from the vault

```bash
.venv/bin/python -m math_engine.ai_drill_ingest --unit <UNIT> --list-vault
```

- Read each archetype's `levelNote` if it has one: it says how that archetype can (or cannot) earn its level.
- Use only archetypes at the requested levels. If the brief needs one that is not in the vault, skip that part and log it (`--kind level --action open`); new archetypes are added when the issue log is cleared.
- New unit (no vault yet): first check `docs/backlog.md` for engine gaps in that topic and fix or report them. Build the vault from the unit's OpenStax section per `rules/07` §4 "Curriculum Baseline": one L1–L2 archetype per learning objective first, then L3+ archetypes that go beyond the book. Cite the section in each archetype's `source`; never copy or paraphrase OpenStax exercises.
- Default to plain prompts: state the math directly in one short sentence (e.g. "Simplify $(5 + 3i)(7 - 4i)$. Write the answer as $a + bi$.") with no story and an empty `context`. Do not wrap a computation in a made-up scenario ("in a signal demodulator, a weight is ...").
- Use a real-world context only when the learner asks for word problems, or when the level needs the solver to build the relation from a situation (`setup: model`, usually L4–L5). The context must be physically correct (units, sign conventions, plausible magnitudes) and not in that archetype's `usedContexts`.
- Mix forms: at most 2 diagnose-form ("which line is wrong") problems per drill, and never all L3 problems in that form.
- **Start from the template**: copy `.claude/skills/new-math-drill/template/draft.json` and change the content. It has one problem of each shape (L1 plain, L2 reverse, L3 diagnose, L4 word problem with `contextCheck`, `blindSolve` and `edgeRejected`) in the exact field format the gates accept (`givens` is a dict, `steps[].eq` is `[lhs, rhs]`, choice options use `id`, `display` has no `$`, `trapDerivation` uses literal numbers). `tests/test_skill_template.py` keeps it passing. Its levels and verdicts only illustrate the shape; every draft needs its own blind solve and review.

## 4. Write the draft as JSON

Write to `scratch/drafts/<UNIT>-<short-slug>.json` (gitignored). Never author problems as Python string literals: `"\frac"` in Python silently becomes form-feed + `rac`. In JSON, write LaTeX backslashes doubled (`"\\frac{1}{2}"`).

Top level: `unitCode`, `topicTitle`, `unitTitle`, `subject: "MATH"`, `problems: [...]`. No `drillId` (assigned on ingest).

Per problem, the rules that fail most often:

| Field | Rule |
|---|---|
| `prompt` | States the situation, **never the method**. No substituted formula (`using $P = 2(14) + 2(8)$`), no numbers re-listed by role (`with coefficient $5$, constant $15$`), no hand-over arithmetic (`using $90 - 34$`). The expression itself is fine when evaluating it *is* the task (`Solve $5x + 15 = 60$.`). Numbers in `$...$`. |
| `givens` | Every number in the prompt, and every given appears in the prompt. |
| `constants` | Numbers that belong to the method, not the story: formula constants (2 in `2L + 2W`, 1/3 in cone volume, 90, 180), and derived values. A `0` in the prompt (`= 0`, `> 0`) needs no entry. Never put them in the prompt just to satisfy a rule. |
| `trapDerivation` / `trapValue` | A real misconception; uses ≥ 2 values from `givens`/`constants`; evaluates exactly to `trapValue`; `trapValue` must be graded incorrect. **Derive it from the `commonTrapTag`**: write down, in words, the wrong step the tag names (e.g. `c12-square-diameter-instead-of-radius-trap` → "squares the diameter"), apply only that mistake to the givens, and use the result. The tag **must be one of the archetype's `cognitiveTraps`** (the gate rejects anything else, including tags borrowed from another archetype); if no listed trap fits, propose a new trap for the vault to the learner first. If the number you get is not what a learner with that misconception would actually write, or the correct method also gives it, pick another tag. The gates check the arithmetic, not that the value matches the tag. |
| `trapGivens` | **Required for `MTH-T01-C01` and `MTH-T01-C12`** (G4 fails without it); add it everywhere. List the numbers used in `trapDerivation`; at least 2 must appear in it. Each must appear in the prompt or in `constants`. Exponents and formula numbers (the `2` in `r^2`, the `1/3` in cone volume, the `3` in `^(1/3)`) are not prompt givens: leave them out of `trapGivens`, or declare them in `constants` if you list them. |
| `checkpointHint` | Zero digits. A relationship or self-check, not a number. It must not give away the key step: on a diagnose problem never name the kind or place of the error (no "check the sign", "watch the units", "look at the whole and fractional parts"); use a process-only hint such as "Check whether each line keeps the same value as the line above it." On a modelling problem do not state the relation to build. (The reviewer sent back three hints for this in the first runs.) |
| `steps` | One transformation per step, never `A = B = C`; each has `latex` and an action `explain`; at least one step has a machine check. `"val"` must equal the final answer, so put it only on the last step; check intermediate results with `"eq"`. |
| `display` / `plainText` | Hidden behind "Show equation set-up" until the learner opens it or answers. For word problems prefer the general relation (`A = L \cdot W`) over the substituted one. |
| `level` | What solving the problem demands of a student at this stage (`rules/06` §2.3), not just what passes G2. For L3+ the hard rule is the floor: no problem the learner could do as direct computation or mental math. L4 means building a model from ≥ 2 relations the prompt does not state, plus choosing a method or checking a case; L5 needs an idea no taught method provides. Repeating an L2 calculation ×N, adding a `constraints` line, switching `category` to `Interleaved Synthesis`, or bolting on "if it fits report X, otherwise report 0" does not raise the level (the gate rejects that last one). A single-unit L4 keeps an honest `category`: its `blindSolve` satisfies G2. |
| L3 diagnose form | Ask *which line is wrong*, never *what the correct value is* (a value question is just recomputing → L1). Show the work in the prompt as `Line N: $...$` lines; `answerSpec` `choice` with options `"1"…"n"`; `verify.flaw` `{values, firstWrong}`; the last line equals `trapValue`; at least 4 lines; each `verify.flaw.values` entry is that line's value as one expression (no `=`). "Wrong" means the line's value is wrong, so a method error must change the value on that same line (write the wrong denominator there, not a value-preserving `(3+4i)/(3+4i)`). Use the archetype name `problem-solving`. Full spec: `rules/06` §2.3 "Diagnose form". |
| `review` | Required by ingest: `{"verdict": "pass", "note": "..."}` from the reviewer in step 7. Leave it out of the draft until then. |
| `contextCheck` | Required when `context` is non-empty: `{"verdict": "ok", "note": "..."}` from the context check in step 5. Leave `context` empty for plain problems. |
| `blindSolve` | **Required for L3+** (the gate rejects the draft without it): `{"answer", "ambiguous", "setup", "strategy", "check", "task", "reverse", "steps"}` (plus `edgeRejected` when `check` is `edge`) copied from the blind solve in step 5. The gate maps the tags to a level, which must reach `level`. Record what the solver said; never edit it to pass. |
| `tolerance` | A plain number is absolute (`0.005` accepts ±0.005). For a relative tolerance write `{"rel": 0.005}`. |
| `answerSpec` `solution_set` | `trapValue` is the set the misconception produces, e.g. `"16"` when only the positive root is taken; `trapDerivation` can express one value only. An omission trap (only the principal angle, only the positive root) is a strict subset of the answer: write the kept value(s) as `trapDerivation` and do not invent constants for it; the 2-givens rule does not apply. Check steps with `eq`, not `val`. Ask for all values directly; do not turn the question into "the sum of all values" to avoid it. |
| `prompt` vs. trap | Do not state in the prompt what the trap tests (e.g. saying the roots have the form `p ± qi` when the trap is missing the negative discriminant). |
| `verificationLevel` | `"partial"`. |
| `figure` | If the archetype declares `figureBuilders`, the figure is auto-attached **only when your `givens` keys match the builder's `args` names** in the vault JSON (e.g. `base_1`, `base_2`, `height`); check them before writing `givens`. Otherwise supply a figure or a `figureWaiver` with a reason. |

Also set `id` (`Q01`…), `level`, `archetype`, `archetypeKey`, `context`, `category`, `answerSpec`, `answerPlain`, `answerDisplay`, `commonTrapTag`, `references: ["<UNIT>"]`.

## 5. Blind solve (`rules/07` §4 V2)

Do it for every L3+ problem (L3+ cannot pass step 6 without it). Use **one** subagent for all of them at once; give it only the prompts (no answers, no `level`) and `rules/06` §2.3, tell it to write its results as JSON to `scratch/reviews/<draft-name>-blind.json` and reply only `done`. Wait for that reply; do not poll with short timers or spawn a second solver while it runs. For each prompt ask for (1) the final answer, (2) whether the prompt is ambiguous, (3) the six demand tags of its own solution (`setup`, `strategy`, `check`, `task`, `reverse`, `steps`, using the values in §2.3; do not ask it for a level); if it tags `check: edge`, it must name what the check ruled out (`edgeRejected`), or else tag `none`, and (4) what a typical wrong answer would be. Then:
- Answer differs from `answerSpec`, or "ambiguous" → fix or drop the problem.
- The subagent changed its answer mid-reply → treat as ambiguous: tighten the wording and re-run.
- Its tags map below what the gate accepts (below `level`; check with `--check` in step 6) → redesign **once** to add real demand (a relation the solver must build, a method to choose, a case to check). If the redesign still falls short, do not ask the learner: drop the problem and log it (`--kind level --source gate --action dropped`, naming the archetype, so its vault level can be fixed later). Never change `category`, add `constraints` or add an "otherwise report 0" clause instead.
- Its typical wrong answer differs from `trapValue` → re-check the trap against the tag (step 4). If `trapValue` is what that tag's mistake produces, keep it; the solver's guess may simply be a different mistake.
For L3+, copy the answer, ambiguity, the six tags and `edgeRejected` (when `check` is `edge`) into the problem's `blindSolve`. Re-run the blind solve after any change to the prompt.

**Context check** (every problem with a non-empty `context`, any level): include those prompts in the same blind-solve subagent call (L1–L2 ones too) and ask whether the story is real, using `rules/07` §4.8: (a) the operation is the law that domain really uses, (b) units and magnitudes are physically possible, (c) removal test: with the domain words stripped, does the problem mean exactly the same? If yes, the story is only a label: ok if literally true (a floor's area), fail if it gives the number a meaning it does not have. Copy its verdict and one-line reason into `contextCheck: {"verdict": "ok" | "fail", "note": "..."}`. On `fail`, fix the story or make the problem plain (empty `context`), then re-check.

## 6. Check every gate (writes nothing)

```bash
.venv/bin/python -m math_engine.ai_drill_ingest --unit <UNIT> --ingest-file scratch/drafts/<file>.json --check
```

It lists every failing problem at once. Fix them all and re-run until it prints `OK`.

## 7. Automated review (replaces learner approval)

Spawn **one** fresh reviewer subagent for the whole draft. Give it the brief, the draft path and `rules/07` §4 V3. Tell it to write its verdicts as JSON to `scratch/reviews/<draft-name>-review.json` and reply only `done` (its reply is shown to the learner, so it must not contain answers). Ask it to re-solve every problem itself (L1–L2 included) and judge each one on:
1. the answer, trap value and steps are correct;
2. no second reading: units and conventions (e.g. MB = 1000 or 1024 kB, bits vs bytes), rounding, wording;
3. the problem exercises its archetype and `commonTrapTag`;
4. the drill fits the brief: levels, count, plain vs. word problems, at most 2 diagnose problems, no two problems with the same structure;
5. hints and `display` help without giving the answer away.

It returns per problem `{"verdict": "pass" | "fix", "note": "<one sentence>"}`. Copy each verdict into the problem's `review` as given; never edit it.
- `fix` → fix the problem once, re-run steps 5–6 for it, and ask the same reviewer to re-check just that problem (same file, same `done` reply). Still `fix` → drop it and write one replacement (same level), then review that. If the replacement also fails, ship the drill without it and say so in the report.
- Log every `fix` and every drop with `.venv/bin/python -m scripts.issues add ... --source reviewer --action auto-fixed|dropped` (`rules/00_core.md` §11), using the drill's unit and problem id in `--where`. Log a tool gap the same way with `--action open`. Notes in the log must not contain answers.


## 8. Ingest, then test everything

```bash
.venv/bin/python -m math_engine.ai_drill_ingest --unit <UNIT> --ingest-file scratch/drafts/<file>.json
.venv/bin/python -m pytest -q
```

Run the **full** test suite after ingest and before anything leaves the machine. If a test fails, fix the cause (or delete the new drill file) before step 9; never sync or push a drill with a failing test.

Ingest refuses any problem without `review.verdict: pass`. It assigns the drill ID, writes `drills/data/<UNIT>/<DRILL_ID>.json` and records the used contexts in the vault.

Before reporting, log every friction item from the run: anything you had to guess, a gate or tool that misbehaved (including a workaround you used), a rule that was unclear, a vault gap. Use `.venv/bin/python -m scripts.issues add` with the matching kind; listing it in the report is not enough.

Report to the learner in a few lines and **without answers or prompts**: drill ID, number of problems per level, and how many problems the reviewer fixed or dropped (with the issue-log IDs). If anything is `urgent` (`rules/00_core.md` §11), put a warning on the first line.

## 9. Sync, then ship (in this order)

Only after every test in step 8 passed: (1) sync to Notion, which adds the drill's entry to `id_map.json`; (2) commit the drill, its vault and `id_map.json`; (3) push, open the PR and merge it.

- Ship it without being asked (learner decision 2026-11-15): commit on a branch `drill/<drill-id>` (never on `main`), push, open a PR and merge it yourself (`gh pr merge --merge --delete-branch`), then return the checkout to `main` (`git checkout main && git pull --ff-only`). Self-merge is allowed **only** when the PR changes nothing but the new drill file under `drills/data/<UNIT>/`, that unit's vault file and `id_map.json`; check with `git diff --stat origin/main...HEAD` before merging. Anything else (rules, code, tests, other drills) needs the learner's go-ahead.
- Ingest fills `topicCode`, `chapterCode` and missing `levelLabel`s. Do not patch drill fields by hand to make a sync pass: if the sync reports missing fields, fix the cause (ingest or the draft) and say so.
- Sync the new drill's pristine record to Notion once the tests pass (`rules/00_core.md` §8); no need to wait for the merge or ask. Use `notion_sync.drill_sync.sync_drill_to_notion` from the repo root; in a worktree it reads the main checkout's `.env` automatically, so never copy `.env`. A result with `degraded: true` means Notion was **not** updated; report it as not synced.
- Drill files are content only: never add `state` or `sessionSummary` to them (learner progress lives in `progress/`).
