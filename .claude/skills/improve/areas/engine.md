# Engine assessment playbook

Assess Python and TypeScript engine quality, extension points, and maintainability. Read `rules/00_core.md` and relevant engine rules (`rules/01_arch.md`, `rules/03_stem.md`, `rules/04_code.md`, `rules/07_problem_generation.md`) before inspecting implementation. Keep the assessment read-only. Use the `AUDIT_SHA` pinned in `improve/SKILL.md`; invoke Python as `"$MAIN/.venv/bin/python"` because a worker worktree may not contain `.venv`.

## Scope & Boundary

- **Engine scope:** `math_engine/` (including `variant_bank.py`, `figure_builder.py`, `figure_svg.py`, `figure_autofill.py`, `answer_spec_registry.py`, `source_cores/`), `code_engine/` (`ai_drill_ingest.py`, `lab_ingest.py`, `review_run.py`, `test_runner.py`, `submit.py`, `workspace.py`, `quality_checks.py`, `lint_check.py`), root `quality_rules.py` and `progress_store.py`, and vault evidence (`scripts/vault_report.py`). Include shared Studio engine/type contracts: `practice-studio/src/lib/{scoring,progress,redact,variants,reviewItems,dueToday}.ts`, `practice-studio/src/types/{drill,figure}.ts`, and `practice-studio/src/components/MathFigure/`.
- **Route elsewhere:** Source discovery and card-extraction orchestration (`scripts/source_find.py`, `scripts/extract_cards_job.py`, `scripts/source_gap.py`, stage wall times, token budgets) belong to `areas/pipeline.md`; Studio visual/interaction issues belong to `areas/ux.md`; per-unit archetype/drill authoring gaps belong to `areas/content.md`.

## Inspect

- Trace shared engine logic across `math_engine` and `code_engine`: vault loading/registration, `validate_answer_spec`, `check_choice`/`check_text`, `validate_review`, originality gates, and PRG test/Vitest/ESLint/`tsc` subprocess runners. Do not assume parity.
- Identify oversized multi-responsibility modules and extension points in `answer_check` and `figure_builder`.
- Compare `docs/backlog.md` carefully: topic-specific gaps (trigonometry `T02-C06..C09`, calculus) are trigger-only until that topic starts; active diagnostic/cosmetic observations under “Open cosmetic observations” affect current units and can be Phase 1 findings.
- Check Python/TypeScript parity across:
  1. Scoring and cycle state: `progress_store.py` vs `practice-studio/src/lib/scoring.ts` and `progress.ts`; `scripts/review_items.py` vs `reviewItems.ts`; `scripts/weak_spots.py` vs `dueToday.ts`.
  2. Figure specs and themes: `math_engine/figure_builder.py` and `figure_svg.py` vs `practice-studio/src/types/figure.ts` and `src/components/MathFigure/`.
  3. Answer specs and redaction: `math_engine/answer_spec_registry.py` and `notion_sync/drill_sync.py` vs `practice-studio/src/types/drill.ts` and `src/lib/redact.ts`.
- Measure file size (`wc -l -c`), AST function/branch complexity, recent churn (`git log --since=<7d-ago> --name-only`), duplication, targeted coverage, and fast-suite timings. For timings, use a clean environment with neither `LEARNINGOS_PILOT` nor `NOTION_DRY_RUN`: `env -u LEARNINGOS_PILOT -u NOTION_DRY_RUN "$MAIN/.venv/bin/python" -m pytest -n auto -m "not prg" --durations=20 -q`. Optionally measure PRG separately with `-m prg --durations=10` when runner timings are in scope. Use focused search evidence and state exact commands and scope.
- Do not propose removing legacy templates (`math_engine/templates/`, `code_engine/templates/`, `generate.py`) while the learner's template-removal policy is ON HOLD.
