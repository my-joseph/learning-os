---
name: synthesize-source
description: Synthesise original math or programming (MTH-* / PRG-*) problems and reasoning-vault upgrades from the abstract cores of local source material — never copying source wording, numbers, code, identifiers, test names, or strings. Use when the learner says "สังเคราะห์โจทย์ <UNIT>" or "synthesize problems for <UNIT>".
---

# Synthesise from source cores

Goal: turn local raw material (`sources/`, gitignored) into original, verified reasoning-vault archetypes, drills (or PRG labs), and (for math) variants for one `<UNIT>` with zero copying, zero paraphrasing, zero reused numbers, and (for PRG) zero copied code, identifiers, test names, or string literals. The learner studies the resulting drills and labs, so **never show answers, drafts, or source excerpts to the learner**. Subagents write results to files and reply only `done`. Run everything from the repo root with `.venv/bin/python -m ...`. Talk to the learner in polite Thai; everything written to cards, vaults, drills, labs, and PRs is English.

## 1. Brief & policy check

1. Take `<UNIT>` (and optional focus, exam-style request, drill vs lab target, or family filter) from the request; ask only if `<UNIT>` is missing. State the brief in one line and continue without waiting.
2. Read `docs/sources.md` and `rules/07_problem_generation.md` §4 (plus `rules/04_code.md` for `PRG-*` units).
   - **OpenStax is `scope` only** (TOC + learning objectives): **never** extract core cards or mine exercises from OpenStax.
   - **`NO-AUTOMATION` families** are **never** indexed, cached, or extracted automatically.
   - Allowed **`cores`** families (e.g. math `smartmathpro`, `thai-exams`, `illustrative-math`, `mathsgenie`, or copyleft/ARR PRG repos) yield source-free core cards only — never copy, translate, paraphrase, or reuse numbers/code.
   - Allowed **`reuse`** PRG families under `sources/prg/<family>/` (e.g. `exercism-typescript`, `exercism-javascript`, `typescript-exercises`, `eslint`, `javascript-questions`, `javascript-koans`, `wtfjs`) also produce source-free PRG core cards; when a test idea is adapted (still rewritten from scratch, never pasted), record licence + attribution in the optional `reuse` block.

## 2. Locate, rank & plan candidate pages/files (`source_find --plan`)

```bash
.venv/bin/python -m scripts.source_find <UNIT> --plan [--budget-pages 30 --budget-items 40] [--batch-size 10] [--refresh] [--terms ...] [--families ...]
```

- Resolves `LEARNINGOS_SOURCES_DIR` (defaults to `<main checkout>/sources` even from a worktree), writes `sources/_index/located_<UNIT>.json` (for the originality gate), and warns if any folder under `sources/` or `sources/prg/` (excluding `_`-prefixed folders) is not registered in `docs/sources.md` — register its family, licence, allowed use (`reuse` / `cores` / `no-automation` / `scope`), and priority before mining it.
  - **MTH/PHY units:** scans PDFs (and PDFs in zips), caching extracted page text in `sources/_index/pdf_*.json`. Empty or legacy-font-garbled pages use the optional OCR fallback (`pdftoppm` + Tesseract `tha+eng`); OCR text/PNG are cached by PDF hash and page in `sources/_index/`. `--no-ocr` disables it. OCR pages are marked `textSource: "ocr"`; weak OCR sets `needsImage: true`.
  - **PRG units:** scans `.js`/`.ts`/`.tsx`/`.jsx`/`.py`/`.md`/`.json` files under `sources/prg/<family>/` (no PDF needed), splitting large files into numbered chunks cached in `sources/_index/code_*.json` using PRG terms from `math_engine/source_cores/unit_terms.json`.
- Writes a bounded extraction plan `sources/_index/plan_<UNIT>.json` (defaults: **30 pages/chunks / 40 items** per unit run, split into batches of **10**):
  - Ranked by **(a)** family priority (`docs/sources.md` / `SOURCE_FAMILIES` + `docs/source_backlog.md` rank), **(b)** term-hit density, **(c)** Thai-exam relevance boost (math), and **(d)** round-robin diversity across families so one source cannot fill the budget.
  - Always skips **`scope`-only** and **`no-automation`** families.
  - Excludes `(unit, file, page)` entries already recorded in `sources/_cores/_ledger.json` unless the source file's SHA-256 hash changed or `--refresh` is passed.
- Review the plan summary (selected pages/chunks per family, skipped ledger/scope/no-automation counts, and batch count). If `selectedPageCount == 0` and carried-forward cards exist, proceed directly to step 4.

## 3. Extract source-free core cards in bounded worker batches (`extract_cards_job` + `run-worker.sh`)

Run extraction in batches (default 10 pages/chunks per batch) on a **worker model** (Neon/Argon/Luna via `tools/agents/run-worker.sh` with `DONE_FILE`) rather than a Claude subagent reading raw PDFs or code repos — **Claude only reviews `source_gap` output** in steps 4–5.

For each batch `k = 1, 2, ...` in `sources/_index/plan_<UNIT>.json`:

1. Render the worker prompt (automatically selects `math_engine/source_cores/schema.json` for MTH/PHY or `math_engine/source_cores/prg_schema.json` for PRG, embeds batch `k` targets, strict no-copy/zero-leak rules, `validate_core_card`, append to `sources/_cores/<UNIT>.jsonl`, `_ledger.json` update, and `DONE_FILE`):
   ```bash
   .venv/bin/python -m scripts.extract_cards_job <UNIT> --batch <k> \
     --batch-out sources/_cores/_batches/<UNIT>-batch-<k>.jsonl \
     --done-file sources/_cores/_batches/<UNIT>-batch-<k>.done \
     --out scratch/prompts/<UNIT>-extract-b<k>.txt
   ```
   OCR pages include their OCR text; OCR pages and pages marked `needsImage` also include the cached PNG path. Inspect that image when text is unclear or formulas are missing. A rendered page remains one page for budgeting.
2. Launch the worker with `DONE_FILE` so `run-worker.sh` stops cleanly once the batch commits:
   ```bash
   DONE_FILE=sources/_cores/_batches/<UNIT>-batch-<k>.done \
     tools/agents/run-worker.sh <worktree> <branch> \
     scratch/prompts/<UNIT>-extract-b<k>.txt \
     scratch/logs/<UNIT>-extract-b<k>.log
   ```
   The worker drafts batch cards into the batch JSONL and runs `.venv/bin/python -m scripts.extract_cards_job <UNIT> --batch <k> --commit <batch_jsonl> --run-id <run_id> --done-file <done_file>`, which validates every card with `validate_core_card(card, source_item_text=...)`, appends new cards to `sources/_cores/<UNIT>.jsonl`, updates `sources/_cores/_ledger.json` for every page/chunk in batch `k` (including 0-card items), and writes `DONE_FILE`.
3. Check batch novelty / saturation:
   ```bash
   .venv/bin/python -m scripts.source_gap <UNIT> --novelty sources/_cores/_batches/<UNIT>-batch-<k>.jsonl
   ```
4. **Saturation & budget stop rule:**
   - Stop early if **two consecutive batches** each add **`< 2` new cores** (fuzzy duplicates on `skill` + `reasoningMove` + `traps` for math, or `skill` + `concept` + `bugPattern` + `archetypeKind` + `traps`/`qualityCheckIdeas` for PRG).
   - Otherwise stop when all planned batches (bounded by `--budget-pages` / `--budget-items`) are complete.

Mandatory card invariants (enforced by `validate_core_card` during `--commit`):
- **Math cards (`schema.json`):** abstract `skill`, `reasoningMove`, `difficultyDriver`, `level`, `traps`, `format`, `representation`, optional `notes`. Zero source wording and zero source numbers; every string ≤ 200 chars.
- **PRG cards (`prg_schema.json`):** abstract `language`, `archetypeKind` (`implement` | `predict-output` | `find-the-bug` | `refactor` | `project-milestone`), `skill`, `concept`, `bugPattern`, optional `smell`, `testsCatch`, `difficultyDriver`, `level`, `traps`, `qualityCheckIdeas` (`QC-*` style), `sourceRef`, optional `notes`, and optional `reuse` (`{license, attribution, adaptedIdea?}`) **only** on `REUSE` families. Zero copied source code, identifiers, test names, string literals, or wording; every string ≤ 200 chars.
- Never extract from `openstax` (`scope`) or `NO-AUTOMATION` families.
- If an item goes deeper than `<UNIT>`'s scope, keep its core card with `"laterUnit": "<TARGET_UNIT>"` using a **real unit/chapter code from `id_map.json`** (or `"UNMAPPED:<label>"`; remap older files with `.venv/bin/python -m scripts.source_cores_retag <file> [--apply]`).
- For math items combining ≥ 2 units, set `"units": ["<UNIT_A>", "<UNIT_B>", ...]`.

## 4. Gap analysis (`source_gap`)

```bash
.venv/bin/python -m scripts.source_gap <UNIT>
```

Read-only report comparing `sources/_cores/<UNIT>.jsonl` (plus carried-forward cards from other units' files marked `carriedFrom`) against the reasoning vault:
- **MTH/PHY (`math_engine/reasoning_vault/<UNIT>.json`):** matched vs unmatched candidate archetypes, new trap tags, missing reasoning moves & levels, exam formats seen, deferred `laterUnit` cards, and `Bridge candidates` (`ELIGIBLE` vs `not eligible` via `scripts.bridge_scope`).
- **PRG (`code_engine/reasoning_vault/<CHAPTER>.json`):** matched vs unmatched candidate archetypes, new `cognitiveTraps`, new bug patterns / smells, new `QC-*` `qualityCheckIdeas` not yet in the vault, missing PRG archetype kinds (`implement`, `predict-output`, `find-the-bug`, `refactor`, `project-milestone`) and levels, languages/concepts, and deferred `laterUnit` cards.

## 5. Update the Reasoning Vault (with reviewer subagent)

- **MTH/PHY (`math_engine/reasoning_vault/<UNIT>.json`):**
  - Add new archetypes for genuine unmatched cores; extend existing archetypes' `cognitiveTraps`, `levelNote`s, and `usedContexts` (preserving figure decisions per `rules/03` §3.1).
  - Add eligible bridge archetypes to `math_engine/reasoning_vault/MTH-BRIDGE.json` when `source_gap` shows eligible pairs (`scripts.bridge_scope`).
  - Cite provenance: `"source": "OpenStax <Book> §x.y; cores: <families>"`.
- **PRG (`code_engine/reasoning_vault/<CHAPTER>.json`):**
  - Add new archetypes for genuine unmatched cores; extend existing archetypes' `cognitiveTraps` (with reproducers) and `qualityChecks` (`QC-*` R2 properties with `knownBad`, never a mandated API).
  - Cite provenance: `"source": "docs: <primary doc>; cores: <families>"` (include licence attribution if a `REUSE` test idea was adapted).
  - Run `.venv/bin/python -m code_engine.quality_checks --check-vaults` and fix every error before spawning the reviewer.
- **Vault reviewer subagent (both MTH & PRG):**
  - Spawn **one** fresh reviewer subagent with the vault diff, `docs/sources.md`, and the unit scope (OpenStax TOC for MTH, `docs/prg_curriculum_v2.md` row + `docs/prg_reviewer_spec.md` for PRG). Ask it to check that every new/updated archetype is (1) 100% original and source-free (no copied wording, numbers, code, identifiers, or test strings), (2) strictly within `<UNIT>` scope (deeper items stayed in `laterUnit`), (3) has valid traps and figure decision (MTH) or valid R2 `qualityChecks` (PRG), and (4) for `MTH-BRIDGE.json`, real `junction` and passed `unitCodes`. Have it write its verdict to `scratch/reviews/<UNIT>-vault-review.json` and reply only `done`. Fix any flagged items before step 6.

## 6. Generate drills (or PRG labs)

- **MTH/PHY:** Hand off to `new-math-drill` (`.claude/skills/new-math-drill/SKILL.md`) targeting the new/extended archetypes, traps, and missing moves (and optional TCAS-style choice sets). After ingest, run `.venv/bin/python -m math_engine.variant_bank --coverage <UNIT>` and fill pairs with `< 3` variants via AI-made variants (`variant_bank --add`; never `--from-templates`).
- **PRG:** Hand off to `new-code-drill` (`.claude/skills/new-code-drill/SKILL.md`) for unit/chapter drills — or `new-project` (`.claude/skills/new-project/SKILL.md`) for chapter labs / extra projects — targeting the new bug patterns, traps, `QC-*` checks, and missing archetype kinds/levels from step 4. *(Similar/variants for PRG are out of scope and not built yet.)*

## 7. Originality gate (mandatory)

Every generated drill draft, math variant bank, and PRG lab must pass the originality gate against `sources/_index/` before ingest/finalise (default ON on `--check` when `sources/` exists):

```bash
# Math drills & variants:
.venv/bin/python -m math_engine.ai_drill_ingest --unit <UNIT> --ingest-file scratch/drafts/<file>.json --check --originality
.venv/bin/python -m math_engine.variant_bank --check <UNIT> --originality

# PRG drills & labs (token-level winnowing/k-gram code check + prompt text check):
.venv/bin/python -m code_engine.ai_drill_ingest --check scratch/drafts/<file>.json --originality
.venv/bin/python -m code_engine.lab_ingest --check labs/<LAB_ID> --originality

# Standalone CLI (works for math drafts, variant banks, PRG drafts, and lab directories):
.venv/bin/python -m math_engine.source_cores.originality <draft.json|lab_dir> --unit <UNIT>
```

Rejections (8-word shingle overlap, normalised text similarity ≥ 0.6, math number multiset match, or PRG normalized token fingerprint overlap on solutions/starters/tests) mean rewrite from scratch with fresh domain, structure, and implementation — never rename variables or tweak a few words.

## 8. Test, ship PR, and report in Thai

1. Run `.venv/bin/python -m pytest -n auto -q` (or `-m "not prg"` if PRG untouched) and `.venv/bin/ruff check . && .venv/bin/ruff format --check .`.
2. Verify `git status` shows **nothing** staged under `sources/` or `scratch/`.
3. Follow `new-math-drill` / `new-code-drill` / `new-project` for Notion sync (`drill_sync` / `lab_sync`) and PR workflow:
   - Never commit or push on `main`.
   - Follow `rules/00_core.md` §10 for branch, PR, and merge handling; task-specific instructions may narrow it.
4. Report concisely in polite Thai **without showing prompts, answers, code solutions, or source text**: families scanned, core cards extracted (current vs `laterUnit`), vault archetypes/traps/`QC-*` checks added, drill/lab ID (and math variant counts), originality gate pass, and PR link/status.

## Final documentation check

- [ ] If this PR changes system behaviour, the matching rules/*.md, docs/*.md, CLAUDE.md and skills are updated in the same PR.

## Self-review

After the run, compare the outcome against this skill's goal. For each friction (unclear step, missing tool, gate miss, rework, reviewer catch, or learner correction), log `.venv/bin/python -m scripts.issues propose --target skill:synthesize-source --evidence "<what happened>" --proposal "<concrete change>"` (or `.venv/bin/python -m scripts.issues add --kind <kind> --severity batch --source author --where <where> --what "<what>" --target skill:synthesize-source`). If the fix is a small, scoped edit to this `SKILL.md`, make it in the same PR.
