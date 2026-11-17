import { CrawlerError, normalizeUrls } from "./contracts.ts";
import type {
  CrawlOutcome,
  CrawlReport,
  CrawlerOptions,
  PageCrawler,
  PageFetcher,
} from "./contracts.ts";

function isSignalAborted(signal?: AbortSignal): boolean {
  return signal?.aborted === true;
}

function toError(err: unknown): Error {
  return err instanceof Error ? err : new CrawlerError("FETCH_FAILED", String(err));
}

function makeCrawlAbortError(signal?: AbortSignal): CrawlerError {
  return new CrawlerError("CRAWL_ABORTED", "Crawl cancelled by AbortSignal", {
    cause: signal?.reason,
  });
}

function isAbortOutcomeError(err: unknown, signal?: AbortSignal): boolean {
  if (isSignalAborted(signal)) {
    return true;
  }
  return err instanceof CrawlerError && (err.code === "CRAWL_ABORTED" || err.code === "RATE_LIMIT_ABORTED");
}

async function fetchOneUrl(
  url: string,
  fetcher: PageFetcher,
  options: CrawlerOptions,
  signal?: AbortSignal,
): Promise<CrawlOutcome> {
  if (isSignalAborted(signal)) {
    return { url, ok: false, aborted: true, error: makeCrawlAbortError(signal) };
  }
  try {
    await options.rateLimiter?.acquire(signal);
    if (isSignalAborted(signal)) {
      return { url, ok: false, aborted: true, error: makeCrawlAbortError(signal) };
    }
    const page = await fetcher(url, signal);
    return { url, ok: true, aborted: false, page };
  } catch (err: unknown) {
    return {
      url,
      ok: false,
      aborted: isAbortOutcomeError(err, signal),
      error: toError(err),
    };
  }
}

function buildReport(
  urls: readonly string[],
  outcomes: Array<CrawlOutcome | undefined>,
  signal?: AbortSignal,
): CrawlReport {
  const filled: CrawlOutcome[] = urls.map((url, idx) => {
    const entry = outcomes[idx];
    return entry ?? { url, ok: false, aborted: true, error: makeCrawlAbortError(signal) };
  });
  const succeeded = filled.filter((item) => item.ok).length;
  const aborted = isSignalAborted(signal) || filled.some((item) => item.aborted);
  return { results: filled, succeeded, failed: filled.length - succeeded, aborted };
}

export function createPageCrawler(fetcher: PageFetcher, options: CrawlerOptions): PageCrawler {
  if (!Number.isInteger(options.concurrency) || options.concurrency <= 0) {
    throw new CrawlerError("INVALID_CONFIG", "concurrency must be a positive integer");
  }

  return {
    async crawl(seeds: readonly string[], runOptions?: { readonly signal?: AbortSignal }): Promise<CrawlReport> {
      const uniqueUrls = normalizeUrls(seeds);
      const signal = runOptions?.signal;
      const outcomes: Array<CrawlOutcome | undefined> = new Array<CrawlOutcome | undefined>(uniqueUrls.length);
      if (uniqueUrls.length === 0 || isSignalAborted(signal)) {
        return buildReport(uniqueUrls, outcomes, signal);
      }

      let cursor = 0;
      const workerCount = Math.min(options.concurrency, uniqueUrls.length);
      async function runWorker(): Promise<void> {
        while (cursor < uniqueUrls.length && !isSignalAborted(signal)) {
          const index = cursor;
          cursor += 1;
          outcomes[index] = await fetchOneUrl(uniqueUrls[index], fetcher, options, signal);
        }
      }

      await Promise.all(Array.from({ length: workerCount }, () => runWorker()));
      return buildReport(uniqueUrls, outcomes, signal);
    },
  };
}
