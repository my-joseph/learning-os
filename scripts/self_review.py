"""Read-only self-review auto-signal collector for LearningOS.

Collects deterministic, no-AI improvement signals from:
1. Issue log (``issues/log.jsonl``): recurring ``(target, kind)`` patterns (>= 2),
   open ``proposal`` records, and gate-gaps (explicit ``gate-gap`` or reviewer/learner catches).
2. Agent usage log (``pilot/agent-usage.jsonl``): per-model and per-job-type tokens,
   duration, failed runs (non-zero/non-quota rc), fallbacks, and reopened branches (revisions).
3. Git / GitHub PRs: PRs with "Review fixes" sections and follow-up ``fix`` PRs merged
   within 2 days of a related merge.
4. Drill-quality signals (when local progress exists): archetypes flagged ``too_easy``
   or ``too_hard`` -> target ``content`` (aggregate counts only; zero learner content).
5. Doc-reference checks via ``scripts/doc_refs.py`` (skipped gracefully if absent).

Usage:
    python -m scripts.self_review [--since YYYY-MM-DD] [--compare-at YYYY-MM-DD] [--target TARGET] [--json]
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from progress_store import progress_root
from scripts import issues as issues_mod

_IMPACT_WEIGHT = {"high": 3, "med": 2, "low": 1}
_QUALITY_CATCH_KINDS = frozenset({"wrong-answer", "ambiguity", "context", "leak", "reasoning", "level"})
_REVIEW_FIXES_RE = re.compile(r"(?:^|\n)\s*#{1,6}\s*(?:post-)?review\s+fixes\b|\breview\s+fixes\b", re.IGNORECASE)
_RC_RE = re.compile(r"\brc=(\d+)\b")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

_USAGE_HIGH_TOKENS = 2_000_000
_USAGE_HIGH_DURATION_SECS = 1500.0
_REWORK_WINDOW_HOURS = 48.0
_FALLBACK_WINDOW_SECS = 1800.0
_COMPARE_MIN_RUNS = 5


def _load_addressed(path: str | None = None) -> dict[str, dict[str, Any]]:
    """Load target|kind process resolutions from the optional mapping file."""
    mapping_path = path or os.path.join(Path(__file__).resolve().parent.parent, "docs", "self_review_addressed.json")
    try:
        with open(mapping_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _addressed_footer(addressed: dict[str, dict[str, Any]], observed: set[str]) -> list[dict[str, Any]]:
    return [
        {"key": key, "since": value.get("since"), "pr": value.get("pr"), "note": value.get("note", "")}
        for key, value in sorted(addressed.items())
        if key not in observed
    ]


def _parse_iso_dt(value: str | None) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    raw = value.strip()
    if not raw:
        return None
    # Issue log format: "YYYY-MM-DD HH:MM UTC"
    if raw.endswith(" UTC"):
        try:
            return datetime.strptime(raw, "%Y-%m-%d %H:%M UTC").replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _date_prefix(value: str | None) -> str:
    if not value or not isinstance(value, str):
        return ""
    m = re.match(r"(\d{4}-\d{2}-\d{2})", value.strip())
    return m.group(1) if m else ""


def _after_since(value: str | None, since: str | None) -> bool:
    if not since:
        return True
    prefix = _date_prefix(value)
    if not prefix:
        return True
    return prefix >= since


def infer_target_from_path_or_where(text: str) -> str:
    """Map a file path, drill ID, or issue `where` field to a normalized target."""
    raw = (text or "").strip()
    low = raw.lower()
    skill_m = re.search(r"\.claude/skills/([a-z0-9-]+)", raw)
    if skill_m:
        return f"skill:{skill_m.group(1)}"
    if any(tok in low for tok in ("practice-studio", "studio", "studiosidepanel", "mathfigure")):
        return "studio"
    if any(tok in low for tok in ("math_engine", "code_engine", "quality_rules", "progress_store")):
        return "engine"
    if any(tok in low for tok in ("scripts/", "tools/agents", "notion_sync", "run-worker")):
        return "pipeline"
    if any(
        tok in raw for tok in ("DRL-", "LAB-", "MTH-", "PRG-", "drills/", "labs/", "reasoning_vault", "id_map.json")
    ):
        return "content"
    if any(tok in low for tok in (".github/", ".githooks/", "tests/", "ci.yml", "pytest")):
        return "ci"
    if any(tok in low for tok in ("docs/", "rules/", "claude.md", "agents.md", "gemini.md")):
        return "docs"
    return "pipeline"


def infer_job_type(branch: str) -> str:
    """Extract job type from a branch name like 'fix/foo' or 'content/bar'."""
    cleaned = (branch or "").strip()
    if "/" in cleaned:
        prefix = cleaned.split("/", 1)[0].strip().lower()
        if prefix:
            return prefix
    return "other"


def infer_target_from_branch_and_files(branch: str, files: list[str] | None = None) -> str:
    """Infer target area/skill from PR changed files first, falling back to branch name."""
    if files:
        counts: Counter[str] = Counter()
        for path in files:
            if path.startswith("tests/"):
                continue
            counts[infer_target_from_path_or_where(path)] += 1
        if counts:
            return counts.most_common(1)[0][0]
        return infer_target_from_path_or_where(files[0])
    low = (branch or "").lower()
    if "studio" in low or "ux" in low or "style/" in low:
        return "studio"
    if any(k in low for k in ("engine", "gate", "figure", "vault", "originality", "review-engine", "scoring")):
        return "engine"
    if any(k in low for k in ("drill/", "lab/", "content/", "variant", "prg-examples")):
        return "content"
    if any(k in low for k in ("docs/", "doc-drift", "doc-refs")):
        return "docs"
    if any(k in low for k in ("ci/", "hook", "harness", "test")):
        return "ci"
    if "skill" in low:
        return "skill:improve" if "improve" in low else "docs"
    return "pipeline"


def playbook_for_target(target: str) -> str:
    """Return the recommended skill or playbook to act on proposals for `target`."""
    if target.startswith("skill:"):
        skill_name = target.split(":", 1)[1]
        return f"edit .claude/skills/{skill_name}/SKILL.md"
    if target.startswith(("model:", "job:")):
        return "edit .claude/skills/dispatch-worker/SKILL.md"
    if target.startswith("gate:"):
        return "improve engine"
    mapping = {
        "engine": "improve engine",
        "studio": "improve ux",
        "pipeline": "improve pipeline",
        "content": "improve content",
        "ci": "health-check",
        "docs": "health-check",
    }
    return mapping.get(target, "health-check")


def _target_matches_filter(target: str, filter_target: str | None) -> bool:
    if not filter_target:
        return True
    ft = filter_target.strip().lower()
    t = target.strip().lower()
    if ft == t:
        return True
    # Allow `improve ux` to match `studio` proposals and `improve pipeline` to match dispatch/ci/job/model.
    aliases = {
        "ux": {"studio", "ux"},
        "studio": {"studio", "ux"},
        "pipeline": {"pipeline", "ci", "skill:dispatch-worker"},
        "content": {
            "content",
            "skill:new-math-drill",
            "skill:new-code-drill",
            "skill:new-project",
            "skill:start-unit",
            "skill:synthesize-source",
            "skill:drill-quality",
        },
        "engine": {"engine"},
    }
    allowed = aliases.get(ft)
    if allowed:
        if t in allowed:
            return True
        if ft == "pipeline" and t.startswith(("job:", "model:")):
            return True
        if ft == "engine" and t.startswith("gate:"):
            return True
    return False


def _make_proposal(
    *,
    target: str,
    category: str,
    impact: str,
    evidence_count: int,
    examples: list[str],
    suggested_change: str,
    playbook: str | None = None,
    urgent_bonus: int = 0,
) -> dict[str, Any]:
    weight = _IMPACT_WEIGHT.get(impact, 2)
    score = weight * max(1, evidence_count) + urgent_bonus
    return {
        "target": target,
        "category": category,
        "impact": impact,
        "score": score,
        "evidenceCount": evidence_count,
        "examples": examples[:5],
        "suggestedChange": suggested_change,
        "playbook": playbook or playbook_for_target(target),
    }


def collect_issue_signals(
    *,
    issues_path: str | None = None,
    since: str | None = None,
    include_resolved: bool = False,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Collect open proposals, recurring target+kind patterns, and gate-gaps from issues/log.jsonl."""
    path = issues_path or issues_mod.log_path()
    records = issues_mod.issues(path)
    filtered = [r for r in records if _after_since(r.get("date"), since)]

    open_proposals: list[dict[str, Any]] = []
    by_target_kind: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    gate_gaps_by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    reviewer_catches: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for rec in filtered:
        target = rec.get("target") or infer_target_from_path_or_where(rec.get("where", ""))
        kind = rec.get("kind", "other")
        resolved = bool(rec.get("resolved"))
        if kind == "proposal":
            if not resolved:
                open_proposals.append({**rec, "_target": target})
            continue
        if resolved and not include_resolved:
            continue
        by_target_kind[(target, kind)].append(rec)
        if kind == "gate-gap" and not resolved:
            gate_gaps_by_target[target].append(rec)
        if rec.get("source") in ("reviewer", "learner") and kind in _QUALITY_CATCH_KINDS:
            reviewer_catches[(target, kind)].append(rec)

    proposals: list[dict[str, Any]] = []
    covered_buckets: set[tuple[str, str]] = set()

    # 1. Explicit open proposals
    for rec in open_proposals:
        target = rec["_target"]
        impact = rec.get("impact") or ("high" if rec.get("severity") == "urgent" else "med")
        evidence = rec.get("evidence") or rec.get("where") or ""
        proposal_text = rec.get("proposal") or rec.get("what") or ""
        proposal = _make_proposal(
            target=target,
            category="open-proposal",
            impact=impact,
            evidence_count=1,
            examples=[f"[{rec['id']}] {evidence}"],
            suggested_change=proposal_text,
            urgent_bonus=3 if rec.get("severity") == "urgent" else 1,
        )
        proposal["addressKey"] = f"{target}|proposal"
        proposals.append(proposal)

    # 2. Explicit open gate-gap records
    for target, recs in sorted(gate_gaps_by_target.items()):
        covered_buckets.add((target, "gate-gap"))
        urgent = any(r.get("severity") == "urgent" for r in recs)
        impact = "high" if urgent or len(recs) >= 2 else "med"
        examples = [f"[{r['id']}] {r['where']}: {r['what']}" for r in recs[:5]]
        proposal = _make_proposal(
            target=target,
            category="gate-gap",
            impact=impact,
            evidence_count=len(recs),
            examples=examples,
            suggested_change=(
                f"Gate for {target} missed {len(recs)} issue(s) -> add automated gate check and regression test"
            ),
            urgent_bonus=3 if urgent else 1,
        )
        proposal["addressKey"] = f"{target}|gate-gap"
        proposals.append(proposal)

    # 3. Reviewer / learner catches that gates missed (same target + quality kind >= 2)
    for (target, kind), recs in sorted(reviewer_catches.items()):
        if len(recs) < 2:
            continue
        covered_buckets.add((target, kind))
        sources = sorted({r.get("source", "reviewer") for r in recs})
        source_label = "/".join(sources)
        urgent = any(r.get("severity") == "urgent" for r in recs)
        impact = "high" if urgent or len(recs) >= 3 else "med"
        examples = [f"[{r['id']}] {r['where']}: {r['what']}" for r in recs[:5]]
        proposal = _make_proposal(
            target=target,
            category="gate-gap",
            impact=impact,
            evidence_count=len(recs),
            examples=examples,
            suggested_change=(
                f"Gate for {target} missed {len(recs)} {source_label} catch(es) of kind {kind} "
                f"-> add automated check for {kind}"
            ),
            urgent_bonus=2 if urgent else 0,
        )
        proposal["addressKey"] = f"{target}|{kind}"
        proposals.append(proposal)

    # 4. Recurring (target, kind) >= 2 patterns not already emitted above
    recurring_summary: list[dict[str, Any]] = []
    for (target, kind), recs in sorted(by_target_kind.items()):
        if len(recs) < 2:
            continue
        pending_count = sum(1 for r in recs if not r.get("resolved"))
        recurring_summary.append(
            {
                "target": target,
                "kind": kind,
                "count": len(recs),
                "pending": pending_count,
                "ids": [r["id"] for r in recs],
            }
        )
        if (target, kind) in covered_buckets:
            continue
        urgent = any(r.get("severity") == "urgent" for r in recs)
        impact = "high" if urgent or len(recs) >= 3 else "med"
        playbook = playbook_for_target(target)
        examples = [f"[{r['id']}] {r['where']}: {r['what']}" for r in recs[:5]]
        proposal = _make_proposal(
            target=target,
            category="recurring-issue",
            impact=impact,
            evidence_count=len(recs),
            examples=examples,
            suggested_change=(
                f"Recurring {kind} on {target} ({len(recs)}x, {pending_count} pending) -> fix root cause via {playbook}"
            ),
            playbook=playbook,
            urgent_bonus=2 if urgent else 0,
        )
        proposal["addressKey"] = f"{target}|{kind}"
        proposals.append(proposal)

    signal = {
        "path": path,
        "exists": os.path.isfile(path),
        "totalRecords": len(filtered),
        "pendingRecords": sum(1 for r in filtered if not r.get("resolved")),
        "openProposals": len(open_proposals),
        "recurringPatterns": recurring_summary,
    }
    return signal, proposals


def _parse_outcome_rc(outcome: str) -> int | None:
    m = _RC_RE.search(outcome or "")
    return int(m.group(1)) if m else None


def collect_usage_signals(
    *,
    usage_path: str | None = None,
    since: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Collect token, timing, failure, fallback, and revision signals from pilot/agent-usage.jsonl."""
    path = usage_path or os.path.join(issues_mod.main_checkout_root(), "pilot", "agent-usage.jsonl")
    if not os.path.isfile(path):
        return {
            "path": path,
            "exists": False,
            "runs": 0,
            "byModel": {},
            "byJobType": {},
            "fallbacks": [],
            "reopenedBranches": [],
        }, []

    runs: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(rec, dict):
                continue
            if not _after_since(rec.get("ts"), since):
                continue
            runs.append(rec)

    by_model: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "runs": 0,
            "failedRuns": 0,
            "idleAfterPr": 0,
            "totalTokens": 0,
            "outputTokens": 0,
            "durationSeconds": 0.0,
            "timedRuns": 0,
            "fallbacksOut": 0,
            "failedBranches": [],
        }
    )
    by_job: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "runs": 0,
            "failedRuns": 0,
            "totalTokens": 0,
            "outputTokens": 0,
            "durationSeconds": 0.0,
            "timedRuns": 0,
            "branches": set(),
            "reopenedBranches": [],
            "failedBranches": [],
        }
    )
    by_branch: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for rec in runs:
        model = str(rec.get("model") or "unknown")
        branch = str(rec.get("branch") or "")
        job_type = infer_job_type(branch)
        outcome = str(rec.get("outcome") or "")
        rc = _parse_outcome_rc(outcome)
        idle_pr = "idle-after-pr" in outcome
        # run-worker uses rc=3 for a quota-limit fallback and may stop a run
        # after a PR exists. Neither is a failed implementation attempt.
        failed = rc is not None and rc not in {0, 3} and not idle_pr
        tokens = int(rec.get("total_tokens") or 0)
        out_tokens = int(rec.get("output_tokens") or 0)
        dur = rec.get("duration_seconds")

        m_row = by_model[model]
        m_row["runs"] += 1
        m_row["totalTokens"] += tokens
        m_row["outputTokens"] += out_tokens
        if idle_pr:
            m_row["idleAfterPr"] += 1
        if failed:
            m_row["failedRuns"] += 1
            if branch:
                m_row["failedBranches"].append(f"{branch} ({outcome or 'ERROR'})")
        if isinstance(dur, (int, float)) and dur > 0:
            m_row["durationSeconds"] += float(dur)
            m_row["timedRuns"] += 1

        j_row = by_job[job_type]
        j_row["runs"] += 1
        j_row["totalTokens"] += tokens
        j_row["outputTokens"] += out_tokens
        if branch:
            j_row["branches"].add(branch)
        if failed:
            j_row["failedRuns"] += 1
            if branch:
                j_row["failedBranches"].append(f"{branch} ({model}, {outcome or 'ERROR'})")
        if isinstance(dur, (int, float)) and dur > 0:
            j_row["durationSeconds"] += float(dur)
            j_row["timedRuns"] += 1

        if branch:
            by_branch[branch].append(rec)

    fallbacks: list[dict[str, Any]] = []
    reopened_branches: list[dict[str, Any]] = []

    for branch, branch_runs in sorted(by_branch.items()):
        if len(branch_runs) < 2:
            continue
        ordered = sorted(branch_runs, key=lambda r: str(r.get("ts") or ""))
        job_type = infer_job_type(branch)
        fallback_indices: set[int] = set()

        for idx in range(1, len(ordered)):
            prev = ordered[idx - 1]
            curr = ordered[idx]
            prev_outcome = str(prev.get("outcome") or "")
            prev_rc = _parse_outcome_rc(prev_outcome)
            prev_failed = prev_rc is not None and prev_rc not in {0, 3} and "idle-after-pr" not in prev_outcome
            prev_quota_fallback = prev_rc == 3
            prev_model = str(prev.get("model") or "unknown")
            curr_model = str(curr.get("model") or "unknown")
            dt_prev = _parse_iso_dt(prev.get("ts"))
            dt_curr = _parse_iso_dt(curr.get("ts"))
            close_in_time = (
                dt_prev is not None
                and dt_curr is not None
                and 0 <= (dt_curr - dt_prev).total_seconds() <= _FALLBACK_WINDOW_SECS
            )
            if (
                (prev_failed or prev_quota_fallback)
                and prev_model != curr_model
                and (close_in_time or dt_prev is None or dt_curr is None)
            ):
                fallback_indices.add(idx)
                by_model[prev_model]["fallbacksOut"] += 1
                fallbacks.append(
                    {
                        "branch": branch,
                        "fromModel": prev_model,
                        "toModel": curr_model,
                        "fromOutcome": prev_outcome,
                        "ts": curr.get("ts"),
                    }
                )

        # Revisions / reopened jobs: extra runs beyond quota fallbacks and
        # runner stops after a PR already exists.
        post_pr_stops = sum("idle-after-pr" in str(r.get("outcome") or "") for r in ordered)
        revisions = max(0, len(ordered) - 1 - len(fallback_indices) - post_pr_stops)
        if revisions >= 1:
            info = {
                "branch": branch,
                "jobType": job_type,
                "runs": len(ordered),
                "revisions": revisions,
                "models": [str(r.get("model") or "unknown") for r in ordered],
            }
            reopened_branches.append(info)
            by_job[job_type]["reopenedBranches"].append(info)

    proposals: list[dict[str, Any]] = []

    # Model failure & fallback proposals
    for model, stats in sorted(by_model.items()):
        runs_n = stats["runs"]
        fails = stats["failedRuns"]
        fail_rate = fails / runs_n if runs_n else 0.0
        if fails >= 2 and fail_rate >= 0.2:
            impact = "high" if fail_rate >= 0.4 or fails >= 4 else "med"
            proposals.append(
                _make_proposal(
                    target=f"model:{model}",
                    category="usage-failure",
                    impact=impact,
                    evidence_count=fails,
                    examples=stats["failedBranches"][:5],
                    suggested_change=(
                        f"Model {model} failed {fails}/{runs_n} runs ({fail_rate:.0%}) "
                        f"-> adjust routing/fallback order or narrow job specs in dispatch-worker"
                    ),
                )
            )
        if stats["fallbacksOut"] >= 2:
            fb_examples = [
                f"{fb['branch']}: {fb['fromModel']} -> {fb['toModel']}" for fb in fallbacks if fb["fromModel"] == model
            ]
            proposals.append(
                _make_proposal(
                    target=f"model:{model}",
                    category="usage-fallback",
                    impact="med",
                    evidence_count=stats["fallbacksOut"],
                    examples=fb_examples[:5],
                    suggested_change=(
                        f"Model {model} triggered {stats['fallbacksOut']} fallback(s) "
                        f"-> spread parallel jobs across quota pools in dispatch-worker"
                    ),
                )
            )

    # Job-type revision (reopened branch) and cost proposals
    for job_type, stats in sorted(by_job.items()):
        reopened = stats["reopenedBranches"]
        if len(reopened) >= 2 or sum(r["revisions"] for r in reopened) >= 2:
            rev_total = sum(r["revisions"] for r in reopened)
            examples = [f"{r['branch']} ({r['runs']} runs, +{r['revisions']} rev)" for r in reopened[:5]]
            proposals.append(
                _make_proposal(
                    target=f"job:{job_type}",
                    category="usage-rework",
                    impact="high" if rev_total >= 4 else "med",
                    evidence_count=rev_total,
                    examples=examples,
                    suggested_change=(
                        f"Job type '{job_type}' had {rev_total} revision run(s) across {len(reopened)} reopened branch(es) "
                        f"-> tighten pre-PR checks and acceptance criteria in dispatch-worker"
                    ),
                )
            )
        runs_n = stats["runs"]
        avg_tokens = stats["totalTokens"] / runs_n if runs_n else 0.0
        avg_dur = stats["durationSeconds"] / stats["timedRuns"] if stats["timedRuns"] else 0.0
        if runs_n >= 2 and (avg_tokens >= _USAGE_HIGH_TOKENS or avg_dur >= _USAGE_HIGH_DURATION_SECS):
            parts = []
            if avg_tokens >= _USAGE_HIGH_TOKENS:
                parts.append(f"avg {avg_tokens / 1_000_000:.2f}M tokens/run")
            if avg_dur >= _USAGE_HIGH_DURATION_SECS:
                parts.append(f"avg {avg_dur / 60:.1f} min/run")
            proposals.append(
                _make_proposal(
                    target=f"job:{job_type}",
                    category="usage-cost",
                    impact="low" if avg_tokens < 4_000_000 and avg_dur < 2400 else "med",
                    evidence_count=runs_n,
                    examples=[f"{job_type}: {runs_n} runs, {', '.join(parts)}"],
                    suggested_change=(
                        f"Job type '{job_type}' is expensive ({', '.join(parts)}) "
                        f"-> split large jobs into smaller specs or route simpler slices to a lighter model"
                    ),
                )
            )

    by_model_out = {
        m: {
            "runs": s["runs"],
            "failedRuns": s["failedRuns"],
            "idleAfterPr": s["idleAfterPr"],
            "fallbacksOut": s["fallbacksOut"],
            "totalTokens": s["totalTokens"],
            "avgTokens": round(s["totalTokens"] / s["runs"]) if s["runs"] else 0,
            "avgDurationSeconds": round(s["durationSeconds"] / s["timedRuns"], 1) if s["timedRuns"] else None,
        }
        for m, s in sorted(by_model.items())
    }
    by_job_out = {
        j: {
            "runs": s["runs"],
            "failedRuns": s["failedRuns"],
            "branches": len(s["branches"]),
            "reopenedBranches": len(s["reopenedBranches"]),
            "totalTokens": s["totalTokens"],
            "avgTokens": round(s["totalTokens"] / s["runs"]) if s["runs"] else 0,
            "avgDurationSeconds": round(s["durationSeconds"] / s["timedRuns"], 1) if s["timedRuns"] else None,
        }
        for j, s in sorted(by_job.items())
    }
    signal = {
        "path": path,
        "exists": True,
        "runs": len(runs),
        "byModel": by_model_out,
        "byJobType": by_job_out,
        "fallbacks": fallbacks,
        "reopenedBranches": reopened_branches,
    }
    return signal, proposals


def _read_jsonl(path: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(rec, dict):
                    records.append(rec)
    except OSError:
        pass
    return records


def _percent_delta(before: float | int | None, after: float | int | None) -> float | None:
    if before is None or after is None:
        return None
    if before == 0:
        return 0.0 if after == 0 else None
    return round((after - before) / before * 100, 1)


def _usage_window_stats(records: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    branches: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rec in records:
        branch = str(rec.get("branch") or "")
        model = str(rec.get("model") or "unknown")
        job = infer_job_type(branch)
        for key, val in ((f"model:{model}", rec), (f"job:{job}", rec)):
            groups[key].append(val)
        if branch:
            branches[branch].append(rec)

    fallback_count: Counter[str] = Counter()
    revisions: Counter[str] = Counter()
    branch_count: Counter[str] = Counter()
    for branch, runs in branches.items():
        ordered = sorted(runs, key=lambda r: str(r.get("ts") or ""))
        fallback_indexes: set[int] = set()
        for idx in range(1, len(ordered)):
            prev, curr = ordered[idx - 1], ordered[idx]
            prev_outcome = str(prev.get("outcome") or "")
            rc = _parse_outcome_rc(prev_outcome)
            is_fallback_run = rc == 3 or (rc is not None and rc not in {0, 3} and "idle-after-pr" not in prev_outcome)
            prev_dt, curr_dt = _parse_iso_dt(prev.get("ts")), _parse_iso_dt(curr.get("ts"))
            close_in_time = (
                prev_dt is not None
                and curr_dt is not None
                and 0 <= (curr_dt - prev_dt).total_seconds() <= _FALLBACK_WINDOW_SECS
            )
            if (
                is_fallback_run
                and str(prev.get("model") or "unknown") != str(curr.get("model") or "unknown")
                and (close_in_time or prev_dt is None or curr_dt is None)
            ):
                fallback_indexes.add(idx)
                fallback_count[f"model:{prev.get('model') or 'unknown'}"] += 1
                fallback_count[f"job:{infer_job_type(branch)}"] += 1
        for key in (f"job:{infer_job_type(branch)}",):
            branch_count[key] += 1
            stop_count = sum("idle-after-pr" in str(r.get("outcome") or "") for r in ordered)
            revisions[key] += max(0, len(ordered) - 1 - len(fallback_indexes) - stop_count)
        for model in {str(r.get("model") or "unknown") for r in ordered}:
            key = f"model:{model}"
            branch_count[key] += 1
            model_runs = [r for r in ordered if str(r.get("model") or "unknown") == model]
            revisions[key] += max(0, len(model_runs) - 1)

    result: dict[str, Any] = {}
    for key, rows in sorted(groups.items()):
        n = len(rows)
        timed = [
            float(r["duration_seconds"])
            for r in rows
            if isinstance(r.get("duration_seconds"), (int, float)) and r["duration_seconds"] > 0
        ]
        failed = sum((_parse_outcome_rc(str(r.get("outcome") or "")) not in (None, 0, 3)) for r in rows)
        result[key] = {
            "runs": n,
            "avgTokensPerRun": round(sum(int(r.get("total_tokens") or 0) for r in rows) / n, 1) if n else None,
            "avgMinutesPerRun": round(sum(timed) / len(timed) / 60, 2) if timed else None,
            "revisionRate": round(revisions[key] / branch_count[key], 4) if branch_count[key] else 0.0,
            "fallbackRate": round(fallback_count[key] / n, 4) if n else 0.0,
            "failureRate": round(failed / n, 4) if n else 0.0,
        }
    return result


def collect_compare_metrics(
    *,
    usage_path: str,
    compare_at: str,
    prs: list[dict[str, Any]] | None = None,
    followup_prs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compare worker usage and follow-up PRs across a date boundary."""
    rows = _read_jsonl(usage_path)
    before_rows = [r for r in rows if _date_prefix(r.get("ts")) and _date_prefix(r.get("ts")) < compare_at]
    after_rows = [r for r in rows if _date_prefix(r.get("ts")) and _date_prefix(r.get("ts")) >= compare_at]
    before, after = _usage_window_stats(before_rows), _usage_window_stats(after_rows)
    comparison: dict[str, Any] = {}
    for group in sorted(set(before) | set(after)):
        b, a = before.get(group, {}), after.get(group, {})
        metrics: dict[str, Any] = {}
        for name in ("runs", "avgTokensPerRun", "avgMinutesPerRun", "revisionRate", "fallbackRate", "failureRate"):
            bv, av = b.get(name, 0 if name == "runs" else None), a.get(name, 0 if name == "runs" else None)
            metrics[name] = {"before": bv, "after": av, "deltaPercent": _percent_delta(bv, av)}
        metrics["insufficientData"] = a.get("runs", 0) < _COMPARE_MIN_RUNS
        comparison[group] = metrics

    # Count only follow-up fixes already identified against a preceding merged PR.
    if followup_prs is None:
        followup_signal, _, _ = collect_git_gh_signals(repo_root=".", prs=prs or [], use_gh=False)
        followup_rows = followup_signal["followupFixPrs"]
    else:
        followup_rows = followup_prs
    bcount = sum(1 for p in followup_rows if (_date_prefix(p.get("mergedAt")) or "") < compare_at)
    acount = sum(1 for p in followup_rows if (_date_prefix(p.get("mergedAt")) or "") >= compare_at)
    return {
        "compareAt": compare_at,
        "usage": comparison,
        "followupFixPrs": {
            "before": bcount,
            "after": acount,
            "deltaPercent": _percent_delta(bcount, acount),
            "insufficientData": False,
        },
    }


def _fetch_gh_merged_prs(repo_root: str, limit: int = 50) -> tuple[list[dict[str, Any]] | None, str | None]:
    """Query merged PR metadata read-only via `gh pr list`. Returns (prs, skip_reason)."""
    try:
        proc = subprocess.run(
            [
                "gh",
                "pr",
                "list",
                "--state",
                "merged",
                "--base",
                "main",
                "--limit",
                str(limit),
                "--json",
                "number,title,body,mergedAt,headRefName,files",
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
        return None, f"gh unavailable ({exc})"
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip().splitlines()
        return None, f"gh pr list failed ({err[0] if err else f'rc={proc.returncode}'})"
    try:
        data = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError as exc:
        return None, f"gh returned invalid JSON ({exc})"
    return data if isinstance(data, list) else [], None


def _is_fix_pr(pr: dict[str, Any]) -> bool:
    title = str(pr.get("title") or "").strip().lower()
    branch = str(pr.get("headRefName") or "").strip().lower()
    return branch.startswith("fix/") or title.startswith("fix:") or title.startswith("fix(") or "hotfix" in branch


def _pr_file_paths(pr: dict[str, Any]) -> list[str]:
    files = pr.get("files") or []
    out: list[str] = []
    for item in files:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, dict) and item.get("path"):
            out.append(str(item["path"]))
    return out


def collect_git_gh_signals(
    *,
    repo_root: str,
    since: str | None = None,
    prs: list[dict[str, Any]] | None = None,
    use_gh: bool = True,
) -> tuple[dict[str, Any], list[dict[str, Any]], str | None]:
    """Detect PRs with 'Review fixes' sections and follow-up fix PRs merged within 2 days."""
    skip_reason: str | None = None
    if prs is None:
        if not use_gh:
            return (
                {"source": "disabled", "prsScanned": 0, "reviewFixPrs": [], "followupFixPrs": []},
                [],
                "gh skipped (--no-gh)",
            )
        fetched, skip_reason = _fetch_gh_merged_prs(repo_root)
        if fetched is None:
            return {"source": "skipped", "prsScanned": 0, "reviewFixPrs": [], "followupFixPrs": []}, [], skip_reason
        prs = fetched

    filtered: list[dict[str, Any]] = []
    for pr in prs:
        if not isinstance(pr, dict):
            continue
        if not _after_since(pr.get("mergedAt"), since):
            continue
        filtered.append(pr)

    # Sort chronologically by mergedAt for 48h follow-up detection
    def _sort_dt(pr: dict[str, Any]) -> datetime:
        return _parse_iso_dt(pr.get("mergedAt")) or datetime.min.replace(tzinfo=timezone.utc)

    ordered = sorted(filtered, key=_sort_dt)
    review_fix_prs: list[dict[str, Any]] = []
    followup_fix_prs: list[dict[str, Any]] = []
    rework_by_target: dict[str, list[str]] = defaultdict(list)

    for idx, pr in enumerate(ordered):
        num = pr.get("number")
        title = str(pr.get("title") or "")
        body = str(pr.get("body") or "")
        branch = str(pr.get("headRefName") or "")
        files = _pr_file_paths(pr)
        target = infer_target_from_branch_and_files(branch, files)

        if _REVIEW_FIXES_RE.search(body):
            entry = {"number": num, "title": title, "branch": branch, "target": target, "mergedAt": pr.get("mergedAt")}
            review_fix_prs.append(entry)
            rework_by_target[target].append(f"PR #{num} (review fixes): {title}")

        if _is_fix_pr(pr):
            dt_curr = _parse_iso_dt(pr.get("mergedAt"))
            if dt_curr is None:
                continue
            curr_files = set(files)
            matched_prior: dict[str, Any] | None = None
            for prev in reversed(ordered[:idx]):
                dt_prev = _parse_iso_dt(prev.get("mergedAt"))
                if dt_prev is None:
                    continue
                delta = dt_curr - dt_prev
                if delta > timedelta(hours=_REWORK_WINDOW_HOURS):
                    break
                if delta.total_seconds() < 0:
                    continue
                prev_files = set(_pr_file_paths(prev))
                prev_target = infer_target_from_branch_and_files(str(prev.get("headRefName") or ""), list(prev_files))
                overlap = bool(curr_files & prev_files) if (curr_files and prev_files) else (prev_target == target)
                if overlap:
                    matched_prior = prev
                    break
            if matched_prior is not None:
                prev_num = matched_prior.get("number")
                entry = {
                    "number": num,
                    "title": title,
                    "branch": branch,
                    "target": target,
                    "afterPr": prev_num,
                    "mergedAt": pr.get("mergedAt"),
                }
                followup_fix_prs.append(entry)
                rework_by_target[target].append(f"PR #{num} (fix <=48h after #{prev_num}): {title}")

    proposals: list[dict[str, Any]] = []
    for target, examples in sorted(rework_by_target.items()):
        # Deduplicate if one PR triggered both review-fixes and follow-up
        unique_examples = list(dict.fromkeys(examples))
        count = len(unique_examples)
        impact = "high" if count >= 3 else "med"
        playbook = playbook_for_target(target)
        proposals.append(
            _make_proposal(
                target=target,
                category="pr-rework",
                impact=impact,
                evidence_count=count,
                examples=unique_examples[:5],
                suggested_change=(
                    f"{count} PR rework signal(s) in {target} (review fixes or <=48h follow-up fix PRs) "
                    f"-> strengthen pre-PR gates/checklist via {playbook}"
                ),
                playbook=playbook,
            )
        )

    signal = {
        "source": "gh",
        "prsScanned": len(ordered),
        "reviewFixPrs": review_fix_prs,
        "followupFixPrs": followup_fix_prs,
    }
    return signal, proposals, skip_reason


def collect_drill_quality_signals(
    *,
    repo_root: str,
) -> tuple[dict[str, Any], list[dict[str, Any]], str | None]:
    """Collect aggregate too_easy / too_hard archetype flags when local progress exists (zero-leak)."""
    prog_dir = progress_root(repo_root)
    if not os.path.isdir(prog_dir):
        return {"progressDir": prog_dir, "unitsChecked": 0, "tooEasy": [], "tooHard": []}, [], "no progress directory"

    prog_ids: set[str] = set()
    for path in glob.glob(os.path.join(prog_dir, "*.json")):
        base = os.path.basename(path)
        if base.startswith("_"):
            continue
        try:
            with open(path, "r", encoding="utf-8") as fh:
                rec = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(rec, dict) and rec.get("drillId"):
            prog_ids.add(str(rec["drillId"]))

    if not prog_ids:
        return {"progressDir": prog_dir, "unitsChecked": 0, "tooEasy": [], "tooHard": []}, [], "no drill progress files"

    data_root = os.environ.get("DRILLS_DATA_DIR", os.path.join(repo_root, "drills", "data"))
    scopes: set[str] = set()
    for path in glob.glob(os.path.join(data_root, "*", "*.json")):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        if str(doc.get("drillId") or "") in prog_ids and doc.get("unitCode"):
            scopes.add(str(doc["unitCode"]))

    if not scopes:
        return (
            {"progressDir": prog_dir, "unitsChecked": 0, "tooEasy": [], "tooHard": []},
            [],
            "no drills match progress",
        )

    from scripts import drill_quality as dq

    too_easy: list[str] = []
    too_hard: list[str] = []
    for scope in sorted(scopes):
        report = dq.build_report(scope, repo_root=repo_root)
        for flag in report.get("flags", []):
            ftype = flag.get("type")
            arch = flag.get("archetype")
            lvl = flag.get("level")
            if ftype == "too_easy" and arch:
                too_easy.append(f"{scope}/{arch}@L{lvl}")
            elif ftype == "too_hard" and arch:
                too_hard.append(f"{scope}/{arch}@L{lvl}")

    proposals: list[dict[str, Any]] = []
    if too_hard:
        proposals.append(
            _make_proposal(
                target="content",
                category="drill-quality",
                impact="high" if len(too_hard) >= 2 else "med",
                evidence_count=len(too_hard),
                examples=too_hard[:5],
                suggested_change=(
                    f"{len(too_hard)} archetype/level(s) flagged too_hard (<=30% first-try clean over >=3 items) "
                    f"-> add scaffolding or lower level via drill-quality / improve content"
                ),
                playbook="improve content",
            )
        )
    if too_easy:
        proposals.append(
            _make_proposal(
                target="content",
                category="drill-quality",
                impact="med" if len(too_easy) >= 2 else "low",
                evidence_count=len(too_easy),
                examples=too_easy[:5],
                suggested_change=(
                    f"{len(too_easy)} archetype/level(s) flagged too_easy (>=90% first-try clean over >=3 items) "
                    f"-> step up level or add harder variants via drill-quality / improve content"
                ),
                playbook="improve content",
            )
        )

    signal = {
        "progressDir": prog_dir,
        "unitsChecked": len(scopes),
        "tooEasy": too_easy,
        "tooHard": too_hard,
    }
    return signal, proposals, None


def collect_doc_refs_signals(
    *,
    repo_root: str,
    python_exe: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], str | None]:
    """Run scripts.doc_refs.check_doc_files if scripts/doc_refs.py exists; skip gracefully otherwise."""
    root_path = Path(repo_root).resolve()
    doc_refs_file = root_path / "scripts" / "doc_refs.py"
    if not doc_refs_file.is_file():
        return {"available": False, "count": 0, "issues": []}, [], "scripts/doc_refs.py not found"

    try:
        from scripts import doc_refs as dr
    except ImportError as exc:
        return {"available": False, "count": 0, "issues": []}, [], f"scripts.doc_refs import failed ({exc})"

    doc_issues = dr.check_doc_files(root_path, python_exe=python_exe or sys.executable)
    by_target: dict[str, list[str]] = defaultdict(list)
    for item in doc_issues:
        target = infer_target_from_path_or_where(item.file)
        if not target.startswith("skill:"):
            target = "docs"
        by_target[target].append(item.format_line())

    proposals: list[dict[str, Any]] = []
    for target, lines in sorted(by_target.items()):
        playbook = playbook_for_target(target)
        proposals.append(
            _make_proposal(
                target=target,
                category="doc-refs",
                impact="high" if len(lines) >= 3 else "med",
                evidence_count=len(lines),
                examples=lines[:5],
                suggested_change=(
                    f"{len(lines)} broken doc reference(s) in {target} -> repair stale paths/flags from scripts.doc_refs"
                ),
                playbook=playbook,
            )
        )

    signal = {
        "available": True,
        "count": len(doc_issues),
        "issues": [i.to_dict() for i in doc_issues],
    }
    return signal, proposals, None


def build_self_review(
    *,
    repo_root: str | None = None,
    issues_path: str | None = None,
    usage_path: str | None = None,
    since: str | None = None,
    compare_at: str | None = None,
    addressed_path: str | None = None,
    target: str | None = None,
    prs: list[dict[str, Any]] | None = None,
    use_gh: bool = True,
    no_progress: bool = False,
    python_exe: str | None = None,
) -> dict[str, Any]:
    """Run all read-only auto-signal collectors and return ranked improvement proposals."""
    if since and not _ISO_DATE_RE.fullmatch(since):
        raise ValueError(f"--since must be YYYY-MM-DD, got {since!r}")
    if compare_at and not _ISO_DATE_RE.fullmatch(compare_at):
        raise ValueError(f"--compare-at must be YYYY-MM-DD, got {compare_at!r}")

    root = os.path.abspath(repo_root or str(Path(__file__).resolve().parent.parent))
    effective_usage_path = usage_path or os.path.join(root, "pilot", "agent-usage.jsonl")
    addressed = _load_addressed(addressed_path)
    if compare_at is None and addressed:
        compare_at = max(str(v.get("since")) for v in addressed.values() if v.get("since"))
    if compare_at is None:
        compare_at = datetime.now(timezone.utc).date().isoformat()
    skipped: list[str] = []
    all_proposals: list[dict[str, Any]] = []

    issue_sig, issue_props = collect_issue_signals(issues_path=issues_path, since=since)
    all_proposals.extend(issue_props)
    if not issue_sig["exists"]:
        skipped.append(f"issues: log not found at {issue_sig['path']}")

    usage_sig, usage_props = collect_usage_signals(usage_path=effective_usage_path, since=since)
    all_proposals.extend(usage_props)
    if not usage_sig["exists"]:
        skipped.append(f"usage: file not found at {usage_sig['path']}")

    gh_sig, gh_props, gh_skip = collect_git_gh_signals(repo_root=root, since=since, prs=prs, use_gh=use_gh)
    all_proposals.extend(gh_props)
    if gh_skip:
        skipped.append(f"git/gh: {gh_skip}")

    # Resolved issue notes naming a PR and the explicit mapping are both durable
    # resolution records. Refresh matching proposals using only post-resolution evidence.
    resolved: dict[str, dict[str, Any]] = dict(addressed)
    for rec in issues_mod.issues(issues_path or issues_mod.log_path()):
        note = str(rec.get("resolved") or "")
        match = re.search(r"(\d{4}-\d{2}-\d{2}).*?(?:PR\s*#?)(\d+)", note, re.IGNORECASE)
        if match:
            key = f"{rec.get('target') or infer_target_from_path_or_where(rec.get('where', ''))}|{rec.get('kind', 'other')}"
            resolved.setdefault(key, {"since": match.group(1), "pr": int(match.group(2)), "note": note})

    addressed_footer: list[dict[str, Any]] = []
    kept_proposals: list[dict[str, Any]] = []
    observed_addressed: set[str] = set()
    usage_addressed_cache: dict[str, list[dict[str, Any]]] = {}
    for prop in all_proposals:
        key = prop.get("addressKey", f"{prop['target']}|{prop['category']}")
        resolution = resolved.get(key)
        if not resolution:
            kept_proposals.append(prop)
            continue
        cutoff = str(resolution.get("since") or "0000-00-00")
        if prop["category"].startswith("usage-"):
            target_prefix, target_name = prop["target"].split(":", 1)
            usage_rows = _read_jsonl(effective_usage_path)
            has_new_evidence = any(
                (_date_prefix(r.get("ts")) or "") >= cutoff
                and (
                    (target_prefix == "job" and infer_job_type(str(r.get("branch") or "")) == target_name)
                    or (target_prefix == "model" and str(r.get("model") or "unknown") == target_name)
                )
                for r in usage_rows
            )
            if has_new_evidence:
                observed_addressed.add(key)
            if cutoff not in usage_addressed_cache:
                _, fresh = collect_usage_signals(usage_path=effective_usage_path, since=cutoff)
                usage_addressed_cache[cutoff] = fresh
            fresh = next(
                (
                    p
                    for p in usage_addressed_cache[cutoff]
                    if p["target"] == prop["target"] and p["category"] == prop["category"]
                ),
                None,
            )
            if fresh:
                kept_proposals.append(fresh)
            continue
        # For issue-derived keys, only post-resolution issue evidence is active.
        issue_kind = key.split("|", 1)[1]
        raw_issue_records = issues_mod.issues(issues_path or issues_mod.log_path())
        if any(
            not rec.get("resolved")
            and rec.get("kind") == issue_kind
            and (rec.get("target") or infer_target_from_path_or_where(rec.get("where", ""))) == prop["target"]
            and _after_since(rec.get("date"), cutoff)
            for rec in raw_issue_records
        ):
            observed_addressed.add(key)
        _, fresh_issues = collect_issue_signals(issues_path=issues_path, since=cutoff)
        fresh_issue = next(
            (p for p in fresh_issues if p.get("addressKey", f"{p['target']}|{p['category']}") == key),
            None,
        )
        if fresh_issue:
            kept_proposals.append(fresh_issue)
    all_proposals = kept_proposals
    addressed_footer = _addressed_footer(resolved, observed_addressed)

    compare_sig = collect_compare_metrics(
        usage_path=effective_usage_path,
        compare_at=compare_at,
        prs=prs,
        followup_prs=gh_sig.get("followupFixPrs", []),
    )

    if no_progress:
        dq_sig = {"unitsChecked": 0, "tooEasy": [], "tooHard": []}
        skipped.append("drill-quality: skipped (--no-progress)")
    else:
        dq_sig, dq_props, dq_skip = collect_drill_quality_signals(repo_root=root)
        all_proposals.extend(dq_props)
        if dq_skip:
            skipped.append(f"drill-quality: {dq_skip}")

    doc_sig, doc_props, doc_skip = collect_doc_refs_signals(repo_root=root, python_exe=python_exe)
    all_proposals.extend(doc_props)
    if doc_skip:
        skipped.append(f"doc-refs: {doc_skip}")

    if target:
        all_proposals = [p for p in all_proposals if _target_matches_filter(p["target"], target)]

    all_proposals.sort(
        key=lambda p: (
            -p["score"],
            -_IMPACT_WEIGHT.get(p["impact"], 2),
            -p["evidenceCount"],
            p["target"],
            p["category"],
            p["suggestedChange"],
        )
    )

    return {
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "since": since,
        "compareAt": compare_at,
        "targetFilter": target,
        "proposals": all_proposals,
        "addressed": addressed_footer,
        "comparison": compare_sig,
        "signals": {
            "issues": issue_sig,
            "usage": usage_sig,
            "gitGh": gh_sig,
            "drillQuality": dq_sig,
            "docRefs": doc_sig,
        },
        "skipped": skipped,
    }


def _format_compare_value(value: Any, *, is_rate: bool = False) -> str:
    if value is None:
        return "n/a"
    return f"{value:.1%}" if is_rate else str(value)


def format_self_review(report: dict[str, Any], *, limit: int = 20) -> str:
    """Format ranked improvement proposals as concise human-readable text."""
    since_label = f" (since {report['since']})" if report.get("since") else ""
    target_label = f" [target={report['targetFilter']}]" if report.get("targetFilter") else ""
    proposals = report.get("proposals") or []
    lines = [f"Self-Review Auto-Signals{since_label}{target_label} — {len(proposals)} proposal(s)"]

    sigs = report.get("signals", {})
    iss = sigs.get("issues", {})
    usg = sigs.get("usage", {})
    gh = sigs.get("gitGh", {})
    dq = sigs.get("drillQuality", {})
    dr = sigs.get("docRefs", {})
    lines.append(
        "Sources: "
        f"issues={iss.get('totalRecords', 0)} ({iss.get('openProposals', 0)} open proposals), "
        f"usage_runs={usg.get('runs', 0)} ({len(usg.get('fallbacks', []))} fallbacks, "
        f"{len(usg.get('reopenedBranches', []))} reopened), "
        f"prs={gh.get('prsScanned', 0)} ({len(gh.get('reviewFixPrs', []))} review-fix, "
        f"{len(gh.get('followupFixPrs', []))} <=48h fix), "
        f"drill_units={dq.get('unitsChecked', 0)}, "
        f"doc_refs_broken={dr.get('count', 0)}"
    )
    if report.get("skipped"):
        lines.append("Skipped: " + "; ".join(report["skipped"]))

    comparison = report.get("comparison", {})
    lines.append(f"\nBefore/after usage comparison (boundary {comparison.get('compareAt', 'unknown')}):")
    lines.append("Group | Metric | Before | After | Delta")
    for group, metrics in comparison.get("usage", {}).items():
        for metric, label in (
            ("runs", "runs"),
            ("avgTokensPerRun", "avg tokens/run"),
            ("avgMinutesPerRun", "avg minutes/run"),
            ("revisionRate", "revision rate"),
            ("fallbackRate", "fallback rate"),
            ("failureRate", "failure rate"),
        ):
            item = metrics[metric]
            delta = item.get("deltaPercent")
            delta_text = (
                "n/a" if delta is None else f"{'↑' if delta > 0 else '↓' if delta < 0 else '→'} {abs(delta):.1f}%"
            )
            is_rate = metric in {"revisionRate", "fallbackRate", "failureRate"}
            b = _format_compare_value(item.get("before"), is_rate=is_rate)
            a = _format_compare_value(item.get("after"), is_rate=is_rate)
            suffix = " (insufficient data)" if metrics.get("insufficientData") else ""
            lines.append(f"{group} | {label} | {b} | {a} | {delta_text}{suffix}")
    pr_metrics = comparison.get("followupFixPrs", {})
    pr_delta = pr_metrics.get("deltaPercent")
    pr_delta_text = (
        "n/a" if pr_delta is None else f"{'↑' if pr_delta > 0 else '↓' if pr_delta < 0 else '→'} {abs(pr_delta):.1f}%"
    )
    pr_before = _format_compare_value(pr_metrics.get("before", 0))
    pr_after = _format_compare_value(pr_metrics.get("after", 0))
    lines.append(f"PR follow-up fix PRs (within 48h) | {pr_before} | {pr_after} | {pr_delta_text}")

    if not proposals:
        lines.append("\nNo improvement proposals found.")
        if report.get("addressed"):
            lines.append("\nAddressed (no newer evidence):")
            lines.extend(f"- {row['key']} — PR #{row['pr']} ({row['since']})" for row in report["addressed"])
        return "\n".join(lines)

    lines.append("\nRanked improvement proposals:")
    shown = proposals[:limit] if limit > 0 else proposals
    for idx, prop in enumerate(shown, 1):
        lines.append(
            f"{idx}. [{prop['impact'].upper()}] {prop['target']} ({prop['category']}, "
            f"evidence={prop['evidenceCount']}, score={prop['score']}) -> {prop['playbook']}"
        )
        lines.append(f"   Change: {prop['suggestedChange']}")
        for ex in prop.get("examples", [])[:3]:
            lines.append(f"   - {ex}")
    if limit > 0 and len(proposals) > limit:
        lines.append(f"... {len(proposals) - limit} more; pass --limit 0 or --json to view all.")
    if report.get("addressed"):
        lines.append("\nAddressed (no newer evidence):")
        lines.extend(f"- {row['key']} — PR #{row['pr']} ({row['since']})" for row in report["addressed"])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python -m scripts.self_review",
        description="Read-only self-review auto-signal collector and proposal ranker.",
    )
    ap.add_argument("--since", default=None, help="only include dated signals on or after YYYY-MM-DD")
    ap.add_argument("--compare-at", default=None, help="compare before/after usage windows at YYYY-MM-DD")
    ap.add_argument(
        "--target",
        default=None,
        help="filter proposals to a target skill or area (e.g. engine, ux, skill:health-check)",
    )
    ap.add_argument("--limit", type=int, default=20, help="max proposals to print in text mode (0 = all)")
    ap.add_argument("--no-progress", action="store_true", help="skip progress-derived drill-quality signals")
    ap.add_argument("--no-gh", action="store_true", help="skip calling `gh pr list`")
    ap.add_argument("--json", action="store_true", help="emit full structured report as JSON")
    args = ap.parse_args(argv)

    try:
        report = build_self_review(
            since=args.since,
            compare_at=args.compare_at,
            target=args.target,
            use_gh=not args.no_gh,
            no_progress=args.no_progress,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_self_review(report, limit=args.limit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
