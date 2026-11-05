/**
 * ============================================================================
 * [DRL-PRG-T01-C03-04] Q02: Project-Based (Multi-Module Architecture)
 * Target Competencies: State Management, Component Design, Performance & Optimization
 * ============================================================================
 * 
 * 6-STEP PEDAGOGICAL PRACTICE LOOP:
 * 1. คิดเองก่อนเขียน : Sketch invariants, mental model, and boundary edge cases.
 * 2. ลงมือทำ         : Write your implementation in this file.
 * 3. ทดสอบ           : Run `npm test` or `npm run test:q02` in this folder.
 * 4. อธิบายโค้ด      : Explain the algorithm and request an AI Senior Tech Lead PR Review.
 * 5. Refactor        : Decouple helpers, improve readability, and optimize performance.
 * 6. เพิ่มความยาก     : Scale up test inputs and handle harsher stress scenarios.
 * 
 * SPECIFICATION:
 * Build an event-driven RateLimiter class implementing a sliding window algorithm. It extends EventEmitter and tracks request timestamps per key. consume(key) allows up to maxRequests within windowMs and returns { allowed, remaining, resetMs }. When a request exceeds the limit, it emits a 'blocked' event with (key, resetMs) and returns allowed: false. reset(key) clears the history for the specified key.
 * ============================================================================
 */

const EventEmitter = require('node:events');

/**
 * Event-Driven Sliding Window Rate Limiter.
 * 
 * Specifications:
 * - Extends EventEmitter.
 * - constructor({ maxRequests = 5, windowMs = 1000 })
 * - consume(key):
 *     Checks how many requests key has made within the trailing windowMs window.
 *     If requests < maxRequests:
 *       Record invocation timestamp, return { allowed: true, remaining: number, resetMs: number }.
 *     If requests >= maxRequests:
 *       Emit 'blocked' event with arguments (key, resetMs).
 *       Return { allowed: false, remaining: 0, resetMs: number }.
 * - reset(key): Clears recorded history for key.
 */
class RateLimiter extends EventEmitter {
  constructor({ maxRequests = 5, windowMs = 1000 } = {}) {
    super();
    this.maxRequests = maxRequests;
    this.windowMs = windowMs;
    // TODO: Initialize data structures for tracking timestamps per key
  }

  consume(key) {
    // TODO: Implement sliding window logic and emit 'blocked' on limit breach
  }

  reset(key) {
    // TODO: Reset history for key
  }
}

module.exports = { RateLimiter };
