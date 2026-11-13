function createTokenBucketLimiter({ capacity, refillRate, initialTokens }) {
  let tokens = initialTokens !== undefined ? initialTokens : capacity;
  let lastTimestamp = Date.now();

  return {
    consume(cost = 1) {
      const now = Date.now();
      const elapsedSec = (now - lastTimestamp) / 1000;
      tokens = Math.min(capacity, tokens + elapsedSec * refillRate);
      lastTimestamp = now;

      if (tokens >= cost) {
        tokens -= cost;
        return true;
      }
      return false;
    }
  };
}

module.exports = { createTokenBucketLimiter };
