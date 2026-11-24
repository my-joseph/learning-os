import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { test, type TestContext } from "node:test";
import { NextRequest } from "next/server";
import { GET as revealGET, POST as revealPOST } from "../src/app/api/reveal/route";
import { POST as variantPOST } from "../src/app/api/variant/route";
import { POST as reviewPOST } from "../src/app/api/review-items/route";
import { POST as savePOST } from "../src/app/api/save-state/route";
import { getDueReviewItems, getReviewItemsSchedule, loadSavedReviewItems, normalizeReviewDate, addDays, writeReviewItemsStore } from "../src/lib/reviewItems";
import { loadPracticeDocument, recordOriginalCheck } from "../src/lib/practiceEvidence";
import { readProgress, mutateProblemState, writeProgress } from "../src/lib/progress";
import { saveReviewProblemState } from "../src/lib/reviewSession";
import type { ProblemState } from "../src/types/drill";

const drillId = "DRL-MTH-T01-C01-U01-99";
const unitCode = "MTH-T01-C01-U01";
const qid = "Q01";
const key = `${drillId}/${qid}`;
const today = normalizeReviewDate();
const yesterday = addDays(today, -1);

function fixture(t: TestContext) {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "learningos-review-practice-"));
  const dataDir = path.join(tmp, "data");
  const progressDir = path.join(tmp, "progress");
  const drillDir = path.join(dataDir, unitCode);
  fs.mkdirSync(drillDir, { recursive: true });
  const drillPath = path.join(drillDir, `${drillId}.json`);
  fs.writeFileSync(drillPath, JSON.stringify({
    drillId, unitCode, subject: "MATH", problems: [{
      id: qid, prompt: "Synthetic question", answerPlain: "2",
      checkpointHint: "Synthetic hint", display: "x + x",
      steps: [{ latex: "2x", explain: "Synthetic step" }],
    }],
  }));
  const previous = { ...process.env };
  Object.assign(process.env, { LEARNINGOS_ROOT: tmp, PROGRESS_DIR: progressDir, DRILLS_DATA_DIR: dataDir });
  t.after(() => {
    for (const key of ["LEARNINGOS_ROOT", "PROGRESS_DIR", "DRILLS_DATA_DIR"]) {
      if (previous[key] === undefined) delete process.env[key];
      else process.env[key] = previous[key];
    }
    fs.rmSync(tmp, { recursive: true, force: true });
  });
  const post = (route: string, body: Record<string, unknown>) =>
    new NextRequest(`http://localhost/api/${route}`, {
      method: "POST", body: JSON.stringify({ drillId, qid, ...body }),
    });
  return {
    drillPath, dataDir, progressDir,
    reveal: (action: string, cycleStartedAt?: string) =>
      revealPOST(post("reveal", { action, cycleStartedAt })),
    steps: () => revealGET(new NextRequest(`http://localhost/api/reveal?drill=${drillId}&q=${qid}&part=steps`)),
    variant: (action: string) => variantPOST(post("variant", { action, ...(action === "reset-all" ? { qid: undefined } : {}) })),
    complete: (eventId?: string) => reviewPOST(post("review-items", { eventId })),
    read: () => readProgress(drillId)?.problems?.[qid] as ProblemState,
    check: (verdict: "correct" | "incorrect", cycle: string) => {
      const doc = loadPracticeDocument(drillId)!;
      return recordOriginalCheck(doc, doc.problems[0], cycle, "2", {
        verdict, message: "", components: [], diagnostics: [],
      });
    },
  };
}

function pythonReviewCommand(f: ReturnType<typeof fixture>, args: string[]) {
  const result = spawnSync(process.env.PYTHON || "python3", [
    "-m", "scripts.review_items", "--data-root", f.dataDir, "--progress-dir", f.progressDir, ...args,
  ], { cwd: "..", encoding: "utf8", env: process.env });
  assert.equal(result.status, 0, result.stderr || result.error?.message);
  return result.stdout;
}

function seedHistory() {
  mutateProblemState(drillId, unitCode, qid, (state) => {
    state.attempts = [{ input: "1", verdict: "incorrect", ts: `${yesterday}T10:00:00.000Z`, eventId: "previous-check" }];
  });
}

function seedSchedule(level: number) {
  writeReviewItemsStore({
    [key]: { drillId, qid, unitCode, subject: "MTH", level, lastReviewed: yesterday, dueDate: today,
      commonTrapTag: null, archetypeKey: null, revisitNote: null },
  });
}

test("B1: variant requests cannot undo an original reset or erase variant evidence", async (t) => {
  const f = fixture(t);
  seedHistory();
  mutateProblemState(drillId, unitCode, qid, (state) => {
    state.exampleViewedAt = `${yesterday}T09:00:00.000Z`;
    state.variants = { synthetic: { variantId: "VAR-SYNTHETIC", servedAt: state.exampleViewedAt, role: "example", attempts: [] } };
  });
  assert.equal((await f.steps()).status, 200);
  assert.equal((await f.reveal("reset")).status, 200);
  assert.equal((await f.steps()).status, 403);
  const state = f.read();
  for (const action of ["reset-question", "reset-all", "start-cycle"]) {
    const response = await f.variant(action);
    assert.equal((await f.steps()).status, 403, action);
    assert.equal(response.status, 400, action);
    assert.deepEqual(f.read(), state);
  }
  fs.unlinkSync(f.drillPath);
  assert.equal((await f.variant("reset-all")).status, 400);
  assert.deepEqual(f.read(), state);
});

test("B2: an unfinished review stays due and retains help across reset and reload", async (t) => {
  const f = fixture(t);
  seedHistory();
  assert.equal((await f.reveal("reset")).status, 200);
  assert.equal(getReviewItemsSchedule()[key]?.dueDate, today, "Backfilled items survive a drill reset");
  seedSchedule(3);
  const started = await f.reveal("start-review");
  assert.equal(started.status, 200, "A previously due item can start after a drill reset");
  const { cycleStartedAt } = await started.json();
  assert.equal((await f.reveal("hint", cycleStartedAt)).status, 200);
  assert.equal((await f.reveal("setup", cycleStartedAt)).status, 200);
  assert.equal((await f.steps()).status, 403);
  assert.equal(getReviewItemsSchedule()[key]?.level, 3);
  assert.ok(getDueReviewItems({ today }).items.some((item) => item.drillId === drillId && item.qid === qid));
  const resumed = await f.reveal("start-review");
  assert.equal((await resumed.json()).cycleStartedAt, cycleStartedAt);
  const reset = await f.reveal("reset-review", cycleStartedAt);
  assert.equal(reset.status, 200);
  const resetCycle = (await reset.json()).cycleStartedAt;
  assert.ok(resetCycle > cycleStartedAt);
  assert.equal(f.read().reviewBaseLevel, 3);
  assert.equal(f.read().hintsRevealed, 1);
  assert.equal(f.read().reviewHintRevealedAt, resetCycle);
  assert.equal(f.read().reviewSetupRevealedAt, resetCycle);
  assert.equal((await f.steps()).status, 403);
  const event = f.check("correct", resetCycle);
  assert.equal(f.read().attempts?.at(-1)?.hintsUsed, true);
  assert.equal(getReviewItemsSchedule()[key]?.dueDate, today, "A check awaits review completion");
  const pythonDue = JSON.parse(pythonReviewCommand(f, ["--today", today, "--due", "--json"]));
  assert.ok(pythonDue.items.some((item: { drillId: string; qid: string }) =>
    item.drillId === drillId && item.qid === qid
  ));
  const completed = await f.complete(event.eventId);
  assert.equal(completed.status, 200);
  assert.equal((await completed.json()).item.level, 3);
});

for (const verdict of ["incorrect", "correct"] as const) {
  test(`B3: an initial ${verdict} review remains scheduled across a same-day retry`, async (t) => {
    const f = fixture(t);
    seedHistory();
    seedSchedule(verdict === "correct" ? 3 : 4);
    const start = await f.reveal("start-review");
    assert.equal(start.status, 200);
    const first = f.check(verdict, (await start.json()).cycleStartedAt);
    const complete = await f.complete(first.eventId);
    assert.equal(complete.status, 200);
    const firstItem = (await complete.json()).item;
    assert.equal(firstItem.level, verdict === "correct" ? 4 : 2);
    const secondStart = await f.reveal("start-review");
    assert.equal(secondStart.status, 200);
    const secondCycle = (await secondStart.json()).cycleStartedAt;
    const retry = f.check("correct", secondCycle);
    const second = await f.complete(retry.eventId);
    assert.equal(second.status, 200);
    assert.deepEqual((await second.json()).item, firstItem);
    const stored = loadSavedReviewItems()[key];
    assert.equal(stored.completedCycle, secondCycle);
    assert.equal(stored.lastWrong, verdict === "incorrect");
    pythonReviewCommand(f, ["--rebuild"]);
    assert.deepEqual(loadSavedReviewItems()[key], stored);
  });
}

test("N1: clearing a note before a review cycle starts does not change the practice evidence", async (t) => {
  const f = fixture(t);
  seedHistory();
  mutateProblemState(drillId, unitCode, qid, (state) => {
    state.revisitNote = "A prior note";
    state.mistakeNote = "Another prior note";
    state.userInput = "existing draft";
  });
  const fetchSave: typeof fetch = async (url, init) => savePOST(new NextRequest(`http://localhost${url}`, {
    method: init?.method, body: init?.body as string | undefined,
  }));
  assert.equal(await saveReviewProblemState(drillId, unitCode, qid, {
    cycleStartedAt: new Date().toISOString(), revisitNote: "",
  }, fetchSave), true);
  assert.equal(f.read().revisitNote, "");
  assert.equal(f.read().mistakeNote, "Another prior note");
  assert.equal(await saveReviewProblemState(drillId, unitCode, qid, {
    cycleStartedAt: new Date().toISOString(), mistakeNote: "",
  }, fetchSave), true);
  assert.equal(f.read().mistakeNote, "");
  assert.equal(f.read().userInput, "existing draft");
  assert.equal(f.read().attempts?.at(-1)?.eventId, "previous-check");
});

test("N2: historical hint counts do not make a new server check assisted", async (t) => {
  const f = fixture(t);
  seedHistory();
  const reset = await f.reveal("reset");
  const cycle = (await reset.json()).cycleStartedAt;
  mutateProblemState(drillId, unitCode, qid, (state) => {
    state.hintsRevealed = 2;
    state.reviewHintRevealedAt = `${yesterday}T10:00:00.000Z`;
  });
  f.check("correct", cycle);
  assert.equal(f.read().attempts?.at(-1)?.hintsUsed, false);
  assert.equal(f.read().score, 1);
});

test("N2: internal progress writes retain the review base of the winning cycle", (t) => {
  const f = fixture(t);
  const cycle = "2026-11-20T10:00:00.000Z";
  mutateProblemState(drillId, unitCode, qid, (state) => {
    state.cycleStartedAt = cycle;
    state.reviewBaseLevel = 4;
  });
  writeProgress({ drillId, unitCode, problems: [{ id: qid, state: { cycleStartedAt: "2026-11-19T10:00:00.000Z", reviewBaseLevel: 2 } }] });
  assert.equal(f.read().cycleStartedAt, cycle);
  assert.equal(f.read().reviewBaseLevel, 4);
  writeProgress({
    drillId, unitCode, reviewMerge: true,
    problems: [{ id: qid, state: { cycleStartedAt: "2026-11-21T10:00:00.000Z" } }],
  });
  assert.equal(f.read().reviewBaseLevel, undefined);
});
