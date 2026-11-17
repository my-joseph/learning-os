import assert from "node:assert/strict";
import test from "node:test";
const { CrawlerError, createRateLimiter } = await import(`${process.env.LAB_SRC_DIR || "../src"}/index.ts`);

test("createRateLimiter rejects invalid maxPerWindow or windowMs", () => {
  assert.throws(
    () => createRateLimiter({ maxPerWindow: 0, windowMs: 100 }),
    (err: unknown) => err instanceof CrawlerError && err.code === "INVALID_CONFIG",
  );
  assert.throws(
    () => createRateLimiter({ maxPerWindow: 2, windowMs: -10 }),
    (err: unknown) => err instanceof CrawlerError && err.code === "INVALID_CONFIG",
  );
});

test("createRateLimiter allows up to maxPerWindow calls before sleeping for the next window", async () => {
  let currentTime = 1000;
  const sleeps: number[] = [];
  const limiter = createRateLimiter({
    maxPerWindow: 2,
    windowMs: 100,
    now: () => currentTime,
    sleep: async (ms: number) => {
      sleeps.push(ms);
      currentTime += ms;
    },
  });

  await limiter.acquire();
  await limiter.acquire();
  assert.deepEqual(sleeps, []);

  await limiter.acquire();
  assert.deepEqual(sleeps, [100]);
  assert.equal(currentTime, 1100);
});
