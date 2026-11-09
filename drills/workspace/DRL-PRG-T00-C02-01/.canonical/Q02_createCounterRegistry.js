function createCounterRegistry() {
  const metrics = new Map();

  return {
    increment(metric, amount = 1) {
      const current = metrics.get(metric) || 0;
      metrics.set(metric, current + amount);
    },
    getCount(metric) {
      return metrics.get(metric) || 0;
    },
    getSnapshot() {
      const snapshot = {};
      for (const [k, v] of metrics.entries()) {
        snapshot[k] = v;
      }
      return snapshot;
    }
  };
}

module.exports = { createCounterRegistry };
