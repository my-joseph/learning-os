#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Report math problems whose prompt (or display) gives away the solution.

Read-only. Usage:
    python scripts/audit_solution_leaks.py                 # all math drills
    python scripts/audit_solution_leaks.py MTH-T01-C12     # one unit
    python scripts/audit_solution_leaks.py --display       # also check the display box
"""

import argparse
import glob
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from math_engine.ai_drill_ingest import find_solution_leaks  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("unit", nargs="?", default="MTH-*", help="unit folder glob under drills/data")
    ap.add_argument("--display", action="store_true", help="also flag set-up computations in `display`")
    ap.add_argument("--data-root", default=os.environ.get("DRILLS_DATA_DIR", "drills/data"))
    args = ap.parse_args(argv)

    total = flagged = 0
    for path in sorted(glob.glob(os.path.join(args.data_root, args.unit, "*.json"))):
        with open(path, encoding="utf-8") as f:
            drill = json.load(f)
        for prob in drill.get("problems", []):
            total += 1
            display = prob.get("display", "") if args.display else ""
            reasons = find_solution_leaks(prob.get("prompt", ""), display)
            if reasons:
                flagged += 1
                print(f"{drill.get('drillId')} {prob.get('id')} (L{prob.get('level')})")
                for r in reasons:
                    print(f"   - {r}")
    print(f"\n{flagged} of {total} problems flagged")
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())
