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
          { id: "Q03", level: 4, form: "direct", commonTrapTag: "c09-sign-flip" },
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
          Q03: {
            attempts: [{ verdict: "correct", ts: "2026-11-03", exampleViewed: true }],
            exampleViewedAt: "2026-11-03T09:00:00Z",
            score: 0.5,
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
    assert.deepEqual(due.units[0].masteryCap, {
      capped: true,
      reason: "needs one L4 challenge without hints",
    });
    assert.deepEqual(due.units[1].masteryCap, {
      capped: false,
      reason: "",
    });

    // Route /api/due-today
    const dueRes = await dueTodayGET();
    assert.equal(dueRes.status, 200);
    const dueJson = (await dueRes.json()) as {
      today: string;
      units: Array<{ unitCode: string; masteryCap: { capped: boolean; reason: string } }>;
    };
    assert.ok(Array.isArray(dueJson.units));
    assert.deepEqual(dueJson.units[0]?.masteryCap, {
      capped: true,
      reason: "needs one L4 challenge without hints",
    });

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
      units: Array<{
        unitCode: string;
        open: Array<{ id: string }>;
        masteryCap: { capped: boolean; reason: string };
      }>;
    };
    assert.equal(wsJson.scope, "MTH-T09-C01-U01");
    assert.equal(wsJson.units.length, 1);
    assert.deepEqual(
      wsJson.units[0].open.map((x) => x.id),
      ["c09-sign-flip"]
    );
    assert.deepEqual(wsJson.units[0].masteryCap, {
      capped: false,
      reason: "",
    });

    // 4. Component rendering: one-queue item counts, workspace split, unit mastery context,
    //    no unit to-do list, loading skeleton while drill loads, and mobile overflow guards
    assert.ok(due.unitMastery?.["MTH-T09-C01-U01"]);
    assert.ok(due.unitMastery?.["MTH-T09-C01-U03"], "unitMastery includes non-due units as context");

    // 4a. Math workspace: header count & CTA come from item-level dueReviewCount (NOT dueUnits.length),
    //     shows the current due count and capped session estimate, a full-width other-workspace row,
    //     and keeps current unit mastery dots + "Capped at 2 · …" as context only.
    const mathHtml = renderToStaticMarkup(
      <StudioSidePanel
        workspace="math"
        currentUnitCode="MTH-T09-C01-U01"
        dueReviewCount={7}
        reviewSessionSize={7}
        otherWorkspaceDueCount={3}
        estimatedMinutes={11}
        currentUnitMastery={due.unitMastery?.["MTH-T09-C01-U01"]}
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
    assert.match(mathHtml, />10 total across workspaces<\/span>/, "header count must be the all-workspace total");
    assert.match(mathHtml, /7 due · next 7 · ~11 min/);
    assert.match(mathHtml, /10 total across workspaces/);
    assert.match(mathHtml, /Start review · 7 of 7/);
    assert.match(mathHtml, /min-h-\[36px\][^>]*>3 due in the other workspace/);
    assert.match(mathHtml, /href="\/review\?scope=subject:MTH"/);
    assert.match(mathHtml, /href="\/review\?scope=subject:PRG"/);
    assert.match(mathHtml, /Start review/);
    // Unit mastery context for current unit stays visible with dots and cap reason, NOT as a to-do link:
    assert.match(mathHtml, /Complex Conjugates/);
    assert.match(mathHtml, /Mastery 2 of 4/);
    assert.match(mathHtml, /Capped at 2 · needs one L4 challenge without hints/);
    assert.doesNotMatch(
      mathHtml,
      /href="\/math\/DRL-MTH-T09-C01-U01-02"/,
      "Panel must not list due units as a second to-do list"
    );

    const cappedSessionHtml = renderToStaticMarkup(
      <StudioSidePanel
        workspace="math"
        dueReviewCount={29}
        reviewSessionSize={8}
        otherWorkspaceDueCount={7}
        estimatedMinutes={44}
        weakSpotUnits={[]}
      />
    );
    assert.match(cappedSessionHtml, /36 total across workspaces/);
    assert.match(cappedSessionHtml, /29 due · next 8 · ~12 min/);
    assert.match(cappedSessionHtml, /Start review · 8 of 29/);
    assert.doesNotMatch(
      mathHtml,
      /href="\/code\/DRL-PRG-T09-C01-01"/,
      "Panel must not list other-workspace due units as a to-do list"
    );
    assert.doesNotMatch(mathHtml, /Async Error Boundaries/);
    assert.match(mathHtml, /Repeated traps/);
    assert.match(mathHtml, /c09-sign-flip/);

    // 4b. Fallback 1.5 min per item when estimatedMinutes is omitted (5 * 1.5 = 7.5 -> ~8 min)
    const fallbackEstimateHtml = renderToStaticMarkup(
      <StudioSidePanel
        workspace="math"
        currentUnitCode="MTH-T09-C01-U01"
        dueReviewCount={5}
        reviewSessionSize={5}
        dueUnits={due.units}
        weakSpotUnits={[]}
      />
    );
    assert.match(fallbackEstimateHtml, /5 due · next 5 · ~8 min/);
    assert.match(fallbackEstimateHtml, /href="\/review\?scope=subject:MTH"/);
    assert.doesNotMatch(fallbackEstimateHtml, /in the other workspace/);

    // 4c. Code workspace split: /code shows PRG items and hints MTH count in the other workspace
    const prgHtml = renderToStaticMarkup(
      <StudioSidePanel
        workspace="code"
        currentUnitCode="PRG-T09-C01-U02"
        dueReviewCount={4}
        reviewSessionSize={4}
        otherWorkspaceDueCount={6}
        estimatedMinutes={9}
        currentUnitMastery={due.unitMastery?.["PRG-T09-C01-U02"]}
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
    assert.match(prgHtml, /4 due · next 4 · ~9 min/);
    assert.match(prgHtml, /10 total across workspaces/);
    assert.match(prgHtml, /6 due in the other workspace/);
    assert.match(prgHtml, /href="\/review\?scope=subject:PRG"/);
    assert.match(prgHtml, /href="\/review\?scope=subject:MTH"/);
    assert.match(prgHtml, /Mastery 1 of 4/);
    assert.match(prgHtml, /Checks and lint rules/);
    assert.match(prgHtml, /U-no-input-mutation/);
    assert.match(prgHtml, /<code[^>]*>req\.body<\/code>/);

    // 4d. Empty workspace due queue still shows other-workspace hint and nextDueDate
    const prgEmptyHtml = renderToStaticMarkup(
      <StudioSidePanel
        workspace="code"
        currentUnitCode="PRG-T09-C01-U02"
        dueReviewCount={0}
        otherWorkspaceDueCount={2}
        nextDueDate="2026-11-22"
        dueUnits={due.units}
        weakSpotUnits={[]}
      />
    );
    assert.match(prgEmptyHtml, /Nothing due today/);
    assert.match(prgEmptyHtml, /Next due: 2026-11-22/);
    assert.match(prgEmptyHtml, /2 due in the other workspace/);
    assert.match(prgEmptyHtml, /2 total across workspaces/);
    assert.match(prgEmptyHtml, /No open check or lint issues in this unit\./);
    // Header count must NOT show dueUnits.length when dueReviewCount is 0
    assert.doesNotMatch(prgEmptyHtml, /Due today<\/h2><span[^>]*>2<\/span>/);

    // 4e. Loading skeleton while drill is still loading: NEVER show "Open a drill to see unit weak spots."
    const loadingDrillHtml = renderToStaticMarkup(
      <StudioSidePanel
        workspace="code"
        currentUnitCode={undefined}
        drillLoading={true}
        dueLoading={true}
        dueReviewCount={0}
        weakSpotUnits={[]}
      />
    );
    assert.doesNotMatch(
      loadingDrillHtml,
      /Open a drill to see unit weak spots/,
      "Must not show 'Open a drill to see unit weak spots.' while a drill is still loading"
    );
    assert.match(loadingDrillHtml, /animate-pulse/);
    assert.match(loadingDrillHtml, /aria-label="Loading unit weak spots"/);
    assert.match(loadingDrillHtml, /aria-label="Loading due reviews"/);

    // When NOT loading and no drill is open, the empty prompt IS shown
    const noDrillOpenHtml = renderToStaticMarkup(
      <StudioSidePanel
        workspace="code"
        currentUnitCode={undefined}
        drillLoading={false}
        weakLoading={false}
        dueReviewCount={0}
        weakSpotUnits={[]}
      />
    );
    assert.match(noDrillOpenHtml, /Open a drill to see unit weak spots\./);

    const embeddedDrawerHtml = renderToStaticMarkup(
      <StudioSidePanel
        workspace="math"
        currentUnitCode="MTH-T09-C01-U01"
        dueReviewCount={3}
        reviewSessionSize={3}
        weakSpotUnits={[]}
        embedded
      />
    );
    assert.doesNotMatch(embeddedDrawerHtml, /rounded-2xl border/, "embedded side panel must not render a nested bordered card");
    assert.doesNotMatch(embeddedDrawerHtml, /-mx-/, "panel must not use negative horizontal margins that overflow mobile drawer");
    assert.match(embeddedDrawerHtml, /overflow-x-hidden/);

    const shellSource = fs.readFileSync("src/components/shell/StudioShell.tsx", "utf8");
    const sidePanelDataSource = fs.readFileSync("src/hooks/useSidePanelData.ts", "utf8");
    assert.match(shellSource, /useState\(false\)/, "drawer must be closed by default");
    assert.match(shellSource, /hidden lg:block/, "side panel visible on >=1024px");
    assert.match(shellSource, /lg:hidden/, "drawer only below 1024px");
    assert.match(shellSource, /embedded/, "drawer must pass embedded to StudioSidePanel");
    assert.match(sidePanelDataSource, /api\/review-items\?limit=8/, "session size must come from the API-limited item batch");
    assert.match(shellSource, /overflow-x-hidden/, "mobile drawer panel must prevent horizontal overflow");
    assert.doesNotMatch(shellSource, /calc\(100vw-2\.5rem\)/, "invalid space-less calc() width must not remain on mobile drawer");

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
