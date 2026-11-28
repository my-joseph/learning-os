"""Deterministic regressions for PRG sandbox SIGTERM spawn/registration and lock-reentrancy races."""

from __future__ import annotations

import json
import os
import select
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

import pytest

import code_engine.sandbox as sbx_mod
from code_engine.sandbox import create_sandbox_dir, run_isolated

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _parse_proc_stat_state(raw: str) -> tuple[str, str]:
    """Parse Linux `/proc/<pid>/stat` into ('zombie' | 'live' | 'unknown', detail)."""
    rparen = raw.rfind(")")
    if rparen != -1:
        fields = raw[rparen + 1 :].split()
        if fields:
            state_char = fields[0]
            if state_char in ("Z", "X", "x"):
                return ("zombie", f"proc:{state_char}")
            return ("live", f"proc:{state_char}")
    return ("unknown", f"proc-unparsed:{raw[:64]}")


def inspect_pid_state(pid: int) -> tuple[str, str]:
    """Classify a POSIX PID as ('absent' | 'zombie' | 'live' | 'unknown', raw_detail).

    `os.kill(pid, 0)` succeeds for zombies as well as live processes; this helper
    reads `/proc/<pid>/stat` on Linux or `ps -o stat= -p <pid>` on macOS/BSD to
    distinguish a dead zombie from a live orphan.
    """
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return ("absent", "ESRCH")
    except PermissionError:
        return ("live", "EPERM")

    proc_stat = Path(f"/proc/{pid}/stat")
    if proc_stat.parent.is_dir():
        try:
            raw = proc_stat.read_text(encoding="utf-8", errors="replace").strip()
        except (FileNotFoundError, ProcessLookupError):
            return ("absent", "proc-vanished")
        except OSError as exc:
            return ("unknown", f"proc-error:{exc}")
        return _parse_proc_stat_state(raw)

    try:
        res = subprocess.run(
            ["ps", "-o", "stat=", "-p", str(pid)],
            capture_output=True,
            text=True,
            timeout=2.0,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return ("unknown", f"ps-error:{exc}")
    stat_str = res.stdout.strip()
    if res.returncode != 0 or not stat_str:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return ("absent", "ps-empty-ESRCH")
        except PermissionError:
            return ("live", "ps-empty-EPERM")
        return ("unknown", f"ps-rc={res.returncode}")
    if stat_str[0] in ("Z", "X"):
        return ("zombie", f"ps:{stat_str}")
    return ("live", f"ps:{stat_str}")


def wait_for_pid_absent(pid: int, *, timeout_sec: float = 2.0) -> tuple[str, str]:
    """Poll `inspect_pid_state` until the PID is absent or `timeout_sec` expires."""
    deadline = time.monotonic() + timeout_sec
    state, detail = inspect_pid_state(pid)
    while state != "absent" and time.monotonic() < deadline:
        time.sleep(0.05)
        state, detail = inspect_pid_state(pid)
    return (state, detail)


def _readline_with_timeout(stream: Any, timeout_sec: float) -> str:
    """Read one line from a pipe without blocking forever."""
    ready, _, _ = select.select([stream], [], [], timeout_sec)
    if not ready:
        return ""
    return stream.readline()


def _cleanup_stray_pid(pid: int | None) -> None:
    if pid is None or pid <= 0:
        return
    try:
        os.killpg(pid, signal.SIGKILL)
    except OSError:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass


@pytest.mark.skipif(os.name != "posix", reason="POSIX signal/process-state semantics only")
def test_inspect_pid_state_distinguishes_live_zombie_and_absent() -> None:
    # 1. Linux /proc/<pid>/stat parser handles spaces and nested parentheses in comm.
    assert _parse_proc_stat_state("1234 (sh (child)) Z 1 2 3") == ("zombie", "proc:Z")
    assert _parse_proc_stat_state("1234 (dead proc) X 1 2 3") == ("zombie", "proc:X")
    assert _parse_proc_stat_state("1234 (sleep) S 1 2 3") == ("live", "proc:S")
    assert _parse_proc_stat_state("1234 (worker) R 1 2 3") == ("live", "proc:R")

    # 2. Exited-but-unreaped child is classified as zombie, then absent after wait().
    short_proc = subprocess.Popen([sys.executable, "-c", "pass"])
    try:
        deadline = time.monotonic() + 3.0
        state, detail = inspect_pid_state(short_proc.pid)
        while state == "live" and time.monotonic() < deadline:
            time.sleep(0.02)
            state, detail = inspect_pid_state(short_proc.pid)
        assert state == "zombie", f"Expected zombie before wait(), got {(state, detail)}"
    finally:
        short_proc.wait(timeout=3.0)
    assert inspect_pid_state(short_proc.pid)[0] == "absent"

    # 3. Sleeping child is classified as live until killed and reaped.
    live_proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        state, detail = inspect_pid_state(live_proc.pid)
        assert state == "live", f"Expected live sleeping process, got {(state, detail)}"
    finally:
        live_proc.kill()
        live_proc.wait(timeout=3.0)
    assert inspect_pid_state(live_proc.pid)[0] == "absent"


@pytest.mark.skipif(os.name != "posix", reason="POSIX SIGTERM spawn/registration semantics only")
def test_sigterm_during_popen_registration_boundary_cleans_up_child_and_sandbox() -> None:
    """Force SIGTERM after Popen spawns a new-session child but BEFORE Popen returns to run_isolated."""
    driver = """
import json, os, sys, time
from pathlib import Path
import code_engine.sandbox as sbx_mod
from code_engine.sandbox import create_sandbox_dir, run_isolated

orig_popen = sbx_mod.subprocess.Popen
pid_file_holder = []
sbx_holder = []

# Pre-warm cached capability probes so racing_popen only wraps run_isolated's child Popen.
sbx_mod.sandbox_capabilities()

def racing_popen(*args, **kwargs):
    proc = orig_popen(*args, **kwargs)
    pid_file = pid_file_holder[0]
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        if pid_file.is_file():
            text = pid_file.read_text(encoding="utf-8").strip()
            if text:
                break
        time.sleep(0.01)
    # Child is now live in its own session (ignoring SIGTERM), and run_isolated has NOT YET
    # returned from Popen or registered proc.pid. Pause on stdin so the test can deliver
    # SIGTERM deterministically right at the spawn/registration boundary.
    sys.stdout.write(json.dumps({"child_pid": proc.pid, "sbx": str(sbx_holder[0])}) + "\\n")
    sys.stdout.flush()
    sys.stdin.readline()
    return proc

sbx_mod.subprocess.Popen = racing_popen

with create_sandbox_dir(prefix="prg_race_spawn_") as sbx_str:
    sbx = Path(sbx_str)
    work = sbx / "work"
    work.mkdir()
    child_pid_file = work / "child.pid"
    tmp_pid_file = work / "child.pid.tmp"
    pid_file_holder.append(child_pid_file)
    sbx_holder.append(sbx)
    cmd = (
        f"trap '' TERM; "
        f"echo $$ > {str(tmp_pid_file)!r} && mv {str(tmp_pid_file)!r} {str(child_pid_file)!r}; "
        f"exec sleep 60"
    )
    run_isolated(
        ["/bin/sh", "-c", cmd],
        cwd=work,
        sandbox_root=sbx,
        timeout_sec=30.0,
        use_node_permission=False,
    )
"""
    parent = subprocess.Popen(
        [sys.executable, "-c", driver],
        cwd=str(_REPO_ROOT),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    child_pid: int | None = None
    sbx_path: Path | None = None
    try:
        assert parent.stdout is not None and parent.stdin is not None
        ready_line = _readline_with_timeout(parent.stdout, timeout_sec=10.0)
        assert ready_line, (
            f"Driver failed to reach spawn boundary (rc={parent.poll()}, "
            f"stderr={parent.stderr.read() if parent.stderr else ''!r})"
        )
        info = json.loads(ready_line)
        child_pid = int(info["child_pid"])
        sbx_path = Path(info["sbx"])

        # Child must genuinely be alive before we signal the driver.
        pre_state, pre_detail = inspect_pid_state(child_pid)
        assert pre_state == "live", f"Expected live child at spawn boundary, got {(pre_state, pre_detail)}"

        # Deliver external SIGTERM to the driver's process group while paused inside Popen.
        os.killpg(parent.pid, signal.SIGTERM)

        # Release the Popen boundary barrier (ignore BrokenPipeError if an unfixed driver already died).
        try:
            parent.stdin.write("resume\n")
            parent.stdin.flush()
            parent.stdin.close()
        except OSError:
            pass

        driver_rc = parent.wait(timeout=5.0)
        child_state, child_detail = wait_for_pid_absent(child_pid, timeout_sec=2.0)
        sbx_exists = sbx_path.exists()
        stderr_out = parent.stderr.read() if parent.stderr else ""

        assert child_state != "live", (
            f"Spawn/registration race left LIVE ORPHAN child PID {child_pid} "
            f"(state={child_state}/{child_detail}, driver_rc={driver_rc}, "
            f"sbx_exists={sbx_exists}, stderr={stderr_out!r})"
        )
        assert child_state != "zombie", (
            f"Spawn/registration race left unreaped ZOMBIE child PID {child_pid} "
            f"(state={child_state}/{child_detail}, driver_rc={driver_rc}, "
            f"sbx_exists={sbx_exists}, stderr={stderr_out!r})"
        )
        assert child_state == "absent", (
            f"Unexpected child state {(child_state, child_detail)} for PID {child_pid} "
            f"(driver_rc={driver_rc}, sbx_exists={sbx_exists})"
        )
        assert driver_rc == 128 + signal.SIGTERM, (
            f"Expected driver exit {128 + signal.SIGTERM} from termination handler, "
            f"got {driver_rc} (sbx_exists={sbx_exists}, stderr={stderr_out!r})"
        )
        assert not sbx_exists, (
            f"Sandbox temp dir {sbx_path} leaked after SIGTERM at spawn boundary "
            f"(driver_rc={driver_rc}, child_state={child_state}/{child_detail})"
        )
    finally:
        if parent.poll() is None:
            _cleanup_stray_pid(parent.pid)
            try:
                parent.wait(timeout=3.0)
            except subprocess.TimeoutExpired:
                pass
        _cleanup_stray_pid(child_pid)
        if sbx_path is not None and sbx_path.exists():
            shutil.rmtree(sbx_path, ignore_errors=True)


@pytest.mark.skipif(os.name != "posix", reason="POSIX signal/lock re-entrancy semantics only")
def test_sigterm_while_active_lock_held_does_not_deadlock_and_cleans_up() -> None:
    """Delivering SIGTERM while the main thread holds `_ACTIVE_LOCK` must not deadlock."""
    driver = """
import json, os, signal, sys, time
from pathlib import Path
import code_engine.sandbox as sbx_mod
from code_engine.sandbox import create_sandbox_dir, run_isolated

orig_popen = sbx_mod.subprocess.Popen
pid_file_holder = []
sbx_holder = []

# Pre-warm cached capability probes so hooking_popen only wraps run_isolated's child Popen.
sbx_mod.sandbox_capabilities()

def hooking_popen(*args, **kwargs):
    proc = orig_popen(*args, **kwargs)
    orig_wait = proc.wait
    triggered = False

    def wait_with_locked_sigterm(*wargs, **wkwargs):
        nonlocal triggered
        if not triggered:
            triggered = True
            pid_file = pid_file_holder[0]
            deadline = time.monotonic() + 5.0
            while time.monotonic() < deadline:
                if pid_file.is_file() and pid_file.read_text(encoding="utf-8").strip():
                    break
                time.sleep(0.01)
            sys.stdout.write(json.dumps({"child_pid": proc.pid, "sbx": str(sbx_holder[0])}) + "\\n")
            sys.stdout.flush()
            with sbx_mod._ACTIVE_LOCK:
                os.kill(os.getpid(), signal.SIGTERM)
        return orig_wait(*wargs, **wkwargs)

    proc.wait = wait_with_locked_sigterm
    return proc

sbx_mod.subprocess.Popen = hooking_popen

with create_sandbox_dir(prefix="prg_race_lock_") as sbx_str:
    sbx = Path(sbx_str)
    work = sbx / "work"
    work.mkdir()
    child_pid_file = work / "child.pid"
    tmp_pid_file = work / "child.pid.tmp"
    pid_file_holder.append(child_pid_file)
    sbx_holder.append(sbx)
    cmd = (
        f"trap '' TERM; "
        f"echo $$ > {str(tmp_pid_file)!r} && mv {str(tmp_pid_file)!r} {str(child_pid_file)!r}; "
        f"exec sleep 60"
    )
    run_isolated(
        ["/bin/sh", "-c", cmd],
        cwd=work,
        sandbox_root=sbx,
        timeout_sec=30.0,
        use_node_permission=False,
    )
"""
    parent = subprocess.Popen(
        [sys.executable, "-c", driver],
        cwd=str(_REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    child_pid: int | None = None
    sbx_path: Path | None = None
    try:
        assert parent.stdout is not None
        ready_line = _readline_with_timeout(parent.stdout, timeout_sec=10.0)
        assert ready_line, (
            f"Driver failed to start child (rc={parent.poll()}, "
            f"stderr={parent.stderr.read() if parent.stderr else ''!r})"
        )
        info = json.loads(ready_line)
        child_pid = int(info["child_pid"])
        sbx_path = Path(info["sbx"])

        try:
            driver_rc = parent.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            pytest.fail(
                f"Driver deadlocked on SIGTERM while holding _ACTIVE_LOCK "
                f"(child_pid={child_pid}, child_state={inspect_pid_state(child_pid)})"
            )

        child_state, child_detail = wait_for_pid_absent(child_pid, timeout_sec=2.0)
        sbx_exists = sbx_path.exists()
        assert child_state != "live", (
            f"Child PID {child_pid} survived as LIVE ORPHAN after locked SIGTERM "
            f"(state={child_state}/{child_detail}, driver_rc={driver_rc}, sbx_exists={sbx_exists})"
        )
        assert child_state != "zombie", (
            f"Child PID {child_pid} remained ZOMBIE after locked SIGTERM "
            f"(state={child_state}/{child_detail}, driver_rc={driver_rc}, sbx_exists={sbx_exists})"
        )
        assert child_state == "absent"
        assert driver_rc == 128 + signal.SIGTERM
        assert not sbx_exists, f"Sandbox temp dir {sbx_path} leaked after locked SIGTERM"
    finally:
        if parent.poll() is None:
            _cleanup_stray_pid(parent.pid)
            try:
                parent.wait(timeout=3.0)
            except subprocess.TimeoutExpired:
                pass
        _cleanup_stray_pid(child_pid)
        if sbx_path is not None and sbx_path.exists():
            shutil.rmtree(sbx_path, ignore_errors=True)


@pytest.mark.skipif(os.name != "posix", reason="POSIX signal mask semantics only")
def test_child_inherits_unblocked_signal_mask_and_parent_state_restored() -> None:
    """Child must inherit unblocked SIGTERM/SIGINT, and parent handlers/mask must be restored."""
    orig_sigterm = signal.getsignal(signal.SIGTERM)
    orig_sigint = signal.getsignal(signal.SIGINT)
    orig_mask = signal.pthread_sigmask(signal.SIG_BLOCK, set())

    with create_sandbox_dir(prefix="prg_sigmask_") as sbx_str:
        sbx = Path(sbx_str)
        work = sbx / "work"
        work.mkdir()

        # 1. Inspect the child's actual kernel blocked signal mask.
        res = run_isolated(
            [
                sys.executable,
                "-c",
                "import json, signal; print(json.dumps(sorted(int(s) for s in signal.pthread_sigmask(signal.SIG_BLOCK, set()))))",
            ],
            cwd=work,
            sandbox_root=sbx,
            timeout_sec=10.0,
            use_node_permission=False,
        )
        assert res.returncode == 0, res.stderr
        child_blocked = set(json.loads(res.stdout.strip()))
        assert int(signal.SIGTERM) not in child_blocked, f"Child inherited blocked SIGTERM: {child_blocked}"
        assert int(signal.SIGINT) not in child_blocked, f"Child inherited blocked SIGINT: {child_blocked}"

        # 2. A child sending SIGTERM to itself must terminate by SIGTERM (not block/ignore it).
        term_res = run_isolated(
            ["/bin/sh", "-c", "kill -TERM $$"],
            cwd=work,
            sandbox_root=sbx,
            timeout_sec=5.0,
            use_node_permission=False,
        )
        assert term_res.returncode in (-signal.SIGTERM, 128 + signal.SIGTERM), term_res

        # 3. Failed Popen must still restore parent signal handlers and signal mask.
        sbx_mod.sandbox_capabilities()
        orig_popen = sbx_mod.subprocess.Popen

        def failing_popen(*args: Any, **kwargs: Any) -> Any:
            raise OSError("synthetic spawn failure")

        sbx_mod.subprocess.Popen = failing_popen  # type: ignore[assignment]
        try:
            with pytest.raises(OSError, match="synthetic spawn failure"):
                run_isolated(
                    ["/bin/true"],
                    cwd=work,
                    sandbox_root=sbx,
                    timeout_sec=5.0,
                    use_node_permission=False,
                )
        finally:
            sbx_mod.subprocess.Popen = orig_popen  # type: ignore[assignment]

    assert signal.getsignal(signal.SIGTERM) == orig_sigterm
    assert signal.getsignal(signal.SIGINT) == orig_sigint
    assert signal.pthread_sigmask(signal.SIG_BLOCK, set()) == orig_mask


@pytest.mark.skipif(os.name != "posix", reason="POSIX thread/signal semantics only")
def test_non_main_thread_run_isolated_cleans_up_without_touching_main_handlers() -> None:
    """Non-main threads must not mutate process handlers/masks yet must still kill and reap children."""
    orig_sigterm = signal.getsignal(signal.SIGTERM)
    orig_mask = signal.pthread_sigmask(signal.SIG_BLOCK, set())

    def sentinel_handler(signum: int, frame: Any) -> None:
        pass

    signal.signal(signal.SIGTERM, sentinel_handler)
    errors: list[BaseException] = []
    child_pid_box: list[int] = []

    try:
        with create_sandbox_dir(prefix="prg_thread_") as sbx_str:
            sbx = Path(sbx_str)
            work = sbx / "work"
            work.mkdir()
            pid_file = work / "thread_child.pid"
            tmp_pid = work / "thread_child.pid.tmp"

            def worker() -> None:
                try:
                    cmd = (
                        f"trap '' TERM; "
                        f"echo $$ > {str(tmp_pid)!r} && mv {str(tmp_pid)!r} {str(pid_file)!r}; "
                        f"exec sleep 30"
                    )
                    res = run_isolated(
                        ["/bin/sh", "-c", cmd],
                        cwd=work,
                        sandbox_root=sbx,
                        timeout_sec=0.4,
                        use_node_permission=False,
                    )
                    assert res.timed_out is True
                    if pid_file.is_file() and pid_file.read_text(encoding="utf-8").strip():
                        child_pid_box.append(int(pid_file.read_text(encoding="utf-8").strip()))
                except BaseException as exc:  # noqa: BLE001
                    errors.append(exc)

            t = threading.Thread(target=worker)
            t.start()
            t.join(timeout=10.0)
            assert not t.is_alive(), "Worker thread hung inside run_isolated"
            assert not errors, f"Worker thread failed: {errors!r}"
            assert child_pid_box, "Worker child did not write its PID before timeout"
            state, detail = wait_for_pid_absent(child_pid_box[0], timeout_sec=2.0)
            assert state != "live", f"Worker child survived as LIVE ORPHAN: {(state, detail)}"
            assert state != "zombie", f"Worker child remained ZOMBIE: {(state, detail)}"
            assert state == "absent"
            assert not sbx_mod._ACTIVE_CHILD_PGIDS
            assert signal.getsignal(signal.SIGTERM) is sentinel_handler
            assert signal.pthread_sigmask(signal.SIG_BLOCK, set()) == orig_mask
    finally:
        signal.signal(signal.SIGTERM, orig_sigterm)
        if child_pid_box:
            _cleanup_stray_pid(child_pid_box[0])
