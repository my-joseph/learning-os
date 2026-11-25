# Distractor Provenance Lessons

The read-only distractor audit found eight failing problems across four legacy drills. Before retirement, `python -m math_engine.ai_drill_ingest --ingest-file <drill.json> --check` also reported these failures for the three retired drills:

| Drill / problem | Gate findings |
|---|---|
| `DRL-MTH-T02-C01-U01-05` Q05 | Distractor B had no `trapTag`; option C carried `commonTrapTag` but its value (`k = -3` or `k = 2`) did not equal `trapValue` (`2`). |
| `DRL-MTH-T02-C01-U01-05` Q06 | Distractors A, D, and E had no `trapTag`. |
| `DRL-MTH-T02-C01-U01-05` Q07 | Distractors A, C, and E had no `trapTag`. |
| `DRL-MTH-T02-C02-U05-01` Q02 | Distractors 4, 5, and 6 had neither provenance nor a `trapTag`. |
| `DRL-MTH-T02-C03-U03-01` Q01 | Distractors B, C, and D had no `trapTag`; none carried the required `commonTrapTag`. Their prose provenance was unverifiable. |
| `DRL-MTH-T02-C03-U03-01` Q03 | `trapValue` (`4`) equaled the correct value; distractors A and C lacked `trapTag`; correct option B had a distractor tag; no distractor carried the required common tag. |
| `DRL-MTH-T02-C03-U03-01` Q04 | `trapValue` (`43`) equaled the correct value; distractor A had no provenance and C had no `trapTag`. |
| `DRL-MTH-T02-C04-U05-01` Q02 | Distractors B, C, and D had no `trapTag`; none carried the required `commonTrapTag`. Their prose provenance was unverifiable. |

The individual `--check` runs also found an unrelated originality failure in `DRL-MTH-T02-C04-U05-01`: Q01 reused a source number multiset (`1, 2, 2, 3`, source PDF p. 5) and Q03 reused (`2, 3, 6`, p. 17). They are not part of the eight-problem distractor audit.

## Authoring rules

- Give every wrong choice exactly one `trapTag` from that problem's archetype vault traps. The correct choice has no distractor tag.
- Make each trap a single, recognizable misconception. Explain the wrong operation in `provenance` and provide an evaluable expression that uses problem givens/constants and produces that option's value. Prose alone does not prove the value.
- On each choice problem, include a distractor carrying `commonTrapTag`; its value must equal `trapValue`. Derive `trapValue` from the misconception and verify that it differs from the correct answer.
- For a diagnose/flaw option, provide provenance for every wrong line/value option as well; naming a flaw does not establish how its value was produced.
- Do not use string-only `cognitiveTraps` in a new vault. Store trap objects with a clear misconception description and a SymPy-evaluable `trapFormula`, so the gate can verify the operational result. Existing string-only traps make verification unverifiable.
- Run `python -m math_engine.ai_drill_ingest --ingest-file <draft.json> --check` and resolve every error and unverifiable warning before review or ingest.
