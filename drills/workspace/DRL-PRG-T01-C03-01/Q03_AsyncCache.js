/**
 * In-Memory Async Cache with TTL.
 * 
 * KNOWN DEFECTS TO TRIAGE & FIX:
 * 1. Cache Stampede: Simultaneous concurrent requests for the same key fire multiple fetches
 *    instead of sharing a single in-flight Promise.
 * 2. State Mutation Leak: Callers mutating returned cache objects corrupt the internal cache.
 */
class AsyncCache {
  constructor(ttlMs = 1000) {
    this.ttlMs = ttlMs;
    this.cache = new Map();
  }

  async getOrFetch(key, fetcher) {
    const now = Date.now();
    const existing = this.cache.get(key);

    if (existing && existing.expiry > now) {
      // BUG: Returns raw reference! Caller mutations corrupt internal store
      return existing.value;
    }

    // BUG: Missing in-flight Promise deduplication! Concurrent calls execute fetcher multiple times
    const val = await fetcher(key);
    this.cache.set(key, { value: val, expiry: Date.now() + this.ttlMs });
    return val;
  }

  invalidate(key) {
    this.cache.delete(key);
  }

  clear() {
    this.cache.clear();
  }
}

module.exports = { AsyncCache };
