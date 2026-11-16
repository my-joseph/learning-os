/** Compare Python terminal-practice attempt scoring with the Studio reducer. */
import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { applyCheckResult } from "../src/lib/applyCheckResult";
import { Problem } from "../src/types/drill";

const root = path.resolve(process.cwd(), "..");
const progressDir = mkdtempSync(path.join(tmpdir(), "learningos-practice-parity-"));
try {
  const commonTrapTag = "fraction-reciprocal";
  const base: Problem = {
    id: "Q01", templateKey: "parity", level: 1, levelLabel: "Level 1", category: "Fractions",
    prompt: "Compute the quotient.", answerDisplay: "27/10", answerPlain: "27/10",
    checkpointHint: "Track which quantity is the divisor.", steps: [],
    answerSpec: { type: "number", value: "27/10" }, commonTrapTag, trapValue: "15/8",
    state: { userInput: "", score: null, divergedStep: null, mistakes: [], attempts: [], hintsRevealed: 1,
      setupRevealedBeforeAnswer: true, durationMs: 0 },
  };
  const attempts = [
    { input: "15/8", verdict: "incorrect", trapMatched: true, setupRevealed: true },
    { input: "not a fraction", verdict: "invalid input" },
    { input: "27/10", verdict: "correct", setupRevealed: true },
  ];
  let state = base.state;
  for (const item of attempts) {
    state = applyCheckResult(
      { ...base, state }, item.input,
      { verdict: item.verdict as "incorrect" | "invalid input" | "correct", message: "", components: [], diagnostics: [],
        ...(item.trapMatched ? { trapMatched: true } : {}) },
      [], { ts: "2026-11-17T00:00:00.000Z", hintsRevealed: 1 },
    );
  }

  const venvPython = path.join(root, ".venv", "bin", "python");
  const python = process.env.PYTHON || (existsSync(venvPython) ? venvPython : "python3");
  const source = `
import contextlib, io, json
from scripts.practice import _record_answer
doc = {"drillId":"DRL-MTH-PARITY-01","unitCode":"MTH-PARITY","mistakeTags":[],"sessionSummary":{},"problems":[{
 "id":"Q01","prompt":"Compute the quotient.","answerSpec":{"type":"number","value":"27/10"},
 "commonTrapTag":"fraction-reciprocal","trapValue":"15/8","checkpointHint":"Track which quantity is the divisor.",
 "display":"model","steps":[],"state":{"userInput":"","score":None,"divergedStep":None,"mistakes":[],"attempts":[],
 "hintsRevealed":1,"setupRevealedBeforeAnswer":True,"durationMs":0}}]}
for answer in ["15/8", "not a fraction", "27/10"]:
 with contextlib.redirect_stdout(io.StringIO()): _record_answer(doc, "Q01", answer)
print(json.dumps(doc["problems"][0]["state"]))
`;
  const py = spawnSync(python, ["-c", source], {
    cwd: root,
    encoding: "utf8",
    env: { ...process.env, PROGRESS_DIR: progressDir, LEARNINGOS_PILOT: "1" },
  });
  if (py.status !== 0) throw new Error(`Python practice failed: ${py.stderr}`);
  const pythonState = JSON.parse(py.stdout);
  if (state?.score !== pythonState.score) throw new Error(`Score mismatch: Studio=${state?.score}, Python=${pythonState.score}`);
  if (JSON.stringify(state?.mistakes) !== JSON.stringify(pythonState.mistakes)) throw new Error("Mistake tags differ between Studio and Python");
  if ((state?.attempts || []).map((a) => a.verdict).join(",") !== pythonState.attempts.map((a: { verdict: string }) => a.verdict).join(",")) {
    throw new Error("Attempt verdict sequence differs between Studio and Python");
  }
  console.log("[PASS] Python practice and Studio agree on trap, invalid input, and retry scoring");
} finally {
  rmSync(progressDir, { recursive: true, force: true });
}
