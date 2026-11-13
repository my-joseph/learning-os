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

let threw = false;
try {
  writeProgress({ ...content(), drillId: "../x" });
} catch {
  threw = true;
}
assert(threw, "writeProgress refuses unsafe ids");

fs.rmSync(tmp, { recursive: true, force: true });
console.log("ALL 5 PROGRESS CHECKS PASSED");
