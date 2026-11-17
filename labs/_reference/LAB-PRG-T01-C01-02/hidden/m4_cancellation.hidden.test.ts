import assert from "node:assert/strict";
import test from "node:test";
const { createPageCrawler, createRateLimiter } = await import(`${process.env.LAB_SRC_DIR || "../src"}/index.ts`);

test("M4 hidden: mid-flight abort stops queued fetches and preserves started outcome", async () => {
  const controller = new AbortController();
  const started: string[] = [];

  const crawler = createPageCrawler(
    async (url: string) => {
      started.push(url);
      if (url.endsWith("/first")) {
        controller.abort(new Error("stop queue"));
      }
      await Promise.resolve();
      return { url, status: 200, title: url };
    },
    { concurrency: 1 },
  );

  const report = await crawler.crawl(
    ["https://docs.example.test/first", "https://docs.example.test/second", "https://docs.example.test/third"],
    { signal: controller.signal },
  );

  assert.deepEqual(started, ["https://docs.example.test/first"]);
  assert.equal(report.aborted, true);
  assert.equal(report.results[0].ok, true);
  assert.equal(report.results[1].aborted, true);
  assert.equal(report.results[2].aborted, true);
});

test("M4 hidden: rateLimiter.acquire detaches abort listeners after settling", async () => {
  const controller = new AbortController();
  const signal = controller.signal;
  let activeListeners = 0;
  const origAdd = signal.addEventListener.bind(signal);
  const origRemove = signal.removeEventListener.bind(signal);

  signal.addEventListener = ((type: string, listener: EventListenerOrEventListenerObject, options?: boolean | AddEventListenerOptions) => {
    if (type === "abort") {
      activeListeners += 1;
    }
    return origAdd(type, listener, options);
  }) as typeof signal.addEventListener;

  signal.removeEventListener = ((type: string, listener: EventListenerOrEventListenerObject, options?: boolean | EventListenerOptions) => {
    if (type === "abort") {
      activeListeners = Math.max(0, activeListeners - 1);
    }
    return origRemove(type, listener, options);
  }) as typeof signal.removeEventListener;

  let clock = 0;
  const limiter = createRateLimiter({
    maxPerWindow: 1,
    windowMs: 50,
    now: () => clock,
    sleep: async (ms: number) => {
      await Promise.resolve();
      clock += ms;
    },
  });

  await limiter.acquire(signal);
  await limiter.acquire(signal);
  assert.equal(activeListeners, 0);
});
