# Pilot quality workflow — successor to the old injection-only brief

Use with [protocol](pilot_quality_protocol.md) and [collection CLI](pilot_quality_runner.md). This workflow supplements existing content gates; it does not launch the paused content lanes. The private original `pilot/orchestrator/common.txt` remains historical. Do not execute its launcher or reuse its deliberate-error instructions in natural attempts.

## Supervisor preparation

1. Check Git/worktree ownership. Freeze source commit, drill byte hashes, unit-page snapshot hashes, selection reason, item IDs, random seed, and deep-review/probe parents before inspecting outcomes. Plain unit-page snapshots must omit personal implementation/mistake-log content. Read Notion only; writes still use `notion_sync.unit_page` under the normal authorization rules.
2. Keep raw artifacts in ignored `pilot/quality/`. Use separate fresh sessions and destinations for natural attempts and fault injection. `LEARNINGOS_PILOT=1` alone does not isolate runs: the old default `pilot/workspace/` is shared. `PROGRESS_DIR` overrides progress only. The collection CLI creates directories but does not reconfigure existing runners.
3. Prepare an explicit learner allowlist: page snapshot; prompt/context/input contract; starter/snippet and visible tests for PRG; displayed figure and choices when applicable. Never pass full drill JSON, answer specs, review notes, vaults, hidden tests, expected probe answers or planted manifests. Figures that carry necessary information require the real rendered visual; a text-only approximation is not equivalent.
4. Initialize the collection run **before** the learner starts. Capture protected-path hashes before/after execution. For old sessions imported after execution, use `retrospective`, preserving actual execution timestamps as referenced evidence; do not pretend collection began prospectively.
5. Choose the actual available model through `agy models`. Use the requested Hydrogen model and explicit effort. Record CLI version, requested model, session/log identifiers and observed execution metadata. A selected-model log is not a billing statement. Do not output credentials or raw logs.

## Natural learner brief

> Work independently from the supplied unit page and visible task packet only. Do not deliberately make mistakes, request hints, or dispute to satisfy a quota. Submit every item with confidence before receiving feedback. Use `needs_help` when needed; do not invent missing information. Keep submissions in separate per-attempt files. Do not read canonical drill JSON, vaults, references, hidden tests, review notes or other runs. After locking the first submission, record requested help and feedback in order before revising. Explain decisions briefly after submission. Never write learner progress or Notion. No Git mutations or subagents.

For a bounded no-tool first-attempt experiment, supply the packet literally to a fresh session outside the repo, prohibit tools, and record that this excludes the normal IDE/test/retry experience. The supervisor executes submitted code locally after it is locked. Do not report this as a full interactive learner pilot or an architectural code-review pass.

## Review and probes

- Preserve submission bytes and confidence before invoking any grader. Run existing math checking or PRG tests separately; raw grader output stays private. Passing tests is behavioral evidence, not a Layer 3 verdict.
- Give the quality reviewers identical evidence and the protocol. They judge design independently, without seeing each other's ratings. An author who also reviews a task is not its independent reviewer.
- Prepare probes before viewing learner results. Independently solve/check them and reject multi-dimension changes before exposure. Preserve rejected drafts and reasons; no production ingest/sync is implied by a private probe.
- A cue-removal contrast measures dependence on cues; label it separately from representation transfer. A fresh-session solve is not retention. Record prior page/task exposure and whether feedback was supplied before the probe.
- Capture post-attempt reflection privately: essential decision, ambiguity, prior-item similarity and unique contribution. Record model self-report as such.
- Run deliberate fault injection only in its own cohort when testing the checker. Preserve planted/caught/uncaught/dispute records; never add them to spontaneous error rates.

## Closeout and scaling

Record through the collection CLI, validate, finish, and generate answer-free summaries. Retain unknowns and excluded denominators. Reconcile all items, attempts, revisions, probes and blockers; verify protected paths again. Log confirmed issues using `scripts.issues`, searching for duplicates first.

Close the learner execution run immediately after recording its frozen submission and initial grading, before waiting for a later review or user reply. Preserve later quality-review judgments as separate linked evidence rather than keeping an execution run open for hours. If a thread interruption prevents timely isolation capture, quarantine the incomplete run with its evidence; never restore real learner progress or invent a past closing snapshot. Later legitimate study must not invalidate an already captured clean closeout.

Supervisor adjudication must distinguish an ambiguous rating anchor, different evidence access, a real task defect, and an uncertain hypothesis. If all AI attempts pass, report the ceiling effect; do not make stronger learning claims or force artificial mistakes into natural attempts. Scale collection only after integrity failures and rubric disagreements are addressed. Generator policy and learner-facing changes require their own reviewed changes.

Finish with a handoff: commit/PR/CI, private artifact paths, model/account evidence where relevant, counts and exclusions, known limits, pending worktrees and the next reproducible command. Never include exercise answers in a PR or learner-facing report.
