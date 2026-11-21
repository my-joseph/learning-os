"""Originality source loading falls back to the source_find OCR cache."""

from __future__ import annotations

import hashlib
import json

import pytest

from math_engine.source_cores.originality import load_located_source_pages


@pytest.mark.parametrize(
    ("pdf_text", "page_metadata"),
    [
        ("", {"textQuality": "empty"}),
        ("garbled glyphs", {"textQuality": "garbled"}),
        ("stale raw text", {"textSource": "ocr"}),
    ],
)
def test_located_source_page_uses_ocr_cache_when_raw_pdf_text_is_unusable(tmp_path, pdf_text, page_metadata):
    unit_code = "MTH-T02-C01-U01"
    rel_path = "thai-exams/mock.pdf"
    file_hash = "a" * 64
    index_dir = tmp_path / "_index"
    index_dir.mkdir(parents=True)
    (index_dir / "pdf_fixture.json").write_text(
        json.dumps({"relPath": rel_path, "pages": [{"page": 12, "text": pdf_text}]}),
        encoding="utf-8",
    )
    ocr_key = hashlib.sha256(f"{file_hash}:12".encode("utf-8")).hexdigest()
    (index_dir / f"ocr_{ocr_key}_p12.json").write_text(
        json.dumps({"text": "Thai OCR source text with x + 3 = 8"}), encoding="utf-8"
    )
    (index_dir / f"located_{unit_code}.json").write_text(
        json.dumps(
            {
                "matches": [
                    {
                        "relPath": rel_path,
                        "cacheFile": "pdf_fixture.json",
                        "fileHash": file_hash,
                        "pages": [{"page": 12, **page_metadata}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    pages = load_located_source_pages(unit_code, sources_dir=str(tmp_path))

    assert pages == [{"relPath": rel_path, "page": 12, "text": "Thai OCR source text with x + 3 = 8"}]
