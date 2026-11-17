import assert from "node:assert/strict";
import test from "node:test";
const { CrawlerError, normalizeUrls } = await import(`${process.env.LAB_SRC_DIR || "../src"}/index.ts`);

test("CrawlerError preserves code, message, and cause while staying an Error", () => {
  const rootCause = new TypeError("socket closed");
  const err = new CrawlerError("FETCH_FAILED", "Failed to download docs page", { cause: rootCause });
  assert.ok(err instanceof Error);
  assert.ok(err instanceof CrawlerError);
  assert.equal(err.name, "CrawlerError");
  assert.equal(err.code, "FETCH_FAILED");
  assert.equal(err.message, "Failed to download docs page");
  assert.equal(err.cause, rootCause);
});

test("normalizeUrls trims whitespace, drops blanks, and deduplicates in order", () => {
  const input = [
    "  https://docs.example.test/intro ",
    "",
    "   ",
    "https://docs.example.test/api",
    "https://docs.example.test/intro",
    "https://docs.example.test/guides/auth",
  ];
  const snapshot = [...input];
  const normalized = normalizeUrls(input);
  assert.deepEqual(normalized, [
    "https://docs.example.test/intro",
    "https://docs.example.test/api",
    "https://docs.example.test/guides/auth",
  ]);
  assert.deepEqual(input, snapshot);
});
