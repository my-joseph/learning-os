---
name: synthesize-source
description: Synthesise original math problems and reasoning-vault upgrades from the abstract cores of local source material — never copying, translating, paraphrasing, or reusing numbers. Use when the learner says "สังเคราะห์โจทย์ <UNIT>" or "synthesize problems for <UNIT>".
---

# Synthesise from source cores

Goal: turn local raw material (`sources/`, gitignored) into original, verified reasoning-vault archetypes, drills, and variants for one `<UNIT>` with zero copying, zero paraphrasing, and zero reused numbers. The learner studies the resulting drills, so **never show answers, drafts, or source excerpts to the learner**. Subagents write results to files and reply only `done`. Run everything from the repo root with `.venv/bin/python -m ...`. Talk to the learner in polite Thai; everything written to cards, vaults, drills, and PRs is English.

## 1. Brief & policy check

1. Take `<UNIT>` (and optional focus, exam-style request, or family filter) from the request; ask only if `<UNIT>` is missing. State the brief in one line and continue without waiting.
2. Read `docs/sources.md` and `rules/07_problem_generation.md` §4.
   - **OpenStax is `scope` only** (TOC + learning objectives): **never** extract core cards or mine exercises from OpenStax.
   - Allowed `cores` families (`mathsgenie`, `thai-exams`, `illustrative-math`) are mined for abstract problem cores only — never copy, translate, paraphrase, or reuse numbers.

## 2. Locate candidate pages (`source_find`)

```bash
.venv/bin/python -m scripts.source_find <UNIT> [--terms ...] [--families ...]
```

- Resolves `LEARNINGOS_SOURCES_DIR` (defaults to `<main checkout>/sources` even from a worktree), caches extracted PDF text under `sources/_index/`, and writes `sources/_index/located_<UNIT>.json`.
- Review the three output groups:
  - **Mining targets (`cores`)** — file + pages with hit counts (pass these to step 3).
  - **Scope only (`scope`)** — OpenStax TOC/learning-objective pages to confirm unit boundaries only (never pass to card extraction).
  - **Image pages (`image page — read visually`)** — scanned pages with no extractable text; note their page numbers for visual inspection in step 3.

## 3. Extract source-free core cards (subagent)

Spawn **one** extractor subagent for the located `cores` pages (and relevant scanned pages). Give it:
- The located `cores` file paths and page ranges (use the `Read` tool on PDF pages; inspect scanned pages visually).
- The schema at `math_engine/source_cores/schema.json` and `docs/sources.md`.
- Output path: `sources/_cores/<UNIT>.jsonl` (validate every card with `math_engine.source_cores.validate_core_card(card, source_item_text=...)` before saving).

Mandatory extractor instructions:
- Abstract only the mathematical core (`skill`, `reasoningMove`, `difficultyDriver`, `level`, `traps`, `format`, `representation`, `notes`).
- **No source wording and no source numbers** anywhere in content fields; every string field ≤ 200 characters.
- Record provenance in `sourceRef` (`{family, file, page, item}`) — never `openstax`.
- If a source problem goes deeper than `<UNIT>`'s scope, still keep its core card but set `"laterUnit": "<TARGET_UNIT>"` so it is deferred rather than drilled now.
- If a source item genuinely combines skills from two or more units in one problem (e.g. complex numbers + quadratics), set `"units": ["<UNIT_A>", "<UNIT_B>", ...]` (≥ 2 distinct unit codes) in addition to `unitCode` (and `laterUnit` if any required unit is beyond `<UNIT>`).
- Reply only `done`.

## 4. Gap analysis (`source_gap`)

```bash
.venv/bin/python -m scripts.source_gap <UNIT>
```

Read-only report comparing `sources/_cores/<UNIT>.jsonl` against `math_engine/reasoning_vault/<UNIT>.json`:
- Cards matched to existing archetypes vs unmatched candidate archetypes.
- New trap tags not yet in any archetype.
- Reasoning moves and levels the vault lacks.
- Exam formats seen (e.g. 5-option choice with trap distractors).
- Deferred `laterUnit` cards grouped for future units (leave for later; do not drill now).
- **Bridge candidates**: multi-unit cards (`units`) grouped by unit pair and marked `ELIGIBLE` vs `not eligible` via `scripts.bridge_scope`.

## 5. Update the Reasoning Vault (with reviewer subagent)

Update `math_engine/reasoning_vault/<UNIT>.json` from the gap report:
- Add new archetypes for genuine unmatched cores; extend existing archetypes' `cognitiveTraps`, `levelNote`s, and `usedContexts` (preserving existing fields and figure decisions per `rules/03` §3.1).
- **Bridge archetypes (`MTH-BRIDGE.json`)**: when `source_gap` shows **eligible** bridge candidates (all units in the pair are passed per `scripts.bridge_scope`), add bridge archetypes to `math_engine/reasoning_vault/MTH-BRIDGE.json` with `unitCodes` (≥ 2), `junction` (abstract link where one skill's output feeds the next), `skillsByUnit`, `cognitiveTraps` (junction traps), base `level` ≥ 3, `levelNote`, `figureNone`/`figureBuilders`, and `source`. Leave non-eligible bridge candidates deferred.
- Cite provenance on every added/updated archetype as:
  `"source": "OpenStax <Book> §x.y; cores: <families>"` (e.g. `"OpenStax Algebra and Trigonometry 2e §2.4; cores: mathsgenie, thai-exams"`).
- Spawn **one** fresh reviewer subagent with the vault diff, `docs/sources.md`, and OpenStax unit scope. Ask it to check that every new or updated archetype is (1) 100% original and source-free (no copied wording/numbers), (2) strictly within `<UNIT>` scope (deeper items stayed in `laterUnit`), (3) has valid traps and figure decision, and (4) for any `MTH-BRIDGE.json` addition, that each `junction` is real (one skill's output genuinely feeds the next) and all `unitCodes` are passed per `bridge_scope`. Have it write its verdict to `scratch/reviews/<UNIT>-vault-review.json` and reply only `done`. Fix any flagged items before step 6.

## 6. Generate drills (and optional variants / exam-style set)

Hand off to the `new-math-drill` skill (`.claude/skills/new-math-drill/SKILL.md`) to author, blind-solve, review, ingest, and sync the drill from the updated vault:
- Default: target the new/extended archetypes, traps, and missing reasoning moves identified in step 4.
- **Optional exam-style set** (when requested or when `source_gap` highlights exam choice formats): pass a brief for a TCAS-style 4–5 option `choice` drill where every distractor is derived from a card trap tag (`commonTrapTag`), omitting `plainText` on choice items (`rules/07` §4.9).
- **Optional variant bank**: seed or append distinct gated variants via `.venv/bin/python -m math_engine.variant_bank --add <draft.json>` (`rules/07` §6).

## 7. Originality gate (mandatory)

Every generated drill draft and variant bank must pass the originality gate against `sources/_index/` before ingest:

```bash
.venv/bin/python -m math_engine.ai_drill_ingest --unit <UNIT> --ingest-file scratch/drafts/<file>.json --check --originality
.venv/bin/python -m math_engine.source_cores.originality scratch/drafts/<file>.json --unit <UNIT>
# If variants were added:
.venv/bin/python -m math_engine.variant_bank --check <UNIT> --originality
```

Rejections (8-word shingle overlap, identical prompt number multiset to a source item, or normalised similarity ≥ 0.6) mean rewrite from scratch with fresh numbers and structure — never tweak a few words.

## 8. Test, ship PR, and report in Thai

1. Run `.venv/bin/python -m pytest -q` and `.venv/bin/ruff check . && .venv/bin/ruff format --check .`.
2. Verify `git status` shows **nothing** staged under `sources/` or `scratch/`.
3. Follow `new-math-drill` step 9 for Notion sync (`drill_sync`) and PR workflow:
   - Never commit or push on `main`.
   - Vault + new drill + `id_map.json` only → follows existing self-merge rule (`git diff --stat origin/main...HEAD` must contain only the new drill, that unit's vault, and `id_map.json`).
   - Any other changes (variant banks, scripts, rules, multiple units) → open PR and wait for the learner to say "merge".
4. Report concisely in polite Thai **without showing prompts, answers, or source text**: families scanned, core cards extracted (current vs `laterUnit`), vault archetypes/traps added, drill ID / variant counts, originality gate pass, and PR link/status.
