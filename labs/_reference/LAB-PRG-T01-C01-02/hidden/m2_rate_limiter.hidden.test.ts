import assert from "node:assert/strict";
import test from "node:test";
const { createRateLimiter } = await import(`${process.env.LAB_SRC_DIR || "../src"}/index.ts`);

test("M2 hidden: separate rateLimiter instances keep completely isolated windows", async () => {
  let timeA = 0;
  let timeB = 0;
  const sleepsA: number[] = [];
  const sleepsB: number[] = [];

  const limiterA = createRateLimiter({
    maxPerWindow: 1,
    windowMs: 100,
    now: () => timeA,
    sleep: async (ms: number) => {
      sleepsA.push(ms);
      timeA += ms;
    },
  });
  const limiterB = createRateLimiter({
    maxPerWindow: 1,
    windowMs: 100,
    now: () => timeB,
    sleep: async (ms: number) => {
      sleepsB.push(ms);
      timeB += ms;
    },
  });

  await limiterA.acquire();
  await limiterB.acquire();
  assert.deepEqual(sleepsA, []);
  assert.deepEqual(sleepsB, []);

  await limiterA.acquire();
  assert.deepEqual(sleepsA, [100]);
  assert.deepEqual(sleepsB, []);
});

test("M2 hidden: concurrent acquire calls serialize and respect maxPerWindow", async () => {
  let clock = 0;
  const acquiredAt: number[] = [];
  const limiter = createRateLimiter({
    maxPerWindow: 2,
    windowMs: 50,
    now: () => clock,
    sleep: async (ms: number) => {
      await Promise.resolve();
      clock += ms;
    },
  });

  await Promise.all([
    limiter.acquire().then(() => acquiredAt.push(clock)),
    limiter.acquire().then(() => acquiredAt.push(clock)),
    limiter.acquire().then(() => acquiredAt.push(clock)),
    limiter.acquire().then(() => acquiredAt.push(clock)),
  ]);

  assert.deepEqual(acquiredAt, [0, 0, 50, 50]);
});
