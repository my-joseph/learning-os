# LAB-PRG-T01-C01-02 — Rate-Limited Web Page Fetcher

## Scenario

Build an isolated, rate-limited web page fetcher for a documentation indexing service. Each rate limiter and crawler instance must own its own quota, deduplication, and cancellation state while bounding concurrency, preserving error causes, and cleaning up abort listeners.

## Milestones

### M1 — Contracts, Errors & URL Normalization

Define typed crawler contracts, a `CrawlerError` subclass that preserves error `code` and `cause`, and `normalizeUrls(urls)` that trims whitespace, skips empty entries, and deduplicates URLs in first-seen order without mutating the input array.

Run this milestone's visible checks with `npm run test:m1` and all checks with `npm run check:m1`.

### M2 — Closure-Scoped Rate Limiter

Implement `createRateLimiter(options)` enforcing at most `maxPerWindow` acquisitions within any sliding `windowMs` interval using injectable `now` and `sleep` functions. Each created rate limiter must keep its timing window strictly isolated from other instances and reject non-positive `maxPerWindow` or `windowMs` with `CrawlerError` (`"INVALID_CONFIG"`).

Run this milestone's visible checks with `npm run test:m2` and all checks with `npm run check:m2`.

### M3 — Bounded Concurrent Page Crawler

Implement `createPageCrawler(fetcher, options)` returning `{ crawl(seeds, runOptions?) }`. Deduplicate URLs per `crawl()` call, enforce `concurrency` and optional `rateLimiter`, preserve input order in `CrawlReport.results`, and record per-URL failures as `{ url, ok: false, aborted: false, error }` without halting sibling fetches.

Run this milestone's visible checks with `npm run test:m3` and all checks with `npm run check:m3`.

### M4 — `AbortSignal` Cancellation & Listener Cleanup

Observe an optional `AbortSignal` in both `rateLimiter.acquire(signal)` and `crawler.crawl(seeds, { signal })`. Never invoke `fetcher` for queued URLs after cancellation, mark skipped/aborted URLs with `aborted: true`, preserve results for already-started fetches, and always detach any registered `abort` event listener when operations settle.

Run this milestone's visible checks with `npm run test:m4` and all checks with `npm run check:m4`.

## Commands

- `npm test` runs all visible milestone tests.
- `npm run check` runs tests, lint, and typecheck.
- `npm run test:m1` / `npm run check:m1` run one milestone; use `m2`, `m3`, or `m4` for the others.
- `npm run review -- m1` prints the review request for the milestone.
- Ask Claude Code: `ตรวจโค้ด LAB-PRG-T01-C01-02 M1` (replace `M1` with the milestone being reviewed).
