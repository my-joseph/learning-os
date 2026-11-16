# -*- coding: utf-8 -*-
"""
Code review instructions helper for Project Labs (clipboard prompt retired).
"""

from __future__ import annotations

import json
import sys
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
    milestones = json.loads(cfg_path.read_text()).get("milestones", []) if cfg_path.exists() else []
    allowed = {m.get("id", "").upper() for m in milestones}
    milestone = next((arg.upper() for arg in sys.argv[1:] if arg.upper() in allowed), "M1")
    print(f"\n=== PRG Code Review ({lab_id}) ===")
    print(f"  In Claude Code, say: ตรวจโค้ด {lab_id} {milestone}")
    print("  Local deterministic checks: npm run check")
    print("  (For drill problems: python -m code_engine.review_run <DRILL_ID> <QID>)\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
