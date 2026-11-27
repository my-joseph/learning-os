"""Tests for the optional Thai PDF OCR fallback."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from scripts import extract_cards_job, source_find


def test_classify_pdf_text_quality_for_scans_legacy_fonts_and_unicode() -> None:
    assert source_find.classify_text_quality("  \n\t") == "empty"
    assert source_find.classify_text_quality("ข้อ 1 ที' 2 + 3 = 5 และมุม A&B; ข้อ 2 นี' 4 = 6") == "garbled"
    assert source_find.classify_text_quality("ข้อ 1 ที่มีจำนวนเชิงซ้อนและสังยุค") == "ok"
    assert source_find.classify_text_quality("Solve the equation and simplify the expression 3x + 2 = 8") == "ok"


def test_ocr_cache_key_is_stable_and_scoped_to_file_hash_and_page() -> None:
    first = source_find.ocr_cache_key("a" * 64, 3)
    assert first == source_find.ocr_cache_key("a" * 64, 3)
    assert first != source_find.ocr_cache_key("b" * 64, 3)
    assert first != source_find.ocr_cache_key("a" * 64, 4)
    assert first.startswith(hashlib.sha256(b"a" * 64 + b":3").hexdigest())


def test_ocr_weak_text_flags_page_image_for_missing_math_notation() -> None:
    assert source_find._ocr_needs_image("สมการกำลังสองมีข้อความไทยเพียงอย่างเดียว", 91.0)
    assert source_find._ocr_needs_image("x = 2", 42.0)
    assert not source_find._ocr_needs_image("Solve x^2 + 3x = 0 with Thai explanation", 91.0)


def test_worker_prompt_includes_ocr_text_and_cached_image_path(tmp_path: Path) -> None:
    sources_dir = tmp_path / "sources"
    index_dir = sources_dir / "_index"
    index_dir.mkdir(parents=True)
    image_name = "ocr_fixture_p1.png"
    image_path = index_dir / image_name
    image_path.write_bytes(b"fixture image")
    plan = {
        "unitCode": "MTH-T02-C01-U02",
        "sourcesDir": str(sources_dir),
        "budget": {"maxItems": 1},
        "batches": [
            {
                "batch": 1,
                "pageCount": 1,
                "estimatedItems": 1,
                "pages": [
                    {
                        "rank": 1,
                        "family": "thai-exams",
                        "mode": "cores",
                        "relPath": "thai-exams/math.pdf",
                        "page": 1,
                        "cacheFile": "pdf_fixture.json",
                        "fileHash": "a" * 64,
                        "hits": 1,
                        "terms": {"quadratic": 1},
                        "itemAllowance": 1,
                        "textSource": "ocr",
                        "needsImage": True,
                        "imageFile": image_name,
                        "ocrText": "OCR fixture text",
                    }
                ],
            }
        ],
    }
    (index_dir / "plan_MTH-T02-C01-U02.json").write_text(json.dumps(plan), encoding="utf-8")

    prompt = extract_cards_job.build_worker_prompt("MTH-T02-C01-U02", 1, sources_dir=str(sources_dir))
    assert "OCR fixture text" in prompt
    assert str(image_path) in prompt
    assert "Open and read this page image (view_image or your image tool)" in prompt
    assert "extract cores only, never copy wording or numbers" in prompt


def test_ocr_missing_binary_degrades_to_warning_and_no_result(tmp_path, monkeypatch, capsys) -> None:
    def missing_binary(*args, **kwargs):
        raise FileNotFoundError("pdftoppm")

    monkeypatch.setattr(source_find.subprocess, "run", missing_binary)
    result = source_find._ocr_page("missing.pdf", 1, "f" * 64, str(tmp_path))
    assert result is None
    assert "WARNING: OCR fallback unavailable" in capsys.readouterr().err


def test_ocr_tesseract_failure_keeps_page_rendered_for_visual_fallback(tmp_path, monkeypatch, capsys) -> None:
    calls = 0

    def fake_run(command, **kwargs):
        nonlocal calls
        calls += 1
        if command[0] == "pdftoppm":
            prefix = command[-1]
            with open(prefix + ".png", "wb") as fh:
                fh.write(b"png")
            return subprocess.CompletedProcess(command, 0, "", "")
        raise FileNotFoundError("tesseract")

    monkeypatch.setattr(source_find.subprocess, "run", fake_run)
    result = source_find._ocr_page("source.pdf", 2, "e" * 64, str(tmp_path))
    assert result is not None and result["ocrUnavailable"] is True and result["needsImage"] is True
    assert calls == 2
    assert list(tmp_path.glob("ocr_*.png"))
    assert "WARNING: OCR fallback unavailable" in capsys.readouterr().err


def test_plan_diagnostics_count_nonmatching_pages_and_only_retry_unresolved_ocr(tmp_path, monkeypatch) -> None:
    pdf = tmp_path / "SmartMathPro" / "fixture.pdf"
    pdf.parent.mkdir()
    pdf.write_bytes(b"%PDF test fixture")
    pages = [
        {"page": 1, "text": ""},
        {"page": 2, "text": "ข้อ 1 ที' 2 + 3 = 5 และมุม A&B; ข้อ 2 นี' 4 = 6"},
        {"page": 3, "text": "Quadratic expressions can be factored."},
    ]
    monkeypatch.setattr(
        source_find,
        "_load_or_extract_pdf",
        lambda *args, **kwargs: (
            "fixture.json",
            {
                "pages": pages,
                "fileHash": "test-hash",
            },
        ),
    )
    monkeypatch.setattr(
        source_find,
        "_ocr_page",
        lambda _path, page, *_args, **_kwargs: (
            {"ocrUnavailable": True, "needsImage": True}
            if page == 1
            else {"text": "Recovered text without the requested term.", "needsImage": False}
        ),
    )

    found = source_find.find_sources("MTH-T02-C01-U02", terms=["quadratic"], sources_dir=str(tmp_path))
    plan = source_find.build_extraction_plan(found, sources_dir=str(tmp_path))
    assert plan["diagnostics"] == {
        "emptyPages": 1,
        "garbledPages": 1,
        "sourceFamilyCount": 1,
        "ocrRetry": [{"relPath": "SmartMathPro/fixture.pdf", "page": 1, "originalQuality": "empty"}],
    }
    assert "OCR retry: 1 page(s)" in source_find.format_plan_report(plan)
