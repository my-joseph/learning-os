function createTelemetryRateLimiter({ capacity, refillRate, initialTokens, now = Date.now }) {
  let tokens = initialTokens !== undefined ? initialTokens : capacity;
  let lastTimestamp = now();

  return {
    consume(cost = 1) {
      const currentTime = now();
      const elapsedSec = (currentTime - lastTimestamp) / 1000;
      tokens = Math.min(capacity, tokens + elapsedSec * refillRate);
      lastTimestamp = currentTime;

      if (tokens >= cost) {
        tokens -= cost;
        return true;
      }
      return false;
    }
  };
}

module.exports = { createTelemetryRateLimiter };
