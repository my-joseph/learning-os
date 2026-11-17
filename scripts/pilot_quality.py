"""Isolated collection, validation, and answer-free summary CLI for pilot exercise-quality runs.

Implements the minimum data contract in `docs/pilot_quality_protocol.md` without
modifying drill content, graders, UI, Notion, or learner progress.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "pilot-quality-v1"

MODES = ("retrospective", "natural_attempt", "fault_injection", "transfer_probe")
ACTOR_TYPES = ("ai", "human", "unknown")
EXPOSURE_LEVELS = ("none", "visible_only", "solution", "unknown")
CONTAMINATION_STATES = ("no", "yes", "unknown")
CLOSURE_STATUSES = ("open", "closed", "quarantined")
OUTCOMES = ("correct", "incorrect", "partial", "invalid_input", "blocked", "not_attempted")
CONFIDENCE_LEVELS = ("low", "medium", "high")
ERROR_ORIGINS = ("spontaneous", "planted", "tooling", "ambiguous", "unknown")
REVIEW_VERDICTS = ("PASS", "REVISE", "blocked", "not_reviewed")
CAUGHT_BY_VALUES = ("test", "lint", "typecheck", "reviewer", "none", "unknown")
DISPUTE_OUTCOMES = ("upheld", "rejected", "partial", "pending", "not_applicable")
EXPLAIN_STATUSES = ("supported", "partial", "unsupported", "not_observed")
TIME_SOURCES = ("measured", "estimated", "unavailable")
HELP_EVENT_KINDS = ("hint", "setup", "solution", "review_feedback", "other")
DIMENSIONS = tuple(
    "objective_alignment reasoning_and_cues transfer misconception_diagnosis context "
    "difficulty_and_load feedback sequence_and_redundancy assessment_validity learner_agency".split()
)
DIMENSION_STATUSES = ("supported", "concern", "unknown", "not_applicable")
DECISIONS = ("keep", "revise", "replace", "investigate")

PROTECTED_REL_DIRS = ("progress", "drills/workspace")
DISALLOWED_REF_PREFIXES = (
    "progress/",
    "drills/workspace/",
    "pilot/progress/",
    "pilot/workspace/",
    "pilot/labs/",
    ".git/",
    ".env",
)
LEARNER_FORBIDDEN_TOKENS = (
    "vault",
    "solution",
    "hidden",
    "planted",
    "plant_manifest",
    "answer",
    "secret",
    "labs/_reference",
)

SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
ISO_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
SAFE_MATERIAL_TAG_RE = re.compile(r"^(unit|chapter|topic|notion|page|resource):[A-Za-z0-9_.-]+$")
ISSUE_ID_RE = re.compile(r"^ISS-[A-Za-z0-9_.-]+$")

FORBIDDEN_EXACT_KEYS = frozenset(
    "accepted steps rawsubmission submissiontext userinput usercode explanationtext feedbacktext "
    "prompt prompts startercode trapvalue trapmutant trapderivation trapgivens checkpointhint "
    "display plaintext progressdir workspacedir rundir snapshotpath reporoot".split()
)
FORBIDDEN_KEY_SUBSTRINGS = (
    "answer",
    "solution",
    "hiddentest",
    "visibletest",
    "writepath",
    "outputpath",
    "targetpath",
    "destpath",
    "secret",
    "token",
    "password",
)

RUN_DOC_KEYS = frozenset(
    "schema_version run_id mode started_at ended_at source_commit content_sha256 drill_path unit_id drill_id "
    "sample_reason actor_type model_id effort role session_id allowed_materials prior_exposure contamination "
    "missing_reasons isolation_check".split()
)
RUN_OPTIONAL_KEYS = frozenset("closure_status closed_observed_at quarantine".split())
RUN_ALLOWED_KEYS = RUN_DOC_KEYS | RUN_OPTIONAL_KEYS
ISOLATION_CHECK_REQUIRED_KEYS = frozenset("run_progress_dir run_workspace_dir protected_snapshot".split())
ISOLATION_CHECK_ALLOWED_KEYS = ISOLATION_CHECK_REQUIRED_KEYS | frozenset(("end_protected_snapshot",))
QUARANTINE_KEYS = frozenset("reason quarantined_at evidence_ref evidence_sha256 isolation_mismatches".split())
RUN_NULLABLE_FIELDS = ("model_id", "effort", "session_id", "sample_reason", "source_commit", "ended_at")
CORE_ITEM_KEYS = frozenset(
    "schema_version run_id record_id recorded_at mode problem_id attempt_index supersedes_record_id objective_ref "
    "prerequisite_refs form code_type demand_tags sequence_index first_submission_ref first_submission_snapshot "
    "first_submission_sha256 outcome confidence_before_feedback error_origin blocker evidence_refs planted "
    "plant_manifest_ref solution_exposure help_events feedback_ref revision_ref review_verdict caught_by "
    "dispute_ref dispute_outcome explain_status issue_refs active_ms tool_wait_ms elapsed_ms time_source "
    "dimensions unique_contribution comparison_ids decision decision_reason probe missing_reasons "
    "captured_digests additional".split()
)
SINGLE_REF_FIELDS = ("first_submission_ref", "plant_manifest_ref", "feedback_ref", "revision_ref", "dispute_ref")
PROBE_KEYS = frozenset(
    "probe_id parent_problem_id changed_dimension unchanged_objective delay_ms exposure outcome explanation_status".split()
)
DIMENSION_ENTRY_KEYS = frozenset(("status", "evidence_refs", "reason", "confidence"))
HELP_EVENT_KEYS = frozenset(("kind", "observed_at", "ref"))
ITEM_MISSINGNESS_TRACKED = (
    "planted",
    "confidence_before_feedback",
    "error_origin",
    "help_events",
    "active_ms",
    "dimensions",
    "decision",
)


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _is_forbidden_key(key: str) -> bool:
    norm = key.lower().replace("_", "").replace("-", "")
    return norm in FORBIDDEN_EXACT_KEYS or any(sub in norm for sub in FORBIDDEN_KEY_SUBSTRINGS)


def _check_no_forbidden_keys(obj: Any, path: str) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if not isinstance(k, str):
                raise ValueError(f"Non-string key at {path}")
            if _is_forbidden_key(k):
                raise ValueError(f"Forbidden answer/solution/write-path key rejected: {path}.{k}")
            _check_no_forbidden_keys(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            _check_no_forbidden_keys(item, f"{path}[{idx}]")


def find_repo_root(start: str | os.PathLike[str] | None = None) -> Path:
    """Find the repository root from `start` or cwd using `id_map.json` or `drills/data`."""
    current = Path(start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "id_map.json").is_file() or (candidate / "drills" / "data").is_dir():
            return candidate
    return current


def validate_safe_id(value: Any, label: str) -> str:
    """Validate an identifier with strict anti-traversal rules."""
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    if ".." in value or "/" in value or "\\" in value or "\x00" in value:
        raise ValueError(f"Unsafe {label}: traversal or path separator rejected")
    if not SAFE_ID_RE.match(value):
        raise ValueError(f"Invalid {label}: {value!r}")
    return value


def _parse_iso_utc(value: Any, field: str) -> dt.datetime:
    if not isinstance(value, str) or not ISO_UTC_RE.match(value):
        raise ValueError(f"{field} must be a UTC ISO-8601 timestamp ending in 'Z', got {value!r}")
    try:
        return dt.datetime.fromisoformat(value).astimezone(dt.timezone.utc)
    except ValueError as exc:
        raise ValueError(f"{field} is not a valid calendar UTC timestamp: {value!r}") from exc


def _ensure_contained(base: Path, target: Path) -> Path:
    if base.is_symlink():
        raise ValueError(f"Symlink rejected at {base}")
    try:
        rel = target.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"Path {target} escapes base {base}") from exc
    cur = base
    for part in rel.parts:
        cur = cur / part
        if cur.is_symlink():
            raise ValueError(f"Symlink component rejected: {cur}")
    target_resolved = target.resolve(strict=False)
    if not target_resolved.is_relative_to(base.resolve(strict=False)):
        raise ValueError(f"Resolved path escapes {base}: {target}")
    return target_resolved


def quality_root(repo_root: Path) -> Path:
    """Return `<repo_root>/pilot/quality` after verifying no symlink components."""
    root = repo_root.resolve(strict=True)
    if repo_root.is_symlink():
        raise ValueError("Repository root cannot be a symlink")
    return _ensure_contained(root, root / "pilot" / "quality")


def safe_run_dir(repo_root: Path, run_id: str, *, must_exist: bool = False) -> Path:
    """Return validated `<repo_root>/pilot/quality/<run_id>` directory."""
    safe_id = validate_safe_id(run_id, "run_id")
    qroot = quality_root(repo_root)
    run_dir = qroot / safe_id
    _ensure_contained(qroot, run_dir)
    if must_exist and not run_dir.is_dir():
        raise FileNotFoundError(f"Run does not exist: {safe_id}")
    return run_dir


def _split_ref_fragment(ref: str) -> tuple[str, str | None]:
    return ref.split("#", 1) if "#" in ref else (ref, None)


def _is_disallowed_ref(rel_posix: str) -> bool:
    norm = rel_posix.lstrip("./")
    return (
        norm == ".env"
        or norm.startswith(".env.")
        or any(norm == p.rstrip("/") or norm.startswith(p) for p in DISALLOWED_REF_PREFIXES)
    )


def resolve_safe_ref(repo_root: Path, run_dir: Path, ref: str, *, must_exist: bool = True) -> tuple[Path, str]:
    """Resolve a reference local to `run_dir` or repo-relative evidence safely."""
    if not isinstance(ref, str) or not ref.strip():
        raise ValueError("Reference must be a non-empty string")
    if "\x00" in ref or "\\" in ref or ref.startswith(("~", "/")) or re.match(r"^[A-Za-z]:", ref):
        raise ValueError(f"Unsafe reference path rejected: {ref!r}")
    file_part, frag = _split_ref_fragment(ref.strip())
    if not file_part or any(part in ("..", "") for part in Path(file_part).parts):
        raise ValueError(f"Invalid or traversal reference path: {ref!r}")

    root = repo_root.resolve(strict=True)
    run_rel_prefix = run_dir.relative_to(root).as_posix() + "/"
    if file_part.startswith(run_rel_prefix):
        candidate = _ensure_contained(run_dir, root / file_part)
    elif (run_dir / file_part).exists() or (run_dir / file_part).is_symlink():
        candidate = _ensure_contained(run_dir, run_dir / file_part)
    else:
        candidate = _ensure_contained(root, root / file_part)

    rel_posix = candidate.relative_to(root).as_posix()
    if _is_disallowed_ref(rel_posix):
        raise ValueError(f"Reference targets protected or restricted path: {rel_posix}")
    if must_exist:
        if candidate.is_symlink():
            raise ValueError(f"Symlink reference rejected: {rel_posix}")
        if not candidate.is_file():
            raise FileNotFoundError(f"Referenced evidence file does not exist: {rel_posix}")
    return candidate, (f"{rel_posix}#{frag}" if frag is not None else rel_posix)


def _resolve_or_capture_ref(repo_root: Path, run_dir: Path, raw_ref: Any, capture_into: dict[str, str] | None) -> str:
    fpath, canon = resolve_safe_ref(repo_root, run_dir, raw_ref, must_exist=True)
    if capture_into is not None:
        capture_into[canon] = _sha256_file(fpath)
    return canon


def _scaffold_symlink_target(root: Path, target_dir: Path, rel_root: str, link_path: Path) -> str | None:
    """Return resolved target if `link_path` is an expected `materialize_drill_workspace` symlink."""
    if rel_root != "drills/workspace":
        return None
    parts = link_path.relative_to(target_dir).parts
    if len(parts) != 2:
        return None
    link_name = parts[1]
    repo_base = Path(__file__).resolve().parents[1]
    if link_name == "code_engine":
        allowed = (root / "code_engine", repo_base / "code_engine")
    elif link_name == "node_modules":
        allowed = (root / "tools" / "lint" / "node_modules", repo_base / "tools" / "lint" / "node_modules")
    else:
        return None
    try:
        resolved = link_path.resolve(strict=True)
    except OSError:
        return None
    allowed_resolved = {cand.resolve(strict=False) for cand in allowed}
    return str(resolved) if resolved in allowed_resolved else None


def snapshot_protected_paths(repo_root: Path) -> dict[str, Any]:
    """Capture read-only SHA-256 content hashes of protected learner directories."""
    root = repo_root.resolve(strict=True)
    roots_data: dict[str, Any] = {}
    for rel in PROTECTED_REL_DIRS:
        target = root / rel
        entry: dict[str, Any] = {
            "exists": False,
            "is_symlink": False,
            "symlinks_found": [],
            "scaffold_symlinks": {},
            "file_count": 0,
            "tree_sha256": _sha256_bytes(b""),
            "files": {},
        }
        cur = root
        for part in Path(rel).parts:
            cur = cur / part
            if cur.is_symlink():
                entry.update({"exists": True, "is_symlink": True})
                break
        if entry["is_symlink"] or not target.exists():
            roots_data[rel] = entry
            continue
        if not target.is_dir():
            entry.update({"exists": True, "symlinks_found": [f"{rel} (not a directory)"]})
            roots_data[rel] = entry
            continue

        entry["exists"] = True
        files: dict[str, str] = {}
        symlinks_found: list[str] = []
        scaffold_symlinks: dict[str, str] = {}
        for dirpath, dirnames, filenames in os.walk(target, followlinks=False):
            dp = Path(dirpath)
            kept: list[str] = []
            for dname in sorted(dirnames):
                dpath = dp / dname
                if dpath.is_symlink():
                    rpath = dpath.relative_to(root).as_posix()
                    scaffold_target = _scaffold_symlink_target(root, target, rel, dpath)
                    if scaffold_target is not None:
                        scaffold_symlinks[rpath] = scaffold_target
                    else:
                        symlinks_found.append(rpath)
                else:
                    kept.append(dname)
            dirnames[:] = kept
            for fname in sorted(filenames):
                fpath = dp / fname
                rpath = fpath.relative_to(root).as_posix()
                if fpath.is_symlink():
                    scaffold_target = _scaffold_symlink_target(root, target, rel, fpath)
                    if scaffold_target is not None:
                        scaffold_symlinks[rpath] = scaffold_target
                    else:
                        symlinks_found.append(rpath)
                elif fpath.is_file():
                    files[rpath] = _sha256_file(fpath)

        lines = "\n".join(f"{k}:{files[k]}" for k in sorted(files))
        entry.update(
            {
                "files": files,
                "file_count": len(files),
                "symlinks_found": sorted(symlinks_found),
                "scaffold_symlinks": dict(sorted(scaffold_symlinks.items())),
                "tree_sha256": _sha256_bytes(lines.encode("utf-8")),
            }
        )
        roots_data[rel] = entry
    return {"captured_at": _utc_now(), "roots": roots_data}


def compare_protected_snapshots(recorded: dict[str, Any], current: dict[str, Any]) -> list[str]:
    """Compare a recorded protected snapshot against the current filesystem state."""
    rec_roots, cur_roots = recorded.get("roots"), current.get("roots")
    if not isinstance(rec_roots, dict) or not isinstance(cur_roots, dict):
        return ["Invalid protected_snapshot structure"]
    mismatches: list[str] = []
    for rel in PROTECTED_REL_DIRS:
        rec, cur = rec_roots.get(rel), cur_roots.get(rel)
        if not isinstance(rec, dict) or not isinstance(cur, dict):
            mismatches.append(f"{rel}: missing snapshot entry")
            continue
        if cur.get("is_symlink") or rec.get("is_symlink"):
            mismatches.append(f"{rel}: protected path is a symlink")
        if rec.get("symlinks_found"):
            mismatches.append(f"{rel}: symlinks found inside recorded snapshot: {rec['symlinks_found']}")
        if cur.get("symlinks_found"):
            mismatches.append(f"{rel}: symlinks found inside protected path: {cur['symlinks_found']}")
        rec_scaf = rec.get("scaffold_symlinks") or {}
        cur_scaf = cur.get("scaffold_symlinks") or {}
        if rec_scaf != cur_scaf:
            mismatches.append(
                f"{rel}: workspace scaffold symlinks changed "
                f"(added={sorted(set(cur_scaf) - set(rec_scaf))}, "
                f"removed={sorted(set(rec_scaf) - set(cur_scaf))}, "
                f"changed={sorted(k for k in set(rec_scaf) & set(cur_scaf) if rec_scaf[k] != cur_scaf[k])})"
            )
        if rec.get("exists") != cur.get("exists"):
            mismatches.append(f"{rel}: existence changed ({rec.get('exists')} -> {cur.get('exists')})")
        if rec.get("tree_sha256") != cur.get("tree_sha256"):
            rf, cf = rec.get("files") or {}, cur.get("files") or {}
            mismatches.append(
                f"{rel}: protected content hash mismatch (added={sorted(set(cf) - set(rf))}, "
                f"removed={sorted(set(rf) - set(cf))}, changed={sorted(k for k in set(rf) & set(cf) if rf[k] != cf[k])})"
            )
    return mismatches


def locate_drill(repo_root: Path, drill_id: str, unit_id: str | None = None) -> tuple[Path, dict[str, Any], str]:
    """Locate `drill_id` under `drills/data/`, verify safety, and return `(path, doc, sha256)`."""
    safe_drill_id = validate_safe_id(drill_id, "drill_id")
    root = repo_root.resolve(strict=True)
    data_root = _ensure_contained(root, root / "drills" / "data")
    if not data_root.is_dir():
        raise FileNotFoundError("drills/data directory does not exist")

    candidates: list[Path] = []
    if unit_id:
        direct = _ensure_contained(
            data_root, data_root / validate_safe_id(unit_id, "unit_id") / f"{safe_drill_id}.json"
        )
        if direct.is_file():
            candidates = [direct]
    if not candidates:
        candidates = [
            p
            for p in sorted(data_root.glob(f"*/{safe_drill_id}.json"))
            if _ensure_contained(data_root, p) and p.is_file()
        ]
    if len(candidates) != 1:
        raise FileNotFoundError(f"Expected 1 drill file for {safe_drill_id}; found {len(candidates)}")

    drill_path = candidates[0]
    raw_bytes = drill_path.read_bytes()
    doc = json.loads(raw_bytes.decode("utf-8"))
    if not isinstance(doc, dict):
        raise ValueError(f"Drill file is not a JSON object: {drill_path}")
    doc_drill_id = doc.get("drillId") or doc.get("id")
    if doc_drill_id and doc_drill_id != safe_drill_id:
        raise ValueError(f"Drill ID mismatch in {drill_path}: expected {safe_drill_id}, got {doc_drill_id}")
    if unit_id and doc.get("unitCode") and doc.get("unitCode") != unit_id:
        raise ValueError(f"Unit ID mismatch in {drill_path}: expected {unit_id}, got {doc.get('unitCode')}")
    return drill_path, doc, _sha256_bytes(raw_bytes)


def _detect_git_commit(repo_root: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo_root, capture_output=True, text=True, timeout=5, check=False
        )
        return proc.stdout.strip() or None if proc.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def _check_enum(val: Any, allowed: tuple[str, ...], field: str, errors: list[str], *, allow_none: bool = False) -> None:
    if not (val is None and allow_none) and (not isinstance(val, str) or val not in allowed):
        errors.append(f"{field} must be one of {allowed}" + (" or null" if allow_none else "") + f", got {val!r}")


def _check_non_empty_str(val: Any, field: str, errors: list[str], *, allow_none: bool = False) -> None:
    if not (val is None and allow_none) and (not isinstance(val, str) or not val.strip()):
        errors.append(f"{field} must be a non-empty string" + (" or null" if allow_none else ""))


def _check_str_list(val: Any, field: str, errors: list[str], *, allow_none: bool = False) -> None:
    if not (val is None and allow_none) and (
        not isinstance(val, list) or not all(isinstance(x, str) and x.strip() for x in val)
    ):
        errors.append(f"{field} must be a list of non-empty strings" + (" or null" if allow_none else ""))


def _check_non_neg_int(val: Any, field: str, errors: list[str], *, min_val: int = 0, allow_none: bool = True) -> None:
    if not (val is None and allow_none) and (isinstance(val, bool) or not isinstance(val, int) or val < min_val):
        errors.append(f"{field} must be an integer >= {min_val}" + (" or null" if allow_none else ""))


def _check_keyset(
    obj: dict[str, Any],
    allowed: frozenset[str],
    label: str,
    errors: list[str],
    *,
    required: frozenset[str] | None = None,
) -> None:
    req = allowed if required is None else required
    for k in sorted(set(obj.keys()) - allowed):
        errors.append(
            f"Forbidden answer/solution/write-path key rejected: {label}.{k}"
            if _is_forbidden_key(k)
            else f"{label} unsupported key: {k}"
        )
    missing = sorted(req - set(obj.keys()))
    if missing:
        errors.append(f"{label} missing required keys: {missing}")


def _check_id_safe(val: Any, label: str, errors: list[str]) -> str | None:
    try:
        return validate_safe_id(val, label)
    except ValueError as exc:
        errors.append(str(exc))
        return None


def _validate_missing_reasons(
    obj: dict[str, Any], nullable_fields: tuple[str, ...], raw: Any, label: str, errors: list[str]
) -> dict[str, str]:
    reasons: dict[str, str] = {}
    if isinstance(raw, dict):
        try:
            _check_no_forbidden_keys(raw, f"{label}.missing_reasons")
        except ValueError as exc:
            errors.append(str(exc))
        for k, v in raw.items():
            if not isinstance(k, str) or not isinstance(v, str) or not v.strip():
                errors.append(f"{label}.missing_reasons[{k!r}] must be a non-empty string")
            else:
                reasons[k] = v.strip()
    elif raw is not None:
        errors.append(f"{label}.missing_reasons must be an object mapping field names to reasons")
    for field in nullable_fields:
        if obj.get(field) is None and not reasons.get(field):
            errors.append(f"Explicit missing_reasons[{field!r}] is required when {field} is null")
    return reasons


def _validate_allowed_materials(
    repo_root: Path, run_dir: Path, materials: Any, mode: Any, role: Any, errors: list[str]
) -> list[str]:
    if not isinstance(materials, list):
        errors.append("allowed_materials must be a list")
        return []
    learner_restricted = role == "learner" and mode != "retrospective"
    validated: list[str] = []
    for item in materials:
        if not isinstance(item, str) or not item.strip():
            errors.append("Each allowed_materials entry must be a non-empty string")
            continue
        entry = item.strip()
        if learner_restricted and any(tok in entry.lower() for tok in LEARNER_FORBIDDEN_TOKENS):
            errors.append(f"Disallowed material for learner {mode} mode: {entry!r}")
            continue
        if SAFE_MATERIAL_TAG_RE.match(entry):
            validated.append(entry)
            continue
        try:
            _, canon = resolve_safe_ref(repo_root, run_dir, entry, must_exist=False)
        except ValueError as exc:
            errors.append(f"Invalid allowed_materials entry {entry!r}: {exc}")
            continue
        fpart = _split_ref_fragment(canon)[0]
        if learner_restricted and (
            fpart == "drills/data"
            or fpart.startswith(("drills/data/", "labs/_reference/"))
            or any(p.startswith(".") for p in Path(fpart).parts)
        ):
            errors.append(f"Disallowed canonical drill or hidden material for learner {mode} mode: {entry!r}")
            continue
        validated.append(canon)
    return validated


def _validate_snapshot_struct(snap: Any, label: str, errors: list[str]) -> bool:
    if not isinstance(snap, dict):
        errors.append(f"{label} must be an object")
        return False
    ok = True
    try:
        _parse_iso_utc(snap.get("captured_at"), f"{label}.captured_at")
    except ValueError as exc:
        errors.append(str(exc))
        ok = False
    roots = snap.get("roots")
    if not isinstance(roots, dict):
        errors.append(f"{label}.roots must be an object")
        return False
    for rel in PROTECTED_REL_DIRS:
        entry = roots.get(rel)
        if not isinstance(entry, dict):
            errors.append(f"{label}.roots[{rel!r}] missing snapshot entry")
            ok = False
    return ok


def _validate_quarantine_doc(qdoc: Any, errors: list[str]) -> None:
    if not isinstance(qdoc, dict):
        errors.append("run.quarantine must be an object")
        return
    _check_keyset(qdoc, QUARANTINE_KEYS, "run.quarantine", errors)
    reason = qdoc.get("reason")
    _check_non_empty_str(reason, "run.quarantine.reason", errors)
    if isinstance(reason, str) and (len(reason.strip()) > 500 or "```" in reason):
        errors.append("run.quarantine.reason exceeds safe short metadata limits")
    try:
        _parse_iso_utc(qdoc.get("quarantined_at"), "run.quarantine.quarantined_at")
    except ValueError as exc:
        errors.append(str(exc))
    _check_str_list(qdoc.get("isolation_mismatches"), "run.quarantine.isolation_mismatches", errors)
    ev_ref, ev_sha = qdoc.get("evidence_ref"), qdoc.get("evidence_sha256")
    if ev_ref is None:
        if ev_sha is not None:
            errors.append("run.quarantine.evidence_sha256 must be null when evidence_ref is null")
    else:
        _check_non_empty_str(ev_ref, "run.quarantine.evidence_ref", errors)
        if not isinstance(ev_sha, str) or not SHA256_HEX_RE.match(ev_sha):
            errors.append("run.quarantine.evidence_sha256 must be a 64-char hex digest")


def _validate_run_doc(
    repo_root: Path, run_dir: Path, run_doc: dict[str, Any], *, expected_run_id: str | None = None
) -> list[str]:
    """Pure shared validator for `run.json`, used by `init_run`, `end_run`, `quarantine_run`, and `validate_run`."""
    errors: list[str] = []
    _check_keyset(run_doc, RUN_ALLOWED_KEYS, "run", errors, required=RUN_DOC_KEYS)
    if run_doc.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"run.schema_version must be {SCHEMA_VERSION!r}, got {run_doc.get('schema_version')!r}")
    rid = _check_id_safe(run_doc.get("run_id"), "run.run_id", errors)
    if expected_run_id is not None and rid is not None and rid != expected_run_id:
        errors.append(f"run.json run_id mismatch: expected {expected_run_id!r}, got {rid!r}")
    _check_id_safe(run_doc.get("drill_id"), "run.drill_id", errors)
    _check_id_safe(run_doc.get("unit_id"), "run.unit_id", errors)

    for fld, allowed in (
        ("mode", MODES),
        ("actor_type", ACTOR_TYPES),
        ("prior_exposure", EXPOSURE_LEVELS),
        ("contamination", CONTAMINATION_STATES),
    ):
        _check_enum(run_doc.get(fld), allowed, f"run.{fld}", errors)
    _check_non_empty_str(run_doc.get("role"), "run.role", errors)
    for fld in ("model_id", "effort", "session_id", "sample_reason", "source_commit"):
        _check_non_empty_str(run_doc.get(fld), f"run.{fld}", errors, allow_none=True)

    started_dt: dt.datetime | None = None
    try:
        started_dt = _parse_iso_utc(run_doc.get("started_at"), "run.started_at")
    except ValueError as exc:
        errors.append(str(exc))
    if run_doc.get("ended_at") is not None:
        try:
            ended_dt = _parse_iso_utc(run_doc["ended_at"], "run.ended_at")
            if started_dt is not None and ended_dt < started_dt:
                errors.append(
                    f"run.ended_at ({run_doc['ended_at']}) cannot precede run.started_at ({run_doc.get('started_at')})"
                )
        except ValueError as exc:
            errors.append(str(exc))

    closure_status = run_doc.get("closure_status")
    if "closure_status" in run_doc:
        _check_enum(closure_status, CLOSURE_STATUSES, "run.closure_status", errors)
    closed_obs = run_doc.get("closed_observed_at")
    if closed_obs is not None:
        try:
            _parse_iso_utc(closed_obs, "run.closed_observed_at")
        except ValueError as exc:
            errors.append(str(exc))

    quarantine_doc = run_doc.get("quarantine")
    is_open = run_doc.get("ended_at") is None
    if is_open:
        if "closure_status" in run_doc and closure_status != "open":
            errors.append(f"run.closure_status must be 'open' while ended_at is null, got {closure_status!r}")
        if closed_obs is not None:
            errors.append("run.closed_observed_at must be null while run is open")
        if quarantine_doc is not None:
            errors.append("run.quarantine must be null while run is open")
    else:
        if "closure_status" in run_doc and closure_status not in ("closed", "quarantined"):
            errors.append("run.closure_status cannot be 'open' when ended_at is set")
        if closure_status == "quarantined":
            _validate_quarantine_doc(quarantine_doc, errors)
        elif quarantine_doc is not None:
            errors.append("run.quarantine must be null unless closure_status is 'quarantined'")

    _validate_missing_reasons(run_doc, RUN_NULLABLE_FIELDS, run_doc.get("missing_reasons"), "run", errors)
    _validate_allowed_materials(
        repo_root, run_dir, run_doc.get("allowed_materials"), run_doc.get("mode"), run_doc.get("role"), errors
    )
    if not isinstance(run_doc.get("content_sha256"), str) or not SHA256_HEX_RE.match(run_doc["content_sha256"]):
        errors.append("run.content_sha256 must be a 64-char hex digest")
    _check_non_empty_str(run_doc.get("drill_path"), "run.drill_path", errors)
    iso = run_doc.get("isolation_check")
    if not isinstance(iso, dict):
        errors.append("run.isolation_check must be an object")
    else:
        _check_keyset(
            iso, ISOLATION_CHECK_ALLOWED_KEYS, "run.isolation_check", errors, required=ISOLATION_CHECK_REQUIRED_KEYS
        )
        _validate_snapshot_struct(iso.get("protected_snapshot"), "run.isolation_check.protected_snapshot", errors)
        end_snap = iso.get("end_protected_snapshot")
        if is_open and end_snap is not None:
            errors.append("run.isolation_check.end_protected_snapshot must be absent/null while run is open")
        elif end_snap is not None:
            _validate_snapshot_struct(end_snap, "run.isolation_check.end_protected_snapshot", errors)
            if closed_obs is None:
                errors.append("run.closed_observed_at is required when end_protected_snapshot is recorded")
        elif closure_status == "quarantined":
            errors.append("run.isolation_check.end_protected_snapshot is required when closure_status is 'quarantined'")
    return errors


def _collect_record_refs(rec: dict[str, Any]) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = [(f, rec[f]) for f in SINGLE_REF_FIELDS if isinstance(rec.get(f), str)]
    for fld in ("evidence_refs", "issue_refs"):
        for idx, item in enumerate(rec.get(fld) if isinstance(rec.get(fld), list) else []):
            if isinstance(item, str) and not (fld == "issue_refs" and ISSUE_ID_RE.match(item)):
                refs.append((f"{fld}[{idx}]", item))
    for idx, ev in enumerate(rec.get("help_events") if isinstance(rec.get("help_events"), list) else []):
        if isinstance(ev, dict) and isinstance(ev.get("ref"), str):
            refs.append((f"help_events[{idx}].ref", ev["ref"]))
    if isinstance(rec.get("dimensions"), dict):
        for dname, entry in rec["dimensions"].items():
            for idx, ref in enumerate(
                entry.get("evidence_refs")
                if isinstance(entry, dict) and isinstance(entry.get("evidence_refs"), list)
                else []
            ):
                if isinstance(ref, str):
                    refs.append((f"dimensions.{dname}.evidence_refs[{idx}]", ref))
    if isinstance(rec.get("additional"), dict):
        for k, v in rec["additional"].items():
            if isinstance(k, str) and k.endswith("_ref") and isinstance(v, str):
                refs.append((f"additional.{k}", v))
            elif isinstance(k, str) and k.endswith("_refs") and isinstance(v, list):
                for idx, item in enumerate(v):
                    if isinstance(item, str):
                        refs.append((f"additional.{k}[{idx}]", item))
    return refs


def _validate_help_events(
    repo_root: Path, run_dir: Path, events: Any, label: str, errors: list[str], capture_into: dict[str, str] | None
) -> list[dict[str, Any]] | None:
    if events is None:
        return None
    if not isinstance(events, list):
        errors.append(f"{label}.help_events must be a list or null")
        return None
    out: list[dict[str, Any]] = []
    prev_dt: dt.datetime | None = None
    for idx, ev in enumerate(events):
        ev_lbl = f"{label}.help_events[{idx}]"
        if not isinstance(ev, dict):
            errors.append(f"{ev_lbl} must be an object")
            continue
        extra = sorted(set(ev.keys()) - HELP_EVENT_KEYS)
        if extra:
            errors.append(f"{ev_lbl} unsupported keys: {extra}")
        _check_enum(ev.get("kind"), HELP_EVENT_KINDS, f"{ev_lbl}.kind", errors)
        obs = ev.get("observed_at")
        try:
            obs_dt = _parse_iso_utc(obs, f"{ev_lbl}.observed_at")
            if prev_dt is not None and obs_dt < prev_dt:
                errors.append(f"{ev_lbl} is out of chronological order ({obs} < prior timestamp)")
            prev_dt = obs_dt
        except ValueError as exc:
            errors.append(str(exc))
        cleaned: dict[str, Any] = {"kind": ev.get("kind"), "observed_at": obs}
        if ev.get("ref") is not None:
            try:
                cleaned["ref"] = _resolve_or_capture_ref(repo_root, run_dir, ev["ref"], capture_into)
            except (ValueError, FileNotFoundError) as exc:
                errors.append(f"{ev_lbl}.ref invalid: {exc}")
        out.append(cleaned)
    return out


def _validate_dimensions(
    repo_root: Path, run_dir: Path, dimensions: Any, label: str, errors: list[str], capture_into: dict[str, str] | None
) -> dict[str, Any] | None:
    if dimensions is None:
        return None
    if not isinstance(dimensions, dict):
        errors.append(f"{label}.dimensions must be an object or null")
        return None
    out: dict[str, Any] = {}
    for dname, entry in dimensions.items():
        dlbl = f"{label}.dimensions.{dname}"
        if dname not in DIMENSIONS:
            errors.append(f"{label} unknown dimension: {dname!r}")
            continue
        if not isinstance(entry, dict):
            errors.append(f"{dlbl} must be an object")
            continue
        extra = sorted(set(entry.keys()) - DIMENSION_ENTRY_KEYS)
        if extra:
            errors.append(f"{dlbl} unsupported keys: {extra}")
        status = entry.get("status")
        _check_enum(status, DIMENSION_STATUSES, f"{dlbl}.status", errors)
        _check_non_empty_str(entry.get("reason"), f"{dlbl}.reason", errors)
        _check_enum(entry.get("confidence"), CONFIDENCE_LEVELS, f"{dlbl}.confidence", errors, allow_none=True)
        ev_refs = entry.get("evidence_refs")
        cleaned_refs: list[str] = []
        if not isinstance(ev_refs, list):
            errors.append(f"{dlbl}.evidence_refs must be a list")
        else:
            if status in ("supported", "concern") and not ev_refs:
                errors.append(f"{dlbl}.evidence_refs required for status={status}")
            for idx, ref in enumerate(ev_refs):
                try:
                    cleaned_refs.append(_resolve_or_capture_ref(repo_root, run_dir, ref, capture_into))
                except (ValueError, FileNotFoundError) as exc:
                    errors.append(f"{dlbl}.evidence_refs[{idx}] invalid: {exc}")
        out[dname] = {
            "status": status,
            "evidence_refs": cleaned_refs,
            "reason": entry["reason"].strip() if isinstance(entry.get("reason"), str) else entry.get("reason"),
            "confidence": entry.get("confidence"),
        }
    return out


def _validate_probe(probe: Any, label: str, errors: list[str]) -> dict[str, Any] | None:
    if probe is None:
        return None
    if not isinstance(probe, dict):
        errors.append(f"{label}.probe must be an object or null")
        return None
    _check_keyset(probe, PROBE_KEYS, f"{label}.probe", errors)
    _check_id_safe(probe.get("probe_id"), f"{label}.probe.probe_id", errors)
    _check_id_safe(probe.get("parent_problem_id"), f"{label}.probe.parent_problem_id", errors)
    _check_non_empty_str(probe.get("changed_dimension"), f"{label}.probe.changed_dimension", errors)
    if not isinstance(probe.get("unchanged_objective"), bool):
        errors.append(f"{label}.probe.unchanged_objective must be a boolean")
    _check_non_neg_int(probe.get("delay_ms"), f"{label}.probe.delay_ms", errors)
    _check_enum(probe.get("exposure"), EXPOSURE_LEVELS, f"{label}.probe.exposure", errors)
    _check_enum(probe.get("outcome"), OUTCOMES, f"{label}.probe.outcome", errors)
    _check_enum(probe.get("explanation_status"), EXPLAIN_STATUSES, f"{label}.probe.explanation_status", errors)
    cd = probe.get("changed_dimension")
    return {**probe, "changed_dimension": cd.strip() if isinstance(cd, str) else cd}


def _validate_additional(
    repo_root: Path, run_dir: Path, additional: Any, label: str, errors: list[str], capture_into: dict[str, str] | None
) -> dict[str, Any]:
    if additional is None:
        return {}
    if not isinstance(additional, dict):
        errors.append(f"{label}.additional must be an object")
        return {}
    try:
        _check_no_forbidden_keys(additional, f"{label}.additional")
    except ValueError as exc:
        errors.append(str(exc))
    cleaned: dict[str, Any] = {}
    for k, v in additional.items():
        if not isinstance(k, str):
            continue
        if k.endswith("_ref"):
            if v is None:
                cleaned[k] = None
            else:
                try:
                    cleaned[k] = _resolve_or_capture_ref(repo_root, run_dir, v, capture_into)
                except (ValueError, FileNotFoundError) as exc:
                    errors.append(f"{label}.additional.{k} invalid: {exc}")
        elif k.endswith("_refs"):
            if not isinstance(v, list):
                errors.append(f"{label}.additional.{k} must be a list")
            else:
                refs_out: list[str] = []
                for idx, item in enumerate(v):
                    try:
                        refs_out.append(_resolve_or_capture_ref(repo_root, run_dir, item, capture_into))
                    except (ValueError, FileNotFoundError) as exc:
                        errors.append(f"{label}.additional.{k}[{idx}] invalid: {exc}")
                cleaned[k] = refs_out
        else:
            if isinstance(v, str) and (len(v) > 500 or "```" in v):
                errors.append(f"{label}.additional.{k} exceeds safe short metadata limits")
            cleaned[k] = v
    return cleaned


def _verify_snapshot_and_digests(
    repo_root: Path,
    run_dir: Path,
    rec: dict[str, Any],
    label: str,
    *,
    capture_refs: bool,
    verify_files: bool,
    errors: list[str],
) -> bool:
    tampering = False
    first_sub_ref, snap_rel, snap_sha = (
        rec.get("first_submission_ref"),
        rec.get("first_submission_snapshot"),
        rec.get("first_submission_sha256"),
    )
    if first_sub_ref is None:
        if snap_rel is not None or snap_sha is not None:
            errors.append(f"{label}.first_submission_snapshot/sha256 must be null when first_submission_ref is null")
    elif not capture_refs:
        if not isinstance(snap_rel, str) or not snap_rel.strip():
            errors.append(f"{label}.first_submission_snapshot is required when first_submission_ref is set")
        if not isinstance(snap_sha, str) or not SHA256_HEX_RE.match(snap_sha):
            errors.append(f"{label}.first_submission_sha256 must be a 64-char hex digest")
        if isinstance(snap_rel, str) and snap_rel.strip():
            try:
                snap_path, _ = resolve_safe_ref(repo_root, run_dir, snap_rel, must_exist=verify_files)
                _ensure_contained(run_dir / "snapshots", snap_path)
                if "#" in snap_rel:
                    errors.append(f"{label}.first_submission_snapshot cannot contain fragment '#'")
                if verify_files and _sha256_file(snap_path) != snap_sha:
                    tampering = True
                    errors.append(f"Tampering detected in snapshot {snap_rel}: digest mismatch")
            except (FileNotFoundError, ValueError) as exc:
                tampering = tampering or verify_files
                errors.append(f"{label} invalid or missing snapshot {snap_rel!r}: {exc}")

    digests = rec.get("captured_digests")
    if not isinstance(digests, dict):
        errors.append(f"{label}.captured_digests must be an object")
        return tampering
    for ref_label, ref_str in _collect_record_refs(rec):
        if ref_str not in digests:
            errors.append(f"{label}.captured_digests missing digest for {ref_label}: {ref_str}")
    if verify_files:
        for ref_str, expected_sha in digests.items():
            if not isinstance(expected_sha, str) or not SHA256_HEX_RE.match(expected_sha):
                errors.append(f"{label}.captured_digests[{ref_str!r}] has invalid SHA-256 digest")
                continue
            try:
                fpath, _ = resolve_safe_ref(repo_root, run_dir, ref_str, must_exist=True)
                actual_sha = _sha256_file(fpath)
                if actual_sha != expected_sha:
                    tampering = True
                    errors.append(
                        f"Tampering detected in {rec.get('record_id')} ref {ref_str}: {actual_sha} != {expected_sha}"
                    )
            except (FileNotFoundError, ValueError) as exc:
                tampering = True
                errors.append(f"Tampering or missing ref in {rec.get('record_id')} ({ref_str}): {exc}")
    return tampering


def _validate_item_record(
    repo_root: Path,
    run_dir: Path,
    run_doc: dict[str, Any],
    rec: dict[str, Any],
    drill_problem_ids: set[str],
    *,
    label: str,
    capture_refs: bool,
    verify_files: bool,
) -> tuple[list[str], bool]:
    """Single shared validator for item records used by `record_item` and `validate_run`."""
    errors: list[str] = []
    _check_keyset(rec, CORE_ITEM_KEYS, label, errors)
    if rec.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"{label}.schema_version must be {SCHEMA_VERSION!r}, got {rec.get('schema_version')!r}")
    if rec.get("run_id") != run_doc.get("run_id"):
        errors.append(f"{label}.run_id {rec.get('run_id')!r} does not match run {run_doc.get('run_id')!r}")
    mode = run_doc.get("mode")
    if rec.get("mode") != mode:
        errors.append(f"{label}.mode {rec.get('mode')!r} does not match run mode {mode!r}")

    _check_id_safe(rec.get("record_id"), f"{label}.record_id", errors)
    pid = _check_id_safe(rec.get("problem_id"), f"{label}.problem_id", errors)
    if rec.get("supersedes_record_id") is not None:
        _check_id_safe(rec["supersedes_record_id"], f"{label}.supersedes_record_id", errors)
    try:
        _parse_iso_utc(rec.get("recorded_at"), f"{label}.recorded_at")
    except ValueError as exc:
        errors.append(str(exc))

    att = rec.get("attempt_index")
    _check_non_neg_int(att, f"{label}.attempt_index", errors, min_val=1, allow_none=False)
    if mode != "transfer_probe" and drill_problem_ids and pid is not None and pid not in drill_problem_ids:
        errors.append(f"{label}.problem_id {pid!r} not found in drill {run_doc.get('drill_id')!r}")

    for fld in ("objective_ref", "form", "code_type", "blocker", "unique_contribution", "decision_reason"):
        _check_non_empty_str(rec.get(fld), f"{label}.{fld}", errors, allow_none=True)
    _check_str_list(rec.get("prerequisite_refs"), f"{label}.prerequisite_refs", errors, allow_none=True)
    _check_str_list(rec.get("demand_tags"), f"{label}.demand_tags", errors, allow_none=True)
    _check_str_list(rec.get("comparison_ids"), f"{label}.comparison_ids", errors)
    _check_non_neg_int(rec.get("sequence_index"), f"{label}.sequence_index", errors, min_val=1)

    planted = rec.get("planted")
    if planted is not None and not isinstance(planted, bool):
        errors.append(f"{label}.planted must be boolean true, false, or null, got {planted!r}")

    for fld, allowed, allow_none in (
        ("outcome", OUTCOMES, False),
        ("confidence_before_feedback", CONFIDENCE_LEVELS, True),
        ("error_origin", ERROR_ORIGINS, True),
        ("solution_exposure", EXPOSURE_LEVELS, False),
        ("review_verdict", REVIEW_VERDICTS, False),
        ("caught_by", CAUGHT_BY_VALUES, False),
        ("dispute_outcome", DISPUTE_OUTCOMES, False),
        ("explain_status", EXPLAIN_STATUSES, False),
        ("time_source", TIME_SOURCES, False),
        ("decision", DECISIONS, True),
    ):
        _check_enum(rec.get(fld), allowed, f"{label}.{fld}", errors, allow_none=allow_none)

    outcome, error_origin, time_source = rec.get("outcome"), rec.get("error_origin"), rec.get("time_source")
    if mode in ("natural_attempt", "transfer_probe") and planted is True:
        errors.append(f"{label}.planted=true is forbidden in {mode} mode")
    if mode in ("natural_attempt", "transfer_probe") and error_origin == "planted":
        errors.append(f"{label}.error_origin='planted' is forbidden in {mode} mode")
    if planted is False and error_origin == "planted":
        errors.append(f"{label}.error_origin='planted' is forbidden when planted=false")
    if planted is True and error_origin not in (None, "planted", "ambiguous"):
        errors.append(f"{label}.error_origin must be 'planted' or 'ambiguous' when planted=true")

    for tfld in ("active_ms", "tool_wait_ms", "elapsed_ms"):
        tval = rec.get(tfld)
        if tval is not None and time_source == "unavailable":
            errors.append(f"{label}.{tfld} must be null when time_source is 'unavailable'")
        _check_non_neg_int(tval, f"{label}.{tfld}", errors)

    capture_into: dict[str, str] | None = {} if capture_refs else None
    for fld in SINGLE_REF_FIELDS:
        if rec.get(fld) is not None:
            try:
                canon = _resolve_or_capture_ref(repo_root, run_dir, rec[fld], capture_into)
                if capture_refs:
                    rec[fld] = canon
            except (ValueError, FileNotFoundError) as exc:
                errors.append(f"{label}.{fld} invalid: {exc}")

    for list_fld in ("evidence_refs", "issue_refs"):
        raw_list = rec.get(list_fld)
        if not isinstance(raw_list, list):
            errors.append(f"{label}.{list_fld} must be a list")
        else:
            cleaned_list: list[str] = []
            for idx, item in enumerate(raw_list):
                if list_fld == "issue_refs" and isinstance(item, str) and ISSUE_ID_RE.match(item):
                    cleaned_list.append(item)
                else:
                    try:
                        cleaned_list.append(_resolve_or_capture_ref(repo_root, run_dir, item, capture_into))
                    except (ValueError, FileNotFoundError) as exc:
                        errors.append(f"{label}.{list_fld}[{idx}] invalid: {exc}")
            if capture_refs:
                rec[list_fld] = cleaned_list

    help_events = _validate_help_events(repo_root, run_dir, rec.get("help_events"), label, errors, capture_into)
    dims = _validate_dimensions(repo_root, run_dir, rec.get("dimensions"), label, errors, capture_into)
    probe = _validate_probe(rec.get("probe"), label, errors)
    additional = _validate_additional(repo_root, run_dir, rec.get("additional"), label, errors, capture_into)
    if capture_refs:
        rec.update(
            {
                "help_events": help_events,
                "dimensions": dims,
                "probe": probe,
                "additional": additional,
                "captured_digests": capture_into,
            }
        )

    first_sub_ref, plant_manifest_ref = rec.get("first_submission_ref"), rec.get("plant_manifest_ref")
    if mode != "retrospective" and outcome not in ("not_attempted", "blocked") and att == 1 and first_sub_ref is None:
        errors.append(f"{label}.first_submission_ref is required for first attempted items outside retrospective mode")
    if mode == "natural_attempt" and plant_manifest_ref is not None:
        errors.append(f"{label}.plant_manifest_ref is forbidden in natural_attempt mode")
    if planted is True and mode == "fault_injection" and plant_manifest_ref is None:
        errors.append(f"{label}.plant_manifest_ref is required when planted=true in fault_injection mode")
    if outcome != "not_attempted" and not (
        first_sub_ref or (isinstance(rec.get("evidence_refs"), list) and rec["evidence_refs"])
    ):
        errors.append(f"{label} requires at least one reference (first_submission_ref or evidence_refs)")
    if mode == "transfer_probe" and probe is None:
        errors.append(f"{label}.probe object is required in transfer_probe mode")
    if rec.get("decision") is not None and (
        not isinstance(rec.get("decision_reason"), str) or not rec["decision_reason"].strip()
    ):
        errors.append(f"{label}.decision_reason must be a non-empty string when decision is set")

    nullable_req = ["planted", "confidence_before_feedback", "help_events"] + (
        ["error_origin"] if outcome in ("incorrect", "partial", "invalid_input", "blocked") else []
    )
    cleaned_mr = _validate_missing_reasons(rec, tuple(nullable_req), rec.get("missing_reasons"), label, errors)
    if capture_refs:
        rec["missing_reasons"] = cleaned_mr

    tampering = _verify_snapshot_and_digests(
        repo_root, run_dir, rec, label, capture_refs=capture_refs, verify_files=verify_files, errors=errors
    )
    return errors, tampering


def _validate_revision_chains(records: list[dict[str, Any]]) -> list[str]:
    """Enforce linear revision chains preserving `(problem_id, attempt_index)` and locked first submission."""
    errors: list[str] = []
    by_id: dict[str, dict[str, Any]] = {}
    superseded: set[str] = set()
    active_roots: set[tuple[str, int]] = set()
    for idx, rec in enumerate(records, start=1):
        rid, pid, att, sup = (
            rec.get("record_id"),
            rec.get("problem_id"),
            rec.get("attempt_index"),
            rec.get("supersedes_record_id"),
        )
        if not isinstance(rid, str) or not isinstance(pid, str) or isinstance(att, bool) or not isinstance(att, int):
            continue
        if rid in by_id:
            errors.append(f"Duplicate record_id in items.jsonl: {rid}")
            continue
        if sup is not None:
            if not isinstance(sup, str):
                continue
            if sup == rid or sup not in by_id:
                errors.append(f"items[{idx}] supersedes_record_id {sup!r} does not reference a prior record")
            elif sup in superseded:
                errors.append(f"items[{idx}] supersedes_record_id {sup!r} already superseded (branching forbidden)")
            else:
                target = by_id[sup]
                if target.get("problem_id") != pid:
                    errors.append(
                        f"items[{idx}] supersedes_record_id {sup!r} belongs to different problem_id {target.get('problem_id')!r}"
                    )
                if target.get("attempt_index") != att:
                    errors.append(
                        f"items[{idx}] supersedes_record_id {sup!r} changes attempt_index ({target.get('attempt_index')} -> {att})"
                    )
                if (target.get("first_submission_ref") is None) != (rec.get("first_submission_ref") is None):
                    errors.append(
                        f"items[{idx}] supersedes_record_id {sup!r} changes first_submission_ref null/non-null state"
                    )
                elif target.get("first_submission_sha256") != rec.get("first_submission_sha256"):
                    errors.append(
                        f"items[{idx}] supersedes_record_id {sup!r} changes locked first_submission_sha256 "
                        f"({target.get('first_submission_sha256')} -> {rec.get('first_submission_sha256')})"
                    )
                superseded.add(sup)
        else:
            if (pid, att) in active_roots:
                errors.append(
                    f"Duplicate attempt for ({pid}, attempt_index={att}); use supersedes_record_id for revisions"
                )
            active_roots.add((pid, att))
        by_id[rid] = rec
    return errors


def init_run(
    repo_root: Path,
    *,
    run_id: str,
    mode: str,
    drill_id: str,
    unit_id: str | None = None,
    actor_type: str = "ai",
    model_id: str | None = None,
    effort: str | None = None,
    role: str = "learner",
    session_id: str | None = None,
    sample_reason: str | None = None,
    source_commit: str | None = None,
    allowed_materials: list[str] | None = None,
    prior_exposure: str = "unknown",
    contamination: str = "unknown",
    missing_reasons: dict[str, str] | None = None,
    started_at: str | None = None,
    ended_at: str | None = None,
) -> dict[str, Any]:
    """Initialize an isolated quality collection run under `pilot/quality/<run_id>/`."""
    run_dir = safe_run_dir(repo_root, run_id, must_exist=False)
    if run_dir.exists():
        raise FileExistsError(f"Run already exists and cannot be overwritten: {run_id}")
    if mode != "retrospective" and ended_at is not None:
        raise ValueError("ended_at can only be supplied at init in retrospective mode; use finish for prospective runs")

    drill_path, drill_doc, content_sha256 = locate_drill(repo_root, drill_id, unit_id=unit_id)
    resolved_unit = unit_id or drill_doc.get("unitCode")
    if not isinstance(resolved_unit, str) or not resolved_unit.strip():
        raise ValueError("unit_id is required when drill JSON lacks unitCode")

    commit = (
        source_commit.strip()
        if isinstance(source_commit, str) and source_commit.strip()
        else _detect_git_commit(repo_root)
    )
    reasons_in = dict(missing_reasons or {})
    if commit is None and "source_commit" not in reasons_in:
        reasons_in["source_commit"] = "git HEAD unavailable in repository"
    if ended_at is None:
        reasons_in.setdefault("ended_at", "run_in_progress")

    root_resolved = repo_root.resolve()
    materials_in = allowed_materials if allowed_materials is not None else []
    start_ts = started_at if started_at is not None else _utc_now()
    start_snapshot = snapshot_protected_paths(repo_root)
    is_retro_preclosed = ended_at is not None
    observed_close = _utc_now() if is_retro_preclosed else None
    iso_check: dict[str, Any] = {
        "run_progress_dir": (run_dir / "progress").relative_to(root_resolved).as_posix(),
        "run_workspace_dir": (run_dir / "workspace").relative_to(root_resolved).as_posix(),
        "protected_snapshot": start_snapshot,
    }
    if is_retro_preclosed:
        iso_check["end_protected_snapshot"] = start_snapshot
    run_doc: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "mode": mode,
        "started_at": start_ts,
        "ended_at": ended_at,
        "closure_status": "closed" if is_retro_preclosed else "open",
        "closed_observed_at": observed_close,
        "quarantine": None,
        "source_commit": commit,
        "content_sha256": content_sha256,
        "drill_path": drill_path.resolve().relative_to(root_resolved).as_posix(),
        "unit_id": resolved_unit,
        "drill_id": drill_id,
        "sample_reason": sample_reason.strip() if isinstance(sample_reason, str) else sample_reason,
        "actor_type": actor_type,
        "model_id": model_id.strip() if isinstance(model_id, str) else model_id,
        "effort": effort.strip() if isinstance(effort, str) else effort,
        "role": role.strip() if isinstance(role, str) else role,
        "session_id": session_id.strip() if isinstance(session_id, str) else session_id,
        "allowed_materials": materials_in,
        "prior_exposure": prior_exposure,
        "contamination": contamination,
        "missing_reasons": reasons_in,
        "isolation_check": iso_check,
    }
    errors = _validate_run_doc(repo_root, run_dir, run_doc, expected_run_id=run_id)
    if errors:
        raise ValueError("; ".join(errors))

    norm_errs: list[str] = []
    run_doc["allowed_materials"] = _validate_allowed_materials(
        repo_root, run_dir, materials_in, mode, run_doc["role"], norm_errs
    )
    run_doc["missing_reasons"] = _validate_missing_reasons(run_doc, RUN_NULLABLE_FIELDS, reasons_in, "run", norm_errs)

    run_dir.mkdir(parents=True, exist_ok=False)
    for sub in ("progress", "workspace", "snapshots"):
        (run_dir / sub).mkdir(exist_ok=False)
    with (run_dir / "run.json").open("x", encoding="utf-8") as f:
        json.dump(run_doc, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return run_doc


def _load_run_doc(repo_root: Path, run_id: str) -> tuple[Path, dict[str, Any]]:
    run_dir = safe_run_dir(repo_root, run_id, must_exist=True)
    run_json = _ensure_contained(run_dir, run_dir / "run.json")
    if not run_json.is_file():
        raise FileNotFoundError(f"Missing run.json in {run_dir}")
    doc = json.loads(run_json.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        raise ValueError("run.json must be a JSON object")
    return run_dir, doc


def _read_items_jsonl(run_dir: Path) -> list[dict[str, Any]]:
    items_path = _ensure_contained(run_dir, run_dir / "items.jsonl")
    if not items_path.exists():
        return []
    if not items_path.is_file():
        raise ValueError("items.jsonl is not a regular file")
    records: list[dict[str, Any]] = []
    for idx, line in enumerate(items_path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.strip():
            obj = json.loads(line)
            if not isinstance(obj, dict):
                raise ValueError(f"items.jsonl line {idx} is not a JSON object")
            records.append(obj)
    return records


def record_item(repo_root: Path, *, run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Validate and append an answer-free item attempt record to `items.jsonl`."""
    if not isinstance(payload, dict):
        raise ValueError("Payload must be a JSON object")
    run_dir, run_doc = _load_run_doc(repo_root, run_id)
    if run_doc.get("run_id") != run_id:
        raise ValueError(f"run.json run_id mismatch: expected {run_id}, got {run_doc.get('run_id')}")
    if run_doc.get("ended_at") is not None:
        raise ValueError(f"Cannot record item to closed run {run_id!r} (ended_at={run_doc['ended_at']})")

    _, drill_doc, _ = locate_drill(repo_root, run_doc["drill_id"], unit_id=run_doc["unit_id"])
    drill_problem_ids = {p.get("id") for p in drill_doc.get("problems", []) if isinstance(p, dict) and p.get("id")}

    defaults: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "recorded_at": _utc_now(),
        "mode": run_doc["mode"],
        "evidence_refs": [],
        "review_verdict": "not_reviewed",
        "caught_by": "unknown",
        "dispute_outcome": "not_applicable",
        "explain_status": "not_observed",
        "issue_refs": [],
        "time_source": "unavailable",
        "comparison_ids": [],
        "missing_reasons": {},
        "captured_digests": {},
    }
    record: dict[str, Any] = {k: payload[k] if k in payload else defaults.get(k) for k in CORE_ITEM_KEYS}
    record.update(
        {
            "schema_version": SCHEMA_VERSION,
            "first_submission_snapshot": None,
            "first_submission_sha256": None,
            "captured_digests": {},
        }
    )
    if record["recorded_at"] is None:
        record["recorded_at"] = _utc_now()
    if isinstance(record.get("decision_reason"), str):
        record["decision_reason"] = record["decision_reason"].strip()
    if "missing_reasons" in payload and payload["missing_reasons"] is None:
        record["missing_reasons"] = {}
    for extra_k in set(payload.keys()) - CORE_ITEM_KEYS:
        record[extra_k] = payload[extra_k]

    val_errors, _ = _validate_item_record(
        repo_root, run_dir, run_doc, record, drill_problem_ids, label="record", capture_refs=True, verify_files=False
    )
    src_path: Path | None = None
    snap_bytes: bytes | None = None
    if isinstance(record.get("first_submission_ref"), str):
        try:
            src_path, _ = resolve_safe_ref(repo_root, run_dir, record["first_submission_ref"], must_exist=True)
        except (ValueError, FileNotFoundError):
            src_path = None
        if src_path is not None:
            snap_bytes = src_path.read_bytes()
            record["first_submission_sha256"] = _sha256_bytes(snap_bytes)

    existing = _read_items_jsonl(run_dir)
    all_errors = val_errors + _validate_revision_chains([*existing, record])
    if all_errors:
        raise ValueError("; ".join(all_errors))

    snap_path: Path | None = None
    if src_path is not None and snap_bytes is not None:
        suffix = src_path.suffix if len(src_path.suffix) <= 16 else ".bin"
        snap_dir = _ensure_contained(run_dir, run_dir / "snapshots")
        snap_path = _ensure_contained(snap_dir, snap_dir / f"{record['record_id']}_first_submission{suffix}")
        if snap_path.exists():
            raise FileExistsError(f"Snapshot already exists for {record['record_id']}: {snap_path.name}")
        record["first_submission_snapshot"] = (
            snap_path.resolve(strict=False).relative_to(repo_root.resolve()).as_posix()
        )

    wrote_snap = False
    try:
        if snap_path is not None and snap_bytes is not None:
            snap_path.parent.mkdir(exist_ok=True)
            with snap_path.open("xb") as f:
                f.write(snap_bytes)
            os.chmod(snap_path, 0o444)
            wrote_snap = True
        items_path = _ensure_contained(run_dir, run_dir / "items.jsonl")
        with items_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        if wrote_snap and snap_path is not None and snap_path.exists():
            os.chmod(snap_path, 0o644)
            snap_path.unlink()
        raise
    return record


def _write_run_doc(run_dir: Path, doc: dict[str, Any]) -> None:
    tmp_json = _ensure_contained(run_dir, run_dir / ".run.json.tmp")
    with tmp_json.open("w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp_json, run_dir / "run.json")


def _ensure_run_open(run_doc: dict[str, Any], run_id: str) -> None:
    if run_doc.get("ended_at") is not None or run_doc.get("closure_status") in ("closed", "quarantined"):
        raise ValueError(f"Run {run_id!r} is already closed at {run_doc.get('ended_at')}")


def end_run(repo_root: Path, run_id: str, *, ended_at: str | None = None) -> dict[str, Any]:
    """Validate and close an open run by storing final protected snapshot and close timestamps in `run.json`."""
    run_dir, run_doc = _load_run_doc(repo_root, run_id)
    _ensure_run_open(run_doc, run_id)
    validation = validate_run(repo_root, run_id)
    if not validation["valid"]:
        raise ValueError(f"Cannot finish invalid run {run_id!r}: " + "; ".join(validation["errors"]))

    observed_close = _utc_now()
    end_snapshot = snapshot_protected_paths(repo_root)
    start_snapshot = (run_doc.get("isolation_check") or {}).get("protected_snapshot") or {}
    mismatches = compare_protected_snapshots(start_snapshot, end_snapshot)
    if mismatches:
        raise ValueError(
            f"Cannot finish run {run_id!r} due to protected-path isolation mismatch: " + "; ".join(mismatches)
        )

    updated = dict(run_doc)
    updated["ended_at"] = ended_at if ended_at is not None else observed_close
    updated["closure_status"] = "closed"
    updated["closed_observed_at"] = observed_close
    updated["quarantine"] = None
    reasons = dict(run_doc.get("missing_reasons") or {})
    reasons.pop("ended_at", None)
    updated["missing_reasons"] = reasons
    iso = dict(run_doc["isolation_check"])
    iso["end_protected_snapshot"] = end_snapshot
    updated["isolation_check"] = iso

    errors = _validate_run_doc(repo_root, run_dir, updated, expected_run_id=run_id)
    if errors:
        raise ValueError("; ".join(errors))

    _write_run_doc(run_dir, updated)
    return updated


def quarantine_run(
    repo_root: Path,
    run_id: str,
    *,
    reason: str,
    evidence_ref: str | None = None,
    ended_at: str | None = None,
) -> dict[str, Any]:
    """Close an interrupted open run as quarantined when only protected-path isolation mismatched."""
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("Quarantine reason must be a non-empty string")
    clean_reason = reason.strip()
    if len(clean_reason) > 500 or "```" in clean_reason:
        raise ValueError("Quarantine reason exceeds safe short metadata limits")

    run_dir, run_doc = _load_run_doc(repo_root, run_id)
    _ensure_run_open(run_doc, run_id)

    canon_ref: str | None = None
    evidence_sha: str | None = None
    if evidence_ref is not None:
        fpath, canon_ref = resolve_safe_ref(repo_root, run_dir, evidence_ref, must_exist=True)
        evidence_sha = _sha256_file(fpath)

    validation, _, _, _, non_iso_errors, _ = _inspect_run(repo_root, run_id)
    if non_iso_errors or not validation["content_hash_ok"] or validation["tampering_detected"]:
        blocking = non_iso_errors or validation["errors"]
        raise ValueError(f"Cannot quarantine run {run_id!r} with integrity/schema errors: " + "; ".join(blocking))

    observed_close = _utc_now()
    end_snapshot = snapshot_protected_paths(repo_root)
    start_snapshot = (run_doc.get("isolation_check") or {}).get("protected_snapshot") or {}
    mismatches = compare_protected_snapshots(start_snapshot, end_snapshot)

    updated = dict(run_doc)
    updated["ended_at"] = ended_at if ended_at is not None else observed_close
    updated["closure_status"] = "quarantined"
    updated["closed_observed_at"] = observed_close
    reasons = dict(run_doc.get("missing_reasons") or {})
    reasons.pop("ended_at", None)
    updated["missing_reasons"] = reasons
    iso = dict(run_doc["isolation_check"])
    iso["end_protected_snapshot"] = end_snapshot
    updated["isolation_check"] = iso
    updated["quarantine"] = {
        "reason": clean_reason,
        "quarantined_at": observed_close,
        "evidence_ref": canon_ref,
        "evidence_sha256": evidence_sha,
        "isolation_mismatches": mismatches,
    }

    errors = _validate_run_doc(repo_root, run_dir, updated, expected_run_id=run_id)
    if errors:
        raise ValueError("; ".join(errors))

    _write_run_doc(run_dir, updated)
    return updated


def _inspect_run(
    repo_root: Path, run_id: str
) -> tuple[dict[str, Any], Path, dict[str, Any], list[dict[str, Any]], list[str], list[str]]:
    errors: list[str] = []
    non_iso_errors: list[str] = []
    warnings: list[str] = []
    exclusion_reasons: list[str] = []

    run_dir, run_doc = _load_run_doc(repo_root, run_id)
    doc_errs = _validate_run_doc(repo_root, run_dir, run_doc, expected_run_id=run_id)
    errors.extend(doc_errs)
    non_iso_errors.extend(doc_errs)

    content_hash_ok = False
    drill_problem_ids: set[str] = set()
    try:
        drill_path, drill_doc, actual_sha = locate_drill(
            repo_root, str(run_doc.get("drill_id", "")), unit_id=run_doc.get("unit_id")
        )
        if actual_sha != run_doc.get("content_sha256"):
            msg = f"Source content_sha256 mismatch: expected {run_doc.get('content_sha256')}, got {actual_sha}"
            errors.append(msg)
            non_iso_errors.append(msg)
        else:
            content_hash_ok = True
        drill_problem_ids = {
            p["id"] for p in drill_doc.get("problems", []) if isinstance(p, dict) and isinstance(p.get("id"), str)
        }
        expected_rel = drill_path.resolve().relative_to(repo_root.resolve()).as_posix()
        if run_doc.get("drill_path") and run_doc.get("drill_path") != expected_rel:
            msg = f"drill_path mismatch: {run_doc.get('drill_path')} != {expected_rel}"
            errors.append(msg)
            non_iso_errors.append(msg)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        msg = f"Source drill verification failed: {exc}"
        errors.append(msg)
        non_iso_errors.append(msg)

    is_open = run_doc.get("ended_at") is None
    closure_status = run_doc.get("closure_status") or ("open" if is_open else "closed")
    isolation_ok: bool | None = True
    isolation_status = "verified"
    isolation_mismatches: list[str] = []
    root_resolved = repo_root.resolve()
    iso = run_doc.get("isolation_check")
    dirs_ok = True
    if not isinstance(iso, dict):
        isolation_ok = False
        isolation_status = "mismatch"
        dirs_ok = False
    else:
        for key, sub in (("run_progress_dir", "progress"), ("run_workspace_dir", "workspace")):
            expected_sub = (run_dir / sub).relative_to(root_resolved).as_posix()
            if iso.get(key) != expected_sub:
                msg = f"Isolated {sub}_dir mismatch: {iso.get(key)!r} != {expected_sub!r}"
                errors.append(msg)
                non_iso_errors.append(msg)
                isolation_ok = False
                isolation_status = "mismatch"
                dirs_ok = False
            sub_dir = run_dir / sub
            if sub_dir.is_symlink() or not sub_dir.is_dir():
                msg = f"Isolated directory missing or symlink: {sub_dir.relative_to(root_resolved)}"
                errors.append(msg)
                non_iso_errors.append(msg)
                isolation_ok = False
                isolation_status = "mismatch"
                dirs_ok = False

        start_snap = iso.get("protected_snapshot") or {}
        end_snap = iso.get("end_protected_snapshot")
        if is_open:
            isolation_mismatches = compare_protected_snapshots(start_snap, snapshot_protected_paths(repo_root))
            if isolation_mismatches:
                isolation_ok = False
                isolation_status = "mismatch"
                errors.extend(f"Protected-path isolation mismatch: {m}" for m in isolation_mismatches)
        elif closure_status == "quarantined":
            warnings.append("run_quarantined")
            isolation_status = "quarantined"
            isolation_ok = False
            if isinstance(end_snap, dict):
                isolation_mismatches = compare_protected_snapshots(start_snap, end_snap)
                qdoc = run_doc.get("quarantine")
                if isinstance(qdoc, dict) and qdoc.get("isolation_mismatches") != isolation_mismatches:
                    msg = "Quarantine isolation_mismatches does not match stored start/end protected snapshots"
                    errors.append(msg)
                    non_iso_errors.append(msg)
        elif isinstance(end_snap, dict):
            isolation_mismatches = compare_protected_snapshots(start_snap, end_snap)
            if isolation_mismatches:
                isolation_ok = False
                isolation_status = "mismatch"
                for m in isolation_mismatches:
                    msg = f"Protected-path isolation mismatch: {m}"
                    errors.append(msg)
                    non_iso_errors.append(msg)
        else:
            warnings.append("missing_end_protected_snapshot")
            if dirs_ok:
                isolation_status = "unknown"
                isolation_ok = None

    records: list[dict[str, Any]] = []
    tampering_detected = False
    try:
        records = _read_items_jsonl(run_dir)
    except (ValueError, json.JSONDecodeError) as exc:
        msg = f"Failed to read items.jsonl: {exc}"
        errors.append(msg)
        non_iso_errors.append(msg)

    for idx, rec in enumerate(records, start=1):
        rec_errs, rec_tamper = _validate_item_record(
            repo_root,
            run_dir,
            run_doc,
            rec,
            drill_problem_ids,
            label=f"items[{idx}]",
            capture_refs=False,
            verify_files=True,
        )
        errors.extend(rec_errs)
        non_iso_errors.extend(rec_errs)
        tampering_detected = tampering_detected or rec_tamper
    rev_errs = _validate_revision_chains(records)
    errors.extend(rev_errs)
    non_iso_errors.extend(rev_errs)

    qdoc = run_doc.get("quarantine")
    if closure_status == "quarantined" and isinstance(qdoc, dict) and isinstance(qdoc.get("evidence_ref"), str):
        ev_ref = qdoc["evidence_ref"]
        ev_sha = qdoc.get("evidence_sha256")
        try:
            fpath, _ = resolve_safe_ref(repo_root, run_dir, ev_ref, must_exist=True)
            actual_ev_sha = _sha256_file(fpath)
            if actual_ev_sha != ev_sha:
                tampering_detected = True
                msg = f"Tampering detected in quarantine evidence_ref {ev_ref}: {actual_ev_sha} != {ev_sha}"
                errors.append(msg)
                non_iso_errors.append(msg)
        except (FileNotFoundError, ValueError) as exc:
            tampering_detected = True
            msg = f"Tampering or missing quarantine evidence_ref ({ev_ref}): {exc}"
            errors.append(msg)
            non_iso_errors.append(msg)

    mode, contamination, prior_exposure = (
        run_doc.get("mode"),
        run_doc.get("contamination"),
        run_doc.get("prior_exposure"),
    )
    for cond, reason in (
        (mode != "natural_attempt", f"mode={mode}"),
        (contamination != "no", f"contamination={contamination}"),
        (prior_exposure not in ("none", "visible_only"), f"prior_exposure={prior_exposure}"),
        (closure_status == "quarantined", "quarantined"),
        (isolation_status == "unknown", "isolation_unknown"),
        (isolation_ok is False, "isolation_failed"),
        (not content_hash_ok, "content_hash_mismatch"),
        (tampering_detected, "tampering_detected"),
    ):
        if cond:
            exclusion_reasons.append(reason)

    if not records:
        warnings.append("no_item_records")
    if is_open:
        warnings.append("run_still_open")

    covered = sorted({r.get("problem_id") for r in records if isinstance(r.get("problem_id"), str)})
    missingness = {fld: sum(1 for r in records if r.get(fld) is None) for fld in ITEM_MISSINGNESS_TRACKED}
    missingness = {k: v for k, v in missingness.items() if v > 0}

    quarantine_summary = None
    if closure_status == "quarantined" and isinstance(qdoc, dict):
        quarantine_summary = {
            "reason": qdoc.get("reason"),
            "quarantined_at": qdoc.get("quarantined_at"),
            "evidence_ref": qdoc.get("evidence_ref"),
            "evidence_sha256": qdoc.get("evidence_sha256"),
            "isolation_mismatches": list(qdoc.get("isolation_mismatches") or []),
        }

    validation = {
        "valid": not errors,
        "run_id": run_id,
        "mode": mode,
        "closed": not is_open,
        "closure_status": closure_status,
        "started_at": run_doc.get("started_at"),
        "ended_at": run_doc.get("ended_at"),
        "closed_observed_at": run_doc.get("closed_observed_at"),
        "drill_id": run_doc.get("drill_id"),
        "unit_id": run_doc.get("unit_id"),
        "content_hash_ok": content_hash_ok,
        "isolation_ok": isolation_ok,
        "isolation_status": isolation_status,
        "tampering_detected": tampering_detected,
        "clean_run_eligible": not exclusion_reasons and not errors,
        "exclusion_reasons": exclusion_reasons,
        "quarantine": quarantine_summary,
        "record_count": len(records),
        "coverage": {
            "total_problems": len(drill_problem_ids),
            "covered_count": len(covered),
            "covered_problem_ids": covered,
            "uncovered_problem_ids": sorted(drill_problem_ids - set(covered)),
        },
        "missingness_counts": missingness,
        "errors": errors,
        "warnings": warnings,
    }
    return validation, run_dir, run_doc, records, non_iso_errors, isolation_mismatches


def _validate_run_with_data(
    repo_root: Path, run_id: str
) -> tuple[dict[str, Any], Path, dict[str, Any], list[dict[str, Any]]]:
    validation, run_dir, run_doc, records, _, _ = _inspect_run(repo_root, run_id)
    return validation, run_dir, run_doc, records


def validate_run(repo_root: Path, run_id: str) -> dict[str, Any]:
    """Validate run provenance, content hash, isolation, item integrity, and tampering."""
    return _validate_run_with_data(repo_root, run_id)[0]


def _active_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    superseded = {r["supersedes_record_id"] for r in records if isinstance(r.get("supersedes_record_id"), str)}
    return [r for r in records if r.get("record_id") not in superseded], sorted(superseded)


def summarize_run(repo_root: Path, run_id: str, *, write_md: bool = False) -> dict[str, Any]:
    """Produce an answer-free aggregate summary separated by mode, provenance, and contamination."""
    validation, run_dir, run_doc, records = _validate_run_with_data(repo_root, run_id)
    active, superseded_ids = _active_records(records)

    natural = {
        "total_records": 0,
        "eligible_denominator": 0,
        "first_attempt_correct": 0,
        "incorrect": 0,
        "partial": 0,
        "invalid_input": 0,
        "blocked": 0,
        "not_attempted": 0,
        "assisted_corrections": 0,
        "assisted_non_correct": 0,
        "retry_attempts": 0,
    }
    injection = {
        "total_records": 0,
        "planted_true": 0,
        "planted_false": 0,
        "planted_unknown": 0,
        "caught": 0,
        "uncaught": 0,
        "caught_unknown": 0,
        "disputes": {k: 0 for k in DISPUTE_OUTCOMES},
    }
    probe_cohort: dict[str, Any] = {"total_records": 0, "outcomes": {}, "explained_supported": 0}
    retro_cohort: dict[str, Any] = {"total_records": 0, "outcomes": {}}
    excluded = {
        "total_records": 0,
        "planted_unknown": 0,
        "run_contaminated_or_unknown": 0,
        "run_quarantined": 0,
        "run_isolation_unknown": 0,
        "solution_exposed": 0,
        "solution_help_before_submission": 0,
        "help_events_unknown": 0,
    }
    dimensions_summary = {dim: {st: 0 for st in DIMENSION_STATUSES} for dim in DIMENSIONS}

    run_clean = (
        run_doc.get("contamination") == "no"
        and run_doc.get("prior_exposure") in ("none", "visible_only")
        and validation["closure_status"] != "quarantined"
        and validation["isolation_ok"] is True
        and validation["content_hash_ok"]
        and not validation["tampering_detected"]
    )
    mode = run_doc.get("mode")

    for rec in active:
        outcome = rec.get("outcome") if rec.get("outcome") in OUTCOMES else "not_attempted"
        planted, exposure = rec.get("planted"), rec.get("solution_exposure")
        raw_help = rec.get("help_events")
        help_known = isinstance(raw_help, list)
        help_list = raw_help if help_known else []
        has_sol_help = any(isinstance(ev, dict) and ev.get("kind") == "solution" for ev in help_list)
        has_any_help = bool(help_list)

        if isinstance(rec.get("dimensions"), dict):
            for dname, dval in rec["dimensions"].items():
                if dname in dimensions_summary and isinstance(dval, dict) and dval.get("status") in DIMENSION_STATUSES:
                    dimensions_summary[dname][dval["status"]] += 1

        if mode == "fault_injection" or planted is True:
            injection["total_records"] += 1
            injection[
                "planted_true" if planted is True else ("planted_false" if planted is False else "planted_unknown")
            ] += 1
            caught_by = rec.get("caught_by")
            injection[
                "caught"
                if caught_by in ("test", "lint", "typecheck", "reviewer")
                else ("uncaught" if caught_by == "none" else "caught_unknown")
            ] += 1
            disp = rec.get("dispute_outcome", "not_applicable")
            if disp in injection["disputes"]:
                injection["disputes"][disp] += 1
            continue

        if mode == "retrospective":
            retro_cohort["total_records"] += 1
            retro_cohort["outcomes"][outcome] = retro_cohort["outcomes"].get(outcome, 0) + 1
            continue

        probe_obj = rec.get("probe") if isinstance(rec.get("probe"), dict) else None
        is_probe = mode == "transfer_probe" or probe_obj is not None
        probe_exposed = is_probe and (probe_obj is None or probe_obj.get("exposure") not in ("none", "visible_only"))

        is_excluded = False
        for flag, key in (
            (not run_clean, "run_contaminated_or_unknown"),
            (validation["closure_status"] == "quarantined", "run_quarantined"),
            (validation["isolation_status"] == "unknown", "run_isolation_unknown"),
            (planted is None, "planted_unknown"),
            (exposure not in ("none", "visible_only") or probe_exposed, "solution_exposed"),
            (not help_known, "help_events_unknown"),
            (has_sol_help, "solution_help_before_submission"),
        ):
            if flag:
                excluded[key] += 1
                is_excluded = True
        if is_excluded:
            excluded["total_records"] += 1
            continue

        if is_probe:
            probe_cohort["total_records"] += 1
            probe_cohort["outcomes"][outcome] = probe_cohort["outcomes"].get(outcome, 0) + 1
            if probe_obj and probe_obj.get("explanation_status") == "supported":
                probe_cohort["explained_supported"] += 1
            continue

        natural["total_records"] += 1
        att = rec.get("attempt_index") if isinstance(rec.get("attempt_index"), int) else 1
        if outcome in ("blocked", "invalid_input", "not_attempted"):
            natural[outcome] += 1
        elif att == 1 and not has_any_help:
            natural["eligible_denominator"] += 1
            natural["first_attempt_correct" if outcome == "correct" else outcome] += 1
        elif att == 1:
            natural["assisted_corrections" if outcome == "correct" else "assisted_non_correct"] += 1
        else:
            natural["assisted_corrections" if outcome == "correct" else "retry_attempts"] += 1

    summary: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "valid": validation["valid"],
        "closed": validation["closed"],
        "closure_status": validation["closure_status"],
        "isolation_status": validation["isolation_status"],
        "clean_run_eligible": validation["clean_run_eligible"],
        "exclusion_reasons": validation["exclusion_reasons"],
        "warnings": validation["warnings"],
        "quarantine": validation["quarantine"],
        "provenance": {
            "closure_status": validation["closure_status"],
            "started_at": run_doc.get("started_at"),
            "ended_at": run_doc.get("ended_at"),
            "closed_observed_at": run_doc.get("closed_observed_at"),
            **{
                k: run_doc.get(k)
                for k in (
                    "mode",
                    "drill_id",
                    "unit_id",
                    "actor_type",
                    "model_id",
                    "effort",
                    "source_commit",
                    "content_sha256",
                    "prior_exposure",
                    "contamination",
                )
            },
        },
        "integrity": {
            "content_hash_ok": validation["content_hash_ok"],
            "isolation_ok": validation["isolation_ok"],
            "isolation_status": validation["isolation_status"],
            "tampering_detected": validation["tampering_detected"],
            "errors": validation["errors"],
            "warnings": validation["warnings"],
        },
        "coverage": {
            **validation["coverage"],
            "active_record_ids": [r.get("record_id") for r in active],
            "superseded_record_ids": superseded_ids,
        },
        "cohorts": {
            "natural_unassisted": natural,
            "fault_injection": injection,
            "transfer_probe": probe_cohort,
            "retrospective": retro_cohort,
            "excluded_or_unknown": excluded,
        },
        "missingness_counts": validation["missingness_counts"],
        "dimensions_counts": dimensions_summary,
    }
    if write_md and validation["valid"]:
        _ensure_contained(run_dir, run_dir / "summary.md").write_text(
            _format_summary_markdown(summary), encoding="utf-8"
        )
    return summary


def _format_summary_markdown(summary: dict[str, Any]) -> str:
    prov, cov = summary["provenance"], summary["coverage"]
    nat, inj = summary["cohorts"]["natural_unassisted"], summary["cohorts"]["fault_injection"]
    prb, ret, exc = (
        summary["cohorts"]["transfer_probe"],
        summary["cohorts"]["retrospective"],
        summary["cohorts"]["excluded_or_unknown"],
    )
    lines = [
        f"# Pilot Quality Summary: {summary['run_id']}",
        "",
        f"- Valid: `{summary['valid']}` | Closed: `{summary['closed']}` (`{summary['closure_status']}`) | Isolation: `{summary['isolation_status']}` | Clean eligible: `{summary['clean_run_eligible']}`",
        f"- Mode: `{prov['mode']}` | Drill: `{prov['drill_id']}` | Unit: `{prov['unit_id']}`",
        f"- Timestamps: started=`{prov['started_at']}` | ended=`{prov['ended_at']}` | closed_observed=`{prov['closed_observed_at']}`",
        f"- Model: `{prov['model_id']}` | Effort: `{prov['effort']}` | Commit: `{prov['source_commit']}`",
        f"- Content SHA-256: `{prov['content_sha256']}`",
        f"- Contamination: `{prov['contamination']}` | Prior exposure: `{prov['prior_exposure']}`",
        f"- Exclusion reasons: `{summary['exclusion_reasons']}`",
        f"- Coverage: `{cov['covered_count']}/{cov['total_problems']}` problems (uncovered: `{cov['uncovered_problem_ids']}`)",
    ]
    q = summary.get("quarantine")
    if isinstance(q, dict):
        lines.append(
            f"- Quarantine: reason=`{q.get('reason')}` | quarantined_at=`{q.get('quarantined_at')}` | evidence_ref=`{q.get('evidence_ref')}` | mismatches=`{len(q.get('isolation_mismatches') or [])}`"
        )
    lines.extend(
        [
            "",
            "## Cohorts (mutually exclusive)",
            f"- Natural unassisted (`total={nat['total_records']}`): `{nat['first_attempt_correct']}/{nat['eligible_denominator']}` first-attempt correct (assisted_corrections=`{nat['assisted_corrections']}`, assisted_non_correct=`{nat['assisted_non_correct']}`, retry_attempts=`{nat['retry_attempts']}`, blocked=`{nat['blocked']}`, invalid_input=`{nat['invalid_input']}`)",
            f"- Fault injection (`total={inj['total_records']}`): planted_true=`{inj['planted_true']}`, planted_false=`{inj['planted_false']}`, planted_unknown=`{inj['planted_unknown']}`, caught=`{inj['caught']}`, uncaught=`{inj['uncaught']}`",
            f"- Transfer probe (`total={prb['total_records']}`): outcomes=`{prb['outcomes']}`, explained_supported=`{prb['explained_supported']}`",
            f"- Retrospective (`total={ret['total_records']}`): outcomes=`{ret['outcomes']}`",
            f"- Excluded / unknown (`total={exc['total_records']}`): planted_unknown=`{exc['planted_unknown']}`, help_events_unknown=`{exc['help_events_unknown']}`, contaminated_or_unknown=`{exc['run_contaminated_or_unknown']}`, quarantined=`{exc['run_quarantined']}`, isolation_unknown=`{exc['run_isolation_unknown']}`",
            "",
            "## Missingness counts",
            f"- `{summary['missingness_counts']}`",
            "",
        ]
    )
    return "\n".join(lines)


def _parse_kv_pairs(items: list[str] | None) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            raise ValueError(f"Expected FIELD=REASON, got {item!r}")
        k, v = item.split("=", 1)
        if not k.strip() or not v.strip():
            raise ValueError(f"Empty field or reason in {item!r}")
        out[k.strip()] = v.strip()
    return out


def _read_json_input(path_arg: str) -> dict[str, Any]:
    if path_arg == "-":
        raw = sys.stdin.read()
    else:
        p = Path(path_arg)
        if p.is_symlink():
            raise ValueError(f"Symlink input file rejected: {path_arg}")
        raw = p.read_text(encoding="utf-8")
    obj = json.loads(raw)
    if not isinstance(obj, dict):
        raise ValueError("Input JSON must be an object")
    return obj


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pilot exercise-quality collection CLI (isolated, answer-free).")
    parser.add_argument("--repo-root", default=None, help="Repository root (defaults to auto-detected root)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Initialize an isolated quality run under pilot/quality/<run_id>/")
    p_init.add_argument("--run-id", required=True)
    p_init.add_argument("--mode", required=True, choices=MODES)
    p_init.add_argument("--drill-id", required=True)
    p_init.add_argument("--unit-id", default=None)
    p_init.add_argument("--actor-type", default="ai", choices=ACTOR_TYPES)
    p_init.add_argument("--model-id", default=None)
    p_init.add_argument("--effort", default=None)
    p_init.add_argument("--role", default="learner")
    p_init.add_argument("--session-id", default=None)
    p_init.add_argument("--sample-reason", default=None)
    p_init.add_argument("--source-commit", default=None)
    p_init.add_argument(
        "--started-at", default=None, help="External UTC ISO-8601 timestamp (e.g. retrospective import)"
    )
    p_init.add_argument("--ended-at", default=None, help="External UTC ISO-8601 close timestamp (retrospective only)")
    p_init.add_argument("--allowed-material", action="append", dest="allowed_materials", default=None)
    p_init.add_argument("--prior-exposure", default="unknown", choices=EXPOSURE_LEVELS)
    p_init.add_argument("--contamination", default="unknown", choices=CONTAMINATION_STATES)
    p_init.add_argument("--missing-reason", action="append", dest="missing_reasons", default=None)

    p_rec = sub.add_parser("record", help="Validate and append a typed item attempt record to items.jsonl")
    p_rec.add_argument("--run-id", required=True)
    p_rec.add_argument("--input", required=True, help="Path to item attempt JSON file, or '-' for stdin")

    p_fin = sub.add_parser("finish", help="Validate and close an open run by storing end snapshot and ended_at")
    p_fin.add_argument("--run-id", required=True)
    p_fin.add_argument("--ended-at", default=None, help="UTC ISO-8601 close timestamp (defaults to current UTC time)")

    p_quar = sub.add_parser(
        "quarantine",
        aliases=["close-incomplete"],
        help="Close an interrupted open run with protected-path isolation mismatch as quarantined",
    )
    p_quar.add_argument("--run-id", required=True)
    p_quar.add_argument("--reason", required=True, help="Non-empty reason for quarantine/incomplete closeout")
    p_quar.add_argument("--evidence-ref", default=None, help="Optional safe evidence ref whose SHA-256 is captured")
    p_quar.add_argument(
        "--ended-at", default=None, help="UTC ISO-8601 runtime close timestamp (defaults to current UTC time)"
    )

    p_val = sub.add_parser("validate", help="Verify run provenance, content hash, isolation, and tampering")
    p_val.add_argument("--run-id", required=True)

    p_sum = sub.add_parser("summary", help="Output an answer-free aggregate summary for a run")
    p_sum.add_argument("--run-id", required=True)
    p_sum.add_argument("--format", default="json", choices=("json", "md"))
    p_sum.add_argument("--write-md", action="store_true", help="Write summary.md inside pilot/quality/<run_id>/")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root).resolve() if args.repo_root else find_repo_root()
    try:
        if args.command == "init":
            run_doc = init_run(
                repo_root,
                run_id=args.run_id,
                mode=args.mode,
                drill_id=args.drill_id,
                unit_id=args.unit_id,
                actor_type=args.actor_type,
                model_id=args.model_id,
                effort=args.effort,
                role=args.role,
                session_id=args.session_id,
                sample_reason=args.sample_reason,
                source_commit=args.source_commit,
                started_at=args.started_at,
                ended_at=args.ended_at,
                allowed_materials=args.allowed_materials,
                prior_exposure=args.prior_exposure,
                contamination=args.contamination,
                missing_reasons=_parse_kv_pairs(args.missing_reasons),
            )
            print(json.dumps(run_doc, ensure_ascii=False, indent=2))
            return 0
        if args.command == "record":
            rec = record_item(repo_root, run_id=args.run_id, payload=_read_json_input(args.input))
            print(json.dumps({"recorded": rec["record_id"], "run_id": args.run_id}, ensure_ascii=False))
            return 0
        if args.command == "finish":
            run_doc = end_run(repo_root, args.run_id, ended_at=args.ended_at)
            print(
                json.dumps(
                    {
                        "closed": True,
                        "closure_status": run_doc["closure_status"],
                        "run_id": args.run_id,
                        "ended_at": run_doc["ended_at"],
                        "closed_observed_at": run_doc["closed_observed_at"],
                    },
                    ensure_ascii=False,
                )
            )
            return 0
        if args.command in ("quarantine", "close-incomplete"):
            run_doc = quarantine_run(
                repo_root,
                args.run_id,
                reason=args.reason,
                evidence_ref=args.evidence_ref,
                ended_at=args.ended_at,
            )
            print(
                json.dumps(
                    {
                        "closed": True,
                        "closure_status": run_doc["closure_status"],
                        "run_id": args.run_id,
                        "ended_at": run_doc["ended_at"],
                        "closed_observed_at": run_doc["closed_observed_at"],
                        "quarantine": run_doc["quarantine"],
                    },
                    ensure_ascii=False,
                )
            )
            return 0
        if args.command == "validate":
            res = validate_run(repo_root, args.run_id)
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0 if res["valid"] else 1
        if args.command == "summary":
            res = summarize_run(repo_root, args.run_id, write_md=args.write_md)
            print(
                _format_summary_markdown(res) if args.format == "md" else json.dumps(res, ensure_ascii=False, indent=2)
            )
            return 0 if res["valid"] else 1
    except (FileExistsError, FileNotFoundError, ValueError, json.JSONDecodeError, OSError) as exc:
        print(f"pilot_quality: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
