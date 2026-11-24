import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { NextRequest } from "next/server";
import { DELETE as drillDELETE, GET as drillGET } from "../src/app/api/drill/route";
import { GET as drillsGET } from "../src/app/api/drills/route";
import { POST as saveStatePOST } from "../src/app/api/save-state/route";
import { POST as syncNotionPOST } from "../src/app/api/sync-notion/route";
import { setNotionDrillSyncSpawnerForTests } from "../src/lib/notionSyncRunner";

function deleteReq(id?: string): NextRequest {
  return new NextRequest(`http://127.0.0.1:3000/api/drill${id ? `?id=${encodeURIComponent(id)}` : ""}`, {
    method: "DELETE",
  });
}

async function main() {
  const tmpRoot = fs.mkdtempSync(path.join(os.tmpdir(), "learningos-drill-delete-"));
  const dataDir = path.join(tmpRoot, "drills", "data");
  const progressDir = path.join(tmpRoot, "progress");
  const workspaceDir = path.join(tmpRoot, "drills", "workspace", "DRL-MTH-T01-C01-01");
  const drillId = "DRL-MTH-T01-C01-01";
  const siblingId = "DRL-PRG-T02-C03-02";
  const linkedId = "DRL-MTH-T01-C02-03";
  const makeDrill = (id: string, subject: string) => ({
    drillId: id,
    subject,
    unitCode: subject === "PRG" ? "PRG-T02-C03-U01" : "MTH-T01-C01-U01",
    problems: [{ id: "Q01", prompt: "Synthetic fixture", answerPlain: "1" }],
  });
  const writeDrill = (id: string, subject: string) => {
    const unitDir = path.join(dataDir, makeDrill(id, subject).unitCode);
    fs.mkdirSync(unitDir, { recursive: true });
    fs.writeFileSync(path.join(unitDir, `${id}.json`), JSON.stringify(makeDrill(id, subject)));
    return path.join(unitDir, `${id}.json`);
  };
  const targetPath = writeDrill(drillId, "MATH");
  const siblingPath = writeDrill(siblingId, "PRG");
  const externalTarget = path.join(tmpRoot, "outside-drill-data.json");
  fs.writeFileSync(
    externalTarget,
    JSON.stringify({ ...makeDrill(linkedId, "MATH"), unitCode: "MTH-T01-C02-U01" })
  );
  fs.mkdirSync(progressDir, { recursive: true });
  const progressPath = path.join(progressDir, `${drillId}.json`);
  fs.writeFileSync(progressPath, JSON.stringify({ drillId, learnerNote: "retained" }));
  fs.mkdirSync(workspaceDir, { recursive: true });
  const workspaceFile = path.join(workspaceDir, "Q01.js");
  fs.writeFileSync(workspaceFile, "// retained workspace fixture");
  const labDir = path.join(tmpRoot, "labs", "LAB-PRG-T01-C01-01");
  fs.mkdirSync(labDir, { recursive: true });
  const labFile = path.join(labDir, "lab.config.json");
  fs.writeFileSync(labFile, "{}\n");

  const prior = {
    root: process.env.LEARNINGOS_ROOT,
    drills: process.env.DRILLS_DATA_DIR,
    progress: process.env.PROGRESS_DIR,
    pilot: process.env.LEARNINGOS_PILOT,
  };
  process.env.LEARNINGOS_ROOT = tmpRoot;
  process.env.DRILLS_DATA_DIR = dataDir;
  process.env.PROGRESS_DIR = progressDir;
  delete process.env.LEARNINGOS_PILOT;
  setNotionDrillSyncSpawnerForTests(async () => assert.fail("Deleted drill must never start Notion sync"));

  try {
    // Delete an inactive drill by its canonical ID and verify the response.
    const deleted = await drillDELETE(deleteReq(drillId));
    assert.equal(deleted.status, 200);
    assert.deepEqual(await deleted.json(), { ok: true, deleted: true, drillId });
    assert.equal(fs.existsSync(targetPath), false);

    // A repeat is safe and does not affect the sibling drill or retained records.
    const repeated = await drillDELETE(deleteReq(drillId));
    assert.equal(repeated.status, 404);
    assert.equal(fs.existsSync(siblingPath), true);
    assert.equal(fs.existsSync(progressPath), true);
    assert.equal(fs.existsSync(workspaceFile), true);
    assert.equal(fs.existsSync(labFile), true);
    const listRes = await drillsGET();
    const listed = (await listRes.json()).drills as Array<{ drillId: string }>;
    assert.deepEqual(listed.map((drill) => drill.drillId), [siblingId]);
    const direct = await drillGET(
      new NextRequest(`http://127.0.0.1:3000/api/drill?id=${encodeURIComponent(drillId)}`)
    );
    assert.equal(direct.status, 404);

    // Refuse symlinks and leave their targets untouched.
    const linkedDir = path.join(dataDir, "MTH-T01-C02-U01");
    fs.mkdirSync(linkedDir, { recursive: true });
    const linkedPath = path.join(linkedDir, `${linkedId}.json`);
    fs.symlinkSync(externalTarget, linkedPath);
    assert.equal((await drillDELETE(deleteReq(linkedId))).status, 404);
    assert.equal(fs.existsSync(linkedPath), true);
    assert.equal((await drillGET(new NextRequest(
      `http://127.0.0.1:3000/api/drill?id=${linkedId}`
    ))).status, 404);
    assert.deepEqual((await (await drillsGET()).json()).drills.map(
      (drill: { drillId: string }) => drill.drillId
    ), [siblingId]);
    assert.equal(fs.existsSync(externalTarget), true);

    // Refuse to choose between duplicate canonical IDs in separate unit folders.
    const duplicatePath = path.join(dataDir, "PRG-T02-C03-U02", `${siblingId}.json`);
    fs.mkdirSync(path.dirname(duplicatePath), { recursive: true });
    fs.writeFileSync(
      duplicatePath,
      JSON.stringify({ ...makeDrill(siblingId, "PRG"), unitCode: "PRG-T02-C03-U02" })
    );
    assert.equal((await drillDELETE(deleteReq(siblingId))).status, 404);
    assert.equal(fs.existsSync(siblingPath), true);
    assert.equal(fs.existsSync(duplicatePath), true);

    const staleSave = await saveStatePOST(
      new NextRequest("http://127.0.0.1:3000/api/save-state", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ drillId, unitCode: "MTH-T01-C01-U01", problems: [] }),
      })
    );
    assert.equal(staleSave.status, 404);
    const retainedProgress = fs.readFileSync(progressPath, "utf-8");
    const syncDeleted = () => syncNotionPOST(new NextRequest("http://127.0.0.1:3000/api/sync-notion", {
      method: "POST",
      body: JSON.stringify({ drillId, unitCode: "MTH-T01-C01-U01" }),
    }));
    assert.equal((await syncDeleted()).status, 404);
    assert.equal(fs.readFileSync(progressPath, "utf-8"), retainedProgress);
    fs.unlinkSync(progressPath);
    assert.equal((await syncDeleted()).status, 404);
    assert.equal(fs.existsSync(progressPath), false);

    for (const invalidId of ["", "drL-MTH-T01-C01-01", "LAB-PRG-T01-C01-01", "../escape"]) {
      const response = await drillDELETE(deleteReq(invalidId));
      assert.equal(response.status, 400);
    }
    assert.equal((await drillDELETE(deleteReq())).status, 400);

    // A regular file cannot serve as a drill data root.
    const invalidRoot = path.join(tmpRoot, "not-a-directory");
    fs.writeFileSync(invalidRoot, "fixture");
    process.env.DRILLS_DATA_DIR = invalidRoot;
    const failed = await drillDELETE(deleteReq(siblingId));
    assert.equal(failed.status, 404);
    assert.deepEqual(await failed.json(), { ok: false, error: "Drill not found" });
    assert.equal(fs.existsSync(siblingPath), true);
  } finally {
    setNotionDrillSyncSpawnerForTests(null);
    if (prior.root === undefined) delete process.env.LEARNINGOS_ROOT;
    else process.env.LEARNINGOS_ROOT = prior.root;
    if (prior.drills === undefined) delete process.env.DRILLS_DATA_DIR;
    else process.env.DRILLS_DATA_DIR = prior.drills;
    if (prior.progress === undefined) delete process.env.PROGRESS_DIR;
    else process.env.PROGRESS_DIR = prior.progress;
    if (prior.pilot === undefined) delete process.env.LEARNINGOS_PILOT;
    else process.env.LEARNINGOS_PILOT = prior.pilot;
    fs.rmSync(tmpRoot, { recursive: true, force: true });
  }
}

void main();
