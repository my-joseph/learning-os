# DRL-PRG-T01-C03-04 — PRG-T01-C03: Problem Solving & Utility Toolkit

> **100% Local IDE Mandate**: All problem solving, refactoring, and debugging must be performed natively in your IDE (VS Code / Cursor).

## Universal 6-Step Pedagogical Practice Loop
1. **คิดเองก่อนเขียน (Mental Model)**: Review the Acceptance Criteria and boundary traps before typing.
2. **ลงมือทำ (Local IDE)**: Open the source file in VS Code or Cursor and implement the logic.
3. **ทดสอบ (Automated Acceptance Testing)**: Run `npm test` or `npm run test:<qid>` in this directory.
4. **อธิบายโค้ด (AI Senior Lead PR Review)**: Articulate your algorithm and request an AI Senior Tech Lead architectural review.
5. **Refactor (Clean Architecture)**: Decouple helpers, clean code smells, and optimize hot paths while keeping tests green.
6. **เพิ่มความยาก (Progression)**: Scale up test inputs and edge cases.

## Quick Terminal Commands
```bash
# Run all acceptance test suites in this workspace
npm test

# Run tests in watch mode while editing
npm run test:watch

# Run tests for a specific question
npm run test:q01
```

## Exercises in this Workspace

### Q01 — `Q01_calculateMonthlyBill.js`
- **Archetype:** Refactoring (Clean Code & Safe Extensibility)
- **Acceptance Scenarios:** 3 test cases in `Q01_calculateMonthlyBill.test.js`
- **Requirement:** Refactor calculateMonthlyBill(account) to support the new 'family' plan (34.99 USD base for 2 members, +8.99 USD per extra member up to 6 max, RangeError if > 6) and annualCommitment (15% discount before tax). Keep all legacy plans (basic, pro, enterprise) green. Decouple plan configuration into clean lookup dictionaries rather than monolithic nested if/else statements.
- **Run Single Suite:** `npm run test:q01`

### Q02 — `Q02_RateLimiter.js`
- **Archetype:** Project-Based (Multi-Module Architecture)
- **Acceptance Scenarios:** 3 test cases in `Q02_RateLimiter.test.js`
- **Requirement:** Build an event-driven RateLimiter class implementing a sliding window algorithm. It extends EventEmitter and tracks request timestamps per key. consume(key) allows up to maxRequests within windowMs and returns { allowed, remaining, resetMs }. When a request exceeds the limit, it emits a 'blocked' event with (key, resetMs) and returns allowed: false. reset(key) clears the history for the specified key.
- **Run Single Suite:** `npm run test:q02`

### Q03 — `Q03_groupBy.js`
- **Archetype:** Problem Solving (Logic & Algorithm)
- **Acceptance Scenarios:** 2 test cases in `Q03_groupBy.test.js`
- **Requirement:** Implement a groupBy(collection, iteratee) utility in JavaScript. It splits a collection into sets, grouped by the result of running each value through iteratee. Iteratee may be either a function (e.g. Math.floor) or a string property key (e.g. 'type'). Return an empty object if the input is null, undefined, or empty.
- **Run Single Suite:** `npm run test:q03`

### Q04 — `Q04_debounce.js`
- **Archetype:** Problem Solving (Logic & Algorithm)
- **Acceptance Scenarios:** 2 test cases in `Q04_debounce.test.js`
- **Requirement:** Implement a production-grade debounce(fn, delay) utility. It delays executing 'fn' until 'delay' milliseconds have elapsed since the last call. All subsequent calls within the delay window must reset the timer. The debounced function must preserve the invocation 'this' context and arguments.
- **Run Single Suite:** `npm run test:q04`

### Q05 — `Q05_calculateOrderTotal.js`
- **Archetype:** Problem Solving (Logic & Algorithm)
- **Acceptance Scenarios:** 3 test cases in `Q05_calculateOrderTotal.test.js`
- **Requirement:** Implement calculateOrderTotal(order) for an e-commerce platform. Validate inputs defensively (items non-empty, price >= 0, integer quantity > 0, throw RangeError). Apply coupon rules (PERCENT10: 10% off up to 20 USD; FIXED15: 15 USD off if subtotal >= 50 USD; FREESHIP). Apply shipping (8 USD standard, free if post-discount subtotal >= 100 USD or VIP or FREESHIP). Calculate 7% sales tax on taxable items (item.taxable !== false) after proportional discount. Return formatted price breakdown { subtotal, discount, shipping, tax, total, currency: 'USD' }.
- **Run Single Suite:** `npm run test:q05`

## Requesting an AI Architectural Review
Once your automated acceptance tests pass 100%, copy this prompt and ask Antigravity / Cursor AI:
```text
Please act as a Senior Tech Lead and conduct an Architecture & Code Craftsmanship Review on my implementation in `DRL-PRG-T01-C03-04`.
Evaluate my code across:
1. Separation of Concerns & Clean Code standards
2. State Management & Data Handling invariants
3. TypeScript typing / JSDoc precision and edge case resilience
4. Performance hot paths, algorithmic complexity, and decoupling suggestions
```
