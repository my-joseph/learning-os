from __future__ import annotations

import subprocess
import sys
from pathlib import Path

lab_dir = Path(__file__).resolve().parents[1]
repo_root = lab_dir.parents[1]
shared_modules = repo_root / "tools" / "lint" / "node_modules"
tsc = shared_modules / ".bin" / "tsc"
project = Path(sys.argv[1] if len(sys.argv) > 1 else "tsconfig.json")
if not project.is_absolute():
    project = (lab_dir / project).resolve()
module_link = project.parent / "node_modules"
created = False
if not module_link.exists() and not module_link.is_symlink():
    module_link.symlink_to(shared_modules, target_is_directory=True)
    created = True
try:
    result = subprocess.run([str(tsc), "--noEmit", "-p", str(project)], cwd=lab_dir, check=False)
    raise SystemExit(result.returncode)
finally:
    if created:
        module_link.unlink(missing_ok=True)
