import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { NextRequest } from "next/server";
import { POST as saveStatePOST } from "../src/app/api/save-state/route";
import { POST as syncNotionPOST } from "../src/app/api/sync-notion/route";
import {
  NotionDrillSyncSpawnArgs,
  setNotionDrillSyncSpawnerForTests,
} from "../src/lib/notionSyncRunner";
import { redactProblemStateForClient } from "../src/lib/redact";
import type { ProblemState } from "../src/types/drill";

function makePostReq(url: string, body: unknown): NextRequest {
  return new NextRequest(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

async function main() {
  const tmpRoot = fs.mkdtempSync(path.join(os.tmpdir(), "learningos-save-sync-"));
  const drillId = "DRL-MTH-T01-C01-01";
  const unitCode = "MTH-T01-C01-U01";
  const drillsUnitDir = path.join(tmpRoot, "drills", "data", unitCode);
  fs.mkdirSync(drillsUnitDir, { recursive: true });

  const canonicalDrillDoc = {
    schemaVersion: "2.0",
    drillId,
    subject: "MATH",
    unitCode,
    unitTitle: "Linear Equations",
    problems: [
      {
        id: "Q01",
        prompt: "Solve $2x = 10$.",
        answerPlain: "5",
        answerDisplay: "5",
        steps: [
          { latex: "2x = 10", explain: "Start with the given equation." },
          { latex: "x = 5", explain: "Divide both sides by 2." },
        ],
      },
    ],
  };

  const drillFilePath = path.join(drillsUnitDir, `${drillId}.json`);
  const originalDrillFileContent = JSON.stringify(canonicalDrillDoc, null, 2);
  fs.writeFileSync(drillFilePath, originalDrillFileContent, "utf-8");

  const prevRoot = process.env.LEARNINGOS_ROOT;
  const prevDrillsDir = process.env.DRILLS_DATA_DIR;
  const prevProgressDir = process.env.PROGRESS_DIR;
  const prevPilot = process.env.LEARNINGOS_PILOT;
  const prevDryRun = process.env.NOTION_DRY_RUN;

  process.env.LEARNINGOS_ROOT = tmpRoot;
  delete process.env.DRILLS_DATA_DIR;
  delete process.env.PROGRESS_DIR;
  delete process.env.LEARNINGOS_PILOT;
  delete process.env.NOTION_DRY_RUN;

  try {
    // -------------------------------------------------------------------------
    // 1. /api/save-state validation, normal progress write, pilot mode, and
    //    strict drills/data immutability
    // -------------------------------------------------------------------------
    {
      const missingIdRes = await saveStatePOST(
        makePostReq("http://127.0.0.1:3000/api/save-state", { unitCode })
      );
      assert.equal(missingIdRes.status, 400, "Missing drillId must return 400");

      const unsafeIdRes = await saveStatePOST(
        makePostReq("http://127.0.0.1:3000/api/save-state", {
          drillId: "../escape",
          unitCode,
        })
      );
      assert.equal(unsafeIdRes.status, 400, "Unsafe drillId must return 400");

      const unsafeUnitRes = await saveStatePOST(
        makePostReq("http://127.0.0.1:3000/api/save-state", {
          drillId,
          unitCode: "../evil",
        })
      );
      assert.equal(unsafeUnitRes.status, 400, "Unsafe unitCode must return 400");

      // Normal mode write: writes to <root>/progress/<drillId>.json and never touches drills/data
      const normalSaveRes = await saveStatePOST(
        makePostReq("http://127.0.0.1:3000/api/save-state", {
          drillId,
          unitCode,
          unitTitle: "TAMPERED TITLE",
          sessionSummary: {
            practiceStatus: "In Progress",
            score: 1,
            maxScore: 1,
            accuracyPct: 100,
            mistakeCategories: [],
            divergedStepsSummary: "",
            attemptDate: "2026-11-19",
          },
          problems: [
            {
              id: "Q01",
              prompt: "TAMPERED PROMPT",
              answerPlain: "999",
              state: {
                userInput: "5",
                score: 1,
                divergedStep: null,
                mistakes: [],
                attempts: [{ input: "5", ts: "2026-11-19T00:00:00Z", verdict: "correct" }],
              },
            },
          ],
        })
      );
      assert.equal(normalSaveRes.status, 200);
      const normalSaveBody = (await normalSaveRes.json()) as {
        ok: boolean;
        progressFilePath: string;
      };
      assert.equal(normalSaveBody.ok, true);

      const expectedNormalProgressPath = path.join(tmpRoot, "progress", `${drillId}.json`);
      assert.equal(normalSaveBody.progressFilePath, expectedNormalProgressPath);
      assert.equal(fs.existsSync(expectedNormalProgressPath), true);

      const savedNormalProgress = JSON.parse(
        fs.readFileSync(expectedNormalProgressPath, "utf-8")
      ) as Record<string, unknown>;
      assert.equal(savedNormalProgress.drillId, drillId);
      assert.equal(
        ((savedNormalProgress.problems as Record<string, { score: number }>).Q01).score,
        1
      );
      // Verify progress file does not store curriculum content fields
      assert.equal("unitTitle" in savedNormalProgress, false);

      // Verify drills/data file is byte-for-byte untouched
      assert.equal(
        fs.readFileSync(drillFilePath, "utf-8"),
        originalDrillFileContent,
        "/api/save-state must never write into drills/data"
      );

      // Pilot mode write: writes to <root>/pilot/progress/<drillId>.json and leaves real progress/ untouched
      process.env.LEARNINGOS_PILOT = "1";
      const normalProgressBeforePilot = fs.readFileSync(expectedNormalProgressPath, "utf-8");

      const pilotSaveRes = await saveStatePOST(
        makePostReq("http://127.0.0.1:3000/api/save-state", {
          drillId,
          unitCode,
          sessionSummary: {
            practiceStatus: "Needs Retry",
            score: 0,
            maxScore: 1,
            accuracyPct: 0,
            mistakeCategories: ["sign-error"],
            divergedStepsSummary: "Q01#1",
            attemptDate: "2026-11-19",
          },
          problems: [
            {
              id: "Q01",
              state: {
                userInput: "-5",
                score: 0,
                divergedStep: 0,
                mistakes: ["sign-error"],
                attempts: [{ input: "-5", ts: "2026-11-19T01:00:00Z", verdict: "incorrect" }],
              },
            },
          ],
        })
      );
      assert.equal(pilotSaveRes.status, 200);
      const pilotSaveBody = (await pilotSaveRes.json()) as {
        ok: boolean;
        progressFilePath: string;
      };
      const expectedPilotProgressPath = path.join(
        tmpRoot,
        "pilot",
        "progress",
        `${drillId}.json`
      );
      assert.equal(pilotSaveBody.progressFilePath, expectedPilotProgressPath);
      assert.equal(fs.existsSync(expectedPilotProgressPath), true);

      const savedPilotProgress = JSON.parse(
        fs.readFileSync(expectedPilotProgressPath, "utf-8")
      ) as Record<string, unknown>;
      assert.equal(
        ((savedPilotProgress.problems as Record<string, { userInput: string }>).Q01).userInput,
        "-5"
      );
      assert.equal(
        fs.readFileSync(expectedNormalProgressPath, "utf-8"),
        normalProgressBeforePilot,
        "Pilot mode /api/save-state must not modify non-pilot progress/"
      );
      assert.equal(
        fs.readFileSync(drillFilePath, "utf-8"),
        originalDrillFileContent,
        "Pilot mode /api/save-state must never write into drills/data"
      );
      delete process.env.LEARNINGOS_PILOT;
    }

    // -------------------------------------------------------------------------
    // 2. /api/sync-notion validation, canonical server rehydration, and
    //    stubbed drill_sync spawn args (no real Notion call)
    // -------------------------------------------------------------------------
    {
      const capturedSpawns: NotionDrillSyncSpawnArgs[] = [];
      setNotionDrillSyncSpawnerForTests(async (spawnArgs) => {
        capturedSpawns.push(spawnArgs);
        return {
          code: 0,
          stdout: `[PILOT] skipped Notion write: learner state\n${JSON.stringify({
            ok: true,
            dryRun: spawnArgs.env.NOTION_DRY_RUN === "1",
            notionPageId: "page-stub-123",
          })}`,
          stderr: "",
        };
      });

      const badSyncRes = await syncNotionPOST(
        makePostReq("http://127.0.0.1:3000/api/sync-notion", {
          drillId: "../bad",
          unitCode,
        })
      );
      assert.equal(badSyncRes.status, 400);
      assert.equal(capturedSpawns.length, 0, "Invalid drillId must not spawn drill_sync");

      // Send a redacted client doc (missing answerPlain and steps) with dryRun: true
      const syncRes = await syncNotionPOST(
        makePostReq("http://127.0.0.1:3000/api/sync-notion", {
          drillId,
          unitCode,
          dryRun: true,
          sessionSummary: {
            practiceStatus: "Graded",
            score: 1,
            maxScore: 1,
            accuracyPct: 100,
            mistakeCategories: [],
            divergedStepsSummary: "",
            attemptDate: "2026-11-19",
          },
          problems: [
            {
              id: "Q01",
              prompt: "Solve $2x = 10$.",
              state: {
                userInput: "5",
                score: 1,
                divergedStep: null,
                mistakes: [],
                attempts: [{ input: "5", ts: "2026-11-19T02:00:00Z", verdict: "correct" }],
              },
            },
          ],
        })
      );
      assert.equal(syncRes.status, 200);
      const syncBody = (await syncRes.json()) as {
        ok: boolean;
        dryRun: boolean;
        notionPageId: string;
      };
      assert.equal(syncBody.ok, true);
      assert.equal(syncBody.dryRun, true);
      assert.equal(syncBody.notionPageId, "page-stub-123");

      assert.equal(capturedSpawns.length, 1);
      const spawnCall = capturedSpawns[0];
      assert.equal(spawnCall.cwd, tmpRoot);
      assert.equal(spawnCall.args[0], "-c");
      assert.match(spawnCall.args[1], /from notion_sync\.drill_sync import sync_drill_to_notion/);
      assert.equal(spawnCall.env.PYTHONPATH, tmpRoot);
      assert.equal(spawnCall.env.DRILLS_DATA_DIR, path.join(tmpRoot, "drills", "data"));
      assert.equal(spawnCall.env.NOTION_DRY_RUN, "1");

      // Verify stdin payload rehydrated canonical server steps & answerPlain while merging client state
      const pipedDoc = JSON.parse(spawnCall.stdinPayload) as {
        drillId: string;
        sessionSummary: { practiceStatus: string };
        problems: Array<{
          id: string;
          answerPlain?: string;
          steps?: Array<{ latex: string; explain: string }>;
          state?: { userInput: string; score: number };
        }>;
      };
      assert.equal(pipedDoc.drillId, drillId);
      assert.equal(pipedDoc.sessionSummary.practiceStatus, "Graded");
      assert.equal(pipedDoc.problems[0].answerPlain, "5", "Canonical answerPlain must be rehydrated");
      assert.equal(pipedDoc.problems[0].steps?.length, 2, "Canonical steps must be rehydrated");
      assert.equal(pipedDoc.problems[0].state?.userInput, "5", "Client state must be merged");
      assert.equal(pipedDoc.problems[0].state?.score, 1);

      // Non-zero exit code returns 500
      setNotionDrillSyncSpawnerForTests(async () => ({
        code: 1,
        stdout: "",
        stderr: "Simulated drill_sync failure",
      }));
      const failSyncRes = await syncNotionPOST(
        makePostReq("http://127.0.0.1:3000/api/sync-notion", { drillId, unitCode })
      );
      assert.equal(failSyncRes.status, 500);
      const failBody = (await failSyncRes.json()) as { ok: boolean; error: string };
      assert.equal(failBody.ok, false);
      assert.match(failBody.error, /Simulated drill_sync failure/);
    }

    // -------------------------------------------------------------------------
    // 3. /api/sync-notion MUST preserve server-owned progress (Similar variants
    //    with variantId & matchedTrap, variantsSeen/Attempted, concurrent
    //    reviews/attempts/testRuns/lastTestReport) when client sends a redacted
    //    and stale drill document (skill-review.md Missed Finding 1).
    // -------------------------------------------------------------------------
    {
      const syncDrillId = "DRL-MTH-T01-C01-98";
      const syncDrillDoc = {
        schemaVersion: "2.0",
        drillId: syncDrillId,
        subject: "MATH",
        unitCode,
        chapterCode: "MTH-T01-C01",
        topicCode: "MTH-T01",
        unitTitle: "Linear Equations",
        problems: [
          {
            id: "Q01",
            levelLabel: "Level 1",
            category: "Core Skill",
            prompt: "Solve $2x = 10$.",
            answerPlain: "5",
            answerDisplay: "5",
            steps: [
              { latex: "2x = 10", explain: "Start with the given equation." },
              { latex: "x = 5", explain: "Divide both sides by 2." },
            ],
          },
          {
            id: "Q02",
            levelLabel: "Level 1",
            category: "Core Skill",
            prompt: "Solve $3x = 12$.",
            answerPlain: "4",
            answerDisplay: "4",
            steps: [{ latex: "x = 4", explain: "Divide by 3." }],
          },
        ],
      };
      fs.writeFileSync(
        path.join(drillsUnitDir, `${syncDrillId}.json`),
        JSON.stringify(syncDrillDoc, null, 2),
        "utf-8"
      );

      const diskQ01State: ProblemState = {
        userInput: "5",
        score: 0.5,
        divergedStep: 0,
        mistakes: ["sign-error"],
        mistakeNote: "Initial note",
        revisitNote: "Initial revisit",
        attempts: [
          {
            input: "-5",
            ts: "2026-11-20T09:00:00Z",
            verdict: "incorrect",
            matchedTrap: "sign-flip",
          },
          {
            input: "5",
            ts: "2026-11-20T09:02:00Z",
            verdict: "correct",
          },
          // Concurrent /review attempt written after Studio tab loaded
          {
            input: "5",
            ts: "2026-11-20T11:30:00Z",
            verdict: "correct",
          },
        ],
        // Concurrent code/rubric review written on disk
        reviews: [
          {
            at: "2026-11-20T11:00:00Z",
            attempt: 1,
            codeHash: "sha256:disk-review",
            code: "const x = 5;",
            tests: { passed: 2, total: 2, failed: [] },
            lint: [],
            typecheck: [],
            findings: [],
            verdict: "pass",
            explain: "Server-recorded explanation",
          },
        ],
        testRuns: [
          { ts: "2026-11-20T11:00:00Z", allPassed: true, passedCount: 2, totalCount: 2 },
        ],
        lastTestReport: {
          allPassed: true,
          score: 1,
          passedCount: 2,
          totalCount: 2,
          visibleResults: [],
          hiddenPassed: 1,
          hiddenTotal: 1,
          executionTimeMs: 15,
          ts: "2026-11-20T11:00:00Z",
        },
        variants: {
          vabc123: {
            variantId: "VAR-MTH-T01-C01-U01-linear-01",
            role: "try",
            attempts: [
              {
                input: "-3",
                ts: "2026-11-20T09:05:00Z",
                verdict: "incorrect",
                matchedTrap: "sign-flip",
                kind: "variant",
              },
              {
                input: "3",
                ts: "2026-11-20T09:06:00Z",
                verdict: "correct",
                kind: "variant",
              },
            ],
            hintsRevealed: 1,
            setupRevealed: true,
            stepsRevealed: false,
            durationMs: 4200,
            servedAt: "2026-11-20T09:04:00Z",
          },
          vdef456: {
            variantId: "VAR-MTH-T01-C01-U01-linear-02",
            role: "try",
            attempts: [],
            hintsRevealed: 0,
            setupRevealed: false,
            stepsRevealed: false,
            durationMs: 0,
            servedAt: "",
          },
        },
        similarSlots: ["vabc123", "vdef456"],
        variantsSeen: ["VAR-MTH-T01-C01-U01-linear-01"],
        variantsAttempted: ["VAR-MTH-T01-C01-U01-linear-01"],
        exampleViewedAt: "2026-11-20T09:03:00Z",
        cycleStartedAt: "2026-11-20T11:25:00Z",
        reviewSetupRevealedAt: "2026-11-20T11:26:00Z",
        reviewStepsRevealedAt: "2026-11-20T11:27:00Z",
      };

      const syncProgressPath = path.join(tmpRoot, "progress", `${syncDrillId}.json`);
      fs.mkdirSync(path.dirname(syncProgressPath), { recursive: true });
      fs.writeFileSync(
        syncProgressPath,
        JSON.stringify(
          {
            drillId: syncDrillId,
            unitCode,
            updatedAt: "2026-11-20T11:30:00Z",
            sessionSummary: { practiceStatus: "In Progress", score: 0.5, maxScore: 2 },
            problems: {
              Q01: diskQ01State,
              Q02: {
                userInput: "4",
                score: 1,
                divergedStep: null,
                mistakes: [],
                attempts: [{ input: "4", ts: "2026-11-20T09:10:00Z", verdict: "correct" }],
              },
            },
          },
          null,
          2
        ),
        "utf-8"
      );

      // Build a redacted, stale client state (strips variantId, variantsSeen/Attempted,
      // variant matchedTrap; lacks the concurrent review, concurrent /review attempt,
      // testRuns, lastTestReport, and newer cycle timestamps), while updating learner-editable fields.
      const redactedClientQ01 = redactProblemStateForClient({
        ...diskQ01State,
        attempts: diskQ01State.attempts!.slice(0, 2),
        reviews: [],
        testRuns: [],
        lastTestReport: null,
        cycleStartedAt: null,
        reviewSetupRevealedAt: null,
        reviewStepsRevealedAt: null,
        mistakeNote: "Updated note in Review & Sync",
        revisitNote: "Double-check signs next time",
        mistakes: ["sign-error", "arithmetic"],
      })!;
      assert.equal(
        redactedClientQ01.variants?.vabc123?.variantId,
        undefined,
        "Precondition: redacted client state must not carry variantId"
      );
      assert.equal(
        redactedClientQ01.variants?.vabc123?.attempts?.[0]?.matchedTrap,
        undefined,
        "Precondition: redacted client state must not carry variant matchedTrap"
      );
      assert.equal(
        redactedClientQ01.variantsSeen,
        undefined,
        "Precondition: redacted client state must not carry variantsSeen"
      );

      const syncSpawns: NotionDrillSyncSpawnArgs[] = [];
      setNotionDrillSyncSpawnerForTests(async (spawnArgs) => {
        syncSpawns.push(spawnArgs);
        return {
          code: 0,
          stdout: JSON.stringify({
            ok: true,
            dryRun: true,
            drillPageId: `mock-${syncDrillId}`,
          }),
          stderr: "",
        };
      });

      const preserveRes = await syncNotionPOST(
        makePostReq("http://127.0.0.1:3000/api/sync-notion", {
          drillId: syncDrillId,
          unitCode,
          dryRun: true,
          sessionSummary: {
            practiceStatus: "Graded",
            score: 1.5,
            maxScore: 2,
            accuracyPct: 75,
            mistakeCategories: ["sign-error", "arithmetic"],
            divergedStepsSummary: "Q01 (Updated note in Review & Sync)",
            attemptDate: "2026-11-20",
          },
          problems: [
            {
              id: "Q01",
              prompt: "Solve $2x = 10$.",
              state: redactedClientQ01,
            },
          ],
        })
      );
      assert.equal(preserveRes.status, 200);
      assert.equal(syncSpawns.length, 1);

      // 3a. Python drill_sync must be invoked with save_local=False so TS writeProgress is the single merge/save path
      assert.match(
        syncSpawns[0].args[1],
        /sync_drill_to_notion\(doc,\s*save_local=False\)/,
        "Studio /api/sync-notion must pass save_local=False to avoid a second Python progress overwrite"
      );

      // 3b. Disk progress/<drillId>.json must retain EVERY server-owned field and concurrent record
      const diskAfterSync = JSON.parse(fs.readFileSync(syncProgressPath, "utf-8")) as {
        sessionSummary: Record<string, unknown>;
        problems: Record<string, ProblemState>;
      };
      const savedQ01 = diskAfterSync.problems.Q01;
      assert.equal(
        savedQ01.variants?.vabc123?.variantId,
        "VAR-MTH-T01-C01-U01-linear-01",
        "Sync must never wipe variants[tok].variantId"
      );
      assert.equal(
        savedQ01.variants?.vdef456?.variantId,
        "VAR-MTH-T01-C01-U01-linear-02",
        "Sync must preserve unopened Similar slot variantId"
      );
      assert.equal(
        savedQ01.variants?.vabc123?.attempts?.[0]?.matchedTrap,
        "sign-flip",
        "Sync must preserve variant attempt matchedTrap telemetry"
      );
      assert.deepEqual(savedQ01.similarSlots, ["vabc123", "vdef456"]);
      assert.deepEqual(savedQ01.variantsSeen, ["VAR-MTH-T01-C01-U01-linear-01"]);
      assert.deepEqual(savedQ01.variantsAttempted, ["VAR-MTH-T01-C01-U01-linear-01"]);
      assert.equal(savedQ01.exampleViewedAt, "2026-11-20T09:03:00Z");
      assert.equal(savedQ01.cycleStartedAt, "2026-11-20T11:25:00Z");
      assert.equal(savedQ01.reviewSetupRevealedAt, "2026-11-20T11:26:00Z");
      assert.equal(savedQ01.reviewStepsRevealedAt, "2026-11-20T11:27:00Z");
      assert.equal(savedQ01.reviews?.length, 1, "Sync must preserve concurrent review");
      assert.equal(savedQ01.reviews?.[0]?.explain, "Server-recorded explanation");
      assert.equal(savedQ01.attempts?.length, 3, "Sync must union concurrent attempts");
      assert.equal(savedQ01.attempts?.[0]?.matchedTrap, "sign-flip", "Sync must preserve original attempt matchedTrap");
      assert.equal(savedQ01.testRuns?.length, 1, "Sync must preserve concurrent testRuns");
      assert.equal(savedQ01.lastTestReport?.allPassed, true, "Sync must preserve concurrent lastTestReport");
      assert.equal(diskAfterSync.problems.Q02?.userInput, "4", "Sync must preserve untouched problems on disk");

      // Learner-editable fields and client sessionSummary MUST still be applied
      assert.equal(savedQ01.mistakeNote, "Updated note in Review & Sync");
      assert.equal(savedQ01.revisitNote, "Double-check signs next time");
      assert.deepEqual(savedQ01.mistakes, ["sign-error", "arithmetic"]);
      assert.equal(diskAfterSync.sessionSummary.practiceStatus, "Graded");
      assert.equal(diskAfterSync.sessionSummary.score, 1.5);

      // 3c. The stdin payload sent to Python must also carry the merged server-side progress (not redacted client state)
      const pipedMerged = JSON.parse(syncSpawns[0].stdinPayload) as {
        problems: Array<{ id: string; state?: ProblemState }>;
      };
      const pipedQ01 = pipedMerged.problems.find((p) => p.id === "Q01")?.state;
      assert.equal(
        pipedQ01?.variants?.vabc123?.variantId,
        "VAR-MTH-T01-C01-U01-linear-01",
        "Payload piped to drill_sync must contain merged server variantId"
      );
      assert.equal(
        pipedQ01?.reviews?.length,
        1,
        "Payload piped to drill_sync must contain concurrent disk reviews"
      );
      assert.equal(
        pipedQ01?.attempts?.length,
        3,
        "Payload piped to drill_sync must contain unioned disk attempts"
      );

      // 3d. End-to-end with the REAL Python notion_sync.drill_sync subprocess (dryRun + isolated dirs):
      //     syncing a redacted client doc through the actual route + Python never loses variantId.
      setNotionDrillSyncSpawnerForTests(null);
      const repoRoot = path.resolve(__dirname, "..", "..");
      process.env.LEARNINGOS_ROOT = repoRoot;
      process.env.DRILLS_DATA_DIR = path.join(tmpRoot, "drills", "data");
      process.env.PROGRESS_DIR = path.join(tmpRoot, "progress");
      process.env.NOTION_DRY_RUN = "1";

      const realSyncRes = await syncNotionPOST(
        makePostReq("http://127.0.0.1:3000/api/sync-notion", {
          drillId: syncDrillId,
          unitCode,
          dryRun: true,
          sessionSummary: {
            practiceStatus: "Graded",
            score: 1.5,
            maxScore: 2,
            accuracyPct: 75,
            mistakeCategories: ["sign-error"],
            divergedStepsSummary: "Q01 (End-to-end dry run)",
            attemptDate: "2026-11-20",
          },
          problems: [
            {
              id: "Q01",
              prompt: "Solve $2x = 10$.",
              state: {
                ...redactedClientQ01,
                mistakeNote: "End-to-end dry run note",
              },
            },
          ],
        })
      );
      assert.equal(realSyncRes.status, 200, "Real Python dry-run sync must succeed");
      const realSyncBody = (await realSyncRes.json()) as { ok: boolean; dryRun?: boolean };
      assert.equal(realSyncBody.ok, true);
      assert.equal(realSyncBody.dryRun, true);

      const diskAfterRealSync = JSON.parse(fs.readFileSync(syncProgressPath, "utf-8")) as {
        problems: Record<string, ProblemState>;
      };
      assert.equal(
        diskAfterRealSync.problems.Q01.variants?.vabc123?.variantId,
        "VAR-MTH-T01-C01-U01-linear-01",
        "End-to-end TS + Python sync must never lose variantId"
      );
      assert.equal(
        diskAfterRealSync.problems.Q01.variants?.vabc123?.attempts?.[0]?.matchedTrap,
        "sign-flip",
        "End-to-end TS + Python sync must never lose variant matchedTrap"
      );
      assert.equal(
        diskAfterRealSync.problems.Q01.reviews?.length,
        1,
        "End-to-end TS + Python sync must never lose concurrent review"
      );
      assert.equal(diskAfterRealSync.problems.Q01.mistakeNote, "End-to-end dry run note");

      process.env.LEARNINGOS_ROOT = tmpRoot;
      delete process.env.DRILLS_DATA_DIR;
      delete process.env.PROGRESS_DIR;
      delete process.env.NOTION_DRY_RUN;
    }

    console.log("save-state and sync-notion route tests passed");
  } finally {
    setNotionDrillSyncSpawnerForTests(null);
    if (prevRoot === undefined) delete process.env.LEARNINGOS_ROOT;
    else process.env.LEARNINGOS_ROOT = prevRoot;
    if (prevDrillsDir === undefined) delete process.env.DRILLS_DATA_DIR;
    else process.env.DRILLS_DATA_DIR = prevDrillsDir;
    if (prevProgressDir === undefined) delete process.env.PROGRESS_DIR;
    else process.env.PROGRESS_DIR = prevProgressDir;
    if (prevPilot === undefined) delete process.env.LEARNINGOS_PILOT;
    else process.env.LEARNINGOS_PILOT = prevPilot;
    if (prevDryRun === undefined) delete process.env.NOTION_DRY_RUN;
    else process.env.NOTION_DRY_RUN = prevDryRun;
    fs.rmSync(tmpRoot, { recursive: true, force: true });
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
