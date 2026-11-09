# DRL-PRG-T01-C01-02 — PRG-T01-C01: JavaScript Deep Dive

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

### Q01 — `Q01_createSandboxContext.js`
- **Archetype:** Problem Solving (Logic & Algorithm)
- **Acceptance Scenarios:** 2 visible scenarios (+ 1 hidden trap tests) in `Q01_createSandboxContext.test.js`
- **Requirement:** Implement `createSandboxContext(parentConfig)` for isolated plugin execution environments.

**System Requirements:**
- `get(key)`: Retrieves `key` from the local child context, or delegates to `parentConfig` if not overridden locally.
- `set(key, value)`: Stores `key` strictly in the local child context without mutating or polluting `parentConfig`.
- `has(key)`: Returns `true` if `key` exists in either child context or parent context.
- Scope Isolation: Mutating child properties must NEVER alter `parentConfig` properties.
- **Run Single Suite:** `npm run test:q01`

### Q02 — `Q02_bindMethodReceiver.js`
- **Archetype:** Problem Solving (Logic & Algorithm)
- **Acceptance Scenarios:** 2 visible scenarios (+ 1 hidden trap tests) in `Q02_bindMethodReceiver.test.js`
- **Requirement:** Implement `bindMethodReceiver(targetInstance, methodNames)` for detached pub/sub event listeners.

**System Requirements:**
- `targetInstance`: An object or class instance containing member methods.
- `methodNames`: Array of string method names to bind.
- Binds each method on `targetInstance` so that detached calls (e.g. `const cb = targetInstance.method; cb()`) retain `this === targetInstance`.
- Preserves prototype method inheritance and passes through all arguments and return values.
- Returns `targetInstance` for fluent chaining.
- **Run Single Suite:** `npm run test:q02`

### Q03 — `Q03_createCurrencyAmount.js`
- **Archetype:** Debugging (Bug Triage & Root Cause)
- **Acceptance Scenarios:** 2 visible scenarios (+ 1 hidden trap tests) in `Q03_createCurrencyAmount.test.js`
- **Requirement:** Debug `createCurrencyAmount(amount, currency)` in a fintech ledger calculation engine.

**System Requirements:**
- Returns an immutable Value Object representing a monetary amount.
- In numeric arithmetic contexts (`+`, `-`, `>`, `<`), the object must evaluate to its numeric `amount`.
- In string contexts (template literals, string concatenation), it evaluates to formatted `"<amount> <currency>"`.
- Strict Numeric Addition: `createCurrencyAmount(100, 'USD') + 50` must yield `150`, NOT `"100 USD50"`.
- **Run Single Suite:** `npm run test:q03`

### Q04 — `Q04_deepCloneCircular.js`
- **Archetype:** Problem Solving (Logic & Algorithm)
- **Acceptance Scenarios:** 2 visible scenarios (+ 1 hidden trap tests) in `Q04_deepCloneCircular.test.js`
- **Requirement:** Implement `deepCloneCircular(target)` for deep state tree cloning with cyclic reference handling.

**System Requirements:**
- Recursively clone all nested plain objects and arrays.
- Primitive values (`number`, `string`, `boolean`, `null`, `undefined`) and functions are returned as-is.
- Circular References: Self-referential or cross-referencing objects must be preserved in the cloned graph without throwing `RangeError: Maximum call stack size exceeded`.
- Complete Mutation Isolation: Mutating properties on the clone must NEVER modify the original target object.
- **Run Single Suite:** `npm run test:q04`

### Q05 — `Q05_composeAsyncMiddleware.js`
- **Archetype:** Problem Solving (Logic & Algorithm)
- **Acceptance Scenarios:** 2 visible scenarios (+ 1 hidden trap tests) in `Q05_composeAsyncMiddleware.test.js`
- **Requirement:** Implement `composeAsyncMiddleware(middlewares)` for an onion-model API gateway request pipeline.

**Pipeline Specification:**
- `middlewares`: Array of functions with signature `async (context, next) => void`.
- Returns an executable runner: `async (context) => void`.
- Flow: Each middleware executes sequentially, delegating to the downstream middleware by calling `await next()`.
- Multiple Next Guard: If a single middleware calls `next()` more than once, throw `Error('next() called multiple times')`.
- Upstream Return: Once the downstream completes, control flows back up the stack (onion-style).
- Error Bubbling: Uncaught exceptions in downstream middleware propagate back to upstream catch blocks.
- **Run Single Suite:** `npm run test:q05`

## Requesting an AI Architectural Review
Once your automated acceptance tests pass 100%, copy this prompt and ask Antigravity / Cursor AI:
```text
Please act as a Senior Tech Lead and conduct an Architecture & Code Craftsmanship Review on my implementation in `DRL-PRG-T01-C01-02`.
Evaluate my code across:
1. Separation of Concerns & Clean Code standards
2. State Management & Data Handling invariants
3. TypeScript typing / JSDoc precision and edge case resilience
4. Performance hot paths, algorithmic complexity, and decoupling suggestions
```
