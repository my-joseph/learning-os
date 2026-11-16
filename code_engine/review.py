# -*- coding: utf-8 -*-
"""
PRG Code Review helper (retired clipboard prompt — replaced by rubric-bound review).

Prints how to request a code review in Claude Code and how to run Layer 1-2 checks locally.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def format_review_instructions(ws_dir: Path, target_qid: str | None = None) -> str:
    """Return human-readable instructions for requesting a PRG code review."""
    is_lab = (ws_dir / "lab.config.json").exists()
    if is_lab:
        cfg = json.loads((ws_dir / "lab.config.json").read_text(encoding="utf-8"))
        lab_id = cfg.get("labId", ws_dir.name)
        return (
            f"Code review for {lab_id}:\n"
            f"  In Claude Code, say: review code {lab_id}\n"
            f"  Local deterministic checks: npm run check\n"
            f"  (For drill problems: python -m code_engine.review_run <DRILL_ID> <QID>)"
        )

    drill_id = ws_dir.name
    qid = (target_qid or "Q01").upper()
    return (
        f"Code review for {drill_id} {qid}:\n"
        f"  In Claude Code, say: review code {drill_id} {qid}\n"
        f"  Run Layer 1 (tests) + Layer 2 (ESLint/tsc) + rubric:\n"
        f"    python -m code_engine.review_run {drill_id} {qid}"
    )


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    target_arg = None
    for arg in args:
        if arg.startswith("--target="):
            target_arg = arg.split("=", 1)[1]
        elif not arg.startswith("-"):
            target_arg = arg

    ws_dir = Path.cwd()
    msg = format_review_instructions(ws_dir, target_arg)
    print(f"\n{BOLD}{CYAN}=== PRG Code Review ==={RESET}")
    print(msg)
    print(f"{DIM}(Clipboard prompt retired; reviews are recorded via scripts.review_record.){RESET}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
