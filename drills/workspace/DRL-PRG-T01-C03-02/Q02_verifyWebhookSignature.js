/**
 * ============================================================================
 * [DRL-PRG-T01-C03-02] Q02: Debugging (Bug Triage & Root Cause)
 * Target Competencies: Engineering Fundamentals
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
 * Debug `verifyWebhookSignature(payload, signatureHeader, secret, toleranceSeconds)` in a payment webhook receiver.

**Defect Analysis:**
- The legacy starter implementation compares signatures with naive equality `===`, vulnerable to timing side-channels.
- The legacy implementation ignores timestamp drift, permitting stale replayed requests.

**Target Invariants:**
- Extract `timestamp` and `v1` signature hex from `signatureHeader` formatted as `t=<timestamp>,v1=<signatureHex>`.
- Validate that `Math.abs(currentTimeSec - timestamp) <= toleranceSeconds` (default $300$ seconds). Reject if outside window.
- Compute expected HMAC-SHA256 hex digest using `crypto.createHmac('sha256', secret)`.
- Compare computed digest and received `v1` signature using `crypto.timingSafeEqual` over Buffers of equal byte length.
 * ============================================================================
 */

const crypto = require('crypto');

function verifyWebhookSignature(payload, signatureHeader, secret, toleranceSeconds = 300) {
  const parts = signatureHeader.split(',');
  let timestamp = null;
  let signatureHex = null;

  for (const part of parts) {
    const [key, val] = part.split('=');
    if (key === 't') timestamp = parseInt(val, 10);
    if (key === 'v1') signatureHex = val;
  }

  if (!timestamp || !signatureHex) return false;

  // BUG 1: Missing timestamp expiration check (replays accepted)
  // BUG 2: Naive string equality comparison vulnerable to timing attacks
  const expectedHex = crypto.createHmac('sha256', secret).update(`${timestamp}.${payload}`).digest('hex');
  return expectedHex === signatureHex;
}

module.exports = { verifyWebhookSignature };
