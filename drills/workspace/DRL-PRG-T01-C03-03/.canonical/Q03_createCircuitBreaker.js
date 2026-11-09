function createCircuitBreaker(asyncOperation, options = {}) {
  const failureThreshold = options.failureThreshold !== undefined ? options.failureThreshold : 3;
  const resetTimeoutMs = options.resetTimeoutMs !== undefined ? options.resetTimeoutMs : 50;
  const now = options.now || Date.now;

  let state = 'CLOSED';
  let failureCount = 0;
  let openedAt = 0;
  let probing = false;

  return {
    async execute(...args) {
      const currentTime = now();

      if (state === 'OPEN') {
        if (currentTime - openedAt >= resetTimeoutMs) {
          state = 'HALF_OPEN';
        } else {
          throw new Error('CIRCUIT_BREAKER_OPEN');
        }
      }

      if (state === 'HALF_OPEN') {
        if (probing) {
          throw new Error('CIRCUIT_BREAKER_OPEN');
        }
        probing = true;
      }

      try {
        const result = await asyncOperation(...args);
        state = 'CLOSED';
        failureCount = 0;
        probing = false;
        return result;
      } catch (err) {
        failureCount++;
        if (state === 'HALF_OPEN' || failureCount >= failureThreshold) {
          state = 'OPEN';
          openedAt = now();
        }
        probing = false;
        throw err;
      }
    },
    getState() {
      if (state === 'OPEN' && now() - openedAt >= resetTimeoutMs) {
        return 'HALF_OPEN';
      }
      return state;
    }
  };
}

module.exports = { createCircuitBreaker };
