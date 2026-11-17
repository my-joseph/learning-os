import assert from "node:assert/strict";
import test from "node:test";
const { CrawlerError, normalizeUrls } = await import(`${process.env.LAB_SRC_DIR || "../src"}/index.ts`);

test("M1 hidden: normalizeUrls does not mutate a frozen input array", () => {
  const frozen = Object.freeze([
    " https://docs.example.test/a ",
    "https://docs.example.test/b",
    "https://docs.example.test/a",
  ]);
  assert.deepEqual(normalizeUrls(frozen), [
    "https://docs.example.test/a",
    "https://docs.example.test/b",
  ]);
  assert.equal(frozen[0], " https://docs.example.test/a ");
});

test("M1 hidden: CrawlerError retains undefined cause cleanly and distinguishes codes", () => {
  const err = new CrawlerError("INVALID_CONFIG", "bad concurrency");
  assert.equal(err.code, "INVALID_CONFIG");
  assert.equal(err.cause, undefined);
  assert.equal(err instanceof Error, true);
});
