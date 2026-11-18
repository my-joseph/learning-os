import assert from "node:assert/strict";
import { NextRequest } from "next/server";
import {
  choosePrimaryAction,
  deriveCodeStatus,
  deriveLabMilestoneStates,
  deriveMilestoneStepperState,
  deriveReviewStatus,
  formatReviewRunFailures,
  isWorkspaceProblem,
  layerSymbol,
  resolveIdeLinks,
  reviewStatusLabel,
  ReviewRunResult,
  sanitizeCodeCheckError,
} from "../src/lib/codeStatus";
import { POST as reviewRunPOST } from "../src/app/api/review-run/route";
import type { ProblemState, ReviewRecord } from "../src/types/drill";

const makeState = (overrides: Partial<ProblemState> = {}): ProblemState => ({
  userInput: "",
  score: null,
  divergedStep: null,
  mistakes: [],
  ...overrides,
});

const makeReview = (
  verdict: "pass" | "revise",
  overrides: Partial<ReviewRecord> = {}
): ReviewRecord => ({
  at: "2026-11-17T10:00:00Z",
  attempt: 1,
  codeHash: "sha256:abc",
  code: "export function solve() { return 1; }",
  tests: { passed: 3, total: 3, failed: [] },
  lint: [],
  typecheck: [],
  findings: [],
  verdict,
  explain: null,
  ...overrides,
});

// 1. Symbols & review status helpers
assert.equal(layerSymbol("pass"), "✓");
assert.equal(layerSymbol("fail"), "✗");
assert.equal(layerSymbol("revise"), "✗");
assert.equal(layerSymbol("not_run"), "–");
assert.equal(layerSymbol("not_requested"), "–");

assert.equal(deriveReviewStatus(undefined), "not_requested");
assert.equal(deriveReviewStatus([]), "not_requested");
assert.equal(deriveReviewStatus([makeReview("revise")]), "revise");
assert.equal(deriveReviewStatus([makeReview("revise"), makeReview("pass")]), "pass");
assert.equal(deriveReviewStatus([makeReview("pass"), makeReview("revise")]), "revise");

assert.equal(reviewStatusLabel("not_requested"), "not requested");
assert.equal(reviewStatusLabel("revise"), "revise");
assert.equal(reviewStatusLabel("pass"), "pass");

// 2. Initial unattempted state -> all not run / not requested, primary action = Open in VS Code
const initialStatus = deriveCodeStatus(makeState(), null, "Q01_clampPort.js");
assert.equal(initialStatus.tests, "not_run");
assert.equal(initialStatus.lint, "not_run");
assert.equal(initialStatus.types, "not_run");
assert.equal(initialStatus.review, "not_requested");
assert.equal(initialStatus.testsSymbol, "–");
assert.equal(initialStatus.lintSymbol, "–");
assert.equal(initialStatus.typesSymbol, "–");
assert.equal(initialStatus.reviewSymbol, "–");
assert.equal(initialStatus.reviewLabel, "not requested");
assert.deepEqual(initialStatus.failures, []);

const initialAction = choosePrimaryAction(
  initialStatus,
  "DRL-PRG-T00-C03-02",
  "Q01"
);
assert.deepEqual(initialAction, {
  kind: "open_vscode",
  label: "Open in VS Code",
});

// 3. Failing review_run JSON -> failures formatted as file:line rule message, primary action = Open in VS Code
const failingRun: ReviewRunResult = {
  drillId: "DRL-PRG-T00-C03-02",
  problemId: "Q01",
  tests: {
    passed: 2,
    total: 3,
    failed: ["[Q01-HIDDEN-T01] rejects negative input"],
  },
  lint: [
    {
      file: "Q01_clampPort.ts",
      line: 12,
      rule: "no-param-reassign",
      message: "Assignment to function parameter 'port'.",
    },
  ],
  typecheck: [
    {
      file: "Q01_clampPort.ts",
      line: 15,
      message: "TS2322: Type 'string' is not assignable to type 'number'.",
    },
  ],
};

const failingStatus = deriveCodeStatus(
  makeState(),
  failingRun,
  "Q01_clampPort.ts"
);
assert.equal(failingStatus.tests, "fail");
assert.equal(failingStatus.lint, "fail");
assert.equal(failingStatus.types, "fail");
assert.equal(failingStatus.review, "not_requested");
assert.equal(failingStatus.testsSymbol, "✗");
assert.equal(failingStatus.lintSymbol, "✗");
assert.equal(failingStatus.typesSymbol, "✗");
assert.deepEqual(failingStatus.failures, [
  "Q01_clampPort.ts:0 test [Q01-HIDDEN-T01] rejects negative input",
  "Q01_clampPort.ts:12 no-param-reassign Assignment to function parameter 'port'.",
  "Q01_clampPort.ts:15 TS2322 Type 'string' is not assignable to type 'number'.",
]);
assert.deepEqual(
  choosePrimaryAction(failingStatus, "DRL-PRG-T00-C03-02", "Q01"),
  {
    kind: "open_vscode",
    label: "Open in VS Code",
  }
);

// 4. Passing tests in review_run, review not requested yet -> Copy review request
const passingRun: ReviewRunResult = {
  drillId: "DRL-PRG-T00-C03-02",
  problemId: "Q01",
  tests: { passed: 3, total: 3, failed: [] },
  lint: [],
  typecheck: [],
};
const passingTestsStatus = deriveCodeStatus(
  makeState(),
  passingRun,
  "Q01_clampPort.js"
);
assert.equal(passingTestsStatus.tests, "pass");
assert.equal(passingTestsStatus.lint, "pass");
assert.equal(passingTestsStatus.types, "pass");
assert.equal(passingTestsStatus.review, "not_requested");
assert.equal(passingTestsStatus.testsSymbol, "✓");
assert.equal(passingTestsStatus.lintSymbol, "✓");
assert.equal(passingTestsStatus.typesSymbol, "✓");
assert.equal(passingTestsStatus.reviewSymbol, "–");

const copyAction = choosePrimaryAction(
  passingTestsStatus,
  "DRL-PRG-T00-C03-02",
  "Q01"
);
assert.deepEqual(copyAction, {
  kind: "copy_review",
  label: "Copy review request",
  reviewCommand: "ตรวจโค้ด DRL-PRG-T00-C03-02 Q01",
});

// 5. Passing tests, review verdict = revise -> primary action stays Copy review request
const reviseState = makeState({
  reviews: [
    makeReview("revise", {
      findings: [
        {
          check: "U-no-input-mutation",
          severity: "must",
          line: 8,
          note: "Mutates caller array in place.",
        },
      ],
    }),
  ],
});
const reviseStatus = deriveCodeStatus(reviseState, null, "Q01_clampPort.js");
assert.equal(reviseStatus.tests, "pass");
assert.equal(reviseStatus.lint, "pass");
assert.equal(reviseStatus.types, "pass");
assert.equal(reviseStatus.review, "revise");
assert.equal(reviseStatus.reviewSymbol, "✗");
assert.equal(reviseStatus.reviewLabel, "revise");
assert.equal(
  choosePrimaryAction(reviseState, "DRL-PRG-T00-C03-02", "Q01").kind,
  "copy_review"
);

// 6. Review verdict = pass -> primary action becomes Next problem
const passState = makeState({
  reviews: [
    makeReview("revise"),
    makeReview("pass", { explain: "Guards non-finite numbers before clamping." }),
  ],
});
const passStatus = deriveCodeStatus(passState, null, "Q01_clampPort.js");
assert.equal(passStatus.tests, "pass");
assert.equal(passStatus.lint, "pass");
assert.equal(passStatus.types, "pass");
assert.equal(passStatus.review, "pass");
assert.equal(passStatus.reviewSymbol, "✓");
assert.equal(passStatus.reviewLabel, "pass");
assert.deepEqual(
  choosePrimaryAction(passStatus, "DRL-PRG-T00-C03-02", "Q01"),
  {
    kind: "next_problem",
    label: "Next problem",
  }
);

// 7. Workspace problem detection & defensive folder link resolution
assert.equal(
  isWorkspaceProblem({
    id: "Q01",
    workspaceFile: "drills/workspace/DRL-PRG-T00-C03-02/Q01_clampPort.js",
  }),
  true
);
assert.equal(
  isWorkspaceProblem({
    id: "Q02",
    codeType: "predict-output",
    answerSpec: { type: "choice", options: [{ id: "A", label: "1" }] },
  }),
  false
);
assert.equal(
  isWorkspaceProblem({
    id: "Q03",
    codeType: "find-bug",
    answerSpec: { type: "line_number" },
  }),
  false
);

const links = resolveIdeLinks({
  workspaceFile: "drills/workspace/DRL-PRG-T00-C03-02/Q01_clampPort.js",
});
assert.equal(links.filename, "Q01_clampPort.js");
assert.equal(links.workspaceDir, "drills/workspace/DRL-PRG-T00-C03-02");
assert.equal(
  links.vscodeFolderUrl,
  "vscode://file/drills/workspace/DRL-PRG-T00-C03-02"
);
assert.equal(
  links.cursorFolderUrl,
  "cursor://file/drills/workspace/DRL-PRG-T00-C03-02"
);
assert.equal(
  links.vscodeFolderUrl.endsWith(".js"),
  false,
  "folder URL must never point to an isolated source file"
);

// 8. formatReviewRunFailures handles plain tsc messages without TS code prefix
assert.deepEqual(
  formatReviewRunFailures(
    {
      typecheck: [{ line: 4, message: "Cannot find name 'window'." }],
    },
    "Q01_app.ts"
  ),
  ["Q01_app.ts:4 tsc Cannot find name 'window'."]
);

// 9. Lab milestone stepper states (passed / regressed / notYet)
assert.equal(deriveMilestoneStepperState(null), "notYet");
assert.equal(deriveMilestoneStepperState(makeState()), "notYet");
assert.equal(
  deriveMilestoneStepperState(
    makeState({
      lastTestReport: {
        allPassed: true,
        score: 1,
        passedCount: 3,
        totalCount: 3,
        visibleResults: [],
        hiddenPassed: 0,
        hiddenTotal: 0,
        executionTimeMs: 5,
      },
    })
  ),
  "notYet",
  "passing tests without a passing review is still notYet"
);
assert.equal(
  deriveMilestoneStepperState(makeState({ reviews: [makeReview("revise")] })),
  "notYet",
  "first-time revise verdict without prior pass is notYet"
);
assert.equal(
  deriveMilestoneStepperState(makeState({ reviews: [makeReview("pass")] })),
  "passed"
);
assert.equal(
  deriveMilestoneStepperState(
    makeState({ reviews: [makeReview("revise"), makeReview("pass")] })
  ),
  "passed"
);
assert.equal(
  deriveMilestoneStepperState(
    makeState({
      reviews: [makeReview("pass")],
      lastTestReport: {
        allPassed: false,
        score: 0.67,
        passedCount: 2,
        totalCount: 3,
        visibleResults: [{ name: "handles edge case", passed: false }],
        hiddenPassed: 0,
        hiddenTotal: 0,
        executionTimeMs: 4,
      },
    })
  ),
  "regressed",
  "passing review followed by failing lastTestReport is regressed"
);
assert.equal(
  deriveMilestoneStepperState(
    makeState({ reviews: [makeReview("pass")] }),
    {
      tests: { passed: 3, total: 3, failed: [] },
      lint: [{ rule: "no-unused-vars", line: 4, message: "Unused x" }],
      typecheck: [],
    }
  ),
  "regressed",
  "passing review followed by failing lint run is regressed"
);
assert.equal(
  deriveMilestoneStepperState(
    makeState({ reviews: [makeReview("pass")] }),
    {
      tests: { passed: 3, total: 3, failed: [] },
      lint: [],
      typecheck: [{ line: 8, message: "TS2322: Type mismatch" }],
    }
  ),
  "regressed",
  "passing review followed by failing typecheck run is regressed"
);
assert.equal(
  deriveMilestoneStepperState(
    makeState({
      reviews: [
        makeReview("pass"),
        makeReview("revise", { tests: { passed: 2, total: 3, failed: ["t1"] } }),
      ],
    })
  ),
  "regressed",
  "passing review followed by revise review is regressed"
);
assert.deepEqual(
  deriveLabMilestoneStates([
    { state: makeState({ reviews: [makeReview("pass")] }) },
    {
      state: makeState({
        reviews: [makeReview("pass")],
        lastTestReport: {
          allPassed: false,
          score: 0,
          passedCount: 0,
          totalCount: 2,
          visibleResults: [],
          hiddenPassed: 0,
          hiddenTotal: 0,
          executionTimeMs: 1,
        },
      }),
    },
    { state: makeState({ reviews: [makeReview("revise")] }) },
    { state: makeState() },
  ]),
  ["passed", "regressed", "notYet", "notYet"]
);

// 10. /api/review-run route validation checks
async function runReviewRunRouteChecks() {
  const badIdReq = new NextRequest("http://127.0.0.1:3000/api/review-run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ drillId: "../etc/passwd", problemId: "Q01" }),
  });
  const badIdRes = await reviewRunPOST(badIdReq);
  assert.equal(badIdRes.status, 400, "Unsafe drillId must be rejected with 400");

  const missingDrillReq = new NextRequest("http://127.0.0.1:3000/api/review-run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ drillId: "DRL-PRG-DOES-NOT-EXIST", problemId: "Q01" }),
  });
  const missingDrillRes = await reviewRunPOST(missingDrillReq);
  assert.equal(missingDrillRes.status, 404, "Unknown drill must return 404");
}

runReviewRunRouteChecks().then(() => {
  // 11. Code check error sanitization strips absolute paths and gives setup hint when tools/lint is missing
  const missingLintErr =
    "Error: Lint toolkit not installed. Expected /Users/Joseph/Documents/antigravity/LearningOS/.claude/worktrees/fix1/tools/lint/base.js and /Users/Joseph/Documents/antigravity/LearningOS/.claude/worktrees/fix1/tools/lint/node_modules/.bin/eslint. Run `npm ci` in tools/lint.";
  const sanitizedMissing = sanitizeCodeCheckError(missingLintErr);
  assert.doesNotMatch(sanitizedMissing, /\/Users\//);
  assert.match(sanitizedMissing, /npm ci/);
  assert.match(sanitizedMissing, /tools\/lint/);

  const absPathErr =
    "Source file for Q01 not found in /Users/Joseph/Documents/antigravity/LearningOS/.claude/worktrees/fix1/drills/workspace/DRL-PRG-01";
  const sanitizedPath = sanitizeCodeCheckError(absPathErr);
  assert.doesNotMatch(sanitizedPath, /\/Users\//);
  assert.match(sanitizedPath, /drills\/workspace\/DRL-PRG-01/);

  console.log("codeStatus tests passed");
});
