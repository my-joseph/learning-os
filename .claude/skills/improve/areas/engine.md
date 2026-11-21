# Engine assessment playbook

Assess Python and TypeScript engine quality, extension points, and maintainability. Read `rules/00_core.md` and relevant engine rules before inspecting implementation. Keep the assessment read-only.

## Inspect

- `math_engine/`, `code_engine/`, root `quality_rules.py`, shared ingest gates, originality checks, and vault evidence. Trace shared logic across math and code rather than assuming parity.
- Identify oversized multi-responsibility modules and extension points in `answer_check` and `figure_builder`; compare trig/calculus gaps with `docs/backlog.md`.
- Check Python/TypeScript parity for scoring, validation, saved fields, and any other shared contracts relevant to the focus.
- Measure file size and complexity, recent churn (`git log --since=<date> --stat`), duplication, targeted test coverage, and test timings (`.venv/bin/python -m pytest --durations=20`). Use focused grep/search evidence for duplication; name exact commands and scope.

## Better means

- Clear ownership and smaller responsibilities without losing useful extension points.
- Consistent behavior at Python/TypeScript boundaries, backed by parity tests where applicable.
- Reduced measured duplication, complexity, or test cost without changing behavior accidentally.
- Refactor only behind characterization tests. Report baseline and proposed before/after measures; preserve behavior, keep refactor commits separate from features, and keep tests green at each step.

## Report

For every finding include exact `file:line`, reproduction or measurement, impact, strength to preserve, size/risk, and a bounded test-first remedy. Distinguish observed evidence from hypotheses. Do not expose exercise answers, steps, or hidden tests.
