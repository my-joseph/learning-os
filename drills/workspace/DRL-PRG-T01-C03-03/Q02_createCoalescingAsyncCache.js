function createCoalescingAsyncCache(fetchFn) {
  const cache = new Map();

  return {
    async get(key) {
      if (cache.has(key)) {
        return cache.get(key);
      }
      // BUG: Directly invokes fetchFn without tracking in-flight promise!
      const data = await fetchFn(key);
      cache.set(key, data);
      return data;
    }
  };
}

module.exports = { createCoalescingAsyncCache };
