# Architectural Deprecation & Archive Notice

**Subsystem**: `math_engine/templates/`  
**Status**: `DEPRECATED / ARCHIVED` (as of Phase 4 Curriculum Modernization)  
**Superseded By**: 
- Reasoning Vaults: `math_engine/reasoning_vault/*.json`
- Autonomous Ingest & Contract Guard: `math_engine/ai_drill_ingest.py`
- Rules & Contract Governance: `rules/06_template_contract.md`, `rules/07_problem_generation.md`

---

## 1. Context & Motivation

Historically (Phase 1), drills were synthesized using procedural Python template functions in `math_engine/templates/mth_t01_cXX.py` that picked random numbers within predetermined ranges.

This pattern suffered from fundamental architectural limitations:
1. **Lack of Mental Models**: Did not capture student misconception archetypes or domain models.
2. **Repetition Vulnerability**: Generated synthetic collisions and lacked dynamic context deduplication.
3. **Format Inconsistencies**: Lacked display equations, LaTeX wrapping, and standard provenance verification.

## 2. Current Architecture (Phase 4 Standards)

1. **Reasoning Vaults (`math_engine/reasoning_vault/`)**:
   - Each unit contains $\ge 10$ archetypes detailing governing invariants, cognitive traps, and mental models.
   - Dynamic context memory tracking (`usedContexts`) prevents repetition.
2. **AI Problem Contract Guard (`math_engine/ai_drill_ingest.py`)**:
   - Two-way givens matching.
   - Zero-number hints.
   - Display equations for KaTeX rendering.
   - Safe parsing and evaluation of cognitive trap derivations.
3. **Active Production Drills (`drills/data/`)**:
   - All 20 active drill sets across mathematics and programming are 100% verified and decoupled from procedural template scripts.

## 3. Maintenance Policy

- Files in this directory are frozen and maintained exclusively for regression tests (`tests/test_sweep_mth_t01.py`, `tests/test_quality_gates.py`).
- **No new templates should be added here.** All new drill generation must pass through `ingest_ai_drill` or `ingest_ai_code_drill`.
