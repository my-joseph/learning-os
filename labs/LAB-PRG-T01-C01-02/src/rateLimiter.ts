import type { RateLimiter, RateLimiterOptions } from "./contracts.ts";

export function createRateLimiter(_options: RateLimiterOptions): RateLimiter {
  throw new Error("TODO [M2]: implement closure-scoped sliding-window rate limiter");
}
