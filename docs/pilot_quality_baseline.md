# Initial exercise-quality assessment

> **Pilot closed 2026-11-17 — historical.** This document is retained as a record and is not an active pilot runbook.


Date: 2026-11-17. Source commit: `b204415df01693884c3c063369bb1725d7fd94f2` (PR #149 merged).
Scope: local artifact inventory plus targeted historical evidence, not a full pedagogical audit or a new pilot run. No Notion pages audited in this task.

Worker review: one completed `agy` call using `gemini-4-hydrogen-high`, read-only plan mode, bounded to the old orchestrator instructions and five selected reports/improvement files (PRG T01 C01 U06/U08, PRG T02 C01 U06, MTH T02 C04 U03/C02 U02). It corroborated the distinction between historical observations and current defects, and recommended preserving verdict/dispute/explanation paths. The supervisor checked the source evidence and authored this synthesis. The worker did not review all 174 items; no independent full-corpus audit or protocol calibration is claimed. Raw output remains local at `/tmp/learningos-quality-worker.txt` and is not part of this PR.

## What is recoverable

Read-only inventory of `pilot/runs/*/` found 52 directories, 51 `REPORT.md`, 49 `IMPROVEMENTS.md`, 10 `learner_notes.md`, and 18 `planted.md` files. `pilot/progress/` contains 19 JSON files. These are file counts, not completed-run counts; one report can cover several phases, and some runs are content-only.

Extracting full `DRL-(PRG|MTH)-…-NN` identifiers from the 51 reports gives 41 unique IDs. Forty join to current `drills/data/**/*.json`: 23 PRG drills (105 items) and 17 MTH drills (69 items), 174 items total. `DRL-PRG-T01-C03-U06-01` does not join in this checkout and is excluded; the handoff/worktree inventory identifies it as pending work. It has not been marked missing or lost globally.

This is a conservative cohort based on full IDs, not all historical practice: the phase-A report also uses abbreviated drill IDs, and labs are outside this item inventory. The entire current drill directory contains 52 drill JSON files / 251 items (25 PRG / 120 items; 27 MTH / 131 items), which must not be reported as new pilot output. The earlier conversational estimate of 41 ready sets / roughly 200 questions is not the denominator for this assessment.

Inventory method: enumerate files; parse JSON without printing prompts or solutions; extract full drill IDs from reports; exact-join against JSON `id`/`drillId` (filename fallback); sum `problems`; count `codeType` for PRG and `form` for MTH. Deduplicate drill IDs, not report mentions. Re-run at a new commit before comparing future counts.

## Observable format distribution

| Domain | Author metadata | Items |
|---|---|---:|
| PRG | implement | 47 |
| PRG | fix-bug | 28 |
| PRG | trace-explain | 11 |
| PRG | refactor / refactoring | 11 / 1 |
| PRG | predict-output | 7 |
| MTH | direct | 41 |
| MTH | reverse | 20 |
| MTH | diagnose | 4 |
| MTH | choose | 3 |
| MTH | translation | 1 |

These labels were counted, not independently validated as thinking demands. They show where to sample, not which format teaches best. Preserve the raw `refactor` / `refactoring` distinction in source data even if grouping them for display.

## Evidence and implications

All paths below are local, ignored artifacts. Do not publish their raw contents: some contain solutions. Historical observations are not re-tested current defects.

| Finding | Evidence | Confidence and next observation |
|---|---|---|
| Existing pilots deliberately mix learning attempts with checker tests. | `pilot/orchestrator/common.txt`, PILOT paragraph; `pilot/runs/MTH-T02-C04-U03/REPORT.md`, outcome/table | High confidence about instructions and reported practice. Split natural attempts from injection; historical error rates cannot measure difficulty. |
| Specific PRG sets concentrate formats. | Current U06 drill metadata: 3 implement + 2 fix-bug; U08: 3 refactor + 2 fix-bug. Corresponding `IMPROVEMENTS.md`, section 3, requests prediction/tracing. | High confidence in composition; pedagogical benefit of changing it is unproven. Test representation/decision diversity while holding objective constant. |
| Tool friction can masquerade as difficulty. | `pilot/runs/PRG-T01-C01-U04/learner_notes.md`, workspace feedback and estimated time; `pilot/runs/PRG-T02-C01-U06/REPORT.md`, Q02/dependency notes | Reported harness and dependency failures; present status not re-run. Capture blocker cause and time source separately from reasoning. |
| Passing and correction do not establish independent understanding. | `pilot/runs/MTH-T02-C04-U03/REPORT.md`, final checks versus retry summary; `pilot/runs/PRG-T02-C01-U06/REPORT.md`, explanation records | High confidence in reports, no comparable unseen-transfer outcome recovered in this sample. Record first pass, help exposure, explanation and probe separately. |
| Feedback usefulness deserves its own observation. | `pilot/runs/MTH-T02-C02-U02/IMPROVEMENTS.md`, item 2 (generic feedback) and item 10 (hint/trap review) | Historical reviewer/learner observations. Compare correction before/after help and subsequent unseen application; do not assume a hint helped merely because it was used. |
| Context and prerequisites can obscure the target skill. | `pilot/runs/MTH-T02-C03-U02/IMPROVEMENTS.md`, modeling-context row; `pilot/runs/MTH-T02-C02-U04/IMPROVEMENTS.md`, Worked Examples row | Hypotheses from reports, not a corpus-wide prevalence estimate. Capture domain constraints, prerequisite exposure and ambiguities. |
| Exposure and launch discipline affect validity. | `pilot/runs/PRG-T01-C03-U06/IMPROVEMENTS.md`, reviewer safety row; `pilot/runs/PRG-T02-C01-U06/REPORT.md`, isolation note | Reports distinguish a restarted reviewer from broader instruction exposure. Record allowed materials, actual exposure and replacement-session IDs. Do not infer contamination for all runs. |

## Limits of retrospective recovery

- Ten files named `learner_notes.md` does not mean only ten runs have learner observations; other names exist. Notes are heterogeneous and sometimes contain estimated time rather than measured telemetry.
- Nineteen progress files do not cover all report-linked drills. Fields also differ: inspected MTH records expose attempts/hints/last checks; PRG records often expose reviews and test reports. A final summary alone cannot reconstruct exposure order or natural first-attempt performance.
- Missing `planted.md`, or a report saying no plant was recorded, does not prove an unprompted attempt. Keep unknown attribution rather than invent it.
- Pretraining, differing models, author/reviewer exposure, changing tools and deterministic intentional mistakes prevent causal claims about learning gain. No human completion-time or retention estimate is warranted.
- The original workflow also tested disputes, explanations, weak-spot detection, submission isolation and content production. Preserve these operational checks; do not confuse them with exercise-effectiveness measurement.

## Immediate deliverable and deferred work

The [v1 protocol](pilot_quality_protocol.md) defines a separate quality review, minimal evidence fields, explicit missingness, a small calibration batch and decision rules. It is ready for integration review, not yet wired into the runner. No drill, generation skill, Notion data, pilot history or learner progress is changed here.

Defer to the next authorized execution: the full semantic audit of all items; normalization of phase-A abbreviated IDs; inspection of pending U06 worktree content; fresh natural attempts; verified transfer probes; independent rubric calibration; runner integration; and any generator-policy changes. These require additional worker work and, where relevant, historical context. Do not resume the old three lanes automatically.
