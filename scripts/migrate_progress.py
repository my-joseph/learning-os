#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-time move of learner progress out of drill content files.

For every drills/data/<UNIT>/DRL-*.json:
  1. if it carries practice (answers, scores, attempts, summary), save that to
     progress/<DRILL_ID>.json (an existing progress file is kept unless --force);
  2. remove `state` / `sessionSummary` from the drill file, keeping its formatting.

Run from the repo root:  python scripts/migrate_progress.py [--dry-run] [--force]
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from progress_store import has_practice, progress_path, save_progress, strip_progress  # noqa: E402


def migrate(data_root: str = "drills/data", dry_run: bool = False, force: bool = False) -> dict[str, list[str]]:
    report: dict[str, list[str]] = {"saved": [], "kept_existing": [], "stripped": []}
    for path in sorted(glob.glob(os.path.join(data_root, "*", "DRL-*.json"))):
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
        doc = json.loads(raw)
        drill_id = doc.get("drillId") or Path(path).stem

        if has_practice(doc):
            if os.path.exists(progress_path(drill_id)) and not force:
                report["kept_existing"].append(drill_id)
            else:
                if not dry_run:
                    save_progress(doc)
                report["saved"].append(drill_id)

        has_fields = "sessionSummary" in doc or any("state" in p for p in doc.get("problems", []))
        if has_fields:
            strip_progress(doc)
            if not dry_run:
                out = json.dumps(doc, ensure_ascii=False, indent=2)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(out + ("\n" if raw.endswith("\n") else ""))
            report["stripped"].append(drill_id)
    return report


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-root", default=os.environ.get("DRILLS_DATA_DIR", "drills/data"))
    ap.add_argument("--dry-run", action="store_true", help="report only; write nothing")
    ap.add_argument("--force", action="store_true", help="overwrite existing progress files")
    args = ap.parse_args()
    rep = migrate(args.data_root, dry_run=args.dry_run, force=args.force)
    prefix = "[dry-run] " if args.dry_run else ""
    print(f"{prefix}progress saved:   {len(rep['saved'])} {rep['saved']}")
    print(f"{prefix}progress kept:    {len(rep['kept_existing'])} {rep['kept_existing']}")
    print(f"{prefix}drills stripped:  {len(rep['stripped'])}")


if __name__ == "__main__":
    main()
