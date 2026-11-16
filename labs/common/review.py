# -*- coding: utf-8 -*-
"""
Code review instructions helper for Project Labs (clipboard prompt retired).
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    ws_dir = Path.cwd()
    lab_id = ws_dir.name
    cfg_path = ws_dir / "lab.config.json"
    if cfg_path.exists():
        try:
            lab_id = json.loads(cfg_path.read_text(encoding="utf-8")).get("labId", lab_id)
        except Exception:
            pass
    print(f"\n=== PRG Code Review ({lab_id}) ===")
    print(f"  In Claude Code, say: review code {lab_id}")
    print("  Local deterministic checks: npm run check")
    print("  (For drill problems: python -m code_engine.review_run <DRILL_ID> <QID>)\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
