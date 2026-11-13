# math_engine/templates — replay path (not archived)

LearningOS has two ways to produce math problems. They have different jobs:

| Path | Job | Entry point |
|---|---|---|
| **AI + reasoning vault** (primary) | **New** problems: fresh contexts, new archetypes, targeting weak spots. | `.claude/skills/new-math-drill`, `math_engine/ai_drill_ingest.py` (`--check`, then ingest) |
| **Templates** (this folder) | **Replay** a problem structure that already exists, with new numbers, for repeated practice. | `python3 -m math_engine.generate --unit <UNIT> --count <N> --difficulty <D>` |

Templates are procedural: each picks numbers within fixed ranges and computes the answer,
steps and trap in code, so every generated instance is correct by construction. They do not
invent new situations, so they are not the place for variety.

## Policy

- New problem types or contexts go through the AI path first.
- Add or extend a template only to make an existing, already-ingested problem structure
  replayable with new numbers. Follow `rules/06_template_contract.md`.
- Templates are also used by `scripts/sample_sheet.py`, `scripts/capacity_report.py`,
  `scripts/benchmark_templates.py` and the regression tests (`tests/test_sweep_mth_t01.py`,
  `tests/test_quality_gates.py`); keep them passing.
