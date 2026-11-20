# Exercise quality assessment — pilot protocol v1

> **Pilot closed 2026-11-17 — historical.** This document is retained as a record and is not an active pilot runbook.


Status: calibration protocol with a local collection CLI; see [runner commands](pilot_quality_runner.md). Collection does not automatically instrument the existing learner runners or change generation skills.
Scope: assess exercises and design useful observations, not restart content production.
Read the [initial assessment](pilot_quality_baseline.md) before interpreting historical results.

## Roles and separation

- Supervisor selects the objective and sample, checks evidence, adjudicates disagreements, and decides what to revise.
- Author follows existing page, vault, drill, blind-solve and review gates. This protocol does not change the canonical branch, PR, or merge policy in `rules/00_core.md` §10.
- Learner receives only the permitted page and visible workspace. Never provide vaults, reference solutions, hidden tests, planted-error manifests, or quality-review notes before submission.
- Quality reviewer evaluates exercise design separately from the existing code reviewer. The latter evaluates submitted code; a PASS is not an exercise-quality verdict.
- Record actual model ID, effort and role. Do not silently substitute a model. Use one bounded worker batch before expanding; do not launch an unattended loop.

Two separate runs are required when measuring both learning opportunities and checker robustness:

1. `natural_attempt`: fresh learner session with no instruction to plant errors, dispute, or request a hint. Lock first submission and confidence before feedback. Offer normal help; record its use. Do not prompt the learner to critique the design until its attempt is locked.
2. `fault_injection`: preserve the existing intentional-error workflow, including disputes and explanation checks. Use a separate workspace/progress destination; reviewer cannot read the planted manifest. Never aggregate this run with natural attempts as a learner error rate.

Fresh sessions reduce cross-run exposure but do not erase model pretraining. If isolation or content exposure cannot be established, mark `contamination=unknown` or `yes` and exclude the run from unassisted/transfer summaries. Historical items with no plant recorded are not automatically natural attempts.

## Questions and evidence anchors

These are design-review dimensions, not a validated educational scale. Use `supported`, `concern`, `unknown`, or `not_applicable` with an evidence reference and a short reason. Never compute an overall quality score by averaging them.

| Dimension | Question | Evidence needed to move beyond opinion |
|---|---|---|
| Objective alignment | What observable skill must the learner demonstrate? Can the task be passed without it? | Objective reference, required decision, and a bypass/cue check |
| Reasoning and cues | Must the learner choose or justify a method, or does wording/test structure reveal it? | Prompt-visible demand; distinguish intentional scaffolding from accidental cues |
| Transfer | Can the same concept be used when representation, constraints, or context change? | A separately identified unseen probe with outcome and exposure record |
| Misconception diagnosis | Does an error distinguish a conceptual gap from a slip, format error, or tool failure? | Attempt and feedback provenance; planted errors labelled explicitly |
| Context | Does the scenario impose meaningful constraints or merely add reading? | Context removal test; PRG production relevance, MTH plain prompts acceptable |
| Difficulty and load | Is the challenge reasoning, prerequisites, reading, arithmetic, or setup? | Demand tags plus observed blocker; timing alone is insufficient |
| Feedback | Does help permit self-correction without giving the answer away? | Before/after attempt references, help type and exposure; correction alone is not transfer |
| Sequence and redundancy | What does this item add beyond earlier ones? Is repetition deliberate retrieval or only renaming? | Comparison item IDs and the different decision/representation; deletion test |
| Assessment validity | Could tests/checker reject valid work or accept a shortcut? | Reproducer/review reference; distinguish historical report from current verification |
| Learner agency | Can the learner explain limits, choose alternatives, or diagnose uncertainty? | Post-attempt explanation rubric, confidence recorded before feedback, prerequisite exposure |

Keep existing `form`, `codeType`, category and blind-solve demand tags. Add observations beside them; do not overwrite author labels or turn labels into proof of cognitive demand.

Calibration anchors: use `context=not_applicable` for appropriate plain math without a scenario (neutral, not a defect). Judge objective alignment against the item's stated objective; record missing unit-wide coverage separately. Compare reviewers only when they receive the same evidence: a reviewer without checker contracts must use `assessment_validity=unknown`. Design support and an observed learning outcome remain distinct, even when a model solves every item correctly.

## Minimum data contract

Store raw records only under ignored `pilot/quality/<run_id>/`. No answers, hidden tests, raw progress, or solution-bearing excerpts go into Git, PRs, or learner-facing reports. Use relative path references plus item IDs and headings/record IDs; keep any private explanation in a separate local file. No changes to the learner's `progress/`, Notion, or current drill schema are needed.

Use `run.json`, append-only `items.jsonl` (one record per attempt), and `summary.md`. Missing data is `null` with `missing_reason`, never invented or converted to zero. Revisions create new records with `supersedes_record_id`.

| Record | Required fields | Convention |
|---|---|---|
| Run identity | `schema_version`, `run_id`, `mode`, `started_at`, `ended_at`, `source_commit`, `content_sha256`, `unit_id`, `drill_id`, `sample_reason` | UTC timestamps; hash exact drill bytes; modes: retrospective, natural_attempt, fault_injection, transfer_probe |
| Provenance | `actor_type`, `model_id`, `effort`, `role`, `session_id`, `allowed_materials`, `prior_exposure`, `contamination`, `isolation_check` | AI and human separate; unknown model/effort remains null; exposure: none/visible_only/solution/unknown |
| Item identity | `record_id`, `problem_id`, `attempt_index`, `objective_ref`, `prerequisite_refs`, `form`, `code_type`, `demand_tags`, `sequence_index` | Reuse existing labels; absent observations remain null |
| Outcome | `first_submission_ref`, `outcome`, `confidence_before_feedback`, `error_origin`, `blocker`, `evidence_refs` | outcome: correct/incorrect/partial/invalid_input/blocked/not_attempted; confidence low/medium/high/null |
| Attribution | `planted`, `plant_manifest_ref`, `solution_exposure`, `help_events`, `feedback_ref`, `revision_ref` | error_origin: spontaneous/planted/tooling/ambiguous/unknown; help events ordered with kind and observed timestamp |
| Review path | `review_verdict`, `caught_by`, `dispute_ref`, `dispute_outcome`, `explain_status`, `issue_refs` | Verdict PASS/REVISE/blocked/not_reviewed; caught_by test/lint/typecheck/reviewer/none/unknown; disputes upheld/rejected/partial/pending/not_applicable; explain supported/partial/unsupported/not_observed |
| Effort | `active_ms`, `tool_wait_ms`, `elapsed_ms`, `time_source` | measured/estimated/unavailable; never infer active time from shell wall time or token count |
| Item review | `dimensions`, `unique_contribution`, `comparison_ids`, `decision`, `decision_reason` | Each dimension has status, evidence refs, confidence; decision keep/revise/replace/investigate |
| Probe | `probe_id`, `parent_problem_id`, `changed_dimension`, `unchanged_objective`, `delay_ms`, `exposure`, `outcome`, `explanation_status` | Null unless a probe ran; `unchanged_objective` is a reviewer-verified boolean (the objective statement stays in the referenced probe artifact); explanation supported/partial/unsupported/not_observed |

`planted` is true/false/null. The quality reviewer may join the private plant manifest only after the code-review verdict is locked. Attempt outputs are references, not copied solution text. Preserve raw checker outcomes alongside reviewer interpretations. Record any harness patch and the commit used to re-run it.

## Collection checklist

1. Freeze commit/hash and sample criteria before running. Snapshot protected learner paths without copying contents into reports. Capture model and allowed input files.
2. For each item, capture first submission and confidence before feedback. Record all hints, setup/solution reveals, retries, invalid input and blockers in order. A broken harness yields `blocked`, not evidence of low ability.
3. After the attempt, ask briefly: What decision was essential? What was unclear? Which previous item felt equivalent, and why? What would be lost if this item were removed? Treat answers as model self-report, not facts about human experience.
4. Quality reviewer fills the dimension statuses using prompt/attempt evidence. Mark unknown rather than request long speculative narratives.
5. For selected items, run an independently prepared, verified probe that preserves the objective and changes one dimension. Do not show its solution beforehand. Within-session transfer and later retention are separate outcomes; an AI fresh-session result is not human retention.
6. Run checker fault injection separately using the existing pilot protections. Record planted/caught/uncaught counts and disputes only in that cohort.
7. Close out with coverage, missingness, protected-path comparison and an answer-free summary. Failed isolation blocks a clean-run claim. Log confirmed bugs using the existing issue workflow, checking for duplicates first.

## Small calibration batch before scaling

Proposed next execution, not performed by this change:

- Select two PRG and two MTH units, with one format-concentrated set and one contrasting set per domain, matched on objectives/prerequisites as far as possible. Record exclusions and avoid choosing only reported problem cases.
- Collect minimum fields for every item in those four drills. Deep-review at most two items per drill: one randomly selected and one flagged, recording which is which. Do not generalize flagged-item rates to the corpus.
- Prepare one transfer probe per unit. Select before seeing the learner's result. Keep objective and core prerequisites constant; change only one representation/constraint/context initially.
- Have a second independent quality reviewer double-code four deep-review items (one per unit), blind to the first verdict. Supervisor records disagreements and revises unclear anchors before scale-up. Do not call model agreement proof of human validity.
- Worker brief: read only assigned artifacts, at most 500 words of findings, no unrelated exploration, no automatic continuation. Stop after the batch and assess missing fields and usefulness. Increase effort only for a specific unresolved issue.

## Reporting and decisions

Report counts as numerator/eligible denominator with exclusions: natural unassisted first attempts, assisted corrections, probe passes with explanation, tool-blocked items, and injection detection. Separate domains, objectives, models, content versions and modes. Missing records are missing, not failures or passes. Do not report artificial timing as human completion time.

- Immediate safety/correctness concerns follow existing issue severity rules. Historical reports are not automatically current bugs.
- Revise a design when an evidence-backed ambiguity, misleading cue, or alignment failure is established. Broader generator policy needs replication across units and calibration review.
- A narrow format mix is an investigation signal, not a defect by itself; repetition can be purposeful. No mandatory format quotas from this small baseline.
- Successful explanation or transfer in an AI pilot supports task feasibility only. Claims about learner improvement need actual learner evidence; no mastery updates from pilot outcomes.

## Integration handoff

Before resuming pilots, wire this checklist into a reviewed successor of the local `pilot/orchestrator/common.txt`; do not run its old launcher as part of this assessment. Separate progress destinations must be verified against the actual runner before execution.

Only after calibration should changes to `new-code-drill`, `new-math-drill`, review rules, UI telemetry, or automated schemas be proposed in separate PRs. Preserve existing gates, domain-specific requirements and the learner's merge boundary. Claude/Gemini can use this document directly without reconstructing chat history.
