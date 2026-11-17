export type CrawlerErrorCode =
  | "INVALID_CONFIG"
  | "RATE_LIMIT_ABORTED"
  | "FETCH_FAILED"
  | "CRAWL_ABORTED";

export class CrawlerError extends Error {
  readonly code: CrawlerErrorCode;

  constructor(code: CrawlerErrorCode, message: string, options?: { readonly cause?: unknown }) {
    super(message, options);
    this.name = "CrawlerError";
    this.code = code;
  }
}

export interface FetchPageResult {
  readonly url: string;
  readonly status: number;
  readonly title: string;
}

export type PageFetcher = (url: string, signal?: AbortSignal) => Promise<FetchPageResult>;

export interface RateLimiterOptions {
  readonly maxPerWindow: number;
  readonly windowMs: number;
  readonly now?: () => number;
  readonly sleep?: (ms: number, signal?: AbortSignal) => Promise<void>;
}

export interface RateLimiter {
  acquire(signal?: AbortSignal): Promise<void>;
}

export interface CrawlerOptions {
  readonly concurrency: number;
  readonly rateLimiter?: RateLimiter;
}

export type CrawlOutcome =
  | {
      readonly url: string;
      readonly ok: true;
      readonly aborted: false;
      readonly page: FetchPageResult;
    }
  | {
      readonly url: string;
      readonly ok: false;
      readonly aborted: boolean;
      readonly error: Error;
    };

export interface CrawlReport {
  readonly results: readonly CrawlOutcome[];
  readonly succeeded: number;
  readonly failed: number;
  readonly aborted: boolean;
}

export interface PageCrawler {
  crawl(seeds: readonly string[], runOptions?: { readonly signal?: AbortSignal }): Promise<CrawlReport>;
}

export function normalizeUrls(_urls: readonly string[]): string[] {
  throw new Error("TODO [M1]: normalize and deduplicate URLs without mutating input");
}
