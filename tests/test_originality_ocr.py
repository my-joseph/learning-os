"""Originality source loading falls back to the source_find OCR cache."""

from __future__ import annotations

import hashlib
import json

import pytest

from math_engine.source_cores.originality import load_located_source_pages
from scripts import source_find


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


@pytest.mark.parametrize("path_kind", ["core", "fallback"])
def test_non_manifest_source_paths_use_source_find_ocr_cache(tmp_path, monkeypatch, path_kind):
    unit_code = "MTH-T02-C01-U01"
    rel_path = "thai-exams/mock.pdf"
    file_hash = "b" * 64
    index_dir = tmp_path / "_index"
    index_dir.mkdir(parents=True)
    (index_dir / "pdf_fixture.json").write_text(
        json.dumps(
            {
                "relPath": rel_path,
                "fileHash": file_hash,
                "pages": [{"page": 7, "text": ""}],
            }
        ),
        encoding="utf-8",
    )
    ocr_key = source_find.ocr_cache_key(file_hash, 7)
    (index_dir / f"ocr_{ocr_key}.json").write_text(
        json.dumps({"text": "OCR source includes a distinctive algebra exercise"}),
        encoding="utf-8",
    )
    if path_kind == "core":
        cores_dir = tmp_path / "_cores"
        cores_dir.mkdir()
        (cores_dir / f"{unit_code}.jsonl").write_text(
            json.dumps({"sourceRef": {"file": "mock.pdf", "page": 7}}) + "\n",
            encoding="utf-8",
        )
    else:
        monkeypatch.setattr("math_engine.source_cores.originality.get_unit_terms", lambda _unit: ["OCR"])

    pages = load_located_source_pages(unit_code, sources_dir=str(tmp_path))

    assert pages == [{"relPath": rel_path, "page": 7, "text": "OCR source includes a distinctive algebra exercise"}]
