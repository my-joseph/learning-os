---
name: new-math-drill
description: Create a new verified math drill (MTH-*) from a short brief — pick reasoning-vault archetypes, write the problems as a JSON draft, run every ingest gate with --check, have a reviewer subagent check the whole draft, then ingest into drills/data and sync to Notion with branch and PR handling per `rules/00_core.md` §10. Use when asked to make, generate, write or add math problems, a math drill, or practice for a MTH unit or chapter.
---

# New math drill

Goal: a drill that matches what the learner asked for and passes every gate on the first ingest, with no hand-fixing afterwards. The learner studies these drills, so they never see answers before practising: do not show them drafts, answers or previews, and do not ask them to approve. Mistakes you or the reviewer catch go into the issue log (`rules/00_core.md` §11), not into questions to the learner. Run everything from the repo root with `.venv/bin/python` and call tools as modules (`.venv/bin/python -m pytest`, `-m ruff`, `-m pip`; the `.venv/bin/pip` launcher is broken). **Keep answers out of the terminal**: subagents write their results to files and reply only `done`, because their replies are shown to the learner. Talk to the learner in Thai; everything written into the drill is English.

## 1. Brief

Take the brief from the request; ask only if the unit is missing or no vault exists for it. Defaults:
- **Scope**: a unit (`MTH-T01-C04-U03`) or a chapter (`MTH-T01-C04`). A **unit drill** uses only that unit's archetypes, never another unit's, so the learner can drill one weak unit on its own. A **chapter drill** mixes the archetypes of all its units. Archetypes belong to a unit through their `unitCode` (or by living in a unit vault file such as `MTH-T02-C01-U01.json`); the ingest CLI's `--list-vault` and `vault_report` show the scope. Use the scope code as the draft's `unitCode`.
- **Levels** and **count**: every level the vault has (usually L1–L5), 2 problems each, unless the request says otherwise. Plain prompts unless word problems are asked for.
- **Focus** (optional): specific archetypes, trap tags / weak spots, or contexts to use or avoid.
- **Feedback signals (default step for every drill):** run `.venv/bin/python -m scripts.authoring_signals <UNIT>` (read-only, aggregates only — zero answers, prompts, notes, or drill/question/issue locators; add `--no-progress` for offline/audit runs). It combines `scripts.weak_spots`, `scripts.drill_quality`, recurring recent-mistake tags, and unit-scoped `issues/log.jsonl` records. Use its open traps, level advice, mastery cap, and difficulty/ladder flags when selecting archetypes and levels, and pass that aggregate summary verbatim in the worker spec when delegating authoring.
- **Weak-spot drill**: when the learner asks what to practise or says "ดูจุดอ่อน", run `.venv/bin/python -m scripts.weak_spots [SCOPE]` and show its output (it has no answers). A request "focused on <trap>" (the script's `NEXT` line) makes a weak-spot drill: use only archetypes in scope whose `cognitiveTraps` include that tag, make it the `commonTrapTag` of every problem (or a diagnose option's `trapTag`), include at least one reverse-form problem, and set top-level `"focusTags": ["<trap>"]` in the draft. Keep 1–2 tags per drill (`rules/07` §2). Use the unit from the `NEXT` line as the scope. **Levels for a weak-spot drill** come from the script's `levels` line for that unit, not the default: 2 problems per level from the archetypes' base level up to and including the lowest level marked `down` (that is where the weakness shows), never above it; if no level is marked `down`, go one level above the highest `stay`. At least 4 problems.
- **Bridge drill** (trigger `"ขอโจทย์ผสม"` / `"bridge drill"`): run `.venv/bin/python -m scripts.bridge_scope` first (read-only). If it reports `dormant` (< 2 passed units at mastery ≥ 2) or has no eligible bridge archetypes, tell the learner in polite Thai which units are already passed and which units still need passing, and **stop** — never invent or force a bridge drill. Otherwise use scope `MTH-BRIDGE` (`--unit MTH-BRIDGE --list-vault` lists only eligible bridge archetypes), author **L3+ problems only** (each with `blindSolve` and `review`), set `references` and `unitCodes` to all of the archetype's `unitCodes`, and tag at least one step per unit via `steps[].unit` (enforced by `--check` and ingest; saved to `drills/data/MTH-BRIDGE/DRL-MTH-BRIDGE-NN.json`).

State the brief in one line and continue without waiting. Do not stop to ask during the run. If part of the brief cannot be met (a level the vault lacks, an archetype that never reaches its level), ship what can be made, log the gap (`--kind level --action open`) and say so in the final report.

## 2. Load only the rules this task needs

Read `rules/00_core.md` §5–§7, `rules/03_stem.md`, `rules/06_quality_contract.md` and `rules/07_problem_generation.md` §4. Do not load the other modules.

## 3. Pick archetypes from the vault

```bash
.venv/bin/python -m math_engine.ai_drill_ingest --unit <UNIT> --list-vault
.venv/bin/python -m scripts.vault_report <UNIT> --log
.venv/bin/python -m scripts.vault_report <UNIT> --usage
```

`vault_report` shows, from evidence only, which levels each archetype has **earned** in ingested drills and where it **failed** (issue-log `level` records), and flags `FAILING@Ln` and `UNPROVEN`. `--log` puts `FAILING` into the issue log for the next batch. The report counts those `(vault)` records at the archetype's base level. `--usage` compares current drills and active variants with retired drills. It lists `UNUSED` and `HIST-ONLY` first when history is available. With `--no-history` or a shallow checkout, it shows `UNKNOWN` for archetypes with no current usage evidence.

- **An archetype is a skill, not a level.** Its `level` is the base level (the skill used directly). Build a problem on it at any level from the base upward: L1 direct, L2 reverse or translate, L3 diagnose or a real case to rule out, L4 a model from two or more relations plus a check. The gates (blind solve for L3+) decide whether the level was earned.
- **Prefer unused archetypes and unserved levels:** unless a weak-spot focus or brief names specific archetypes, pick `UNUSED` and `HIST-ONLY` archetypes (and levels not yet served in current drills) from `vault_report <UNIT> --usage` before repeating already-served `(archetypeKey, level)` pairs.
- **Quarantined variants check (mandatory):** inspect `vault_report <UNIT>` for a `Quarantined variants: N` line. If quarantined legacy variants exist in this unit, run `.venv/bin/python -m math_engine.variant_bank --reverify <UNIT>` before authoring Similar variants: re-verify (`--reverify <UNIT> --apply` for items passing every current gate with cached source pages) or replace them with fresh reviewed variants. Quarantined variants are never served and never count toward `--coverage-gate`.
- Choose by evidence: prefer an archetype that has already earned the level you need; trying a new level is fine; avoid an archetype at a level where it is `FAILING` unless its `levelNote` says how to earn it. Read every `levelNote`.
- Unit scope with too few archetypes for the brief, or none at all: add archetypes for that unit first (next bullet), writing them to `math_engine/reasoning_vault/<UNIT>.json` with `unitCode` set, then continue. Never borrow another unit's archetypes for a unit drill.
- New unit, or a unit without archetypes: first check `docs/backlog.md` for engine gaps in that topic and fix or report them. Build the vault from the unit's OpenStax section per `rules/07` §4 "Curriculum Baseline": one L1–L2 archetype per learning objective first, then L3+ archetypes that go beyond the book. Cite the section in each archetype's `source`; never copy or paraphrase OpenStax exercises.
- Default to plain prompts: state the math directly in one short sentence (e.g. "Simplify $(5 + 3i)(7 - 4i)$. Write the answer as $a + bi$.") with no story and an empty `context`. Do not wrap a computation in a made-up scenario ("in a signal demodulator, a weight is ...").
- Use a real-world context only when the learner asks for word problems, or when the level needs the solver to build the relation from a situation (`setup: model`, usually L4–L5). The context must be physically correct (units, sign conventions, plausible magnitudes) and not in that archetype's `usedContexts`.
- Mix forms: at most 2 diagnose-form ("which line is wrong") problems per drill, and never all L3 problems in that form.
- **Start from the template**: copy `.claude/skills/new-math-drill/template/draft.json` and change the content. It has one problem of each shape (L1 plain, L2 reverse, L3 diagnose, L4 word problem with `contextCheck`, `blindSolve` and `edgeRejected`) in the exact field format the gates accept (`givens` is a dict, `steps[].eq` is `[lhs, rhs]`, choice options use `id`, `display` has no `$`, `trapDerivation` uses literal numbers). `tests/test_skill_template.py` keeps it passing. Its levels and verdicts only illustrate the shape; every draft needs its own blind solve and review.

## 4. Write the draft as JSON

For distractor provenance pitfalls and authoring rules, see `docs/lessons/distractor_provenance.md`.

Write to `scratch/drafts/<UNIT>-<short-slug>.json` (gitignored). Never author problems as Python string literals: `"\frac"` in Python silently becomes form-feed + `rac`. In JSON, write LaTeX backslashes doubled (`"\\frac{1}{2}"`).

Top level: `unitCode`, `topicTitle`, `unitTitle`, `subject: "MATH"`, `problems: [...]`. No `drillId` (assigned on ingest).

Per problem, the rules that fail most often:

| Field | Rule |
|---|---|
| `prompt` | States the situation, **never the method**. No substituted formula (`using $P = 2(14) + 2(8)$`), no numbers re-listed by role (`with coefficient $5$, constant $15$`), no hand-over arithmetic (`using $90 - 34$`). The expression itself is fine when evaluating it *is* the task (`Solve $5x + 15 = 60$.`). Numbers in `$...$`. Choice prompts never list the options; options live only in `answerSpec.options` (Studio and Notion render them), except L3 diagnose problems with `verify.flaw` which show `Line N: $...$` lines (`rules/06` §2.3). |
| `givens` | Every number in the prompt, and every given appears in the prompt. |
| `constants` | Numbers that belong to the method, not the story: formula constants (2 in `2L + 2W`, 1/3 in cone volume, 90, 180), and derived values. A `0` in the prompt (`= 0`, `> 0`) needs no entry. Never put them in the prompt just to satisfy a rule. |
| `trapDerivation` / `trapValue` | A real misconception; uses ≥ 2 values from `givens`/`constants`; evaluates with SymPy from `givens`/`constants` to `trapValue`; `trapValue` must be graded incorrect (and differ from `verify.source`). **Derive it from the `commonTrapTag`**: write down, in words, the wrong step the tag names (e.g. `c12-square-diameter-instead-of-radius-trap` → "squares the diameter"), apply only that mistake to the givens, and use the result. The tag **must be one of the archetype's `cognitiveTraps`** (the gate rejects anything else, including tags borrowed from another archetype), and when the vault defines a SymPy-evaluable `trapFormula` over `givens`, `trapDerivation` must use those givens and match `trapFormula`; if no listed trap fits, add the new trap to the unit's vault file first (and log/report the vault addition) instead of stopping mid-run to ask the learner. On non-flaw `choice` problems, **every distractor option (`id != correct`) must carry a vault `trapTag` of the archetype and a `provenance`** (write a SymPy expression in `provenance` over `givens`/`constants` that evaluates to that option's value and differs from the correct answer; prose-only `provenance` or qualitative prose labels without a symbolic formula emit an `"unverifiable"` warning), the correct option must not carry a `trapTag`, and at least one distractor must carry `commonTrapTag` with value matching `trapValue`. |
| `trapGivens` | **Required for `MTH-T01-C01` and `MTH-T01-C12`** (G4 fails without it); add it everywhere. List the numbers used in `trapDerivation`; at least 2 must appear in it. Each must appear in the prompt or in `constants`. Exponents and formula numbers (the `2` in `r^2`, the `1/3` in cone volume, the `3` in `^(1/3)`) are not prompt givens: leave them out of `trapGivens`, or declare them in `constants` if you list them. |
| `checkpointHint` | Zero digits. A relationship or self-check, not a number. It must not give away the key step: on a diagnose problem never name the kind or place of the error (no "check the sign", "watch the units", "look at the whole and fractional parts"); use a process-only hint such as "Check whether each line keeps the same value as the line above it." On a modelling problem do not state the relation to build. (The reviewer sent back three hints for this in the first runs.) |
| `steps` | Write one transformation per step and avoid chains like `A = B = C`. Each step needs `latex` and an action `explain`. Include a machine check in at least one step. New L2 drills and newly added Similar variants need ≥ 4 real steps, matching `demand_level`. The gate compares each mathematical line against the given expressions and all prior lines. It ignores presentation boxes, text labels, style commands, delimiter sizing, and trailing punctuation. It compares aligned rows individually and treats equivalent fraction and multiplication notation, reordered terms, flipped equation sides, and extra braces as duplicates. Genuine arithmetic and algebraic transformations still count. `python -m math_engine.ai_drill_ingest --l2-step-gate` checks the corpus with the grandfathered entries in `tests/data/l2_step_floor_baseline.json`. Under-labelling (demand level above `level`, `form: "reverse"` at L1, `form: "diagnose"` or `verify.flaw` below L3, or `level < arch["level"]` below L3) is rejected across all levels. In `explain`, wrap equations, quantities (including signed numbers), variables, and symbols in `$...$`, as in `Replace $i^2$ with $-1$.` (`rules/03_stem.md` §2). `"val"` must equal the final answer, so put it only on the last step; check intermediate results with `"eq"`. |
| `display` / `plainText` | Hidden behind "Show equation set-up" until the learner opens it or answers. For word problems prefer the general relation (`A = L \cdot W`) over the substituted one. `plainText` is the CAS copy line for typed answers only: omit it on `choice` problems (incl. diagnose); ingest drops it there. |
| `level` | What solving the problem demands of a student at this stage (`rules/06` §2.3), not just what passes G2. For L3+ the hard rule is the floor: no problem the learner could do as direct computation or mental math. L4 means building a model from ≥ 2 relations the prompt does not state, plus choosing a method or checking a case; L5 needs an idea no taught method provides. Repeating an L2 calculation ×N, adding a `constraints` line, switching `category` to `Interleaved Synthesis`, or bolting on "if it fits report X, otherwise report 0" does not raise the level (the gate rejects that last one). A single-unit L4 keeps an honest `category`: its `blindSolve` satisfies G2. |
| L3 diagnose form | Ask *which line is wrong*, never *what the correct value is* (a value question is just recomputing → L1). Show the work in the prompt as `Line N: $...$` lines; `answerSpec` `choice` with options `"1"…"n"`; `verify.flaw` `{values, firstWrong}`; the last line equals `trapValue`; at least 4 lines; each `verify.flaw.values` entry is that line's value as one expression (no `=`). "Wrong" means the line's value is wrong, so a method error must change the value on that same line (write the wrong denominator there, not a value-preserving `(3+4i)/(3+4i)`). Use the archetype name `problem-solving`. Full spec: `rules/06` §2.3 "Diagnose form". |
| `review` | Required by ingest: `{"verdict": "pass", "note": "..."}` from the reviewer in step 7. Leave it out of the draft until then. |
| `contextCheck` | Required when `context` is non-empty: `{"verdict": "ok", "note": "..."}` from the context check in step 5. Leave `context` empty for plain problems. |
| `blindSolve` | **Required for L3+** (the gate rejects the draft without it): `{"answer", "ambiguous", "setup", "strategy", "check", "task", "reverse", "steps"}` (plus `edgeRejected` when `check` is `edge`) copied from the blind solve in step 5. The gate maps the tags to a level, which must reach `level`. Record what the solver said; never edit it to pass. |
| `tolerance` | A plain number is absolute (`0.005` accepts ±0.005). For a relative tolerance write `{"rel": 0.005}`. |
| `answerSpec` `solution_set` | `trapValue` is the set the misconception produces, e.g. `"16"` when only the positive root is taken; `trapDerivation` can express one value only. An omission trap (only the principal angle, only the positive root) is a strict subset of the answer: write the kept value(s) as `trapDerivation` and do not invent constants for it; the 2-givens rule does not apply. Check steps with `eq`, not `val`. Ask for all values directly; do not turn the question into "the sum of all values" to avoid it. |
| `answerSpec` `interval` | For Domain, Range, and inequality solution-set problems, use `{"type": "interval", "value": "[a, b)"}` (use `U` for unions and `-oo`/`oo` or `-inf`/`inf` for infinities; set `answerPlain` to match). `trapValue` is an interval string (e.g. wrong bracket `"(3, 21)"` or omitted union part `"(2, inf)"`), and `trapDerivation` is the matching interval expression (single-given domain problems need only 1 given in `trapDerivation`, and missing union parts count as omission traps). |
| `prompt` vs. trap | Do not state in the prompt what the trap tests (e.g. saying the roots have the form `p ± qi` when the trap is missing the negative discriminant). |
| `form` | Set it on every problem: `direct` (compute forward), `reverse` (given the result, find an input), `diagnose` (which line is wrong) or `choose` (pick or rule out among options). Ingest defaults a missing `form` to `direct`, and `weak_spots` only counts a problem as reverse when `form` is `reverse`, so a reverse problem left unlabelled can never move the learner up a level. |
| `verificationLevel` | `"partial"`. |
| `figure` | Every archetype you use needs a figure decision (`rules/03` §3.1): `figureBuilders` or `figureNone`; the gate rejects the draft otherwise. If it has neither, add one to its vault file now (anything a learner would sketch gets `figureBuilders`). The figure is auto-attached **only when the names in the builder's `args` expressions are keys of your `givens`**; check them before writing `givens`, or add a builder entry with your names. For a reverse problem, size the unknown from the givens and label it `?` (e.g. `"label_h": "h = ?"`) instead of dropping the figure; `figureWaiver` only when even that would give the answer away. |

Also set `id` (`Q01`…), `level`, `archetype`, `archetypeKey`, `context`, `category`, `answerSpec`, `answerPlain`, `answerDisplay`, `commonTrapTag`, `references: ["<UNIT>"]`.

## 5. Blind solve (`rules/07` §4 V2)

Do it for every L3+ problem (L3+ cannot pass step 6 without it). Use **one** subagent for all of them at once; give it only the prompts (no answers, no `level`) and `rules/06` §2.3, tell it to write its results as JSON to `scratch/reviews/<draft-name>-blind.json` and reply only `done`. Wait for that reply; do not poll with short timers or spawn a second solver while it runs. For each prompt ask for (1) the final answer, (2) whether the prompt is ambiguous, (3) the six demand tags of its own solution (`setup`, `strategy`, `check`, `task`, `reverse`, `steps`, using the values in §2.3; do not ask it for a level); if it tags `check: edge`, it must name what the check ruled out (`edgeRejected`), or else tag `none`, and (4) what a typical wrong answer would be. Then:
- Answer differs from `answerSpec`, or "ambiguous" → fix or drop the problem.
- The subagent changed its answer mid-reply → treat as ambiguous: tighten the wording and re-run.
- Its tags map below what the gate accepts (below `level`; check with `--check` in step 6) → redesign **once** to add real demand (a relation the solver must build, a method to choose, a case to check). If the redesign still falls short, do not ask the learner: drop the problem and log it with `--kind level --source gate --action dropped --where <SCOPE>/<archetypeKey>@L<level>` (this exact `--where` format is what `vault_report` counts as that archetype failing at that level). Never change `category`, add `constraints` or add an "otherwise report 0" clause instead.
- Its typical wrong answer differs from `trapValue` → re-check the trap against the tag (step 4). If `trapValue` is what that tag's mistake produces, keep it; the solver's guess may simply be a different mistake.
For L3+, copy the answer, ambiguity, the six tags and `edgeRejected` (when `check` is `edge`) into the problem's `blindSolve`. Re-run the blind solve after any change to the prompt.

**Context check** (every problem with a non-empty `context`, any level): include those prompts in the same blind-solve subagent call (L1–L2 ones too) and ask whether the story is real, using `rules/07` §4.8: (a) the operation is the law that domain really uses, (b) units and magnitudes are physically possible, (c) removal test: with the domain words stripped, does the problem mean exactly the same? If yes, the story is only a label: ok if literally true (a floor's area), fail if it gives the number a meaning it does not have. Copy its verdict and one-line reason into `contextCheck: {"verdict": "ok" | "fail", "note": "..."}`. On `fail`, fix the story or make the problem plain (empty `context`), then re-check.

## 6. Check every gate (writes nothing)

```bash
.venv/bin/python -m math_engine.ai_drill_ingest --unit <UNIT> --ingest-file scratch/drafts/<file>.json --check
```

It lists every failing problem at once, prints figure-title and distractor-provenance warnings, and states in its final summary whether originality was checked or skipped (and why). Fix every error and re-run until it prints `OK`. To inspect corpus-wide originality skips across math drills and variant banks, run `.venv/bin/python -m math_engine.ai_drill_ingest --originality-summary`.

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


## 8. Ingest

```bash
.venv/bin/python -m math_engine.ai_drill_ingest --unit <UNIT> --ingest-file scratch/drafts/<file>.json
```

Ingest refuses any problem without `review.verdict: pass`. It assigns the drill ID, writes `drills/data/<UNIT>/<DRILL_ID>.json`, records the used contexts in the vault, and prints a non-blocking warning if any `(archetypeKey, level)` pair in the drill has < 3 Similar variants.

## 9. Complete Similar coverage and test before the drill PR

```bash
.venv/bin/python -m math_engine.variant_bank --coverage drills/data/<UNIT>/<DRILL_ID>.json
```

Bring every `(archetypeKey, level)` pair in the new drill to at least three AI-made Similar variants at that exact level. Vary the numbers or form while preserving the archetype and level.

1. Run blind solve (required for L3+, plus context check when non-empty) and reviewer subagent on the variant draft.
2. Append via `.venv/bin/python -m math_engine.variant_bank --add scratch/drafts/<UNIT>-variants.json` and check originality with `.venv/bin/python -m math_engine.variant_bank --check <UNIT> --originality`.

Run the coverage gate and the **full** test suite before syncing or opening the PR. Fix every failure before step 10.

```bash
.venv/bin/python -m math_engine.variant_bank --coverage-gate
.venv/bin/python -m pytest -q
```

CI blocks math drill PRs with any new uncovered pair. Delete any stale pair flagged in `tests/data/variant_coverage_baseline.json` when closing an existing gap. Adding baseline entries is forbidden.

Before reporting, log every friction item from the run: anything you had to guess, a gate or tool that misbehaved (including a workaround you used), a rule that was unclear, a vault gap. Use `.venv/bin/python -m scripts.issues add` with the matching kind; listing it in the report is not enough.

Report to the learner in a few lines and **without answers or prompts**: drill ID, number of problems per level, Similar-bank coverage / variants added, and how many problems the reviewer fixed or dropped (with the issue-log IDs). If anything is `urgent` (`rules/00_core.md` §11), put a warning on the first line.

## 10. Sync, then ship (in this order)

Once step 9 passes, sync to Notion to add the drill's entry to `id_map.json`. Commit the drill, its vault, `id_map.json`, and any variant bank or baseline changes. Push and open the PR, including a `Signals used:` line in the PR body (copy the `Signals used:` line from `scripts.authoring_signals <UNIT>` and note how the brief used it, or `none` when no prior practice data exists).

- Follow the canonical branch, PR, and merge policy in `rules/00_core.md` §10; task-specific instructions may narrow it.
- For a drill-only PR eligible for self-merge under §10, wait for CI to pass the coverage gate before merging. A PR that changes a variant bank or the coverage baseline follows the standard review and merge policy.
- Ingest fills `topicCode`, `chapterCode` and missing `levelLabel`s. Do not patch drill fields by hand to make a sync pass: if the sync reports missing fields, fix the cause (ingest or the draft) and say so.
- Register the new drill’s pristine overview and Practice Studio link in Notion once the tests pass. Question and solution blocks require saved attempt evidence. Run `.venv/bin/python -m notion_sync.drill_sync drills/data/<UNIT>/<DRILL_ID>.json` from the repo root. A worktree reads the main checkout's `.env` automatically. Report a result with `degraded: true` as pending Notion sync. Report a partial sync with the steps listed in `failedSteps`.
- Drill files are content only: never add `state` or `sessionSummary` to them (learner progress lives in `progress/`).

## Final documentation check

- [ ] If this PR changes system behaviour, the matching rules/*.md, docs/*.md, CLAUDE.md and skills are updated in the same PR.

## Self-review

After the run, compare the outcome against this skill's goal. For each friction (unclear step, missing tool, gate miss, rework, reviewer catch, or learner correction), log `.venv/bin/python -m scripts.issues propose --target skill:new-math-drill --evidence "<what happened>" --proposal "<concrete change>"` (or `.venv/bin/python -m scripts.issues add --kind <kind> --severity batch --source author --where <where> --what "<what>" --target skill:new-math-drill`). If the fix is a small, scoped edit to this `SKILL.md`, make it in the same PR.
