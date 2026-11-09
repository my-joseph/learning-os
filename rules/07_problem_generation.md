# 07_PROBLEM_GENERATION — Drill Composition, Weak-Spot Targeting, Progression & AI-Written Problem Verification

**Module Code:** `RULES-PROBLEM-GEN`
**Applies To:** Deciding what a drill contains, and verifying problems not produced by a tested template
**Prerequisite:** `rules/00_core.md`, `rules/02_pedagogy.md`, `rules/06_template_contract.md`
**Does not redefine:** levels L1–L4, trap provenance, gates G1–G6, reporting (see 06 §2, §3, §4, §9)

## 1. Scope and composition
- A drill's scope is the Unit the learner selects. Add no skills outside it, except hard prerequisites (`skills_taxonomy.json`) for prior-blend items.
- Composition mirrors the Unit Practice Guide (02 §8): core skills, prior-unit blend, traps and edge cases, applied.
- Default drill of 8: 3 core (L1–L2, at least 1 reverse), 2 trap (L3), 2 prior-unit blend, 1 applied (L4). If the Unit lacks enough distinct problems at a level, lower the count; never duplicate (06 §2.1, G3).

## 2. Weak-spot targeting
- Sources, most to least reliable: (1) mistake tags with `trapMatched` in >= 2 attempts, (2) `concept-gap` skips, (3) the learner's Mistake & Pitfall Log (02 §7), (4) learner statement. `unclassified` wrong answers are data to inspect, not a weakness label. `durationMs` and `hintsRevealed` are supporting signals only.
- With >= 1 weak spot: up to 4 of 8 slots use `--focus-tag` (new surface, same misconception, >= 1 reverse form); the rest stay core and review. With no data: use the default drill and collect data.
- A weak spot closes after 2 consecutive drills with all its items correct; any `trapMatched` for that tag reopens it.

## 3. Progression
- Starting level from `Mastery (0-4)` (01 §7): 0–1 -> L1–L2; 2 -> L2–L3; 3 -> L3–L4; 4 -> L4 plus spaced review.
- Move up when the last 5 items at a level score >= 80% including >= 1 reverse; move down when < 50%. Requested levels follow 06 §2.1.
- Difficulty comes from reasoning, not arithmetic size.

## 4. Problems not produced by a tested template
- Allowed for conceptual, formula-selection and word-heavy items. Procedural skills use templates.
- Required: typed givens and a solution; prompt and answer derived from the same givens; every number in the prompt is a given; `trapDerivation` built from the learner's wrong step (06 §3).
- V1 automatic: `verify_problem`, round-trip through `check_answer`, trap != answer and trap judged `incorrect`, anti-leak, G6, no duplicates.
- V2 blind solve: a separate session receives only the prompt and returns an answer; compare through `check_answer`. Mismatch or "ambiguous" = reject. Without V1 and V2 the problem is `verificationLevel: "partial"`, never `machine-verified`.
- V3 human: the learner reads the first 3 items of every new AI-written type (06 §8 checklist).

## 5. Test drills
- A throwaway drill (telemetry or UI testing) is generated with `NOTION_DRY_RUN=1` and deleted afterwards, so that, if the generator performs Pristine Sync (00 §8 Phase C), no Notion record is created.
