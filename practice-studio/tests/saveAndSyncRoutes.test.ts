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
