---
name: review-code
description: Review the learner's code for one PRG drill problem like a senior engineer's pull-request review - run tests, lint and types, judge design against the archetype's rubric (qualityChecks), give hints not rewrites, record the attempt, and show the reference only after a pass. Use when the learner asks to review or check their code ("ตรวจโค้ด DRL-PRG-T00-C02-02 Q01", "review code ...", "รีวิว Q03"), disputes a finding, or answers the explain question.
---

# Review code

The learner studies programming alone and cannot yet judge structure themselves. Your review is the only thing between
"it runs" and "it is well built", so it must be strict, consistent and fair. Spec: `docs/prg_reviewer_spec.md`.
Talk to the learner in polite Thai; finding notes stored in the record are English.

Run every command from the **main checkout** (`/Users/Joseph/Documents/antigravity/LearningOS`, the folder that holds
`progress/` and `drills/workspace/`), with its `.venv/bin/python`. Never edit the learner's files.

## 1. Run layers 1–2

```bash
.venv/bin/python -m code_engine.review_run <DRILL_ID> <QID> --json
.venv/bin/python -m scripts.review_record show <DRILL_ID> <QID>     # earlier attempts
```

If the drill or problem is missing, say so and stop. If the workspace file is missing, the learner has not started:
tell them to open the workspace from the Studio. Labs are not supported by `review_run` yet: say so.

Read: the learner's source file, the problem's `prompt` in `drills/data/<UNIT>/<DRILL_ID>.json`, the rubric printed by
`review_run` (universal `U-*` + archetype `QC-*`, with effective severity), and the archetype's `cognitiveTraps` in
`code_engine/reasoning_vault/`. Do not read or quote `hiddenTests` code or `solutionCode` to the learner before a pass.

## 2. Judge design (layer 3)

Go through each rubric check against the code. For each one decide: met, violated, or not applicable to this problem
(e.g. `QC-coercion-pure-output` on a function that returns a number). Only violations become findings.

A finding needs all of:
- `check`: a rubric id from the `review_run` output (the record refuses others). No id fits → not a finding; if it is
  a real recurring design problem, propose a new check for the vault in your reply to the learner instead.
- `line`: the line in the learner's file.
- `note`: what is wrong and **why it matters** (the consequence), one or two sentences, English.
- `hint`: a question or direction that makes the learner find the fix (Thai is fine), at most one line of code, never
  the whole fix. Prefer "What does `timeoutSec || 30` return when `timeoutSec` is 0?" over "use `??`".

Rules:
- Severity comes from the rubric, not from you. Raise a `must` check only when you can point at the line and state the
  consequence; if you are unsure it applies, do not raise it — ask the learner a question about it instead.
- Taste is never a finding (brace style, `for` vs `forEach`, `function` vs arrow when both are clear).
- Do not repeat what lint or tests already report; explain them instead (step 4).
- Two equally good designs: accept the learner's. The reference solution is not the standard; the rubric is.
- Tests failing is enough for revise; still review design, so the learner fixes both in one round.

Write the findings to a temp file and record:

```bash
.venv/bin/python -m scripts.review_record add <DRILL_ID> <QID> --findings /tmp/…/findings.json
```

`findings.json` is a list of `{"check", "line", "note", "hint"}` (an empty list is valid). The script re-runs tests and
lint itself and computes the verdict; report the verdict it prints, never your own.

## 3. Reply (Thai)

1. Verdict line: **ผ่าน** or **ยังไม่ผ่าน (revise)**, attempt number, tests x/y, lint/type error count.
2. Failing tests: name each one and what behaviour it expects in general terms (from the visible test or the prompt),
   plus one hint. Never paste hidden test code or give the expected value of a hidden case.
3. Lint/type errors: `file:line rule`, and why the rule exists in one sentence.
4. Findings: grouped must first, then should; each with check id, line, note in Thai, hint.
5. Patterns: if `review_record show` or `python -m scripts.weak_spots <UNIT|CHAPTER>` shows the same check or rule in
   earlier problems, say so plainly ("แก้ค่า input ซ้ำเป็นครั้งที่ 3").
6. What is good: one or two concrete things the code does well (only if true).
7. Next step: fix and ask for review again.

## 4. After a pass

- Show the reference `solutionCode` next to the learner's code, with one paragraph on differences worth noticing
  (trade-offs, not a ranking). If the learner's design is as good, say so.
- Ask one explain question about why the code works or what input would break a weaker version. When they answer, check
  it for correctness (correct gaps kindly), then:
  `.venv/bin/python -m scripts.review_record explain <DRILL_ID> <QID> "<their answer>"`.

## 5. Disputes

If the learner disagrees with a finding, weigh their argument honestly. If they are right or it is genuinely arguable:

```bash
.venv/bin/python -m scripts.review_record dispute <DRILL_ID> <QID> <CHECK_ID> --reason "<why>"
```

This logs an issue and recomputes the verdict. If the check's wording caused the mistake, propose a rubric fix (a PR on
the vault, Claude's work) in the same reply. If they are wrong, explain why with a concrete input or change that shows
the consequence; do not dispute.

## 6. Never

- Rewrite the learner's code, or give a fix longer than one line before a pass.
- Show hidden tests or the reference before a pass.
- Pass code by your own judgement: only the recorded verdict counts.
- Edit `drills/workspace/` or `progress/` by hand.
