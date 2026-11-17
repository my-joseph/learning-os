import assert from "node:assert/strict";
import test from "node:test";
const { createTreeIndex } = await import(`${process.env.LAB_SRC_DIR || "../src"}/index.ts`);

function deepFreeze<T>(obj: T): T {
  if (obj && typeof obj === "object") {
    Object.freeze(obj);
    for (const val of Object.values(obj as Record<string, unknown>)) {
      deepFreeze(val);
    }
  }
  return obj;
}

test("TreeIndex findFirstByTag picks shallowest BFS node and never mutates frozen trees", () => {
  const empty = createTreeIndex<number>(null);
  assert.equal(empty.findById("any"), null);
  assert.equal(empty.findFirstByTag("any"), null);
  assert.deepEqual(empty.collectPreorderIds(), []);
  assert.equal(empty.pathToId("any"), null);

  const tree = deepFreeze({
    id: "root",
    label: "Root",
    tags: ["top"],
    data: 0,
    children: [
      {
        id: "left",
        label: "Left",
        tags: [],
        data: 1,
        children: [
          {
            id: "left-deep",
            label: "Left Deep",
            tags: ["promo"],
            data: 2,
            children: [],
          },
        ],
      },
      {
        id: "right",
        label: "Right",
        tags: ["promo"],
        data: 3,
        children: [],
      },
    ],
  });

  const index = createTreeIndex(tree);
  assert.equal(index.findFirstByTag("promo")?.id, "right");
  assert.equal(index.findById("left-deep")?.data, 2);
  assert.deepEqual(index.collectPreorderIds(), ["root", "left", "left-deep", "right"]);
  assert.deepEqual(index.pathToId("right"), ["root", "right"]);
  assert.equal(index.pathToId("missing"), null);
});
