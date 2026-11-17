import assert from "node:assert/strict";
import test from "node:test";
const { createTreeIndex } = await import(`${process.env.LAB_SRC_DIR || "../src"}/index.ts`);

const catalogTree = {
  id: "root",
  label: "Catalog",
  tags: ["top"],
  data: 0,
  children: [
    {
      id: "books",
      label: "Books",
      tags: ["media"],
      data: 10,
      children: [
        { id: "sci-fi", label: "Sci-Fi", tags: ["featured"], data: 4, children: [] },
      ],
    },
    {
      id: "audio",
      label: "Audio",
      tags: ["featured", "media"],
      data: 8,
      children: [],
    },
  ],
};

test("createTreeIndex finds by DFS id, BFS shallowest tag, preorder ids, and path", () => {
  const index = createTreeIndex(catalogTree);
  assert.deepEqual(index.collectPreorderIds(), ["root", "books", "sci-fi", "audio"]);
  assert.equal(index.findById("sci-fi")?.label, "Sci-Fi");
  assert.equal(index.findById("missing"), null);
  assert.equal(index.findFirstByTag("featured")?.id, "audio");
  assert.deepEqual(index.pathToId("sci-fi"), ["root", "books", "sci-fi"]);
  assert.equal(index.pathToId("missing"), null);
});

test("createTreeIndex handles null root cleanly", () => {
  const empty = createTreeIndex(null);
  assert.deepEqual(empty.collectPreorderIds(), []);
  assert.equal(empty.findById("root"), null);
  assert.equal(empty.findFirstByTag("featured"), null);
  assert.equal(empty.pathToId("root"), null);
});
