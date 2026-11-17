import assert from "node:assert/strict";
import test from "node:test";
const { CrawlerError, createPageCrawler, createRateLimiter } = await import(
  `${process.env.LAB_SRC_DIR || "../src"}/index.ts`
);

test("pre-aborted signal prevents fetching and marks all seeds aborted", async () => {
  const controller = new AbortController();
  controller.abort(new Error("user cancelled"));
  let calls = 0;

  const crawler = createPageCrawler(
    async (url: string) => {
      calls += 1;
      return { url, status: 200, title: "ok" };
    },
    { concurrency: 2 },
  );

  const report = await crawler.crawl(
    ["https://docs.example.test/a", "https://docs.example.test/b"],
    { signal: controller.signal },
  );
  assert.equal(calls, 0);
  assert.equal(report.aborted, true);
  assert.equal(report.failed, 2);
  assert.equal(report.results.every((r: { aborted: boolean }) => r.aborted), true);
});

test("rateLimiter.acquire rejects when aborted while sleeping", async () => {
  const controller = new AbortController();
  let clock = 0;
  const limiter = createRateLimiter({
    maxPerWindow: 1,
    windowMs: 100,
    now: () => clock,
    sleep: async () => {
      await new Promise((resolve) => setTimeout(resolve, 25));
      clock += 100;
    },
  });

  await limiter.acquire();
  setTimeout(() => controller.abort(new Error("timeout")), 5);
  await assert.rejects(
    () => limiter.acquire(controller.signal),
    (err: unknown) => err instanceof CrawlerError && err.code === "RATE_LIMIT_ABORTED",
  );
});
