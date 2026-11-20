"""Hermetic tests for cross-unit bridge problem infrastructure.

Covers:
1. Empty production MTH-BRIDGE vault + bridge archetype schema validation via quality_checks.
2. Eligibility (0 / 1 / 2 passed units, --min-mastery, --json, dormant message) via scripts.bridge_scope.
3. load_scope_archetypes("MTH-BRIDGE") filtering with injected eligible sets.
4. Bridge draft ingest (passing draft + originality gate + stamping references/unitCodes + file path)
   and gate failures (one unit only, step not touching a unit, level < 3, missing blindSolve).
5. covered_units & unit_relation_ids for bridge drills in notion_sync.drill_sync.
6. weak_spots & review_items multi-unit attribution without double-counting drill/trap totals.
7. Core-card `units` validation and scripts.source_gap "Bridge candidates" section.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

from code_engine import quality_checks
from math_engine import ai_drill_ingest, source_cores
from math_engine.bridge import (
    BRIDGE_SCOPE,
    validate_bridge_archetype,
    validate_bridge_vault,
)
from notion_sync import drill_sync
from scripts import bridge_scope, review_items, source_gap
from scripts import weak_spots as ws

U1 = "MTH-T09-C01-U01"
U2 = "MTH-T09-C02-U01"
U3 = "MTH-T09-C03-U01"
TRAP_BRIDGE = "bridge-conjugate-product-sign-trap"


def _bridge_archetype(
    key: str = "bridge-complex-quadratic-vieta",
    units: list[str] | None = None,
    **overrides,
) -> dict:
    unit_codes = units if units is not None else [U1, U2]
    arch = {
        "archetypeKey": key,
        "name": "Conjugate Root to Quadratic Constant",
        "unitCodes": unit_codes,
        "junction": "Complex conjugate pair from unit 1 feeds Vieta's product-of-roots relation in unit 2.",
        "skillsByUnit": {u: f"Skill for {u}" for u in unit_codes},
        "cognitiveTraps": [
            {
                "trapTag": TRAP_BRIDGE,
                "description": "Subtracts imaginary square instead of adding when multiplying conjugates.",
            }
        ],
        "level": 3,
        "levelNote": "Earns L3 by choosing conjugate-root symmetry before applying Vieta's product.",
        "figureNone": "Symbolic complex-quadratic junction; no geometric sketch is required.",
        "source": "OpenStax Algebra and Trigonometry 2e §2.4, §2.5; cores: thai-exams",
    }
    arch.update(overrides)
    return arch


def _write_bridge_vault(tmp_path: Path, archetypes: list[dict]) -> Path:
    vdir = tmp_path / "vault"
    vdir.mkdir(parents=True, exist_ok=True)
    (vdir / f"{BRIDGE_SCOPE}.json").write_text(
        json.dumps({"unitCode": BRIDGE_SCOPE, "archetypes": archetypes}, indent=2),
        encoding="utf-8",
    )
    return vdir


def _bridge_problem(**overrides) -> dict:
    prob = {
        "id": "Q01",
        "level": 3,
        "category": "Trap & Edge Case",
        "archetype": "problem-solving",
        "archetypeKey": "bridge-complex-quadratic-vieta",
        "form": "reverse",
        "context": "",
        "prompt": "A quadratic equation $x^2 - 6x + k = 0$ with real coefficients has a root $z = 3 + 4i$. Find $k$.",
        "display": "k = z \\cdot \\bar{z}",
        "plainText": "k = (3 + 4*i)*(3 - 4*i)",
        "givens": {"b_mag": 6, "re_z": 3, "im_z": 4},
        "checkpointHint": "Use the conjugate root pair and the product-of-roots relation.",
        "answerSpec": {"type": "number", "value": "25", "tolerance": 0.001},
        "answerPlain": "25",
        "answerDisplay": "25",
        "commonTrapTag": TRAP_BRIDGE,
        "trapValue": "-7",
        "trapDerivation": "3^2 - 4^2",
        "trapGivens": [3, 4],
        "verify": {"source": "25", "trapValue": "-7"},
        "steps": [
            {
                "latex": "\\bar{z} = 3 - 4i",
                "explain": "Apply the conjugate root theorem to find the second root.",
                "unit": U1,
            },
            {
                "latex": "k = (3 + 4i)(3 - 4i)",
                "explain": "Set the constant term equal to the product of the two roots.",
                "unit": U2,
            },
            {
                "latex": "k = 3^2 + 4^2",
                "explain": "Expand the conjugate product using i squared equals negative one.",
                "eq": ["3^2 + 4^2", "25"],
                "unit": U1,
            },
            {
                "latex": "k = 25",
                "explain": "Add the squared components to obtain the real constant.",
                "val": "25",
                "unit": U2,
            },
        ],
        "references": [U1, U2],
        "verificationLevel": "partial",
        "blindSolve": {
            "answer": "25",
            "ambiguous": False,
            "setup": "translate",
            "strategy": "choose",
            "check": "none",
            "task": "compute",
            "reverse": True,
            "steps": 4,
        },
        "review": {"verdict": "pass", "note": "Verified bridge junction, steps, and trap."},
    }
    prob.update(overrides)
    return prob


def _seed_unit_progress(
    data_root: Path,
    progress_dir: Path,
    unit_code: str,
    *,
    score_pattern: list[tuple[int, bool]],
    drill_suffix: str = "01",
) -> str:
    """Create one unit drill and matching progress file.

    ``score_pattern`` is a list of ``(level, correct)`` tuples.
    """
    drill_id = f"DRL-{unit_code}-{drill_suffix}"
    udir = data_root / unit_code
    udir.mkdir(parents=True, exist_ok=True)
    progress_dir.mkdir(parents=True, exist_ok=True)

    problems = []
    prog_probs = {}
    for idx, (lvl, ok) in enumerate(score_pattern, 1):
        qid = f"Q{idx:02d}"
        problems.append(
            {
                "id": qid,
                "level": lvl,
                "form": "direct",
                "unitCode": unit_code,
                "archetypeKey": f"arch-{unit_code}",
            }
        )
        verdict = "correct" if ok else "incorrect"
        prog_probs[qid] = {
            "attempts": [{"verdict": verdict, "ts": f"2026-11-{idx:02d}T10:00:00Z"}],
            "score": 1 if ok else 0,
        }

    (udir / f"{drill_id}.json").write_text(
        json.dumps({"drillId": drill_id, "unitCode": unit_code, "problems": problems}),
        encoding="utf-8",
    )
    (progress_dir / f"{drill_id}.json").write_text(
        json.dumps({"drillId": drill_id, "problems": prog_probs}),
        encoding="utf-8",
    )
    return drill_id


# ---------------------------------------------------------------------------
# 1. Production empty vault & bridge archetype schema validation
# ---------------------------------------------------------------------------


def test_real_bridge_vault_starts_empty_and_passes_quality_checks() -> None:
    vault_path = Path("math_engine/reasoning_vault/MTH-BRIDGE.json")
    assert vault_path.exists()
    data = json.loads(vault_path.read_text(encoding="utf-8"))
    assert data["unitCode"] == BRIDGE_SCOPE
    assert data["archetypes"] == []
    assert validate_bridge_vault(data) == []

    errors, count = quality_checks.check_bridge_vault()
    assert errors == []
    assert count == 0


def test_bridge_archetype_schema_validation_passes_and_catches_errors(tmp_path: Path) -> None:
    good = _bridge_archetype()
    assert validate_bridge_archetype(good) == []

    # Invalid cases
    bad_one_unit = _bridge_archetype(units=[U1])
    assert any("at least 2" in e for e in validate_bridge_archetype(bad_one_unit))

    bad_level = _bridge_archetype(level=2)
    assert any("level" in e for e in validate_bridge_archetype(bad_level))

    bad_junction = _bridge_archetype(junction="   ")
    assert any("junction" in e for e in validate_bridge_archetype(bad_junction))

    bad_skills = _bridge_archetype(skillsByUnit={U1: "Only one unit"})
    assert any("missing skill" in e for e in validate_bridge_archetype(bad_skills))

    bad_traps = _bridge_archetype(cognitiveTraps=[])
    assert any("cognitiveTraps" in e for e in validate_bridge_archetype(bad_traps))

    bad_figure = _bridge_archetype()
    del bad_figure["figureNone"]
    assert any("figureBuilders" in e for e in validate_bridge_archetype(bad_figure))

    bad_source = _bridge_archetype(source="")
    assert any("source" in e for e in validate_bridge_archetype(bad_source))

    # Hooked into code_engine.quality_checks --check-vaults
    vdir = _write_bridge_vault(tmp_path, [bad_level])
    errs, count = quality_checks.check_bridge_vault(math_vault_dir=vdir)
    assert count == 1
    assert any("level" in e for e in errs)


# ---------------------------------------------------------------------------
# 2. Eligibility: scripts/bridge_scope.py (0 / 1 / 2 passed units)
# ---------------------------------------------------------------------------


def test_bridge_scope_eligibility_zero_one_two_units(tmp_path: Path, capsys) -> None:
    vdir = _write_bridge_vault(
        tmp_path,
        [
            _bridge_archetype("bridge-u1-u2", [U1, U2]),
            _bridge_archetype("bridge-u1-u3", [U1, U3]),
        ],
    )
    data_root = tmp_path / "data"
    progress_dir = tmp_path / "progress"
    data_root.mkdir()
    progress_dir.mkdir()

    # 0 passed units -> dormant
    rep0 = bridge_scope.evaluate_bridge_scope(str(data_root), str(progress_dir), str(vdir))
    assert rep0["dormant"] is True
    assert rep0["eligibleUnitCount"] == 0
    assert rep0["eligibleArchetypes"] == []
    assert "dormant: 0 eligible unit(s), need ≥2" in bridge_scope.format_bridge_scope(rep0)

    # 1 passed unit (U1 mastery >= 2) + 1 failing unit (U3 mastery == 1) -> still dormant
    _seed_unit_progress(data_root, progress_dir, U1, score_pattern=[(1, True), (2, True)])
    _seed_unit_progress(data_root, progress_dir, U3, score_pattern=[(1, False), (2, False)])
    rep1 = bridge_scope.evaluate_bridge_scope(str(data_root), str(progress_dir), str(vdir))
    assert rep1["dormant"] is True
    assert rep1["eligibleUnitCount"] == 1
    assert [u["unitCode"] for u in rep1["eligibleUnits"]] == [U1]
    assert [u["unitCode"] for u in rep1["pendingUnits"]] == [U3]
    assert rep1["eligibleArchetypes"] == []
    assert "dormant: 1 eligible unit(s), need ≥2" in bridge_scope.format_bridge_scope(rep1)

    # 2 passed units (U1 + U2) -> active, bridge-u1-u2 eligible, bridge-u1-u3 still blocked
    _seed_unit_progress(data_root, progress_dir, U2, score_pattern=[(2, True), (3, True)])
    rep2 = bridge_scope.evaluate_bridge_scope(str(data_root), str(progress_dir), str(vdir))
    assert rep2["dormant"] is False
    assert rep2["eligibleUnitCount"] == 2
    assert [u["unitCode"] for u in rep2["eligibleUnits"]] == [U1, U2]
    assert [a["archetypeKey"] for a in rep2["eligibleArchetypes"]] == ["bridge-u1-u2"]
    assert [a["archetypeKey"] for a in rep2["blockedArchetypes"]] == ["bridge-u1-u3"]
    assert rep2["blockedArchetypes"][0]["missingUnits"] == [U3]

    # --min-mastery 3 makes U1/U2 (mastery 2) dormant again
    rep_m3 = bridge_scope.evaluate_bridge_scope(str(data_root), str(progress_dir), str(vdir), min_mastery=3)
    assert rep_m3["dormant"] is True
    assert rep_m3["eligibleUnitCount"] == 0

    # CLI --json output
    rc = bridge_scope.main(
        ["--data-root", str(data_root), "--progress-dir", str(progress_dir), "--vault-dir", str(vdir), "--json"]
    )
    assert rc == 0
    cli_payload = json.loads(capsys.readouterr().out)
    assert cli_payload["status"] == "active"
    assert cli_payload["eligibleUnitCount"] == 2


def test_bridge_scope_worktree_reads_main_checkout_progress_and_env_wins(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("PROGRESS_DIR", raising=False)
    monkeypatch.delenv("LEARNINGOS_PILOT", raising=False)

    main = tmp_path / "main"
    (main / ".git" / "worktrees" / "wt-feature").mkdir(parents=True)
    main_progress = main / "progress"

    wt = tmp_path / "wt-feature"
    wt.mkdir()
    (wt / ".git").write_text(f"gitdir: {main / '.git' / 'worktrees' / 'wt-feature'}\n", encoding="utf-8")
    (wt / "id_map.json").write_text("{}", encoding="utf-8")
    wt_data = wt / "drills" / "data"
    vdir = _write_bridge_vault(wt, [_bridge_archetype("bridge-u1-u2", [U1, U2])])

    _seed_unit_progress(wt_data, main_progress, U1, score_pattern=[(1, True), (2, True)])
    _seed_unit_progress(wt_data, main_progress, U2, score_pattern=[(2, True), (3, True)])

    # From the worktree (which has no local progress/), resolve_progress_dir and evaluate_bridge_scope
    # read the main checkout's progress/ and report active instead of dormant.
    monkeypatch.chdir(wt)
    assert bridge_scope.resolve_progress_dir() == str(main_progress)
    rep = bridge_scope.evaluate_bridge_scope(data_root=str(wt_data), vault_dir=str(vdir))
    assert rep["dormant"] is False
    assert [u["unitCode"] for u in rep["eligibleUnits"]] == [U1, U2]
    assert [a["archetypeKey"] for a in rep["eligibleArchetypes"]] == ["bridge-u1-u2"]

    # PROGRESS_DIR env still wins over the main checkout's progress/.
    env_progress = tmp_path / "env_progress"
    env_progress.mkdir()
    monkeypatch.setenv("PROGRESS_DIR", str(env_progress))
    assert bridge_scope.resolve_progress_dir() == str(env_progress)
    rep_env = bridge_scope.evaluate_bridge_scope(data_root=str(wt_data), vault_dir=str(vdir))
    assert rep_env["dormant"] is True
    assert rep_env["eligibleUnitCount"] == 0

    # Explicit progress_dir argument wins over PROGRESS_DIR env.
    assert bridge_scope.resolve_progress_dir(str(main_progress)) == str(main_progress)

    # A worktree's own progress/ wins when present (matching notion_sync.client.load_env).
    monkeypatch.delenv("PROGRESS_DIR")
    wt_progress = wt / "progress"
    wt_progress.mkdir()
    assert bridge_scope.resolve_progress_dir() == str(wt_progress)

    # Plain non-worktree checkout without progress/ stays on its own default path.
    plain = tmp_path / "plain"
    (plain / ".git").mkdir(parents=True)
    monkeypatch.chdir(plain)
    assert bridge_scope.main_checkout_progress_dir() is None
    assert bridge_scope.resolve_progress_dir() == str(plain / "progress")


# ---------------------------------------------------------------------------
# 3. load_scope_archetypes("MTH-BRIDGE") filtering
# ---------------------------------------------------------------------------


def test_load_scope_archetypes_bridge_filtering(tmp_path: Path) -> None:
    vdir = _write_bridge_vault(
        tmp_path,
        [
            _bridge_archetype("bridge-u1-u2", [U1, U2]),
            _bridge_archetype("bridge-u2-u3", [U2, U3]),
        ],
    )
    # Dormant when < 2 eligible units
    assert ai_drill_ingest.load_scope_archetypes(BRIDGE_SCOPE, str(vdir), eligible_units=set()) == []
    assert ai_drill_ingest.load_scope_archetypes(BRIDGE_SCOPE, str(vdir), eligible_units={U1}) == []

    # Exactly {U1, U2} unlocks only bridge-u1-u2
    found = ai_drill_ingest.load_scope_archetypes(BRIDGE_SCOPE, str(vdir), eligible_units={U1, U2})
    assert [a["archetypeKey"] for a in found] == ["bridge-u1-u2"]
    assert found[0]["_vaultFile"] == BRIDGE_SCOPE

    # All 3 units unlock both
    found_all = ai_drill_ingest.load_scope_archetypes(BRIDGE_SCOPE, str(vdir), eligible_units={U1, U2, U3})
    assert [a["archetypeKey"] for a in found_all] == ["bridge-u1-u2", "bridge-u2-u3"]

    # Non-bridge scopes never receive bridge archetypes
    assert ai_drill_ingest.load_scope_archetypes(U1, str(vdir)) == []


# ---------------------------------------------------------------------------
# 4. Ingest of bridge draft fixture + gate failures
# ---------------------------------------------------------------------------


def test_bridge_draft_passes_check_and_ingests_to_mth_bridge(tmp_path: Path) -> None:
    vdir = _write_bridge_vault(tmp_path, [_bridge_archetype()])
    draft = {
        "unitCode": BRIDGE_SCOPE,
        "subject": "MATH",
        "problems": [_bridge_problem()],
    }

    errs = ai_drill_ingest.check_ai_drill(draft, vault_dir=str(vdir), eligible_units={U1, U2})
    assert errs == []

    data_root = tmp_path / "data"
    saved = ai_drill_ingest.ingest_ai_drill(
        copy.deepcopy(draft),
        data_root=str(data_root),
        vault_dir=str(vdir),
        eligible_units={U1, U2},
    )
    assert saved["drillId"] == "DRL-MTH-BRIDGE-01"
    expected_path = data_root / BRIDGE_SCOPE / "DRL-MTH-BRIDGE-01.json"
    assert expected_path.exists()
    prob = saved["problems"][0]
    assert prob["unitCodes"] == [U1, U2]
    assert prob["references"] == [U1, U2]
    assert saved["topicCode"] == BRIDGE_SCOPE
    assert saved["chapterCode"] == BRIDGE_SCOPE


def test_bridge_gate_rejects_one_unit_missing_step_unit_and_low_level(tmp_path: Path) -> None:
    vdir = _write_bridge_vault(tmp_path, [_bridge_archetype()])

    # Gate failure 1: references only one unit
    one_unit_draft = {
        "unitCode": BRIDGE_SCOPE,
        "problems": [_bridge_problem(references=[U1])],
    }
    errs_one = ai_drill_ingest.check_ai_drill(one_unit_draft, vault_dir=str(vdir), eligible_units={U1, U2})
    assert any("at least 2 distinct units" in e for e in errs_one)

    # Gate failure 2: steps do not touch U2
    missing_step_prob = _bridge_problem()
    for st in missing_step_prob["steps"]:
        st["unit"] = U1
    missing_step_draft = {"unitCode": BRIDGE_SCOPE, "problems": [missing_step_prob]}
    errs_step = ai_drill_ingest.check_ai_drill(missing_step_draft, vault_dir=str(vdir), eligible_units={U1, U2})
    assert any("missing step tag" in e and U2 in e for e in errs_step)

    # Gate failure 3: L2 bridge problem rejected
    low_level_prob = _bridge_problem(level=2)
    low_level_prob.pop("blindSolve", None)
    errs_lvl = ai_drill_ingest.check_ai_drill(
        {"unitCode": BRIDGE_SCOPE, "problems": [low_level_prob]},
        vault_dir=str(vdir),
        eligible_units={U1, U2},
    )
    assert any("L3+" in e for e in errs_lvl)

    # Gate failure 4: missing blindSolve rejected (existing L3+ gate preserved)
    no_bs = _bridge_problem()
    no_bs.pop("blindSolve")
    errs_bs = ai_drill_ingest.check_ai_drill(
        {"unitCode": BRIDGE_SCOPE, "problems": [no_bs]},
        vault_dir=str(vdir),
        eligible_units={U1, U2},
    )
    assert any("blindSolve" in e for e in errs_bs)

    # Gate failure 5: dormant / ineligible units reject draft
    errs_dormant = ai_drill_ingest.check_ai_drill(
        {"unitCode": BRIDGE_SCOPE, "problems": [_bridge_problem()]},
        vault_dir=str(vdir),
        eligible_units={U1},
    )
    assert any("not yet eligible" in e for e in errs_dormant)


def test_bridge_originality_gate_checks_component_unit_sources(tmp_path: Path) -> None:
    vdir = _write_bridge_vault(tmp_path, [_bridge_archetype()])
    sources_dir = tmp_path / "sources"
    idx_dir = sources_dir / "_index"
    idx_dir.mkdir(parents=True)
    source_text = "A quadratic equation x^2 - 6x + k = 0 with real coefficients has a root z = 3 + 4i. Find k."
    (idx_dir / "pdf_u1.json").write_text(
        json.dumps(
            {
                "relPath": "thai-exams/mock.pdf",
                "family": "thai-exams",
                "mode": "cores",
                "pages": [{"page": 1, "text": source_text, "isImagePage": False}],
            }
        ),
        encoding="utf-8",
    )
    (idx_dir / f"located_{U1}.json").write_text(
        json.dumps(
            {
                "unitCode": U1,
                "terms": ["complex"],
                "matches": [{"relPath": "thai-exams/mock.pdf", "cacheFile": "pdf_u1.json", "pages": [{"page": 1}]}],
            }
        ),
        encoding="utf-8",
    )
    draft = {"unitCode": BRIDGE_SCOPE, "problems": [_bridge_problem()]}
    errs = ai_drill_ingest.check_ai_drill(
        draft,
        vault_dir=str(vdir),
        check_originality=True,
        sources_dir=str(sources_dir),
        eligible_units={U1, U2},
    )
    assert any("Originality gate failed" in e for e in errs)


# ---------------------------------------------------------------------------
# 5. covered_units for bridge drills (Notion sync coverage)
# ---------------------------------------------------------------------------


def test_covered_units_includes_all_bridge_problem_units() -> None:
    id_map = {
        U1: {"id": "page-u1", "title": "Unit 1"},
        U2: {"id": "page-u2", "title": "Unit 2"},
        U3: {"id": "page-u3", "title": "Unit 3"},
        "CON-VIETA": {"id": "page-con"},
    }
    bridge_drill = {
        "unitCode": BRIDGE_SCOPE,
        "problems": [
            {"id": "Q01", "unitCodes": [U1, U2], "references": [U1, U2, "CON-VIETA"]},
            {"id": "Q02", "references": [U2, U3]},
        ],
    }
    assert drill_sync.covered_units(bridge_drill, BRIDGE_SCOPE, id_map) == [U1, U2, U3]
    assert drill_sync.unit_relation_ids(bridge_drill, BRIDGE_SCOPE, id_map) == ["page-u1", "page-u2", "page-u3"]


# ---------------------------------------------------------------------------
# 6. weak_spots & review_items attribution without double-counting
# ---------------------------------------------------------------------------


def test_weak_spots_and_review_items_attribute_bridge_without_double_counting(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    progress_dir = tmp_path / "progress"
    bdir = data_root / BRIDGE_SCOPE
    bdir.mkdir(parents=True)
    progress_dir.mkdir(parents=True)

    drill_id = "DRL-MTH-BRIDGE-01"
    (bdir / f"{drill_id}.json").write_text(
        json.dumps(
            {
                "drillId": drill_id,
                "unitCode": BRIDGE_SCOPE,
                "problems": [
                    {
                        "id": "Q01",
                        "level": 4,
                        "form": "reverse",
                        "archetypeKey": "bridge-complex-quadratic-vieta",
                        "commonTrapTag": TRAP_BRIDGE,
                        "unitCodes": [U1, U2],
                        "references": [U1, U2],
                    },
                    {
                        "id": "Q02",
                        "level": 3,
                        "form": "direct",
                        "archetypeKey": "bridge-complex-quadratic-vieta",
                        "commonTrapTag": TRAP_BRIDGE,
                        "unitCodes": [U1, U2],
                        "references": [U1, U2],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    (progress_dir / f"{drill_id}.json").write_text(
        json.dumps(
            {
                "drillId": drill_id,
                "problems": {
                    "Q01": {
                        "attempts": [{"verdict": "correct", "ts": "2026-11-10T10:00:00Z"}],
                        "score": 1,
                    },
                    "Q02": {
                        "attempts": [
                            {"verdict": "incorrect", "ts": "2026-11-11T10:00:00Z", "matchedTrap": TRAP_BRIDGE},
                            {"verdict": "incorrect", "ts": "2026-11-11T10:05:00Z", "matchedTrap": TRAP_BRIDGE},
                        ],
                        "score": 0,
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    loaded = ws.load_items(str(data_root), str(progress_dir))
    # Exactly 2 Items (one per problem), never duplicated!
    assert len(loaded) == 2
    assert loaded[0].units == (U1, U2)

    # Trap matched twice on Q02 -> matches == 2 (not 4!), drills == 1 (not 2!), attributed to both U1 and U2
    traps = ws.trap_status(loaded)
    assert traps[TRAP_BRIDGE]["matches"] == 2
    assert traps[TRAP_BRIDGE]["drills"] == 1
    assert traps[TRAP_BRIDGE]["units"] == [U1, U2]

    # Report attributes evidence to both U1 and U2 with drillCount == 1 each
    rep_all = ws.report_json(None, str(data_root), str(progress_dir))
    by_unit = {u["unitCode"]: u for u in rep_all["units"]}
    assert set(by_unit) == {U1, U2}
    for code in (U1, U2):
        assert by_unit[code]["itemCount"] == 2
        assert by_unit[code]["drillCount"] == 1
        assert by_unit[code]["open"][0]["id"] == TRAP_BRIDGE
        assert by_unit[code]["open"][0]["matches"] == 2

    # Scoped report only emits the requested unit
    rep_u1 = ws.report_json(U1, str(data_root), str(progress_dir))
    assert [u["unitCode"] for u in rep_u1["units"]] == [U1]

    # review_update computes mastery for both constituent units from the bridge drill
    upd1 = ws.review_update(U1, None, "2026-11-12", str(data_root), str(progress_dir))
    upd2 = ws.review_update(U2, None, "2026-11-12", str(data_root), str(progress_dir))
    assert upd1 is not None and upd2 is not None
    assert upd1["mastery"] == 2 and upd2["mastery"] == 2

    # review_items schedules 2 items total (no duplicates), matching unit:U1, unit:U2, chapter:C01, chapter:C02
    sched = review_items.build_schedule_from_progress(str(data_root), str(progress_dir))
    assert len(sched) == 2
    q1_item = sched[f"{drill_id}/Q01"]
    assert q1_item["unitCode"] == BRIDGE_SCOPE
    assert q1_item["unitCodes"] == [U1, U2]
    for scope_str in (f"unit:{U1}", f"unit:{U2}", f"unit:{BRIDGE_SCOPE}", "chapter:MTH-T09-C01", "chapter:MTH-T09-C02"):
        due = review_items.get_due_items(
            today="2026-12-31",
            scope=scope_str,
            data_root=str(data_root),
            progress_dir=str(progress_dir),
        )
        assert len(due) == 2, f"Expected 2 due items for scope {scope_str}"


# ---------------------------------------------------------------------------
# 7. Core card `units` schema + scripts/source_gap.py Bridge candidates
# ---------------------------------------------------------------------------


def _sample_card(**overrides) -> dict:
    card = {
        "id": "CORE-BRIDGE-01",
        "unitCode": U1,
        "sourceRef": {"family": "thai-exams/tcas", "file": "exam.pdf", "page": 2, "item": "Q05"},
        "skill": "Combine conjugate root symmetry with Vieta product of roots",
        "reasoningMove": "multi-relation",
        "difficultyDriver": "Unknown quadratic coefficient determined from complex root",
        "level": 4,
        "traps": [{"tag": TRAP_BRIDGE, "description": "Sign error in conjugate product"}],
        "format": {"kind": "choice", "optionCount": 5},
        "representation": "symbolic",
    }
    card.update(overrides)
    return card


def test_core_card_units_validation_and_source_gap_bridge_candidates(tmp_path: Path, monkeypatch) -> None:
    # Synthetic U1/U2/U3 unit codes are not in id_map.json; inject them for hermetic laterUnit validation.
    monkeypatch.setattr(source_cores, "load_valid_unit_codes", lambda id_map_path=None: {U1: "U1", U2: "U2", U3: "U3"})

    # Schema validation for optional `units`
    assert source_cores.validate_core_card(_sample_card(units=[U1, U2])) == []
    assert any("at least 2" in e for e in source_cores.validate_core_card(_sample_card(units=[U1])))
    assert any("duplicate" in e for e in source_cores.validate_core_card(_sample_card(units=[U1, U1])))

    # source_gap groups multi-unit cards by unit pair and marks eligibility
    vault_dir = tmp_path / "vault"
    vault_dir.mkdir()
    (vault_dir / f"{U1}.json").write_text(json.dumps({"unitCode": U1, "archetypes": []}), encoding="utf-8")

    cards = [
        _sample_card(id="CORE-B1", units=[U2, U1]),  # reversed order should normalize to (U1, U2)
        _sample_card(id="CORE-B2", units=[U1, U2], skill="Complex modulus feeding quadratic discriminant bound"),
        _sample_card(id="CORE-B3", units=[U1, U3], laterUnit=U3, skill="Complex power feeding geometric sequence sum"),
        _sample_card(id="CORE-SINGLE"),  # single-unit card -> not a bridge candidate
    ]
    source_cores.save_core_cards(U1, cards, sources_dir=str(tmp_path))

    report = source_gap.build_gap_report(
        U1,
        sources_dir=str(tmp_path),
        vault_dir=str(vault_dir),
        eligible_units={U1, U2},
    )
    candidates = report["bridgeCandidates"]
    assert len(candidates) == 2

    pair_12 = next(c for c in candidates if c["units"] == [U1, U2])
    assert pair_12["eligible"] is True
    assert pair_12["missingUnits"] == []
    assert [c["id"] for c in pair_12["cards"]] == ["CORE-B1", "CORE-B2"]

    pair_13 = next(c for c in candidates if c["units"] == [U1, U3])
    assert pair_13["eligible"] is False
    assert pair_13["missingUnits"] == [U3]
    assert [c["id"] for c in pair_13["cards"]] == ["CORE-B3"]

    text = source_gap.format_gap_report(report)
    assert "Bridge candidates (2 pair(s), 3 card(s)):" in text
    assert f"{U1} + {U2} [ELIGIBLE] (2 card(s)):" in text
    assert f"{U1} + {U3} [not eligible — needs {U3}] (1 card(s)):" in text
