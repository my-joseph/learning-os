from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

lab_dir = Path(__file__).resolve().parents[1]
shared_modules = lab_dir.parents[1] / "tools" / "lint" / "node_modules"
vitest = shared_modules / ".bin" / "vitest"
source = Path(os.environ.get("LAB_SRC_DIR", "../src"))
if not source.is_absolute():
    first_test = next(
        (Path(arg) for arg in sys.argv[1:] if arg.endswith((".test.tsx", ".test.ts", ".test.js"))),
        Path("tests/test.tsx"),
    )
    if not first_test.is_absolute():
        first_test = (lab_dir / first_test).resolve()
    source = (first_test.parent / source).resolve()
link_targets = {lab_dir, source.parent}
created: list[Path] = []
try:
    for target in link_targets:
        link = target / "node_modules"
        if not link.exists() and not link.is_symlink():
            link.symlink_to(shared_modules, target_is_directory=True)
            created.append(link)
    with tempfile.TemporaryDirectory(prefix="lab_vitest_config_", dir=shared_modules) as temp:
        config = Path(temp) / "vitest.config.ts"
        config.write_text(
            "import { defineConfig } from 'vitest/config';\n"
            f"export default defineConfig({{ root: {str(first_test.parent)!r}, esbuild: {{ jsx: 'automatic' }}, test: {{ environment: 'jsdom' }}, server: {{ fs: {{ allow: [{str(lab_dir.resolve())!r}, {str(source.resolve())!r}, {str(lab_dir.parents[1])!r}] }} }} }});\n",
            encoding="utf-8",
        )
        test_files = [str((lab_dir / arg).resolve()) if not Path(arg).is_absolute() else arg for arg in sys.argv[1:]]
        result = subprocess.run(
            [str(vitest), "run", *test_files, "--config", str(config), "--environment", "jsdom"],
            cwd=lab_dir,
            env={**os.environ, "LAB_SRC_DIR": str(source)},
            check=False,
        )
        raise SystemExit(result.returncode)
finally:
    for link in created:
        link.unlink(missing_ok=True)
