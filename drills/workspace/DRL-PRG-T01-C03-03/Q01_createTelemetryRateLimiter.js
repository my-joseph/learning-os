function createTelemetryRateLimiter({ capacity, refillRate, initialTokens, now = Date.now }) {
  let tokens = initialTokens !== undefined ? initialTokens : capacity;
  let lastTimestamp = now();

  return {
    consume(cost = 1) {
      // TODO: implement continuous rate limiting with capacity clamping
      return false;
    }
  };
}

module.exports = { createTelemetryRateLimiter };
