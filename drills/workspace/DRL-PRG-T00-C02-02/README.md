# DRL-PRG-T00-C02-02 — PRG-T00-C02: JavaScript & TypeScript Baseline

> **Environment Preset:** `node-vanilla` — Standard Node.js Native Runner (CommonJS/ESM)
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

# Request Senior Tech Lead AI PR Review (packages code & copies prompt to clipboard)
npm run review
npm run review q01

# Grade all exercises (runs visible + hidden trap tests) and sync to Notion
npm run submit
```

## Exercises in this Workspace

### Q01 — `Q01_clampBatteryPercent.js`
- **Archetype:** Problem Solving (Logic & Algorithm)
- **Acceptance Scenarios:** 2 visible scenarios (+ 2 hidden trap tests) in `Q01_clampBatteryPercent.test.js`
- **Requirement:** Implement `clampBatteryPercent(rawLevel)` for a device dashboard.

**Requirements:**
- If `rawLevel` is a finite `number`, return it limited to the range `0` to `100`.
- For anything else (numeric strings, `NaN`, `Infinity`, `null`, `undefined`), return `null`.
- Do not coerce strings into numbers.
- **Run Single Suite:** `npm run test:q01`

### Q02 — `Q02_resolveRetryLimit.js`
- **Archetype:** Problem Solving (Logic & Algorithm)
- **Acceptance Scenarios:** 2 visible scenarios (+ 3 hidden trap tests) in `Q02_resolveRetryLimit.test.js`
- **Requirement:** Implement `resolveRetryLimit(settings)` for a background job queue.

**Requirements:**
- Return `settings.maxRetries` when it is provided.
- When it is `null` or `undefined` (or `settings` itself is missing), return the default `3`.
- `0` is a valid configured value and must be returned as `0`.
- **Run Single Suite:** `npm run test:q02`

### Q03 — `Q03_countValidQuantities.js`
- **Archetype:** Problem Solving (Logic & Algorithm)
- **Acceptance Scenarios:** 2 visible scenarios (+ 4 hidden trap tests) in `Q03_countValidQuantities.test.js`
- **Requirement:** Implement `countValidQuantities(rawQuantities)` for a warehouse CSV import.

**Requirements:**
- `rawQuantities` is an array of mixed values.
- Count only entries that are real `number` values, are integers, and are `>= 0`.
- Numeric strings such as `'12'` are invalid and must not be counted.
- **Run Single Suite:** `npm run test:q03`

### Q04 — `Q04_formatDisplayName.js`
- **Archetype:** Problem Solving (Logic & Algorithm)
- **Acceptance Scenarios:** 2 visible scenarios (+ 2 hidden trap tests) in `Q04_formatDisplayName.test.js`
- **Requirement:** Implement `formatDisplayName(profile)` for a profile header.

**Requirements:**
- Return `profile.fullName` when it contains non-whitespace text (trimmed).
- Otherwise return the trimmed `profile.username` when it has non-whitespace text.
- Otherwise return `'Guest'`.
- Missing properties and empty or whitespace-only strings count as absent.
- **Run Single Suite:** `npm run test:q04`

### Q05 — `Q05_applyDiscount.js`
- **Archetype:** Problem Solving (Logic & Algorithm)
- **Acceptance Scenarios:** 2 visible scenarios (+ 3 hidden trap tests) in `Q05_applyDiscount.test.js`
- **Requirement:** Implement `applyDiscount(price, rate)` for a checkout service.

**Requirements:**
- `price` is a number in dollars; `rate` is a fraction (for example `0.2` means 20% off).
- When `rate` is not supplied, use a default rate of `0.1`.
- Return the discounted price rounded to 2 decimal places as a number.
- An explicit rate of `0` means no discount and must be respected.
- **Run Single Suite:** `npm run test:q05`

### Q06 — `Q06_sumInvoiceTotal.js`
- **Archetype:** Problem Solving (Logic & Algorithm)
- **Acceptance Scenarios:** 2 visible scenarios (+ 3 hidden trap tests) in `Q06_sumInvoiceTotal.test.js`
- **Requirement:** Implement `sumInvoiceTotal(taxRate, ...lineAmounts)` for an invoicing module.

**Requirements:**
- `taxRate` is a fraction (for example `0.07` means 7% tax).
- `lineAmounts` are any number of line item amounts supplied as separate arguments.
- Return the sum of all line amounts plus tax, rounded to 2 decimal places.
- With no line amounts, return `0`.
- **Run Single Suite:** `npm run test:q06`

### Q07 — `Q07_summarizeTemperatures.js`
- **Archetype:** Problem Solving (Logic & Algorithm)
- **Acceptance Scenarios:** 2 visible scenarios (+ 3 hidden trap tests) in `Q07_summarizeTemperatures.test.js`
- **Requirement:** Implement `summarizeTemperatures(readings)` for a weather station.

**Requirements:**
- `readings` is a non-empty array of numbers (degrees Celsius).
- Return an object `{ min, max, average }`.
- `average` must be rounded to 1 decimal place.
- Do not mutate the input array.
- **Run Single Suite:** `npm run test:q07`

### Q08 — `Q08_listActiveEmails.js`
- **Archetype:** Problem Solving (Logic & Algorithm)
- **Acceptance Scenarios:** 2 visible scenarios (+ 3 hidden trap tests) in `Q08_listActiveEmails.test.js`
- **Requirement:** Implement `listActiveEmails(subscribers)` for a newsletter export.

**Requirements:**
- `subscribers` is an array of `{ email, isActive }` objects.
- Return an array of the lowercase, trimmed `email` values of active subscribers only.
- Preserve the original order and do not mutate the input.
- **Run Single Suite:** `npm run test:q08`

### Q09 — `Q09_buildShippingLabel.js`
- **Archetype:** Problem Solving (Logic & Algorithm)
- **Acceptance Scenarios:** 2 visible scenarios (+ 2 hidden trap tests) in `Q09_buildShippingLabel.test.js`
- **Requirement:** Implement `buildShippingLabel(order)` for a shipping label printer.

**Requirements:**
- `order` has the shape `{ customer: { name, address: { city, postalCode } }, items: [...] }`.
- Return a string formatted exactly as `NAME - CITY POSTALCODE (N items)` where `N` is the number of items.
- Use `1 item` (singular) when there is exactly one item.
- **Run Single Suite:** `npm run test:q09`

### Q10 — `Q10_adjustStock.js`
- **Archetype:** Problem Solving (Logic & Algorithm)
- **Acceptance Scenarios:** 2 visible scenarios (+ 3 hidden trap tests) in `Q10_adjustStock.test.js`
- **Requirement:** Implement `adjustStock(stockBySku, sku, delta)` for a stock ledger.

**Requirements:**
- `stockBySku` maps SKU strings to integer quantities, for example `{ 'SKU-1': 4 }`.
- Return a **new** object where `sku` has its quantity increased by `delta` (`delta` may be negative).
- A SKU that does not exist yet starts from `0`.
- The original `stockBySku` object must remain unchanged.
- **Run Single Suite:** `npm run test:q10`

## Requesting an AI Architectural Review
Once your automated acceptance tests pass 100%, copy this prompt and ask Antigravity / Cursor AI:
```text
Please act as a Senior Tech Lead and conduct an Architecture & Code Craftsmanship Review on my implementation in `DRL-PRG-T00-C02-02`.
Evaluate my code across:
1. Separation of Concerns & Clean Code standards
2. State Management & Data Handling invariants
3. TypeScript typing / JSDoc precision and edge case resilience
4. Performance hot paths, algorithmic complexity, and decoupling suggestions
```
