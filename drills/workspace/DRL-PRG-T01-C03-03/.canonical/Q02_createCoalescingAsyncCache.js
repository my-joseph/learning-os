function createCoalescingAsyncCache(fetchFn) {
  const cache = new Map();
  const inFlight = new Map();

  return {
    async get(key) {
      if (cache.has(key)) {
        return cache.get(key);
      }
      if (inFlight.has(key)) {
        return inFlight.get(key);
      }

      const promise = (async () => {
        try {
          const data = await fetchFn(key);
          cache.set(key, data);
          return data;
        } finally {
          inFlight.delete(key);
        }
      })();

      inFlight.set(key, promise);
      return promise;
    }
  };
}

module.exports = { createCoalescingAsyncCache };
