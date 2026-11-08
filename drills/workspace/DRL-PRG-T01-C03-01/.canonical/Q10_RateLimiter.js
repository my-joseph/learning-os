const EventEmitter = require('node:events');

class RateLimiter extends EventEmitter {
  constructor({ maxRequests = 5, windowMs = 1000 } = {}) {
    super();
    this.maxRequests = maxRequests;
    this.windowMs = windowMs;
    this.records = new Map();
  }

  consume(key) {
    const now = Date.now();
    let timestamps = this.records.get(key) || [];

    // Filter out timestamps outside the sliding window
    timestamps = timestamps.filter(t => now - t < this.windowMs);

    if (timestamps.length >= this.maxRequests) {
      const oldest = timestamps[0];
      const resetMs = Math.max(0, this.windowMs - (now - oldest));
      this.emit('blocked', key, resetMs);
      this.records.set(key, timestamps);
      return { allowed: false, remaining: 0, resetMs };
    }

    timestamps.push(now);
    this.records.set(key, timestamps);
    const remaining = this.maxRequests - timestamps.length;
    return { allowed: true, remaining, resetMs: this.windowMs };
  }

  reset(key) {
    this.records.delete(key);
  }
}

module.exports = { RateLimiter };
