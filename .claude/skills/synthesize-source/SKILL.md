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
   - Allowed `cores` families (`smartmathpro`, `mathsgenie`, `thai-exams`, `illustrative-math`) are mined for abstract problem cores only — never copy, translate, paraphrase, or reuse numbers.

## 2. Locate, rank & plan candidate pages (`source_find --plan`)

```bash
.venv/bin/python -m scripts.source_find <UNIT> --plan [--budget-pages 30 --budget-items 40] [--batch-size 10] [--refresh] [--terms ...] [--families ...]
```

- Resolves `LEARNINGOS_SOURCES_DIR` (defaults to `<main checkout>/sources` even from a worktree), caches extracted PDF text under `sources/_index/`, writes `sources/_index/located_<UNIT>.json` (for the originality gate), and warns if any top-level folder under `sources/` (excluding `_`-prefixed folders) is not registered in `docs/sources.md` — register its family, licence, allowed use, and `priority` before mining it.
- Writes a bounded extraction plan `sources/_index/plan_<UNIT>.json` (defaults: **30 pages / 40 items** per unit run, split into batches of **10 pages**):
  - Ranked by **(a)** family priority (`docs/sources.md` `Priority` column / `SOURCE_FAMILIES` + `docs/source_backlog.md` rank), **(b)** term-hit density, **(c)** Thai-exam relevance boost (`SmartMathPro`, `thai-exams`), and **(d)** round-robin diversity across families so one source cannot fill the budget.
  - Always skips **`scope`-only** families (`openstax`) — read OpenStax TOC/learning-objective pages only to confirm unit boundaries, never for card extraction.
  - Excludes `(unit, file, page)` entries already recorded in `sources/_cores/_ledger.json` unless the source file's SHA-256 hash changed or `--refresh` is passed, so incremental runs only process newly added or updated sources.
- Review the plan summary (selected pages per family, skipped ledger/scope counts, and batch count). If `selectedPageCount == 0` and carried-forward cards exist, proceed directly to step 4.

## 3. Extract source-free core cards in bounded worker batches (`extract_cards_job` + `run-worker.sh`)

Run extraction in batches (default 10 pages per batch) on a **worker model** (Neon/Argon/Luna via `tools/agents/run-worker.sh` with `DONE_FILE`) rather than a Claude subagent reading raw PDFs — **Claude only reviews `source_gap` output** in steps 4–5.

For each batch `k = 1, 2, ...` in `sources/_index/plan_<UNIT>.json`:

1. Render the worker prompt (embeds batch `k` pages, `math_engine/source_cores/schema.json`, strict no-copy/zero-leak rules, `validate_core_card`, append to `sources/_cores/<UNIT>.jsonl`, `_ledger.json` update, and `DONE_FILE`):
   ```bash
   .venv/bin/python -m scripts.extract_cards_job <UNIT> --batch <k> \
     --batch-out sources/_cores/_batches/<UNIT>-batch-<k>.jsonl \
     --done-file sources/_cores/_batches/<UNIT>-batch-<k>.done \
     --out scratch/prompts/<UNIT>-extract-b<k>.txt
   ```
2. Launch the worker with `DONE_FILE` so `run-worker.sh` stops cleanly once the batch commits:
   ```bash
   DONE_FILE=sources/_cores/_batches/<UNIT>-batch-<k>.done \
     tools/agents/run-worker.sh <worktree> <branch> \
     scratch/prompts/<UNIT>-extract-b<k>.txt \
     scratch/logs/<UNIT>-extract-b<k>.log
   ```
   The worker drafts batch cards into the batch JSONL and runs `.venv/bin/python -m scripts.extract_cards_job <UNIT> --batch <k> --commit <batch_jsonl> --run-id <run_id> --done-file <done_file>`, which validates every card with `validate_core_card(card, source_item_text=...)`, appends new cards to `sources/_cores/<UNIT>.jsonl`, updates `sources/_cores/_ledger.json` for every page in batch `k` (including 0-card pages), and writes `DONE_FILE`.
3. Check batch novelty / saturation:
   ```bash
   .venv/bin/python -m scripts.source_gap <UNIT> --novelty sources/_cores/_batches/<UNIT>-batch-<k>.jsonl
   ```
4. **Saturation & budget stop rule:**
   - Stop early if **two consecutive batches** each add **`< 2` new cores** (same `skill` + `reasoningMove` + `traps`, fuzzy).
   - Otherwise stop when all planned batches (bounded by `--budget-pages` / `--budget-items`) are complete.

Mandatory card invariants (enforced by `validate_core_card` during `--commit`):
- Abstract only the mathematical core (`skill`, `reasoningMove`, `difficultyDriver`, `level`, `traps`, `format`, `representation`, `notes`).
- **No source wording and no source numbers** anywhere in content fields; every string field ≤ 200 characters.
- Record provenance in `sourceRef` (`{family, file, page, item}`) — never `openstax`.
- If a source problem goes deeper than `<UNIT>`'s scope, keep its core card with `"laterUnit": "<TARGET_UNIT>"` using a **real unit/chapter code from `id_map.json`** (unknown codes are warned and rejected unless prefixed `"UNMAPPED:"`; remap older files with `.venv/bin/python -m scripts.source_cores_retag <file> [--apply]`).
- If a source item genuinely combines skills from two or more units in one problem, set `"units": ["<UNIT_A>", "<UNIT_B>", ...]` (≥ 2 distinct unit codes) in addition to `unitCode` (and `laterUnit` if any required unit is beyond `<UNIT>`).

## 4. Gap analysis (`source_gap`)

```bash
.venv/bin/python -m scripts.source_gap <UNIT>
```

Read-only report comparing `sources/_cores/<UNIT>.jsonl` (plus carried-forward cards from other units' files whose `laterUnit == <UNIT>` or `units` contains `<UNIT>`, marked `carriedFrom`) against `math_engine/reasoning_vault/<UNIT>.json`:
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

## 6. Generate drills and fill Similar variant coverage

Hand off to the `new-math-drill` skill (`.claude/skills/new-math-drill/SKILL.md`) to author, blind-solve, review, ingest, and sync the drill from the updated vault:
- Default: target the new/extended archetypes, traps, and missing reasoning moves identified in step 4.
- **Optional exam-style set** (when requested or when `source_gap` highlights exam choice formats): pass a brief for a TCAS-style 4–5 option `choice` drill where every distractor is derived from a card trap tag (`commonTrapTag`), omitting `plainText` on choice items (`rules/07` §4.9).
- **Post-ingest Similar variant coverage:** Run `.venv/bin/python -m math_engine.variant_bank --coverage <UNIT>` (or the ingested drill file). For every `(archetypeKey, level)` pair with `< 3` variants, create AI-made variants (~3 per pair: same form with new numbers, changed form e.g. reverse, and one level up when the vault allows) via `.venv/bin/python -m math_engine.variant_bank --add <draft.json>` with its full gates (blind solve for L3+, reviewer, originality). **Templates are being retired: never seed variants from templates (`--from-templates`).**

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
3. Follow `new-math-drill` step 10 for Notion sync (`drill_sync`) and PR workflow:
   - Never commit or push on `main`.
   - Follow `rules/00_core.md` §10 for branch, PR, and merge handling; task-specific instructions may narrow it.
   - For any other changes (variant banks, scripts, rules, multiple units), follow `rules/00_core.md` §10 and task-specific instructions for delivery.
4. Report concisely in polite Thai **without showing prompts, answers, or source text**: families scanned, core cards extracted (current vs `laterUnit`), vault archetypes/traps added, drill ID / variant counts, originality gate pass, and PR link/status.

## Final documentation check

- [ ] If this PR changes system behaviour, the matching rules/*.md, docs/*.md, CLAUDE.md and skills are updated in the same PR.
