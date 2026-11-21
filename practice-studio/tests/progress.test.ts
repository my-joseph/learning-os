/**
 * Progress is stored apart from drill content (src/lib/progress.ts).
 * Run: npx tsx tests/progress.test.ts
 */
import fs from "fs";
import os from "os";
import path from "path";

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "progress-"));
process.env.PROGRESS_DIR = tmp;

// eslint-disable-next-line @typescript-eslint/no-require-imports
const { applyProgress, readProgress, writeProgress } = require("../src/lib/progress");

function assert(cond: boolean, msg: string) {
  if (!cond) throw new Error(`FAIL: ${msg}`);
}

const content = () => ({
  drillId: "DRL-MTH-X-01",
  unitCode: "MTH-X",
  problems: [{ id: "Q01", prompt: "p1" }, { id: "Q02", prompt: "p2" }] as Array<{ id: string; prompt: string; state?: unknown }>,
});

const doc = content();
doc.problems[0].state = { userInput: "42", attempts: [{ input: "41" }], setupRevealedBeforeAnswer: true };
const file = writeProgress({ ...doc, sessionSummary: { score: 1 } });
assert(file.startsWith(tmp), "writes under PROGRESS_DIR");

const merged = applyProgress(content(), readProgress("DRL-MTH-X-01"));
const st = merged.problems[0].state as { attempts: unknown[]; setupRevealedBeforeAnswer: boolean };
assert(st.attempts.length === 1 && st.setupRevealedBeforeAnswer === true, "state restored with all fields");
assert(merged.problems[1].state === undefined, "untouched problem stays without state");
assert(readProgress("../../etc/passwd") === null, "unsafe ids rejected");

const overrideDoc = {
  ...content(),
  drillId: "DRL-MTH-X-OVERRIDE",
  sessionSummary: { score: 1, statusOverride: "Graded" },
};
writeProgress(overrideDoc);
const restoredOverride = applyProgress(
  { ...content(), sessionSummary: {} as Record<string, unknown> },
  readProgress("DRL-MTH-X-OVERRIDE"),
);
assert(
  restoredOverride.sessionSummary.statusOverride === "Graded",
  "manual status override is persisted in sessionSummary",
);

let threw = false;
try {
  writeProgress({ ...content(), drillId: "../x" });
} catch {
  threw = true;
}
assert(threw, "writeProgress refuses unsafe ids");

// Verify writeProgress preserves existing `reviews` when Studio saves state without it
const prgDoc = () => ({
  drillId: "DRL-PRG-X-01",
  unitCode: "PRG-X",
  problems: [{ id: "Q01", prompt: "p1" }] as Array<{ id: string; prompt: string; state?: unknown }>,
});
const withReviews = prgDoc();
const sampleReview = [
  {
    at: "2026-11-16T10:00:00Z",
    attempt: 1,
    codeHash: "sha256:abc",
    code: "function f() { return 1; }",
    tests: { passed: 1, total: 1, failed: [] },
    lint: [],
    typecheck: [],
    findings: [],
    verdict: "pass",
    explain: null,
  },
];
withReviews.problems[0].state = { userInput: "", score: 1, reviews: sampleReview };
writeProgress({ ...withReviews, sessionSummary: { score: 1 } });

// Simulate Studio saving state without `reviews` in memory
const studioSave = prgDoc();
studioSave.problems[0].state = { userInput: "", score: 1, mistakeNote: "checked" };
writeProgress({ ...studioSave, sessionSummary: { score: 1 } });
const reloaded = applyProgress(prgDoc(), readProgress("DRL-PRG-X-01"));
const reloadedState = reloaded.problems[0].state as { reviews?: unknown[]; mistakeNote?: string };
assert(
  Array.isArray(reloadedState.reviews) && reloadedState.reviews.length === 1,
  "writeProgress preserves existing reviews when omitted from incoming state",
);
assert(reloadedState.mistakeNote === "checked", "writeProgress keeps new state fields alongside preserved reviews");

// Verify revisitNote is saved and preserved by writeProgress
const withRevisit = prgDoc();
withRevisit.problems[0].state = {
  userInput: "",
  score: 1,
  revisitNote: "Next time guard against empty inputs first.",
};
writeProgress({ ...withRevisit, sessionSummary: { score: 1 } });
const reloadedWithNote = applyProgress(prgDoc(), readProgress("DRL-PRG-X-01"));
const noteState = reloadedWithNote.problems[0].state as {
  reviews?: unknown[];
  revisitNote?: string;
};
assert(
  noteState.revisitNote === "Next time guard against empty inputs first.",
  "writeProgress persists revisitNote",
);
assert(
  Array.isArray(noteState.reviews) && noteState.reviews.length === 1,
  "writeProgress keeps reviews when updating revisitNote",
);

// 9. Stale autosave sending `reviews: []` or older subset must NEVER drop server reviews
const serverReviews = [
  {
    ...sampleReview[0],
    at: "2026-11-16T10:00:00Z",
    attempt: 1,
    verdict: "revise",
    explain: "Server-recorded explanation",
  },
  {
    ...sampleReview[0],
    at: "2026-11-16T10:05:00Z",
    attempt: 2,
    verdict: "pass",
    explain: null,
  },
];
const prgServerDoc = prgDoc();
prgServerDoc.drillId = "DRL-PRG-MERGE-01";
prgServerDoc.problems[0].state = {
  userInput: "",
  score: 1,
  reviews: serverReviews,
  attempts: [
    { input: "a", ts: "2026-11-16T10:00:00Z", verdict: "incorrect" },
    { input: "b", ts: "2026-11-16T10:05:00Z", verdict: "correct" },
  ],
  mistakes: ["QC-NAMING"],
  mistakeNote: "Rename loop variable",
  revisitNote: "Check edge cases first",
};
writeProgress({ ...prgServerDoc, sessionSummary: { score: 1 } });

// Stale tab autosaves with reviews: [] (e.g. labModel default), only the first attempt, and empty notes/tags
const staleAutosave = prgDoc();
staleAutosave.drillId = "DRL-PRG-MERGE-01";
staleAutosave.problems[0].state = {
  userInput: "draft",
  score: 0.5,
  reviews: [],
  attempts: [{ input: "a", ts: "2026-11-16T10:00:00Z", verdict: "incorrect" }],
  mistakes: [],
  mistakeNote: "",
  revisitNote: "",
};
writeProgress({ ...staleAutosave, sessionSummary: { score: 0.5 } });

const afterStale = readProgress("DRL-PRG-MERGE-01")?.problems?.Q01 as {
  reviews: Array<{ at: string; verdict: string; explain: string | null }>;
  attempts: Array<{ ts: string; verdict: string }>;
  mistakes: string[];
  mistakeNote: string;
  revisitNote: string;
};
assert(afterStale.reviews.length === 2, "stale autosave with reviews:[] must keep all server reviews");
assert(
  afterStale.reviews[0].explain === "Server-recorded explanation",
  "stale autosave must keep server explain field on existing review",
);
assert(afterStale.reviews[1].verdict === "pass", "stale autosave must keep newer server review");
assert(afterStale.attempts.length === 2, "stale autosave must keep server attempts by ts");
assert(afterStale.attempts[1].ts === "2026-11-16T10:05:00Z", "merged attempts stay in chronological order");
assert(afterStale.mistakes.length === 1 && afterStale.mistakes[0] === "QC-NAMING", "empty mistakes keeps server mistakes");
assert(afterStale.mistakeNote === "Rename loop variable", "empty mistakeNote keeps server mistakeNote");
assert(afterStale.revisitNote === "Check edge cases first", "empty revisitNote keeps server revisitNote");

// Also verify stale client sending older copy of r1 (explain: null) without r2 keeps both r1's explain and r2
const stalePartialReviews = prgDoc();
stalePartialReviews.drillId = "DRL-PRG-MERGE-01";
stalePartialReviews.problems[0].state = {
  userInput: "draft",
  score: 1,
  reviews: [{ ...serverReviews[0], explain: null }],
  attempts: [
    { input: "a", ts: "2026-11-16T10:00:00Z", verdict: "incorrect" },
    { input: "c", ts: "2026-11-16T10:03:00Z", verdict: "incorrect" },
  ],
};
writeProgress({ ...stalePartialReviews, sessionSummary: { score: 1 } });
const afterPartial = readProgress("DRL-PRG-MERGE-01")?.problems?.Q01 as {
  reviews: Array<{ at: string; explain: string | null }>;
  attempts: Array<{ ts: string }>;
};
assert(afterPartial.reviews.length === 2, "partial client reviews keeps server reviews");
assert(afterPartial.reviews[0].explain === "Server-recorded explanation", "server review copy wins on key match");
assert(
  afterPartial.attempts.map((a) => a.ts).join(",") ===
    "2026-11-16T10:00:00Z,2026-11-16T10:03:00Z,2026-11-16T10:05:00Z",
  "merged attempts union by ts and keep chronological order",
);

// 10. reviewMerge NEVER overwrites original score, hintsRevealed, setup/solution flags, skipped, lastCheck, lastTestReport, durationMs
const originalDrill = {
  drillId: "DRL-MTH-REVMERGE-01",
  unitCode: "MTH-REV",
  problems: [
    {
      id: "Q01",
      state: {
        userInput: "5",
        score: 0.5,
        hintsRevealed: 1,
        setupRevealedBeforeAnswer: true,
        solutionRevealedBeforeAnswer: false,
        skipped: false,
        lastCheck: { verdict: "correct", message: "Correct", components: [], diagnostics: [] },
        lastTestReport: {
          allPassed: true,
          score: 1,
          passedCount: 3,
          totalCount: 3,
          visibleResults: [],
          hiddenPassed: 1,
          hiddenTotal: 1,
          executionTimeMs: 12,
        },
        durationMs: 15_000,
        mistakes: ["sign-error"],
        mistakeNote: "Initial note",
        revisitNote: "",
        attempts: [{ input: "5", ts: "2026-11-18T10:00:00Z", verdict: "correct", setupRevealed: true }],
      },
    },
  ],
  sessionSummary: { score: 0.5, practiceStatus: "Needs Retry" },
};
writeProgress(originalDrill);

// Scenario A & B combined: /review skips item with clean state (score: 0, hintsRevealed: 0, setupRevealedBeforeAnswer: false,
// solutionRevealedBeforeAnswer: true, skipped: true, lastTestReport: null, durationMs: 2000) and adds revisitNote + new tag
writeProgress({
  drillId: "DRL-MTH-REVMERGE-01",
  unitCode: "MTH-REV",
  reviewMerge: true,
  problems: [
    {
      id: "Q01",
      state: {
        userInput: "(Skipped)",
        score: 0,
        hintsRevealed: 0,
        setupRevealedBeforeAnswer: false,
        solutionRevealedBeforeAnswer: true,
        skipped: true,
        lastCheck: { verdict: "skipped", message: "Skipped", components: [], diagnostics: [] },
        lastTestReport: null,
        durationMs: 2_000,
        mistakes: ["concept-gap"],
        mistakeNote: "",
        revisitNote: "Check formula before substituting",
        attempts: [{ input: "(Skipped)", ts: "2026-11-19T12:00:00Z", verdict: "skipped" }],
        cycleStartedAt: "2026-11-19T11:59:00Z",
      },
    },
  ],
});

const afterRevMerge = readProgress("DRL-MTH-REVMERGE-01")?.problems?.Q01 as {
  userInput: string;
  score: number;
  hintsRevealed: number;
  setupRevealedBeforeAnswer: boolean;
  solutionRevealedBeforeAnswer: boolean;
  skipped: boolean;
  lastCheck: { verdict: string };
  lastTestReport: { passedCount: number } | null;
  durationMs: number;
  mistakes: string[];
  mistakeNote: string;
  revisitNote: string;
  attempts: Array<{ ts: string; verdict: string }>;
  reviewStepsRevealedAt?: string;
};
assert(afterRevMerge.score === 0.5, "reviewMerge must leave original score untouched");
assert(afterRevMerge.hintsRevealed === 1, "reviewMerge must leave original hintsRevealed untouched");
assert(afterRevMerge.setupRevealedBeforeAnswer === true, "reviewMerge must leave original setupRevealedBeforeAnswer untouched");
assert(afterRevMerge.solutionRevealedBeforeAnswer === false, "reviewMerge must leave original solutionRevealedBeforeAnswer untouched");
assert(afterRevMerge.skipped === false, "reviewMerge must leave original skipped untouched");
assert(afterRevMerge.lastCheck.verdict === "correct", "reviewMerge must leave original lastCheck untouched");
assert(afterRevMerge.lastTestReport?.passedCount === 3, "reviewMerge must leave original lastTestReport untouched");
assert(afterRevMerge.durationMs === 15_000, "reviewMerge must leave original durationMs untouched");
assert(afterRevMerge.userInput === "5", "reviewMerge must leave original userInput untouched");
assert(afterRevMerge.attempts.length === 2, "reviewMerge must append new review attempt");
assert(afterRevMerge.attempts[1].verdict === "skipped", "appended review attempt preserved");
assert(afterRevMerge.mistakes.includes("sign-error") && afterRevMerge.mistakes.includes("concept-gap"), "reviewMerge unions mistake tags");
assert(afterRevMerge.mistakeNote === "Initial note", "reviewMerge keeps original mistakeNote when review note is empty");
assert(afterRevMerge.revisitNote === "Check formula before substituting", "reviewMerge fills revisitNote");
assert(Boolean(afterRevMerge.reviewStepsRevealedAt), "reviewMerge records cycle-scoped reviewStepsRevealedAt without mutating original flag");

// 10b. reviewMerge records cycle-scoped reviewHintRevealedAt when incoming hintsRevealed > 0
//      and does NOT leak Cycle 1 hints/setup flags into a clean Cycle 2 score.
// eslint-disable-next-line @typescript-eslint/no-require-imports
const { scoreProblem } = require("../src/lib/scoring");
writeProgress({
  drillId: "DRL-MTH-REVMERGE-HINT-01",
  unitCode: "MTH-REV",
  problems: [
    {
      id: "Q01",
      state: {
        userInput: "5",
        score: 0.5,
        hintsRevealed: 1,
        setupRevealedBeforeAnswer: true,
        solutionRevealedBeforeAnswer: false,
        skipped: false,
        attempts: [{ input: "5", ts: "2026-11-18T10:00:00Z", verdict: "correct", setupRevealed: true }],
      },
    },
    {
      id: "Q02",
      state: {
        userInput: "4",
        score: 0,
        hintsRevealed: 0,
        setupRevealedBeforeAnswer: false,
        solutionRevealedBeforeAnswer: false,
        skipped: false,
        attempts: [{ input: "4", ts: "2026-11-18T10:00:00Z", verdict: "incorrect" }],
      },
    },
  ],
  sessionSummary: { score: 0.5 },
});

// Cycle 2 on /review: Q01 solved cleanly with ZERO help; Q02 opens a hint then answers correctly.
writeProgress({
  drillId: "DRL-MTH-REVMERGE-HINT-01",
  unitCode: "MTH-REV",
  reviewMerge: true,
  problems: [
    {
      id: "Q01",
      state: {
        userInput: "5",
        score: 1,
        hintsRevealed: 0,
        setupRevealedBeforeAnswer: false,
        solutionRevealedBeforeAnswer: false,
        skipped: false,
        attempts: [{ input: "5", ts: "2026-11-20T12:05:00Z", verdict: "correct" }],
        cycleStartedAt: "2026-11-20T12:00:00Z",
      },
    },
    {
      id: "Q02",
      state: {
        userInput: "5",
        score: 0.5,
        hintsRevealed: 1,
        setupRevealedBeforeAnswer: false,
        solutionRevealedBeforeAnswer: false,
        skipped: false,
        attempts: [{ input: "5", ts: "2026-11-20T12:06:00Z", verdict: "correct" }],
        cycleStartedAt: "2026-11-20T12:00:00Z",
      },
    },
  ],
});

const mergedHintProg = readProgress("DRL-MTH-REVMERGE-HINT-01")?.problems as Record<string, Record<string, unknown>>;
assert(mergedHintProg.Q01.hintsRevealed === 1, "reviewMerge preserves Cycle 1 hintsRevealed on Q01");
assert(!mergedHintProg.Q01.reviewHintRevealedAt, "clean Cycle 2 must not stamp reviewHintRevealedAt");
assert(scoreProblem(mergedHintProg.Q01).score === 1, "clean Cycle 2 on Q01 must score 1.0 despite Cycle 1 hint/setup");
assert(scoreProblem(mergedHintProg.Q01).usedHelp === false, "clean Cycle 2 on Q01 must have usedHelp=false");

assert(mergedHintProg.Q02.hintsRevealed === 0, "reviewMerge preserves Cycle 1 hintsRevealed=0 on Q02");
assert(
  typeof mergedHintProg.Q02.reviewHintRevealedAt === "string" &&
    mergedHintProg.Q02.reviewHintRevealedAt >= "2026-11-20T12:00:00Z",
  "reviewMerge must stamp cycle-scoped reviewHintRevealedAt when /review opened a hint",
);
assert(scoreProblem(mergedHintProg.Q02).score === 0.5, "hinted Cycle 2 on Q02 must score 0.5");
assert(scoreProblem(mergedHintProg.Q02).usedHelp === true, "hinted Cycle 2 on Q02 must have usedHelp=true");

// Normal autosave on drill page after clean Cycle 2 (e.g. editing mistakeNote) must NOT falsely stamp review*RevealedAt
writeProgress({
  drillId: "DRL-MTH-REVMERGE-HINT-01",
  unitCode: "MTH-REV",
  problems: [
    {
      id: "Q01",
      state: {
        ...mergedHintProg.Q01,
        mistakeNote: "Reviewed cleanly",
      },
    },
  ],
  sessionSummary: { score: 1.5 },
});
const afterNoteAutosave = readProgress("DRL-MTH-REVMERGE-HINT-01")?.problems?.Q01 as Record<string, unknown>;
assert(!afterNoteAutosave.reviewSetupRevealedAt, "normal autosave must not stamp reviewSetupRevealedAt from stale Cycle 1 flag");
assert(!afterNoteAutosave.reviewHintRevealedAt, "normal autosave must not stamp reviewHintRevealedAt from stale Cycle 1 hintsRevealed");
assert(scoreProblem(afterNoteAutosave).score === 1, "Q01 must stay 1.0 after drill-page note autosave");

// 11. Atomic writes leave no leftover .tmp files
const leftoverTmp = fs.readdirSync(tmp).filter((f) => f.endsWith(".tmp"));
assert(leftoverTmp.length === 0, "atomic progress writes must not leave .tmp files behind");

fs.rmSync(tmp, { recursive: true, force: true });
console.log("ALL PROGRESS CHECKS PASSED");
