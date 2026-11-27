"""Hermetic tests for the source-synthesis pipeline.

Covers core-card schema & copied-number validation, originality gate (CLI + ingest & variant_bank
integration), scripts.source_find (term matching, scope-only OpenStax, scans, zip PDFs, cache),
and scripts.source_gap (matched/unmatched cards, new traps, missing moves/levels, exam formats,
laterUnit grouping). Never reads the real ``sources/`` directory.
"""

from __future__ import annotations

import builtins
import copy
import importlib.util
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from math_engine import ai_drill_ingest, source_cores, variant_bank
from math_engine.source_cores import code_originality, originality
from scripts import source_cores_retag, source_find, source_gap

ROOT = Path(__file__).resolve().parent.parent


def _sample_card(**overrides) -> dict:
    card = {
        "id": "CORE-MTH-T02-C01-U01-01",
        "unitCode": "MTH-T02-C01-U01",
        "sourceRef": {
            "family": "thai-exams/tcas68-a-level",
            "file": "math1-2568.pdf",
            "page": 4,
            "item": "Q12",
        },
        "skill": "Rationalize a complex quotient using the denominator conjugate",
        "reasoningMove": "reverse",
        "difficultyDriver": "Unknown real coefficient inside numerator determined from target imaginary part",
        "level": 3,
        "traps": [
            {
                "tag": "t02-c01-u01-denominator-conjugate-sign-error-trap",
                "description": "Subtracts squared imaginary coefficient instead of adding in denominator",
            }
        ],
        "format": {
            "kind": "choice",
            "optionCount": 5,
            "distractorPatterns": ["denominator sign flip", "omitted conjugate on numerator"],
        },
        "representation": "symbolic",
        "notes": "Tests reverse solving with complex division",
    }
    card.update(overrides)
    return card


def _sample_prg_card(**overrides) -> dict:
    card = {
        "profile": "prg",
        "id": "CORE-PRG-T00-C03-U01-01",
        "unitCode": "PRG-T00-C03-U01",
        "sourceRef": {
            "family": "prg/exercism-typescript",
            "file": "concepts/example.ts",
            "page": "L1-L18",
            "item": "exercise source",
        },
        "language": "typescript",
        "archetypeKind": "find-the-bug",
        "skill": "Preserve narrowing across a guarded property access",
        "concept": "discriminated unions",
        "bugPattern": "A mutable alias invalidates a previously established type guard",
        "testsCatch": "A valid variant fails after control flow crosses a mutation boundary",
        "difficultyDriver": "Reason across a helper call that can change the discriminant",
        "level": 3,
        "traps": [{"tag": "mutation-breaks-narrowing", "description": "Trusts stale narrowed state"}],
        "qualityCheckIdeas": [
            {"id": "QC-stable-boundary", "check": "Narrowed values remain stable across helper calls"}
        ],
    }
    card.update(overrides)
    return card


def _minimal_pdf_bytes(text: str) -> bytes:
    """Build a tiny, valid single-page PDF 1.4 containing ``text`` (pure Python, no external libs)."""
    safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 72 720 Td ({safe}) Tj ET\n".encode("latin-1")
    objs = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n",
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        (f"5 0 obj << /Length {len(stream)} >> stream\n".encode("ascii") + stream + b"endstream endobj\n"),
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objs:
        offsets.append(len(out))
        out.extend(obj)
    xref_pos = len(out)
    out.extend(f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode("ascii"))
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    out.extend(f"trailer << /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("ascii"))
    return bytes(out)


def _write_located_cache(sources_dir: Path, unit_code: str, rel_path: str, page_text: str) -> None:
    idx_dir = sources_dir / "_index"
    idx_dir.mkdir(parents=True, exist_ok=True)
    cache_file = "pdf_testfixture0001.json"
    (idx_dir / cache_file).write_text(
        json.dumps(
            {
                "relPath": rel_path,
                "family": source_cores.family_root(rel_path),
                "mode": source_cores.family_mode(rel_path),
                "mtime": 1.0,
                "size": 100,
                "pages": [{"page": 1, "text": page_text, "isImagePage": False}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (idx_dir / f"located_{unit_code}.json").write_text(
        json.dumps(
            {
                "unitCode": unit_code,
                "terms": ["complex"],
                "matches": [
                    {
                        "relPath": rel_path,
                        "family": source_cores.family_root(rel_path),
                        "mode": source_cores.family_mode(rel_path),
                        "cacheFile": cache_file,
                        "totalHits": 2,
                        "pages": [{"page": 1, "hits": 2, "terms": {"complex": 2}}],
                        "imagePages": [],
                    }
                ],
                "imageOnlyFiles": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# 1. Sources directory resolution & core-card schema validation
# ---------------------------------------------------------------------------


def test_resolve_sources_dir_env_and_worktree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    main_repo = tmp_path / "main-repo"
    wt_dir = tmp_path / "wt-branch"
    git_wt = main_repo / ".git" / "worktrees" / "wt-branch"
    git_wt.mkdir(parents=True)
    wt_dir.mkdir()
    (wt_dir / ".git").write_text(f"gitdir: {git_wt}\n", encoding="utf-8")

    monkeypatch.delenv("LEARNINGOS_SOURCES_DIR", raising=False)
    assert source_cores.resolve_sources_dir(cwd=str(wt_dir)) == str(main_repo / "sources")

    custom = tmp_path / "custom-sources"
    monkeypatch.setenv("LEARNINGOS_SOURCES_DIR", str(custom))
    assert source_cores.resolve_sources_dir(cwd=str(wt_dir)) == str(custom)


def test_core_card_schema_valid_and_invalid() -> None:
    schema = source_cores.load_schema()
    assert schema["title"] == "Source Core Card"
    assert source_cores.validate_core_card(_sample_card()) == []
    assert source_cores.validate_core_card(_sample_card(laterUnit="MTH-T02-C01-U03")) == []

    # Missing required field
    bad_missing = _sample_card()
    del bad_missing["reasoningMove"]
    assert any("reasoningMove" in e for e in source_cores.validate_core_card(bad_missing))

    # Invalid enum & bounds
    assert any("reasoningMove" in e for e in source_cores.validate_core_card(_sample_card(reasoningMove="guess")))
    assert any("level" in e for e in source_cores.validate_core_card(_sample_card(level=6)))
    assert any("level" in e for e in source_cores.validate_core_card(_sample_card(level=True)))
    assert any("representation" in e for e in source_cores.validate_core_card(_sample_card(representation="audio")))
    assert any("format.kind" in e for e in source_cores.validate_core_card(_sample_card(format={"kind": "essay"})))

    # OpenStax family rejected for core cards (scope only)
    openstax_card = _sample_card(
        sourceRef={"family": "openstax/math/algebra-trig", "file": "ch2.pdf", "page": 10, "item": "Ex 1"}
    )
    assert any("scope-only" in e for e in source_cores.validate_core_card(openstax_card))

    # SmartMathPro is registered as a cores family with priority and Thai-exam flag
    assert source_cores.SOURCE_FAMILIES["smartmathpro"] == {
        "mode": "cores",
        "priority": 100,
        "thaiExam": True,
        "label": "SmartMathPro Thai past papers",
    }
    assert source_cores.family_mode("SmartMathPro/tcas68.pdf") == "cores"
    smp_card = _sample_card(sourceRef={"family": "smartmathpro", "file": "tcas68.pdf", "page": 2, "item": "Q3"})
    assert source_cores.validate_core_card(smp_card) == []

    # units[] validates every code against id_map.json (or UNMAPPED:) like laterUnit
    assert (
        source_cores.validate_core_card(
            _sample_card(units=["MTH-T02-C01-U01", "MTH-T02-C01-U02"]),
            valid_unit_codes={"MTH-T02-C01-U01", "MTH-T02-C01-U02"},
        )
        == []
    )
    assert (
        source_cores.validate_core_card(
            _sample_card(units=["MTH-T02-C01-U01", "UNMAPPED:MTH-FUTURE"]),
            valid_unit_codes={"MTH-T02-C01-U01"},
        )
        == []
    )
    assert any(
        "UNMAPPED:" in e
        for e in source_cores.validate_core_card(
            _sample_card(units=["MTH-T02-C01-U01", "UNMAPPED:"]),
            valid_unit_codes={"MTH-T02-C01-U01"},
        )
    )
    with pytest.warns(UserWarning, match="MTH-T99-BOGUS"):
        bad_units_errs = source_cores.validate_core_card(
            _sample_card(units=["MTH-T02-C01-U01", "MTH-T99-BOGUS"]),
            valid_unit_codes={"MTH-T02-C01-U01", "MTH-T02-C01-U02"},
        )
    assert any("units[1]: unknown unit/chapter code" in e for e in bad_units_errs), bad_units_errs

    # 200-char field limit enforced everywhere (top-level & nested)
    long_text = "x" * 201
    assert any("200-char" in e for e in source_cores.validate_core_card(_sample_card(notes=long_text)))
    nested_long = _sample_card(traps=[{"tag": "trap-a", "description": long_text}])
    assert any("traps[0].description" in e for e in source_cores.validate_core_card(nested_long))


def test_core_card_rejects_copied_numbers_and_wording(tmp_path: Path) -> None:
    source_text = "Question 12. Find the value of a such that (a + 17i) / (3 - 4i) has imaginary part 42."

    # Abstract card (no source digits; unit-code digits in trap tag 't02-c01-u01' are allowed)
    clean = _sample_card()
    assert source_cores.validate_core_card(clean, source_item_text=source_text) == []

    # Card leaking copied source numbers
    leaked_num = _sample_card(notes="Divide by 3 - 4i to hit target 42")
    errs_num = source_cores.validate_core_card(leaked_num, source_item_text=source_text)
    assert any("digit run" in e for e in errs_num), errs_num

    # Card leaking copied source wording (6-word shingle overlap)
    leaked_words = _sample_card(difficultyDriver="Find the value of a such that quotient is imaginary")
    errs_words = source_cores.validate_core_card(leaked_words, source_item_text=source_text)
    assert any("source wording overlap" in e for e in errs_words), errs_words

    # Save + load JSONL round-trip
    saved_path = source_cores.save_core_cards("MTH-T02-C01-U01", [clean], sources_dir=str(tmp_path))
    assert Path(saved_path).is_file()
    loaded = source_cores.load_core_cards("MTH-T02-C01-U01", sources_dir=str(tmp_path))
    assert loaded == [clean]

    with pytest.raises(source_cores.CoreCardError):
        source_cores.append_core_card(
            "MTH-T02-C01-U01",
            leaked_num,
            sources_dir=str(tmp_path),
            source_item_text=source_text,
        )


# ---------------------------------------------------------------------------
# 2. Originality gate (unit + CLI + ingest & variant_bank wiring)
# ---------------------------------------------------------------------------


def test_originality_gate_copy_paraphrase_similarity_and_original() -> None:
    source_pages = [
        {
            "relPath": "mathsgenie/Grade_8/Exam_Questions/complex.pdf",
            "page": 2,
            "text": (
                "1. Expand and simplify the complex product (3 + 4i)(5 - 2i) in standard form.\n"
                "2. Determine the real parameter k when the quadratic equation x^2 + 6x + k = 0 "
                "has non-real roots with modulus 5."
            ),
        }
    ]

    # 1. Verbatim copy (>= 8-word shingle overlap) -> reject
    copied = {
        "id": "Q01",
        "prompt": "Expand and simplify the complex product $(3 + 4i)(5 - 2i)$ in standard form.",
    }
    errs_copy = originality.check_problem_originality(copied, source_pages)
    assert any("shingle" in e for e in errs_copy), errs_copy

    # 2. Paraphrase reusing exact source number multiset {3, 4, 5, 2} -> reject
    same_nums = {
        "id": "Q02",
        "prompt": "Given $z_1 = 3 + 4i$ and $z_2 = 5 - 2i$, compute $z_1 z_2$.",
    }
    errs_nums = originality.check_problem_originality(same_nums, source_pages)
    assert any("number multiset" in e for e in errs_nums), errs_nums

    # 3. High normalised similarity (>= 0.6) even with changed numbers -> reject
    near_copy = {
        "id": "Q03",
        "prompt": "Expand and simplify the complex product $(7 + 8i)(9 - 6i)$ in standard form.",
    }
    errs_sim = originality.check_problem_originality(near_copy, source_pages)
    assert any("normalised similarity" in e for e in errs_sim), errs_sim

    # 4. Choice option copying source sentence -> reject
    copied_opt = {
        "id": "Q04",
        "prompt": "Select the statement that matches the identity.",
        "answerSpec": {
            "type": "choice",
            "options": [
                {"id": "A", "label": "Expand and simplify the complex product (3 + 4i)(5 - 2i) in standard form."}
            ],
        },
    }
    errs_opt = originality.check_problem_originality(copied_opt, source_pages)
    assert any("option 1" in e for e in errs_opt), errs_opt

    # 5. Fresh original problem (different wording, fresh numbers, low similarity) -> pass
    fresh = {
        "id": "Q05",
        "prompt": "Write the quotient $\\frac{11 - 7i}{2 + 3i}$ as $a + bi$.",
    }
    assert originality.check_problem_originality(fresh, source_pages) == []


def test_originality_cli_and_ingest_variant_wiring(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    unit = "MTH-T01-C04"
    sources_dir = tmp_path / "sources"
    source_text = "1. Reduce the fraction 14/35 to its lowest terms by dividing by the greatest common factor."
    _write_located_cache(sources_dir, unit, "mathsgenie/Grade_4/fractions.pdf", source_text)

    # Load a real passing template draft and inject a copied prompt for testing CLI gates
    tpl_path = ROOT / ".claude" / "skills" / "new-math-drill" / "template" / "draft.json"
    draft = json.loads(tpl_path.read_text(encoding="utf-8"))
    draft_unit = draft["unitCode"]
    draft_copy = copy.deepcopy(draft)
    _write_located_cache(
        sources_dir,
        draft_unit,
        "mathsgenie/Grade_5/sample.pdf",
        f"1. {draft_copy['problems'][0]['prompt']}",
    )
    draft_file = tmp_path / "draft.json"
    draft_file.write_text(json.dumps(draft_copy), encoding="utf-8")

    # Standalone originality CLI rejects copied draft
    rc_fail = originality.main([str(draft_file), "--unit", draft_unit, "--sources-dir", str(sources_dir)])
    assert rc_fail == 1
    out = capsys.readouterr().out
    assert "FAIL" in out

    # Standalone originality CLI skips cleanly with notice when sources dir is absent
    missing_dir = tmp_path / "no-such-sources"
    rc_skip = originality.main([str(draft_file), "--unit", draft_unit, "--sources-dir", str(missing_dir)])
    assert rc_skip == 0
    assert "skipped" in capsys.readouterr().out.lower()

    # Direct Python API check_ai_drill(..., check_originality=True)
    api_ingest_errs = ai_drill_ingest.check_ai_drill(
        draft_copy,
        vault_dir=str(tpl_path.parent),
        check_originality=True,
        sources_dir=str(sources_dir),
    )
    assert any("Originality gate failed" in e for e in api_ingest_errs), api_ingest_errs

    # ai_drill_ingest --check: default ON when sources dir exists -> rejects copied prompt
    monkeypatch.setenv("REASONING_VAULT_DIR", str(tpl_path.parent))
    monkeypatch.setenv("LEARNINGOS_SOURCES_DIR", str(sources_dir))
    rc_ingest_fail = ai_drill_ingest.main(["--unit", draft_unit, "--ingest-file", str(draft_file), "--check"])
    assert rc_ingest_fail == 1
    assert "Originality gate failed" in capsys.readouterr().out

    # ai_drill_ingest --check --no-originality skips originality check
    rc_ingest_no_orig = ai_drill_ingest.main(
        ["--unit", draft_unit, "--ingest-file", str(draft_file), "--check", "--no-originality"]
    )
    assert rc_ingest_no_orig == 0
    capsys.readouterr()

    # ai_drill_ingest --check skips with a notice when sources dir does not exist (CI behaviour)
    monkeypatch.setenv("LEARNINGOS_SOURCES_DIR", str(missing_dir))
    rc_ingest_ci = ai_drill_ingest.main(["--unit", draft_unit, "--ingest-file", str(draft_file), "--check"])
    assert rc_ingest_ci == 0
    assert "Originality gate skipped" in capsys.readouterr().out

    # variant_bank --check: default ON when sources dir exists -> rejects variant copying source prompt
    monkeypatch.delenv("REASONING_VAULT_DIR", raising=False)
    seed_bank = json.loads((ROOT / "drills" / "variants" / "MTH-T01-C04.json").read_text(encoding="utf-8"))
    first_var = copy.deepcopy(seed_bank["variants"][0])
    _write_located_cache(
        sources_dir,
        "MTH-T01-C04",
        "mathsgenie/Grade_4/fractions.pdf",
        f"1. {first_var['prompt']}",
    )
    var_file = tmp_path / "variants.json"
    var_file.write_text(json.dumps({"unitCode": "MTH-T01-C04", "variants": [first_var]}), encoding="utf-8")

    # Direct Python API check_variant_bank(..., check_originality=True)
    api_vb_errs = variant_bank.check_variant_bank(
        {"unitCode": "MTH-T01-C04", "variants": [first_var]},
        check_originality=True,
        sources_dir=str(sources_dir),
    )
    assert any("Originality gate failed" in e for e in api_vb_errs), api_vb_errs

    monkeypatch.setenv("LEARNINGOS_SOURCES_DIR", str(sources_dir))
    rc_vb_fail = variant_bank.main(["--check", str(var_file), "--originality"])
    assert rc_vb_fail == 1
    assert "Originality gate failed" in capsys.readouterr().out

    monkeypatch.setenv("LEARNINGOS_SOURCES_DIR", str(missing_dir))
    rc_vb_ci = variant_bank.main(["--check", str(var_file)])
    assert rc_vb_ci == 0
    assert "Originality gate skipped" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# 3. scripts.source_find (terms, scope-only OpenStax, scans, zip, cache, pypdf)
# ---------------------------------------------------------------------------


def test_source_find_matching_scope_scans_zip_and_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sources_dir = tmp_path / "sources"
    mg_pdf = sources_dir / "mathsgenie" / "Grade_8" / "Exam_Questions" / "complex.pdf"
    thai_pdf = sources_dir / "thai-exams" / "tcas68-a-level" / "math1.pdf"
    scan_pdf = sources_dir / "thai-exams" / "onet-2568" / "m6-scan.pdf"
    os_pdf = sources_dir / "openstax" / "math" / "algebra-trig" / "book.pdf"
    zip_path = sources_dir / "illustrative-math" / "grade6-unit1" / "bundle.zip"

    for p in (mg_pdf, thai_pdf, scan_pdf, os_pdf):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"%PDF-1.4 dummy")

    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("lesson1.pdf", b"%PDF-1.4 zip-dummy")

    extract_calls: list[str] = []

    def fake_extract(source: str | bytes) -> list[dict]:
        if isinstance(source, bytes):
            extract_calls.append("zip::lesson1.pdf")
            return [{"page": 1, "text": "Intro to a + bi and conjugate symmetry", "isImagePage": False}]
        name = Path(source).name
        extract_calls.append(name)
        if name == "complex.pdf":
            return [
                {"page": 1, "text": "Simplify complex conjugate expressions in a + bi form.", "isImagePage": False},
                {"page": 2, "text": "", "isImagePage": True},
            ]
        if name == "math1.pdf":
            return [{"page": 1, "text": "ข้อ 1 จำนวนเชิงซ้อน และ สังยุค ของจำนวนจินตภาพ", "isImagePage": False}]
        if name == "m6-scan.pdf":
            return [
                {"page": 1, "text": "", "isImagePage": True},
                {"page": 2, "text": "   ", "isImagePage": True},
            ]
        if name == "book.pdf":
            return [
                {
                    "page": 1,
                    "text": "Table of Contents - Learning Objectives: Complex Numbers and imaginary unit",
                    "isImagePage": False,
                }
            ]
        return []

    monkeypatch.setattr(source_find, "extract_pdf_pages", fake_extract)

    # Verify seeded terms exist for MTH-T02-C01-U01
    seeded = source_cores.get_unit_terms("MTH-T02-C01-U01")
    assert "complex" in seeded and "จำนวนเชิงซ้อน" in seeded and "สังยุค" in seeded

    res = source_find.find_sources("MTH-T02-C01-U01", sources_dir=str(sources_dir))
    assert res["pdfsScanned"] == 5
    core_paths = {m["relPath"] for m in res["coreMatches"]}
    scope_paths = {m["relPath"] for m in res["scopeMatches"]}
    scan_paths = {m["relPath"] for m in res["imageOnlyFiles"]}

    assert "mathsgenie/Grade_8/Exam_Questions/complex.pdf" in core_paths
    assert "thai-exams/tcas68-a-level/math1.pdf" in core_paths
    assert "illustrative-math/grade6-unit1/bundle.zip::lesson1.pdf" in core_paths
    # OpenStax MUST be scope-only, never in mining targets
    assert "openstax/math/algebra-trig/book.pdf" in scope_paths
    assert not any(p.startswith("openstax/") for p in core_paths)
    # All-scan PDF reported in imageOnlyFiles
    assert "thai-exams/onet-2568/m6-scan.pdf" in scan_paths

    # Report formatting checks
    report = source_find.format_find_report(res)
    assert "[scope:openstax]" in report
    assert "image page — read visually" in report

    # Located manifest and PDF text cache written under sources/_index/
    assert Path(res["manifestPath"]).is_file()
    assert len(list((sources_dir / "_index").glob("pdf_*.json"))) == 5

    # Second run hits cache (zero new extract calls)
    extract_calls.clear()
    res2 = source_find.find_sources("MTH-T02-C01-U01", sources_dir=str(sources_dir))
    assert extract_calls == []
    assert len(res2["coreMatches"]) == len(res["coreMatches"])

    # Family filter narrows search
    res_thai = source_find.find_sources(
        "MTH-T02-C01-U01",
        families=["thai-exams/tcas68-a-level"],
        sources_dir=str(sources_dir),
    )
    assert [m["relPath"] for m in res_thai["coreMatches"]] == ["thai-exams/tcas68-a-level/math1.pdf"]
    assert res_thai["scopeMatches"] == []


def test_source_find_missing_pypdf_error(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def fake_import(name: str, *args, **kwargs):
        if name == "pypdf":
            raise ImportError("No module named 'pypdf'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(RuntimeError, match="requirements-dev.txt"):
        source_find.extract_pdf_pages(b"%PDF-1.4")


@pytest.mark.skipif(importlib.util.find_spec("pypdf") is None, reason="pypdf not installed in this venv")
def test_source_find_real_pypdf_extraction(tmp_path: Path) -> None:
    sources_dir = tmp_path / "sources"
    pdf_path = sources_dir / "mathsgenie" / "Grade_8" / "complex_real.pdf"
    pdf_path.parent.mkdir(parents=True)
    pdf_path.write_bytes(_minimal_pdf_bytes("Complex conjugate and imaginary numbers"))

    res = source_find.find_sources("MTH-T02-C01-U01", sources_dir=str(sources_dir))
    assert len(res["coreMatches"]) == 1
    assert res["coreMatches"][0]["pages"][0]["hits"] >= 3


# ---------------------------------------------------------------------------
# 4. scripts.source_gap (read-only gap report)
# ---------------------------------------------------------------------------


def test_source_gap_report_and_read_only(tmp_path: Path) -> None:
    unit = "MTH-T02-C01-U01"
    vault_dir = tmp_path / "vault"
    vault_dir.mkdir()
    vault_file = vault_dir / f"{unit}.json"
    vault_payload = {
        "unitCode": unit,
        "archetypes": [
            {
                "archetypeKey": "t02-c01-u01-dividing-complex-numbers",
                "level": 2,
                "name": "Dividing Complex Numbers via Conjugate Rationalization",
                "coreConcept": "Multiply numerator and denominator by denominator conjugate.",
                "mentalModel": "Normalize complex ratio to real denominator.",
                "cognitiveTraps": ["t02-c01-u01-denominator-conjugate-sign-error-trap"],
                "figureNone": "Symbolic algebra.",
            }
        ],
    }
    vault_bytes = json.dumps(vault_payload, indent=2).encode("utf-8")
    vault_file.write_bytes(vault_bytes)

    cards = [
        # 1. Matches existing archetype by trap tag, adds a new trap, L3 reverse, 5-option choice
        _sample_card(
            id="CORE-01",
            level=3,
            reasoningMove="reverse",
            traps=[
                {
                    "tag": "t02-c01-u01-denominator-conjugate-sign-error-trap",
                    "description": "Wrong denominator sign",
                },
                {
                    "tag": "t02-c01-u01-swap-real-imag-target-trap",
                    "description": "Equates real part to target imaginary part",
                },
            ],
        ),
        # 2. Unmatched card (candidate new archetype), L5 generalise
        _sample_card(
            id="CORE-02",
            skill="Cyclic sum cancellation for consecutive high powers of imaginary unit",
            reasoningMove="generalise",
            difficultyDriver="Group four consecutive powers summing to zero across arbitrary length",
            level=5,
            traps=[{"tag": "t02-c01-u01-off-by-one-cycle-count-trap", "description": "Miscounts terms in sum"}],
            format={"kind": "numeric"},
        ),
        # 3. Deeper-than-unit card deferred via laterUnit
        _sample_card(
            id="CORE-03",
            laterUnit="MTH-T02-C01-U03",
            skill="De Moivre power expansion in polar coordinates",
            reasoningMove="translate",
            level=4,
            traps=[{"tag": "t02-c01-u03-argument-wrap-trap", "description": "Fails to reduce angle mod 2pi"}],
            format={"kind": "expression"},
        ),
    ]
    source_cores.save_core_cards(unit, cards, sources_dir=str(tmp_path))

    report = source_gap.build_gap_report(unit, sources_dir=str(tmp_path), vault_dir=str(vault_dir))
    assert report["currentCardsCount"] == 2
    assert report["laterCardsCount"] == 1
    assert [m["id"] for m in report["matchedCards"]] == ["CORE-01"]
    assert [u["id"] for u in report["unmatchedCards"]] == ["CORE-02"]

    new_trap_tags = {t["tag"] for t in report["newTraps"]}
    assert "t02-c01-u01-swap-real-imag-target-trap" in new_trap_tags
    assert "t02-c01-u01-off-by-one-cycle-count-trap" in new_trap_tags
    assert "t02-c01-u01-denominator-conjugate-sign-error-trap" not in new_trap_tags
    # laterUnit traps must not pollute current-unit newTraps
    assert "t02-c01-u03-argument-wrap-trap" not in new_trap_tags

    assert report["levels"]["cardLevelsMissingInVault"] == [3, 5]
    assert set(report["reasoningMoves"]["cardMovesMissingInVault"]) == {"generalise", "reverse"}
    assert any(f["kind"] == "choice" and f["optionCount"] == 5 for f in report["examFormats"])
    assert "MTH-T02-C01-U03" in report["laterUnitCards"]
    assert [c["id"] for c in report["laterUnitCards"]["MTH-T02-C01-U03"]] == ["CORE-03"]

    text = source_gap.format_gap_report(report)
    assert "5 options" in text
    assert "MTH-T02-C01-U03" in text
    assert "t02-c01-u01-swap-real-imag-target-trap" in text

    # Strictly read-only: vault file unchanged
    assert vault_file.read_bytes() == vault_bytes


def test_cli_help_smoke() -> None:
    for mod in (
        "scripts.source_find",
        "scripts.source_gap",
        "scripts.source_cores_retag",
        "scripts.extract_cards_job",
        "math_engine.source_cores.originality",
    ):
        proc = subprocess.run(
            [sys.executable, "-m", mod, "--help"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, f"{mod} --help failed: {proc.stderr}"


def test_carried_forward_cards_and_source_gap(tmp_path: Path) -> None:
    u1 = "MTH-T02-C01-U01"
    u2 = "MTH-T02-C01-U02"
    u3 = "MTH-T02-C01-U03"
    valid_codes = {u1, u2, u3}

    # Unit 1 file stores cards targeting U2 via laterUnit and via multi-unit `units`, plus one for U3.
    u1_cards = [
        _sample_card(id="CORE-LOCAL-U1", unitCode=u1, skill="Direct complex addition"),
        _sample_card(
            id="CORE-CF-LATER",
            unitCode=u1,
            laterUnit=u2,
            skill="Recover quadratic coefficients from conjugate pair roots",
            traps=[{"tag": "quad-vieta-sign-trap", "description": "Sign error in sum of roots"}],
        ),
        _sample_card(
            id="CORE-CF-UNITS",
            unitCode=u1,
            units=[u1, u2],
            skill="Combine complex modulus with quadratic discriminant",
            traps=[{"tag": "quad-discriminant-trap", "description": "Misreads negative discriminant"}],
        ),
        _sample_card(id="CORE-OTHER-U3", unitCode=u1, laterUnit=u3, skill="Radical equation extraneous root"),
    ]
    source_cores.save_core_cards(u1, u1_cards, sources_dir=str(tmp_path), valid_unit_codes=valid_codes)

    # Unit 2 has NO local JSONL file yet — load_core_cards(u2) must return both carried-forward cards.
    loaded_u2 = source_cores.load_core_cards(u2, sources_dir=str(tmp_path), valid_unit_codes=valid_codes)
    assert [c["id"] for c in loaded_u2] == ["CORE-CF-LATER", "CORE-CF-UNITS"]
    assert all(c["carriedFrom"] == u1 for c in loaded_u2)

    # Deduplication by id: if U2 also stores CORE-CF-LATER locally, it appears once without carriedFrom.
    local_dup = _sample_card(id="CORE-CF-LATER", unitCode=u2, skill="Local quadratic conjugate root card")
    source_cores.save_core_cards(u2, [local_dup], sources_dir=str(tmp_path), valid_unit_codes=valid_codes)
    loaded_dedup = source_cores.load_core_cards(u2, sources_dir=str(tmp_path), valid_unit_codes=valid_codes)
    assert [c["id"] for c in loaded_dedup] == ["CORE-CF-LATER", "CORE-CF-UNITS"]
    assert "carriedFrom" not in loaded_dedup[0]
    assert loaded_dedup[1]["carriedFrom"] == u1

    # Remove U2's local file again and verify source_gap still shows carried-forward cards as current cards.
    Path(source_cores.cores_path(u2, sources_dir=str(tmp_path))).unlink()
    vault_dir = tmp_path / "vault"
    vault_dir.mkdir()
    (vault_dir / f"{u2}.json").write_text(
        json.dumps(
            {
                "unitCode": u2,
                "archetypes": [
                    {
                        "archetypeKey": "u2-quadratic-formula",
                        "level": 2,
                        "name": "Quadratic Formula and Complex Roots",
                        "coreConcept": "Solve quadratic equations with discriminant and conjugate roots.",
                        "mentalModel": "Discriminant classifies real vs complex conjugate roots.",
                        "cognitiveTraps": ["quad-discriminant-trap"],
                        "figureNone": "Symbolic algebra.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    report = source_gap.build_gap_report(
        u2,
        sources_dir=str(tmp_path),
        vault_dir=str(vault_dir),
        eligible_units=set(),
        valid_unit_codes=valid_codes,
    )
    assert report["cardsFileExists"] is False
    assert report["currentCardsCount"] == 2
    assert report["carriedCardsCount"] == 2
    assert report["laterCardsCount"] == 0
    assert {c["id"] for c in report["matchedCards"] + report["unmatchedCards"]} == {"CORE-CF-LATER", "CORE-CF-UNITS"}
    assert all(c["carriedFrom"] == u1 for c in report["matchedCards"] + report["unmatchedCards"])
    assert any(t["tag"] == "quad-vieta-sign-trap" for t in report["newTraps"])

    text = source_gap.format_gap_report(report)
    assert "No core cards file found yet" not in text
    assert "2 carried-forward" in text
    assert f"[carried from {u1}]" in text
    assert "CORE-CF-LATER" in text and "CORE-CF-UNITS" in text


def test_later_unit_validation_and_retag_on_fixtures(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    fixture_id_map = {
        "MTH-T02-C01-U01": {"title": "Complex Numbers"},
        "MTH-T02-C01-U02": {"title": "Quadratic Equations"},
        "MTH-T02-C04-U05": {"title": "Zeros of Polynomial Functions"},
        "MTH-T02-C09-U05": {"title": "Polar Form of Complex Numbers"},
        "MTH-T02-C09-U08": {"title": "Vectors"},
        "MTH-T02": {"title": "Topic Should Be Ignored"},
    }
    id_map_file = tmp_path / "id_map.json"
    id_map_file.write_text(json.dumps(fixture_id_map), encoding="utf-8")

    valid_codes = source_cores.load_valid_unit_codes(id_map_path=str(id_map_file))
    assert "MTH-T02-C09-U05" in valid_codes
    assert "MTH-T02" not in valid_codes

    # Valid code passes; UNMAPPED: passes; empty UNMAPPED: rejected; unknown code warns AND rejects.
    assert (
        source_cores.validate_core_card(_sample_card(laterUnit="MTH-T02-C01-U02"), valid_unit_codes=valid_codes) == []
    )
    assert (
        source_cores.validate_core_card(
            _sample_card(laterUnit="UNMAPPED:MTH-T04-LEGACY"),
            valid_unit_codes=valid_codes,
        )
        == []
    )
    assert any(
        "UNMAPPED:" in e
        for e in source_cores.validate_core_card(_sample_card(laterUnit="UNMAPPED:"), valid_unit_codes=valid_codes)
    )

    with pytest.warns(UserWarning, match="MTH-T04-COMPLEX-ADV"):
        bad_errs = source_cores.validate_core_card(
            _sample_card(laterUnit="MTH-T04-COMPLEX-ADV"),
            valid_unit_codes=valid_codes,
        )
    assert any("unknown unit/chapter code" in e for e in bad_errs), bad_errs

    # Build a fixture JSONL with valid, None, and invalid laterUnit cards.
    jsonl_path = tmp_path / "fixture_cards.jsonl"
    fixture_cards = [
        _sample_card(id="FX-CURR", skill="Add two complex numbers in standard form"),
        _sample_card(id="FX-QUAD-KEEP", laterUnit="MTH-T02-C01-U02", skill="Quadratic with complex roots"),
        _sample_card(
            id="FX-POLAR",
            laterUnit="MTH-T04-COMPLEX-ADV",
            skill="Compute cube roots in trigonometric form using De Moivre theorem",
            notes="Polar angle and modulus on the unit circle",
        ),
        _sample_card(
            id="FX-PLANE",
            laterUnit="MTH-T04-COMPLEX-ADV",
            skill="Identify the plane region inside an open disc and half-plane",
            notes="Distance to centre below radius",
        ),
        _sample_card(
            id="FX-POLY",
            laterUnit="MTH-T04-COMPLEX-ADV",
            skill="Find a real cubic polynomial coefficients from a complex linear factor",
            notes="Conjugate root gives a real quadratic factor",
        ),
        _sample_card(
            id="FX-OVERRIDE",
            reasoningMove="case-check",
            level=2,
            laterUnit="MTH-T99-BOGUS",
            skill="Abstract task overridden explicitly",
            notes="Uses explicit override map",
        ),
        _sample_card(
            id="FX-UNMAPPED",
            laterUnit="MTH-T99-UNKNOWN",
            skill="Elliptic modular form homology",
            notes="Outside curriculum scope",
        ),
    ]
    jsonl_path.write_text("\n".join(json.dumps(c) for c in fixture_cards) + "\n", encoding="utf-8")
    orig_bytes = jsonl_path.read_bytes()

    overrides_file = tmp_path / "overrides.json"
    overrides_file.write_text(json.dumps({"FX-OVERRIDE": "MTH-T02-C09-U08"}), encoding="utf-8")

    # Dry-run prints summary without modifying file
    rc_dry = source_cores_retag.main(
        [str(jsonl_path), "--id-map", str(id_map_file), "--overrides", str(overrides_file)]
    )
    assert rc_dry == 0
    dry_out = capsys.readouterr().out
    assert "DRY-RUN" in dry_out
    assert "MTH-T02-C09-U05: 2" in dry_out
    assert "MTH-T02-C04-U05: 1" in dry_out
    assert "MTH-T02-C09-U08: 1" in dry_out
    assert "UNMAPPED:MTH-T99-UNKNOWN: 1" in dry_out
    assert jsonl_path.read_bytes() == orig_bytes

    # Apply rewrites file atomically without changing the legacy move or level.
    rc_apply = source_cores_retag.main(
        [str(jsonl_path), "--apply", "--id-map", str(id_map_file), "--overrides", str(overrides_file)]
    )
    assert rc_apply == 0
    apply_out = capsys.readouterr().out
    assert "APPLIED" in apply_out

    rewritten = [json.loads(line) for line in jsonl_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    by_id = {c["id"]: c for c in rewritten}
    assert by_id["FX-CURR"].get("laterUnit") is None
    assert by_id["FX-QUAD-KEEP"]["laterUnit"] == "MTH-T02-C01-U02"
    assert by_id["FX-POLAR"]["laterUnit"] == "MTH-T02-C09-U05"
    assert by_id["FX-PLANE"]["laterUnit"] == "MTH-T02-C09-U05"
    assert by_id["FX-POLY"]["laterUnit"] == "MTH-T02-C04-U05"
    assert by_id["FX-OVERRIDE"]["laterUnit"] == "MTH-T02-C09-U08"
    assert by_id["FX-UNMAPPED"]["laterUnit"] == "UNMAPPED:MTH-T99-UNKNOWN"
    assert by_id["FX-OVERRIDE"]["reasoningMove"] == "case-check"
    assert by_id["FX-OVERRIDE"]["level"] == 2
    for card in rewritten:
        assert source_cores.validate_core_card(card, valid_unit_codes=valid_codes, enforce_move_contract=False) == []


def test_source_find_warns_on_unregistered_folders(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sources_dir = tmp_path / "sources"
    (sources_dir / "mathsgenie").mkdir(parents=True)
    (sources_dir / "new-publisher").mkdir(parents=True)
    (sources_dir / "AnotherSource").mkdir(parents=True)
    (sources_dir / "_index").mkdir(parents=True)
    (sources_dir / "_scratch").mkdir(parents=True)
    (sources_dir / ".hidden").mkdir(parents=True)
    (sources_dir / "README.txt").write_text("top-level file ignored", encoding="utf-8")

    registry = tmp_path / "sources.md"
    registry.write_text(
        "# Source Registry\n\n"
        "| Family (under `sources/`) | What it is | Licence | Allowed use |\n"
        "| :--- | :--- | :--- | :--- |\n"
        "| `mathsgenie/Grade_N/` | MathsGenie | Free | `cores` |\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(source_find, "extract_pdf_pages", lambda source: [])
    res = source_find.find_sources(
        "MTH-T02-C01-U01",
        sources_dir=str(sources_dir),
        registry_path=str(registry),
    )
    assert res["unregisteredSources"] == ["AnotherSource", "new-publisher"]

    report = source_find.format_find_report(res)
    assert "WARNING: Unregistered top-level folder(s)" in report
    assert "AnotherSource" in report
    assert "new-publisher" in report
    assert "_index" not in report and "_scratch" not in report
    assert "family, licence, allowed use" in report


def test_originality_short_prompts_and_unrelated_families(tmp_path):
    """Short prompts with one or two numbers are only rejected on a verbatim copy; CS/physics books are ignored for MTH."""
    from math_engine.source_cores import originality as og

    assert og.MIN_MULTISET_NUMBERS >= 3
    assert not og._family_relevant("openstax/cs-physics/Computer_Science/x.pdf", "MTH-T02-C01-U01")
    assert og._family_relevant("SmartMathPro/a.pdf", "MTH-T02-C01-U01")
    pages = [
        {"loc": "src p.1", "text": "Simplify the expression i to the power eleven quickly. Another sentence here."}
    ]
    short_original = {"id": "Q1", "prompt": "Simplify $\\frac{1}{i^{11}}$."}
    assert og.check_problem_originality(short_original, pages) == []
    verbatim = {"id": "Q2", "prompt": "Simplify the expression i to the power eleven quickly."}
    assert og.check_problem_originality(verbatim, pages)


# ---------------------------------------------------------------------------
# 6. PRG source indexing, cards, originality, and gap analysis
# ---------------------------------------------------------------------------


def test_prg_source_find_indexes_code_and_markdown(tmp_path: Path) -> None:
    sources_dir = tmp_path / "sources"
    ts_file = sources_dir / "prg" / "exercism-typescript" / "concepts" / "narrowing.ts"
    md_file = sources_dir / "prg" / "javascript-questions" / "async.md"
    json_file = sources_dir / "prg" / "exercism-typescript" / "tests" / "narrowing.json"
    ts_file.parent.mkdir(parents=True)
    md_file.parent.mkdir(parents=True)
    json_file.parent.mkdir(parents=True)
    ts_file.write_text(
        "export function normalizeRecord(record: unknown) {\n"
        "  if (record === null || typeof record !== 'object') return null;\n"
        "  return record;\n"
        "}\n",
        encoding="utf-8",
    )
    md_file.write_text(
        "# Async ordering\n\n"
        "A closure can preserve a value while a promise callback runs later.\n\n"
        "```js\nconst result = Promise.resolve('ready').then(value => value);\n```\n",
        encoding="utf-8",
    )
    json_file.write_text(
        json.dumps({"tests": [{"name": "handles unknown records", "testCode": "expect(isRecord(value)).toBe(true);"}]}),
        encoding="utf-8",
    )

    result = source_find.find_sources(
        "PRG-T00-C03-U01",
        terms=["unknown", "closure", "promise"],
        sources_dir=str(sources_dir),
    )

    assert result["track"] == "prg"
    assert result["filesScanned"] == 3
    assert result["pdfsScanned"] == 0
    assert {item["relPath"] for item in result["coreMatches"]} == {
        "prg/exercism-typescript/concepts/narrowing.ts",
        "prg/javascript-questions/async.md",
        "prg/exercism-typescript/tests/narrowing.json",
    }
    cache_files = list((sources_dir / "_index").glob("code_*.json"))
    assert len(cache_files) == 3
    cache_payloads = [json.loads(path.read_text(encoding="utf-8")) for path in cache_files]
    assert all(payload["pages"][0]["text"] for payload in cache_payloads)
    json_page = next(page for page in result["coreMatches"] if page["relPath"].endswith(".json"))
    json_cache = next(path for path in cache_files if path.name == json_page["cacheFile"])
    cached_text = json.loads(json_cache.read_text(encoding="utf-8"))["pages"][0]["text"]
    assert code_originality.extract_code_blocks_from_source(json_page["relPath"], cached_text) == [
        "expect(isRecord(value)).toBe(true);"
    ]


def test_prg_source_find_never_indexes_no_automation_families(tmp_path: Path) -> None:
    sources_dir = tmp_path / "sources"
    restricted = sources_dir / "prg" / "manual-only" / "lesson.ts"
    restricted.parent.mkdir(parents=True)
    restricted.write_text("export function readClosureState() { return undefined; }", encoding="utf-8")
    registry = tmp_path / "sources.md"
    registry.write_text(
        "# Registry\n\n"
        "## PRG Source Families (under sources/prg/)\n\n"
        "| Family | Upstream | Licence | Allowed use | Coverage |\n"
        "| :--- | :--- | :--- | :--- | :--- |\n"
        "| `manual-only/` | local fixture | ARR | `NO-AUTOMATION` | closure |\n",
        encoding="utf-8",
    )

    result = source_find.find_sources(
        "PRG-T00-C03-U01",
        terms=["closure"],
        sources_dir=str(sources_dir),
        registry_path=str(registry),
    )

    assert result["filesScanned"] == 0
    assert result["coreMatches"] == []
    assert result["skippedNoAutomation"] == ["prg/manual-only"]
    assert list((sources_dir / "_index").glob("code_*.json")) == []


def test_prg_core_card_rejects_copied_identifiers_and_strings() -> None:
    source_text = (
        "export function normalizeRecord(record: unknown) {\n"
        "  if (record === null || typeof record !== 'object') return null;\n"
        "  throw new TypeError('Expected record payload');\n"
        "}\n"
    )
    clean = _sample_prg_card()
    assert source_cores.validate_core_card(clean, source_item_text=source_text) == []

    copied_identifier = _sample_prg_card(skill="normalizeRecord validates a guarded value")
    ident_errors = source_cores.validate_core_card(copied_identifier, source_item_text=source_text)
    assert any("copies source identifier 'normalizeRecord'" in error for error in ident_errors), ident_errors

    copied_string = _sample_prg_card(notes="Expected record payload")
    string_errors = source_cores.validate_core_card(copied_string, source_item_text=source_text)
    assert any("copies source test name or string literal" in error for error in string_errors), string_errors


def test_prg_code_originality_rejects_copies_and_allows_original() -> None:
    source_code = """export async function loadAccountProfile(accountId: string) {
  const response = await fetch(`/accounts/${accountId}/profile`);
  if (!response.ok) {
    throw new Error("Profile request failed");
  }
  const payload = await response.json();
  return {
    id: payload.id,
    displayName: payload.displayName,
    roles: Array.isArray(payload.roles) ? payload.roles : [],
  };
}
"""
    pages = [{"relPath": "prg/exercism-typescript/profile.ts", "page": 1, "text": source_code}]

    copied_doc = {
        "unitCode": "PRG-T00-C03-U01",
        "problems": [{"id": "Q01", "prompt": "Implement profile loading.", "solutionCode": source_code}],
    }
    copied_errors, copied_notice = code_originality.check_code_drill_originality(copied_doc, source_pages=pages)
    assert copied_notice is None
    assert any("solutionCode" in error and "Code originality gate failed" in error for error in copied_errors)

    renamed_code = (
        source_code.replace("loadAccountProfile", "readMemberSummary")
        .replace("accountId", "memberKey")
        .replace("payload", "record")
    )
    renamed_doc = {
        "unitCode": "PRG-T00-C03-U01",
        "problems": [{"id": "Q01", "prompt": "Implement profile loading.", "solutionCode": renamed_code}],
    }
    renamed_errors, _ = code_originality.check_code_drill_originality(renamed_doc, source_pages=pages)
    assert any("solutionCode" in error and "Code originality gate failed" in error for error in renamed_errors)

    original_doc = {
        "unitCode": "PRG-T00-C03-U01",
        "problems": [
            {
                "id": "Q01",
                "prompt": "Build a local summary from validated membership records.",
                "solutionCode": """function summarizeMembership(members) {
  const activeMembers = members.filter(member => member.status === "active");
  const totalsByRegion = new Map();
  for (const member of activeMembers) {
    const current = totalsByRegion.get(member.region) || 0;
    totalsByRegion.set(member.region, current + member.credit);
  }
  return [...totalsByRegion.entries()].map(([region, credits]) => ({ region, credits }));
}
""",
            }
        ],
    }
    original_errors, _ = code_originality.check_code_drill_originality(original_doc, source_pages=pages)
    assert original_errors == []


def test_prg_source_gap_reports_vault_gaps_read_only(tmp_path: Path) -> None:
    unit = "PRG-T00-C03-U01"
    vault_dir = tmp_path / "code-vault"
    vault_dir.mkdir()
    vault_file = vault_dir / "PRG-T00-C03.json"
    vault_payload = {
        "unitCode": "PRG-T00-C03",
        "archetypes": [
            {
                "archetypeKey": "type-guard-stability",
                "unitCode": unit,
                "archetypeKind": "find-the-bug",
                "level": 2,
                "name": "Type guard stability",
                "coreConcept": "Preserve narrowing across function boundaries",
                "mentalModel": "A mutable alias can invalidate an earlier observation",
                "cognitiveTraps": [
                    {"trapTag": "mutation-breaks-narrowing", "description": "Trusts stale narrowed state"}
                ],
                "qualityChecks": [
                    {"id": "QC-stable-boundary", "check": "Guarded values stay stable", "severity": "should"}
                ],
            }
        ],
    }
    vault_bytes = json.dumps(vault_payload, indent=2).encode("utf-8")
    vault_file.write_bytes(vault_bytes)

    card = _sample_prg_card(
        traps=[
            {"tag": "mutation-breaks-narrowing", "description": "Trusts stale narrowed state"},
            {"tag": "callback-mutates-discriminant", "description": "Ignores mutation by a callback"},
        ],
        qualityCheckIdeas=[
            {"id": "QC-stable-boundary", "check": "Narrowed values remain stable across helper calls"},
            {
                "id": "QC-copy-before-callback",
                "check": "Snapshot mutable state before deferred work",
                "severity": "must",
            },
        ],
    )
    source_cores.save_core_cards(unit, [card], sources_dir=str(tmp_path))

    report = source_gap.build_gap_report(unit, sources_dir=str(tmp_path), vault_dir=str(vault_dir))
    assert report["track"] == "prg"
    assert report["matchedCards"][0]["id"] == card["id"]
    assert {trap["tag"] for trap in report["newTraps"]} == {"callback-mutates-discriminant"}
    assert [qc["id"] for qc in report["newQualityChecks"]] == ["QC-copy-before-callback"]
    assert "find-the-bug" in report["archetypeKinds"]["vaultKinds"]
    assert report["levels"]["cardLevelsMissingInVault"] == [3]
    assert "implement" in report["archetypeKinds"]["allVaultMissingKinds"]
    assert vault_file.read_bytes() == vault_bytes


def test_source_gap_structured_matching_distinct_ambiguous_unmatched(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    unit = "MTH-T02-C01-U01"
    vault_dir = tmp_path / "vault"
    vault_dir.mkdir()
    vault_payload = {
        "unitCode": unit,
        "archetypes": [
            {
                "archetypeKey": "t02-c01-u01-powers-of-i-cycle",
                "unitCode": unit,
                "level": 2,
                "name": "Powers of i Beyond the First Cycle",
                "coreConcept": "Reduce large powers of the imaginary unit i modulo four in standard form.",
                "governingRelation": "i^{4k+r} = i^r",
                "cognitiveTraps": [
                    {
                        "trapTag": "t02-c01-u01-power-of-i-remainder-trap",
                        "description": "Maps exponent remainder mod 4 to wrong value of i.",
                    }
                ],
                "figureNone": "Symbolic.",
            },
            {
                "archetypeKey": "t02-c01-u01-dividing-complex-numbers",
                "unitCode": unit,
                "level": 3,
                "name": "Dividing Complex Numbers via Denominator Conjugate",
                "coreConcept": "Divide complex numbers in standard form by multiplying by denominator conjugate.",
                "governingRelation": "(a+bi)/(c+di) = (a+bi)(c-di)/(c^2+d^2)",
                "cognitiveTraps": [
                    {
                        "trapTag": "t02-c01-u01-denominator-conjugate-sign-error-trap",
                        "description": "Subtracts d^2 instead of adding in rationalized denominator.",
                    }
                ],
                "figureNone": "Symbolic.",
            },
            {
                "archetypeKey": "t02-c01-u01-multiplying-complex-binomials",
                "unitCode": unit,
                "level": 3,
                "name": "Multiplying Complex Numbers via FOIL Expansion",
                "coreConcept": "Multiply complex binomials in standard form and simplify i^2 = -1.",
                "governingRelation": "(a+bi)(c+di) = (ac-bd)+(ad+bc)i",
                "cognitiveTraps": [
                    {
                        "trapTag": "t02-c01-u01-cross-term-omission-trap",
                        "description": "Omits cross terms when squaring a complex binomial.",
                    }
                ],
                "figureNone": "Symbolic.",
            },
            {
                "archetypeKey": "t02-c01-u01-complex-conjugates-modulus",
                "unitCode": unit,
                "level": 3,
                "name": "Complex Conjugates and Modulus Product",
                "coreConcept": "Compute modulus and conjugate product of a complex number in standard form.",
                "governingRelation": "z * conj(z) = a^2 + b^2",
                "cognitiveTraps": [
                    {
                        "trapTag": "t02-c01-u01-conjugate-modulus-change-trap",
                        "description": "Assumes conjugate has different modulus than original number.",
                    }
                ],
                "figureNone": "Symbolic.",
            },
            {
                "archetypeKey": "t02-c01-u01-adding-complex-numbers",
                "unitCode": unit,
                "level": 1,
                "name": "Adding Complex Numbers in Standard Form",
                "coreConcept": "Add complex numbers in standard form by combining real and imaginary parts.",
                "governingRelation": "(a+bi)+(c+di) = (a+c)+(b+d)i",
                "cognitiveTraps": [
                    {
                        "trapTag": "t02-c01-u01-add-real-and-imaginary-parts-trap",
                        "description": "Combines real coefficient directly with imaginary coefficient.",
                    }
                ],
                "figureNone": "Symbolic.",
            },
        ],
    }
    (vault_dir / f"{unit}.json").write_text(json.dumps(vault_payload), encoding="utf-8")

    cards = [
        # 1. Clearly belongs to one archetype
        _sample_card(
            id="CARD-CLEAR",
            level=2,
            reasoningMove="direct",
            skill="Evaluate large powers of the imaginary unit i by reducing exponents modulo four",
            difficultyDriver="Large integer exponent reduced mod 4",
            traps=[
                {
                    "tag": "t02-c01-u01-power-of-i-remainder-trap",
                    "description": "Maps exponent remainder mod 4 to wrong power of i",
                }
            ],
        ),
        # 2. Ambiguous card spanning two archetypes (plus a 3rd trap to verify <=2 cap)
        _sample_card(
            id="CARD-AMBIGUOUS",
            level=3,
            reasoningMove="multi-relation",
            skill="Expand complex binomials and rationalize complex quotients in standard form",
            difficultyDriver="Combines FOIL expansion, denominator conjugate, and modulus check",
            traps=[
                {
                    "tag": "t02-c01-u01-cross-term-omission-trap",
                    "description": "Omits cross terms when squaring a complex binomial",
                },
                {
                    "tag": "t02-c01-u01-denominator-conjugate-sign-error-trap",
                    "description": "Subtracts d^2 instead of adding in rationalized denominator",
                },
                {
                    "tag": "t02-c01-u01-conjugate-modulus-change-trap",
                    "description": "Assumes conjugate changes modulus",
                },
            ],
        ),
        # 3. Unmatched card despite sharing generic domain words ("complex", "number", "form")
        _sample_card(
            id="CARD-UNMATCHED",
            level=4,
            reasoningMove="translate",
            skill="Convert complex numbers into polar trigonometric form using De Moivre angle rotation",
            difficultyDriver="Quadrant selection for inverse tangent argument",
            traps=[
                {
                    "tag": "t02-c01-u01-de-moivre-argument-wrap-trap",
                    "description": "Fails to adjust polar angle for second or third quadrant",
                }
            ],
        ),
    ]
    source_cores.save_core_cards(unit, cards, sources_dir=str(tmp_path))

    rc = source_gap.main([unit, "--sources-dir", str(tmp_path), "--vault-dir", str(vault_dir), "--json"])
    assert rc == 0
    report = json.loads(capsys.readouterr().out)

    by_id = {m["id"]: m for m in report["matchedCards"]}
    assert set(by_id) == {"CARD-CLEAR", "CARD-AMBIGUOUS"}
    assert [u["id"] for u in report["unmatchedCards"]] == ["CARD-UNMATCHED"]

    clear_matches = by_id["CARD-CLEAR"]["matches"]
    assert len(clear_matches) == 1
    assert clear_matches[0]["archetypeKey"] == "t02-c01-u01-powers-of-i-cycle"
    assert clear_matches[0]["score"] >= 0.5
    assert clear_matches[0]["reason"]
    assert clear_matches[0]["scoreBreakdown"]["trap"] > clear_matches[0]["scoreBreakdown"]["skill"]

    amb_matches = by_id["CARD-AMBIGUOUS"]["matches"]
    assert len(amb_matches) == 2
    assert all(m["score"] >= source_gap.RUNNER_UP_THRESHOLD for m in amb_matches)
    assert all(len(m["matches"]) <= 2 for m in report["matchedCards"])

    # --novelty still works alongside the updated matching
    batch_file = tmp_path / "batch.jsonl"
    dup_card = {**cards[0], "id": "CARD-CLEAR-DUP"}
    batch_file.write_text(json.dumps(dup_card) + "\n", encoding="utf-8")
    rc_nov = source_gap.main([unit, "--novelty", str(batch_file), "--sources-dir", str(tmp_path), "--json"])
    assert rc_nov == 0
    nov = json.loads(capsys.readouterr().out)
    assert nov["duplicateCardsCount"] == 1


def test_source_gap_prg_structured_matching_and_regression(tmp_path: Path) -> None:
    unit = "PRG-T00-C03"
    vault_dir = tmp_path / "code-vault"
    vault_dir.mkdir()
    vault_payload = {
        "unitCode": unit,
        "archetypes": [
            {
                "archetypeKey": "prg-c02-primitive-coercion-guard",
                "unitCode": "PRG-T00-C03-U01",
                "level": 1,
                "archetype": "problem-solving",
                "name": "Defensive Primitive Sanitization and Coercion Guard",
                "coreConcept": "Handle nullish values safely without overwriting legitimate falsy values.",
                "governingInvariant": "sanitized = inputVal !== null && inputVal !== undefined ? inputVal : defaultVal",
                "cognitiveTraps": [
                    {
                        "trapTag": "falsy-numeric-zero-overwrite",
                        "description": "Logical OR overwrites legitimate 0 with fallback default.",
                    }
                ],
                "qualityChecks": [
                    {
                        "id": "QC-coercion-explicit-nullish-intent",
                        "check": "Distinguish nullish values from falsy 0 or false.",
                        "severity": "must",
                    }
                ],
            },
            {
                "archetypeKey": "prg-c02-lexical-closure-factory",
                "unitCode": "PRG-T00-C03-U02",
                "level": 2,
                "archetype": "problem-solving",
                "name": "Encapsulated Lexical Scope and Closure State Factory",
                "coreConcept": "Retain private state inside closure lexical scope without leaking mutable references.",
                "governingInvariant": "privateState accessible exclusively through returned accessor functions",
                "cognitiveTraps": [
                    {
                        "trapTag": "closure-shared-reference-leak",
                        "description": "Returning direct reference to private mutable array breaks encapsulation.",
                    }
                ],
                "qualityChecks": [
                    {
                        "id": "QC-closure-no-ref-escape",
                        "check": "No reference to internal mutable state escapes the factory.",
                        "severity": "must",
                    }
                ],
            },
            {
                "archetypeKey": "prg-c02-immutable-array-pipeline",
                "unitCode": "PRG-T00-C03-U02",
                "level": 2,
                "archetype": "problem-solving",
                "name": "Immutable Collection Transformation Pipeline",
                "coreConcept": "Transform collections with pure map, filter, and reduce stages without mutating input.",
                "governingInvariant": "outputCollection = reduce(filter(map(inputCollection)))",
                "cognitiveTraps": [
                    {
                        "trapTag": "in-place-array-mutation",
                        "description": "Sorting or splicing the input array mutates caller data.",
                    }
                ],
                "qualityChecks": [
                    {
                        "id": "QC-pipeline-pure-stages",
                        "check": "Derived collections never mutate caller-owned arrays.",
                        "severity": "must",
                    }
                ],
            },
            {
                "archetypeKey": "prg-c02-async-promise-combinator",
                "unitCode": "PRG-T00-C03-U03",
                "level": 3,
                "archetype": "problem-solving",
                "name": "Resilient Async Promise Combinator",
                "coreConcept": "Coordinate concurrent asynchronous promises with failure isolation and result ordering.",
                "governingInvariant": "all promises settled before resolving combinator",
                "cognitiveTraps": [
                    {
                        "trapTag": "unhandled-rejection-fast-fail",
                        "description": "Promise.all aborts sibling results on one rejection.",
                    }
                ],
                "qualityChecks": [
                    {
                        "id": "QC-async-isolated-settlement",
                        "check": "Isolate per-task rejections when partial failure tolerance is required.",
                        "severity": "must",
                    }
                ],
            },
        ],
    }
    (vault_dir / f"{unit}.json").write_text(json.dumps(vault_payload), encoding="utf-8")

    cards = [
        _sample_prg_card(
            id="PRG-CLEAR",
            unitCode="PRG-T00-C03-U02",
            level=2,
            archetypeKind="implement",
            skill="Encapsulate private state inside a lexical closure factory with controlled accessors",
            concept="lexical closure encapsulation",
            bugPattern="Exposing a direct mutable array reference lets callers bypass the factory API",
            traps=[
                {
                    "tag": "closure-shared-reference-leak",
                    "description": "Direct reference to internal mutable array allows external mutation",
                }
            ],
            qualityCheckIdeas=[
                {
                    "id": "QC-closure-no-ref-escape",
                    "check": "Prevent internal mutable state references from escaping closure accessors",
                }
            ],
        ),
        _sample_prg_card(
            id="PRG-TYPICAL",
            unitCode=unit,
            level=2,
            archetypeKind="implement",
            skill="Transform array data using pure map and filter functions without mutating input state",
            concept="pure collection pipelines",
            bugPattern="Sorting input arrays in place alters caller state",
            traps=[
                {
                    "tag": "in-place-array-mutation",
                    "description": "Mutating the caller array during sorting or filtering",
                }
            ],
            qualityCheckIdeas=[
                {
                    "id": "QC-pipeline-pure-stages",
                    "check": "Keep transformation stages pure without mutating caller arrays",
                }
            ],
        ),
        _sample_prg_card(
            id="PRG-UNMATCHED",
            unitCode="PRG-T00-C03-U04",
            level=4,
            archetypeKind="find-the-bug",
            skill="Diagnose circular import deadlocks across module dependency graphs",
            concept="module dependency cycles",
            bugPattern="Mutual top-level imports read partially initialized exports",
            traps=[
                {
                    "tag": "circular-import-deadlock",
                    "description": "Reads uninitialized binding during cyclic module evaluation",
                }
            ],
            qualityCheckIdeas=[
                {
                    "id": "QC-acyclic-module-graph",
                    "check": "Verify module dependencies form a directed acyclic graph",
                }
            ],
        ),
    ]
    source_cores.save_core_cards(unit, cards, sources_dir=str(tmp_path))

    report = source_gap.build_gap_report(unit, sources_dir=str(tmp_path), vault_dir=str(vault_dir))
    by_id = {m["id"]: m for m in report["matchedCards"]}
    assert set(by_id) == {"PRG-CLEAR", "PRG-TYPICAL"}
    assert [u["id"] for u in report["unmatchedCards"]] == ["PRG-UNMATCHED"]

    clear_hit = by_id["PRG-CLEAR"]["matches"]
    assert len(clear_hit) == 1
    assert clear_hit[0]["archetypeKey"] == "prg-c02-lexical-closure-factory"
    assert clear_hit[0]["matchedQualityChecks"] == ["QC-closure-no-ref-escape"]
    assert clear_hit[0]["score"] >= 0.6
    assert "trap:closure-shared-reference-leak" in clear_hit[0]["reason"]

    typical_hit = by_id["PRG-TYPICAL"]["matches"]
    assert len(typical_hit) <= 2
    assert typical_hit[0]["archetypeKey"] == "prg-c02-immutable-array-pipeline"

    # Unit compatibility: same-unit archetype beats mismatched-unit archetype when content is equal
    same_unit = source_gap.score_card_against_archetype(
        cards[0],
        vault_payload["archetypes"][1],
        unit_code=unit,
        is_prg=True,
    )
    wrong_unit_arch = {**vault_payload["archetypes"][1], "unitCode": "PRG-T00-C03-U04", "level": 5}
    diff_unit = source_gap.score_card_against_archetype(
        cards[0],
        wrong_unit_arch,
        unit_code=unit,
        is_prg=True,
    )
    assert same_unit["score"] > diff_unit["score"]
    assert same_unit["scoreBreakdown"]["compatibility"] > diff_unit["scoreBreakdown"]["compatibility"]


def test_source_gap_prg_trap_aliases_and_threshold(tmp_path: Path) -> None:
    """PRG cards with ad-hoc trap tags alias onto consolidated vault traps without falsely matching unrelated cards."""
    unit = "PRG-T00-C03"
    vault_dir = tmp_path / "code-vault"
    vault_dir.mkdir()
    vault_payload = {
        "unitCode": unit,
        "archetypes": [
            {
                "archetypeKey": "prg-c02-immutable-array-pipeline",
                "unitCode": "PRG-T00-C03-U02",
                "level": 2,
                "archetype": "problem-solving",
                "name": "Immutable Collection Transformation Pipeline",
                "coreConcept": "Derive new arrays with map, filter, and reduce without mutating caller inputs.",
                "governingInvariant": "output = reduce(filter(map(input)))",
                "cognitiveTraps": [
                    {
                        "trapTag": "in-place-array-mutation",
                        "description": "Mutating the input array in place alters caller state.",
                    },
                    {
                        "trapTag": "collection-result-contract",
                        "description": "Callback side effect confused with returned collection result.",
                        "aliases": ["custom-vault-declared-alias"],
                    },
                ],
                "qualityChecks": [
                    {"id": "QC-pipeline-pure-stages", "check": "Never mutate caller arrays.", "severity": "must"}
                ],
            },
            {
                "archetypeKey": "prg-c02-async-promise-combinator",
                "unitCode": "PRG-T00-C03-U03",
                "level": 3,
                "archetype": "problem-solving",
                "name": "Resilient Async Promise Combinator",
                "coreConcept": "Coordinate concurrent promises and propagate settlement results.",
                "governingInvariant": "all promises settled before resolving combinator",
                "cognitiveTraps": [
                    {
                        "trapTag": "async-result-propagation",
                        "description": "Callback starts async work without returning the promise.",
                    }
                ],
                "qualityChecks": [
                    {"id": "QC-async-propagation", "check": "Return or await async work.", "severity": "should"}
                ],
            },
        ],
    }
    (vault_dir / f"{unit}.json").write_text(json.dumps(vault_payload), encoding="utf-8")

    cards = [
        _sample_prg_card(
            id="PRG-ALIAS-BUILT-IN",
            unitCode=unit,
            level=2,
            archetypeKind="implement",
            skill="Build a collection transformation that preserves input data",
            concept="non-mutating collection operations",
            bugPattern="Sorting input directly alters original data",
            traps=[{"tag": "preserve-input", "description": "Mutates caller collection"}],
            qualityCheckIdeas=[{"id": "QC-preserve-input", "check": "Keep input unchanged"}],
        ),
        _sample_prg_card(
            id="PRG-ALIAS-VAULT-DECLARED",
            unitCode=unit,
            level=2,
            archetypeKind="implement",
            skill="Choose callback shapes that match collection outputs",
            concept="higher-order callback contracts",
            bugPattern="Side effect callback leaves result empty",
            traps=[{"tag": "custom-vault-declared-alias", "description": "Callback returns nothing"}],
            qualityCheckIdeas=[{"id": "QC-callback-shape", "check": "Return value from callback"}],
        ),
        _sample_prg_card(
            id="PRG-GENUINELY-UNMATCHED",
            unitCode="PRG-T00-C03-U04",
            level=4,
            archetypeKind="find-the-bug",
            skill="Diagnose circular import deadlocks across module dependency graphs",
            concept="module dependency cycles",
            bugPattern="Mutual top-level imports read partially initialized exports",
            traps=[{"tag": "circular-import-deadlock", "description": "Cyclic module evaluation"}],
            qualityCheckIdeas=[{"id": "QC-acyclic-module-graph", "check": "Verify acyclic imports"}],
        ),
    ]
    source_cores.save_core_cards(unit, cards, sources_dir=str(tmp_path))

    report = source_gap.build_gap_report(unit, sources_dir=str(tmp_path), vault_dir=str(vault_dir))
    by_id = {m["id"]: m for m in report["matchedCards"]}
    assert set(by_id) == {"PRG-ALIAS-BUILT-IN", "PRG-ALIAS-VAULT-DECLARED"}
    assert [u["id"] for u in report["unmatchedCards"]] == ["PRG-GENUINELY-UNMATCHED"]
    assert "alias-trap:preserve-input->in-place-array-mutation" in by_id["PRG-ALIAS-BUILT-IN"]["matches"][0]["reason"]
    assert (
        "alias-trap:custom-vault-declared-alias->collection-result-contract"
        in by_id["PRG-ALIAS-VAULT-DECLARED"]["matches"][0]["reason"]
    )
    # Aliased traps are covered by the vault and not reported as new traps
    new_trap_tags = {t["tag"] for t in report["newTraps"]}
    assert "preserve-input" not in new_trap_tags
    assert "custom-vault-declared-alias" not in new_trap_tags
    assert "circular-import-deadlock" in new_trap_tags
