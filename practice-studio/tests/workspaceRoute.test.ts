import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { NextRequest } from "next/server";
import { GET, POST, PUT } from "../src/app/api/workspace/route";

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

    // 12. Pilot mode scopes GET/PUT to pilot/workspace/<drillId>/
    {
      process.env.LEARNINGOS_PILOT = "1";
      const resPilotOk = await GET(makeGetReq({ file: pilotWorkspaceFileRel, drillId }));
      assert.equal(resPilotOk.status, 200, "GET pilot workspace file in pilot mode must return 200");
      const pilotJson = (await resPilotOk.json()) as Record<string, unknown>;
      assert.equal(pilotJson.content, "// pilot starter\n");

      const resNonPilotBlocked = await GET(makeGetReq({ file: workspaceFileRel, drillId }));
      assert.equal(
        resNonPilotBlocked.status,
        403,
        "GET drills/workspace file in pilot mode must return 403"
      );
    }

    console.log("workspaceRoute tests passed (12 security & functional assertions)");
  } finally {
    if (prevRoot === undefined) delete process.env.LEARNINGOS_ROOT;
    else process.env.LEARNINGOS_ROOT = prevRoot;
    if (prevDrillsDir === undefined) delete process.env.DRILLS_DATA_DIR;
    else process.env.DRILLS_DATA_DIR = prevDrillsDir;
    if (prevPilot === undefined) delete process.env.LEARNINGOS_PILOT;
    else process.env.LEARNINGOS_PILOT = prevPilot;
    fs.rmSync(outerDir, { recursive: true, force: true });
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
