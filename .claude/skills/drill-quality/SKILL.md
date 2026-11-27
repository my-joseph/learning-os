---
name: drill-quality
description: Evaluate real learner practice across drills, levels, traps, and Similar variants. Use when the learner says "ตรวจคุณภาพโจทย์ <UNIT|CHAPTER>" or "drill quality".
---

# Drill quality

Use recorded practice as evidence about whether drills and the vault are working. Speak to the learner in polite Thai; write the report in Thai. Never include prompts, answers, worked steps, hidden tests, or source solutions in the report.

## 1. Read-only inputs

- Read the requested unit/chapter's drills, reasoning vault, Similar variant bank, and local progress. `scripts.drill_quality` honors `PROGRESS_DIR` and `LEARNINGOS_PILOT` through `progress_store`; do not read or write outside that selected progress root.
- PRG quality-check outcomes come from `state.reviews[]` in progress. Count each review's pass/fail verdict; do not infer rubric outcomes from hidden tests.
- Never write to Notion or learner progress. Keep all generated report files outside `progress/`.

## 2. Run the evidence reports

Run the requested scope through each applicable read-only command:

1. `.venv/bin/python -m scripts.drill_quality <UNIT|CHAPTER>` (use `--json` for detailed metrics).
2. `.venv/bin/python -m scripts.weak_spots <UNIT|CHAPTER>`.
3. `.venv/bin/python -m scripts.vault_report <UNIT|CHAPTER>`.
4. `.venv/bin/python -m math_engine.variant_bank --coverage <UNIT|CHAPTER>` for MTH/PHY.
5. `.venv/bin/python scripts/audit_solution_leaks.py <UNIT> --display` for a unit; treat display-only findings as advisory and do not reproduce flagged content.

`vault_report` counts `--log` records ending in `(vault)` at the archetype's base level, alongside explicit `@Ln` issue-log records.

The quality script reports per archetype and level (scoped to the current practice cycle `cycleStartedAt` via the shared `progress_store.score_problem` / `cycle_evidence` semantics): items and attempts, first-try clean rate, hint/step/solution reveal use, skips, recorded time, score distribution, matched traps, Similar openings, and untouched drills. It flags levels that are too easy (at least 90% clean across 3+ items) or too hard (at most 30% clean across 3+ items), never-triggered traps, undrilled archetypes, Similar banks never opened, and L1–L4 ladder gaps. Zero-data results are evidence gaps, not poor learner performance.

## 3. Make concrete recommendations

Cross-check the reports, then recommend specific next actions without leaking content:

- Which archetype/level to step up, lower, or scaffold, citing its count and clean rate.
- Which named trap to inspect or rewrite when wrong attempts never match it.
- Which missing archetype or level to drill next; distinguish never drilled from attempted with no clean evidence.
- For PRG, state which QC check pass/fail counts suggest review work and use `reviews[]` evidence only.
- Call out active Similar variants that have never been opened, and drills with no recorded attempt. Quarantined variants are excluded from this flag.

Keep findings evidence-based and separate system/content issues from learner decisions. Do not reveal an answer while explaining a recommendation.

## 4. Stop before authoring

Drill or vault changes are not part of this audit. New recommendations may feed `new-math-drill`, `new-code-drill`, or vault edits only after the learner gives the go-ahead. Never author, ingest, or sync content in this skill.

## Final documentation check

- [ ] The Thai report cites scope, evidence counts, recommendations, and missing data without exposing prompts, solutions, or hidden tests.

## Self-review

After the run, compare the outcome against this skill's goal. For each friction (unclear step, missing tool, gate miss, rework, reviewer catch, or learner correction), log `.venv/bin/python -m scripts.issues propose --target skill:drill-quality --evidence "<what happened>" --proposal "<concrete change>"` (or `.venv/bin/python -m scripts.issues add --kind <kind> --severity batch --source author --where <where> --what "<what>" --target skill:drill-quality`). If the fix is a small, scoped edit to this `SKILL.md`, make it in the same PR.
