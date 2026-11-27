# -*- coding: utf-8 -*-
"""Generate worker extraction prompts from ``sources/_index/plan_<UNIT>.json`` and commit validated batches.

Enables running source-card extraction on a worker model (Neon/Argon/Luna via
``tools/agents/run-worker.sh`` with ``DONE_FILE``) instead of spending Claude tokens reading
raw source PDFs or PRG code repositories. Claude only reviews ``scripts.source_gap`` output afterwards.

Supports both Math/PHY units (``schema.json``) and PRG units (``prg_schema.json``).

Usage:
    python -m scripts.extract_cards_job MTH-T02-C01-U02 --batch 1
    python -m scripts.extract_cards_job PRG-T01-C01-U02 --batch 1 --out scratch/prompts/prg-u02-b1.txt
    python -m scripts.extract_cards_job PRG-T01-C01-U02 --batch 1 --commit batch1.jsonl --done-file batch1.done
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any, Iterable

from math_engine.source_cores import (
    FORMAT_KINDS,
    MAX_FIELD_LENGTH,
    PRG_ARCHETYPE_KINDS,
    PRG_LANGUAGES,
    PRG_SCHEMA_PATH,
    REASONING_MOVES,
    REPRESENTATIONS,
    SCHEMA_PATH,
    CoreCardError,
    append_core_card,
    cores_path,
    index_dir,
    is_prg_unit,
    load_core_cards,
    load_schema,
    resolve_sources_dir,
    validate_core_card,
)
from math_engine.source_cores.ledger import (
    compute_relpath_hash,
    ledger_path,
    normalize_rel_path,
    record_batch_extractions,
)


def plan_path(unit_code: str, sources_dir: str | None = None) -> str:
    """Return ``<sources_dir>/_index/plan_<unit_code>.json``."""
    return os.path.join(index_dir(sources_dir=sources_dir), f"plan_{unit_code}.json")


def load_plan(
    unit_code: str,
    *,
    plan_file: str | None = None,
    sources_dir: str | None = None,
) -> dict[str, Any]:
    """Load the extraction plan written by ``scripts.source_find <UNIT> --plan``."""
    target = os.path.abspath(plan_file) if plan_file else plan_path(unit_code, sources_dir=sources_dir)
    if not os.path.isfile(target):
        raise FileNotFoundError(
            f"Extraction plan not found: {target}. Run `python -m scripts.source_find {unit_code} --plan` first."
        )
    with open(target, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict) or not isinstance(data.get("batches"), list):
        raise ValueError(f"Invalid plan file format: {target}")
    return data


def get_plan_batch(plan: dict[str, Any], batch_num: int) -> dict[str, Any]:
    """Return 1-indexed batch ``batch_num`` from ``plan``."""
    batches = plan.get("batches") or []
    if not batches:
        raise ValueError(f"Plan for {plan.get('unitCode', '?')} has 0 batches (nothing left to extract).")
    if batch_num < 1 or batch_num > len(batches):
        raise ValueError(f"Batch {batch_num} out of range (plan has {len(batches)} batch(es): 1..{len(batches)}).")
    for b in batches:
        if int(b.get("batch", 0)) == batch_num:
            return b
    return batches[batch_num - 1]


def default_batch_output_path(unit_code: str, batch_num: int, sources_dir: str | None = None) -> str:
    """Default batch JSONL path under ``<sources_dir>/_cores/_batches/``."""
    sdir = resolve_sources_dir(sources_dir=sources_dir)
    return os.path.join(sdir, "_cores", "_batches", f"{unit_code}-batch-{batch_num}.jsonl")


def default_done_file_path(unit_code: str, batch_num: int, sources_dir: str | None = None) -> str:
    """Default ``DONE_FILE`` marker path for ``tools/agents/run-worker.sh``."""
    sdir = resolve_sources_dir(sources_dir=sources_dir)
    return os.path.join(sdir, "_cores", "_batches", f"{unit_code}-batch-{batch_num}.done")


def _default_run_id(unit_code: str, batch_num: int) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{unit_code}-b{batch_num}-{stamp}"


def _run_id_token(run_id: str) -> str:
    """Return a compact, ID-safe run token without collapsing distinct run IDs."""
    token = re.sub(r"[^A-Za-z0-9]+", "-", run_id).strip("-")
    return token or "run"


def _abs_source_hint(sdir: str, rel_path: str) -> str:
    norm = normalize_rel_path(rel_path)
    if "::" in norm:
        zip_rel, member = norm.split("::", 1)
        return f"{os.path.join(sdir, zip_rel)}::{member}"
    return os.path.join(sdir, norm)


def build_worker_prompt(
    unit_code: str,
    batch_num: int,
    *,
    plan_file: str | None = None,
    sources_dir: str | None = None,
    batch_out: str | None = None,
    done_file: str | None = None,
    run_id: str | None = None,
) -> str:
    """Render a ready-to-run worker prompt for extracting core cards for ``unit_code`` batch ``batch_num``."""
    plan = load_plan(unit_code, plan_file=plan_file, sources_dir=sources_dir)
    batch = get_plan_batch(plan, batch_num)
    total_batches = len(plan.get("batches") or [])

    sdir = resolve_sources_dir(sources_dir=sources_dir or plan.get("sourcesDir"))
    idx_dir = index_dir(sources_dir=sdir)
    target_cores = cores_path(unit_code, sources_dir=sdir)
    target_ledger = ledger_path(sources_dir=sdir)
    out_batch = os.path.abspath(batch_out) if batch_out else default_batch_output_path(unit_code, batch_num, sdir)
    out_done = os.path.abspath(done_file) if done_file else default_done_file_path(unit_code, batch_num, sdir)
    resolved_run_id = (run_id or _default_run_id(unit_code, batch_num)).strip()

    prg_mode = is_prg_unit(unit_code)
    schema_path = PRG_SCHEMA_PATH if prg_mode else SCHEMA_PATH
    schema = load_schema("prg" if prg_mode else "math")
    schema_json = json.dumps(schema, ensure_ascii=False, indent=2)

    pages = batch.get("pages") or []
    est_items = int(batch.get("estimatedItems") or 0)
    plan_budget = plan.get("budget") or {}
    max_items = int(plan_budget.get("maxItems") or est_items)

    page_lines: list[str] = []
    for p in pages:
        rel = str(p["relPath"])
        pnum = int(p["page"])
        fam = str(p["family"])
        cache_file = str(p.get("cacheFile") or "")
        cache_abs = os.path.join(idx_dir, cache_file) if cache_file else "(not cached)"
        abs_src = _abs_source_hint(sdir, rel)
        hits = int(p.get("hits") or 0)
        allowance = int(p.get("itemAllowance") or p.get("estimatedItems") or 1)
        fhash = str(p.get("fileHash") or "")
        terms_str = ", ".join(f"{k}={v}" for k, v in sorted((p.get("terms") or {}).items()))
        mode_part = f" | mode={p['mode']}" if p.get("mode") else ""
        lic_part = f" | license={p['license']}" if p.get("license") else ""
        span_part = f" (L{p['lineStart']}-L{p['lineEnd']})" if p.get("lineStart") and p.get("lineEnd") else ""
        cache_note = (
            "PDF text; OCR text follows below"
            if p.get("textSource") == "ocr"
            else f"read page {pnum} text from `pages[]`"
        )
        page_lines.append(
            f"- Rank #{p.get('rank', '?')} | family=`{fam}`{mode_part}{lic_part} | file=`{rel}` | "
            f"page={pnum}{span_part} | itemAllowance<={allowance} | hits={hits} ({terms_str})\n"
            f"  - Cached text JSON: `{cache_abs}` ({cache_note})\n"
            f"  - Raw source path: `{abs_src}`\n"
            f"  - File SHA-256: `{fhash}`"
        )
        if p.get("textSource") == "ocr":
            ocr_text = str(p.get("ocrText") or "")
            image_file = str(p.get("imageFile") or "")
            image_abs = os.path.abspath(os.path.join(idx_dir, image_file)) if image_file else "(not cached)"
            page_lines.append(f"  - OCR text (use for term matching and source validation):\n```text\n{ocr_text}\n```")
            page_lines.append(
                f"  - Cached page image: `{image_abs}`. Open and read this page image (view_image or your image tool) "
                "when the text is unclear or formulas are missing; extract cores only, never copy wording or numbers."
            )
        elif p.get("needsImage"):
            image_file = str(p.get("imageFile") or "")
            image_abs = os.path.abspath(os.path.join(idx_dir, image_file)) if image_file else "(not cached)"
            page_lines.append(f"  - Page image (OCR disabled or unavailable): `{image_abs}`")
        for answer in p.get("answerKeyPages") or []:
            answer_cache = str(answer.get("cacheFile") or "")
            answer_cache_abs = os.path.join(idx_dir, answer_cache) if answer_cache else "(not cached)"
            answer_rel = str(answer.get("relPath") or "")
            page_lines.append(
                f"  - Answer-key reference ONLY (do not mine): `{answer_rel}` page={answer.get('page')}; "
                f"cached text JSON: `{answer_cache_abs}`; raw source: `{_abs_source_hint(sdir, answer_rel)}`. "
                "Consult only to confirm likely traps for this problem page."
            )

    plan_arg = f" --plan {os.path.abspath(plan_file)}" if plan_file else ""
    sdir_arg = f" --sources-dir {sdir}" if sources_dir else ""
    commit_cmd = (
        f".venv/bin/python -m scripts.extract_cards_job {unit_code} --batch {batch_num} "
        f"--commit {out_batch} --run-id {resolved_run_id} --done-file {out_done}{plan_arg}{sdir_arg}"
    )
    novelty_cmd = f".venv/bin/python -m scripts.source_gap {unit_code} --novelty {out_batch}{sdir_arg}"

    if prg_mode:
        intro = (
            "Read ONLY the assigned code/markdown chunks listed below, abstract source-free PRG core cards, "
            "validate every card"
        )
        rules_section = [
            "## Strict No-Copy, Zero-Leak & Validation Rules (PRG)",
            "1. **Abstract PRG cores ONLY:** extract `language`, `archetypeKind`, `skill`, `concept`, "
            "`bugPattern` (abstract bug/smell), optional `smell`, `testsCatch` (abstract invariant verified by tests), "
            "`difficultyDriver`, `level` (1-5), `traps` (`[{tag, description}]`), `qualityCheckIdeas` "
            "(`[{id: 'QC-...', check, severity?}]`), and optional `notes`.",
            "2. **ZERO copied source code, identifiers, test names, or strings:** NEVER paste code snippets, "
            "function/variable/class identifiers, `describe`/`it`/`test` names, or string literals from source files "
            "(also rejected: 6-word wording overlaps and multi-line text).",
            f"3. **Length limit:** EVERY string field (top-level and nested) MUST be <= {MAX_FIELD_LENGTH} characters.",
            "4. **Allowed enums:**",
            f"   - `language`: {list(PRG_LANGUAGES)}",
            f"   - `archetypeKind`: {list(PRG_ARCHETYPE_KINDS)}",
            "   - `qualityCheckIdeas[].id`: must match `^QC-[a-z0-9][a-z0-9-]*$`",
            "5. **REUSE attribution (optional):** For `mode=reuse` families ONLY, you may add an optional "
            '`"reuse": {"license": "<SPDX>", "attribution": "<source attribution>", "adaptedIdea": "<abstract test idea>"}` '
            "block when a test idea is adapted — still rewritten from scratch, NEVER pasted. Do NOT add `reuse` on "
            "`CORES` families.",
            "6. **Scope & provenance:**",
            '   - Set `sourceRef` to `{"family": "<family>", "file": "<relPath>", "page": <int>, "item": "<item id>"}`.',
            "   - NEVER extract from `scope`-only (`openstax`) or `NO-AUTOMATION` families.",
            "   - Respect each chunk's `itemAllowance` cap; skip duplicate/trivial items.",
            '   - If an item goes beyond this unit\'s scope, keep the card with `"laterUnit": "<REAL_CODE>"` from '
            '`id_map.json` (or `"UNMAPPED:<label>"` if no unit exists yet).',
            f"   - Use unique IDs scoped to this extraction run and batch, e.g. `CORE-{unit_code}-R{_run_id_token(resolved_run_id)}-B{batch_num:02d}-01`, ...",
            "7. **Zero-leak output:** NEVER print source code excerpts, solutions, or answers in stdout or logs.",
            "8. **Programmatic validation:** Validate every card with "
            "`math_engine.source_cores.validate_core_card(card, source_item_text=page_text)` before writing.",
        ]
        schema_heading = "## PRG Core Card Schema (`math_engine/source_cores/prg_schema.json`)"
        step1 = (
            f"1. Read each assigned chunk's cached text JSON (or the source file under `sources/prg/`) and draft "
            f"source-free PRG JSONL cards into `{out_batch}` (create an empty file if a batch yields 0 usable cards)."
        )
        step3 = (
            "3. If `--commit` reports any validation errors (copied identifiers, test names, string literals, "
            "code syntax, wording overlap, length > 200, invalid `QC-*` id, or unknown `laterUnit`), fix the flagged "
            "card(s) in the batch JSONL and re-run the commit command until it exits 0."
        )
    else:
        intro = "Read ONLY the assigned pages listed below, abstract source-free mathematical core cards, validate every card"
        rules_section = [
            "## Strict No-Copy, Zero-Leak & Validation Rules",
            "1. **Abstract mathematical cores ONLY:** extract `skill`, `reasoningMove`, optional `operations` "
            "(ordered list of >= 2 distinct taught sub-skill names; required when `reasoningMove` is `chain`), "
            "`difficultyDriver`, `level` (1-5), `traps` (`[{tag, description}]`), "
            "`format` (`{kind, optionCount?, distractorPatterns?}`), `representation`, and optional `notes`. Diagnose cards also require `flawForm`.",
            "2. **ZERO source wording:** NEVER copy, translate, or paraphrase source sentences or phrases (even short "
            "6-word overlaps are rejected by `validate_core_card`).",
            "3. **ZERO source numbers:** NEVER reuse any numeric literal from the source item text anywhere in content "
            "fields (`skill`, `operations`, `difficultyDriver`, `traps`, `format.distractorPatterns`, `notes`, `flawForm`).",
            f"4. **Length limit:** EVERY string field (top-level and nested) MUST be <= {MAX_FIELD_LENGTH} characters.",
            "5. **Allowed enums & move boundary (`chain` vs `multi-relation`/`model`):**",
            f"   - `reasoningMove`: {list(REASONING_MOVES)}",
            "   - **`chain` (strictly L2, `level` = 2, requires `operations` with >= 2 distinct ordered sub-skills):** "
            "given expression, method obvious, >= 2 different taught operations executed in sequence. Excludes any "
            "`rules/06` §2.3 L3 trigger on a given expression — a check that rejects a candidate (extraneous root, "
            "domain, ± case -> `case-check`), find-the-flaw (`diagnose`), choosing among taught methods, or "
            "`generalise`: if any applies, it is NOT `chain`. Use concise bare sub-skill names matching the unit "
            "vault vocabulary (e.g., `add`, `subtract`, `multiply`, `divide`, `power-of-i` — no redundant topic "
            "prefixes). Original example: "
            '`{"skill": "Expand a product of binomials then simplify the quotient via conjugate rationalization", '
            '"reasoningMove": "chain", "operations": ["multiply", "divide"], "level": 2}`.',
            "   - **`multi-relation` / `model` (L3+):** the solver must combine relations into an equation the prompt "
            "does not state. Original example: "
            '`{"skill": "Combine an unstated modulus relation with a real-part constraint to form and solve a '
            'quadratic equation for a parameter", "reasoningMove": "multi-relation", "level": 3}`.',
            "   - Direct computation can be L1 or L2; reverse and translate start at L2. Case-check, diagnose, "
            "multi-relation, model, and generalise start at L3. Generalise requires an argument, and any card "
            "labelled L5 requires an invented strategy. A case-check must rule out a candidate.",
            "   - Diagnose must ask the learner to find the first wrong step in given work. Use `flawForm` "
            "as an object with two descriptions: `step` names the flawed transformation in the given work, "
            "and `error` explains what makes that transformation wrong. Use at least two words in each. "
            "Do not reproduce any source steps or add `flawForm` to other moves.",
            f"   - `format.kind`: {list(FORMAT_KINDS)}",
            f"   - `representation`: {list(REPRESENTATIONS)}",
            "6. **Scope & provenance:**",
            '   - Set `sourceRef` to `{"family": "<family>", "file": "<relPath>", "page": <int>, "item": "<item id>"}`.',
            "   - NEVER extract from `openstax` (`scope`-only) or `NO-AUTOMATION` families.",
            "   - Respect each page's `itemAllowance` cap; skip duplicate/trivial items on the same page.",
            '   - If an item goes beyond this unit\'s scope, keep the card with `"laterUnit": "<REAL_CODE>"` from '
            '`id_map.json` (or `"UNMAPPED:<label>"` if no unit exists yet).',
            '   - If an item genuinely combines >= 2 units, set `"units": ["<UNIT_A>", "<UNIT_B>"]` using real codes '
            "from `id_map.json`.",
            f"   - Use unique IDs scoped to this extraction run and batch, e.g. `CORE-{unit_code}-R{_run_id_token(resolved_run_id)}-B{batch_num:02d}-01`, ...",
            "7. **Zero-leak output:** NEVER print source problem excerpts, worked solutions, or answers in stdout or logs.",
            "8. **Programmatic validation:** Validate every card with "
            "`math_engine.source_cores.validate_core_card(card, source_item_text=page_text)` before writing.",
        ]
        schema_heading = "## Core Card Schema (`math_engine/source_cores/schema.json`)"
        step1 = (
            f"1. Read each assigned page's cached text JSON (or visually inspect the PDF page if needed) and draft "
            f"source-free JSONL cards into `{out_batch}` (create an empty file if a batch yields 0 usable cards)."
        )
        step3 = (
            "3. If `--commit` reports any validation errors (copied digits, wording overlap, length > 200, missing "
            "`operations` on a `chain` card, unknown `laterUnit`), fix the flagged card(s) in the batch JSONL and "
            "re-run the commit command until it exits 0."
        )

    sections = [
        f"# Source Core-Card Extraction Job — {unit_code} (Batch {batch_num}/{total_batches})",
        "",
        "You are an extraction worker for LearningOS (run via `tools/agents/run-worker.sh` with `DONE_FILE`).",
        intro,
        "with `math_engine.source_cores.validate_core_card`, append validated cards to the unit JSONL file, update",
        "the extraction ledger, and write `DONE_FILE`. Do NOT edit tracked repository files, do NOT commit/push,",
        "do NOT open a PR, do NOT touch `progress/`, and do NOT call Notion.",
        "",
        "## Job Parameters",
        f"- Unit code: `{unit_code}`",
        f"- Batch: `{batch_num}` of `{total_batches}` ({len(pages)} page(s), item allowance cap: {est_items}, "
        f"run max items: {max_items})",
        f"- Run ID: `{resolved_run_id}`",
        f"- Batch output JSONL (write this batch's cards here): `{out_batch}`",
        f"- Unit core cards JSONL (appended by commit step): `{target_cores}`",
        f"- Extraction ledger (updated by commit step): `{target_ledger}`",
        f"- DONE_FILE (written by commit step when finished): `{out_done}`",
        f"- Schema file: `{schema_path}`",
        "",
        f"## Assigned Pages (Batch {batch_num})",
        *page_lines,
        "",
        *rules_section,
        "",
        schema_heading,
        "```json",
        schema_json,
        "```",
        "",
        "## Execution Steps",
        step1,
        "2. Run the commit helper to validate every card with `validate_core_card` (against the cached page text), "
        f"append valid cards to `{target_cores}`, update `{target_ledger}` for all {len(pages)} page(s) in this "
        f"batch (including 0-card pages), and write `{out_done}`:",
        "```bash",
        commit_cmd,
        "```",
        step3,
        "4. After `--commit` exits 0 and `DONE_FILE` is non-empty, reply only `done` (do NOT print card text or "
        "source excerpts). The coordinator will run novelty/saturation next:",
        "```bash",
        novelty_cmd,
        "```",
    ]
    return "\n".join(sections) + "\n"


def _load_batch_page_texts(sdir: str, pages: list[dict[str, Any]]) -> dict[tuple[str, int], str]:
    idx_dir = index_dir(sources_dir=sdir)
    cache_docs: dict[str, dict[str, Any]] = {}
    texts: dict[tuple[str, int], str] = {}
    for p in pages:
        rel = normalize_rel_path(str(p.get("relPath") or ""))
        pnum = int(p.get("page") or 0)
        if p.get("textSource") == "ocr":
            texts[(rel, pnum)] = str(p.get("ocrText") or "")
            continue
        cache_file = str(p.get("cacheFile") or "")
        if not cache_file:
            continue
        if cache_file not in cache_docs:
            cpath = os.path.join(idx_dir, cache_file)
            if os.path.isfile(cpath):
                try:
                    with open(cpath, "r", encoding="utf-8") as fh:
                        cache_docs[cache_file] = json.load(fh)
                except (OSError, ValueError):
                    cache_docs[cache_file] = {}
            else:
                cache_docs[cache_file] = {}
        doc = cache_docs[cache_file]
        for entry in doc.get("pages") or []:
            if int(entry.get("page") or 0) == pnum:
                texts[(rel, pnum)] = str(entry.get("text") or "")
                break
    return texts


def _match_page_text_for_card(
    card: dict[str, Any],
    page_texts: dict[tuple[str, int], str],
) -> str | None:
    ref = card.get("sourceRef") or {}
    ref_file = normalize_rel_path(str(ref.get("file") or ""))
    ref_page = ref.get("page")
    if not ref_file:
        return None
    if isinstance(ref_page, int):
        if (ref_file, ref_page) in page_texts:
            return page_texts[(ref_file, ref_page)]
        for (rel, pnum), text in page_texts.items():
            if pnum == ref_page and (rel.endswith("/" + ref_file) or os.path.basename(rel) == ref_file):
                return text
        return None
    # String page refs (e.g. "L10-L45" in PRG cards): match cached chunks for the same file
    matching_chunks = [
        text
        for (rel, _pnum), text in sorted(page_texts.items())
        if rel == ref_file or rel.endswith("/" + ref_file) or os.path.basename(rel) == ref_file
    ]
    if matching_chunks:
        return "\n".join(matching_chunks)
    return None


def commit_batch_cards(
    unit_code: str,
    batch_num: int,
    batch_jsonl_path: str,
    *,
    plan_file: str | None = None,
    sources_dir: str | None = None,
    run_id: str | None = None,
    done_file: str | None = None,
    valid_unit_codes: Iterable[str] | None = None,
    registry_path: str | None = None,
) -> dict[str, Any]:
    """Validate batch cards, append them to ``sources/_cores/<UNIT>.jsonl``, update ``_ledger.json``,
    and optionally write ``done_file``.
    """
    if not os.path.isfile(batch_jsonl_path):
        raise FileNotFoundError(f"Batch JSONL file not found: {batch_jsonl_path}")

    plan = load_plan(unit_code, plan_file=plan_file, sources_dir=sources_dir)
    batch = get_plan_batch(plan, batch_num)
    sdir = resolve_sources_dir(sources_dir=sources_dir or plan.get("sourcesDir"))
    resolved_run_id = (run_id or _default_run_id(unit_code, batch_num)).strip()

    batch_pages = batch.get("pages") or []
    page_texts = _load_batch_page_texts(sdir, batch_pages)

    cards: list[dict[str, Any]] = []
    with open(batch_jsonl_path, "r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, 1):
            line = raw.strip()
            if not line:
                continue
            try:
                card = json.loads(line)
            except ValueError as exc:
                raise CoreCardError(f"{batch_jsonl_path}:{line_no}: invalid JSON: {exc}") from exc
            src_text = _match_page_text_for_card(card, page_texts) if isinstance(card, dict) else None
            errs = validate_core_card(
                card,
                source_item_text=src_text,
                valid_unit_codes=valid_unit_codes,
                registry_path=registry_path,
            )
            if errs:
                cid = card.get("id", f"line {line_no}") if isinstance(card, dict) else f"line {line_no}"
                raise CoreCardError(f"[{cid}] invalid core card: " + "; ".join(errs))
            cards.append(card)

    existing_cards = load_core_cards(
        unit_code,
        sources_dir=sdir,
        validate=False,
        include_carried=False,
    )
    existing_by_id = {str(c.get("id")): c for c in existing_cards if isinstance(c.get("id"), str)}

    # Detect conflicting IDs before appending anything or recording ledger progress.
    submitted_by_id: dict[str, dict[str, Any]] = {}
    for card in cards:
        cid = str(card["id"])
        prior = submitted_by_id.get(cid) or existing_by_id.get(cid)
        if prior is not None and _card_content(prior) != _card_content(card):
            raise CoreCardError(
                f"ID clash for {cid}: an existing/submitted card has different content; "
                "use a new run-scoped card ID instead of skipping it."
            )
        submitted_by_id[cid] = card

    appended_ids: list[str] = []
    skipped_ids: list[str] = []
    for card in cards:
        cid = str(card["id"])
        if cid in existing_by_id:
            skipped_ids.append(cid)
            continue
        src_text = _match_page_text_for_card(card, page_texts)
        append_core_card(
            unit_code,
            card,
            sources_dir=sdir,
            source_item_text=src_text,
            valid_unit_codes=valid_unit_codes,
            registry_path=registry_path,
        )
        existing_by_id[cid] = card
        appended_ids.append(cid)

    # Group produced card IDs by (normalized relPath, page) to record every batch page in the ledger
    cards_by_page: dict[tuple[str, int], list[str]] = {}
    for card in cards:
        ref = card.get("sourceRef") or {}
        ref_file = normalize_rel_path(str(ref.get("file") or ""))
        ref_page = ref.get("page")
        if not ref_file:
            continue
        matched_key: tuple[str, int] | None = None
        for bp in batch_pages:
            bp_rel = normalize_rel_path(str(bp.get("relPath") or ""))
            bp_page = int(bp.get("page") or 0)
            file_matches = bp_rel == ref_file or bp_rel.endswith("/" + ref_file) or os.path.basename(bp_rel) == ref_file
            if file_matches and (bp_page == ref_page or not isinstance(ref_page, int)):
                matched_key = (bp_rel, bp_page)
                break
        if matched_key is not None:
            cards_by_page.setdefault(matched_key, []).append(str(card["id"]))
        elif isinstance(ref_page, int):
            cards_by_page.setdefault((ref_file, ref_page), []).append(str(card["id"]))

    ledger_records: list[dict[str, Any]] = []
    for bp in batch_pages:
        rel = normalize_rel_path(str(bp.get("relPath") or ""))
        pnum = int(bp.get("page") or 0)
        fhash = str(bp.get("fileHash") or "") or (compute_relpath_hash(sdir, rel) or "")
        ledger_records.append(
            {
                "file": rel,
                "page": pnum,
                "fileHash": fhash,
                "cardsProduced": cards_by_page.get((rel, pnum), []),
            }
        )

    record_batch_extractions(
        unit_code,
        ledger_records,
        run_id=resolved_run_id,
        sources_dir=sdir,
    )

    summary = {
        "unitCode": unit_code,
        "batch": batch_num,
        "runId": resolved_run_id,
        "pagesRecorded": len(ledger_records),
        "cardsSubmitted": len(cards),
        "cardsAppended": len(appended_ids),
        "cardsSkippedExisting": len(skipped_ids),
        "coresPath": cores_path(unit_code, sources_dir=sdir),
        "ledgerPath": ledger_path(sources_dir=sdir),
        "doneFile": os.path.abspath(done_file) if done_file else None,
    }

    if done_file:
        abs_done = os.path.abspath(done_file)
        os.makedirs(os.path.dirname(abs_done), exist_ok=True)
        with open(abs_done, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, ensure_ascii=False, indent=2)
            fh.write("\n")

    return summary


def _card_content(card: dict[str, Any]) -> str:
    """Canonical card payload for ID-clash checks; provenance may differ for the same core."""
    return json.dumps(
        {key: value for key, value in card.items() if key not in {"id", "sourceRef"}},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.extract_cards_job",
        description="Render a worker extraction prompt for one batch of plan_<UNIT>.json, or commit validated cards.",
    )
    parser.add_argument("unit", help="Target unit code (e.g. MTH-T02-C01-U02 or PRG-T01-C01-U02).")
    parser.add_argument("--batch", type=int, required=True, help="1-indexed batch number from plan_<UNIT>.json.")
    parser.add_argument(
        "--plan",
        default=None,
        help="Override plan JSON path (default: sources/_index/plan_<UNIT>.json).",
    )
    parser.add_argument(
        "--sources-dir",
        default=None,
        help="Override sources directory (default: LEARNINGOS_SOURCES_DIR or <main>/sources).",
    )
    parser.add_argument(
        "--batch-out",
        default=None,
        help="Batch JSONL path embedded in the generated prompt.",
    )
    parser.add_argument(
        "--done-file",
        default=None,
        help="DONE_FILE path embedded in the generated prompt (or written by --commit).",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Explicit run ID recorded in the extraction ledger (default: auto-generated UTC stamp).",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Write the generated worker prompt to this file path (in addition to printing a notice).",
    )
    parser.add_argument(
        "--commit",
        metavar="BATCH_JSONL",
        default=None,
        help="Validate BATCH_JSONL, append to sources/_cores/<UNIT>.jsonl, update _ledger.json, and write DONE_FILE.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.commit:
            summary = commit_batch_cards(
                args.unit,
                args.batch,
                args.commit,
                plan_file=args.plan,
                sources_dir=args.sources_dir,
                run_id=args.run_id,
                done_file=args.done_file,
            )
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            return 0

        prompt = build_worker_prompt(
            args.unit,
            args.batch,
            plan_file=args.plan,
            sources_dir=args.sources_dir,
            batch_out=args.batch_out,
            done_file=args.done_file,
            run_id=args.run_id,
        )
        if args.out:
            out_path = os.path.abspath(args.out)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write(prompt)
            print(f"Wrote worker extraction prompt to {out_path}")
        else:
            sys.stdout.write(prompt)
        return 0
    except (FileNotFoundError, ValueError, CoreCardError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
