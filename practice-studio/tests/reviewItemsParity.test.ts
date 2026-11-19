/**
 * Parity and route tests for per-item review scheduling:
 * compares Python (`scripts/review_items.py`) and TypeScript (`src/lib/reviewItems.ts`),
 * plus `/api/review-items` (GET due list redacted + POST outcome recording) and `/api/save-state` revisitNote.
 */
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { NextRequest } from "next/server";
import {
  DEFAULT_ITEM_DURATION_MS,
  REVIEW_INTERVALS,
  addDays,
  buildScheduleFromProgress,
  estimateReviewMinutes,
  getDueReviewItems,
  interleaveDueItems,
  extractReviewEvents,
  normalizeReviewDate,
  parseReviewScope,
  prioritizeDueItems,
  recordReviewItemResult,
  stepReviewSchedule,
  ReviewItem,
} from "../src/lib/reviewItems";
import { GET as reviewItemsGET, POST as reviewItemsPOST } from "../src/app/api/review-items/route";
import { POST as saveStatePOST } from "../src/app/api/save-state/route";

async function runTests() {
  // 1. Pure scheduling transitions in TypeScript
  assert.deepEqual(REVIEW_INTERVALS, { 1: 1, 2: 3, 3: 7, 4: 16, 5: 35 });
  assert.deepEqual(
    stepReviewSchedule(1, { correct: true, hintsUsed: false, date: "2026-11-01" }),
    { level: 2, lastReviewed: "2026-11-01", dueDate: "2026-11-04" }
  );
  assert.deepEqual(
    stepReviewSchedule(2, { correct: true, hintsUsed: true, date: "2026-11-04" }),
    { level: 2, lastReviewed: "2026-11-04", dueDate: "2026-11-07" }
  );
  assert.deepEqual(
    stepReviewSchedule(5, { correct: true, hintsUsed: 0, date: "2026-11-10" }),
    { level: 5, lastReviewed: "2026-11-10", dueDate: "2026-12-15" }
  );
  assert.deepEqual(
    stepReviewSchedule(5, { correct: false, hintsUsed: false, date: "2026-11-10" }),
    { level: 2, lastReviewed: "2026-11-10", dueDate: "2026-11-11" }
  );
  assert.deepEqual(
    stepReviewSchedule(3, { correct: false, hintsUsed: 1, date: "2026-11-10" }),
    { level: 1, lastReviewed: "2026-11-10", dueDate: "2026-11-11" }
  );
  assert.equal(addDays("2026-11-10", 35), "2026-12-15");

  // Local calendar boundary parity, including timestamps between midnight and 06:59 in UTC+7.
  const previousTz = process.env.TZ;
  process.env.TZ = "Asia/Bangkok";
  try {
    const localDates = [
      normalizeReviewDate("2026-11-18T17:00:00Z"),
      normalizeReviewDate("2026-11-18T23:59:00Z"),
      normalizeReviewDate("2026-11-18T16:59:00Z"),
      extractReviewEvents({ attempts: [{ verdict: "correct" }] })[0]?.date,
    ];
    assert.deepEqual(localDates, ["2026-11-19", "2026-11-19", "2026-11-18", "1970-01-01"]);
    const root = path.resolve(process.cwd(), "..");
    const pyDates = spawnSync(
      process.env.PYTHON ||
        (fs.existsSync(path.join(root, ".venv", "bin", "python"))
          ? path.join(root, ".venv", "bin", "python")
          : "python3"),
      ["-c", "from scripts.review_items import _normalize_date, extract_review_events; import json; print(json.dumps([_normalize_date('2026-11-18T17:00:00Z'), _normalize_date('2026-11-18T23:59:00Z'), _normalize_date('2026-11-18T16:59:00Z'), extract_review_events({'attempts':[{'verdict':'correct'}]})[0]['date']]))"],
      { cwd: root, encoding: "utf8", env: { ...process.env, TZ: "Asia/Bangkok" } }
    );
    assert.equal(pyDates.status, 0, pyDates.stderr);
    assert.deepEqual(JSON.parse(pyDates.stdout), localDates);
  } finally {
    if (previousTz === undefined) delete process.env.TZ;
    else process.env.TZ = previousTz;
  }

  // 2. Python <-> TypeScript parity on a shared multi-unit, multi-subject fixture
  const root = path.resolve(process.cwd(), "..");
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "learningos-review-items-parity-"));
  const dataDir = path.join(tmp, "drills", "data");
  const progressDir = path.join(tmp, "progress");
  const labsDir = path.join(tmp, "labs");

  const prevProgressDir = process.env.PROGRESS_DIR;
  const prevDrillsDir = process.env.DRILLS_DATA_DIR;
  const prevLabsDir = process.env.LABS_DIR;

  try {
    fs.mkdirSync(path.join(dataDir, "MTH-T01-C04-U01"), { recursive: true });
    fs.mkdirSync(path.join(dataDir, "MTH-T01-C04-U02"), { recursive: true });
    fs.mkdirSync(path.join(dataDir, "PRG-T01-C01-U01"), { recursive: true });
    fs.mkdirSync(progressDir, { recursive: true });
    fs.mkdirSync(labsDir, { recursive: true });

    const mthU1Drill = {
      drillId: "DRL-MTH-T01-C04-U01-01",
      unitCode: "MTH-T01-C04-U01",
      problems: [
        {
          id: "Q01",
          level: 2,
          commonTrapTag: "c04-divide-not-invert-trap",
          archetypeKey: "fraction-division",
          answerDisplay: "SECRET_42",
          answerPlain: "SECRET_42",
          answerSpec: { type: "number", value: "SECRET_42" },
          steps: [{ latex: "x = 42", explain: "SECRET_STEP_EXPLAIN" }],
        },
        {
          id: "Q02",
          level: 3,
          commonTrapTag: "c04-sign-drop-trap",
          archetypeKey: "signed-fractions",
          answerDisplay: "SECRET_99",
          steps: [{ latex: "y = 99", explain: "SECRET_STEP_2" }],
        },
        {
          id: "Q03",
          level: 4,
          commonTrapTag: "c04-reciprocal-flip-trap",
          archetypeKey: "complex-fraction",
        },
      ],
    };
    const mthU1File = path.join(dataDir, "MTH-T01-C04-U01", "DRL-MTH-T01-C04-U01-01.json");
    const mthU1OriginalText = JSON.stringify(mthU1Drill, null, 2);
    fs.writeFileSync(mthU1File, mthU1OriginalText, "utf-8");

    fs.writeFileSync(
      path.join(dataDir, "MTH-T01-C04-U02", "DRL-MTH-T01-C04-U02-01.json"),
      JSON.stringify({
        drillId: "DRL-MTH-T01-C04-U02-01",
        unitCode: "MTH-T01-C04-U02",
        problems: [
          {
            id: "Q01",
            level: 2,
            commonTrapTag: "c04-lcd-mismatch-trap",
            archetypeKey: "unlike-denominators",
          },
          {
            id: "Q02",
            level: 2,
            commonTrapTag: "c04-cancel-term-trap",
            archetypeKey: "term-cancellation",
          },
        ],
      }),
      "utf-8"
    );

    fs.writeFileSync(
      path.join(dataDir, "PRG-T01-C01-U01", "DRL-PRG-T01-C01-U01-01.json"),
      JSON.stringify({
        drillId: "DRL-PRG-T01-C01-U01-01",
        subject: "PRG",
        unitCode: "PRG-T01-C01-U01",
        problems: [
          {
            id: "Q01",
            level: 2,
            archetypeKey: "array-guard",
            solutionCode: "function secretSolution() { return 123; }",
          },
        ],
      }),
      "utf-8"
    );

    fs.writeFileSync(
      path.join(progressDir, "DRL-MTH-T01-C04-U01-01.json"),
      JSON.stringify({
        drillId: "DRL-MTH-T01-C04-U01-01",
        updatedAt: "2026-11-18T10:00:00Z",
        problems: {
          Q01: {
            attempts: [
              { verdict: "correct", ts: "2026-10-20T10:00:00Z" },
              { verdict: "correct", ts: "2026-10-23T10:00:00Z" },
              { verdict: "correct", ts: "2026-10-30T10:00:00Z" },
              { verdict: "incorrect", ts: "2026-11-17T10:00:00Z" },
            ],
            score: 0,
            hintsRevealed: 0,
            revisitNote: "Flip the divisor before cancelling common factors.",
          },
          Q02: {
            attempts: [{ verdict: "correct", ts: "2026-11-17T12:00:00Z" }],
            score: 0.5,
            hintsRevealed: 1,
            revisitNote: "Keep negative sign attached to numerator.",
          },
          Q03: {
            attempts: [{ verdict: "correct", ts: "2026-11-18T12:00:00Z" }],
            score: 1.0,
            hintsRevealed: 0,
          },
        },
      }),
      "utf-8"
    );

    fs.writeFileSync(
      path.join(progressDir, "DRL-MTH-T01-C04-U02-01.json"),
      JSON.stringify({
        drillId: "DRL-MTH-T01-C04-U02-01",
        updatedAt: "2026-11-17T15:00:00Z",
        problems: {
          Q01: {
            skipped: true,
            score: 0,
          },
          Q02: {
            lastCheck: { verdict: "correct" },
            setupRevealedBeforeAnswer: true,
            score: 0.5,
          },
        },
      }),
      "utf-8"
    );

    fs.writeFileSync(
      path.join(progressDir, "DRL-PRG-T01-C01-U01-01.json"),
      JSON.stringify({
        drillId: "DRL-PRG-T01-C01-U01-01",
        updatedAt: "2026-11-18T09:00:00Z",
        problems: {
          Q01: {
            reviews: [
              {
                at: "2026-11-18T09:00:00Z",
                verdict: "revise",
                findings: [{ check: "U-edge-empty", severity: "must", line: 3, note: "guard" }],
                lint: [],
              },
            ],
            revisitNote: "Check for empty array before indexing.",
          },
        },
      }),
      "utf-8"
    );

    process.env.PROGRESS_DIR = progressDir;
    process.env.DRILLS_DATA_DIR = dataDir;
    process.env.LABS_DIR = labsDir;

    const tsSchedule = buildScheduleFromProgress({
      dataDir,
      progressDir,
      labsDir,
      rootDir: root,
    });
    const tsDue = getDueReviewItems({
      today: "2026-11-19",
      dataDir,
      progressDir,
      labsDir,
      rootDir: root,
    });

    const venvPython = path.join(root, ".venv", "bin", "python");
    const python = process.env.PYTHON || (fs.existsSync(venvPython) ? venvPython : "python3");

    const pyAll = spawnSync(
      python,
      [
        "-m",
        "scripts.review_items",
        "--today",
        "2026-11-19",
        "--data-root",
        dataDir,
        "--progress-dir",
        progressDir,
        "--json",
      ],
      {
        cwd: root,
        encoding: "utf8",
        env: { ...process.env, PROGRESS_DIR: progressDir, DRILLS_DATA_DIR: dataDir, LABS_DIR: labsDir },
      }
    );
    if (pyAll.status !== 0) {
      throw new Error(`Python review_items failed: ${pyAll.stderr}`);
    }
    const pyAllJson = JSON.parse(pyAll.stdout) as { items: ReviewItem[] };
    const pyScheduleMap: Record<string, ReviewItem> = {};
    for (const item of pyAllJson.items) {
      pyScheduleMap[`${item.drillId}/${item.qid}`] = item;
    }

    assert.deepEqual(
      tsSchedule,
      pyScheduleMap,
      "TypeScript and Python backfilled schedules must match 100%"
    );

    const pyDue = spawnSync(
      python,
      [
        "-m",
        "scripts.review_items",
        "--due",
        "--today",
        "2026-11-19",
        "--data-root",
        dataDir,
        "--progress-dir",
        progressDir,
        "--json",
      ],
      {
        cwd: root,
        encoding: "utf8",
        env: { ...process.env, PROGRESS_DIR: progressDir, DRILLS_DATA_DIR: dataDir, LABS_DIR: labsDir },
      }
    );
    if (pyDue.status !== 0) {
      throw new Error(`Python review_items --due failed: ${pyDue.stderr}`);
    }
    const pyDueJson = JSON.parse(pyDue.stdout) as { today: string; items: ReviewItem[] };

    assert.deepEqual(
      tsDue.items,
      pyDueJson.items,
      "TypeScript and Python interleaved due lists must match 100%"
    );

    // Verify interleaving: no two adjacent items share unitCode
    for (let i = 0; i < tsDue.items.length - 1; i += 1) {
      assert.notEqual(
        tsDue.items[i].unitCode,
        tsDue.items[i + 1].unitCode,
        `Adjacent due items at ${i} and ${i + 1} must not come from the same unit`
      );
    }

    // 3. Test /api/review-items GET (redaction + revisitNote + limit)
    const getRes = await reviewItemsGET(
      new NextRequest("http://127.0.0.1:3000/api/review-items?today=2026-11-19")
    );
    assert.equal(getRes.status, 200);
    const getBodyText = await getRes.text();
    assert.ok(!getBodyText.includes("SECRET_42"), "GET /api/review-items must never leak answerDisplay/answerSpec");
    assert.ok(!getBodyText.includes("SECRET_STEP"), "GET /api/review-items must never leak steps");
    assert.ok(!getBodyText.includes("secretSolution"), "GET /api/review-items must never leak solutionCode");

    const getJson = JSON.parse(getBodyText) as { today: string; items: ReviewItem[] };
    assert.equal(getJson.today, "2026-11-19");
    assert.equal(getJson.items.length, 5);
    const q1Item = getJson.items.find(
      (it) => it.drillId === "DRL-MTH-T01-C04-U01-01" && it.qid === "Q01"
    );
    assert.ok(q1Item);
    assert.equal(q1Item.revisitNote, "Flip the divisor before cancelling common factors.");

    // 4. Test /api/save-state updating revisitNote and reflecting in GET /api/review-items without touching drill file
    const saveRes = await saveStatePOST(
      new NextRequest("http://127.0.0.1:3000/api/save-state", {
        method: "POST",
        body: JSON.stringify({
          drillId: "DRL-MTH-T01-C04-U01-01",
          unitCode: "MTH-T01-C04-U01",
          problems: [
            {
              id: "Q01",
              state: {
                attempts: [
                  { verdict: "correct", ts: "2026-10-20T10:00:00Z" },
                  { verdict: "correct", ts: "2026-10-23T10:00:00Z" },
                  { verdict: "correct", ts: "2026-10-30T10:00:00Z" },
                  { verdict: "incorrect", ts: "2026-11-17T10:00:00Z" },
                ],
                score: 0,
                hintsRevealed: 0,
                revisitNote: "Updated note: invert the second fraction immediately.",
              },
            },
            {
              id: "Q02",
              state: {
                attempts: [{ verdict: "correct", ts: "2026-11-17T12:00:00Z" }],
                score: 0.5,
                hintsRevealed: 1,
                revisitNote: "Keep negative sign attached to numerator.",
              },
            },
            {
              id: "Q03",
              state: {
                attempts: [{ verdict: "correct", ts: "2026-11-18T12:00:00Z" }],
                score: 1.0,
                hintsRevealed: 0,
              },
            },
          ],
        }),
      })
    );
    assert.equal(saveRes.status, 200);
    assert.equal(
      fs.readFileSync(mthU1File, "utf-8"),
      mthU1OriginalText,
      "save-state must never modify drill content file in drills/data"
    );

    const getAfterNote = await reviewItemsGET(
      new NextRequest("http://127.0.0.1:3000/api/review-items?today=2026-11-19")
    );
    const afterNoteJson = (await getAfterNote.json()) as { items: ReviewItem[] };
    const updatedQ1 = afterNoteJson.items.find(
      (it) => it.drillId === "DRL-MTH-T01-C04-U01-01" && it.qid === "Q01"
    );
    assert.equal(updatedQ1?.revisitNote, "Updated note: invert the second fraction immediately.");

    // 5. Test /api/review-items POST records outcome and updates review_items.json store
    const postRes = await reviewItemsPOST(
      new NextRequest("http://127.0.0.1:3000/api/review-items", {
        method: "POST",
        body: JSON.stringify({
          drillId: "DRL-MTH-T01-C04-U01-01",
          qid: "Q01",
          correct: true,
          hintsUsed: false,
          date: "2026-11-19",
        }),
      })
    );
    assert.equal(postRes.status, 200);
    const postJson = (await postRes.json()) as { ok: boolean; item: ReviewItem };
    assert.equal(postJson.ok, true);
    // Q01 was at level 2 -> correct without hint -> level 3 (due in 7 days = 2026-11-26)
    assert.equal(postJson.item.level, 3);
    assert.equal(postJson.item.lastReviewed, "2026-11-19");
    assert.equal(postJson.item.dueDate, "2026-11-26");

    // Store file on disk was created and updated
    const storeFile = path.join(progressDir, "review_items.json");
    assert.ok(fs.existsSync(storeFile));

    // POST validation rejects unsafe drillId
    const badPost = await reviewItemsPOST(
      new NextRequest("http://127.0.0.1:3000/api/review-items", {
        method: "POST",
        body: JSON.stringify({
          drillId: "../etc/passwd",
          qid: "Q01",
          correct: true,
          hintsUsed: false,
        }),
      })
    );
    assert.equal(badPost.status, 400);

    // 6. Test pure interleaveDueItems and recordReviewItemResult directly
    const directUpdated = recordReviewItemResult(
      {
        drillId: "DRL-MTH-T01-C04-U01-01",
        qid: "Q01",
        correct: false,
        hintsUsed: true,
        date: "2026-11-26",
      },
      { dataDir, progressDir, labsDir, rootDir: root }
    );
    // Level 3 wrong -> halved to 1, due next day (2026-11-27)
    assert.equal(directUpdated.level, 1);
    assert.equal(directUpdated.dueDate, "2026-11-27");

    const syntheticInterleave = interleaveDueItems([
      {
        drillId: "D1",
        qid: "Q1",
        unitCode: "MTH-U1",
        subject: "MTH",
        commonTrapTag: null,
        archetypeKey: null,
        level: 1,
        lastReviewed: "2026-11-10",
        dueDate: "2026-11-15",
        revisitNote: null,
      },
      {
        drillId: "D1",
        qid: "Q2",
        unitCode: "MTH-U1",
        subject: "MTH",
        commonTrapTag: null,
        archetypeKey: null,
        level: 1,
        lastReviewed: "2026-11-10",
        dueDate: "2026-11-15",
        revisitNote: null,
      },
      {
        drillId: "D2",
        qid: "Q1",
        unitCode: "PRG-U1",
        subject: "PRG",
        commonTrapTag: null,
        archetypeKey: null,
        level: 1,
        lastReviewed: "2026-11-10",
        dueDate: "2026-11-11",
        revisitNote: null,
      },
    ]);
    assert.deepEqual(
      syntheticInterleave.map((x) => x.unitCode),
      ["MTH-U1", "PRG-U1", "MTH-U1"]
    );

    // 7. Priority rule (wrong-last > open weak spot > most overdue, pick-then-interleave),
    //    all 5 scope filters, HTTP redaction on scope=trap:..., and duration estimation parity
    const priTmp = fs.mkdtempSync(path.join(os.tmpdir(), "learningos-review-priority-parity-"));
    const priData = path.join(priTmp, "drills", "data");
    const priProgress = path.join(priTmp, "progress");
    const priLabs = path.join(priTmp, "labs");
    try {
      for (const sub of [
        "MTH-T01-C04-U01",
        "MTH-T01-C04-U02",
        "MTH-T02-C01-U01",
        "PRG-T01-C01-U01",
      ]) {
        fs.mkdirSync(path.join(priData, sub), { recursive: true });
      }
      fs.mkdirSync(priProgress, { recursive: true });
      fs.mkdirSync(priLabs, { recursive: true });

      fs.writeFileSync(
        path.join(priData, "MTH-T01-C04-U01", "DRL-MTH-T01-C04-U01-01.json"),
        JSON.stringify({
          drillId: "DRL-MTH-T01-C04-U01-01",
          unitCode: "MTH-T01-C04-U01",
          unitTitle: "Fraction Division",
          problems: [
            { id: "Q01", level: 2, commonTrapTag: "c04-open-weak-trap", archetypeKey: "a1" },
            { id: "Q02", level: 2, commonTrapTag: "c04-closed-trap", archetypeKey: "a2" },
          ],
        }),
        "utf-8"
      );
      fs.writeFileSync(
        path.join(priData, "MTH-T01-C04-U02", "DRL-MTH-T01-C04-U02-01.json"),
        JSON.stringify({
          drillId: "DRL-MTH-T01-C04-U02-01",
          unitCode: "MTH-T01-C04-U02",
          unitTitle: "Signed Fractions",
          problems: [
            { id: "Q01", level: 2, commonTrapTag: "c04-other-trap", archetypeKey: "b1" },
            { id: "Q02", level: 2, commonTrapTag: "c04-open-weak-trap", archetypeKey: "b2" },
          ],
        }),
        "utf-8"
      );
      fs.writeFileSync(
        path.join(priData, "MTH-T02-C01-U01", "DRL-MTH-T02-C01-U01-01.json"),
        JSON.stringify({
          drillId: "DRL-MTH-T02-C01-U01-01",
          unitCode: "MTH-T02-C01-U01",
          unitTitle: "Complex Numbers",
          problems: [
            { id: "Q01", level: 2, commonTrapTag: "t02-sign-trap", archetypeKey: "c1" },
          ],
        }),
        "utf-8"
      );
      fs.writeFileSync(
        path.join(priData, "PRG-T01-C01-U01", "DRL-PRG-T01-C01-U01-01.json"),
        JSON.stringify({
          drillId: "DRL-PRG-T01-C01-U01-01",
          subject: "PRG",
          unitCode: "PRG-T01-C01-U01",
          unitTitle: "Array Guards",
          problems: [
            { id: "Q01", level: 2, archetypeKey: "p1" },
            { id: "Q02", level: 2, archetypeKey: "p2" },
          ],
        }),
        "utf-8"
      );

      fs.writeFileSync(
        path.join(priProgress, "DRL-MTH-T01-C04-U01-01.json"),
        JSON.stringify({
          drillId: "DRL-MTH-T01-C04-U01-01",
          updatedAt: "2026-11-17T10:00:00Z",
          problems: {
            Q01: {
              attempts: [
                {
                  verdict: "incorrect",
                  ts: "2026-11-10T10:00:00Z",
                  matchedTrap: "c04-open-weak-trap",
                  durationMs: 120000,
                },
                {
                  verdict: "correct",
                  ts: "2026-11-17T10:00:00Z",
                  assisted: true,
                  durationMs: 60000,
                },
              ],
              score: 0.5,
              hintsRevealed: 1,
            },
            Q02: {
              attempts: [
                { verdict: "correct", ts: "2026-11-02T10:00:00Z", durationMs: 180000 },
              ],
              score: 1.0,
            },
          },
        }),
        "utf-8"
      );
      fs.writeFileSync(
        path.join(priProgress, "DRL-MTH-T01-C04-U02-01.json"),
        JSON.stringify({
          drillId: "DRL-MTH-T01-C04-U02-01",
          updatedAt: "2026-11-18T10:00:00Z",
          problems: {
            Q01: {
              attempts: [
                { verdict: "incorrect", ts: "2026-11-18T10:00:00Z", durationMs: 120000 },
              ],
              score: 0,
            },
            Q02: {
              attempts: [
                {
                  verdict: "incorrect",
                  ts: "2026-11-15T10:00:00Z",
                  matchedTrap: "c04-open-weak-trap",
                  durationMs: 120000,
                },
                {
                  verdict: "correct",
                  ts: "2026-11-15T10:05:00Z",
                  durationMs: 60000,
                },
              ],
              score: 0.5,
            },
          },
        }),
        "utf-8"
      );
      fs.writeFileSync(
        path.join(priProgress, "DRL-MTH-T02-C01-U01-01.json"),
        JSON.stringify({
          drillId: "DRL-MTH-T02-C01-U01-01",
          updatedAt: "2026-11-07T10:00:00Z",
          problems: {
            Q01: {
              attempts: [
                { verdict: "correct", ts: "2026-11-07T10:00:00Z", durationMs: 120000 },
              ],
              score: 1.0,
            },
          },
        }),
        "utf-8"
      );
      fs.writeFileSync(
        path.join(priProgress, "DRL-PRG-T01-C01-U01-01.json"),
        JSON.stringify({
          drillId: "DRL-PRG-T01-C01-U01-01",
          updatedAt: "2026-11-18T09:00:00Z",
          problems: {
            Q01: {
              reviews: [
                {
                  at: "2026-11-18T09:00:00Z",
                  verdict: "revise",
                  findings: [{ check: "U-edge-empty", severity: "must", line: 2, note: "guard" }],
                  lint: [],
                },
              ],
              durationMs: 240000,
            },
            Q02: {
              reviews: [
                {
                  at: "2026-11-14T09:00:00Z",
                  verdict: "revise",
                  findings: [{ check: "U-edge-empty", severity: "must", line: 4, note: "guard" }],
                  lint: [],
                },
                {
                  at: "2026-11-16T09:00:00Z",
                  verdict: "pass",
                  findings: [],
                  lint: [],
                },
              ],
              durationMs: 180000,
            },
          },
        }),
        "utf-8"
      );

      process.env.PROGRESS_DIR = priProgress;
      process.env.DRILLS_DATA_DIR = priData;
      process.env.LABS_DIR = priLabs;

      const cases: Array<{ scope?: string; limit?: number }> = [
        { limit: 4 },
        { scope: "subject:MTH" },
        { scope: "subject:PRG" },
        { scope: "unit:MTH-T01-C04-U01" },
        { scope: "chapter:MTH-T01-C04" },
        { scope: "trap:c04-open-weak-trap" },
        { scope: "drill:DRL-MTH-T02-C01-U01-01" },
      ];

      for (const c of cases) {
        const tsRes = getDueReviewItems({
          today: "2026-11-19",
          limit: c.limit,
          scope: c.scope,
          dataDir: priData,
          progressDir: priProgress,
          labsDir: priLabs,
          rootDir: root,
        });
        const pyArgs = [
          "-m",
          "scripts.review_items",
          "--due",
          "--today",
          "2026-11-19",
          "--data-root",
          priData,
          "--progress-dir",
          priProgress,
          "--json",
        ];
        if (c.limit !== undefined) pyArgs.push("--limit", String(c.limit));
        if (c.scope) pyArgs.push("--scope", c.scope);

        const pyRun = spawnSync(python, pyArgs, {
          cwd: root,
          encoding: "utf8",
          env: {
            ...process.env,
            PROGRESS_DIR: priProgress,
            DRILLS_DATA_DIR: priData,
            LABS_DIR: priLabs,
          },
        });
        if (pyRun.status !== 0) {
          throw new Error(`Python review_items failed for ${JSON.stringify(c)}: ${pyRun.stderr}`);
        }
        const pyJson = JSON.parse(pyRun.stdout) as {
          items: ReviewItem[];
          totalDue: number;
          bySubject: { MTH: number; PRG: number };
          medianDurationMs: number;
          estimatedMinutes: number;
        };

        assert.deepEqual(
          tsRes.items,
          pyJson.items,
          `Py/TS parity mismatch on items for ${JSON.stringify(c)}`
        );
        assert.equal(tsRes.totalDue, pyJson.totalDue);
        assert.deepEqual(tsRes.bySubject, pyJson.bySubject);
        assert.equal(tsRes.medianDurationMs, pyJson.medianDurationMs);
        assert.equal(tsRes.estimatedMinutes, pyJson.estimatedMinutes);
      }

      // Verify pure prioritizeDueItems order: wrong > open weak > oldest dueDate
      const priTest = prioritizeDueItems(
        [
          {
            drillId: "D1",
            qid: "Q1",
            unitCode: "MTH-U1",
            subject: "MTH",
            commonTrapTag: "t-normal",
            archetypeKey: null,
            level: 1,
            lastReviewed: "2026-11-01",
            dueDate: "2026-11-02",
            revisitNote: null,
            lastWrong: false,
          },
          {
            drillId: "D2",
            qid: "Q1",
            unitCode: "MTH-U2",
            subject: "MTH",
            commonTrapTag: "t-weak",
            archetypeKey: null,
            level: 2,
            lastReviewed: "2026-11-10",
            dueDate: "2026-11-18",
            revisitNote: null,
            lastWrong: false,
          },
          {
            drillId: "D3",
            qid: "Q1",
            unitCode: "MTH-U3",
            subject: "MTH",
            commonTrapTag: "t-other",
            archetypeKey: null,
            level: 1,
            lastReviewed: "2026-11-18",
            dueDate: "2026-11-19",
            revisitNote: null,
            lastWrong: true,
          },
        ],
        new Set(["t-weak"])
      );
      assert.deepEqual(
        priTest.map((x) => x.drillId),
        ["D3", "D2", "D1"]
      );

      // Verify GET /api/review-items?scope=trap:... filters on server AND stays strictly redacted
      const trapRes = await reviewItemsGET(
        new NextRequest(
          "http://127.0.0.1:3000/api/review-items?today=2026-11-19&scope=trap:c04-open-weak-trap"
        )
      );
      assert.equal(trapRes.status, 200);
      const trapBody = await trapRes.text();
      assert.ok(
        !trapBody.includes("c04-open-weak-trap"),
        "GET /api/review-items?scope=trap:... must not leak trap tag in response payload"
      );
      assert.ok(
        !trapBody.includes("lastWrong"),
        "GET /api/review-items must not expose lastWrong before an attempt"
      );
      const trapJson = JSON.parse(trapBody) as { totalDue: number; items: ReviewItem[] };
      assert.equal(trapJson.totalDue, 2);
      assert.equal(trapJson.items.length, 2);
      assert.ok(trapJson.items.every((it) => it.commonTrapTag === null && it.archetypeKey === null));

      // Invalid scope returns 400
      for (const bad of ["invalid", "subject:BIO", "unit:../etc", "trap:a..b", "foo:bar"]) {
        assert.throws(() => parseReviewScope(bad));
        const badRes = await reviewItemsGET(
          new NextRequest(
            `http://127.0.0.1:3000/api/review-items?scope=${encodeURIComponent(bad)}`
          )
        );
        assert.equal(badRes.status, 400, `Expected 400 for invalid scope '${bad}'`);
      }

      // Duration fallback 1.5 min/item
      assert.equal(DEFAULT_ITEM_DURATION_MS, 90_000);
      assert.equal(estimateReviewMinutes(0, 90_000), 0);
      assert.equal(estimateReviewMinutes(1, 90_000), 2);
      assert.equal(estimateReviewMinutes(8, 90_000), 12);
    } finally {
      fs.rmSync(priTmp, { recursive: true, force: true });
    }

    // 8. Parity test: kind:"variant" never moves review level, and Q2 after exampleViewedAt counts as assisted
    if (fs.existsSync(storeFile)) fs.unlinkSync(storeFile);
    fs.writeFileSync(
      path.join(progressDir, "DRL-MTH-T01-C04-U01-01.json"),
      JSON.stringify({
        drillId: "DRL-MTH-T01-C04-U01-01",
        updatedAt: "2026-11-19T12:00:00Z",
        problems: {
          Q01: {
            attempts: [
              { verdict: "correct", ts: "2026-11-10T10:00:00Z" },
              { verdict: "incorrect", ts: "2026-11-15T10:00:00Z", matchedTrap: "c04-divide-not-invert-trap" },
              { verdict: "correct", ts: "2026-11-19T11:00:00Z", exampleViewed: true },
            ],
            exampleViewedAt: "2026-11-19T10:30:00Z",
            variants: {
              v1: {
                variantId: "VAR-MTH-T01-C04-fraction-division-01",
                role: "try",
                servedAt: "2026-11-19T10:00:00Z",
                attempts: [
                  { verdict: "correct", ts: "2026-11-19T10:05:00Z", kind: "variant" },
                  { verdict: "incorrect", ts: "2026-11-19T10:10:00Z", kind: "variant", matchedTrap: "c04-divide-not-invert-trap" },
                ],
              },
            },
            score: 0.5,
            hintsRevealed: 0,
          },
        },
      }),
      "utf-8"
    );
    const tsVariantParity = buildScheduleFromProgress({
      dataDir,
      progressDir,
      labsDir,
      rootDir: root,
    });
    const pyVariantParityProc = spawnSync(
      python,
      [
        "-m",
        "scripts.review_items",
        "--today",
        "2026-11-19",
        "--data-root",
        dataDir,
        "--progress-dir",
        progressDir,
        "--json",
      ],
      {
        cwd: root,
        encoding: "utf8",
        env: { ...process.env, PROGRESS_DIR: progressDir, DRILLS_DATA_DIR: dataDir, LABS_DIR: labsDir },
      }
    );
    assert.equal(pyVariantParityProc.status, 0, pyVariantParityProc.stderr);
    const pyVariantItems = (JSON.parse(pyVariantParityProc.stdout) as { items: ReviewItem[] }).items;
    const pyVariantMap: Record<string, ReviewItem> = {};
    for (const it of pyVariantItems) {
      pyVariantMap[`${it.drillId}/${it.qid}`] = it;
    }
    assert.deepEqual(tsVariantParity, pyVariantMap, "TS and Python must match on variant + exampleViewedAt parity");
    // Q01: 11-10 correct -> L2; 11-15 wrong -> L1; 11-19 correct AFTER exampleViewedAt -> assisted -> STAYS at L1 (due +1d = 11-20)
    assert.equal(tsVariantParity["DRL-MTH-T01-C04-U01-01/Q01"].level, 1);
    assert.equal(tsVariantParity["DRL-MTH-T01-C04-U01-01/Q01"].dueDate, "2026-11-20");

    // A reset later on the same local day invalidates evidence and must be pruned in both engines.
    const resetProgressPath = path.join(progressDir, "DRL-MTH-T01-C04-U01-01.json");
    const resetProgress = JSON.parse(fs.readFileSync(resetProgressPath, "utf8")) as Record<string, any>;
    resetProgress.problems.Q01.cycleStartedAt = "2026-11-19T11:30:00Z";
    fs.writeFileSync(resetProgressPath, JSON.stringify(resetProgress), "utf8");
    const resetTestTz = process.env.TZ;
    process.env.TZ = "UTC";
    try {
      const tsAfterReset = buildScheduleFromProgress({ dataDir, progressDir, labsDir, rootDir: root });
      const pyAfterReset = spawnSync(
        python,
        ["-m", "scripts.review_items", "--data-root", dataDir, "--progress-dir", progressDir, "--json"],
        { cwd: root, encoding: "utf8", env: { ...process.env, TZ: "UTC" } }
      );
      assert.equal(pyAfterReset.status, 0, pyAfterReset.stderr);
      const pyResetMap = Object.fromEntries(
        (JSON.parse(pyAfterReset.stdout) as { items: ReviewItem[] }).items.map((item) => [`${item.drillId}/${item.qid}`, item])
      );
      assert.equal(tsAfterReset["DRL-MTH-T01-C04-U01-01/Q01"], undefined);
      assert.equal(pyResetMap["DRL-MTH-T01-C04-U01-01/Q01"], undefined);
      assert.deepEqual(tsAfterReset, pyResetMap, "TS and Python must agree after a same-day reset");
    } finally {
      if (resetTestTz === undefined) delete process.env.TZ;
      else process.env.TZ = resetTestTz;
    }

    console.log("[PASS] Python and TypeScript review_items schedules, priority, scopes, variants, and /api/review-items routes match");
  } finally {
    if (prevProgressDir === undefined) delete process.env.PROGRESS_DIR;
    else process.env.PROGRESS_DIR = prevProgressDir;
    if (prevDrillsDir === undefined) delete process.env.DRILLS_DATA_DIR;
    else process.env.DRILLS_DATA_DIR = prevDrillsDir;
    if (prevLabsDir === undefined) delete process.env.LABS_DIR;
    else process.env.LABS_DIR = prevLabsDir;
    fs.rmSync(tmp, { recursive: true, force: true });
  }
}

runTests().catch((err) => {
  console.error(err);
  process.exit(1);
});
