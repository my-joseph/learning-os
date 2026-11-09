function createTelemetryRateLimiter({ capacity, refillRate, initialTokens }) {
  let tokens = initialTokens !== undefined ? initialTokens : capacity;
  let lastTimestamp = Date.now();

  return {
    consume(cost = 1) {
      // TODO: calculate elapsed time, clamp tokens to capacity, and deduct cost
      return false;
    }
  };
}

module.exports = { createTelemetryRateLimiter };
