# -*- coding: utf-8 -*-
"""
Shared least-privilege execution sandbox for PRG learner and reference code.

Used across `code_engine.test_runner`, `code_engine.submit`, `code_engine.review_run`,
`code_engine.lab_ingest`, `code_engine.verify`, `code_engine.lint_check`,
`code_engine.ai_drill_ingest`, and `labs/common/submit_lab.py`.

Isolation layers (local single-user macOS + Linux CI, stdlib only):
1. Scrubbed environment: allowlist only (`PATH`, `HOME`, `TMPDIR`, `LANG`, `LC_ALL`,
   `TZ`, `CI`, `NO_COLOR`, plus explicit non-secret vars like `LAB_SRC_DIR`). Never
   inherits `NOTION_TOKEN`, `NODE_OPTIONS`, cloud/API keys, or Studio secrets.
2. Ephemeral workspace copy: `cwd`, `HOME`, and `TMPDIR` live inside a per-run temp
   directory outside the repository. Symlinked roots/files and escaping paths are
   rejected before staging so real workspaces, `progress/`, `sources/`, `drills/data/`,
   `labs/_reference/`, and host secrets are never copied or mutated.
3. Filesystem & process confinement:
   - Node 24 `--permission` (`--allow-fs-read`, `--allow-fs-write`) for direct Node
     runs (`node`, `node --test --test-isolation=none`) on macOS and Linux CI — blocks
     writes/reads outside the per-run sandbox and blocks `child_process` / `worker_threads`.
     Fails closed (`SandboxUnavailableError`) if `--permission` is requested but unavailable.
   - macOS `/usr/bin/sandbox-exec` (Seatbelt) wraps all runners (Node, Vitest, ESLint,
     tsc, lab commands) — enforces write confinement to the per-run sandbox, blocks
     network access (restricting Unix sockets to the per-run sandbox), and denies
     `file-read*` on `.env`/`.env.*`, `progress/`, `pilot/progress/`, `sources/`,
     `issues/`, `drills/data/`, `labs/_reference/` (across both the active checkout and
     git main checkout when running in a worktree) plus sensitive home directories
     (`~/.ssh`, `~/.aws`, `~/.gnupg`, `~/.config`, etc.). Fails closed on macOS if
     Seatbelt is unavailable.
   - Linux `unshare -r -n` wraps runners when unprivileged user namespaces are allowed
     by the kernel/AppArmor, removing network access without root. Where host policy
     blocks unprivileged user namespaces without root (e.g. AppArmor on Ubuntu CI),
     degradation is explicitly logged once to `sys.stderr` and recorded on `SandboxResult`.
4. Resource & output bounds: POSIX `resource.setrlimit` (`RLIMIT_CPU`, `RLIMIT_FSIZE`,
   `RLIMIT_NOFILE`, `RLIMIT_CORE`), V8 `--max-old-space-size`, wall-time timeout with
   process-group (`SIGTERM` -> `SIGKILL` sweep) cleanup including `SIGTERM`/`SIGINT`
   forwarding across `start_new_session=True`, and bounded stdout/stderr pipes.
"""

from __future__ import annotations

import atexit
import functools
import math
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import pwd as _pwd
except ImportError:  # pragma: no cover - Windows fallback
    _pwd = None  # type: ignore[assignment]

try:
    import resource as _resource
except ImportError:  # pragma: no cover - Windows fallback
    _resource = None  # type: ignore[assignment]

_REPO_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_TIMEOUT_SEC = 10.0
DEFAULT_REACT_TIMEOUT_SEC = 30.0
DEFAULT_TOOL_TIMEOUT_SEC = 30.0
DEFAULT_MAX_OUTPUT_BYTES = 1024 * 1024  # 1 MiB per stream
DEFAULT_MAX_FSIZE_BYTES = 16 * 1024 * 1024  # 16 MiB max file created inside sandbox
DEFAULT_MAX_OLD_SPACE_MB = 512
DEFAULT_NOFILE_LIMIT = 1024

_STAGE_SKIP_NAMES = frozenset(
    {
        "node_modules",
        ".git",
        ".venv",
        "__pycache__",
        ".canonical",
        "_reference",
        ".next",
    }
)
_SECRET_ENV_KEY_RE = re.compile(
    r"(TOKEN|SECRET|PASSWORD|PASSWD|API_KEY|PRIVATE_KEY|CREDENTIAL|AUTH|COOKIE|SESSION|NOTION_)",
    re.IGNORECASE,
)

_REPO_DENY_DIR_RELS = (
    "progress",
    "pilot/progress",
    "sources",
    "issues",
    "drills/data",
    "labs/_reference",
)
_HOME_DENY_DIR_RELS = (
    ".ssh",
    ".aws",
    ".gnupg",
    ".config",
    ".kube",
    ".docker",
    "Library/Keychains",
)
_HOME_DENY_FILE_RELS = (
    ".npmrc",
    ".netrc",
    ".pypirc",
    ".git-credentials",
)
_KNOWN_SINGLE_FILE_NAMES = frozenset(
    {
        ".env",
        ".npmrc",
        ".netrc",
        ".pypirc",
        ".git-credentials",
    }
)

_TERM_SIGNALS: frozenset[int] = frozenset({signal.SIGTERM, signal.SIGINT}) if os.name == "posix" else frozenset()
_ACTIVE_LOCK = threading.Lock()
_ACTIVE_CHILD_PGIDS: frozenset[int] = frozenset()
_ACTIVE_CHILDREN: tuple[tuple[int, subprocess.Popen[bytes]], ...] = ()
_SIGNAL_INSTALL_DEPTH = 0
_SAVED_SIG_HANDLERS: dict[int, Any] = {}
_WARN_LOCK = threading.Lock()
_WARNED_DEGRADATIONS: set[str] = set()


class SandboxUnavailableError(RuntimeError):
    """Raised when a required PRG isolation layer is unavailable (fail closed)."""


@dataclass(frozen=True)
class SandboxResult:
    """Bounded result of an isolated PRG subprocess invocation."""

    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False
    output_truncated: bool = False
    sandbox_mode: str = "rlimit-only"
    degraded_reasons: tuple[str, ...] = ()


def _warn_degraded(reason: str, message: str) -> None:
    """Emit a one-time visible warning to stderr when an OS layer cannot be enforced."""
    with _WARN_LOCK:
        if reason in _WARNED_DEGRADATIONS:
            return
        _WARNED_DEGRADATIONS.add(reason)
    try:
        sys.stderr.write(f"[sandbox] WARNING: {message}\n")
        sys.stderr.flush()
    except OSError:
        pass


def _resolve_node_bin() -> str:
    return shutil.which("node") or "node"


@functools.lru_cache(maxsize=1)
def _supports_node_permission() -> bool:
    """Return True if the active `node` binary supports `--permission` (Node 22.13+/24+)."""
    node_bin = _resolve_node_bin()
    try:
        proc = subprocess.run(
            [node_bin, "--permission", "-e", "process.exit(0)"],
            capture_output=True,
            text=True,
            timeout=5.0,
        )
        return proc.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


@functools.lru_cache(maxsize=1)
def _supports_macos_seatbelt() -> bool:
    """Return True on macOS when `/usr/bin/sandbox-exec` can apply a Seatbelt profile."""
    if sys.platform != "darwin":
        return False
    sbx = "/usr/bin/sandbox-exec"
    if not os.path.isfile(sbx):
        return False
    try:
        proc = subprocess.run(
            [sbx, "-p", "(version 1)(allow default)", "/usr/bin/true"],
            capture_output=True,
            text=True,
            timeout=5.0,
        )
        return proc.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


@functools.lru_cache(maxsize=1)
def _supports_linux_unshare_net() -> bool:
    """Return True on Linux when unprivileged `unshare -r -n` works without root."""
    if not sys.platform.startswith("linux"):
        return False
    unshare = shutil.which("unshare")
    if not unshare:
        return False
    try:
        proc = subprocess.run(
            [unshare, "-r", "-n", "--", "/bin/true"],
            capture_output=True,
            text=True,
            timeout=5.0,
        )
        return proc.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def sandbox_capabilities() -> dict[str, Any]:
    """Report which OS/runtime isolation layers are active on this host."""
    return {
        "platform": sys.platform,
        "node_permission": _supports_node_permission(),
        "macos_seatbelt": _supports_macos_seatbelt(),
        "linux_unshare_net": _supports_linux_unshare_net(),
        "posix_rlimit": _resource is not None and os.name == "posix",
    }


def _seatbelt_quote(path_str: str) -> str:
    if "\0" in path_str or "\n" in path_str or "\r" in path_str:
        raise ValueError(f"Invalid path for Seatbelt profile: {path_str!r}")
    escaped = path_str.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _resolve_git_main_checkout(repo_root: Path) -> Path | None:
    """When `repo_root` is a git worktree, return the main checkout root path."""
    git_marker = repo_root / ".git"
    if not git_marker.is_file():
        return None
    try:
        text = git_marker.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not text.startswith("gitdir:"):
        return None
    raw_gitdir = text.split(":", 1)[1].strip()
    if not raw_gitdir:
        return None
    gitdir = Path(os.path.abspath(os.path.join(str(repo_root), raw_gitdir)))
    commondir_file = gitdir / "commondir"
    if commondir_file.is_file():
        try:
            common_rel = commondir_file.read_text(encoding="utf-8").strip()
            if common_rel:
                common_git = Path(os.path.abspath(os.path.join(str(gitdir), common_rel))).resolve()
                return common_git.parent
        except OSError:
            pass
    if gitdir.parent.name == "worktrees":
        return gitdir.parent.parent.parent.resolve()
    return None


def _real_home_dirs() -> tuple[Path, ...]:
    """Return canonical real user home directory paths (including getpwuid when HOME is overridden)."""
    homes: list[Path] = []
    try:
        homes.append(Path.home().resolve())
    except (OSError, RuntimeError):
        pass
    if _pwd is not None and os.name == "posix":
        try:
            pw_dir = _pwd.getpwuid(os.getuid()).pw_dir
            if pw_dir:
                homes.append(Path(pw_dir).resolve())
        except (KeyError, OSError):
            pass
    return tuple(dict.fromkeys(homes))


def _default_deny_read_paths() -> tuple[Path, ...]:
    """Sensitive repository, worktree main-checkout, and user-home paths learner code must never read."""
    roots: list[Path] = [_REPO_ROOT.resolve()]
    env_root = os.environ.get("LEARNINGOS_ROOT")
    if env_root:
        try:
            roots.append(Path(env_root).resolve())
        except OSError:
            pass
    for root in list(roots):
        main_root = _resolve_git_main_checkout(root)
        if main_root is not None:
            roots.append(main_root)

    unique_roots = tuple(dict.fromkeys(roots))
    denied: list[Path] = []
    for root in unique_roots:
        # Always deny .env (even when not yet created) and any .env.* files.
        env_file = root / ".env"
        denied.append(Path(os.path.realpath(env_file)) if env_file.is_symlink() else env_file)
        try:
            for env_variant in sorted(root.glob(".env.*")):
                denied.append(env_variant)
                if env_variant.is_symlink():
                    denied.append(Path(os.path.realpath(env_variant)))
        except OSError:
            pass
        for rel in _REPO_DENY_DIR_RELS:
            cand = root / rel
            denied.append(cand)
            if cand.is_symlink():
                try:
                    denied.append(cand.resolve())
                except OSError:
                    pass

    for env_var in ("PROGRESS_DIR", "LEARNINGOS_SOURCES_DIR", "DRILLS_DATA_DIR"):
        raw = os.environ.get(env_var)
        if raw:
            try:
                denied.append(Path(raw).resolve())
            except OSError:
                pass

    for home_dir in _real_home_dirs():
        for rel in (*_HOME_DENY_DIR_RELS, *_HOME_DENY_FILE_RELS):
            denied.append(home_dir / rel)

    return tuple(dict.fromkeys(denied))


def _build_seatbelt_profile(
    sandbox_root: Path,
    *,
    deny_read_paths: Sequence[Path] = (),
    allow_network: bool = False,
) -> str:
    """Build a macOS Seatbelt profile confining writes to `sandbox_root`, blocking reads of secrets, and blocking network."""
    root_real = os.path.realpath(sandbox_root)
    lines = [
        "(version 1)",
        "(allow default)",
    ]
    if not allow_network:
        lines.append("(deny network*)")
        lines.append(f"(allow network* (local unix (subpath {_seatbelt_quote(root_real)})))")

    # Deny reads (data + metadata) of sensitive repo, worktree, and home paths outside sandbox_root.
    deny_rules: list[str] = []
    env_regex_parents: set[str] = set()
    for raw_path in deny_read_paths:
        real_p = os.path.realpath(raw_path)
        if real_p == root_real or real_p.startswith(root_real + os.sep) or root_real.startswith(real_p + os.sep):
            continue
        p_obj = Path(real_p)
        is_known_file = p_obj.name in _KNOWN_SINGLE_FILE_NAMES or p_obj.name.startswith(".env.")
        if p_obj.name == ".env":
            env_regex_parents.add(str(p_obj.parent))
        if os.path.isdir(real_p) or not is_known_file:
            deny_rules.append(f"  (subpath {_seatbelt_quote(real_p)})")
        else:
            deny_rules.append(f"  (literal {_seatbelt_quote(real_p)})")

    for parent in sorted(env_regex_parents):
        if parent == root_real or parent.startswith(root_real + os.sep):
            continue
        pattern = f"^{re.escape(parent)}/\\.env(\\..*)?$"
        deny_rules.append(f"  (regex #{_seatbelt_quote(pattern)})")

    if deny_rules:
        lines.append("(deny file-read*")
        lines.extend(dict.fromkeys(deny_rules))
        lines.append(")")

    lines.extend(
        [
            "(deny file-write*)",
            "(allow file-write*",
            f"  (subpath {_seatbelt_quote(root_real)})",
            '  (literal "/dev/null")',
            '  (literal "/dev/zero")',
            '  (literal "/dev/dtracehelper")',
            '  (literal "/dev/tty")',
            ")",
        ]
    )
    return "\n".join(lines) + "\n"


def build_sandbox_env(
    sandbox_root: Path,
    *,
    extra_env: Mapping[str, str] | None = None,
    extra_path_dirs: Sequence[Path | str] = (),
    max_old_space_mb: int | None = None,
) -> dict[str, str]:
    """Construct a minimal, secret-free environment confined to `sandbox_root`."""
    root_real = Path(os.path.realpath(sandbox_root))
    run_home = root_real / "home"
    run_tmp = root_real / "tmp"
    run_home.mkdir(parents=True, exist_ok=True)
    run_tmp.mkdir(parents=True, exist_ok=True)

    path_parts: list[str] = []
    for entry in extra_path_dirs:
        p = Path(entry)
        if p.is_dir():
            path_parts.append(str(p))

    node_which = shutil.which("node")
    if node_which:
        path_parts.append(str(Path(node_which).parent))
        resolved_node_parent = str(Path(node_which).resolve().parent)
        if resolved_node_parent not in path_parts:
            path_parts.append(resolved_node_parent)

    for std_dir in ("/usr/local/bin", "/usr/bin", "/bin", "/opt/homebrew/bin"):
        if os.path.isdir(std_dir) and std_dir not in path_parts:
            path_parts.append(std_dir)

    minimal_path = os.pathsep.join(dict.fromkeys(path_parts))
    locale = os.environ.get("LANG", "C.UTF-8")
    env: dict[str, str] = {
        "PATH": minimal_path,
        "HOME": str(run_home),
        "TMPDIR": str(run_tmp),
        "TEMP": str(run_tmp),
        "TMP": str(run_tmp),
        "XDG_CONFIG_HOME": str(run_home / ".config"),
        "XDG_CACHE_HOME": str(run_home / ".cache"),
        "XDG_DATA_HOME": str(run_home / ".local" / "share"),
        "LANG": locale,
        "LC_ALL": os.environ.get("LC_ALL") or locale,
        "TZ": os.environ.get("TZ", "UTC"),
        "CI": "1",
        "NO_COLOR": "1",
    }
    if max_old_space_mb is not None and max_old_space_mb > 0:
        env["NODE_OPTIONS"] = f"--max-old-space-size={int(max_old_space_mb)}"

    if extra_env:
        for key, value in extra_env.items():
            if _SECRET_ENV_KEY_RE.search(key):
                continue
            env[str(key)] = str(value)
    return env


def create_sandbox_dir(prefix: str = "prg_sandbox_") -> tempfile.TemporaryDirectory[str]:
    """Create a per-run sandbox temporary directory outside the repository."""
    return tempfile.TemporaryDirectory(prefix=prefix)


def _is_within(base: Path, target: Path) -> bool:
    try:
        target.relative_to(base)
        return True
    except ValueError:
        return False


SOURCE_SUFFIXES = frozenset({".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"})
JSON_SUFFIXES = frozenset({".json"})


def assert_safe_contained_path(
    path: Path | str,
    root: Path,
    *,
    expect_file: bool = True,
    label: str = "path",
    relative: bool = False,
    allow_missing: bool = False,
    suffixes: frozenset[str] | None = None,
) -> Path:
    """Resolve a regular file or directory without traversing symlinks under the trusted root.

    Pass relative=True for untrusted path strings, before joining or normalizing them.
    """
    raw = os.fspath(path)
    raw_path = Path(raw)
    if (
        not raw
        or any(char in raw for char in ("\\", "%", ":", "\0"))
        or ".." in raw.split("/")
        or (relative and (raw_path.is_absolute() or any(part in ("", ".") for part in raw.split("/"))))
    ):
        raise ValueError(f"Refusing unsafe {label}: {raw!r}")

    root_abs = Path(os.path.abspath(root))
    target_abs = root_abs / raw_path if relative else Path(os.path.abspath(raw_path))
    if not _is_within(root_abs, target_abs):
        raise ValueError(f"Refusing {label} outside allowed root {root_abs}: {target_abs}")
    parts = target_abs.relative_to(root_abs).parts
    if expect_file and (not parts or (suffixes is not None and target_abs.suffix not in suffixes)):
        raise ValueError(f"Unexpected file type for {label}: {target_abs}")
    if any(part.startswith(".env") for part in parts):
        raise ValueError(f"Refusing unsafe {label}: {target_abs}")

    resolved = root_abs
    missing = False
    for index, part in enumerate(("", *parts)):
        resolved /= part
        if missing:
            continue
        try:
            mode = resolved.lstat().st_mode
        except FileNotFoundError:
            if not allow_missing:
                raise
            missing = True
            continue
        if stat.S_ISLNK(mode):
            raise ValueError(f"Refusing symlink component in {label}: {resolved}")
        if expect_file and index == len(parts):
            if not stat.S_ISREG(mode):
                raise ValueError(f"Expected regular file for {label}: {resolved}")
        elif not stat.S_ISDIR(mode):
            raise ValueError(f"Expected directory for {label}: {resolved}")
        if index == 0:
            resolved = resolved.resolve(strict=True)
    return resolved


def stage_workspace_copy(
    src_dir: Path,
    dst_dir: Path,
    *,
    ignore_names: set[str] | frozenset[str] | None = None,
    allowed_root: Path | None = None,
) -> Path:
    """Copy a drill or lab workspace into `dst_dir`, rejecting symlinked roots and excluding secrets/symlinks."""
    src_path = Path(src_dir)
    if src_path.is_symlink():
        raise ValueError(f"Refusing to stage symlinked directory: {src_path}")
    if allowed_root is not None:
        src_real = assert_safe_contained_path(src_path, allowed_root, expect_file=False, label="workspace directory")
    else:
        if not src_path.is_dir():
            raise FileNotFoundError(f"Workspace directory not found: {src_path}")
        src_real = src_path.resolve(strict=True)

    dst_dir.mkdir(parents=True, exist_ok=True)
    skip = set(_STAGE_SKIP_NAMES)
    if ignore_names:
        skip.update(ignore_names)

    for root, dirs, files in os.walk(src_real, followlinks=False):
        root_path = Path(root)
        rel_root = root_path.relative_to(src_real)
        # Filter directories in-place so os.walk does not descend into skipped or symlinked dirs.
        kept_dirs: list[str] = []
        for dname in dirs:
            if dname in skip or dname.startswith(".env"):
                continue
            cand = root_path / dname
            if cand.is_symlink():
                continue
            kept_dirs.append(dname)
        dirs[:] = kept_dirs

        target_root = dst_dir / rel_root
        target_root.mkdir(parents=True, exist_ok=True)

        for fname in files:
            if fname in skip or fname.startswith(".env") or ".hidden." in fname:
                continue
            src_file = root_path / fname
            if src_file.is_symlink():
                continue
            if src_file.is_file():
                shutil.copy2(src_file, target_root / fname)
    return dst_dir


def stage_lab_copy(
    lab_dir: Path,
    src_dir: Path,
    test_files: Sequence[Path],
    dst_dir: Path,
    *,
    include_scripts: bool = False,
    allowed_test_roots: Sequence[Path] | None = None,
) -> tuple[Path, Path, list[Path]]:
    """Stage an isolated temp copy of a lab's `src`, `package.json`, and validated test files.

    Rejects symlinked `lab_dir`, `src_dir`, `scripts/`, or `test_files`, and verifies every
    test file stays within `allowed_test_roots` (defaulting to `lab_dir / 'tests'` when
    present, else `lab_dir`).

    Returns `(work_dir, staged_src_dir, staged_test_files)`.
    """
    lab_path = Path(lab_dir)
    src_path = Path(src_dir)
    if lab_path.is_symlink():
        raise ValueError(f"Refusing symlinked lab directory: {lab_path}")
    if src_path.is_symlink():
        raise ValueError(f"Refusing symlinked lab src directory: {src_path}")

    dst_dir.mkdir(parents=True, exist_ok=True)
    staged_src = dst_dir / "src"
    stage_workspace_copy(src_path, staged_src)

    # Copy only package.json needed by Node/TS/Vitest (e.g. `"type": "module"`).
    # Never copy learner-writable eslint.config.*, vitest.config.*, or tsconfig.json.
    has_pkg_json = False
    for meta_root in (lab_path, src_path.parent):
        if meta_root.is_symlink():
            continue
        cand = meta_root / "package.json"
        dst_meta = dst_dir / "package.json"
        if cand.is_file() and not cand.is_symlink() and not dst_meta.exists():
            shutil.copy2(cand, dst_meta)
            has_pkg_json = True

    if not has_pkg_json and any(Path(f).suffix in (".ts", ".tsx", ".mjs") for f in test_files):
        (dst_dir / "package.json").write_text('{"type": "module"}\n', encoding="utf-8")

    if include_scripts:
        scripts_dir = lab_path / "scripts"
        if scripts_dir.is_symlink():
            raise ValueError(f"Refusing symlinked lab scripts directory: {scripts_dir}")
        if scripts_dir.is_dir():
            stage_workspace_copy(scripts_dir, dst_dir / "scripts", allowed_root=lab_path)

    if allowed_test_roots is not None:
        eff_test_roots = tuple(Path(r) for r in allowed_test_roots)
    else:
        tests_sub = lab_path / "tests"
        if tests_sub.is_symlink():
            raise ValueError(f"Refusing symlinked lab tests directory: {tests_sub}")
        eff_test_roots = (tests_sub,) if tests_sub.is_dir() else (lab_path,)

    staged_tests_dir = dst_dir / "tests"
    staged_tests_dir.mkdir(parents=True, exist_ok=True)
    staged_tests: list[Path] = []
    used_names: set[str] = set()
    for tf in test_files:
        tf_path = Path(tf)
        if tf_path.is_symlink():
            raise ValueError(f"Refusing symlinked test file: {tf_path}")
        tf_real: Path | None = None
        last_err: Exception | None = None
        for root_cand in eff_test_roots:
            try:
                tf_real = assert_safe_contained_path(tf_path, root_cand, expect_file=True, label="test file")
                break
            except (ValueError, FileNotFoundError) as exc:
                last_err = exc
        if tf_real is None:
            raise ValueError(
                f"Refusing test file outside allowed test root(s) {[str(r) for r in eff_test_roots]}: {tf_path}"
            ) from last_err

        name = tf_real.name
        if name in used_names:
            stem = tf_real.stem
            suffix = tf_real.suffix
            idx = 2
            while f"{stem}_{idx}{suffix}" in used_names:
                idx += 1
            name = f"{stem}_{idx}{suffix}"
        used_names.add(name)
        dst_test = staged_tests_dir / name
        shutil.copy2(tf_real, dst_test)
        staged_tests.append(dst_test)

    return dst_dir, staged_src, staged_tests


def _make_rlimit_preexec(
    *,
    cpu_limit_sec: int,
    max_fsize_bytes: int,
    nofile_limit: int,
):
    """Build a POSIX `preexec_fn` applying resource limits inside the child process."""
    if _resource is None or os.name != "posix":
        return None

    def _apply_limits() -> None:
        def _cap(limit_name: str, soft: int, hard: int) -> None:
            res_id = getattr(_resource, limit_name, None)
            if res_id is None:
                return
            try:
                cur_soft, cur_hard = _resource.getrlimit(res_id)
                if cur_hard != _resource.RLIM_INFINITY:
                    soft = min(soft, cur_hard)
                    hard = min(hard, cur_hard)
                if soft > hard:
                    soft = hard
                # For RLIMIT_NOFILE, never raise above existing soft limit.
                if limit_name == "RLIMIT_NOFILE" and cur_soft != _resource.RLIM_INFINITY and soft > cur_soft:
                    soft = cur_soft
                _resource.setrlimit(res_id, (soft, hard))
            except (ValueError, OSError):
                pass

        if cpu_limit_sec > 0:
            _cap("RLIMIT_CPU", cpu_limit_sec, cpu_limit_sec + 1)
        if max_fsize_bytes > 0:
            _cap("RLIMIT_FSIZE", max_fsize_bytes, max_fsize_bytes)
        if nofile_limit > 0:
            _cap("RLIMIT_NOFILE", nofile_limit, nofile_limit)
        _cap("RLIMIT_CORE", 0, 0)

    return _apply_limits


def _make_child_preexec(
    *,
    cpu_limit_sec: int,
    max_fsize_bytes: int,
    nofile_limit: int,
    restore_sigmask: set[int] | frozenset[int] | None = None,
):
    """Build a POSIX `preexec_fn` restoring the child's signal mask before exec and applying rlimits."""
    if os.name != "posix":
        return None
    rlimit_fn = _make_rlimit_preexec(
        cpu_limit_sec=cpu_limit_sec,
        max_fsize_bytes=max_fsize_bytes,
        nofile_limit=nofile_limit,
    )
    can_restore_mask = restore_sigmask is not None and hasattr(signal, "pthread_sigmask")
    if rlimit_fn is None and not can_restore_mask:
        return None
    saved_mask = frozenset(restore_sigmask) if restore_sigmask is not None else None

    def _child_setup() -> None:
        # Restore the pre-block signal mask before exec so children never inherit
        # SIGTERM/SIGINT blocked from the parent's spawn/registration critical section.
        if can_restore_mask and saved_mask is not None:
            signal.pthread_sigmask(signal.SIG_SETMASK, saved_mask)
        if rlimit_fn is not None:
            rlimit_fn()

    return _child_setup


def _sweep_process_group(pgid: int, *, proc: subprocess.Popen[bytes] | None = None) -> None:
    """Send SIGKILL to `pgid` until no processes remain in the group (ignoring ESRCH)."""
    if os.name != "posix" or pgid <= 0:
        return
    for attempt in range(25):
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            return
        except OSError:
            return
        if proc is not None:
            try:
                proc.poll()
            except OSError:
                pass
        try:
            os.killpg(pgid, 0)
        except ProcessLookupError:
            return
        except OSError:
            return
        if attempt < 24:
            time.sleep(0.01)


def _kill_process_group(proc: subprocess.Popen[bytes], *, pgid: int | None = None) -> None:
    """Terminate the child and sweep its entire POSIX process group with SIGKILL."""
    target_pgid = pgid if pgid is not None else proc.pid
    if os.name == "posix":
        if proc.poll() is None:
            try:
                os.killpg(target_pgid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            except OSError:
                try:
                    proc.terminate()
                except OSError:
                    pass
            try:
                proc.wait(timeout=0.25)
            except subprocess.TimeoutExpired:
                pass
        # Always sweep the group with SIGKILL even if the leader already exited,
        # so SIGTERM-ignoring descendants in target_pgid can never survive.
        _sweep_process_group(target_pgid, proc=proc)
        if proc.poll() is None:
            try:
                proc.kill()
            except OSError:
                pass
    else:  # pragma: no cover - non-POSIX fallback
        if proc.poll() is None:
            try:
                proc.kill()
            except OSError:
                pass
    try:
        proc.wait(timeout=2.0)
    except subprocess.TimeoutExpired:
        pass


def _register_active_child(pgid: int, proc: subprocess.Popen[bytes]) -> None:
    """Register an active child process group (serialized writers, lock-free readers)."""
    global _ACTIVE_CHILD_PGIDS, _ACTIVE_CHILDREN
    with _ACTIVE_LOCK:
        _ACTIVE_CHILD_PGIDS = _ACTIVE_CHILD_PGIDS | {pgid}
        _ACTIVE_CHILDREN = (*_ACTIVE_CHILDREN, (pgid, proc))


def _unregister_active_child(pgid: int, proc: subprocess.Popen[bytes]) -> None:
    """Unregister a finished child process group without locking signal-handler readers."""
    global _ACTIVE_CHILD_PGIDS, _ACTIVE_CHILDREN
    with _ACTIVE_LOCK:
        remaining = tuple((p, pr) for p, pr in _ACTIVE_CHILDREN if not (p == pgid and pr is proc))
        _ACTIVE_CHILDREN = remaining
        remaining_pgids = {p for p, _ in remaining}
        if pgid not in remaining_pgids:
            _ACTIVE_CHILD_PGIDS = _ACTIVE_CHILD_PGIDS - {pgid}


def _cleanup_all_active_pgids() -> None:
    """Sweep all active child process groups without acquiring `_ACTIVE_LOCK`.

    Copy-on-write snapshots guarantee a POSIX signal handler or `atexit` hook can
    never deadlock by re-entering a held lock on the main thread.
    """
    children = _ACTIVE_CHILDREN
    pgids = _ACTIVE_CHILD_PGIDS
    proc_by_pgid: dict[int, subprocess.Popen[bytes]] = {}
    for pgid, proc in children:
        proc_by_pgid[pgid] = proc
    for pgid in pgids | proc_by_pgid.keys():
        _sweep_process_group(pgid, proc=proc_by_pgid.get(pgid))


def _handle_termination_signal(signum: int, _frame: Any) -> None:
    _cleanup_all_active_pgids()
    raise SystemExit(128 + signum)


def _acquire_termination_handlers() -> bool:
    """Install SIGTERM/SIGINT handlers on the main thread (ref-counted for nesting).

    Non-main-thread policy: CPython forbids `signal.signal()` off the main thread, so
    worker threads do not alter process signal handlers or masks; they still register
    their `start_new_session` children for lock-free sweeps and reap them in `finally`.
    """
    global _SIGNAL_INSTALL_DEPTH
    if os.name != "posix" or threading.current_thread() is not threading.main_thread():
        return False
    if _SIGNAL_INSTALL_DEPTH == 0:
        saved: dict[int, Any] = {}
        try:
            for sig in (signal.SIGTERM, signal.SIGINT):
                saved[sig] = signal.signal(sig, _handle_termination_signal)
        except (ValueError, OSError):
            for sig, prev in saved.items():
                try:
                    signal.signal(sig, prev)
                except (ValueError, OSError):
                    pass
            return False
        _SAVED_SIG_HANDLERS.clear()
        _SAVED_SIG_HANDLERS.update(saved)
    _SIGNAL_INSTALL_DEPTH += 1
    return True


def _release_termination_handlers() -> None:
    """Release a termination handler reference and restore prior handlers at depth 0."""
    global _SIGNAL_INSTALL_DEPTH
    if _SIGNAL_INSTALL_DEPTH <= 0:
        return
    _SIGNAL_INSTALL_DEPTH -= 1
    if _SIGNAL_INSTALL_DEPTH == 0:
        for sig, prev in list(_SAVED_SIG_HANDLERS.items()):
            try:
                signal.signal(sig, prev)
            except (ValueError, OSError):
                pass
        _SAVED_SIG_HANDLERS.clear()


atexit.register(_cleanup_all_active_pgids)


def _inject_node_permission_args(
    cmd: Sequence[str],
    *,
    sandbox_root: Path,
    extra_read_paths: Sequence[Path | str] = (),
    max_old_space_mb: int | None = None,
) -> list[str]:
    """Inject Node 24 `--permission` and heap limit flags into a `node ...` command."""
    cmd_list = list(cmd)
    if not cmd_list:
        return cmd_list

    root_real = os.path.realpath(sandbox_root)
    read_paths: list[str] = [root_real]
    for extra in extra_read_paths:
        real_extra = os.path.realpath(extra)
        if real_extra not in read_paths:
            read_paths.append(real_extra)

    injected: list[str] = ["--permission"]
    for rp in read_paths:
        injected.append(f"--allow-fs-read={rp}")
    injected.append(f"--allow-fs-write={root_real}")
    if max_old_space_mb is not None and max_old_space_mb > 0:
        injected.append(f"--max-old-space-size={int(max_old_space_mb)}")

    tail = cmd_list[1:]
    # `node --test` spawns child processes unless `--test-isolation=none` is enabled.
    if "--test" in tail and not any(arg.startswith("--test-isolation") for arg in tail):
        idx = tail.index("--test")
        tail = [*tail[: idx + 1], "--test-isolation=none", *tail[idx + 1 :]]

    return [cmd_list[0], *injected, *tail]


def run_isolated(
    cmd: Sequence[str],
    *,
    cwd: Path | str,
    sandbox_root: Path | str,
    timeout_sec: float = DEFAULT_TIMEOUT_SEC,
    env_extra: Mapping[str, str] | None = None,
    extra_path_dirs: Sequence[Path | str] = (),
    extra_read_paths: Sequence[Path | str] = (),
    use_node_permission: bool = False,
    max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
    max_old_space_mb: int | None = DEFAULT_MAX_OLD_SPACE_MB,
    max_fsize_bytes: int = DEFAULT_MAX_FSIZE_BYTES,
    cpu_limit_sec: int | None = None,
    nofile_limit: int = DEFAULT_NOFILE_LIMIT,
    deny_read_paths: Sequence[Path] | None = None,
    allow_network: bool = False,
    kill_on_output_limit: bool = True,
) -> SandboxResult:
    """Execute a command inside the shared least-privilege PRG sandbox."""
    sbx_root = Path(os.path.realpath(sandbox_root))
    cwd_path = Path(os.path.realpath(cwd))
    sbx_root.mkdir(parents=True, exist_ok=True)

    final_cmd = [str(part) for part in cmd]
    modes: list[str] = []
    degraded: list[str] = []

    is_direct_node = bool(final_cmd) and Path(final_cmd[0]).name == "node"
    env_old_space = max_old_space_mb
    if use_node_permission:
        if not is_direct_node:
            raise SandboxUnavailableError(
                f"Node --permission requested for non-node command: {final_cmd[:1]!r}; refusing unconfined execution."
            )
        if not _supports_node_permission():
            raise SandboxUnavailableError(
                "Node --permission is unavailable (requires Node 22.13+/24+); refusing unconfined execution."
            )
        final_cmd = _inject_node_permission_args(
            final_cmd,
            sandbox_root=sbx_root,
            extra_read_paths=extra_read_paths,
            max_old_space_mb=max_old_space_mb,
        )
        env_old_space = None  # Passed via CLI flag; no NODE_OPTIONS needed.
        modes.append("node-permission")
    elif is_direct_node and max_old_space_mb is not None and max_old_space_mb > 0:
        final_cmd = [final_cmd[0], f"--max-old-space-size={int(max_old_space_mb)}", *final_cmd[1:]]
        env_old_space = None

    if sys.platform == "darwin":
        if not _supports_macos_seatbelt():
            raise SandboxUnavailableError(
                "macOS Seatbelt (/usr/bin/sandbox-exec) is unavailable; refusing unconfined PRG execution."
            )
        denied = _default_deny_read_paths() if deny_read_paths is None else tuple(deny_read_paths)
        profile = _build_seatbelt_profile(sbx_root, deny_read_paths=denied, allow_network=allow_network)
        final_cmd = ["/usr/bin/sandbox-exec", "-p", profile, *final_cmd]
        modes.append("seatbelt")
    else:
        if not allow_network:
            if _supports_linux_unshare_net():
                unshare_bin = shutil.which("unshare") or "unshare"
                final_cmd = [unshare_bin, "-r", "-n", "--", *final_cmd]
                modes.append("linux-unshare-net")
            else:
                degraded.append("os-network-isolation-unavailable")
                _warn_degraded(
                    "os-network-isolation-unavailable",
                    "OS network confinement (unshare -r -n) is unavailable on this host; running without OS network blocking.",
                )
        if not use_node_permission:
            degraded.append("os-fs-confinement-unavailable")
            _warn_degraded(
                "os-fs-confinement-unavailable",
                "OS filesystem confinement is unavailable for non-node-permission tools on this host; "
                "ephemeral temp-copy cwd, scrubbed env, and POSIX rlimits remain active.",
            )

    env = build_sandbox_env(
        sbx_root,
        extra_env=env_extra,
        extra_path_dirs=extra_path_dirs,
        max_old_space_mb=env_old_space,
    )

    eff_cpu = cpu_limit_sec if cpu_limit_sec is not None else max(int(math.ceil(timeout_sec * 2)), 10)
    is_posix = os.name == "posix"
    if _resource is not None and is_posix:
        modes.append("rlimit")

    is_main_thread = threading.current_thread() is threading.main_thread()
    can_mask_signals = is_posix and is_main_thread and hasattr(signal, "pthread_sigmask")
    can_install_signals = is_posix and is_main_thread

    stdout_buf = bytearray()
    stderr_buf = bytearray()
    output_exceeded = threading.Event()
    cap = max(int(max_output_bytes), 1024)

    def _drain(stream, buf: bytearray) -> None:
        if stream is None:
            return
        try:
            while True:
                chunk = stream.read(8192)
                if not chunk:
                    break
                remaining = cap - len(buf)
                if remaining > 0:
                    buf.extend(chunk[:remaining])
                if len(chunk) > remaining:
                    output_exceeded.set()
                    if kill_on_output_limit:
                        break
        except (OSError, ValueError):
            pass
        finally:
            try:
                stream.close()
            except OSError:
                pass

    prev_sigmask: set[int] | None = None
    installed_signals = False
    proc: subprocess.Popen[bytes] | None = None
    pgid: int | None = None
    registered = False
    t_out: threading.Thread | None = None
    t_err: threading.Thread | None = None
    timed_out = False

    try:
        # Block SIGTERM/SIGINT and install termination handlers BEFORE spawning the child so
        # a signal arriving at the spawn/registration boundary cannot hit SIG_DFL or observe
        # an unregistered child process group. The child's preexec_fn restores `prev_sigmask`
        # before exec so the child never inherits blocked termination signals.
        if can_mask_signals:
            prev_sigmask = signal.pthread_sigmask(signal.SIG_BLOCK, _TERM_SIGNALS)
        if can_install_signals:
            installed_signals = _acquire_termination_handlers()

        preexec = _make_child_preexec(
            cpu_limit_sec=eff_cpu,
            max_fsize_bytes=max_fsize_bytes,
            nofile_limit=nofile_limit,
            restore_sigmask=prev_sigmask,
        )

        proc = subprocess.Popen(
            final_cmd,
            cwd=str(cwd_path),
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=is_posix,
            preexec_fn=preexec,
        )
        pgid = proc.pid
        _register_active_child(pgid, proc)
        registered = True

        # Unmask now that the handler is active and `pgid` is registered; any SIGTERM/SIGINT
        # queued during spawn/registration fires our handler right here and unwinds cleanly.
        if prev_sigmask is not None:
            signal.pthread_sigmask(signal.SIG_SETMASK, prev_sigmask)

        t_out = threading.Thread(target=_drain, args=(proc.stdout, stdout_buf), daemon=True)
        t_err = threading.Thread(target=_drain, args=(proc.stderr, stderr_buf), daemon=True)
        t_out.start()
        t_err.start()

        deadline = time.monotonic() + max(float(timeout_sec), 0.1)
        while True:
            if output_exceeded.is_set() and kill_on_output_limit:
                _kill_process_group(proc, pgid=pgid)
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out = True
                _kill_process_group(proc, pgid=pgid)
                break
            try:
                proc.wait(timeout=min(remaining, 0.05))
                break
            except subprocess.TimeoutExpired:
                if output_exceeded.is_set() and kill_on_output_limit:
                    _kill_process_group(proc, pgid=pgid)
                    break
    finally:
        if prev_sigmask is not None:
            try:
                signal.pthread_sigmask(signal.SIG_BLOCK, _TERM_SIGNALS)
            except OSError:
                pass
        try:
            if proc is not None and pgid is not None:
                if proc.poll() is None:
                    _kill_process_group(proc, pgid=pgid)
                else:
                    _sweep_process_group(pgid, proc=proc)
                if proc.poll() is None:
                    try:
                        proc.wait(timeout=2.0)
                    except subprocess.TimeoutExpired:
                        pass
            if registered and pgid is not None and proc is not None:
                _unregister_active_child(pgid, proc)
            if installed_signals:
                _release_termination_handlers()
            if proc is not None:
                if t_out is None and proc.stdout is not None:
                    try:
                        proc.stdout.close()
                    except OSError:
                        pass
                if t_err is None and proc.stderr is not None:
                    try:
                        proc.stderr.close()
                    except OSError:
                        pass
            if t_out is not None:
                t_out.join(timeout=1.0)
            if t_err is not None:
                t_err.join(timeout=1.0)
        finally:
            if prev_sigmask is not None:
                try:
                    signal.pthread_sigmask(signal.SIG_SETMASK, prev_sigmask)
                except OSError:
                    pass

    returncode = proc.returncode if proc is not None and proc.returncode is not None else -9
    return SandboxResult(
        returncode=returncode,
        stdout=stdout_buf.decode("utf-8", errors="replace"),
        stderr=stderr_buf.decode("utf-8", errors="replace"),
        timed_out=timed_out,
        output_truncated=output_exceeded.is_set(),
        sandbox_mode="+".join(modes) if modes else "env-only",
        degraded_reasons=tuple(degraded),
    )


def run_node_isolated(
    args: Sequence[str],
    *,
    cwd: Path | str,
    sandbox_root: Path | str,
    timeout_sec: float = DEFAULT_TIMEOUT_SEC,
    env_extra: Mapping[str, str] | None = None,
    extra_read_paths: Sequence[Path | str] = (),
    max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
    max_old_space_mb: int | None = DEFAULT_MAX_OLD_SPACE_MB,
    max_fsize_bytes: int = DEFAULT_MAX_FSIZE_BYTES,
    cpu_limit_sec: int | None = None,
) -> SandboxResult:
    """Run `node <args...>` inside the shared least-privilege PRG sandbox with Node `--permission`."""
    node_bin = _resolve_node_bin()
    eff_cpu = cpu_limit_sec if cpu_limit_sec is not None else max(int(math.ceil(timeout_sec)) + 2, 6)
    return run_isolated(
        [node_bin, *[str(a) for a in args]],
        cwd=cwd,
        sandbox_root=sandbox_root,
        timeout_sec=timeout_sec,
        env_extra=env_extra,
        extra_read_paths=extra_read_paths,
        use_node_permission=True,
        max_output_bytes=max_output_bytes,
        max_old_space_mb=max_old_space_mb,
        max_fsize_bytes=max_fsize_bytes,
        cpu_limit_sec=eff_cpu,
    )


def run_vitest_isolated(
    test_files: Sequence[Path | str],
    *,
    cwd: Path | str,
    sandbox_root: Path | str,
    config_path: Path | str,
    report_path: Path | str,
    reporter: str = "junit",
    timeout_sec: float = DEFAULT_REACT_TIMEOUT_SEC,
    env_extra: Mapping[str, str] | None = None,
    tools_lint_dir: Path | None = None,
    extra_read_paths: Sequence[Path | str] = (),
    max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
    max_old_space_mb: int | None = DEFAULT_MAX_OLD_SPACE_MB,
) -> SandboxResult:
    """Run Vitest in jsdom inside the shared least-privilege PRG sandbox."""
    tools_dir = (tools_lint_dir or (_REPO_ROOT / "tools" / "lint")).resolve()
    vitest_bin = tools_dir / "node_modules" / ".bin" / "vitest"
    cmd = [
        str(vitest_bin),
        "run",
        *[str(f) for f in test_files],
        "--config",
        str(config_path),
        "--environment",
        "jsdom",
        f"--reporter={reporter}",
        f"--outputFile={report_path}",
    ]
    return run_isolated(
        cmd,
        cwd=cwd,
        sandbox_root=sandbox_root,
        timeout_sec=timeout_sec,
        env_extra=env_extra,
        extra_path_dirs=(tools_dir / "node_modules" / ".bin",),
        extra_read_paths=(tools_dir / "node_modules", *extra_read_paths),
        use_node_permission=False,
        max_output_bytes=max_output_bytes,
        max_old_space_mb=max_old_space_mb,
        cpu_limit_sec=max(int(math.ceil(timeout_sec * 3)), 20),
    )
