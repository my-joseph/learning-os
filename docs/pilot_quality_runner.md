# Pilot Quality Collection Runner (`scripts/pilot_quality.py`)

Stdlib-only instrumentation CLI implementing the minimum data contract from [pilot_quality_protocol.md](pilot_quality_protocol.md) for isolated exercise-quality runs. It never writes to Notion, learner `progress/`, `drills/workspace/`, or `drills/data/`.

## Storage & Isolation Layout

All artifacts are written strictly under gitignored `pilot/quality/<run-id>/`:

- `run.json` — run provenance (`mode`, `started_at`, `ended_at`, `closure_status`, `closed_observed_at`, `quarantine`, `model_id`, `effort`, `source_commit`, `content_sha256`, `drill_path`, `unit_id`, `drill_id`, `allowed_materials`, `prior_exposure`, `contamination`, `missing_reasons`, and `isolation_check`).
- `progress/` & `workspace/` — isolated directories created per run. **Note:** these directories are **not automatically wired** to existing `scripts/practice.py`, `code_engine`, or Practice Studio workspace runners; runners or operators must explicitly direct outputs into `pilot/quality/<run-id>/workspace/` and keep protected `progress/` and `drills/workspace/` untouched.
- `snapshots/` — read-only (`0444`) copies of `first_submission_ref` captured at `record` time.
- `items.jsonl` — append-only item attempt and revision records.
- `summary.md` — optional answer-free markdown summary created by `summary --write-md`.

At `init`, the CLI hashes `progress/` and `drills/workspace/` (SHA-256 digests only, never copying file contents) into `isolation_check.protected_snapshot` in `run.json`, and defaults `allowed_materials` to `[]` (canonical `drills/data/`, vaults, and hidden dotfiles are rejected for learner roles in prospective modes). While a run is **open**, `validate`, `finish`, and `summary` re-hash live protected directories against `protected_snapshot` to detect isolation mismatches. When `finish` closes a run cleanly, it stores `isolation_check.end_protected_snapshot`, `closed_observed_at`, and `closure_status: "closed"`. Once **closed**, `validate` and `summary` compare `protected_snapshot` against stored `end_protected_snapshot` rather than live protected paths, so legitimate later learner activity does not invalidate an already-closed run. Legacy already-ended runs lacking `end_protected_snapshot` remain readable (`valid: true`) with `isolation_status: "unknown"`, `isolation_ok: null`, `clean_run_eligible: false`, and warning `missing_end_protected_snapshot` (never backfilling an invented historical snapshot). Traversal (`..`), absolute refs, symlink components, and existing-run overwrites are rejected.

## Commands

Run from repository root using `.venv/bin/python` (or `python3`):

1. **`init`** — Initialize a prospective run before execution (`natural_attempt`, `fault_injection`, `transfer_probe`), or import an already-completed private session as `retrospective` with external timestamps:
   ```bash
   .venv/bin/python -m scripts.pilot_quality init \
     --run-id cal-mth-u01-01 \
     --mode natural_attempt \
     --drill-id DRL-MTH-T01-C01-U01-01 \
     --unit-id MTH-T01-C01-U01 \
     --model-id <model-id> \
     --effort high \
     --session-id <session-id> \
     --sample-reason "calibration batch" \
     --prior-exposure none \
     --contamination no
   ```
   - Transfer probe runs (`--mode transfer_probe`) must be initialized before probe execution.
   - Existing private natural sessions run prior to collector initialization must be imported with `--mode retrospective`, passing their external `--started-at` / `--ended-at` UTC timestamps, external `evidence_refs`, and explicit `missing_reasons` (never pretending to be prospectively instrumented `natural_attempt` runs).
   - Nullable provenance fields (`model_id`, `effort`, `session_id`, `sample_reason`, `source_commit`, `ended_at`) require `--missing-reason <field>=<reason>` when omitted/null (`ended_at` defaults to `"run_in_progress"` until `finish`).

2. **`record`** — Validate and append one typed item attempt (or linear metadata revision via `supersedes_record_id` preserving `(problem_id, attempt_index)`, `first_submission_sha256`, and null/non-null `first_submission_ref` state) to an open run:
   ```bash
   .venv/bin/python -m scripts.pilot_quality record \
     --run-id cal-mth-u01-01 \
     --input pilot/quality/cal-mth-u01-01/workspace/attempt_q01.json
   ```
   - Enforces unique `record_id`, linear revisions, strict tri-state `planted` (`true` / `false` / `null`), valid UTC `recorded_at` and chronological `help_events[].observed_at`, and explicit `help_events` (`[]` when observed empty, or `null` with `missing_reasons.help_events` — absent/unknown help is never silently treated as unassisted).
   - All validation runs before writing any `snapshots/` file or appending to `items.jsonl` (no orphan snapshots on failure).

   Example item payload using placeholder references only (no drill answers or prompt text):
   ```json
   {
     "record_id": "rec-q01-1",
     "problem_id": "Q01",
     "attempt_index": 1,
     "form": "direct",
     "first_submission_ref": "workspace/q01_attempt1.txt",
     "outcome": "incorrect",
     "confidence_before_feedback": "medium",
     "error_origin": "spontaneous",
     "planted": false,
     "solution_exposure": "none",
     "help_events": [
       {
         "kind": "hint",
         "observed_at": "2026-11-17T12:05:00Z",
         "ref": "workspace/q01_feedback.txt"
       }
     ],
     "feedback_ref": "workspace/q01_feedback.txt",
     "review_verdict": "REVISE",
     "caught_by": "reviewer",
     "dispute_outcome": "not_applicable",
     "explain_status": "partial",
     "time_source": "measured",
     "active_ms": 1400,
     "tool_wait_ms": 120,
     "elapsed_ms": 1520,
     "evidence_refs": ["workspace/q01_attempt1.txt"],
     "decision": "revise",
     "decision_reason": "Placeholder rationale referencing workspace/q01_feedback.txt"
   }
   ```
   If help usage was not observed (e.g., a retrospective import), set `"help_events": null` and include `"missing_reasons": {"help_events": "help_not_logged_in_source_session"}`.

3. **`finish`** (`end_run`) — Validate an open run against live protected paths, store `isolation_check.end_protected_snapshot`, `closed_observed_at`, and `closure_status: "closed"`, and set `ended_at` in `run.json` (clearing `missing_reasons.ended_at`). Rejects any protected-path isolation mismatch. Closed runs reject further `record`, `finish`, and `quarantine` calls:
   ```bash
   .venv/bin/python -m scripts.pilot_quality finish --run-id cal-mth-u01-01
   ```

4. **`quarantine`** (alias `close-incomplete`; API `quarantine_run`) — Close an interrupted open run with a protected-path isolation mismatch as an honest incomplete run (`closure_status: "quarantined"`), without resetting real progress or altering original start/submission hashes:
   ```bash
   .venv/bin/python -m scripts.pilot_quality quarantine \
     --run-id cal-mth-u01-01 \
     --reason "Thread interrupted before closeout; user confirmed Studio click in protected progress" \
     --evidence-ref workspace/closeout_note.md \
     --ended-at 2026-11-17T07:41:00Z
   ```
   - Requires a non-empty `--reason`; `--evidence-ref` is optional and must resolve safely (never protected paths), with its SHA-256 digest captured and re-verified on `validate`.
   - Captures current `end_protected_snapshot`, `closed_observed_at`, `quarantined_at`, and `isolation_mismatches` while preserving original `protected_snapshot` and `first_submission_sha256` / `snapshots/`.
   - **Only** overrides protected-path isolation mismatches: corrupted `content_sha256`, tampered submissions/snapshots, or invalid `run.json`/`items.jsonl` schema still block quarantine.
   - Quarantined runs remain readable (`valid: true` if evidence is intact) with `isolation_status: "quarantined"`, `isolation_ok: false`, and `clean_run_eligible: false`, and are permanently excluded from clean `natural_unassisted` and `transfer_probe` denominators (`excluded_or_unknown.run_quarantined`).

5. **`validate`** (`validate_run`) — Run the shared `run.json` and `items.jsonl` schema, revision-chain, drill `content_sha256`, protected-path isolation (start vs live when open; start vs `end_protected_snapshot` when closed; `"unknown"` when legacy closed run lacks `end_protected_snapshot`), `captured_digests`, quarantine evidence digest, and snapshot verification checks. Returns structured `errors[]`, `warnings[]`, `closure_status`, `isolation_status`, and exits non-zero on any error.

6. **`summary`** (`summarize_run`) — Run `validate` and emit answer-free aggregate IDs, status, timestamps, counts, and missingness in mutually exclusive cohorts (`natural_unassisted`, `fault_injection`, `transfer_probe`, `retrospective`, and `excluded_or_unknown`). Fault-injection, transfer-probe, retrospective, quarantined, isolation-unknown, contaminated, and unknown-help records never enter `natural_unassisted` denominators; retrospective imports remain separate in `cohorts.retrospective`.

## Late Closeout & Runtime vs Collection Time

- **Runtime window (`started_at`, `ended_at`):** Records when the exercise/session actually started and ended (e.g., external timestamps on `retrospective` imports, or the last recorded attempt timestamp on an interrupted prospective run via `--ended-at`).
- **Collection close time (`closed_observed_at`, `end_protected_snapshot.captured_at`):** Records the wall-clock UTC time when `finish`, `quarantine`, or a pre-closed `retrospective` `init` actually closed the run and hashed the end-of-run protected state.
- **Interrupted runs with late closeout:** If a prospective run finishes executing but closeout is delayed and real learner activity modifies `progress/` or `drills/workspace/` in the interim, default `finish` rejects the run. Do **not** reset real learner progress or fabricate an earlier final snapshot; close the run with `quarantine` (`quarantine_run`) so the original submissions and mismatch provenance are preserved honestly while excluding the run from clean outcome/transfer denominators.

## Truthful Limitations

- **No cryptographic tamper-proof claims:** SHA-256 digests, `0444` snapshots, and protected-path hashes detect accidental drift or post-hoc file edits on local disk, not adversarial tampering. Anyone with filesystem write access can overwrite `run.json`, `items.jsonl`, or `chmod` snapshot files.
- **Isolation directories are not auto-wired:** `pilot/quality/<run-id>/progress/` and `workspace/` are passive isolated storage targets; existing practice/workspace runners do not automatically read from or write to them.
- **Manually recorded timing, confidence, and help chronology:** `record` verifies UTC format and non-decreasing `help_events[].observed_at`, but cannot independently verify whether `confidence_before_feedback` was captured before feedback, whether all help was logged, or whether `active_ms` / `elapsed_ms` were measured accurately.
- **Exposure and pretraining:** `prior_exposure` and `contamination` are self-reported provenance fields; the CLI cannot detect unlogged solution reading or model pretraining exposure.
- **No `packet` export command:** Packet export machinery is intentionally absent in this collection CLI.
- **Mutable workspace artifacts:** Store each attempt's submission under a distinct path inside `pilot/quality/<run-id>/workspace/` (e.g., `q01_attempt1.txt`) so retries do not overwrite previously hashed files.
