"""Hermetic tests for bounded, incremental source synthesis:

1. Ranking & diversity: family priority (docs/sources.md + docs/source_backlog.md + SOURCE_FAMILIES),
   term-hit density, Thai-exam boost, scope-only skipping, and round-robin family diversity.
2. Budget caps: --budget-pages, --budget-items, defaults (30 pages / 40 items), and batching.
3. Extraction ledger: sources/_cores/_ledger.json skip on unchanged hash, re-include on file hash
   change, and --refresh override.
4. Batch novelty & saturation: scripts.source_gap <UNIT> --novelty <batch_cards.jsonl> counting
   new cores vs fuzzy duplicates (skill + reasoningMove + traps), within-batch dedup, and < 2 signal.
5. Worker job prompt & commit: scripts.extract_cards_job <UNIT> --batch <k> prompt rendering,
   --commit validation (including source-free check), append to <UNIT>.jsonl, ledger update
   (including 0-card pages), and DONE_FILE output.

Never touches the real ``sources/`` or ``progress/`` directories.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from math_engine import source_cores
from math_engine.source_cores import ledger
from scripts import extract_cards_job, source_find, source_gap

UNIT = "MTH-T02-C01-U02"


def _card(
    cid: str,
    *,
    unit: str = UNIT,
    skill: str = "Solve quadratic equations by completing the square",
    move: str = "direct",
    level: int = 2,
    traps: list[dict[str, str]] | None = None,
    family: str = "smartmathpro",
    file: str = "SmartMathPro/quad.pdf",
    page: int = 1,
    item: str = "Q1",
    notes: str = "Abstract quadratic core",
) -> dict[str, Any]:
    return {
        "id": cid,
        "unitCode": unit,
        "sourceRef": {"family": family, "file": file, "page": page, "item": item},
        "skill": skill,
        "reasoningMove": move,
        "difficultyDriver": "Requires isolating squared binomial before applying root branches",
        "level": level,
        "traps": traps
        if traps is not None
        else [
            {
                "tag": "t02-c01-u02-added-square-to-one-side-only-trap",
                "description": "Adds half-coefficient square to left side only",
            }
        ],
        "format": {"kind": "choice", "optionCount": 5, "distractorPatterns": ["unbalanced constant"]},
        "representation": "symbolic",
        "notes": notes,
    }


def _prg_card(
    cid: str,
    *,
    skill: str,
    concept: str,
    trap: str,
    kind: str = "predict-output",
    language: str = "javascript",
) -> dict[str, Any]:
    return {
        "profile": "prg",
        "id": cid,
        "unitCode": "PRG-T00-C03",
        "sourceRef": {
            "family": "prg/javascript-questions",
            "file": "prg/javascript-questions/q.md",
            "page": 1,
            "item": cid,
        },
        "language": language,
        "archetypeKind": kind,
        "skill": skill,
        "concept": concept,
        "bugPattern": "",
        "testsCatch": "Observe the resulting asynchronous state",
        "difficultyDriver": "Track control flow across callbacks",
        "level": 2,
        "traps": [{"tag": trap, "description": "Confuses deferred result flow"}],
        "qualityCheckIdeas": [],
        "notes": "Follow the promise result through each continuation",
    }


def _write_fixture_registry(path: Path) -> Path:
    path.write_text(
        "# Source Registry\n\n"
        "| Family (under `sources/`) | What it is | Language | Licence | Allowed use | Priority | Notes |\n"
        "| :--- | :--- | :--- | :--- | :--- | :---: | :--- |\n"
        "| `openstax/math/<book>/` | OpenStax | EN | CC | `scope` | `0` | Scope only |\n"
        "| `SmartMathPro/` | SmartMathPro | TH | ARR | `cores` | `100` | Thai exams |\n"
        "| `thai-exams/tcas68-a-level/` | TCAS | TH | ARR | `cores` | `95` | Thai A-Level |\n"
        "| `illustrative-math/grade6-unit1/` | IM | EN | CC | `cores` | `70` | Conceptual |\n"
        "| `mathsgenie/Grade_N/` | MathsGenie | EN | ARR | `cores` | `50` | Fluency |\n",
        encoding="utf-8",
    )
    return path


def _write_fixture_backlog(path: Path) -> Path:
    path.write_text(
        "# Source backlog\n\n"
        "## Math sources (ranked)\n\n"
        "- [ ] 1. **SmartMathPro Thai Past Papers** — `sources/SmartMathPro/`\n"
        "- [ ] 2. **Thailand TCAS A-Level Math** — `sources/thai-exams/tcas68-a-level/`\n"
        "- [ ] 12. **Illustrative Mathematics** — `sources/illustrative-math/`\n"
        "- [ ] 85. **Maths Genie** — `sources/mathsgenie/`\n",
        encoding="utf-8",
    )
    return path


def _setup_multi_family_sources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    smp_pages: int = 8,
    thai_pages: int = 3,
    mg_pages: int = 4,
    im_pages: int = 2,
    items_per_page: int = 1,
) -> tuple[Path, Path, Path]:
    """Create a hermetic multi-family sources tree with mocked PDF extraction."""
    sdir = tmp_path / "sources"
    files = {
        "smp.pdf": sdir / "SmartMathPro" / "smp.pdf",
        "tcas.pdf": sdir / "thai-exams" / "tcas68-a-level" / "tcas.pdf",
        "mg.pdf": sdir / "mathsgenie" / "Grade_8" / "mg.pdf",
        "im.pdf": sdir / "illustrative-math" / "grade6-unit1" / "im.pdf",
        "openstax.pdf": sdir / "openstax" / "math" / "alg" / "openstax.pdf",
    }
    for key, p in files.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(f"%PDF-1.4 fixture-{key}-v1".encode("utf-8"))

    def _item_block(label: str, n_items: int, repeat_term: int = 2) -> str:
        terms = " ".join(["quadratic discriminant"] * repeat_term)
        if n_items <= 1:
            return f"Topic {label}: {terms} สมการกำลังสอง"
        return "\n".join(f"{i}. Solve {terms} item {label}" for i in range(1, n_items + 1))

    page_map = {
        "smp.pdf": [
            {"page": i, "text": _item_block(f"smp-{i}", items_per_page, repeat_term=i), "isImagePage": False}
            for i in range(1, smp_pages + 1)
        ],
        "tcas.pdf": [
            {"page": i, "text": _item_block(f"tcas-{i}", items_per_page, repeat_term=2), "isImagePage": False}
            for i in range(1, thai_pages + 1)
        ],
        "mg.pdf": [
            {"page": i, "text": _item_block(f"mg-{i}", items_per_page, repeat_term=2), "isImagePage": False}
            for i in range(1, mg_pages + 1)
        ],
        "im.pdf": [
            {"page": i, "text": _item_block(f"im-{i}", items_per_page, repeat_term=2), "isImagePage": False}
            for i in range(1, im_pages + 1)
        ],
        "openstax.pdf": [
            {
                "page": 1,
                "text": "Table of Contents - Learning Objectives: quadratic discriminant quadratic formula",
                "isImagePage": False,
            },
            {
                "page": 2,
                "text": "quadratic equations factoring completing the square quadratic formula",
                "isImagePage": False,
            },
        ],
    }

    def fake_extract(source: str | bytes) -> list[dict[str, Any]]:
        name = Path(str(source)).name
        return page_map.get(name, [])

    monkeypatch.setattr(source_find, "extract_pdf_pages", fake_extract)
    reg = _write_fixture_registry(tmp_path / "sources.md")
    backlog = _write_fixture_backlog(tmp_path / "source_backlog.md")
    return sdir, reg, backlog


# ---------------------------------------------------------------------------
# 1. Ranking, priority parsing, Thai-exam boost, scope skipping & diversity
# ---------------------------------------------------------------------------


def test_registry_and_backlog_priority_parsing_on_real_docs() -> None:
    """Real docs/sources.md and docs/source_backlog.md parse cleanly and preserve ordering."""
    reg_prios = source_find.load_registry_priorities()
    assert reg_prios["smartmathpro"] == 100
    assert reg_prios["thai-exams/tcas68-a-level"] == 95
    assert reg_prios["thai-exams/onet-2568"] == 90
    assert reg_prios["illustrative-math"] == 70
    assert reg_prios["mathsgenie"] == 50
    assert reg_prios["openstax"] == 0

    backlog_ranks = source_find.load_backlog_ranks(unit_code=UNIT)
    assert backlog_ranks["smartmathpro"] == 1
    assert backlog_ranks["thai-exams/tcas68-a-level"] == 2
    assert backlog_ranks["illustrative-math"] == 12


def test_plan_ranking_thai_boost_scope_skip_and_round_robin_diversity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sdir, reg, backlog = _setup_multi_family_sources(
        tmp_path,
        monkeypatch,
        smp_pages=10,
        thai_pages=2,
        mg_pages=3,
        im_pages=2,
        items_per_page=1,
    )
    find_res = source_find.find_sources(UNIT, sources_dir=str(sdir), registry_path=str(reg))
    plan = source_find.build_extraction_plan(
        find_res,
        budget_pages=8,
        budget_items=40,
        batch_size=4,
        sources_dir=str(sdir),
        registry_path=str(reg),
        backlog_path=str(backlog),
    )

    assert Path(plan["planPath"]).is_file()
    selected = plan["selectedPages"]
    assert len(selected) == 8

    # Scope-only OpenStax must NEVER appear in selectedPages and must be counted as skipped
    assert not any(p["family"] == "openstax" for p in selected)
    assert plan["summary"]["skippedScopePages"] == 2

    # Round-robin diversity: first 4 ranks must cover all 4 core families in priority order!
    first_round_fams = [p["family"] for p in selected[:4]]
    assert first_round_fams == ["smartmathpro", "thai-exams", "illustrative-math", "mathsgenie"]

    # Thai-exam boost applied to smartmathpro and thai-exams only
    by_fam = {p["family"]: p for p in selected[:4]}
    assert by_fam["smartmathpro"]["scoreBreakdown"]["thaiExamBoost"] == source_find.THAI_EXAM_BOOST
    assert by_fam["thai-exams"]["scoreBreakdown"]["thaiExamBoost"] == source_find.THAI_EXAM_BOOST
    assert by_fam["illustrative-math"]["scoreBreakdown"]["thaiExamBoost"] == 0.0
    assert by_fam["mathsgenie"]["scoreBreakdown"]["thaiExamBoost"] == 0.0

    # Within SmartMathPro (10 pages where page k has k*2 hits), highest density/hit page ranks first
    smp_selected = [p for p in selected if p["family"] == "smartmathpro"]
    assert smp_selected[0]["page"] == 10
    assert smp_selected[0]["score"] >= smp_selected[-1]["score"]

    # SmartMathPro cannot fill all 8 slots by itself despite having 10 high-scoring pages
    assert plan["summary"]["pagesByFamily"]["smartmathpro"] == 2
    assert plan["summary"]["pagesByFamily"]["thai-exams"] == 2
    assert plan["summary"]["pagesByFamily"]["illustrative-math"] == 2
    assert plan["summary"]["pagesByFamily"]["mathsgenie"] == 2

    # Batching splits 8 pages with batch_size=4 into 2 batches of 4
    assert len(plan["batches"]) == 2
    assert [b["pageCount"] for b in plan["batches"]] == [4, 4]


# ---------------------------------------------------------------------------
# Answer-key page selection
# ---------------------------------------------------------------------------


def test_plan_skips_answer_keys_but_links_them_for_confirmation(tmp_path: Path) -> None:
    sdir = tmp_path / "sources"
    problem_path = "SmartMathPro/ชุด/โจทย์/paper-01.pdf"
    answer_path = "SmartMathPro/ชุด/เฉลย/paper-01.pdf"
    for rel in (problem_path, answer_path):
        target = sdir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"fixture source")
    registry = _write_fixture_registry(tmp_path / "registry.md")
    backlog = _write_fixture_backlog(tmp_path / "backlog.md")
    page = {"page": 1, "hits": 3, "terms": {"quadratic": 3}, "charLen": 800, "estimatedItems": 1}
    find_result = {
        "unitCode": UNIT,
        "track": "math",
        "sourcesDir": str(sdir),
        "terms": ["quadratic"],
        "coreMatches": [
            {
                "relPath": problem_path,
                "family": "SmartMathPro",
                "mode": "cores",
                "cacheFile": "p.json",
                "pages": [page],
            },
            {"relPath": answer_path, "family": "SmartMathPro", "mode": "cores", "cacheFile": "a.json", "pages": [page]},
        ],
    }
    plan = source_find.build_extraction_plan(
        find_result,
        budget_pages=5,
        budget_items=5,
        sources_dir=str(sdir),
        registry_path=str(registry),
        backlog_path=str(backlog),
    )
    assert [p["relPath"] for p in plan["selectedPages"]] == [problem_path]
    assert plan["summary"]["skippedAnswerKeyPages"] == 1
    assert plan["selectedPages"][0]["answerKeyPages"] == [
        {"family": "SmartMathPro", "relPath": answer_path, "page": 1, "cacheFile": "a.json", "hits": 3}
    ]
    assert "answer key: " + answer_path in source_find.format_plan_report(plan)
    worker_prompt = extract_cards_job.build_worker_prompt(UNIT, 1, sources_dir=str(sdir))
    assert f"Answer-key reference ONLY (do not mine): `{answer_path}` page=1" in worker_prompt
    assert "Consult only to confirm likely traps" in worker_prompt

    override = source_find.build_extraction_plan(
        find_result,
        budget_pages=5,
        budget_items=5,
        sources_dir=str(sdir),
        registry_path=str(registry),
        backlog_path=str(backlog),
        include_answer_keys=True,
    )
    assert {p["relPath"] for p in override["selectedPages"]} == {problem_path, answer_path}
    assert override["summary"]["includeAnswerKeys"] is True
    assert source_find._build_parser().parse_args([UNIT, "--plan", "--include-answer-keys"]).include_answer_keys


# ---------------------------------------------------------------------------
# 2. Budget caps (defaults 30/40 + explicit page & item overrides)
# ---------------------------------------------------------------------------


def test_plan_budget_caps_pages_and_items(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # 50 total pages (1 item each) -> default budget caps at 30 pages (40 items)
    sdir, reg, backlog = _setup_multi_family_sources(
        tmp_path,
        monkeypatch,
        smp_pages=20,
        thai_pages=10,
        mg_pages=10,
        im_pages=10,
        items_per_page=1,
    )
    find_res = source_find.find_sources(UNIT, sources_dir=str(sdir), registry_path=str(reg))
    default_plan = source_find.build_extraction_plan(
        find_res,
        sources_dir=str(sdir),
        registry_path=str(reg),
        backlog_path=str(backlog),
    )
    assert default_plan["budget"]["maxPages"] == 30
    assert default_plan["budget"]["maxItems"] == 40
    assert default_plan["summary"]["selectedPageCount"] == 30
    assert default_plan["summary"]["batchCount"] == 3

    # Item-budget cap: each page has 5 numbered items, budget_items=12 -> stops at 3 pages (5+5+2=12)
    sdir2 = tmp_path / "itemcap"
    sdir2_src, reg2, backlog2 = _setup_multi_family_sources(
        sdir2,
        monkeypatch,
        smp_pages=10,
        thai_pages=5,
        mg_pages=5,
        im_pages=0,
        items_per_page=5,
    )
    find_res2 = source_find.find_sources(UNIT, sources_dir=str(sdir2_src), registry_path=str(reg2))
    item_plan = source_find.build_extraction_plan(
        find_res2,
        budget_pages=30,
        budget_items=12,
        sources_dir=str(sdir2_src),
        registry_path=str(reg2),
        backlog_path=str(backlog2),
    )
    assert item_plan["summary"]["selectedPageCount"] == 3
    assert item_plan["summary"]["selectedEstimatedItems"] == 12
    assert [p["itemAllowance"] for p in item_plan["selectedPages"]] == [5, 5, 2]

    first_pages = {(p["relPath"], p["page"]) for p in item_plan["selectedPages"]}
    stop = item_plan["continuation"]["stopAfter"]
    assert (stop["relPath"], stop["page"]) == (
        item_plan["selectedPages"][-1]["relPath"],
        item_plan["selectedPages"][-1]["page"],
    )
    next_plan = source_find.build_extraction_plan(
        find_res2,
        budget_items=12,
        sources_dir=str(sdir2_src),
        registry_path=str(reg2),
        backlog_path=str(backlog2),
    )
    next_pages = {(p["relPath"], p["page"]) for p in next_plan["selectedPages"]}
    assert len(next_pages) == 3 and first_pages.isdisjoint(next_pages)
    assert next_plan["summary"]["skippedPlannedPages"] == 3

    reset = source_find.build_extraction_plan(
        find_res2,
        budget_items=12,
        sources_dir=str(sdir2_src),
        refresh=True,
        registry_path=str(reg2),
        backlog_path=str(backlog2),
    )
    assert {(p["relPath"], p["page"]) for p in reset["selectedPages"]} == first_pages


def test_exercise_heading_and_numbered_items_raise_rank() -> None:
    plain = {"hits": 2, "charLen": 600, "estimatedItems": 1}
    exercise = {**plain, "estimatedItems": 4, "exerciseHeading": True}
    args = {"registry_priorities": {}, "backlog_ranks": {}}
    first_score, _ = source_find._score_candidate_page("fixture.pdf", "fixture", plain, **args)
    exercise_score, breakdown = source_find._score_candidate_page("fixture.pdf", "fixture", exercise, **args)
    assert exercise_score > first_score
    assert breakdown["exerciseBoost"] > 0


# ---------------------------------------------------------------------------
# 3. Extraction ledger: incremental skip, hash-change refresh, --refresh flag
# ---------------------------------------------------------------------------


def test_ledger_skip_hash_change_and_refresh_flag(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sdir, reg, backlog = _setup_multi_family_sources(
        tmp_path,
        monkeypatch,
        smp_pages=2,
        thai_pages=1,
        mg_pages=0,
        im_pages=0,
        items_per_page=1,
    )
    find_res = source_find.find_sources(UNIT, sources_dir=str(sdir), registry_path=str(reg))
    plan1 = source_find.build_extraction_plan(
        find_res,
        sources_dir=str(sdir),
        registry_path=str(reg),
        backlog_path=str(backlog),
    )
    assert plan1["summary"]["selectedPageCount"] == 3

    # Record all 3 pages in _ledger.json using their current hashes
    ledger.record_batch_extractions(
        UNIT,
        [
            {
                "file": p["relPath"],
                "page": p["page"],
                "fileHash": p["fileHash"],
                "cardsProduced": [f"CORE-{idx}"],
            }
            for idx, p in enumerate(plan1["selectedPages"], 1)
        ],
        run_id="run-001",
        sources_dir=str(sdir),
    )
    assert Path(ledger.ledger_path(sources_dir=str(sdir))).is_file()

    # Re-plan without changes -> all 3 pages skipped via ledger
    plan2 = source_find.build_extraction_plan(
        find_res,
        sources_dir=str(sdir),
        registry_path=str(reg),
        backlog_path=str(backlog),
    )
    assert plan2["summary"]["selectedPageCount"] == 0
    assert plan2["summary"]["skippedLedgerPages"] == 3

    # --refresh overrides ledger and re-includes all 3 pages
    plan_refresh = source_find.build_extraction_plan(
        find_res,
        refresh=True,
        sources_dir=str(sdir),
        registry_path=str(reg),
        backlog_path=str(backlog),
    )
    assert plan_refresh["summary"]["selectedPageCount"] == 3
    assert plan_refresh["summary"]["skippedLedgerPages"] == 0

    # Modify SmartMathPro/smp.pdf bytes -> its content hash changes, so ONLY its 2 pages return!
    (sdir / "SmartMathPro" / "smp.pdf").write_bytes(b"%PDF-1.4 fixture-smp-v2-updated-bytes")
    plan_changed = source_find.build_extraction_plan(
        find_res,
        sources_dir=str(sdir),
        registry_path=str(reg),
        backlog_path=str(backlog),
    )
    assert plan_changed["summary"]["selectedPageCount"] == 2
    assert plan_changed["summary"]["skippedLedgerPages"] == 1
    assert all(p["relPath"] == "SmartMathPro/smp.pdf" for p in plan_changed["selectedPages"])


# ---------------------------------------------------------------------------
# 4. Batch novelty & saturation counting (scripts.source_gap --novelty)
# ---------------------------------------------------------------------------


def test_source_gap_novelty_fuzzy_duplicates_and_saturation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    sdir = tmp_path / "sources"
    existing = [
        _card(
            "CORE-EX-01",
            skill="Solve quadratic equations by completing the square",
            move="direct",
            traps=[{"tag": "t02-c01-u02-added-square-to-one-side-only-trap", "description": "One-sided add"}],
        ),
        _card(
            "CORE-EX-02",
            skill="Determine parameter bounds from quadratic discriminant condition",
            move="case-check",
            traps=[{"tag": "t02-c01-u02-discriminant-sign-error-trap", "description": "Sign error in -4ac"}],
        ),
    ]
    source_cores.save_core_cards(UNIT, existing, sources_dir=str(sdir))

    batch_file = tmp_path / "batch1.jsonl"
    batch_cards = [
        # 1. Fuzzy duplicate of CORE-EX-01 (same move, rephrased skill, same trap)
        _card(
            "CORE-B1-01",
            skill="Completing the square to solve monic quadratic equation",
            move="direct",
            traps=[{"tag": "t02-c01-u02-added-square-to-one-side-only-trap", "description": "Unbalanced add"}],
        ),
        # 2. Fuzzy duplicate of CORE-EX-02 (same move, fuzzy skill + fuzzy trap slug without unit prefix)
        _card(
            "CORE-B1-02",
            skill="Find unknown parameter using quadratic discriminant constraint",
            move="case-check",
            traps=[{"tag": "discriminant-sign-trap", "description": "Wrong sign on 4ac"}],
        ),
        # 3. Truly NEW core: different reasoningMove ("reverse") even on completing-the-square
        _card(
            "CORE-B1-03",
            skill="Recover quadratic coefficients from completed square vertex form",
            move="reverse",
            traps=[{"tag": "t02-c01-u02-vertex-shift-sign-trap", "description": "Flips h sign"}],
        ),
        # 4. Within-batch duplicate of CORE-B1-03 -> must count as duplicate, NOT second new core!
        _card(
            "CORE-B1-04",
            skill="Reconstruct quadratic coefficients from completed square form",
            move="reverse",
            traps=[{"tag": "t02-c01-u02-vertex-shift-sign-trap", "description": "Wrong sign on shift"}],
        ),
    ]
    batch_file.write_text("\n".join(json.dumps(c) for c in batch_cards) + "\n", encoding="utf-8")

    # Evaluate BEFORE appending to UNIT.jsonl
    nov = source_gap.compute_batch_novelty(UNIT, str(batch_file), sources_dir=str(sdir))
    assert nov["existingCardsCount"] == 2
    assert nov["batchCardsCount"] == 4
    assert nov["newCoresCount"] == 1
    assert nov["duplicateCardsCount"] == 3
    assert nov["belowSaturationThreshold"] is True
    assert [c["id"] for c in nov["newCards"]] == ["CORE-B1-03"]
    dup_by_id = {d["id"]: d["matchedCardId"] for d in nov["duplicateCards"]}
    assert dup_by_id["CORE-B1-01"] == "CORE-EX-01"
    assert dup_by_id["CORE-B1-02"] == "CORE-EX-02"
    assert dup_by_id["CORE-B1-04"] == "CORE-B1-03"

    # Evaluate AFTER appending batch cards to UNIT.jsonl -> self-copies excluded, identical result!
    for c in batch_cards:
        source_cores.append_core_card(UNIT, c, sources_dir=str(sdir))
    nov_post = source_gap.compute_batch_novelty(UNIT, str(batch_file), sources_dir=str(sdir))
    assert nov_post["newCoresCount"] == 1
    assert nov_post["duplicateCardsCount"] == 3

    # CLI check (human-readable + --json)
    rc = source_gap.main([UNIT, "--novelty", str(batch_file), "--sources-dir", str(sdir)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "1 new core(s), 3 duplicate(s)" in out
    assert "SATURATION SIGNAL" in out


def test_prg_novelty_detects_exact_and_reworded_cores_with_ad_hoc_tags(tmp_path: Path) -> None:
    baseline = [
        _prg_card(
            "CORE-PRG-OLD-01",
            skill="Trace promise reaction order relative to synchronous work",
            concept="Promise continuations run after the current stack and pass settled values downstream",
            trap="turn-order",
        ),
        _prg_card(
            "CORE-PRG-OLD-02",
            skill="Select array entries with a predicate and transform the retained values",
            concept="Filtering chooses entries while mapping transforms each retained entry",
            trap="collection-pipeline",
            kind="implement",
        ),
    ]
    exact = {
        **baseline[0],
        "id": "CORE-PRG-NEW-EXACT",
        "sourceRef": {**baseline[0]["sourceRef"], "item": "exact-copy"},
        "traps": [{"tag": "turn_order", "description": "Confuses deferred result flow"}],
    }
    near = _prg_card(
        "CORE-PRG-NEW-NEAR",
        skill="Observe promise reactions after immediate work has completed",
        concept="Deferred handlers receive the settled result after synchronous execution",
        trap="promise-reaction-sequence",
    )
    cards = [exact, near]
    for card in cards:
        is_duplicate, details = source_gap.cards_are_fuzzy_duplicate(card, baseline[0])
        assert is_duplicate
        assert details["duplicateType"] == ("exact" if card is exact else "near")
    assert source_gap._normalize_tag("PRG-T00-C03-Queue_Order-Trap") == source_gap._normalize_tag("queue order")
    is_duplicate, _ = source_gap.cards_are_fuzzy_duplicate(near, baseline[1])
    assert not is_duplicate  # Different archetype kinds do not collapse into one core.
    other_language = {**near, "language": "typescript"}
    is_duplicate, _ = source_gap.cards_are_fuzzy_duplicate(other_language, baseline[0])
    assert not is_duplicate


def test_prg_novelty_keeps_different_skills_separate_despite_generic_words() -> None:
    existing = _prg_card(
        "CORE-PRG-GENERIC-01",
        skill="Validate request payload before storing user preferences",
        concept="Check required fields and reject malformed input before writing preferences",
        trap="validation-order",
    )
    different_skill = _prg_card(
        "CORE-PRG-GENERIC-02",
        skill="Process network request input and return a response after retrying failures",
        concept="Handle request data and produce a result while limiting repeated attempts",
        trap="retry-budget",
    )

    is_duplicate, details = source_gap.cards_are_fuzzy_duplicate(different_skill, existing)

    assert not is_duplicate
    assert details["reason"] == "distinct core"


# ---------------------------------------------------------------------------
# 5. Worker extraction prompt generation & --commit validation/ledger/DONE_FILE
# ---------------------------------------------------------------------------


def test_extract_cards_job_prompt_and_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    sdir, reg, backlog = _setup_multi_family_sources(
        tmp_path,
        monkeypatch,
        smp_pages=2,
        thai_pages=1,
        mg_pages=0,
        im_pages=0,
        items_per_page=1,
    )
    # Give SmartMathPro page 1 a specific source number (73) to test copied-number rejection during --commit
    find_res = source_find.find_sources(UNIT, sources_dir=str(sdir), registry_path=str(reg))
    plan = source_find.build_extraction_plan(
        find_res,
        budget_pages=3,
        budget_items=10,
        batch_size=2,
        sources_dir=str(sdir),
        registry_path=str(reg),
        backlog_path=str(backlog),
    )
    assert plan["summary"]["batchCount"] == 2

    batch_out = tmp_path / "batch1.jsonl"
    done_file = tmp_path / "batch1.done"

    # 1. Generate worker prompt via CLI
    rc_prompt = extract_cards_job.main(
        [
            UNIT,
            "--batch",
            "1",
            "--sources-dir",
            str(sdir),
            "--batch-out",
            str(batch_out),
            "--done-file",
            str(done_file),
            "--run-id",
            "test-run-b1",
        ]
    )
    assert rc_prompt == 0
    prompt = capsys.readouterr().out
    assert f"Source Core-Card Extraction Job — {UNIT} (Batch 1/2)" in prompt
    assert "validate_core_card" in prompt
    assert "ZERO source wording" in prompt
    assert "ZERO source numbers" in prompt
    assert "NEVER extract from `openstax`" in prompt
    assert str(batch_out) in prompt
    assert str(done_file) in prompt
    assert f"CORE-{UNIT}-Rtest-run-b1-B01-01" in prompt
    assert "--commit" in prompt
    assert "source_gap" in prompt and "--novelty" in prompt
    # Both batch-1 pages appear in prompt
    b1_pages = plan["batches"][0]["pages"]
    for p in b1_pages:
        assert p["relPath"] in prompt
        assert p["fileHash"] in prompt

    # Out-of-range batch returns error
    rc_bad = extract_cards_job.main([UNIT, "--batch", "9", "--sources-dir", str(sdir)])
    assert rc_bad == 1
    assert "out of range" in capsys.readouterr().err

    # 2. Inject a distinctive number into cached text of page 0 to prove --commit validates against source text
    p0 = b1_pages[0]
    cache_path = sdir / "_index" / p0["cacheFile"]
    cache_doc = json.loads(cache_path.read_text(encoding="utf-8"))
    for entry in cache_doc["pages"]:
        if entry["page"] == p0["page"]:
            entry["text"] = "Question 1. Solve quadratic equation x^2 - 73x + 89 = 0 for distinct roots."
    cache_path.write_text(json.dumps(cache_doc), encoding="utf-8")

    # Bad card copying source number 73 -> --commit must fail without writing ledger or DONE_FILE
    bad_card = _card(
        "CORE-BAD-73",
        family=p0["family"],
        file=p0["relPath"],
        page=p0["page"],
        notes="Uses coefficient 73 from source equation",
    )
    batch_out.write_text(json.dumps(bad_card) + "\n", encoding="utf-8")
    rc_commit_fail = extract_cards_job.main(
        [
            UNIT,
            "--batch",
            "1",
            "--sources-dir",
            str(sdir),
            "--commit",
            str(batch_out),
            "--run-id",
            "test-run-b1",
            "--done-file",
            str(done_file),
        ]
    )
    assert rc_commit_fail == 1
    assert "digit run" in capsys.readouterr().err
    assert not done_file.exists()
    assert not Path(ledger.ledger_path(sources_dir=str(sdir))).exists()

    # 3. Valid card for page 0 only (page 1 yields 0 cards) -> --commit appends card, records BOTH pages in ledger, writes DONE_FILE
    good_card = _card(
        "CORE-U02-B01-01",
        family=p0["family"],
        file=p0["relPath"],
        page=p0["page"],
        notes="Abstract factoring pattern with distinct real roots",
    )
    batch_out.write_text(json.dumps(good_card) + "\n", encoding="utf-8")
    rc_commit_ok = extract_cards_job.main(
        [
            UNIT,
            "--batch",
            "1",
            "--sources-dir",
            str(sdir),
            "--commit",
            str(batch_out),
            "--run-id",
            "test-run-b1",
            "--done-file",
            str(done_file),
        ]
    )
    assert rc_commit_ok == 0
    commit_summary = json.loads(capsys.readouterr().out)
    assert commit_summary["cardsAppended"] == 1
    assert commit_summary["pagesRecorded"] == 2
    assert done_file.is_file() and done_file.stat().st_size > 0

    # Core cards file now contains CORE-U02-B01-01
    loaded_cards = source_cores.load_core_cards(UNIT, sources_dir=str(sdir))
    assert [c["id"] for c in loaded_cards] == ["CORE-U02-B01-01"]

    # Reusing an ID for different content fails explicitly and leaves the committed core file intact.
    conflicting = {**good_card, "notes": "A different abstract factoring pattern"}
    batch_out.write_text(json.dumps(conflicting) + "\n", encoding="utf-8")
    cores_before = Path(source_cores.cores_path(UNIT, sources_dir=str(sdir))).read_text(encoding="utf-8")
    rc_clash = extract_cards_job.main(
        [UNIT, "--batch", "1", "--sources-dir", str(sdir), "--commit", str(batch_out), "--run-id", "test-run-b1"]
    )
    assert rc_clash == 1
    assert "ID clash for CORE-U02-B01-01" in capsys.readouterr().err
    assert Path(source_cores.cores_path(UNIT, sources_dir=str(sdir))).read_text(encoding="utf-8") == cores_before

    # Ledger records BOTH pages from Batch 1 (page 0 with 1 card, page 1 with 0 cards)
    led = ledger.load_ledger(sources_dir=str(sdir))
    e0 = ledger.get_ledger_entry(led, UNIT, p0["relPath"], p0["page"])
    e1 = ledger.get_ledger_entry(led, UNIT, b1_pages[1]["relPath"], b1_pages[1]["page"])
    assert e0 is not None and e0["cardsProduced"] == ["CORE-U02-B01-01"] and e0["runId"] == "test-run-b1"
    assert e1 is not None and e1["cardsProduced"] == [] and e1["cardCount"] == 0

    # Re-running plan now skips the 2 committed pages and selects only the 1 remaining page from Batch 2!
    plan_after = source_find.build_extraction_plan(
        find_res,
        budget_pages=3,
        budget_items=10,
        batch_size=2,
        sources_dir=str(sdir),
        registry_path=str(reg),
        backlog_path=str(backlog),
    )
    assert plan_after["summary"]["skippedLedgerPages"] == 2
    assert plan_after["summary"]["selectedPageCount"] == 1
