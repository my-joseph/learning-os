class AsyncCache {
  constructor(ttlMs = 1000) {
    this.ttlMs = ttlMs;
    this.cache = new Map();
    this.inFlight = new Map();
  }

  async getOrFetch(key, fetcher) {
    const now = Date.now();
    const existing = this.cache.get(key);

    // 1. Cache Hit: Return defensive copy
    if (existing && existing.expiry > now) {
      return JSON.parse(JSON.stringify(existing.value));
    }

    // 2. In-Flight Hit: Wait for existing active fetch
    if (this.inFlight.has(key)) {
      const val = await this.inFlight.get(key);
      return JSON.parse(JSON.stringify(val));
    }

    // 3. Cache Miss: Execute single fetch and broadcast
    const fetchPromise = (async () => {
      try {
        const val = await fetcher(key);
        this.cache.set(key, { value: val, expiry: Date.now() + this.ttlMs });
        return val;
      } finally {
        this.inFlight.delete(key);
      }
    })();

    this.inFlight.set(key, fetchPromise);
    const res = await fetchPromise;
    return JSON.parse(JSON.stringify(res));
  }

  invalidate(key) {
    this.cache.delete(key);
    this.inFlight.delete(key);
  }

  clear() {
    this.cache.clear();
    this.inFlight.clear();
  }
}

module.exports = { AsyncCache };
