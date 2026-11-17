import assert from "node:assert/strict";
import {
  subjectOf,
  drillHref,
  parseLegacyQuery,
  findProblemIndex,
  resolveWorkspaceDrill,
  resolveLandingDrill,
} from "../src/lib/routes";

// subjectOf
assert.equal(subjectOf("DRL-MTH-T01-C04-01"), "math");
assert.equal(subjectOf("DRL-PHY-T01-C01-01"), "math");
assert.equal(subjectOf("DRL-PRG-T01-C01-U01-01"), "code");
assert.equal(subjectOf("drl-mth-t01-c01-01"), "math");
assert.equal(subjectOf("  DRL-PRG-T01-01  "), "code");
assert.equal(subjectOf("DRL-BIO-T01-01"), null);
assert.equal(subjectOf("MTH-T01-C04"), null);
assert.equal(subjectOf("../etc/passwd"), null);
assert.equal(subjectOf(""), null);

// drillHref
assert.equal(drillHref("DRL-MTH-T01-C04-01"), "/math/DRL-MTH-T01-C04-01");
assert.equal(drillHref("DRL-MTH-T01-C04-01", "Q03"), "/math/DRL-MTH-T01-C04-01?q=Q03");
assert.equal(drillHref("DRL-PHY-T01-C01-01", "Q02"), "/math/DRL-PHY-T01-C01-01?q=Q02");
assert.equal(drillHref("DRL-PRG-T01-C01-U01-01"), "/code/DRL-PRG-T01-C01-U01-01");
assert.equal(drillHref("DRL-PRG-T01-C01-U01-01", "  "), "/code/DRL-PRG-T01-C01-U01-01");
assert.equal(drillHref("DRL-PRG-T01-C01-U01-01", null), "/code/DRL-PRG-T01-C01-U01-01");
assert.equal(drillHref("unknown-id", "Q01"), "/");

// parseLegacyQuery with URLSearchParams and plain records
assert.deepEqual(
  parseLegacyQuery(new URLSearchParams("drill=DRL-MTH-T01-C04-01&q=Q03")),
  { drillId: "DRL-MTH-T01-C04-01", qid: "Q03" }
);
assert.deepEqual(
  parseLegacyQuery(new URLSearchParams("drill=DRL-PRG-T01-C01-U01-01")),
  { drillId: "DRL-PRG-T01-C01-U01-01" }
);
assert.deepEqual(
  parseLegacyQuery({ drill: " DRL-MTH-T01-C04-01 ", q: ["Q02", "Q03"] }),
  { drillId: "DRL-MTH-T01-C04-01", qid: "Q02" }
);
assert.deepEqual(
  parseLegacyQuery({ drill: "DRL-MTH-T01-C04-01", q: "  " }),
  { drillId: "DRL-MTH-T01-C04-01" }
);
assert.equal(parseLegacyQuery({ q: "Q03" }), null);
assert.equal(parseLegacyQuery({ drill: "   " }), null);
assert.equal(parseLegacyQuery(null), null);

// findProblemIndex
const problems = [{ id: "Q01" }, { id: "Q02" }, { id: "Q03" }];
assert.equal(findProblemIndex(problems, "Q03"), 2);
assert.equal(findProblemIndex(problems, " Q02 "), 1);
assert.equal(findProblemIndex(problems, "Q99"), 0);
assert.equal(findProblemIndex(problems, undefined), 0);
assert.equal(findProblemIndex([], "Q01"), 0);

// resolveWorkspaceDrill & resolveLandingDrill
const sampleDrills = [
  { drillId: "DRL-MTH-T01-C04-01", subject: "MATH" as const },
  { drillId: "DRL-PRG-T01-C01-U01-01", subject: "PRG" as const },
  { drillId: "DRL-MTH-T01-C04-02", subject: "MATH" as const },
];
assert.equal(
  resolveWorkspaceDrill(sampleDrills, "math", "DRL-MTH-T01-C04-02"),
  "DRL-MTH-T01-C04-02"
);
assert.equal(
  resolveWorkspaceDrill(sampleDrills, "math", "DRL-PRG-T01-C01-U01-01"),
  "DRL-MTH-T01-C04-01",
  "wrong-workspace saved drill must fall back to first drill of that workspace"
);
assert.equal(
  resolveWorkspaceDrill(sampleDrills, "code", "DRL-PRG-MISSING"),
  "DRL-PRG-T01-C01-U01-01"
);
assert.equal(resolveWorkspaceDrill([], "code", null), null);

assert.equal(
  resolveLandingDrill(sampleDrills, "DRL-PRG-T01-C01-U01-01"),
  "DRL-PRG-T01-C01-U01-01"
);
assert.equal(
  resolveLandingDrill(sampleDrills, "DRL-MTH-DELETED"),
  "DRL-MTH-T01-C04-01"
);
assert.equal(resolveLandingDrill([], "DRL-MTH-T01-C04-01"), null);

console.log("routes tests passed");
