# Pipeline assessment playbook

Assess source-to-learning-content flow, retries, and manual work for one bounded pipeline focus. Read relevant source-generation and content rules first. Keep the assessment read-only; never write to Notion or learner progress.

Use the `AUDIT_SHA` pinned by `improve/SKILL.md` for repository evidence and record any difference from current `origin/main`. In a worker worktree, resolve `$MAIN` to the main checkout for shared `pilot/` inputs and run Python as `"$MAIN/.venv/bin/python"`; fresh worktrees do not include the ignored `.venv`.

## Inspect

- Trace source synthesis: `source_find`, `extract_cards_job`, `source_gap`, originality, and OCR; then ingest gates, variant bank, review/sync where relevant.
- Measure stage wall time, model tokens/cost from `$MAIN/pilot/agent-usage.jsonl` when present, failure and retry points, handoffs, and manual steps that could be scripted. State missing instrumentation and sample size; do not invent baselines.
- Inspect current source/backlog and the pinned implementation. Treat reports as leads and verify against main; check for open PRs and learner deferrals before recommending changes.
- Use command `--help` for relevant Python entry points before proposing a command-dependent workflow. Do not run write-producing jobs as part of an assessment.

## Better means

- Less elapsed time or model usage per successfully processed unit, measured at comparable quality.
- Fewer silent failures, retries, and manual handoffs, with clear recovery points.
- Ingest, originality, and review gates retain their safety and quality guarantees.
- Every automation proposal identifies its trigger, inputs, outputs, failure handling, and dry-run/pilot boundary.

## Report

Include a stage map, measured baseline and source, failure/retry evidence, useful safeguards to retain, and bounded improvements with measurable success criteria. Do not include source text, secrets, learner data, or hidden exercise material.
