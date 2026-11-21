---
name: new-project
description: Create a new verified PRG project lab (chapter lab from docs/prg_curriculum_v2.md §4, or extra project on request "ขอโปรเจคเพิ่ม <CHAPTER|TOPIC>") — inspect studied units and weak_spots, design lab.config.json + README, author stubs/visible tests/reference/hidden tests/trapMutants, run lab_ingest --check, blind-solve subagent, reviewer subagent, finalise, pytest, sync pristine record to Notion, and ship a lab-only PR with branch and PR handling per `rules/00_core.md` §10.
---

# New project lab

Goal: a multi-milestone TypeScript project lab (`labs/LAB-<CHAPTER>-NN/` + `labs/_reference/LAB-<CHAPTER>-NN/`) that matches what the learner needs and passes every gate on the first finalise, with no hand-fixing afterwards. The learner studies these labs, so they never see drafts, reference solutions, hidden tests, or blind-solve code before practising: do not show them reference code or hidden tests, and do not ask them to approve. Mistakes you, the blind solver, or the reviewer catch go into the issue log (`rules/00_core.md` §11), not into questions to the learner. Run everything from the repo root with `.venv/bin/python` and call tools as modules (`.venv/bin/python -m pytest`, `-m ruff`). **Keep answers and code out of the terminal**: subagents write their results to files and reply only `done`, because their replies are shown to the learner. Talk to the learner in polite Thai; everything written into labs, READMEs, and configs is English. Never edit `progress/` or another lab's `src/` by hand.

## 1. Entry points & Brief

Determine which entry point applies:
- **(a) Chapter lab** (`docs/prg_curriculum_v2.md` §4): when the learner reaches or finishes a chapter. Use that chapter's planned lab spec (`title`, `unitsUsed`, 3–6 milestones `M1`–`M4`/`M6`, ~3–8 sessions).
- **(b) Extra project on request** (`"ขอโปรเจคเพิ่ม <CHAPTER|TOPIC>"`, `docs/prg_curriculum_v2.md` §9):
  1. **Scope (studied units only):** query `id_map.json` + read-only Notion `GET` (`notion_sync.client.notion_request`) for units in `<CHAPTER|TOPIC>` and include **only** units with `Status` `Done` or `In progress` (nothing ahead of the learner).
  2. **Weak-spot targeting:** run `.venv/bin/python -m scripts.weak_spots <SCOPE>` to find open weak spots (`U-*`, `QC-*`, ESLint rules, traps) and weight the lab's milestones and `targetsWeakSpots` toward them.
  3. **Level:** same level as the learner's current work in that scope, or one step up if the learner asks.
  4. **Fresh domain:** read existing `labs/LAB-*/lab.config.json` files in that scope and pick a **different** realistic production domain (e.g. after `PromisePool`, a rate-limited crawler; after `RawHttpRouter`, a static file server). Never use toy names (`foo`, `bar`, `baz`, `test1`, `funcA`).
  5. **Size:** 3–6 milestones (`M1`..`Mk`), ~3–8 sessions (~4.5–12 h).

State the brief in one line and continue without waiting.

## 2. Load only the rules this task needs

Read `rules/00_core.md` §5–§6, §8, §10, §11; `rules/04_code.md` (Part 1, Part 5, Part 6, Part 7, Part 10); `docs/prg_reviewer_spec.md`; and `docs/prg_curriculum_v2.md` (§4, §9).

## 3. Design `lab.config.json` + `README.md`

Allocate the next `LAB-<CHAPTER>-NN` ID (check existing `labs/LAB-<CHAPTER>-*`).

Create `labs/<LAB_ID>/lab.config.json`:
```json
{
  "labId": "LAB-PRG-T01-C01-01",
  "title": "...",
  "chapterCode": "PRG-T01-C01",
  "unitsUsed": ["PRG-T01-C01-U02", "PRG-T01-C01-U06"],
  "kind": "chapter-lab",
  "level": 3,
  "domain": "rate-limited-crawler",
  "targetsWeakSpots": ["U-no-input-mutation"],
  "milestones": [
    {
      "id": "M1",
      "title": "...",
      "goal": "...",
      "units": ["PRG-T01-C01-U02"],
      "qualityChecks": ["U-names", "U-no-input-mutation", "QC-..."],
      "visibleTests": "tests/m1_*.test.ts",
      "examples": [
        {
          "input": "...",
          "output": "...",
          "explanation": "Optional short walkthrough",
          "call": "entryFn(...)"
        }
      ],
      "constraints": ["..."],
      "trapMutant": {
        "files": {"src/...": "..."},
        "note": "Plausible wrong implementation embodying the target trap"
      }
    }
  ]
}
```
- Every `qualityChecks` entry must exist in `code_engine/quality_checks.json` (`U-*`) or in the archetypes of `milestone.units` (`code_engine/reasoning_vault/`).
- Each milestone must include 2–3 `examples` `[{"input": "...", "output": "...", "explanation": "...", "call": "..."}]` (**normal cases only** — never reuse hidden-test inputs or `trapMutant` trap cases) plus optional `constraints: string[]` when the input has limits; `input`/`output` are JS/TS literal display strings and `call` is verified against `labs/_reference/<LAB_ID>/src/` by `lab_ingest --check` and finalise.
- Create `labs/<LAB_ID>/README.md`: scenario, milestones (`M1`..`Mk`), acceptance criteria, and how to run `npm test` / `npm run check` / `"ตรวจโค้ด <LAB_ID> M1"`. **No implementation hints, no internal data-structure spoilers, no solution leaks.**

## 4. Author workspace, stubs, visible tests, reference, hidden tests, and trap mutants

In `labs/<LAB_ID>/`:
- `package.json` with scripts: `test`, `test:reference`, `lint`, `typecheck`, `check`, `check:reference`, `check:hidden`, `review`, `submit`, plus `test:m1`/`check:m1` through every configured milestone (mirror `labs/LAB-PRG-T01-C01-02/package.json`, which matches `code_engine.lab_ingest.REQUIRED_PACKAGE_SCRIPTS`; each check runs tests, lint, and typecheck independently and reports every result). `review` accepts a milestone argument and prints `ตรวจโค้ด <LAB_ID> M<n>`. `check:hidden` runs `LAB_SRC_DIR=../src node --experimental-strip-types --test ../_reference/<LAB_ID>/hidden/*.test.ts`.
- Include a concise `scenario` field in `lab.config.json`; derive `README.md` scenario and its milestone list from `scenario` and `milestones` in the config. Keep README free of implementation hints.
- `eslint.config.js` (`import { prgConfig } from "../../tools/lint/base.js"; export default prgConfig();`) and `tsconfig.json` (`strict: true`, `noEmit: true`, `allowImportingTsExtensions: true`).
- `src/` stubs: exported types/interfaces + function/class signatures with `_`-prefixed unused params and `throw new Error("TODO [M1]: …");` bodies. Must be ESLint-clean and `tsc`-clean, and fail every milestone's visible tests.
- `tests/` visible acceptance tests per milestone (`tests/m1_*.test.ts`, etc.), importing from `process.env.LAB_SRC_DIR || "../src"`. Test names and assertions must not leak the implementation.

In `labs/_reference/<LAB_ID>/` (excluded from learner's VS Code via `.vscode/settings.json`):
- `src/`: complete, clean reference implementation passing all visible + hidden tests, ESLint, `tsc`, and zero `must` rubric findings.
- `hidden/`: hidden trap/edge-case tests per milestone (`m1_*.test.ts`, etc.) importing from `process.env.LAB_SRC_DIR || "../src"`. Time-dependent code must use an injectable clock (`options.now = Date.now`).
- `tsconfig.json`: matching `labs/<LAB_ID>/tsconfig.json`.

## 5. Pre-flight check (`--check`)

```bash
.venv/bin/python -m code_engine.lab_ingest --check labs/<LAB_ID>
```

Never pass `--offline` here or at finalise: it skips the check that an extra project only uses units the learner has studied, and exists for hermetic tests only.

Run this before spawning subagents to catch schema, unit-status, rubric, reference, stub, `trapMutant`, or leak issues early. At this stage, only `blindSolve` and `review` should be reported missing. Fix everything else first.

## 6. Blind solve (independent subagent)

Spawn **one** fresh subagent. Give it **ONLY** `labs/<LAB_ID>/README.md`, `labs/<LAB_ID>/src/` stubs, and `labs/<LAB_ID>/tests/` visible tests (never `labs/_reference/<LAB_ID>/`, `trapMutant`, or `targetsWeakSpots`). Tell it to write its per-milestone solutions to `scratch/reviews/<LAB_ID>-blind.json` as:
`[{"milestone": "M1", "files": {"src/...": "..."}, "ambiguous": false, "note": "..."}]`
and reply only `done`.

Copy that JSON list into `lab.config.json` as `"blindSolve"` (never show the code to the learner). Re-run `--check`: `lab_ingest` copies the lab to a temp dir, applies the blind-solve files per milestone, and runs both visible and hidden tests (refusing if any fails, if `ambiguous: true`, or if any file matches the reference).
- If blind solve fails or flags `ambiguous: true`, tighten `README.md` / stubs / visible tests once and re-run blind solve.
- If it still fails, log it with `.venv/bin/python -m scripts.issues add --kind prompt --source gate --action auto-fixed --where <LAB_ID>/<MILESTONE> --what "..."` and fix the spec.

## 7. Automated review (reviewer subagent)

Spawn **one** fresh reviewer subagent for the whole lab. Give it the brief, `labs/<LAB_ID>/`, `labs/_reference/<LAB_ID>/`, `rules/04_code.md`, and `docs/prg_reviewer_spec.md`. Tell it to write its verdict to `scratch/reviews/<LAB_ID>-review.json` and reply only `done`.

Ask it to check:
1. **No leaks**: `README.md`, `src/` stubs, `examples`, and `tests/` names/code never reveal the implementation, hidden-test inputs, or trap cases (2–3 normal examples per milestone, plus `constraints` when inputs have limits).
2. **Realistic domain**: production domain, no toy names, different domain from earlier labs in that scope.
3. **Rubric & Layer 3**: every milestone's `qualityChecks` fits the milestone, and `labs/_reference/<LAB_ID>/src/` has zero `must` findings.
4. **Scope & traps**: `unitsUsed` are all in scope (and `Done`/`In progress` for `extra-project`), and each `trapMutant` genuinely embodies a realistic trap.

It writes `{"verdict": "pass" | "fix", "note": "<one sentence>"}`. Copy it into `lab.config.json` as `"review"`.
- On `fix`, fix once, re-run `--check` (and blind solve if `README.md` or stubs changed), and ask the same reviewer to re-check.
- Log every `fix` with `.venv/bin/python -m scripts.issues add ... --source reviewer --action auto-fixed`.

## 8. Final `--check`, finalise, and test

```bash
.venv/bin/python -m code_engine.lab_ingest --check labs/<LAB_ID>
.venv/bin/python -m code_engine.lab_ingest labs/<LAB_ID>
.venv/bin/python -m pytest -q
```

`--check` must print `OK` and exit `0`. Finalise strips `blindSolve` file contents and `trapMutant` code from `lab.config.json` and materialises nothing else. Run the full `pytest` suite after finalise. Never sync or push a lab with a failing test.

Report to the learner in polite Thai in a few lines, **without reference code or hidden tests**: lab ID, kind/level/domain, milestone count, and any issue-log IDs.

## 9. Sync, then ship (in this order)

1. Sync the pristine lab record to Notion per this skill’s workflow from repo root:
   ```bash
   .venv/bin/python -m notion_sync.lab_sync labs/<LAB_ID>
   ```
   (If `degraded: true`, report that Notion was not updated.)
2. Create a branch `lab/<LAB_ID>` (never on `main`), commit **only** `labs/<LAB_ID>/`, `labs/_reference/<LAB_ID>/`, and `id_map.json`, push, and open a PR (`gh pr create`).
3. Verify the PR diff and CI result, then follow `rules/00_core.md` §10 for delivery. Do not repeat or expand the policy here.

## Final documentation check

- [ ] If this PR changes system behaviour, the matching rules/*.md, docs/*.md, CLAUDE.md and skills are updated in the same PR.

## Self-review

After the run, compare the outcome against this skill's goal. For each friction (unclear step, missing tool, gate miss, rework, reviewer catch, or learner correction), log `.venv/bin/python -m scripts.issues propose --target skill:new-project --evidence "<what happened>" --proposal "<concrete change>"` (or `.venv/bin/python -m scripts.issues add --kind <kind> --severity batch --source author --where <where> --what "<what>" --target skill:new-project`). If the fix is a small, scoped edit to this `SKILL.md`, make it in the same PR.
