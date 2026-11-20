# Exercise quality calibration — 2026-11-17

> **Pilot closed 2026-11-17 — historical.** This document is retained as a record and is not an active pilot runbook.


This is a bounded AI feasibility and instrumentation study, not evidence of human learning gain. Source exercises were frozen at commit `1536d0efcfc62cef0894e785cf4cfa1b3a9964f1`. Private raw records, rejected drafts, page snapshots, submissions and grader output remain in ignored `pilot/quality/calibration-20261117/` and the referenced collection runs. No solutions are reproduced here.

## Sample and collection

| Unit | Purpose in sample | Original items | Behavioral first-submission checks |
|---|---|---:|---:|
| PRG-T01-C01-U06 | Async implementation / bug-fix concentration | 5 | 5 passed |
| PRG-T01-C01-U07 | Related event-loop prediction / explanation mix | 5 | 5 passed |
| MTH-T02-C04-U06 | Rational-function direct-form concentration | 4 | 4 passed |
| MTH-T02-C04-U07 | Adjacent inverse-function reverse-form concentration | 4 | 4 passed |

The units were deliberately selected for contrast, not randomly sampled or matched perfectly on objective. Do not attribute differences to question format causally. Within each drill, deep review selected Q01 as a flagged item and one seeded-random different item (`seed=20261117`), giving eight design reviews and four independently double-coded items. Probe parents were selected before learner outcomes were inspected.

Fresh `gemini-4-hydrogen-high` sessions received literal packets containing a unit-page snapshot and visible task data, excluding canonical answers, vaults, hidden tests, personal notes and prior pilot reviews. The supervisor extracted pages read-only, omitting the personal implementation/mistake-log section. Models were told not to use tools or plant errors; observed CLI logs show no tool-monitor events in the natural first-attempt sessions. Submissions and confidence were frozen before grading. Code ran locally against existing tests; math used the existing answer checker.

This no-tool first-attempt experiment intentionally excludes the normal IDE/test/retry interaction. It is not a replacement for the full existing operational pilot or a Layer 3 architectural code-review pass. All original submissions passed, so this batch provides no observed correction-after-hint or spontaneous-error diagnosis data. Model confidence and reflections are self-report; pretraining remains uncontrolled.

The 18 original submissions were imported into four `retrospective` collector runs because they were executed before collector initialization. Original timestamps, immutable submissions, and before/after protected-path snapshots are retained as referenced evidence. They are not counted as prospectively instrumented natural attempts. The four later probe runs were initialized before execution, with isolated collection destinations.

## Independent review and probe design

Initial reviewers agreed on 35/40 dimension statuses. Inspection found both inconsistent anchors and unequal evidence access: one reviewer had checker contracts while the other initially had only the visible learner packet. Plain symbolic context was also rated differently despite both judging it appropriate.

After aligning evidence access and clarifying anchors, agreement was 39/40. This is calibration of the rubric, not an independent estimate of reviewer reliability: the same model family and repeated ratings were used. Raw initial and revised ratings remain preserved. The remaining disagreement led to a reproducible checker finding below; it was not erased to manufacture consensus.

Two of four initial probes were rejected before learner exposure because they changed several dimensions at once. Revised PRG probes passed independent blind review and executable checks; the two MTH probes passed independent symbolic/contract checks. Both author and independent PRG implementations passed probe tests.

Four subsequent submissions passed their probe checkers. Three probes test a representation/constraint change; PRG U07 is explicitly a **cue-dependence contrast**, not a pure representation-transfer measure. They were run in the original learner sessions before providing grader feedback. Success therefore supports feasibility and robustness to the selected change, not improvement caused by a lesson, delayed retention, or human transfer.

Independent explanation review rated three probe explanations supported and one partial. These are model-rubric judgments, separate from behavioral passing scores.

### Delayed closeout limitation

The probe calls finished around 07:41 UTC. Thread interruptions delayed final closeout until after real progress changed around 11:23 UTC. The user confirmed clicking around Practice Studio. All current progress was preserved. The original natural batch has matching immediate before/after snapshots, but the probes lack an immediate final protected-path snapshot. Their four passing outputs remain descriptive evidence; they are excluded from strictly clean prospective metrics rather than being relabelled as isolated after the fact.

This exposed a collector lifecycle issue: later legitimate learning must not invalidate a previously closed run. The final collector stores closing snapshots; interrupted runs can be quarantined with a reason and evidence, without bypassing source/submission integrity checks. Legacy closed imports without a stored final snapshot remain readable with unknown isolation, not a fabricated historical snapshot. Private evidence is in `external-activity.json` and the closeout records.

## Reproduced assessment gap

For `DRL-PRG-T01-C01-U06-01/Q03`, an independent worker implemented deliberately sequential behavior and ran the unchanged tests. It passed **4/4 tests**, while separate overlap instrumentation observed a maximum of **one simultaneous operation**, despite the prompt's concurrency requirement.

The supervisor adjudication separates two dimensions: the task aligns with its stated concurrency objective, but its tests do not enforce that property. Consequently, a passing test score alone does not demonstrate the intended skill. Private evidence: `concurrency-check.json`; issue `6034f8`. This task did not change the production drill or its tests; a concurrency-sensitive test is a concrete follow-up, without requiring a broad generator policy change.

## What changed in the workflow

- [Collection CLI](pilot_quality_runner.md): provenance, immutable submission references, separate modes, explicit unknowns, linear metadata revisions, protected-path checks and closeout.
- [Orchestration successor](pilot_quality_orchestration.md): fresh role inputs, isolated natural versus planted-error work, pre-feedback capture, verified probes, evidence-matched independent reviews and answer-free handoff. A local copy is saved at `pilot/orchestrator/quality-common-v1.txt`; the old launcher was not executed.
- [Protocol anchors](pilot_quality_protocol.md): appropriate plain math is context-neutral; item alignment and unit coverage are separate; checker validity requires checker evidence; the probe's `unchanged_objective` flag is a boolean backed by a referenced statement and independent review.

No generation skill, learner-facing content, Notion state, existing pilot history, or learner progress was rewritten. Runtime collection remains manually orchestrated; the CLI does not automatically redirect the existing practice/workspace runners, capture every help event, or verify an operator's exposure declarations.

## Interpretation and next work

Keep the 18/18 and 4/4 results separate from quality conclusions. The ceiling effect limits what this model/batch can reveal about difficulty. Do not force mistakes into natural attempts to create apparent signal. Preserve unknown timing, feedback benefit and human learning effects.

Next useful work is to close the concrete concurrency-test gap, collect a broader sample using the calibrated evidence rules, and run a full interactive pilot with explicit per-run workspace routing. Include failures, blocked tasks, help requests and revisions when they occur naturally. Broader format quotas, claims about optimal contexts, and changes to drill-generation policies are not justified by this batch alone.
