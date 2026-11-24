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
  setNotionDrillSyncTimeoutForTests,
} from "../src/lib/notionSyncRunner";
import { redactProblemStateForClient } from "../src/lib/redact";
import { summaryFingerprint } from "../src/lib/sessionSummary";
import type { ProblemState, SessionSummary } from "../src/types/drill";

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

      const unknownId = "DRL-MTH-T01-C01-99";
      const unknownPath = path.join(drillsUnitDir, `${unknownId}.json`);
      const unknownProgress = path.join(tmpRoot, "progress", `${unknownId}.json`);
      const syncRequest = () => makePostReq("http://127.0.0.1:3000/api/sync-notion", {
        drillId: unknownId,
        unitCode,
        problems: [{ id: "Q01", state: { attempts: [{ input: "5", verdict: "correct" }] } }],
        sessionSummary: { score: 1, attemptDate: "2026-11-19" },
      });
      assert.equal((await syncNotionPOST(syncRequest())).status, 404, "No canonical file");
      fs.writeFileSync(unknownPath, originalDrillFileContent);
      assert.equal((await syncNotionPOST(syncRequest())).status, 404, "Internal drill ID mismatch");
      fs.writeFileSync(unknownPath, JSON.stringify({ ...canonicalDrillDoc, drillId: unknownId }));
      assert.equal((await syncNotionPOST(syncRequest())).status, 409, "Request is not saved evidence");
      assert.equal((await syncNotionPOST(syncRequest())).status, 409, "Retry cannot promote request evidence");
      assert.equal(fs.existsSync(unknownProgress), false);
      assert.equal(capturedSpawns.length, 0);

      const lockedProgress = JSON.stringify({
        drillId: unknownId,
        unitCode,
        problems: {
          Q01: {
            cycleStartedAt: "2026-11-19T02:00:00.500Z",
            attempts: [
              { ts: "2026-11-19T02:00:00Z", verdict: "correct" },
              { ts: "2026-11-19T02:00:01Z", verdict: "parse_error" },
              { ts: "2026-11-19T02:00:02Z", kind: "variant", verdict: "correct" },
            ],
          },
          Q99: { attempts: [{ verdict: "correct" }] },
        },
      });
      fs.writeFileSync(unknownProgress, lockedProgress);
      assert.equal((await syncNotionPOST(syncRequest())).status, 409);
      assert.equal(fs.readFileSync(unknownProgress, "utf-8"), lockedProgress);
      assert.equal(capturedSpawns.length, 0);

      fs.writeFileSync(unknownPath, JSON.stringify({
        ...canonicalDrillDoc,
        drillId: unknownId,
        problems: [canonicalDrillDoc.problems[0], canonicalDrillDoc.problems[0]],
      }));
      assert.equal((await syncNotionPOST(syncRequest())).status, 422);
      assert.equal(fs.readFileSync(unknownProgress, "utf-8"), lockedProgress);
      assert.equal(capturedSpawns.length, 0);

      // Send a redacted client doc (missing answerPlain and steps) with dryRun: true
      const syncRes = await syncNotionPOST(
        makePostReq("http://127.0.0.1:3000/api/sync-notion", {
          drillId,
          unitCode: "MTH-T01-C01-U09",
          dryRun: true,
          sessionSummary: {
            practiceStatus: "Graded",
            score: 99,
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
                userInput: "999",
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

      // The helper receives canonical content and previously saved progress.
      const pipedDoc = JSON.parse(spawnCall.stdinPayload) as {
        drillId: string;
        unitCode: string;
        sessionSummary: { practiceStatus: string; score: number };
        problems: Array<{
          id: string;
          answerPlain?: string;
          steps?: Array<{ latex: string; explain: string }>;
          state?: { userInput: string; score: number };
        }>;
      };
      assert.equal(pipedDoc.drillId, drillId);
      assert.equal(pipedDoc.unitCode, unitCode);
      assert.equal(pipedDoc.sessionSummary.practiceStatus, "Graded");
      assert.equal(pipedDoc.sessionSummary.score, 1);
      assert.equal(pipedDoc.problems[0].answerPlain, "5", "Canonical answerPlain must be rehydrated");
      assert.equal(pipedDoc.problems[0].steps?.length, 2, "Canonical steps must be rehydrated");
      assert.equal(pipedDoc.problems[0].state?.userInput, "5", "Sync uses previously saved state");
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
      const saveEditedNote = (state: ProblemState) => saveStatePOST(
        makePostReq("http://127.0.0.1:3000/api/save-state", {
          drillId: syncDrillId, unitCode, problems: [{ id: "Q01", state }],
        })
      );
      assert.equal((await saveEditedNote(redactedClientQ01)).status, 200);

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
              state: { ...redactedClientQ01, mistakeNote: "Stale unsaved note" },
            },
            { id: "Q99", state: redactedClientQ01 },
          ],
        })
      );
      assert.equal(preserveRes.status, 200);
      assert.equal(syncSpawns.length, 1);

      // 3a. The Python bridge uses the Studio result path and does not save progress.
      assert.match(
        syncSpawns[0].args[1],
        /sync_drill_to_notion\(doc, save_local=False, studio_results=True\)/,
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

      // Autosaved edits survive, and the summary is recomputed from the saved cycle.
      assert.equal(savedQ01.mistakeNote, "Updated note in Review & Sync");
      assert.equal(savedQ01.revisitNote, "Double-check signs next time");
      assert.deepEqual(savedQ01.mistakes, ["sign-error", "arithmetic"]);
      assert.equal(diskAfterSync.problems.Q99, undefined);
      assert.equal(diskAfterSync.sessionSummary.practiceStatus, "Needs Retry");
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
      assert.equal((await saveEditedNote({
        ...redactedClientQ01,
        mistakeNote: "End-to-end dry run note",
      })).status, 200);

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

    // -------------------------------------------------------------------------
    // 4. Server-authoritative sync stamps:
    //    - Real (non-pilot, non-dry-run, non-degraded) sync writes
    //      syncedToNotionAt, notionPageId, and syncedFingerprint to disk and
    //      returns them in the JSON response.
    //    - Later /api/save-state autosave lacking stamps (or passing null/forged
    //      stamps) NEVER clears or overrides them.
    //    - Dry-run, pilot, and degraded syncs NEVER stamp (and preserve prior stamps).
    //    - A newer real sync advances syncedToNotionAt and updates syncedFingerprint.
    // -------------------------------------------------------------------------
    {
      const stampDrillId = "DRL-MTH-T01-C01-77";
      const stampDrillDoc = {
        ...canonicalDrillDoc,
        drillId: stampDrillId,
      };
      fs.writeFileSync(
        path.join(drillsUnitDir, `${stampDrillId}.json`),
        JSON.stringify(stampDrillDoc, null, 2),
        "utf-8"
      );
      const stampProgressPath = path.join(tmpRoot, "progress", `${stampDrillId}.json`);
      const firstSummary: SessionSummary = {
        practiceStatus: "Graded",
        score: 1,
        maxScore: 1,
        accuracyPct: 100,
        skippedCount: 0,
        skippedProblems: [],
        mistakeCategories: [],
        divergedStepsSummary: "No diverged steps logged.",
        attemptDate: "2026-11-21",
      };
      const saveStampAttempt = (divergedStep: number | null) => saveStatePOST(
        makePostReq("http://127.0.0.1:3000/api/save-state", {
          drillId: stampDrillId,
          unitCode,
          problems: [{
            id: "Q01",
            state: {
              userInput: "5", score: 1, divergedStep, mistakes: [],
              attempts: [{ input: "5", verdict: "correct", ts: "2026-11-21T00:00:00Z" }],
            },
          }],
        })
      );
      assert.equal((await saveStampAttempt(null)).status, 200);

      // 4a. Pilot mode, dryRun, and degraded NEVER stamp a fresh drill.
      setNotionDrillSyncSpawnerForTests(async () => ({
        code: 0,
        stdout: JSON.stringify({ ok: true, dryRun: true, drillPageId: "mock-77" }),
        stderr: "",
      }));
      const dryRes = await syncNotionPOST(
        makePostReq("http://127.0.0.1:3000/api/sync-notion", {
          drillId: stampDrillId,
          unitCode,
          dryRun: true,
          sessionSummary: firstSummary,
          problems: [{ id: "Q01", state: { userInput: "5", score: 1, mistakes: [] } }],
        })
      );
      assert.equal(dryRes.status, 200);
      const dryBody = (await dryRes.json()) as Record<string, unknown>;
      assert.equal(dryBody.syncedToNotionAt, undefined, "dryRun response must not include syncedToNotionAt");
      let diskStamp = JSON.parse(fs.readFileSync(stampProgressPath, "utf-8")) as {
        sessionSummary: Record<string, unknown>;
      };
      assert.equal(diskStamp.sessionSummary.syncedToNotionAt, undefined, "dryRun must never stamp disk");
      assert.equal(diskStamp.sessionSummary.syncedFingerprint, undefined, "dryRun must never stamp fingerprint");

      // Pilot mode acknowledges locally even if there is no pilot progress.
      process.env.LEARNINGOS_PILOT = "1";
      setNotionDrillSyncSpawnerForTests(async () => assert.fail("Pilot sync must never spawn the helper"));
      const pilotSyncRes = await syncNotionPOST(
        makePostReq("http://127.0.0.1:3000/api/sync-notion", {
          drillId: stampDrillId,
          unitCode,
          sessionSummary: firstSummary,
          problems: [{ id: "Q01", state: { userInput: "5", score: 1, mistakes: [] } }],
        })
      );
      assert.equal(pilotSyncRes.status, 200);
      const pilotSyncBody = (await pilotSyncRes.json()) as Record<string, unknown>;
      assert.equal(pilotSyncBody.pilotSkipped, true);
      assert.equal(pilotSyncBody.syncedToNotionAt, undefined, "pilot sync must never return syncedToNotionAt");
      const pilotStampPath = path.join(tmpRoot, "pilot", "progress", `${stampDrillId}.json`);
      assert.equal(fs.existsSync(pilotStampPath), false, "pilot sync must never create progress");
      delete process.env.LEARNINGOS_PILOT;

      // Degraded sync must never stamp
      setNotionDrillSyncSpawnerForTests(async () => ({
        code: 0,
        stdout: JSON.stringify({
          ok: true,
          degraded: true,
          drillPageId: null,
          warning: "Saved locally; Notion unavailable",
        }),
        stderr: "",
      }));
      const degradedRes = await syncNotionPOST(
        makePostReq("http://127.0.0.1:3000/api/sync-notion", {
          drillId: stampDrillId,
          unitCode,
          sessionSummary: firstSummary,
          problems: [{ id: "Q01", state: { userInput: "5", score: 1, mistakes: [] } }],
        })
      );
      assert.equal(degradedRes.status, 200);
      const degradedBody = (await degradedRes.json()) as Record<string, unknown>;
      assert.equal(degradedBody.syncedToNotionAt, undefined, "degraded sync must not return syncedToNotionAt");
      diskStamp = JSON.parse(fs.readFileSync(stampProgressPath, "utf-8"));
      assert.equal(diskStamp.sessionSummary.syncedToNotionAt, undefined, "degraded sync must never stamp disk");

      // 4b. Real successful sync writes stamps to disk AND returns them
      setNotionDrillSyncSpawnerForTests(async () => ({
        code: 0,
        stdout: JSON.stringify({
          ok: true,
          drillPageId: "real-notion-page-77",
          parentPageId: "unit-page-1",
          unitReviews: {},
        }),
        stderr: "",
      }));
      const realSuccessRes = await syncNotionPOST(
        makePostReq("http://127.0.0.1:3000/api/sync-notion", {
          drillId: stampDrillId,
          unitCode,
          sessionSummary: firstSummary,
          problems: [{ id: "Q01", state: { userInput: "5", score: 1, mistakes: [] } }],
        })
      );
      assert.equal(realSuccessRes.status, 200);
      const realSuccessBody = (await realSuccessRes.json()) as {
        ok: boolean;
        drillPageId: string;
        syncedToNotionAt: string;
        notionPageId: string;
        syncedFingerprint: string;
      };
      assert.equal(realSuccessBody.ok, true);
      assert.ok(realSuccessBody.syncedToNotionAt, "real sync must return syncedToNotionAt");
      assert.equal(realSuccessBody.notionPageId, "real-notion-page-77");
      assert.equal(
        realSuccessBody.syncedFingerprint,
        summaryFingerprint(firstSummary),
        "syncedFingerprint must match the synced summary"
      );

      diskStamp = JSON.parse(fs.readFileSync(stampProgressPath, "utf-8"));
      assert.equal(diskStamp.sessionSummary.syncedToNotionAt, realSuccessBody.syncedToNotionAt);
      assert.equal(diskStamp.sessionSummary.notionPageId, "real-notion-page-77");
      assert.equal(diskStamp.sessionSummary.syncedFingerprint, summaryFingerprint(firstSummary));

      // 4c. Later /api/save-state autosave lacking stamps (or passing null/forged stamps) preserves server stamps
      const autosaveWithoutStamps = await saveStatePOST(
        makePostReq("http://127.0.0.1:3000/api/save-state", {
          drillId: stampDrillId,
          unitCode,
          sessionSummary: {
            ...firstSummary,
            divergedStepsSummary: "Q01 (Note: added after sync)",
            syncedToNotionAt: null,
            notionPageId: null,
            syncedFingerprint: null,
          },
          problems: [
            {
              id: "Q01",
              state: { userInput: "5", score: 1, mistakes: [], revisitNote: "Check signs" },
            },
          ],
        })
      );
      assert.equal(autosaveWithoutStamps.status, 200);
      diskStamp = JSON.parse(fs.readFileSync(stampProgressPath, "utf-8"));
      assert.equal(
        diskStamp.sessionSummary.syncedToNotionAt,
        realSuccessBody.syncedToNotionAt,
        "autosave must never clear syncedToNotionAt"
      );
      assert.equal(
        diskStamp.sessionSummary.notionPageId,
        "real-notion-page-77",
        "autosave must never clear notionPageId"
      );
      assert.equal(
        diskStamp.sessionSummary.syncedFingerprint,
        summaryFingerprint(firstSummary),
        "autosave must never clear syncedFingerprint"
      );
      assert.equal(
        diskStamp.sessionSummary.divergedStepsSummary,
        "Q01 (Note: added after sync)",
        "non-stamp summary fields must still update"
      );

      // Client attempting to forge a newer stamp via /api/save-state must be ignored
      await saveStatePOST(
        makePostReq("http://127.0.0.1:3000/api/save-state", {
          drillId: stampDrillId,
          unitCode,
          sessionSummary: {
            ...firstSummary,
            syncedToNotionAt: "2099-01-01T00:00:00.000Z",
            notionPageId: "forged-page",
            syncedFingerprint: "forged-fp",
          },
          problems: [{ id: "Q01", state: { userInput: "5", score: 1, mistakes: [] } }],
        })
      );
      diskStamp = JSON.parse(fs.readFileSync(stampProgressPath, "utf-8"));
      assert.equal(diskStamp.sessionSummary.syncedToNotionAt, realSuccessBody.syncedToNotionAt);
      assert.equal(diskStamp.sessionSummary.notionPageId, "real-notion-page-77");
      assert.equal(diskStamp.sessionSummary.syncedFingerprint, summaryFingerprint(firstSummary));

      // 4d. A newer real sync advances syncedToNotionAt and updates syncedFingerprint
      const updatedSummary: SessionSummary = {
        ...firstSummary,
        divergedStepsSummary: "Q01 (Step 2: Divide both sides by 2.)",
      };
      assert.equal((await saveStampAttempt(1)).status, 200);
      const secondSuccessRes = await syncNotionPOST(
        makePostReq("http://127.0.0.1:3000/api/sync-notion", {
          drillId: stampDrillId,
          unitCode: "MTH-T01-C01-U09",
          sessionSummary: updatedSummary,
          problems: [{ id: "Q01", state: { userInput: "5", score: 1, divergedStep: 1, mistakes: [] } }],
        })
      );
      assert.equal(secondSuccessRes.status, 200);
      const secondSuccessBody = (await secondSuccessRes.json()) as {
        syncedToNotionAt: string;
        syncedFingerprint: string;
      };
      assert.ok(
        secondSuccessBody.syncedToNotionAt > realSuccessBody.syncedToNotionAt,
        "newer real sync must advance syncedToNotionAt monotonically"
      );
      assert.equal(secondSuccessBody.syncedFingerprint, summaryFingerprint(updatedSummary));
      diskStamp = JSON.parse(fs.readFileSync(stampProgressPath, "utf-8"));
      assert.equal((diskStamp as { unitCode?: string }).unitCode, unitCode);
      assert.equal(diskStamp.sessionSummary.syncedToNotionAt, secondSuccessBody.syncedToNotionAt);
      assert.equal(diskStamp.sessionSummary.syncedFingerprint, summaryFingerprint(updatedSummary));

      // 4e. Timeout / hang path: a hanging Python process is killed and returns 504 (preserving prior stamps)
      setNotionDrillSyncSpawnerForTests(async () => ({
        code: null,
        stdout: "",
        stderr: "Notion sync timed out after 90s.",
        timedOut: true,
      }));
      const timeoutRes = await syncNotionPOST(
        makePostReq("http://127.0.0.1:3000/api/sync-notion", {
          drillId: stampDrillId,
          unitCode,
          sessionSummary: updatedSummary,
          problems: [{ id: "Q01", state: { userInput: "5", score: 1, mistakes: [] } }],
        })
      );
      assert.equal(timeoutRes.status, 504, "timed out sync must return HTTP 504");
      const timeoutBody = (await timeoutRes.json()) as {
        ok: boolean;
        timedOut?: boolean;
        error?: string;
      };
      assert.equal(timeoutBody.ok, false);
      assert.equal(timeoutBody.timedOut, true);
      assert.match(timeoutBody.error || "", /timed out/i);
      diskStamp = JSON.parse(fs.readFileSync(stampProgressPath, "utf-8"));
      assert.equal(
        diskStamp.sessionSummary.syncedToNotionAt,
        secondSuccessBody.syncedToNotionAt,
        "timed out sync must preserve existing server stamps"
      );

      // 4f. Real child_process timeout in defaultDrillSyncSpawner kills a hanging subprocess promptly
      setNotionDrillSyncSpawnerForTests(null);
      setNotionDrillSyncTimeoutForTests(150);
      const sleepBin = path.join(tmpRoot, "hang-python.sh");
      fs.writeFileSync(sleepBin, "#!/bin/sh\nexec sleep 10\n", { mode: 0o755 });
      const { runNotionDrillSync } = await import("../src/lib/notionSyncRunner");
      const startMs = Date.now();
      const hangResult = await runNotionDrillSync({
        mergedDoc: { drillId: stampDrillId },
        rootDir: tmpRoot,
        pythonBin: sleepBin,
        dataDir: path.join(tmpRoot, "drills", "data"),
        isDryRun: true,
      });
      const elapsedMs = Date.now() - startMs;
      assert.equal(hangResult.timedOut, true, "default spawner must report timedOut=true on hang");
      assert.equal(hangResult.code, null);
      assert.match(hangResult.stderr, /timed out/i);
      assert.ok(elapsedMs < 3_000, `hung subprocess must be killed promptly (took ${elapsedMs}ms)`);
      setNotionDrillSyncTimeoutForTests(null);
    }

    console.log("save-state and sync-notion route tests passed");
  } finally {
    setNotionDrillSyncSpawnerForTests(null);
    setNotionDrillSyncTimeoutForTests(null);
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
