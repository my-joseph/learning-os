# PRG Code Reviewer — spec v1 (2026-11-16)

Status: proposal for the learner to read before implementation. Nothing here is built yet.

## Why

Tests only prove that code does the right thing for the inputs they try. The learner also needs to know whether the code is
well built: names, one job per function, no hidden mutation, honest error handling, no needless complexity. Until now the
"review" step (`code_engine/review.py`) only copies a prompt to the clipboard: no fixed criteria, no record, nothing that
stops badly structured code from passing. This spec replaces that with a review that has fixed criteria, blocks a pass,
and keeps data.

## Verdict

A problem is **passed** only when all three layers agree:

| Layer | Checks | Run by | Deterministic |
| :-- | :-- | :-- | :-- |
| 1. Tests | Behaviour: visible tests + hidden tests (from the drill JSON, run in a temp dir) | `node --test` | yes |
| 2. Lint & types | Measurable smells: see rule set below; TypeScript also `tsc --strict --noEmit` | ESLint, tsc | yes |
| 3. Design review | What a tool cannot judge, against the archetype's rubric | Claude (`review-code` skill) | rubric-bound |

Otherwise the verdict is **revise**: the learner fixes and resubmits, like a real pull request. Each submission is one
attempt.

## Layer 2 — lint rule set (one config, repo root)

One `eslint.config.js` at the repo root covers `drills/workspace/**` and `labs/**`, so VS Code shows the same warnings
while the learner types (the ESLint extension picks it up). Tooling is installed once (root `package.json` dev deps), never
per workspace.

Errors (block a pass): `no-var`, `prefer-const`, `eqeqeq`, `no-unused-vars`, `no-param-reassign` (with `props: true`:
no mutation of arguments), `consistent-return`, `no-implicit-coercion`, `require-await`, `no-shadow`,
`no-unreachable`, `complexity` (max 8), `max-depth` (3), `max-params` (4), `max-lines-per-function` (40, skip blank and
comments). TypeScript adds `@typescript-eslint/no-explicit-any`, `no-floating-promises`, `no-misused-promises`,
`strict-boolean-expressions` (from T01-C02 on).

A drill may switch a rule off only with a reason in its spec (`lintOverrides: [{rule, reason}]`), e.g. a "fix the
mutation bug" drill whose starter mutates on purpose.

## Layer 3 — rubric

### Where the criteria live

Each archetype in `code_engine/reasoning_vault/<CHAPTER>.json` gets `qualityChecks`:

```json
"qualityChecks": [
  {"id": "QC-nullish-default", "check": "Defaults use ?? (or an explicit null/undefined test), never ||",
   "why": "|| replaces valid 0, false and '' with the default", "severity": "must"},
  {"id": "QC-guard-first", "check": "Invalid input is rejected at the top with early returns",
   "why": "the happy path stays flat and readable", "severity": "should"}
]
```

Plus a short universal list that applies to every problem (`code_engine/quality_checks.json`):

| id | check | severity |
| :-- | :-- | :-- |
| U-names | Names say what a value is or what a function does; no `data`, `temp`, `x` for domain values | must |
| U-one-job | Each function does one job; a function that validates, transforms and formats is split | should (must from L3) |
| U-no-input-mutation | Arguments are not mutated unless the spec says so | must |
| U-errors | Errors are thrown or returned on purpose; nothing is swallowed by an empty `catch` | must |
| U-no-magic | Unexplained literals become named constants | should |
| U-no-dead-code | No commented-out code, unused branches or leftover `console.log` | should |
| U-simplest | No cleverness the problem does not need (nested ternaries, needless `reduce`) | should |

`must` blocks a pass; `should` is advice and never blocks. Taste (brace style, `for` vs `forEach` when both are clear)
is not a finding at all.

### Review rules (the skill enforces them)

1. Every finding names a check id, a line, what is wrong and **why it matters**. No finding without a check id; a
   reviewer who wants a new criterion proposes it for the vault instead.
2. Hints, not rewrites: at most one line of code in a finding, and never the full solution. The question form is
   preferred ("What does `timeoutSec || 30` return when `timeoutSec` is 0?").
3. The reference solution is shown only after a pass, next to the learner's code, with one paragraph on the differences
   worth noticing (not a ranking).
4. After a pass, the learner answers one "explain" question (step 4 of the practice loop: why does it work, what would
   break it). The answer is recorded, not graded by tests.
5. The learner may dispute a finding. A dispute is logged with `python -m scripts.issues add` and the finding does not
   block while it is open. Upheld disputes change the rubric, so the same mistake is not repeated by the reviewer.

### Calibration (gates at drill ingest)

- The reference solution must pass layer 1 and 2 and have zero `must` findings from layer 3.
- Every `must` check in a drill's archetypes needs at least one **known-bad variant** (a short code snippet in the vault)
  that the check catches, so a check that never fires is visible. These variants double as mutation tests.

## Record (learner progress, not the drill file)

Each attempt is appended to `progress/<DRILL_ID>.json` under the problem's `state.reviews[]`:

```json
{"at": "2026-11-16T10:00:00Z", "attempt": 2, "codeHash": "sha256:…",
 "tests": {"passed": 9, "total": 10, "failed": ["[Q01-HIDDEN-T02] …"]},
 "lint": [{"rule": "no-param-reassign", "line": 12}],
 "findings": [{"check": "U-no-input-mutation", "severity": "must", "line": 12, "note": "…"}],
 "verdict": "revise", "explain": null, "disputes": []}
```

`scripts/weak_spots.py` counts check ids and lint rules across attempts ("you mutated an argument in 4 of the last 6
problems") and picks the next drill's archetypes from them, as it does for math traps. Mastery written to Notion counts a
problem as correct only on a pass.

## Who runs it

- Layers 1 and 2: `npm run check` in the workspace (and the Studio button later) — instant, free.
- Layer 3: the learner asks Claude in Claude Code ("ตรวจโค้ด DRL-PRG-… Q01"); the `review-code` skill runs layers 1–2,
  reads the code, the archetype rubric and the past review records, writes the review and the record. No paid API calls.
- The workspace README says how to ask for a review; `code_engine/review.py`'s clipboard prompt is retired.

## Build order (each one PR)

| PR | Content | By | Status |
| :-- | :-- | :-- | :-- |
| R1 | ESLint + tsc toolkit (`tools/lint/`), `npm run check` in generated workspaces and the lab, tests | Gemini | done |
| R2 | `qualityChecks` schema, universal list, backfill for the 3 PRG vaults, ingest gates (reference clean, known-bad caught) | Gemini, rubric content reviewed by Claude | done |
| R3 | `state.reviews[]` record + `scripts/review_record.py` CLI + weak_spots/mastery reading it, tests | Gemini | pending |
| R4 | `review-code` skill (this document's rules), retire `code_engine/review.py` | Claude | pending |

### R1 deviations from v1 draft
- **Isolated `tools/lint/` instead of repo-root `package.json`:** `practice-studio/` uses ESLint 8 + `.eslintrc` via `next lint`, so ESLint 9 + `typescript-eslint` + `typescript` + `globals` live in `tools/lint/` and each generated workspace / lab imports `prgConfig` from `tools/lint/base.js`.
- **Test-file allowances:** `*.test.*` relaxes `max-lines-per-function` and `max-params`, and `@typescript-eslint/no-floating-promises` allowlists `node:test` lifecycle calls (`test`, `describe`, `it`, `before`, `after`, `beforeEach`, `afterEach`) via `allowForKnownSafeCalls`.
- **Unused stub parameters:** `no-unused-vars` / `@typescript-eslint/no-unused-vars` ignores `^_`-prefixed names (`argsIgnorePattern: "^_"`), and starter code stubs prefix unused parameters with `_` rather than relaxing `no-unused-vars`.
- **Per-workspace `tsconfig.json`:** TypeScript workspaces and `LAB-PRG-T03-C01-01` include a `tsconfig.json` (`strict: true`, `noEmit: true`) so `projectService` and `tsc --noEmit` run deterministically without `allowDefaultProject` file-count limits.

### R2 deviations from v1 draft
- **`knownBad` on every check (including `should`):** Rather than restricting `knownBad` to `must` checks only, every universal and archetype `qualityChecks` entry includes `knownBad: { code, caughtBy }` (`"lint:<rule-id>"` or `"review"` — `"test"` is rejected because behaviour belongs in `hiddenTests`, not `qualityChecks`), and `python -m code_engine.quality_checks --check-vaults` + ingest verify that every `"lint:<rule-id>"` snippet actually triggers that ESLint rule. Checks may also include an optional `accepted` list of acceptable implementations as reviewer hints, while the check itself states a property of the code rather than a mandated API.
- **Ingest Layer 3 calibration scope:** At ingest, `code_engine/ai_drill_ingest.py` validates archetype `qualityChecks`, verifies `lint:<rule-id>` `knownBad` snippets, and runs Layer 2 ESLint (`lint_drill_doc`) on every problem's `solutionCode`; running an LLM review on `solutionCode` at ingest is left manual/out of scope per the no-paid-API-calls rule.

## Out of scope for v1

Studio UI for reviews (UI comes later, with the Math/Programming workspace split in `docs/backlog.md`); reviews of
multi-file projects beyond the lab (the same rubric idea applies, per milestone, once projects are planned).
