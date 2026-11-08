function memoize(fn, resolver) {
  const cache = new Map();

  function memoized(...args) {
    const key = typeof resolver === 'function' ? resolver.apply(this, args) : args[0];
    if (cache.has(key)) {
      return cache.get(key);
    }
    const result = fn.apply(this, args);
    cache.set(key, result);
    return result;
  }

  memoized.cache = cache;
  return memoized;
}

module.exports = { memoize };
