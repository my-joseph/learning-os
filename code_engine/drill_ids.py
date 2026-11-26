# -*- coding: utf-8 -*-
"""Drill ID sequencing and Notion id_map helpers for code_engine."""

from __future__ import annotations

import glob
import json
import os
from pathlib import Path
from typing import Any

from code_engine.sandbox import assert_safe_contained_path


def load_id_map(path: str = "id_map.json") -> dict[str, Any]:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def notion_url_for(code: str, id_map: dict[str, Any]) -> str | None:
    entry = id_map.get(code)
    if not entry:
        return None
    raw_id = (entry["id"] if isinstance(entry, dict) else str(entry)).replace("-", "")
    return f"https://www.notion.so/{raw_id}"


def next_drill_id(unit_code: str, data_root: str | None = None) -> str:
    if data_root is None:
        data_root = os.environ.get("DRILLS_DATA_DIR", "drills/data")
    root = Path(data_root)
    checkout = Path.cwd()
    boundary = checkout if root.absolute().is_relative_to(checkout) else root
    root = assert_safe_contained_path(root, boundary, expect_file=False, allow_missing=True)
    unit_dir = assert_safe_contained_path(unit_code, root, expect_file=False, relative=True, allow_missing=True)
    unit_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(glob.glob(os.path.join(unit_dir, f"DRL-{unit_code}-*.json")))
    max_num = 0
    for p in existing:
        base = os.path.splitext(os.path.basename(p))[0]
        parts = base.rsplit("-", 1)
        if len(parts) == 2 and parts[1].isdigit():
            max_num = max(max_num, int(parts[1]))
    return f"DRL-{unit_code}-{max_num + 1:02d}"
