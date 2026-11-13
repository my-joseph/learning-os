function createCircuitBreaker(asyncOperation, options = {}) {
  // TODO: implement three-state circuit breaker state machine
  return {
    async execute(...args) {
      return asyncOperation(...args);
    },
    getState() {
      return 'CLOSED';
    }
  };
}

module.exports = { createCircuitBreaker };
