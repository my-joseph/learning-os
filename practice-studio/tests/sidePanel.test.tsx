import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { NextRequest } from "next/server";
import { formatLocalDate, getDueTodayUnits } from "../src/lib/dueToday";
import { getProgressDir } from "../src/lib/paths";
import { GET as dueTodayGET } from "../src/app/api/due-today/route";
import { GET as weakSpotsGET } from "../src/app/api/weak-spots/route";
import { StudioSidePanel } from "../src/components/shell/StudioSidePanel";

async function runTests() {
  // 1. Local calendar date formatting (independent of UTC conversion)
  const localMidnight = new Date(2026, 10, 18, 0, 5, 0);
  assert.equal(formatLocalDate(localMidnight), "2026-11-18");

  // 2. getProgressDir respects LEARNINGOS_PILOT when PROGRESS_DIR is unset
  const prevProgressDir = process.env.PROGRESS_DIR;
  const prevPilot = process.env.LEARNINGOS_PILOT;
  const prevDrillsDir = process.env.DRILLS_DATA_DIR;
  try {
    delete process.env.PROGRESS_DIR;
    process.env.LEARNINGOS_PILOT = "1";
    assert.ok(
      getProgressDir().endsWith(path.join("pilot", "progress")),
      "LEARNINGOS_PILOT=1 must resolve to pilot/progress"
    );

    // 3. Hermetic temp-dir test for getDueTodayUnits + /api/due-today + /api/weak-spots
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "studio-sidepanel-"));
    const progressDir = path.join(tmp, "progress");
    const dataDir = path.join(tmp, "drills", "data");
    fs.mkdirSync(progressDir, { recursive: true });
    fs.mkdirSync(path.join(dataDir, "MTH-T09-C01-U01"), { recursive: true });
    fs.mkdirSync(path.join(dataDir, "PRG-T09-C01"), { recursive: true });

    // Older and newer math unit drills
    fs.writeFileSync(
      path.join(dataDir, "MTH-T09-C01-U01", "DRL-MTH-T09-C01-U01-01.json"),
      JSON.stringify({
        drillId: "DRL-MTH-T09-C01-U01-01",
        unitCode: "MTH-T09-C01-U01",
        createdAt: "2026-11-01 10:00:00",
        problems: [
          {
            id: "Q01",
            level: 2,
            form: "direct",
            commonTrapTag: "c09-sign-flip",
          },
          {
            id: "Q02",
            level: 2,
            form: "direct",
            commonTrapTag: "c09-sign-flip",
          },
        ],
      }),
      "utf-8"
    );
    fs.writeFileSync(
      path.join(dataDir, "MTH-T09-C01-U01", "DRL-MTH-T09-C01-U01-02.json"),
      JSON.stringify({
        drillId: "DRL-MTH-T09-C01-U01-02",
        unitCode: "MTH-T09-C01-U01",
        createdAt: "2026-11-10 10:00:00",
        problems: [],
      }),
      "utf-8"
    );

    // Chapter mixed PRG drill covering PRG-T09-C01-U02
    fs.writeFileSync(
      path.join(dataDir, "PRG-T09-C01", "DRL-PRG-T09-C01-01.json"),
      JSON.stringify({
        drillId: "DRL-PRG-T09-C01-01",
        subject: "PRG",
        unitCode: "PRG-T09-C01",
        createdAt: "2026-11-12 09:00:00",
        problems: [{ id: "Q01", unitCode: "PRG-T09-C01-U02", level: 2 }],
      }),
      "utf-8"
    );

    // Progress file triggering an open math weak spot
    fs.writeFileSync(
      path.join(progressDir, "DRL-MTH-T09-C01-U01-01.json"),
      JSON.stringify({
        drillId: "DRL-MTH-T09-C01-U01-01",
        problems: {
          Q01: {
            attempts: [{ verdict: "incorrect", ts: "2026-11-01", matchedTrap: "c09-sign-flip" }],
            score: 0,
          },
          Q02: {
            attempts: [{ verdict: "incorrect", ts: "2026-11-02", matchedTrap: "c09-sign-flip" }],
            score: 0,
          },
        },
      }),
      "utf-8"
    );

    // Schedule cache: two due units and one future unit
    fs.writeFileSync(
      path.join(progressDir, "_review_schedule.json"),
      JSON.stringify({
        "MTH-T09-C01-U01": {
          mastery: 2,
          lastReviewed: "2026-11-10",
          nextReview: "2026-11-15",
          title: "Complex Conjugates",
        },
        "PRG-T09-C01-U02": {
          mastery: 1,
          lastReviewed: "2026-11-12",
          nextReview: "2026-11-18",
          title: "Async Error Boundaries",
        },
        "MTH-T09-C01-U03": {
          mastery: 3,
          lastReviewed: "2026-11-15",
          nextReview: "2099-12-31",
          title: "Future Unit",
        },
      }),
      "utf-8"
    );

    process.env.PROGRESS_DIR = progressDir;
    process.env.DRILLS_DATA_DIR = dataDir;

    const due = getDueTodayUnits({
      today: "2026-11-18",
      progressDir,
      dataDir,
      rootDir: tmp,
    });
    assert.equal(due.units.length, 2);
    assert.deepEqual(
      due.units.map((u) => [u.unitCode, u.drillId, u.href, u.mastery]),
      [
        ["MTH-T09-C01-U01", "DRL-MTH-T09-C01-U01-02", "/math/DRL-MTH-T09-C01-U01-02", 2],
        ["PRG-T09-C01-U02", "DRL-PRG-T09-C01-01", "/code/DRL-PRG-T09-C01-01", 1],
      ]
    );

    // Route /api/due-today
    const dueRes = await dueTodayGET();
    assert.equal(dueRes.status, 200);
    const dueJson = (await dueRes.json()) as { today: string; units: Array<{ unitCode: string }> };
    assert.ok(Array.isArray(dueJson.units));

    // Route /api/weak-spots rejects invalid scope and returns weak spots for valid scope
    const badRes = await weakSpotsGET(
      new NextRequest("http://127.0.0.1:3000/api/weak-spots?scope=../etc/passwd")
    );
    assert.equal(badRes.status, 400);

    const wsRes = await weakSpotsGET(
      new NextRequest("http://127.0.0.1:3000/api/weak-spots?scope=MTH-T09-C01-U01")
    );
    assert.equal(wsRes.status, 200);
    const wsJson = (await wsRes.json()) as {
      scope: string;
      units: Array<{ unitCode: string; open: Array<{ id: string }> }>;
    };
    assert.equal(wsJson.scope, "MTH-T09-C01-U01");
    assert.equal(wsJson.units.length, 1);
    assert.deepEqual(
      wsJson.units[0].open.map((x) => x.id),
      ["c09-sign-flip"]
    );

    // 4. Component rendering: Math vs PRG labels, mastery dots, deep links, empty states
    const mathHtml = renderToStaticMarkup(
      <StudioSidePanel
        workspace="math"
        currentUnitCode="MTH-T09-C01-U01"
        dueUnits={due.units}
        weakSpotUnits={[
          {
            unitCode: "MTH-T09-C01-U01",
            unitTitle: "Complex Conjugates",
            subject: "MTH",
            itemCount: 4,
            drillCount: 1,
            open: [
              {
                id: "c09-sign-flip",
                matches: 2,
                drills: 1,
                last: "2026-11-02",
                subject: "MTH",
              },
            ],
            closed: [],
            levels: {},
            assistedCount: 0,
            skipped: [],
          },
        ]}
      />
    );
    assert.match(mathHtml, /Due today/);
    assert.match(mathHtml, /Complex Conjugates/);
    assert.match(mathHtml, /Mastery 2 of 4/);
    assert.match(mathHtml, /href="\/math\/DRL-MTH-T09-C01-U01-02"/);
    assert.match(mathHtml, /href="\/code\/DRL-PRG-T09-C01-01"/);
    assert.match(mathHtml, /Repeated traps/);
    assert.match(mathHtml, /c09-sign-flip/);

    const prgHtml = renderToStaticMarkup(
      <StudioSidePanel
        workspace="code"
        currentUnitCode="PRG-T09-C01-U02"
        dueUnits={[]}
        weakSpotUnits={[
          {
            unitCode: "PRG-T09-C01-U02",
            unitTitle: "Async Error Boundaries",
            subject: "PRG",
            itemCount: 3,
            drillCount: 1,
            open: [
              {
                id: "U-no-input-mutation",
                detail: "Never mutate `req.body` directly.",
                matches: 2,
                drills: 2,
                last: "2026-11-12",
                subject: "PRG",
              },
            ],
            closed: [],
            levels: {},
            assistedCount: 0,
            skipped: [],
          },
        ]}
      />
    );
    assert.match(prgHtml, /Nothing due today/);
    assert.match(prgHtml, /Checks and lint rules/);
    assert.match(prgHtml, /U-no-input-mutation/);
    assert.match(prgHtml, /<code[^>]*>req\.body<\/code>/);

    const prgEmptyHtml = renderToStaticMarkup(
      <StudioSidePanel
        workspace="code"
        currentUnitCode="PRG-T09-C01-U02"
        dueUnits={[]}
        weakSpotUnits={[]}
      />
    );
    assert.match(prgEmptyHtml, /No open check or lint issues in this unit\./);

    const shellSource = fs.readFileSync("src/components/shell/StudioShell.tsx", "utf8");
    assert.match(shellSource, /useState\(false\)/, "drawer must be closed by default");
    assert.match(shellSource, /hidden lg:block/, "side panel visible on >=1024px");
    assert.match(shellSource, /lg:hidden/, "drawer only below 1024px");

    fs.rmSync(tmp, { recursive: true, force: true });
    console.log("side panel tests passed");
  } finally {
    if (prevProgressDir === undefined) delete process.env.PROGRESS_DIR;
    else process.env.PROGRESS_DIR = prevProgressDir;
    if (prevPilot === undefined) delete process.env.LEARNINGOS_PILOT;
    else process.env.LEARNINGOS_PILOT = prevPilot;
    if (prevDrillsDir === undefined) delete process.env.DRILLS_DATA_DIR;
    else process.env.DRILLS_DATA_DIR = prevDrillsDir;
  }
}

runTests().catch((err) => {
  console.error(err);
  process.exit(1);
});
