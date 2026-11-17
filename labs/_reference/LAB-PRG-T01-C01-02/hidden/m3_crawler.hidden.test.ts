import assert from "node:assert/strict";
import test from "node:test";
const { createPageCrawler } = await import(`${process.env.LAB_SRC_DIR || "../src"}/index.ts`);

test("M3 hidden: separate crawlers and sequential crawl calls do not share visited state", async () => {
  const fetchedByA: string[] = [];
  const fetchedByB: string[] = [];

  const crawlerA = createPageCrawler(
    async (url: string) => {
      fetchedByA.push(url);
      return { url, status: 200, title: "A" };
    },
    { concurrency: 2 },
  );
  const crawlerB = createPageCrawler(
    async (url: string) => {
      fetchedByB.push(url);
      return { url, status: 200, title: "B" };
    },
    { concurrency: 2 },
  );

  const r1 = await crawlerA.crawl(["https://docs.example.test/shared"]);
  const r2 = await crawlerB.crawl(["https://docs.example.test/shared"]);
  const r3 = await crawlerA.crawl(["https://docs.example.test/shared"]);

  assert.equal(r1.succeeded, 1);
  assert.equal(r2.succeeded, 1);
  assert.equal(r3.succeeded, 1);
  assert.equal(fetchedByA.length, 2);
  assert.equal(fetchedByB.length, 1);
});

test("M3 hidden: wraps non-Error rejections into Error instances", async () => {
  const crawler = createPageCrawler(
    async () => {
      return Promise.reject("network-down");
    },
    { concurrency: 1 },
  );
  const report = await crawler.crawl(["https://docs.example.test/down"]);
  assert.equal(report.failed, 1);
  assert.equal(report.results[0].ok, false);
  assert.equal(report.results[0].error instanceof Error, true);
  assert.match(report.results[0].error.message, /network-down/);
});
