import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { NextRequest } from "next/server";
import { GET, POST, PUT } from "../src/app/api/workspace/route";
import { GET as drillGET } from "../src/app/api/drill/route";
import { POST as runTestsPOST } from "../src/app/api/run-tests/route";
import { GET as labGET } from "../src/app/api/lab/route";

function makeGetReq(params: Record<string, string>): NextRequest {
  const url = new URL("http://127.0.0.1:3000/api/workspace");
  for (const [k, v] of Object.entries(params)) {
    url.searchParams.set(k, v);
  }
  return new NextRequest(url);
}

function makeJsonReq(method: "PUT" | "POST", body: unknown): NextRequest {
  return new NextRequest("http://127.0.0.1:3000/api/workspace", {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

async function main() {
  const outerDir = fs.mkdtempSync(path.join(os.tmpdir(), "learningos-ws-outer-"));
  const repoRoot = path.join(outerDir, "repo");
  const outsideSecretPath = path.join(outerDir, "outside-secret.txt");
  fs.mkdirSync(repoRoot, { recursive: true });
  fs.writeFileSync(outsideSecretPath, "TOP_SECRET_OUTSIDE", "utf-8");

  const drillId = "DRL-PRG-TEST-01";
  const unitCode = "PRG-T01-C01-U01";
  const drillsUnitDir = path.join(repoRoot, "drills", "data", unitCode);
  const wsDir = path.join(repoRoot, "drills", "workspace", drillId);
  const pilotWsDir = path.join(repoRoot, "pilot", "workspace", drillId);

  fs.mkdirSync(drillsUnitDir, { recursive: true });
  fs.mkdirSync(wsDir, { recursive: true });
  fs.mkdirSync(pilotWsDir, { recursive: true });

  const workspaceFileRel = `drills/workspace/${drillId}/Q01_solve.js`;
  const symlinkedWorkspaceFileRel = `drills/workspace/${drillId}/Q02_symlink.js`;
  const danglingWorkspaceFileRel = `drills/workspace/${drillId}/Q03_dangling.js`;
  const pilotWorkspaceFileRel = `pilot/workspace/${drillId}/Q01_solve.js`;

  const drillDoc = {
    drillId,
    unitCode,
    unitTitle: "Workspace Security Test",
    environment: "node-vanilla",
    problems: [
      {
        id: "Q01",
        codeType: "implement",
        entryPoint: "solve",
        prompt: "Return input.",
        starterCode: "function solve(x) { return x; }\nmodule.exports = { solve };\n",
        solutionCode: "function solve(x) { return x; }\nmodule.exports = { solve };\n",
        visibleTests: [{ name: "basic", testCode: "assert.strictEqual(solve(1), 1);" }],
        hiddenTests: [{ name: "hidden", testCode: "assert.strictEqual(solve(2), 2);" }],
        workspaceFile: workspaceFileRel,
      },
      {
        id: "Q02",
        codeType: "implement",
        entryPoint: "symlink",
        prompt: "Symlink escape target.",
        starterCode: "function symlink() {}\nmodule.exports = { symlink };\n",
        workspaceFile: symlinkedWorkspaceFileRel,
      },
      {
        id: "Q03",
        codeType: "implement",
        entryPoint: "dangling",
        prompt: "Dangling symlink target.",
        starterCode: "function dangling() {}\nmodule.exports = { dangling };\n",
        workspaceFile: danglingWorkspaceFileRel,
      },
      { id: "Q04", prompt: "Inline check fixture." },
    ],
  };

  const drillJsonRel = `drills/data/${unitCode}/${drillId}.json`;
  const drillJsonPath = path.join(repoRoot, drillJsonRel);
  fs.writeFileSync(drillJsonPath, JSON.stringify(drillDoc, null, 2), "utf-8");

  const validFilePath = path.join(repoRoot, workspaceFileRel);
  fs.writeFileSync(validFilePath, "// starter code\n", "utf-8");
  fs.writeFileSync(path.join(wsDir, "package.json"), '{"name":"ws"}\n', "utf-8");

  // Symlink inside the drill workspace pointing to drills/data (an allowlisted filename too!)
  const symlinkEscapePath = path.join(repoRoot, symlinkedWorkspaceFileRel);
  fs.symlinkSync(drillJsonPath, symlinkEscapePath);

  // Dangling symlink pointing outside repoRoot (tests PUT never creates outside files)
  const danglingOutsideTarget = path.join(outerDir, "created-via-dangling-symlink.txt");
  const danglingSymlinkPath = path.join(repoRoot, danglingWorkspaceFileRel);
  fs.symlinkSync(danglingOutsideTarget, danglingSymlinkPath);

  // Pilot workspace file
  fs.writeFileSync(path.join(repoRoot, pilotWorkspaceFileRel), "// pilot starter\n", "utf-8");

  const prevRoot = process.env.LEARNINGOS_ROOT;
  const prevDrillsDir = process.env.DRILLS_DATA_DIR;
  const prevPilot = process.env.LEARNINGOS_PILOT;
  const prevProgress = process.env.PROGRESS_DIR;
  process.env.PROGRESS_DIR = path.join(outerDir, "progress");

  process.env.LEARNINGOS_ROOT = repoRoot;
  delete process.env.DRILLS_DATA_DIR;
  delete process.env.LEARNINGOS_PILOT;

  try {
    // 1. GET drills/data file -> 403
    {
      const res = await GET(makeGetReq({ file: drillJsonRel, drillId }));
      assert.equal(res.status, 403, "GET drills/data file must return 403");
    }

    // 2. GET ../ escape -> 403
    {
      const res1 = await GET(makeGetReq({ file: "../outside-secret.txt", drillId }));
      assert.equal(res1.status, 403, "GET ../ escape must return 403");

      const res2 = await GET(
        makeGetReq({
          file: `drills/workspace/${drillId}/../../data/${unitCode}/${drillId}.json`,
          drillId,
        })
      );
      assert.equal(res2.status, 403, "GET workspace/../ escape must return 403");
    }

    // 3. GET symlink escape -> 403
    {
      const res = await GET(makeGetReq({ file: symlinkedWorkspaceFileRel, drillId }));
      assert.equal(res.status, 403, "GET symlink escape must return 403");
    }

    // 4. GET non-allowlisted file inside workspace dir (package.json) -> 403
    {
      const res = await GET(
        makeGetReq({ file: `drills/workspace/${drillId}/package.json`, drillId })
      );
      assert.equal(res.status, 403, "GET non-workspaceFile inside workspace dir must return 403");
    }

    // 5. GET missing or invalid drillId -> 400
    {
      const resMissing = await GET(makeGetReq({ file: workspaceFileRel }));
      assert.equal(resMissing.status, 400, "GET without drillId must return 400");

      const resBad = await GET(makeGetReq({ file: workspaceFileRel, drillId: "../evil" }));
      assert.equal(resBad.status, 400, "GET with unsafe drillId must return 400");
    }

    // 6. GET valid workspace file -> 200 and no absolute server path leaked
    {
      const res = await GET(makeGetReq({ file: workspaceFileRel, drillId }));
      assert.equal(res.status, 200, "GET valid workspace file must return 200");
      const json = (await res.json()) as Record<string, unknown>;
      assert.equal(json.content, "// starter code\n");
      assert.equal("fullPath" in json, false, "GET response must not include fullPath");
      assert.equal(
        JSON.stringify(json).includes(repoRoot),
        false,
        "GET response must not echo repoRoot"
      );
    }

    // 7. PUT outside (drills/data, ../ escape, symlink escape, dangling symlink, package.json) -> 403
    {
      const beforeDrillJson = fs.readFileSync(drillJsonPath, "utf-8");

      const resData = await PUT(
        makeJsonReq("PUT", { drillId, file: drillJsonRel, content: "OVERWRITTEN" })
      );
      assert.equal(resData.status, 403, "PUT drills/data file must return 403");
      assert.equal(fs.readFileSync(drillJsonPath, "utf-8"), beforeDrillJson);

      const resParent = await PUT(
        makeJsonReq("PUT", { drillId, file: "../outside-secret.txt", content: "OVERWRITTEN" })
      );
      assert.equal(resParent.status, 403, "PUT ../ escape must return 403");
      assert.equal(fs.readFileSync(outsideSecretPath, "utf-8"), "TOP_SECRET_OUTSIDE");

      const resSym = await PUT(
        makeJsonReq("PUT", { drillId, file: symlinkedWorkspaceFileRel, content: "OVERWRITTEN" })
      );
      assert.equal(resSym.status, 403, "PUT symlink escape must return 403");
      assert.equal(fs.readFileSync(drillJsonPath, "utf-8"), beforeDrillJson);

      const resDangling = await PUT(
        makeJsonReq("PUT", { drillId, file: danglingWorkspaceFileRel, content: "CREATED" })
      );
      assert.equal(resDangling.status, 403, "PUT dangling symlink escape must return 403");
      assert.equal(fs.existsSync(danglingOutsideTarget), false);

      const resPkg = await PUT(
        makeJsonReq("PUT", {
          drillId,
          file: `drills/workspace/${drillId}/package.json`,
          content: "{}",
        })
      );
      assert.equal(resPkg.status, 403, "PUT non-workspaceFile in workspace must return 403");
    }

    // 8. PUT missing/invalid drillId -> 400
    {
      const resMissing = await PUT(
        makeJsonReq("PUT", { file: workspaceFileRel, content: "// no drillId" })
      );
      assert.equal(resMissing.status, 400, "PUT without drillId must return 400");

      const resBad = await PUT(
        makeJsonReq("PUT", { drillId: "../../etc", file: workspaceFileRel, content: "// bad" })
      );
      assert.equal(resBad.status, 400, "PUT with unsafe drillId must return 400");
    }

    // 9. PUT valid workspace file -> 200, writes content, does not leak fullPath
    {
      const updated = "// updated solution\n";
      const res = await PUT(
        makeJsonReq("PUT", { drillId, file: workspaceFileRel, content: updated })
      );
      assert.equal(res.status, 200, "PUT valid workspace file must return 200");
      const json = (await res.json()) as Record<string, unknown>;
      assert.equal(json.ok, true);
      assert.equal("fullPath" in json, false, "PUT response must not include fullPath");
      assert.equal(fs.readFileSync(validFilePath, "utf-8"), updated);
    }

    // 10. POST with arbitrary drill document -> 400
    {
      const resDocOnly = await POST(
        makeJsonReq("POST", { problems: [{ id: "Q01", starterCode: "evil()" }] })
      );
      assert.equal(resDocOnly.status, 400, "POST with arbitrary doc (no drillId) must return 400");

      const resDocWithId = await POST(
        makeJsonReq("POST", {
          drillId,
          problems: [{ id: "Q01", starterCode: "evil()" }],
        })
      );
      assert.equal(
        resDocWithId.status,
        400,
        "POST with drillId plus arbitrary doc fields must return 400"
      );

      const resUnsafeId = await POST(makeJsonReq("POST", { drillId: "../evil" }));
      assert.equal(resUnsafeId.status, 400, "POST with unsafe drillId must return 400");
    }

    // Materialization refuses redirected outputs and succeeds after the links are removed.
    {
      const res = await POST(makeJsonReq("POST", { drillId }));
      assert.equal(res.status, 404);
      assert.equal(fs.existsSync(danglingOutsideTarget), false);
      fs.unlinkSync(symlinkEscapePath);
      fs.unlinkSync(danglingSymlinkPath);
    }

    for (const file of [
      validFilePath,
      `drills/workspace/${drillId}/sub/../Q01_solve.js`,
      `drills/workspace/${drillId}/%51%30%31_solve.js`,
    ]) {
      assert.equal((await GET(makeGetReq({ file, drillId }))).status, 403);
      assert.equal((await PUT(makeJsonReq("PUT", { drillId, file, content: "" }))).status, 403);
    }

    const missingManifest = await runTestsPOST(
      makeJsonReq("POST", { drillId, problemId: "Q04", workspaceFile: workspaceFileRel })
    );
    assert.equal(missingManifest.status, 403);

    // 11. POST with valid { drillId } -> 200, no absolute server paths leaked
    {
      const res = await POST(makeJsonReq("POST", { drillId }));
      assert.equal(res.status, 200, "POST with valid { drillId } must return 200");
      const json = (await res.json()) as Record<string, unknown>;
      assert.equal(json.ok, true);
      assert.equal("fullPath" in json, false);
      assert.equal("manifest" in json, false);
      assert.equal(JSON.stringify(json).includes(repoRoot), false);
    }

    // 12. Pilot mode scopes GET/PUT to pilot/workspace/<drillId>/ and maps client-sent drills/workspace/<id>/... to pilot/workspace/<id>/... (C-03)
    {
      process.env.LEARNINGOS_PILOT = "1";
      const resPilotOk = await GET(makeGetReq({ file: pilotWorkspaceFileRel, drillId }));
      assert.equal(resPilotOk.status, 200, "GET pilot workspace file in pilot mode must return 200");
      const pilotJson = (await resPilotOk.json()) as Record<string, unknown>;
      assert.equal(pilotJson.content, "// pilot starter\n");

      // Client-sent drills/workspace/<id>/... maps to pilot/workspace/<id>/... (never reads non-pilot workspace)
      const resMappedGet = await GET(makeGetReq({ file: workspaceFileRel, drillId }));
      assert.equal(
        resMappedGet.status,
        200,
        "GET client-sent drills/workspace/<id>/... in pilot mode must map to pilot dir"
      );
      const mappedGetJson = (await resMappedGet.json()) as Record<string, unknown>;
      assert.equal(
        mappedGetJson.content,
        "// pilot starter\n",
        "Mapped GET in pilot mode must read pilot file, not non-pilot file"
      );

      const nonPilotBefore = fs.readFileSync(validFilePath, "utf-8");
      const pilotUpdatedCode = "function solve(x) { return x; }\nmodule.exports = { solve };\n";
      const resMappedPut = await PUT(
        makeJsonReq("PUT", {
          drillId,
          file: workspaceFileRel,
          content: pilotUpdatedCode,
        })
      );
      assert.equal(
        resMappedPut.status,
        200,
        "PUT client-sent drills/workspace/<id>/... in pilot mode must map to pilot dir"
      );
      assert.equal(
        fs.readFileSync(path.join(repoRoot, pilotWorkspaceFileRel), "utf-8"),
        pilotUpdatedCode,
        "Mapped PUT in pilot mode must write to pilot/workspace/<id>/..."
      );
      assert.equal(
        fs.readFileSync(validFilePath, "utf-8"),
        nonPilotBefore,
        "Mapped PUT in pilot mode must never modify real drills/workspace/<id>/..."
      );

      // Absolute path or .. traversal to real drills/workspace in pilot mode is still blocked (403)
      const resAbsNonPilot = await GET(makeGetReq({ file: validFilePath, drillId }));
      assert.equal(
        resAbsNonPilot.status,
        403,
        "GET absolute drills/workspace path in pilot mode must return 403"
      );
      const resTraversalNonPilot = await GET(
        makeGetReq({
          file: `pilot/workspace/${drillId}/../../../drills/workspace/${drillId}/Q01_solve.js`,
          drillId,
        })
      );
      assert.equal(
        resTraversalNonPilot.status,
        403,
        "GET traversal to drills/workspace in pilot mode must return 403"
      );
    }

    // 13. /api/drill, /api/run-tests, and /api/lab respect LEARNINGOS_PILOT (C-03)
    {
      // Write a broken solution in non-pilot workspace and a passing solution in pilot workspace
      fs.writeFileSync(
        validFilePath,
        "function solve() { return 999; }\nmodule.exports = { solve };\n",
        "utf-8"
      );
      fs.writeFileSync(
        path.join(repoRoot, pilotWorkspaceFileRel),
        "function solve(x) { return x; }\nmodule.exports = { solve };\n",
        "utf-8"
      );

      // Set up a synthetic lab under repoRoot/labs/<labId>
      const labId = "LAB-PRG-T01-C01-88";
      const labDir = path.join(repoRoot, "labs", labId);
      fs.mkdirSync(path.join(labDir, "src"), { recursive: true });
      fs.mkdirSync(path.join(labDir, "tests"), { recursive: true });
      fs.writeFileSync(path.join(labDir, "src", "index.ts"), "export const x = 1;\n", "utf-8");
      fs.writeFileSync(
        path.join(labDir, "tests", "m1_basic.test.ts"),
        'test("basic milestone test", () => {});\n',
        "utf-8"
      );
      fs.writeFileSync(
        path.join(labDir, "lab.config.json"),
        JSON.stringify({
          labId,
          title: "Pilot Lab Path Test",
          chapterCode: "PRG-T01-C01",
          unitsUsed: ["PRG-T01-C01-U01"],
          milestones: [
            {
              id: "M1",
              title: "Milestone 1",
              goal: "Test pilot lab paths",
              mainFile: "src/index.ts",
              visibleTests: "tests/m1_*.test.ts",
            },
          ],
        }),
        "utf-8"
      );

      // In pilot mode (LEARNINGOS_PILOT = "1"):
      process.env.LEARNINGOS_PILOT = "1";

      const drillPilotRes = await drillGET(
        new NextRequest(`http://127.0.0.1:3000/api/drill?id=${encodeURIComponent(drillId)}`)
      );
      assert.equal(drillPilotRes.status, 200);
      const drillPilotDoc = (await drillPilotRes.json()) as {
        problems: Array<Record<string, unknown>>;
      };
      const q1Pilot = drillPilotDoc.problems[0];
      assert.equal(q1Pilot.workspaceDir, pilotWsDir);
      assert.equal(q1Pilot.workspaceFile, pilotWorkspaceFileRel);
      assert.equal(q1Pilot.vscodeFolderUrl, `vscode://file/${pilotWsDir}`);
      assert.ok(String(q1Pilot.vscodeUrl).includes("/pilot/workspace/"));

      const runPilotRes = await runTestsPOST(
        new NextRequest("http://127.0.0.1:3000/api/run-tests", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ drillId, problemId: "Q01" }),
        })
      );
      assert.equal(runPilotRes.status, 200);
      const runPilotReport = (await runPilotRes.json()) as { allPassed: boolean };
      assert.equal(
        runPilotReport.allPassed,
        true,
        "/api/run-tests in pilot mode must execute pilot/workspace code (which passes), not drills/workspace code (which returns 999)"
      );

      const labPilotRes = await labGET(
        new NextRequest(`http://127.0.0.1:3000/api/lab?id=${encodeURIComponent(labId)}`)
      );
      assert.equal(labPilotRes.status, 200);
      const labPilotDoc = (await labPilotRes.json()) as {
        workspaceDir: string;
        vscodeFolderUrl: string;
        milestones: Array<{ vscodeUrl: string | null }>;
      };
      const expectedPilotLabDir = path.join(repoRoot, "pilot", "labs", labId);
      assert.equal(labPilotDoc.workspaceDir, expectedPilotLabDir);
      assert.equal(labPilotDoc.vscodeFolderUrl, `vscode://file${expectedPilotLabDir}`);
      assert.equal(
        labPilotDoc.milestones[0].vscodeUrl,
        `vscode://file${path.join(expectedPilotLabDir, "src", "index.ts")}`
      );

      // In normal mode (LEARNINGOS_PILOT unset):
      delete process.env.LEARNINGOS_PILOT;

      const drillNormalRes = await drillGET(
        new NextRequest(`http://127.0.0.1:3000/api/drill?id=${encodeURIComponent(drillId)}`)
      );
      assert.equal(drillNormalRes.status, 200);
      const drillNormalDoc = (await drillNormalRes.json()) as {
        problems: Array<Record<string, unknown>>;
      };
      assert.equal(drillNormalDoc.problems[0].workspaceDir, wsDir);
      assert.equal(drillNormalDoc.problems[0].workspaceFile, workspaceFileRel);

      const runNormalRes = await runTestsPOST(
        new NextRequest("http://127.0.0.1:3000/api/run-tests", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ drillId, problemId: "Q01" }),
        })
      );
      assert.equal(runNormalRes.status, 200);
      const runNormalReport = (await runNormalRes.json()) as { allPassed: boolean };
      assert.equal(
        runNormalReport.allPassed,
        false,
        "/api/run-tests in normal mode must execute drills/workspace code (which returns 999 and fails)"
      );

      const labNormalRes = await labGET(
        new NextRequest(`http://127.0.0.1:3000/api/lab?id=${encodeURIComponent(labId)}`)
      );
      assert.equal(labNormalRes.status, 200);
      const labNormalDoc = (await labNormalRes.json()) as {
        workspaceDir: string;
        vscodeFolderUrl: string;
        milestones: Array<{ vscodeUrl: string | null }>;
      };
      assert.equal(labNormalDoc.workspaceDir, labDir);
      assert.equal(labNormalDoc.vscodeFolderUrl, `vscode://file${labDir}`);
      assert.equal(
        labNormalDoc.milestones[0].vscodeUrl,
        `vscode://file${path.join(labDir, "src", "index.ts")}`
      );
    }

    console.log("workspaceRoute tests passed (13 security & pilot-mode functional assertions)");
  } finally {
    if (prevRoot === undefined) delete process.env.LEARNINGOS_ROOT;
    else process.env.LEARNINGOS_ROOT = prevRoot;
    if (prevDrillsDir === undefined) delete process.env.DRILLS_DATA_DIR;
    else process.env.DRILLS_DATA_DIR = prevDrillsDir;
    if (prevPilot === undefined) delete process.env.LEARNINGOS_PILOT;
    else process.env.LEARNINGOS_PILOT = prevPilot;
    if (prevProgress === undefined) delete process.env.PROGRESS_DIR;
    else process.env.PROGRESS_DIR = prevProgress;
    fs.rmSync(outerDir, { recursive: true, force: true });
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
