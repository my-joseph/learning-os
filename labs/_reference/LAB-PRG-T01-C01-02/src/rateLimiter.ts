import { CrawlerError } from "./contracts.ts";
import type { RateLimiter, RateLimiterOptions } from "./contracts.ts";

interface LimiterState {
  readonly maxPerWindow: number;
  readonly windowMs: number;
  readonly now: () => number;
  readonly sleep: (ms: number, signal?: AbortSignal) => Promise<void>;
  readonly timestamps: number[];
}

function isSignalAborted(signal?: AbortSignal): boolean {
  return signal?.aborted === true;
}

function makeAbortError(signal: AbortSignal): CrawlerError {
  return new CrawlerError("RATE_LIMIT_ABORTED", "Rate limit acquisition aborted", {
    cause: signal.reason,
  });
}

function defaultSleep(ms: number, signal?: AbortSignal): Promise<void> {
  if (signal !== undefined && isSignalAborted(signal)) {
    return Promise.reject(makeAbortError(signal));
  }
  return new Promise<void>((resolve, reject) => {
    const onAbort = (): void => {
      clearTimeout(timerId);
      signal?.removeEventListener("abort", onAbort);
      if (signal !== undefined) {
        reject(makeAbortError(signal));
      }
    };
    const timerId = setTimeout(() => {
      signal?.removeEventListener("abort", onAbort);
      resolve();
    }, ms);
    signal?.addEventListener("abort", onAbort, { once: true });
  });
}

async function raceWithAbort<T>(promise: Promise<T>, signal?: AbortSignal): Promise<T> {
  if (signal === undefined) {
    return promise;
  }
  if (isSignalAborted(signal)) {
    throw makeAbortError(signal);
  }
  let onAbort: (() => void) | undefined;
  const abortPromise = new Promise<never>((_resolve, reject) => {
    onAbort = (): void => {
      reject(makeAbortError(signal));
    };
    signal.addEventListener("abort", onAbort, { once: true });
  });
  try {
    return await Promise.race([promise, abortPromise]);
  } finally {
    if (onAbort !== undefined) {
      signal.removeEventListener("abort", onAbort);
    }
  }
}

function pruneExpired(timestamps: number[], currentTime: number, windowMs: number): void {
  const cutoff = currentTime - windowMs;
  while (timestamps.length > 0 && timestamps[0] <= cutoff) {
    timestamps.shift();
  }
}

async function waitForSlot(state: LimiterState, signal?: AbortSignal): Promise<void> {
  if (signal !== undefined && isSignalAborted(signal)) {
    throw makeAbortError(signal);
  }
  pruneExpired(state.timestamps, state.now(), state.windowMs);
  while (state.timestamps.length >= state.maxPerWindow) {
    const waitMs = Math.max(1, state.timestamps[0] + state.windowMs - state.now());
    await raceWithAbort(state.sleep(waitMs, signal), signal);
    if (signal !== undefined && isSignalAborted(signal)) {
      throw makeAbortError(signal);
    }
    pruneExpired(state.timestamps, state.now(), state.windowMs);
  }
  state.timestamps.push(state.now());
}

export function createRateLimiter(options: RateLimiterOptions): RateLimiter {
  if (!Number.isInteger(options.maxPerWindow) || options.maxPerWindow <= 0) {
    throw new CrawlerError("INVALID_CONFIG", "maxPerWindow must be a positive integer");
  }
  if (!Number.isFinite(options.windowMs) || options.windowMs <= 0) {
    throw new CrawlerError("INVALID_CONFIG", "windowMs must be a positive finite number");
  }

  const state: LimiterState = {
    maxPerWindow: options.maxPerWindow,
    windowMs: options.windowMs,
    now: options.now ?? ((): number => Date.now()),
    sleep: options.sleep ?? defaultSleep,
    timestamps: [],
  };
  let waitChain: Promise<void> = Promise.resolve();

  return {
    async acquire(signal?: AbortSignal): Promise<void> {
      if (signal !== undefined && isSignalAborted(signal)) {
        throw makeAbortError(signal);
      }
      const previous = waitChain;
      let release: (() => void) | undefined;
      waitChain = new Promise<void>((resolve) => {
        release = resolve;
      });
      try {
        await raceWithAbort(previous, signal);
        await waitForSlot(state, signal);
      } finally {
        release?.();
      }
    },
  };
}
