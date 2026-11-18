/**
 * Unit & integration tests for project labs API (/api/labs, /api/lab),
 * redaction/zero-reference invariants across all real labs, milestone tiles,
 * CodeDashboard reuse, and DrillSwitcher Labs group.
 */
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { NextRequest } from "next/server";
import { getLabsDir, resolveInsideRoot } from "../src/lib/paths";
import { writeProgress } from "../src/lib/progress";
import {
  deriveMilestoneStepperState,
  deriveMilestoneTileState,
} from "../src/lib/codeStatus";
import {
  ALWAYS_STRIPPED_LAB_FIELDS,
  ALWAYS_STRIPPED_MILESTONE_FIELDS,
  labToDrillDocument,
  listLabsFromDisk,
  loadLabDetailFromDisk,
  type LabDetailResponse,
  type LabListItem,
} from "../src/lib/labs";
import { GET as labsGET } from "../src/app/api/labs/route";
import { GET as labGET } from "../src/app/api/lab/route";
import { QuizPaginationBar } from "../src/components/QuizPaginationBar";
import { CodeDashboard } from "../src/components/code/CodeDashboard";
import { DrillSwitcher } from "../src/components/shell/DrillSwitcher";
import type { ProblemState, ReviewRecord } from "../src/types/drill";

const makeState = (overrides: Partial<ProblemState> = {}): ProblemState => ({
  userInput: "",
  score: null,
  divergedStep: null,
  mistakes: [],
  ...overrides,
});

const makeReview = (verdict: "pass" | "revise"): ReviewRecord => ({
  at: "2026-11-17T12:00:00Z",
  attempt: 1,
  codeHash: "sha256:labtest",
  code: "export class TinyEventEmitter {}",
  tests: { passed: 4, total: 4, failed: [] },
  lint: [],
  typecheck: [],
  findings: [],
  verdict,
  explain: null,
});

// ---------------------------------------------------------------------------
// 1. Path guards: resolveInsideRoot blocks _reference, .canonical, .hidden.
// ---------------------------------------------------------------------------
assert.equal(
  resolveInsideRoot("labs/_reference/LAB-PRG-T01-C01-01/src/index.ts"),
  null,
  "resolveInsideRoot must reject any path under labs/_reference/"
);
assert.equal(
  resolveInsideRoot("labs/_reference/LAB-PRG-T01-C01-01/hidden/m1_hidden.test.ts"),
  null,
  "resolveInsideRoot must reject hidden tests under _reference"
);
assert.equal(
  resolveInsideRoot("drills/workspace/DRL-1/.canonical/Q01.hidden.test.js"),
  null,
  "resolveInsideRoot must reject .canonical / .hidden. files"
);

// ---------------------------------------------------------------------------
// 2. Assert every real lab is listed & NEVER reads or returns _reference,
//    hidden tests, or trapMutants
// ---------------------------------------------------------------------------
async function testAllRealLabs() {
  const realLabsDir = getLabsDir();
  const realLabFolders = fs
    .readdirSync(realLabsDir, { withFileTypes: true })
    .filter((e) => e.isDirectory() && e.name.startsWith("LAB-"))
    .map((e) => e.name)
    .sort();

  assert.ok(
    realLabFolders.length >= 6,
    `Expected at least 6 real labs under ${realLabsDir}, found ${realLabFolders.length}`
  );

  // Spy on fs.readFileSync and fs.readdirSync while calling /api/labs and /api/lab
  const accessedPaths: string[] = [];
  const origReadFileSync = fs.readFileSync;
  const origReaddirSync = fs.readdirSync;

  fs.readFileSync = ((filePath: fs.PathOrFileDescriptor, ...rest: unknown[]) => {
    accessedPaths.push(String(filePath));
    return (origReadFileSync as (...args: unknown[]) => unknown)(filePath, ...rest);
  }) as typeof fs.readFileSync;

  fs.readdirSync = ((dirPath: fs.PathLike, ...rest: unknown[]) => {
    accessedPaths.push(String(dirPath));
    return (origReaddirSync as (...args: unknown[]) => unknown)(dirPath, ...rest);
  }) as typeof fs.readdirSync;

  let listedLabs: LabListItem[] = [];
  const loadedDetails: Record<string, LabDetailResponse> = {};

  try {
    const listRes = await labsGET();
    assert.equal(listRes.status, 200);
    const listBody = await listRes.json();
    listedLabs = listBody.labs as LabListItem[];

    assert.equal(
      listedLabs.length,
      realLabFolders.length,
      "GET /api/labs must list every real lab folder and skip _reference / common"
    );

    for (const labId of realLabFolders) {
      const detailRes = await labGET(
        new NextRequest(`http://127.0.0.1:3000/api/lab?id=${encodeURIComponent(labId)}`)
      );
      assert.equal(detailRes.status, 200, `GET /api/lab?id=${labId} must succeed`);
      loadedDetails[labId] = (await detailRes.json()) as LabDetailResponse;
    }
  } finally {
    fs.readFileSync = origReadFileSync;
    fs.readdirSync = origReaddirSync;
  }

  // Verify NO fs call touched _reference, .canonical, or hidden test directories
  for (const p of accessedPaths) {
    const normalized = p.replace(/\\/g, "/");
    assert.equal(
      normalized.includes("/_reference"),
      false,
      `API must never read or scan labs/_reference/ (accessed: ${p})`
    );
    assert.equal(
      normalized.includes("/hidden"),
      false,
      `API must never read or scan hidden test directories (accessed: ${p})`
    );
  }

  const listJson = JSON.stringify(listedLabs);
  for (const forbidden of [
    "_reference",
    "trapMutant",
    "trapMutants",
    "hiddenTests",
    "blindSolve",
  ]) {
    assert.equal(
      listJson.includes(forbidden),
      false,
      `GET /api/labs response must not contain '${forbidden}'`
    );
  }

  // Now inspect each real lab's _reference directory in the test and assert zero leaks
  for (const labId of realLabFolders) {
    const detail = loadedDetails[labId];
    const detailJson = JSON.stringify(detail);

    assert.equal(detail.id, labId);
    assert.ok(detail.title.length > 0, `${labId}: title must be non-empty`);
    assert.ok(
      detail.unitCode.startsWith("PRG-") || detail.chapterCode.startsWith("PRG-"),
      `${labId}: must have PRG unitCode/chapterCode`
    );
    assert.ok(detail.readme.length > 0, `${labId}: readme must be non-empty`);
    assert.ok(
      detail.vscodeFolderUrl.startsWith("vscode://file/"),
      `${labId}: vscodeFolderUrl must be folder link`
    );
    assert.ok(
      detail.cursorFolderUrl.startsWith("cursor://file/"),
      `${labId}: cursorFolderUrl must be folder link`
    );
    assert.ok(detail.milestones.length >= 1, `${labId}: must have milestones`);

    for (const secretField of ALWAYS_STRIPPED_LAB_FIELDS) {
      assert.equal(
        secretField in (detail as unknown as Record<string, unknown>),
        false,
        `${labId}: top-level field '${secretField}' must not be returned`
      );
    }

    for (const forbiddenToken of [
      "_reference",
      "trapMutant",
      "trapMutants",
      "hiddenTests",
      "blindSolve",
      "test:reference",
      "check:reference",
      "check:hidden",
    ]) {
      assert.equal(
        detailJson.includes(forbiddenToken),
        false,
        `${labId}: GET /api/lab response must not contain '${forbiddenToken}'`
      );
    }

    for (const ms of detail.milestones) {
      assert.ok(/^M\d+$/i.test(ms.id), `${labId}: milestone id ${ms.id} must be M1..Mn`);
      assert.ok(ms.title.length > 0, `${labId}#${ms.id}: title must be non-empty`);
      assert.ok(ms.goal.length > 0, `${labId}#${ms.id}: goal must be non-empty`);
      assert.ok(
        ms.visibleTestFiles.length > 0,
        `${labId}#${ms.id}: visibleTestFiles must be non-empty`
      );
      assert.ok(
        ms.visibleTests.length > 0,
        `${labId}#${ms.id}: visibleTests must be non-empty`
      );
      assert.equal(
        ms.testCommand,
        `npm run test:${ms.id.toLowerCase()}`,
        `${labId}#${ms.id}: testCommand must target milestone`
      );
      for (const secretMsField of ALWAYS_STRIPPED_MILESTONE_FIELDS) {
        assert.equal(
          secretMsField in (ms as unknown as Record<string, unknown>),
          false,
          `${labId}#${ms.id}: milestone field '${secretMsField}' must be stripped`
        );
      }
    }

    // Check against actual files in labs/_reference/<labId>/
    const refDir = path.join(realLabsDir, "_reference", labId);
    if (fs.existsSync(refDir)) {
      const refSrcDir = path.join(refDir, "src");
      if (fs.existsSync(refSrcDir)) {
        for (const f of fs.readdirSync(refSrcDir)) {
          const full = path.join(refSrcDir, f);
          if (!fs.statSync(full).isFile()) continue;
          const refCode = fs.readFileSync(full, "utf-8").trim();
          if (refCode.length >= 20) {
            assert.equal(
              detailJson.includes(JSON.stringify(refCode)),
              false,
              `${labId}: reference source ${f} must never be returned`
            );
          }
        }
      }

      const refHiddenDir = path.join(refDir, "hidden");
      if (fs.existsSync(refHiddenDir)) {
        for (const f of fs.readdirSync(refHiddenDir)) {
          const full = path.join(refHiddenDir, f);
          if (!fs.statSync(full).isFile()) continue;
          const hiddenContent = fs.readFileSync(full, "utf-8");
          const hiddenIdMatches = hiddenContent.match(/\[M\d+-HIDDEN-[^\]]+\]/gi) || [];
          for (const tag of hiddenIdMatches) {
            assert.equal(
              detailJson.includes(tag),
              false,
              `${labId}: hidden test tag ${tag} must never appear in API response`
            );
          }
        }
      }
    }
  }
}

// ---------------------------------------------------------------------------
// 3. Synthetic lab test: strips unfinalised trapMutant/hiddenTests/blindSolve,
//    computes mainFile vscodeUrl/cursorUrl, and reflects progress review states
// ---------------------------------------------------------------------------
async function testSyntheticLabAndProgress() {
  const tmpRoot = fs.mkdtempSync(path.join(os.tmpdir(), "studio-labs-test-"));
  const tmpLabsDir = path.join(tmpRoot, "labs");
  const tmpProgressDir = path.join(tmpRoot, "progress");
  fs.mkdirSync(tmpLabsDir, { recursive: true });
  fs.mkdirSync(tmpProgressDir, { recursive: true });

  const prevLabsDir = process.env.LABS_DIR;
  const prevProgressDir = process.env.PROGRESS_DIR;
  process.env.LABS_DIR = tmpLabsDir;
  process.env.PROGRESS_DIR = tmpProgressDir;

  try {
    const labId = "LAB-PRG-T01-C01-99";
    const labDir = path.join(tmpLabsDir, labId);
    const refDir = path.join(tmpLabsDir, "_reference", labId);
    fs.mkdirSync(path.join(labDir, "src"), { recursive: true });
    fs.mkdirSync(path.join(labDir, "tests"), { recursive: true });
    fs.mkdirSync(path.join(refDir, "src"), { recursive: true });
    fs.mkdirSync(path.join(refDir, "hidden"), { recursive: true });

    fs.writeFileSync(
      path.join(refDir, "src", "emitter.ts"),
      "export const TOP_SECRET_REFERENCE_IMPL = 987654321;\n",
      "utf-8"
    );
    fs.writeFileSync(
      path.join(refDir, "hidden", "m1_hidden.test.ts"),
      'test("[M1-HIDDEN-99] top secret hidden assertion", () => {});\n',
      "utf-8"
    );
    fs.writeFileSync(
      path.join(labDir, "src", "emitter.ts"),
      "export class Emitter {}\n",
      "utf-8"
    );
    fs.writeFileSync(
      path.join(labDir, "tests", "m1_emitter.test.ts"),
      'test("registers listener and returns unsubscribe", () => {});\n',
      "utf-8"
    );
    fs.writeFileSync(
      path.join(labDir, "tests", "m2_pool.test.ts"),
      'test("caps active tasks at concurrency limit", () => {});\n',
      "utf-8"
    );
    fs.writeFileSync(
      path.join(labDir, "tests", "m3_abort.test.ts"),
      'test("cancels queued tasks on abort", () => {});\n',
      "utf-8"
    );
    fs.writeFileSync(
      path.join(labDir, "README.md"),
      [
        "# LAB-PRG-T01-C01-99 — Synthetic Emitter",
        "## Milestones",
        "### M1 — Contracts",
        "Define contracts cleanly.",
        "### M2 — Pool",
        "Run bounded tasks.",
        "### M3 — Abort",
        "Cancel queued tasks.",
        "## Commands",
        "- `npm test` runs visible tests.",
        "- `npm run check:hidden` runs ../_reference/LAB-PRG-T01-C01-99/hidden tests.",
      ].join("\n"),
      "utf-8"
    );

    const unfinalisedCfg = {
      labId,
      title: "Synthetic Emitter",
      chapterCode: "PRG-T01-C01",
      unitsUsed: ["PRG-T01-C01-U02"],
      kind: "chapter-lab",
      level: 3,
      domain: "emitter",
      scenario: "Build a synthetic emitter.",
      milestones: [
        {
          id: "M1",
          title: "Contracts",
          goal: "Define contracts.",
          mainFile: "src/emitter.ts",
          visibleTests: "tests/m1_*.test.ts",
          trapMutant: {
            files: { "src/emitter.ts": "SECRET_TRAP_MUTANT_CODE_123" },
          },
          hiddenTests: ["SECRET_INLINE_HIDDEN_TEST_123"],
        },
        {
          id: "M2",
          title: "Pool",
          goal: "Run bounded pool.",
          mainFile: "../_reference/LAB-PRG-T01-C01-99/src/emitter.ts",
          visibleTests: "tests/m2_*.test.ts",
        },
        {
          id: "M3",
          title: "Abort",
          goal: "Support abort.",
          visibleTests: "tests/m3_*.test.ts",
        },
      ],
      blindSolve: [
        {
          milestone: "M1",
          files: { "src/emitter.ts": "SECRET_BLIND_SOLVE_CODE_123" },
        },
      ],
      review: {
        verdict: "pass",
        note: "SECRET_REVIEWER_SUBAGENT_NOTE_123",
      },
    };
    fs.writeFileSync(
      path.join(labDir, "lab.config.json"),
      JSON.stringify(unfinalisedCfg, null, 2),
      "utf-8"
    );

    // Record progress: M1 = pass, M2 = revise, M3 = not started
    writeProgress({
      drillId: labId,
      unitCode: "PRG-T01-C01",
      problems: [
        { id: "M1", state: makeState({ reviews: [makeReview("pass")] }) },
        { id: "M2", state: makeState({ reviews: [makeReview("revise")] }) },
      ],
    });

    const labs = listLabsFromDisk();
    assert.equal(labs.length, 1);
    assert.equal(labs[0].id, labId);
    assert.equal(labs[0].milestoneCount, 3);
    assert.equal(labs[0].passedCount, 1);
    assert.equal(labs[0].reviseCount, 1);
    assert.equal(labs[0].practiceStatus, "In Progress");
    assert.deepEqual(labs[0].progress.milestones, {
      M1: "pass",
      M2: "revise",
      M3: "not_requested",
    });

    const detail = loadLabDetailFromDisk(labId);
    assert.ok(detail);
    const detailJson = JSON.stringify(detail);

    for (const secret of [
      "SECRET_TRAP_MUTANT_CODE_123",
      "SECRET_INLINE_HIDDEN_TEST_123",
      "SECRET_BLIND_SOLVE_CODE_123",
      "SECRET_REVIEWER_SUBAGENT_NOTE_123",
      "TOP_SECRET_REFERENCE_IMPL",
      "M1-HIDDEN-99",
      "_reference",
      "check:hidden",
    ]) {
      assert.equal(
        detailJson.includes(secret),
        false,
        `Synthetic secret '${secret}' must never appear in loaded lab detail`
      );
    }

    // M1 has valid mainFile inside labDir
    assert.equal(detail.milestones[0].mainFile, "src/emitter.ts");
    assert.ok(detail.milestones[0].vscodeUrl?.endsWith("/src/emitter.ts"));
    assert.ok(detail.milestones[0].cursorUrl?.endsWith("/src/emitter.ts"));
    assert.equal(detail.milestones[0].reviewStatus, "pass");

    // M2 had a mainFile pointing into ../_reference -> rejected to null
    assert.equal(detail.milestones[1].mainFile, null);
    assert.equal(detail.milestones[1].vscodeUrl, null);
    assert.equal(detail.milestones[1].cursorUrl, null);
    assert.equal(detail.milestones[1].reviewStatus, "revise");

    // M3 has no mainFile and no reviews
    assert.equal(detail.milestones[2].mainFile, null);
    assert.equal(detail.milestones[2].reviewStatus, "not_requested");

    // Test UI components with this lab
    const drillDoc = labToDrillDocument(detail);
    assert.equal(deriveMilestoneTileState(drillDoc.problems[0].state), "pass");
    assert.equal(deriveMilestoneTileState(drillDoc.problems[1].state), "revise");
    assert.equal(deriveMilestoneTileState(drillDoc.problems[2].state), "not_started");
    assert.equal(deriveMilestoneStepperState(drillDoc.problems[0].state), "passed");
    assert.equal(deriveMilestoneStepperState(drillDoc.problems[1].state), "notYet");
    assert.equal(deriveMilestoneStepperState(drillDoc.problems[2].state), "notYet");

    const noop = () => {};
    const stepperHtml = renderToStaticMarkup(
      <QuizPaginationBar
        totalQuestions={drillDoc.problems.length}
        currentIndex={1}
        problems={drillDoc.problems}
        viewMode="quiz"
        isLab={true}
        onSelectQuestion={noop}
        onPrev={noop}
        onNext={noop}
        onToggleViewMode={noop}
      />
    );
    assert.match(stepperHtml, /<nav[^>]*aria-label="Lab milestones"/);
    assert.match(stepperHtml, />M1</);
    assert.match(stepperHtml, />M2</);
    assert.match(stepperHtml, />M3</);
    assert.doesNotMatch(stepperHtml, />Review<\/span>/); // icon-only Review step
    assert.match(stepperHtml, /aria-label="Review &amp; sync"/);
    assert.match(stepperHtml, /aria-label="M1 — passed"/);
    assert.match(stepperHtml, /aria-label="M2 — not passed yet"[^>]*aria-current="step"/);
    assert.match(stepperHtml, /aria-label="M3 — not passed yet"/);
    assert.match(stepperHtml, /bg-indigo-600/, "M1 (passed) dot and line must be indigo");
    assert.match(stepperHtml, /border-zinc-300/, "M3 (not passed yet) dot must be hollow grey");
    assert.match(stepperHtml, /ring-2 ring-indigo-600/, "Current milestone must have indigo ring");
    assert.match(stepperHtml, /aria-label="Review &amp; sync"/);
    assert.doesNotMatch(stepperHtml, /overflow-x-auto/, "3 milestones fit without horizontal scroll");

    // Verify regressed milestone renders amber dot while keeping indigo connector line
    const regressedProblems = drillDoc.problems.map((p, i) =>
      i === 1
        ? {
            ...p,
            state: {
              ...p.state,
              reviews: [makeReview("pass")],
              lastTestReport: {
                allPassed: false,
                score: 0.5,
                passedCount: 1,
                totalCount: 2,
                visibleResults: [{ name: "fails after refactor", passed: false }],
                hiddenPassed: 0,
                hiddenTotal: 0,
                executionTimeMs: 3,
              },
            },
          }
        : p
    );
    const regressedStepperHtml = renderToStaticMarkup(
      <QuizPaginationBar
        totalQuestions={regressedProblems.length}
        currentIndex={2}
        problems={regressedProblems}
        viewMode="quiz"
        isLab={true}
        onSelectQuestion={noop}
        onPrev={noop}
        onNext={noop}
        onToggleViewMode={noop}
      />
    );
    assert.match(regressedStepperHtml, /aria-label="M2 — regressed"/);
    assert.match(regressedStepperHtml, /bg-amber-600/, "Regressed milestone dot must be amber");
    assert.match(regressedStepperHtml, /aria-label="M3 — not passed yet"[^>]*aria-current="step"/);

    // >8 milestones enable horizontal scroll
    const manyMilestones = Array.from({ length: 9 }, (_, i) => ({
      ...drillDoc.problems[0],
      id: `M${i + 1}`,
      state: makeState(),
    }));
    const scrollingStepperHtml = renderToStaticMarkup(
      <QuizPaginationBar
        totalQuestions={manyMilestones.length}
        currentIndex={0}
        problems={manyMilestones}
        viewMode="quiz"
        isLab={true}
        onSelectQuestion={noop}
        onPrev={noop}
        onNext={noop}
        onToggleViewMode={noop}
      />
    );
    assert.match(scrollingStepperHtml, /overflow-x-auto/);

    const labReviewStepperHtml = renderToStaticMarkup(
      <QuizPaginationBar
        totalQuestions={drillDoc.problems.length}
        currentIndex={1}
        problems={drillDoc.problems}
        viewMode="review"
        isLab={true}
        onSelectQuestion={noop}
        onPrev={noop}
        onNext={noop}
        onToggleViewMode={noop}
      />
    );
    assert.match(
      labReviewStepperHtml,
      /aria-label="Review &amp; sync"[^>]*aria-pressed="true"[^>]*aria-current="step"/
    );

    // Render CodeDashboard for M2 (revise, tests passed)
    const dashboardHtml = renderToStaticMarkup(
      <CodeDashboard
        problem={drillDoc.problems[1]}
        drillId={drillDoc.drillId}
        index={1}
        totalQuestions={drillDoc.problems.length}
        drillTitle={drillDoc.unitTitle}
        labReadme={drillDoc.labReadme}
        mistakeTags={[]}
        activeStep={null}
        onInputChange={noop}
        onCheckAnswer={noop}
        onToggleStepHighlight={noop}
        onMarkDivergedStep={noop}
        onSetScore={noop}
        onToggleMistakeTag={noop}
        onMistakeNoteChange={noop}
        onResetProblem={noop}
      />
    );
    assert.match(dashboardHtml, /Milestone M2 \(2 of 3\)/);
    assert.match(dashboardHtml, /caps active tasks at concurrency limit/);
    assert.match(dashboardHtml, /npm run test:m2/);
    assert.match(dashboardHtml, /Copy review request/);
    assert.match(dashboardHtml, /ตรวจโค้ด LAB-PRG-T01-C01-99 M2/);
    assert.match(dashboardHtml, /Lab README/);
    assert.doesNotMatch(dashboardHtml, /Unlocks after review passes/);

    // Render DrillSwitcher open with drills + labs
    const refObj = { current: null };
    const switcherHtml = renderToStaticMarkup(
      <DrillSwitcher
        isOpen={true}
        onToggle={noop}
        onClose={noop}
        switcherRef={refObj}
        currentDrill={drillDoc}
        drills={[
          {
            drillId: "DRL-PRG-T01-C01-U01-01",
            subject: "PRG",
            unitCode: "PRG-T01-C01-U01",
            unitTitle: "Execution Context and Scope",
            createdAt: "2026-11-17",
            questionCount: 4,
            difficultyMode: "Mixed",
            practiceStatus: "Ready",
            score: 0,
            maxScore: 4,
            localFilePath: "",
          },
        ]}
        labs={labs}
        selectedDrillId={labId}
        drillSearch=""
        onSearchChange={noop}
        drillFilter="ALL"
        onFilterChange={noop}
        onSelectDrill={noop}
      />
    );
    assert.match(switcherHtml, />Labs</);
    assert.match(switcherHtml, /Synthetic Emitter/);
    assert.match(switcherHtml, /PRG-T01-C01 · 3 Ms/);
    assert.doesNotMatch(switcherHtml, /LAB-PRG-T01-C01-99/);

    // Route rejection checks
    const badRes1 = await labGET(new NextRequest("http://127.0.0.1:3000/api/lab?id=_reference"));
    assert.equal(badRes1.status, 400);
    const badRes2 = await labGET(
      new NextRequest("http://127.0.0.1:3000/api/lab?id=DRL-PRG-T01-01")
    );
    assert.equal(badRes2.status, 400);
    const notFoundRes = await labGET(
      new NextRequest("http://127.0.0.1:3000/api/lab?id=LAB-DOES-NOT-EXIST")
    );
    assert.equal(notFoundRes.status, 404);
  } finally {
    if (prevLabsDir === undefined) {
      delete process.env.LABS_DIR;
    } else {
      process.env.LABS_DIR = prevLabsDir;
    }
    if (prevProgressDir === undefined) {
      delete process.env.PROGRESS_DIR;
    } else {
      process.env.PROGRESS_DIR = prevProgressDir;
    }
    fs.rmSync(tmpRoot, { recursive: true, force: true });
  }
}

async function main() {
  await testAllRealLabs();
  await testSyntheticLabAndProgress();
  console.log("labs tests passed");
}

main();
