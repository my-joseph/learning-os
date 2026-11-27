---
name: start-unit
description: Start studying a math or programming unit (MTH-* or PRG-*) end to end - check engine support, build the unit's reasoning-vault archetypes, write or extend its Notion page to §7a (MTH) or §7b (PRG) without touching the learner's notes, then run or queue the first drill. Use when the learner says they are starting a unit ("เริ่มเรียน MTH-T02-C01-U02", "เริ่มเรียน PRG-T01-C03-U01", "start unit ...") or asks to prepare a unit's page and practice.
---

# Start a unit

Goal: when the learner starts a unit (`MTH-*` or `PRG-*`), everything they need is ready in one run: a Notion page that teaches it (`rules/02_pedagogy.md` §7a for MTH, §7b for PRG), archetypes for that unit in the vault, and a first drill (or handoff to `new-code-drill` for PRG). Work without stopping to ask (log friction instead, `rules/00_core.md` §11). Talk to the learner in Thai; everything written to Notion, the vault and drills is English. The learner studies this material, so never show them drill answers.

## 1. Brief

- The unit code (e.g. `MTH-T02-C01-U02` or `PRG-T01-C03-U01`) must be in `id_map.json`. Read its Notion page (`notion_sync.client.get_all_blocks`) to see whether it is empty, and its properties (`Status`, `Learning Objective`, `Expected Output`, `Resources`).
- **MTH:** Find its OpenStax section (book and section number) from the chapter page or the book's table of contents. Read only the section title and learning objectives; never copy or paraphrase OpenStax exercises or examples (`rules/07` §4 "Curriculum Baseline").
- **PRG:** Read the v2 row in `docs/prg_curriculum_v2.md` (and `docs/prg_migration_map.json`): `Learning Objective`, `Expected Output`, `Practice Type`, and `Prereqs`. Use primary docs (MDN, ECMAScript spec, TypeScript handbook, Node.js docs, React/Next.js docs, PostgreSQL docs, OWASP) as reference only, never copied.

## 2. Engine support (MTH)

Check `docs/backlog.md` for the topic (trig functions, logs, calculus). If the unit needs something listed there, fix it first (code change on a branch, learner's go-ahead to merge) or log it as `tool-gap` and say so in the report.

## 3. Archetypes for the unit

- **MTH:**
  ```bash
  .venv/bin/python -m math_engine.ai_drill_ingest --unit <UNIT> --list-vault
  .venv/bin/python -m scripts.vault_report <UNIT>
  ```
  The report includes failures logged by `vault_report --log` at each archetype's base level and flags any `Quarantined variants: N` in this unit. If quarantined variants exist, run `.venv/bin/python -m math_engine.variant_bank --reverify <UNIT>` and re-verify or replace them before authoring Similar variants.
  If the unit has no archetypes (or too few to cover its learning objectives), add them to `math_engine/reasoning_vault/<UNIT>.json` (`{"unitCode": "<UNIT>", "archetypes": [...]}`), each with `unitCode`, `level` (base level), `name`, `coreConcept`, `mentalModel`, `governingRelation`, `cognitiveTraps` as objects (`trapTag`, `description`, `trapFormula`; older vaults use bare tag strings, which still work, but write objects in new archetypes), `versatileDomains` (only real ones), `usedContexts: []`, `source` (the OpenStax section) and a figure decision: `figureBuilders` for anything a learner would sketch (shapes, graphs, number lines, the complex plane), or `figureNone` with a reason (`rules/03` §3.1). Label the asked-for quantity `?`. One L1–L2 archetype per learning objective first, then archetypes that go beyond the book. Follow the shape of `.claude/skills/new-math-drill/template/MTH-TEMPLATE.json` and existing vaults.

- **PRG:**
  ```bash
  .venv/bin/python -m code_engine.ai_drill_ingest --unit <UNIT> --list-vault
  .venv/bin/python -m scripts.vault_report <UNIT>
  ```
  If the unit has no archetypes (or too few to cover its learning objectives), add them to the chapter vault `code_engine/reasoning_vault/<CHAPTER>.json` (`{"unitCode": "<CHAPTER>", "archetypes": [...]}`), each with:
  - `archetypeKey`, `unitCode` (the v2 unit code `<UNIT>`), `name`, `level` (base level),
  - `coreConcept`, `mentalModel`, `governingInvariant`,
  - `cognitiveTraps` with reproducers,
  - `qualityChecks` per R2 rules (`id` as `QC-<kebab>`, `check` stating a property of the code rather than a mandated API, `why`, `severity`: `"must"` or `"should"`, `knownBad: {"code": "...", "caughtBy": "review" | "lint:<rule-id>"}`, optional `accepted`),
  - `usedContexts: []`.
  Then run `.venv/bin/python -m code_engine.quality_checks --check-vaults` and fix any errors before continuing.

## 4. Source synthesis (MTH & PRG)

Run `.venv/bin/python -m scripts.source_find <UNIT> --plan` (watch for any unregistered-folder warning under `sources/` or `sources/prg/`; builds the budgeted, diverse, ledger-aware `sources/_index/plan_<UNIT>.json`, skipping `scope`-only and `NO-AUTOMATION` families) and `.venv/bin/python -m scripts.source_gap <UNIT>` (which includes carried-forward cards from other units' `laterUnit` / `units` and compares against `math_engine/reasoning_vault/` for MTH or `code_engine/reasoning_vault/` for PRG).
- If `plan_<UNIT>.json` has planned batches **or** carried-forward cards exist for `<UNIT>`, run `.claude/skills/synthesize-source/SKILL.md` steps 3–5:
  - Step 3: run worker batches via `scripts.extract_cards_job <UNIT> --batch <k>` + `tools/agents/run-worker.sh` (with `DONE_FILE`) and check `scripts.source_gap <UNIT> --novelty <batch_jsonl>` after each batch, stopping on saturation (two consecutive batches adding `< 2` new cores) or when the plan budget is exhausted.
  - Steps 4–5 (Claude): review `scripts.source_gap <UNIT>` output, update the reasoning vault (for PRG, run `.venv/bin/python -m code_engine.quality_checks --check-vaults`), and run the vault reviewer subagent so the Notion page and first drill already use the synthesised archetypes, traps, and `QC-*` checks.
- If neither exists, note that in one line and continue. (`synthesize-source` remains callable on its own; PRG Similar/variants are out of scope.)

## 5. Notion page (`rules/02_pedagogy.md` §7a for MTH, §7b for PRG)

Write the page as a JSON spec in `scratch/pages/<UNIT>.json` (block types and text syntax: `python -m notion_sync.unit_page --help`).

- **MTH (§7a):** Read `rules/02_pedagogy.md` §6–§8 and §7a, `rules/03_stem.md` §1 (vertical derivations).
  - Callout with Learning Objective, Expected Output, prerequisites and next unit as `[[CODE]]` mentions, and the Resource as the book's page `[[R0xx]]` plus the section number (find the code with `grep -n OpenStax id_map.json`; Algebra and Trigonometry 2e is `R036`).
  - Every formula gets a `"Why this works"` toggle (3–5 lines from first principles). Add `"Which method when"` only if the unit has two or more methods.
  - Worked examples, headed `Example 1 (L1 — Direct): …`, `Example 2 (L2 — Reverse): …` (or `L2 — Translation`), `Example 3 (L3 — Trap Contrast): …` built on the unit's most important vault trap (❌ wrong line, ✅ right line, one sentence why). Derivations as `eq` blocks with `\begin{aligned}`, one transformation per line.
  - Figures: section 1 has at least one `figure` block unless the unit is pure symbol work; this includes equation units, where a graph shows how many solutions there are or where an extraneous root comes from. Decide this apart from the archetypes' `figureNone` (that protects drill answers; the page shows its answers anyway). For a unit about shapes, graphs, intervals or the complex plane, section 1 has at least one `figure` block and every worked example about a shape or graph shows it (`{"type": "figure", "fn": "build_function_graph_figure", "args": {...}, "caption": "..."}`). Titles are sentence case with math in `$...$`; captions have math in `$...$`. The dry run builds and renders every figure; the real run uploads them to Notion.
  - Practice Guide with the 4 categories of §8 (no exercise list); 3–4 Active Recall toggles with vertical reference solutions.

- **PRG (§7b):** Read `rules/02_pedagogy.md` §6–§8 and §7b.
  - Callout with Learning Objective, Expected Output, prerequisites and next unit as `[[CODE]]` mentions, and the primary doc Resource `[[R0xx]]` (link the same `R0xx` with `--set "Resources=R0xx"`). Primary docs are used as reference only, never copied.
  - 1. `Core Concepts & Mental Model`: how it works inside, not only syntax; include a diagram or trace table where it helps, and at least one `code` block (`{"type": "code", "code": "...", "lang": "typescript"}`).
  - 2. `Core Patterns`: each pattern with a `"Why this works"` toggle.
  - 3. `Worked Code Examples`: `Example 1 (L1 — Direct): …`, `Example 2 (L2 — Edge Case): …` (or `L2 — Refactor`), `Example 3 (L3 — Bug Contrast): …` (a wrong version that runs, why it is wrong, and the fix), with `code` blocks.
  - 4. `Practice Guide`: the 4 categories of §8, specifying what the drills train and which rubric checks matter in this unit (cite `QC-`/`U-` ids). Add a one-line learner-facing meaning for every cited `QC-`/`U-` id beside the citation or in a short glossary in the section; never leave internal IDs unexplained.
  - 5. `Active Recall`: 3–4 toggles with reference solutions.
  - Code goes in `code` blocks with a Notion language (`javascript`, `typescript`, `json`, `bash`, `shell`, `sql`, `html`, `css`, `plain text`); inline code in backticks; no math LaTeX unless the unit is about complexity (Big-O may use `$O(n)$`).

- **Both (Section 6 & 7 + writing):**
  - Section 6 `"My Implementation & Mistake Log"` with the three empty prompts of §7 (Feynman one-liner, my working, mistake log), and section 7 `"Completion Checklist & Mastery Review"` (or `"Completion Checklist"`).
  - Dry run first, then real:
    ```bash
    .venv/bin/python -m notion_sync.unit_page --code <UNIT> --spec scratch/pages/<UNIT>.json --mode new --dry-run
    .venv/bin/python -m notion_sync.unit_page --code <UNIT> --spec scratch/pages/<UNIT>.json --mode new
    ```
  - `--mode new` refuses a page that already has blocks. For a page with content (both PRG and MTH), never rewrite it: write a spec for each missing part and insert it with `--mode add --after "<heading text>"`. The tool refuses to touch `"My Implementation"`; never edit, move or delete the learner's notes in any other way either.
  - On older pages (e.g. legacy 5-section pages where `"My Implementation"` was at the end), inserting section 7 puts `"Completion Checklist"` before `"My Implementation"` and leaves heading numbers out of order. Fix both (dry-run first, then real):
    - `--move-section-to-end "Completion Checklist"`: moves the section (and nested children) to the end of the page, refusing if any `to_do` is checked or any block was edited by a person.
    - `--renumber`: rewrites only the leading `N. ` of every `heading_2` to `1..n` in page order (refuses if the section count does not match the standard).
  - Fill every empty property with `--set "Name=value"`: `Learning Objective`, `Expected Output`, `Resources` (`--set "Resources=R0xx"`, added to existing links), and `Status=In progress` if it is `Not started`. Never write to Notion any other way (no direct API calls); if the tool cannot do something, log a `tool-gap`. Do not change `Mastery (0-4)` (drill sync sets it from evidence).
  - Run `.venv/bin/python -m scripts.page_audit <UNIT>` after `--mode add` / `--move-section-to-end` / `--renumber`: it must show 0 FAIL. Fix a FAIL with `--mode add`/`--set`; a WARN is your call, say what you decided in the report.

## 6. First drill and Similar variants

- **MTH:** Run the `new-math-drill` skill for the unit code (unit-only drill, default levels). Complete its required Similar coverage and pass the gate in step 9 before opening the drill PR.
- **PRG:** Say that the `new-code-drill` skill comes next and stop there for now (do not hand-write drills).

## 7. Ship and report

- Delivery follows `rules/00_core.md` §10; task-specific instructions may narrow its merge boundary.
- **PRG:** Open a PR for the chapter vault changes; follow `rules/00_core.md` §10 for delivery.
- Log every friction item (`.venv/bin/python -m scripts.issues add ...`).
- Report in Thai in a few lines, with no problem prompts or answers: the page (new or extended, and which sections; the `page_audit` result), source-synthesis status, archetypes added, the drill ID / variant coverage / PR number (or `new-code-drill` next step for PRG), and issue-log IDs.

## Final documentation check

- [ ] If this PR changes system behaviour, the matching rules/*.md, docs/*.md, CLAUDE.md and skills are updated in the same PR.

## Self-review

After the run, compare the outcome against this skill's goal. For each friction (unclear step, missing tool, gate miss, rework, reviewer catch, or learner correction), log `.venv/bin/python -m scripts.issues propose --target skill:start-unit --evidence "<what happened>" --proposal "<concrete change>"` (or `.venv/bin/python -m scripts.issues add --kind <kind> --severity batch --source author --where <where> --what "<what>" --target skill:start-unit`). If the fix is a small, scoped edit to this `SKILL.md`, make it in the same PR.
