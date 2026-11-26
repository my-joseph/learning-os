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
import { GET as recentMistakesGET } from "../src/app/api/recent-mistakes/route";
import { GET as reviewItemsGET } from "../src/app/api/review-items/route";
import { canShowMistakeHistory, mistakeName, mistakePracticeHref } from "../src/lib/mistakePractice";
import { getRecentMistakes } from "../src/lib/reviewItems";
import type { ProblemState } from "../src/types/drill";
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

    const recentRes = recentMistakesGET(
      new NextRequest("http://127.0.0.1:3000/api/recent-mistakes?subject=MTH&unit=MTH-T09-C01-U01")
    );
    assert.equal(recentRes.status, 200);
    const { mistakes: mathMistakes } = await recentRes.json();
    assert.equal(mathMistakes.length, 1);
    assert.equal(mathMistakes[0].name, "Sign flip");
    assert.equal(mathMistakes[0].recentMisses, 2);
    assert.equal(mathMistakes[0].recentTries, 2);
    assert.doesNotMatch(JSON.stringify(mathMistakes), /c09-sign-flip|Q01|DRL-/);
    const reviewHref = mistakePracticeHref(mathMistakes[0].key);
    const scope = new URL(reviewHref, "http://127.0.0.1").searchParams.get("scope");
    const focusedRes = await reviewItemsGET(new NextRequest(
      `http://127.0.0.1:3000/api/review-items?today=2026-11-01&scope=${scope}`
    ));
    assert.equal(focusedRes.status, 200);
    const focused = await focusedRes.json();
    assert.deepEqual(focused.items.map((item: { qid: string }) => item.qid), ["Q01", "Q02"]);
    assert.equal(focused.bySubject.MTH, 0, "early practice must not affect the due count");
    assert.ok(focused.items.every((item: { commonTrapTag: unknown }) => item.commonTrapTag === null));

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
        showMistakes
        mistakes={mathMistakes}
      />
    );
    assert.match(mathHtml, /Due today/);
    assert.match(mathHtml, />10 total across workspaces<\/span>/, "header count must be the all-workspace total");
    assert.match(mathHtml, /7<\/span> due · next 7 · ~11 min/);
    assert.match(mathHtml, /10 total across workspaces/);
    assert.match(mathHtml, /Start review · 7 of 7/);
    assert.match(mathHtml, /min-h-\[36px\][^>]*>3 due in the other workspace/);
    assert.match(mathHtml, /href="\/review\?scope=subject:MTH"/);
    assert.match(mathHtml, /href="\/review\?scope=subject:PRG"/);
    assert.match(mathHtml, /Start review/);
    // Unit mastery context for current unit stays visible with dots and cap reason, NOT as a to-do link:
    assert.match(mathHtml, /Complex Conjugates/);
    assert.match(mathHtml, /Mastery 2 of 4/);
    assert.match(mathHtml, /Capped at <span[^>]*>2<\/span> · <span[^>]*>needs one L4 challenge without hints/);
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
      />
    );
    assert.match(cappedSessionHtml, /36 total across workspaces/);
    assert.match(cappedSessionHtml, /29<\/span> due · next 8 · ~12 min/);
    assert.match(cappedSessionHtml, /Start review · 8 of 29/);
    assert.doesNotMatch(
      mathHtml,
      /href="\/code\/DRL-PRG-T09-C01-01"/,
      "Panel must not list other-workspace due units as a to-do list"
    );
    assert.doesNotMatch(mathHtml, /Async Error Boundaries/);
    assert.match(mathHtml, /What I get wrong/);
    assert.match(mathHtml, /Missed 2 of last 2/);
    assert.match(mathHtml, /aria-expanded="true"/);
    assert.match(mathHtml, /Sign flip/);
    assert.doesNotMatch(mathHtml, /c09-sign-flip/);
    assert.ok(mathHtml.includes(`href="${reviewHref}"`));

    // 4b. Fallback 1.5 min per item when estimatedMinutes is omitted (5 * 1.5 = 7.5 -> ~8 min)
    const fallbackEstimateHtml = renderToStaticMarkup(
      <StudioSidePanel
        workspace="math"
        currentUnitCode="MTH-T09-C01-U01"
        dueReviewCount={5}
        reviewSessionSize={5}
        dueUnits={due.units}
      />
    );
    assert.match(fallbackEstimateHtml, /5<\/span> due · next 5 · ~8 min/);
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
        showMistakes
        mistakes={[{ ...mathMistakes[0], name: "Input changed in place", fixed: true }]}
      />
    );
    assert.match(prgHtml, /4<\/span> due · next 4 · ~9 min/);
    assert.match(prgHtml, /10 total across workspaces/);
    assert.match(prgHtml, /6 due in the other workspace/);
    assert.match(prgHtml, /href="\/review\?scope=subject:PRG"/);
    assert.match(prgHtml, /href="\/review\?scope=subject:MTH"/);
    assert.match(prgHtml, /Mastery 1 of 4/);
    assert.match(prgHtml, /Input changed in place/);
    assert.match(prgHtml, />Fixed</);
    assert.doesNotMatch(prgHtml, /U-no-input-mutation/);

    // 4d. Empty workspace due queue still shows other-workspace hint and nextDueDate
    const prgEmptyHtml = renderToStaticMarkup(
      <StudioSidePanel
        workspace="code"
        currentUnitCode="PRG-T09-C01-U02"
        dueReviewCount={0}
        otherWorkspaceDueCount={2}
        nextDueDate="2026-11-22"
        dueUnits={due.units}
        showMistakes
      />
    );
    assert.match(prgEmptyHtml, /Nothing due today/);
    assert.match(prgEmptyHtml, /Next due: 2026-11-22/);
    assert.match(prgEmptyHtml, /2 due in the other workspace/);
    assert.match(prgEmptyHtml, /2 total across workspaces/);
    assert.match(prgEmptyHtml, /Nothing you keep getting wrong in this unit yet\./);

    const loadingDrillHtml = renderToStaticMarkup(
      <StudioSidePanel workspace="code" drillLoading dueLoading showMistakes mistakes={mathMistakes} />
    );
    assert.match(loadingDrillHtml, /aria-label="Loading due reviews"/);
    assert.match(loadingDrillHtml, /aria-expanded="false"/);
    assert.doesNotMatch(loadingDrillHtml, /Nothing you keep getting wrong|Sign flip|Practise/);

    const loadingMistakesHtml = renderToStaticMarkup(
      <StudioSidePanel workspace="math" showMistakes mistakesLoading />
    );
    assert.match(loadingMistakesHtml, /aria-label="Loading recent mistakes"/);

    const errorHtml = renderToStaticMarkup(
      <StudioSidePanel workspace="math" showMistakes mistakesError />
    );
    assert.match(errorHtml, /Could not load recent mistakes/);

    const unansweredHtml = renderToStaticMarkup(
      <StudioSidePanel workspace="math" mistakes={mathMistakes} embedded />
    );
    assert.match(unansweredHtml, /What I get wrong/);
    assert.match(unansweredHtml, /aria-expanded="false"/);
    assert.doesNotMatch(unansweredHtml, /Missed 2|Sign flip|Practise|mistake%3A/);
    assert.match(unansweredHtml, /overflow-x-hidden/);
    assert.doesNotMatch(unansweredHtml, /rounded-2xl border|-mx-/);

    const baseState: ProblemState = { userInput: "draft", score: null, mistakes: [], divergedStep: null };
    const previousAttempt = { input: "", verdict: "incorrect", ts: "2026-11-01" };
    const resetState = { ...baseState, cycleStartedAt: "2026-11-02", attempts: [previousAttempt] };
    assert.equal(canShowMistakeHistory(baseState), false);
    assert.equal(canShowMistakeHistory(resetState), false);
    assert.equal(canShowMistakeHistory({ ...resetState, attempts: [{ ...previousAttempt, verdict: "parse_error", ts: "2026-11-02" }] }), false);
    assert.equal(canShowMistakeHistory({ ...baseState, attempts: [{ ...previousAttempt, verdict: "skipped" }] }), false);
    assert.equal(canShowMistakeHistory({ ...baseState, attempts: [previousAttempt] }), true);
    assert.equal(canShowMistakeHistory(baseState, "similar"), false);
    assert.equal(canShowMistakeHistory({ ...baseState, attempts: [{ ...previousAttempt, kind: "variant" }] }, "similar"), true);
    assert.equal(canShowMistakeHistory({ ...baseState, testRuns: [{ ts: "2026-11-02", allPassed: false }] }, "code"), true);

    const shellSource = fs.readFileSync("src/components/shell/StudioShell.tsx", "utf8");
    const sidePanelDataSource = fs.readFileSync("src/hooks/useSidePanelData.ts", "utf8");
    assert.match(shellSource, /useState\(false\)/, "drawer must be closed by default");
    assert.match(shellSource, /hidden lg:block/, "side panel visible on >=1024px");
    assert.match(shellSource, /lg:hidden/, "drawer only below 1024px");
    assert.match(shellSource, /embedded/, "drawer must pass embedded to StudioSidePanel");
    assert.match(shellSource, /drillLoading=\{isLoadingDrill\}/, "shell must forward drillLoading state to side panel");
    assert.match(sidePanelDataSource, /api\/review-items\?limit=8/, "session size must come from the API-limited item batch");
    assert.match(
      sidePanelDataSource,
      /if \(!mistakesKey\) return/,
      "mistake history is fetched only when the active problem is safe to show it"
    );
    assert.match(shellSource, /overflow-x-hidden/, "mobile drawer panel must prevent horizontal overflow");
    assert.doesNotMatch(shellSource, /calc\(100vw-2\.5rem\)/, "invalid space-less calc() width must not remain on mobile drawer");

    const secondUnit = "MTH-T09-C01-U02";
    const otherMathId = `DRL-${secondUnit}-01`;
    fs.mkdirSync(path.join(dataDir, secondUnit));
    fs.writeFileSync(path.join(dataDir, secondUnit, `${otherMathId}.json`), JSON.stringify({
      drillId: otherMathId, unitCode: secondUnit,
      problems: [{ id: "Q01", commonTrapTag: "lost-factor" }],
    }));
    const attempt = (day: string, matchedTrap?: string) =>
      ({ verdict: matchedTrap ? "incorrect" : "correct", ts: `2026-11-${day}`, matchedTrap });
    fs.writeFileSync(path.join(progressDir, `${otherMathId}.json`), JSON.stringify({
      drillId: otherMathId,
      problems: { Q01: {
        attempts: [
          attempt("05", "lost-factor"), attempt("06", "lost-factor"),
          attempt("07"), attempt("08"), attempt("09"),
        ],
      } },
    }));
    const review = (day: string, missed: boolean) => ({
      at: `2026-11-${day}`,
      verdict: missed ? "revise" : "pass",
      findings: missed ? [{ check: "QC-RETURNS" }, { check: "QC-disputed", disputed: true }] : [],
      lint: missed ? [{ rule: "@typescript-eslint/no-explicit-any" }] : [],
      tests: { passed: 1, total: 1, failed: [] },
    });
    fs.writeFileSync(path.join(progressDir, "DRL-PRG-T09-C01-01.json"), JSON.stringify({
      drillId: "DRL-PRG-T09-C01-01",
      problems: { Q01: { reviews: [review("06", true), review("07", false), review("08", true)] } },
    }));
    assert.deepEqual(getRecentMistakes("MTH", secondUnit, { today: "2026-11-09" }).map((row) => [row.name, row.fixed, row.recentMisses, row.recentTries]), [
      ["Lost factor", true, 2, 5], ["Sign flip", false, 2, 2],
    ]);
    assert.deepEqual(getRecentMistakes("MTH", undefined, { today: "2026-11-09" }).map((row) => row.name), ["Sign flip", "Lost factor"]);
    assert.deepEqual(getRecentMistakes("MTH", secondUnit, { today: "2026-11-10" }).map((row) => row.name), ["Sign flip"]);
    const codeMistakes = getRecentMistakes("PRG", undefined, { today: "2026-11-09" });
    assert.deepEqual(codeMistakes.map((row) => row.name).sort(), ["Return value missing or incorrect", "Used any type"]);
    for (const row of codeMistakes) {
      const res = await reviewItemsGET(new NextRequest(`http://127.0.0.1:3000${mistakePracticeHref(row.key)}`));
      const payload = await res.json();
      assert.deepEqual(payload.items.map((item: { drillId: string }) => item.drillId), ["DRL-PRG-T09-C01-01"]);
    }
    assert.equal(mistakeName("QC-PRG-T09-C02-U03-check-result", "PRG", {}), "Check result");
    assert.equal(mistakeName("@new-plugin/no-draft-results", "PRG", {}), "No draft results");

    // 5. Bug #7: unitsWithL4Challenge parity with Python weak_spots._has_l4_challenge
    //    (cycle scoping for PRG & Math, review help timestamps, and variant attempt exclusion)
    {
      const l4Tmp = fs.mkdtempSync(path.join(os.tmpdir(), "studio-l4-parity-"));
      const l4Prog = path.join(l4Tmp, "progress");
      const l4Data = path.join(l4Tmp, "drills", "data");
      fs.mkdirSync(l4Prog, { recursive: true });
      fs.mkdirSync(path.join(l4Data, "PRG-T09-C02-U01"), { recursive: true });
      fs.mkdirSync(path.join(l4Data, "MTH-T09-C02-U01"), { recursive: true });
      fs.mkdirSync(path.join(l4Data, "MTH-T09-C02-U02"), { recursive: true });
      fs.mkdirSync(path.join(l4Data, "MTH-T09-C02-U03"), { recursive: true });

      // Unit 1 (PRG): Cycle 1 revise -> Cycle 2 clean pass -> MUST unlock L4 challenge (capped: false)
      fs.writeFileSync(
        path.join(l4Data, "PRG-T09-C02-U01", "DRL-PRG-T09-C02-U01-01.json"),
        JSON.stringify({
          drillId: "DRL-PRG-T09-C02-U01-01",
          subject: "PRG",
          unitCode: "PRG-T09-C02-U01",
          problems: [{ id: "Q01", level: 4, unitCode: "PRG-T09-C02-U01" }],
        })
      );
      fs.writeFileSync(
        path.join(l4Prog, "DRL-PRG-T09-C02-U01-01.json"),
        JSON.stringify({
          drillId: "DRL-PRG-T09-C02-U01-01",
          problems: {
            Q01: {
              cycleStartedAt: "2026-11-20T12:00:00Z",
              hintsRevealed: 1,
              reviews: [
                { at: "2026-11-18T10:00:00Z", verdict: "revise", tests: { passed: 3, total: 3, failed: [] } },
                { at: "2026-11-20T12:05:00Z", verdict: "pass", tests: { passed: 3, total: 3, failed: [] } },
              ],
            },
          },
        })
      );

      // Unit 2 (MTH): Cycle 1 clean -> Cycle 2 review setup revealed -> MUST stay capped (capped: true)
      fs.writeFileSync(
        path.join(l4Data, "MTH-T09-C02-U01", "DRL-MTH-T09-C02-U01-01.json"),
        JSON.stringify({
          drillId: "DRL-MTH-T09-C02-U01-01",
          unitCode: "MTH-T09-C02-U01",
          problems: [{ id: "Q01", level: 4, unitCode: "MTH-T09-C02-U01" }],
        })
      );
      fs.writeFileSync(
        path.join(l4Prog, "DRL-MTH-T09-C02-U01-01.json"),
        JSON.stringify({
          drillId: "DRL-MTH-T09-C02-U01-01",
          problems: {
            Q01: {
              cycleStartedAt: "2026-11-20T12:00:00Z",
              reviewSetupRevealedAt: "2026-11-20T12:01:00Z",
              score: 1,
              attempts: [
                { input: "5", ts: "2026-11-18T10:00:00Z", verdict: "correct" },
                { input: "5", ts: "2026-11-20T12:05:00Z", verdict: "correct" },
              ],
            },
          },
        })
      );

      // Unit 3 (MTH): Variant wrong attempt precedes clean original first-try correct -> MUST unlock L4 (capped: false)
      fs.writeFileSync(
        path.join(l4Data, "MTH-T09-C02-U02", "DRL-MTH-T09-C02-U02-01.json"),
        JSON.stringify({
          drillId: "DRL-MTH-T09-C02-U02-01",
          unitCode: "MTH-T09-C02-U02",
          problems: [{ id: "Q01", level: 4, unitCode: "MTH-T09-C02-U02" }],
        })
      );
      fs.writeFileSync(
        path.join(l4Prog, "DRL-MTH-T09-C02-U02-01.json"),
        JSON.stringify({
          drillId: "DRL-MTH-T09-C02-U02-01",
          problems: {
            Q01: {
              score: 1,
              attempts: [
                { input: "9", ts: "2026-11-18T09:55:00Z", verdict: "incorrect", kind: "variant" },
                { input: "5", ts: "2026-11-18T10:00:00Z", verdict: "correct" },
              ],
            },
          },
        })
      );

      // Unit 4 (MTH): Cycle 1 skipped -> Cycle 2 clean first-try correct -> MUST unlock L4 (capped: false)
      fs.writeFileSync(
        path.join(l4Data, "MTH-T09-C02-U03", "DRL-MTH-T09-C02-U03-01.json"),
        JSON.stringify({
          drillId: "DRL-MTH-T09-C02-U03-01",
          unitCode: "MTH-T09-C02-U03",
          problems: [{ id: "Q01", level: 4, unitCode: "MTH-T09-C02-U03" }],
        })
      );
      fs.writeFileSync(
        path.join(l4Prog, "DRL-MTH-T09-C02-U03-01.json"),
        JSON.stringify({
          drillId: "DRL-MTH-T09-C02-U03-01",
          problems: {
            Q01: {
              skipped: true,
              score: 0,
              cycleStartedAt: "2026-11-20T12:00:00Z",
              attempts: [
                { input: "(Skipped)", ts: "2026-11-18T10:00:00Z", verdict: "skipped" },
                { input: "5", ts: "2026-11-20T12:05:00Z", verdict: "correct" },
              ],
            },
          },
        })
      );

      fs.writeFileSync(
        path.join(l4Prog, "_review_schedule.json"),
        JSON.stringify({
          "PRG-T09-C02-U01": { mastery: 2, lastReviewed: "2026-11-18", nextReview: "2026-11-20", title: "PRG L4 Cycle" },
          "MTH-T09-C02-U01": { mastery: 2, lastReviewed: "2026-11-18", nextReview: "2026-11-20", title: "MTH L4 Setup" },
          "MTH-T09-C02-U02": { mastery: 2, lastReviewed: "2026-11-18", nextReview: "2026-11-20", title: "MTH L4 Variant" },
          "MTH-T09-C02-U03": { mastery: 2, lastReviewed: "2026-11-18", nextReview: "2026-11-20", title: "MTH L4 Skip Reset" },
        })
      );

      const l4Due = getDueTodayUnits({
        today: "2026-11-21",
        progressDir: l4Prog,
        dataDir: l4Data,
        rootDir: l4Tmp,
      });
      assert.equal(
        l4Due.unitMastery?.["PRG-T09-C02-U01"]?.masteryCap.capped,
        false,
        "PRG L4 clean pass in new cycle must lift L4 mastery cap"
      );
      assert.equal(
        l4Due.unitMastery?.["MTH-T09-C02-U01"]?.masteryCap.capped,
        true,
        "MTH L4 with reviewSetupRevealedAt in new cycle must stay capped"
      );
      assert.equal(
        l4Due.unitMastery?.["MTH-T09-C02-U02"]?.masteryCap.capped,
        false,
        "MTH L4 must ignore kind:'variant' attempts and lift L4 mastery cap"
      );
      assert.equal(
        l4Due.unitMastery?.["MTH-T09-C02-U03"]?.masteryCap.capped,
        false,
        "MTH L4 clean answer in new cycle after prior-cycle skip must lift L4 mastery cap"
      );

      fs.rmSync(l4Tmp, { recursive: true, force: true });
    }

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
