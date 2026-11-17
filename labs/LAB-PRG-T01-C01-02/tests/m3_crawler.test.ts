import assert from "node:assert/strict";
import test from "node:test";
const { CrawlerError, createPageCrawler, createRateLimiter } = await import(
  `${process.env.LAB_SRC_DIR || "../src"}/index.ts`
);

test("createPageCrawler rejects non-positive concurrency", () => {
  const fetcher = async (url: string) => ({ url, status: 200, title: "ok" });
  assert.throws(
    () => createPageCrawler(fetcher, { concurrency: 0 }),
    (err: unknown) => err instanceof CrawlerError && err.code === "INVALID_CONFIG",
  );
});

test("createPageCrawler bounds concurrency, deduplicates seeds, and preserves order and errors", async () => {
  let active = 0;
  let peak = 0;
  const seenUrls: string[] = [];

  const crawler = createPageCrawler(
    async (url: string) => {
      seenUrls.push(url);
      active += 1;
      peak = Math.max(peak, active);
      await Promise.resolve();
      active -= 1;
      if (url.endsWith("/broken")) {
        throw new Error("502 Bad Gateway");
      }
      return { url, status: 200, title: `Title for ${url}` };
    },
    { concurrency: 2 },
  );

  const report = await crawler.crawl([
    " https://docs.example.test/start ",
    "https://docs.example.test/broken",
    "https://docs.example.test/start",
    "https://docs.example.test/end",
  ]);

  assert.equal(peak <= 2, true);
  assert.equal(peak, 2);
  assert.equal(seenUrls.length, 3);
  assert.equal(report.succeeded, 2);
  assert.equal(report.failed, 1);
  assert.equal(report.aborted, false);
  assert.deepEqual(
    report.results.map((r: { url: string; ok: boolean }) => [r.url, r.ok]),
    [
      ["https://docs.example.test/start", true],
      ["https://docs.example.test/broken", false],
      ["https://docs.example.test/end", true],
    ],
  );
  const failedItem = report.results[1];
  assert.equal(failedItem.ok, false);
  assert.equal(failedItem.error.message, "502 Bad Gateway");
});

test("createPageCrawler integrates with an instance rate limiter", async () => {
  let clock = 0;
  const sleeps: number[] = [];
  const limiter = createRateLimiter({
    maxPerWindow: 1,
    windowMs: 50,
    now: () => clock,
    sleep: async (ms: number) => {
      sleeps.push(ms);
      clock += ms;
    },
  });
  const crawler = createPageCrawler(
    async (url: string) => ({ url, status: 200, title: url }),
    { concurrency: 2, rateLimiter: limiter },
  );
  const report = await crawler.crawl([
    "https://docs.example.test/p1",
    "https://docs.example.test/p2",
    "https://docs.example.test/p3",
  ]);
  assert.equal(report.succeeded, 3);
  assert.deepEqual(sleeps, [50, 50]);
});
