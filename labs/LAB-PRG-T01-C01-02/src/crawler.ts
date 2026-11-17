import type { CrawlerOptions, PageCrawler, PageFetcher } from "./contracts.ts";

export function createPageCrawler(_fetcher: PageFetcher, _options: CrawlerOptions): PageCrawler {
  throw new Error("TODO [M3]: implement bounded concurrent page crawler");
}
