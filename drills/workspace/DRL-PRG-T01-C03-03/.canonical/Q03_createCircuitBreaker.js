function createCircuitBreaker(asyncOperation, options = {}) {
  const failureThreshold = options.failureThreshold !== undefined ? options.failureThreshold : 3;
  const resetTimeoutMs = options.resetTimeoutMs !== undefined ? options.resetTimeoutMs : 50;

  let state = 'CLOSED';
  let failureCount = 0;
  let openedAt = 0;

  return {
    async execute(...args) {
      const now = Date.now();

      if (state === 'OPEN') {
        if (now - openedAt >= resetTimeoutMs) {
          state = 'HALF_OPEN';
        } else {
          throw new Error('CIRCUIT_BREAKER_OPEN');
        }
      }

      try {
        const result = await asyncOperation(...args);
        if (state === 'HALF_OPEN' || state === 'CLOSED') {
          state = 'CLOSED';
          failureCount = 0;
        }
        return result;
      } catch (err) {
        failureCount++;
        if (state === 'HALF_OPEN' || failureCount >= failureThreshold) {
          state = 'OPEN';
          openedAt = Date.now();
        }
        throw err;
      }
    },
    getState() {
      if (state === 'OPEN' && Date.now() - openedAt >= resetTimeoutMs) {
        return 'HALF_OPEN';
      }
      return state;
    }
  };
}

module.exports = { createCircuitBreaker };
