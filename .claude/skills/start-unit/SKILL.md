---
name: start-unit
description: Start studying a math unit (MTH-*) end to end - check engine support, build the unit's reasoning-vault archetypes from its OpenStax section, write or extend its Notion page to the v4 structure without touching the learner's notes, then make the first drill. Use when the learner says they are starting a unit ("เริ่มเรียน MTH-T02-C01-U02", "start unit ...") or asks to prepare a unit's page and practice.
---

# Start a unit

Goal: when the learner starts a unit, everything they need is ready in one run: a Notion page that teaches it (rules/02 §7a, v4), archetypes for that unit in the vault, and a first drill. Work without stopping to ask (log friction instead, `rules/00_core.md` §11). Talk to the learner in Thai; everything written to Notion, the vault and drills is English. The learner studies this material, so never show them drill answers.

## 1. Brief

- The unit code (e.g. `MTH-T02-C01-U02`) must be in `id_map.json`. Read its Notion page (`notion_sync.client.get_all_blocks`) to see whether it is empty, and its properties (Status, Learning Objective, Expected Output, Resources).
- Find its OpenStax section (book and section number) from the chapter page or the book's table of contents. Read only the section title and learning objectives; never copy or paraphrase OpenStax exercises or examples (`rules/07` §4 "Curriculum Baseline").

## 2. Engine support

Check `docs/backlog.md` for the topic (trig functions, logs, calculus). If the unit needs something listed there, fix it first (code change on a branch, learner's go-ahead to merge) or log it as `tool-gap` and say so in the report.

## 3. Archetypes for the unit

```bash
.venv/bin/python -m math_engine.ai_drill_ingest --unit <UNIT> --list-vault
.venv/bin/python -m scripts.vault_report <UNIT>
```

If the unit has no archetypes (or too few to cover its learning objectives), add them to `math_engine/reasoning_vault/<UNIT>.json` (`{"unitCode": "<UNIT>", "archetypes": [...]}`), each with `unitCode`, `level` (base level), `name`, `coreConcept`, `mentalModel`, `governingRelation`, `cognitiveTraps` as objects (`trapTag`, `description`, `trapFormula`; older vaults use bare tag strings, which still work, but write objects in new archetypes), `versatileDomains` (only real ones), `usedContexts: []` and `source` (the OpenStax section). One L1–L2 archetype per learning objective first, then archetypes that go beyond the book. Follow the shape of `.claude/skills/new-math-drill/template/MTH-TEMPLATE.json` and existing vaults.

## 4. Notion page (rules/02 §7a)

Read `rules/02_pedagogy.md` §6–§8 and §7a, `rules/03_stem.md` §1 (vertical derivations). Write the page as a JSON spec in `scratch/pages/<UNIT>.json` (block types and text syntax: `python -m notion_sync.unit_page --help`). Content rules:
- Callout with Learning Objective, Expected Output, prerequisites and next unit as `[[CODE]]` mentions, and the OpenStax section as the Resource.
- Every formula gets a "Why this works" toggle (3–5 lines from first principles). Add "Which method when" only if the unit has two or more methods.
- Worked examples: L1 direct, L2 reverse (find an input from a result) or translation of a situation, not just a longer procedure, L3 trap contrast built on the unit's most important vault trap (❌ wrong line, ✅ right line, one sentence why). Derivations as `eq` blocks with `\begin{aligned}`, one transformation per line.
- Practice Guide with the 4 categories of §8 (no exercise list); 3–4 Active Recall toggles with vertical reference solutions.
- Section 6 "My Implementation & Mistake Log" with the three empty prompts of §7 (Feynman one-liner, my working, mistake log), and section 7 "Completion Checklist & Mastery Review".

Then:

```bash
.venv/bin/python -m notion_sync.unit_page --code <UNIT> --spec scratch/pages/<UNIT>.json --mode new --dry-run
.venv/bin/python -m notion_sync.unit_page --code <UNIT> --spec scratch/pages/<UNIT>.json --mode new
```

`--mode new` refuses a page that already has blocks. For a page with content, never rewrite it: write a spec for each missing v4 part and insert it with `--mode add --after "<heading text>"`. The tool refuses to touch "My Implementation"; never edit, move or delete the learner's notes in any other way either. If the unit's `Learning Objective` or `Expected Output` property is empty, fill it, and if `Status` is `Not started`, set `In progress`, with `--set "Name=value"` (e.g. `python -m notion_sync.unit_page --code <UNIT> --set "Learning Objective=..."`); relations such as Resources are set in Notion directly. Text syntax: `**bold**` (no `*` inside), `$math$`, `` `code` ``, `[[CODE]]` mentions; no italic. Do not change `Mastery (0-4)` (drill sync sets it from evidence).

## 5. First drill

Run the `new-math-drill` skill for the unit code (unit-only drill, default levels). It ingests, tests, syncs and merges its own PR.

## 6. Ship and report

- Commit the new vault file on the drill's branch (or its own `drill/` branch): a PR that changes only that unit's vault file, the new drill and `id_map.json` may be merged by the agent; anything else (code, rules, other vaults) waits for the learner.
- Log every friction item (`.venv/bin/python -m scripts.issues add ...`).
- Report in a few lines, with no problem prompts or answers: the page (new or extended, and which sections), archetypes added, the drill ID, PR number, and issue-log IDs.
