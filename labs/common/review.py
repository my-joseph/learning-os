# -*- coding: utf-8 -*-
"""
Proxy runner for AI Senior Tech Lead PR Review in Labs.
"""

import subprocess
import sys
from pathlib import Path

# Locate repo root and delegate to code_engine/review.py
script_dir = Path(__file__).resolve().parent
repo_root = script_dir.parent.parent
engine_review = repo_root / "code_engine" / "review.py"

if not engine_review.exists():
    print(f"Error: Cannot locate {engine_review}")
    sys.exit(1)

res = subprocess.run([sys.executable, str(engine_review)] + sys.argv[1:])
sys.exit(res.returncode)
