# -*- coding: utf-8 -*-
"""
Kata, Real-World Problem Solving & Architecture Templates for PRG-T01-C03:
Problem Solving & Utility Toolkit (Debounce, GroupBy, Memoize, AsyncCache, OrderPricing, LegacyRefactor, RateLimiter).

Enforces the 5 Real-World Problem Archetypes:
1. Problem Solving (Logic & Algorithm)
2. Debugging (Bug Triage & Root Cause)
3. Code Tracing (Mental Execution Model)
4. Code Modification & Refactoring (Clean Architecture & Safe Extensibility)
5. Project-Based (Multi-Module Subsystem Architecture)

And the 7 Core Engineering Competencies:
- Data Handling
- State Management
- Component Design
- API Integration
- TypeScript Typing
- Architecture & Separation of Concerns
- Performance & Optimization

All problems are execution-verified against Node.js test runner during generation.
Materializes starter files and test files in drills/workspace/ for real Cursor/VS Code work.
"""
import random

TITLE = "Problem Solving & Utility Toolkit"
CHAPTER_CODE = "PRG-T01-C03"
TOPIC_CODE = "PRG-T01"

MISTAKE_TAGS = [
    {
        "id": "missing-context-binding",
        "name": "Loss of 'this' Context in Higher-Order Functions",
        "label": "Context Binding Loss",
        "autoFrom": ["missing-context-binding"],
    },
    {
        "id": "timer-cancellation-flaw",
        "name": "Failure to Clear Previous Timer in Debounce/Throttle",
        "label": "Timer Cancellation Bug",
        "autoFrom": ["timer-cancellation-flaw"],
    },
    {
        "id": "shallow-vs-deep-copy",
        "name": "Shallow Copy instead of Deep Clone Mutation",
        "label": "Shallow vs Deep Copy",
        "autoFrom": ["shallow-vs-deep-copy"],
    },
    {
        "id": "unhandled-falsy-cache",
        "name": "Cache Check Flaw with Falsy Values (0 / false / null)",
        "label": "Falsy Cache Bug",
        "autoFrom": ["unhandled-falsy-cache"],
    },
    {
        "id": "empty-input-handling",
        "name": "Crash on Empty Array or Null Input",
        "label": "Empty Input Edge Case",
        "autoFrom": ["empty-input-handling"],
    },
    {
        "id": "race-condition-cache-stampede",
        "name": "Concurrent Cache Stampede without In-Flight Deduplication",
        "label": "Cache Stampede Race Condition",
        "autoFrom": ["race-condition-cache-stampede"],
    },
    {
        "id": "state-mutation-leak",
        "name": "Direct Mutation of Shared Cached Reference",
        "label": "State Mutation Leak",
        "autoFrom": ["state-mutation-leak"],
    },
    {
        "id": "legacy-coupling-regression",
        "name": "Regression in Legacy Business Invariants during Refactoring",
        "label": "Legacy Coupling Regression",
        "autoFrom": ["legacy-coupling-regression"],
    },
    {
        "id": "rate-limit-window-leak",
        "name": "Failure to Expire or Slide Rate Limit Window",
        "label": "Rate Limit Window Leak",
        "autoFrom": ["rate-limit-window-leak"],
    },
    {
        "id": "tax-discount-order-inversion",
        "name": "Inverted Discount and Tax Calculation Order",
        "label": "Tax Discount Order Inversion",
        "autoFrom": ["tax-discount-order-inversion"],
    },
]


# ============================================================================
# ARCHETYPE 1: Problem Solving — Debounce Function (Level 2)
# ============================================================================
def build_kata_debounce(rng: random.Random) -> dict:
    default_delay = rng.choice([50, 60, 80])

    starter = """function debounce(fn, delay) {
  let timer = null;

  return function(...args) {
    // TODO: Clear previous timer and schedule new invocation preserving 'this' and args
  };
}

module.exports = { debounce };
"""

    solution = """function debounce(fn, delay) {
  let timer = null;

  return function(...args) {
    clearTimeout(timer);
    timer = setTimeout(() => {
      fn.apply(this, args);
    }, delay);
  };
}

module.exports = { debounce };
"""

    visible_tests = [
        {
            "id": "v1",
            "name": f"should not execute synchronously and only fire once after {default_delay}ms",
            "testCode": f"""
            let callCount = 0;
            const debounced = debounce(() => {{ callCount++; }}, {default_delay});
            debounced();
            debounced();
            debounced();
            assert.strictEqual(callCount, 0, "Should not fire immediately");
            await new Promise(r => setTimeout(r, {default_delay + 30}));
            assert.strictEqual(callCount, 1, "Should fire exactly once after delay");
            """,
        },
        {
            "id": "v2",
            "name": "should reset the timer on each subsequent call within delay window",
            "testCode": f"""
            let value = 0;
            const debounced = debounce((v) => {{ value = v; }}, {default_delay});
            debounced(1);
            await new Promise(r => setTimeout(r, {default_delay // 2}));
            debounced(2);
            await new Promise(r => setTimeout(r, {default_delay // 2}));
            assert.strictEqual(value, 0, "Should still be 0 before second delay expires");
            await new Promise(r => setTimeout(r, {default_delay // 2 + 25}));
            assert.strictEqual(value, 2, "Should record latest value 2");
            """,
        },
    ]

    hidden_tests = [
        {
            "id": "h1",
            "name": "should preserve execution 'this' context and multiple arguments",
            "testCode": """
            let received = null;
            const ctx = { multiplier: 10 };
            const debounced = debounce(function(a, b) {
              received = (this.multiplier || 1) * (a + b);
            }, 30);
            debounced.call(ctx, 3, 4);
            await new Promise(r => setTimeout(r, 50));
            assert.strictEqual(received, 70, "Must preserve 'this' and all arguments");
            """,
        },
        {
            "id": "h2",
            "name": "should support 0ms delay as a macrotask deferral",
            "testCode": """
            let called = false;
            const debounced = debounce(() => { called = true; }, 0);
            debounced();
            assert.strictEqual(called, false, "0ms timeout still defers to next macrotask");
            await new Promise(r => setTimeout(r, 20));
            assert.strictEqual(called, true, "Should fire in subsequent event loop cycle");
            """,
        },
    ]

    return {
        "category": "Concurrency & Timing",
        "context": "Frontend & Event Flow",
        "prompt": (
            "Implement a production-grade `debounce(fn, delay)` utility in JavaScript.\n\n"
            "**Behavioral Requirements:**\n"
            "- Delays executing `fn` until `delay` milliseconds have elapsed since the last invocation.\n"
            "- Repeated calls within the delay window must reset the timer and postpone execution.\n"
            "- Must preserve the invocation `this` context and forward all received arguments.\n"
            "- Supports `0ms` delay as a macrotask deferral."
        ),
        "codeType": "problem-solving",
        "archetype": "problem-solving",
        "competencies": ["performance", "component-design"],
        "entryPoint": "debounce",
        "starterCode": starter,
        "solutionCode": solution,
        "visibleTests": visible_tests,
        "hiddenTests": hidden_tests,
        "answerSpec": {
            "type": "code_output",
            "value": "debounce implementation",
            "commonTrapTag": "timer-cancellation-flaw",
        },
        "answerPlain": "debounce implementation",
        "answerDisplay": "debounce(fn, delay)",
        "inputHint": "Implement in Cursor / VS Code and run tests in terminal",
        "checkpointHint": (
            "Store timer in closure scope and invoke clearTimeout(timer) before scheduling setTimeout."
        ),
        "commonTrapTag": "timer-cancellation-flaw",
        "steps": [
            {
                "latex": "\\text{Closure Scope: } \\text{let timer = null;}",
                "explain": (
                    "Declare a local 'timer' variable in the outer closure so that each invocation of the returned "
                    "wrapper function shares and mutates the same timer handle."
                ),
            },
            {
                "latex": "\\text{Timer Reset: } \\text{clearTimeout(timer); timer = setTimeout(...);}",
                "explain": (
                    "Cancel any pending scheduled task before queuing a new timeout. When the timeout triggers, "
                    "call 'fn.apply(this, args)' to preserve context."
                ),
            },
        ],
        "references": ["PRG-T01-C03-U04", "PRG-T01-C03-U01"],
        "form": "direct",
        "verify": {"solutionCode": solution, "trapValue": "missing clearTimeout(timer) before setTimeout"},
    }


# ============================================================================
# ARCHETYPE 1: Problem Solving — GroupBy Utility (Level 1)
# ============================================================================
def build_kata_groupby(rng: random.Random) -> dict:
    starter = """function groupBy(collection, iteratee) {
  // TODO: Group elements of collection into an object based on iteratee
  return {};
}

module.exports = { groupBy };
"""

    solution = """function groupBy(collection, iteratee) {
  if (!collection || !Array.isArray(collection)) {
    return {};
  }

  const getKey = typeof iteratee === 'function'
    ? iteratee
    : (item) => (item != null ? item[iteratee] : undefined);

  return collection.reduce((acc, item) => {
    const key = getKey(item);
    if (key !== undefined) {
      if (!acc[key]) {
        acc[key] = [];
      }
      acc[key].push(item);
    }
    return acc;
  }, {});
}

module.exports = { groupBy };
"""

    visible_tests = [
        {
            "id": "v1",
            "name": "should group array items by string property name",
            "testCode": """
            const items = [
              { name: 'apple', type: 'fruit' },
              { name: 'carrot', type: 'vegetable' },
              { name: 'banana', type: 'fruit' },
            ];
            const result = groupBy(items, 'type');
            assert.deepStrictEqual(result, {
              fruit: [
                { name: 'apple', type: 'fruit' },
                { name: 'banana', type: 'fruit' },
              ],
              vegetable: [
                { name: 'carrot', type: 'vegetable' },
              ],
            });
            """,
        },
        {
            "id": "v2",
            "name": "should group array items by custom function iteratee",
            "testCode": """
            const numbers = [6.1, 4.2, 6.3];
            const result = groupBy(numbers, Math.floor);
            assert.deepStrictEqual(result, {
              '4': [4.2],
              '6': [6.1, 6.3],
            });
            """,
        },
    ]

    hidden_tests = [
        {
            "id": "h1",
            "name": "should handle empty array and null inputs without throwing",
            "testCode": """
            assert.deepStrictEqual(groupBy([], 'any'), {});
            assert.deepStrictEqual(groupBy(null, 'any'), {});
            assert.deepStrictEqual(groupBy(undefined, 'any'), {});
            """,
        },
        {
            "id": "h2",
            "name": "should omit items where property evaluates to undefined",
            "testCode": """
            const items = [{ a: 'x' }, { b: 'y' }];
            const result = groupBy(items, 'a');
            assert.deepStrictEqual(result, { x: [{ a: 'x' }] });
            """,
        },
    ]

    return {
        "category": "Data Transformation",
        "context": "Collection Processing",
        "prompt": (
            "Implement a `groupBy(collection, iteratee)` utility in JavaScript.\n\n"
            "**Behavioral Requirements:**\n"
            "- Splits `collection` into sets grouped by the result of running each value through `iteratee`.\n"
            "- `iteratee` can be either a function (e.g. `Math.floor`) or a string property name (e.g. `'type'`).\n"
            "- Return an empty object `{}` if `collection` is `null`, `undefined`, or an empty array."
        ),
        "codeType": "problem-solving",
        "archetype": "problem-solving",
        "competencies": ["data-handling", "performance"],
        "entryPoint": "groupBy",
        "starterCode": starter,
        "solutionCode": solution,
        "visibleTests": visible_tests,
        "hiddenTests": hidden_tests,
        "answerSpec": {
            "type": "code_output",
            "value": "groupBy implementation",
            "commonTrapTag": "empty-input-handling",
        },
        "answerPlain": "groupBy implementation",
        "answerDisplay": "groupBy(collection, iteratee)",
        "inputHint": "Implement in Cursor / VS Code and run tests in terminal",
        "checkpointHint": (
            "Check if iteratee is typeof function vs string property, and reduce over collection."
        ),
        "commonTrapTag": "empty-input-handling",
        "steps": [
            {
                "latex": "\\text{Guard Clause: } \\text{if (!collection || !Array.isArray(collection)) return \\{\\};}",
                "explain": (
                    "Prevent TypeError runtime crashes by checking whether the collection input is valid and an Array."
                ),
            },
            {
                "latex": "\\text{Iteratee Normalization: } \\text{typeof iteratee === 'function' ? iteratee : item => item[iteratee]}",
                "explain": (
                    "Normalize the key-extraction logic into a uniform getter function so reduce logic remains identical."
                ),
            },
        ],
        "references": ["PRG-T01-C03-U02", "PRG-T01-C03-U01"],
        "form": "direct",
        "verify": {"solutionCode": solution, "trapValue": "TypeError: Cannot read properties of null (reading 'reduce')"},
    }


# ============================================================================
# ARCHETYPE 1: Problem Solving — Order Pricing Pipeline (Level 2)
# ============================================================================
def build_order_pricing_pipeline(rng: random.Random) -> dict:
    starter = """/**
 * Calculates final pricing for an e-commerce order.
 * 
 * Invariants:
 * - order.items must be a non-empty array of items with price >= 0 and integer quantity > 0.
 * - Throw RangeError for invalid item price, quantity, or empty items array.
 * - Coupons:
 *     'PERCENT10': 10% off subtotal up to $20 max discount.
 *     'FIXED15': $15 off if subtotal >= $50, else $0.
 *     'FREESHIP': Free shipping.
 * - Shipping: $8 standard; free if post-discount subtotal >= $100, isVip is true, or coupon is 'FREESHIP'.
 * - Tax: 7% on taxable items (where item.taxable !== false) applied to discounted taxable subtotal.
 * - Return: { subtotal, discount, shipping, tax, total, currency: 'USD' } with 2 decimal precision.
 */
function calculateOrderTotal(order) {
  // TODO: Implement defensive validation and pricing pipeline
}

module.exports = { calculateOrderTotal };
"""

    solution = """function calculateOrderTotal(order) {
  if (!order || !Array.isArray(order.items) || order.items.length === 0) {
    throw new RangeError('Order must contain at least one item');
  }

  let subtotal = 0;
  let taxableSubtotal = 0;

  for (const item of order.items) {
    if (
      typeof item.price !== 'number' ||
      item.price < 0 ||
      typeof item.quantity !== 'number' ||
      item.quantity <= 0 ||
      !Number.isInteger(item.quantity)
    ) {
      throw new RangeError('Invalid item price or quantity');
    }
    const itemTotal = item.price * item.quantity;
    subtotal += itemTotal;
    if (item.taxable !== false) {
      taxableSubtotal += itemTotal;
    }
  }

  // Round subtotal to 2 decimals
  subtotal = Math.round(subtotal * 100) / 100;

  // 1. Calculate Discount
  let discount = 0;
  if (order.couponCode === 'PERCENT10') {
    discount = Math.min(20, Math.round(subtotal * 0.10 * 100) / 100);
  } else if (order.couponCode === 'FIXED15') {
    discount = subtotal >= 50 ? 15 : 0;
  }

  const discountedSubtotal = Math.max(0, Math.round((subtotal - discount) * 100) / 100);

  // 2. Shipping Calculation
  const isFreeShip = Boolean(
    order.isVip ||
    order.couponCode === 'FREESHIP' ||
    discountedSubtotal >= 100
  );
  const shipping = isFreeShip ? 0 : 8;

  // 3. Tax Calculation (7% on discounted taxable subtotal)
  const taxRatio = subtotal > 0 ? taxableSubtotal / subtotal : 0;
  const taxableDiscounted = Math.max(0, taxableSubtotal - (discount * taxRatio));
  const tax = Math.round(taxableDiscounted * 0.07 * 100) / 100;

  const total = Math.round((discountedSubtotal + shipping + tax) * 100) / 100;

  return { subtotal, discount, shipping, tax, total, currency: 'USD' };
}

module.exports = { calculateOrderTotal };
"""

    visible_tests = [
        {
            "id": "v1",
            "name": "should calculate subtotal, 10% coupon with cap, shipping, and tax",
            "testCode": """
            const order = {
              items: [
                { id: 'p1', name: 'Keyboard', price: 60, quantity: 1, taxable: true },
                { id: 'p2', name: 'Mousepad', price: 20, quantity: 2, taxable: false },
              ],
              couponCode: 'PERCENT10',
              isVip: false,
            };
            const result = calculateOrderTotal(order);
            assert.strictEqual(result.subtotal, 100);
            assert.strictEqual(result.discount, 10);
            assert.strictEqual(result.shipping, 8, 'Post-discount subtotal is 90 < 100, standard shipping $8');
            assert.strictEqual(result.tax, 3.78, '60 taxable - 6 discount = 54 taxable * 0.07 = 3.78');
            assert.strictEqual(result.total, 101.78);
            assert.strictEqual(result.currency, 'USD');
            """,
        },
        {
            "id": "v2",
            "name": "should grant free shipping for orders >= $100 post-discount or VIP",
            "testCode": """
            const vipOrder = {
              items: [{ id: 'p1', price: 30, quantity: 1, taxable: true }],
              couponCode: null,
              isVip: true,
            };
            const resVip = calculateOrderTotal(vipOrder);
            assert.strictEqual(resVip.shipping, 0, 'VIP member gets free shipping');

            const bigOrder = {
              items: [{ id: 'p2', price: 150, quantity: 1, taxable: true }],
              couponCode: 'PERCENT10',
              isVip: false,
            };
            const resBig = calculateOrderTotal(bigOrder);
            assert.strictEqual(resBig.discount, 15);
            assert.strictEqual(resBig.shipping, 0, 'Subtotal 135 >= 100 qualifies for free shipping');
            """,
        },
        {
            "id": "v3",
            "name": "should throw RangeError on empty items or invalid price/quantity",
            "testCode": """
            assert.throws(() => calculateOrderTotal({ items: [] }), /RangeError/);
            assert.throws(() => calculateOrderTotal({ items: [{ price: -5, quantity: 1 }] }), /RangeError/);
            assert.throws(() => calculateOrderTotal({ items: [{ price: 10, quantity: 0 }] }), /RangeError/);
            """,
        },
    ]

    hidden_tests = [
        {
            "id": "h1",
            "name": "should cap PERCENT10 coupon discount at exactly $20.00",
            "testCode": """
            const hugeOrder = {
              items: [{ id: 'p1', price: 500, quantity: 1, taxable: true }],
              couponCode: 'PERCENT10',
              isVip: false,
            };
            const res = calculateOrderTotal(hugeOrder);
            assert.strictEqual(res.discount, 20, 'Max discount is capped at $20');
            """,
        },
        {
            "id": "h2",
            "name": "should handle FIXED15 threshold rule ($50 minimum subtotal)",
            "testCode": """
            const smallOrder = {
              items: [{ id: 'p1', price: 40, quantity: 1, taxable: true }],
              couponCode: 'FIXED15',
              isVip: false,
            };
            assert.strictEqual(calculateOrderTotal(smallOrder).discount, 0, 'Subtotal 40 < 50, discount is 0');
            """,
        },
    ]

    return {
        "category": "E-Commerce & Financial Pipeline",
        "context": "Pricing & Invariant Enforcement",
        "prompt": (
            "Implement `calculateOrderTotal(order)` for an e-commerce platform.\n\n"
            "**Validation Invariants:**\n"
            "- `order.items` must be a non-empty array.\n"
            "- Each item must have `price >= 0` and integer `quantity > 0`.\n"
            "- Throw `RangeError` if validation fails or items is empty.\n\n"
            "**Discount & Coupon Rules:**\n"
            "- `PERCENT10`: 10% discount on subtotal, capped at 20 USD max.\n"
            "- `FIXED15`: 15 USD discount if subtotal >= 50 USD, else 0 USD.\n"
            "- `FREESHIP`: Free shipping voucher.\n\n"
            "**Shipping Policy:**\n"
            "- Standard shipping is 8 USD.\n"
            "- Free shipping if post-discount subtotal >= 100 USD, or `isVip` is `true`, or coupon is `FREESHIP`.\n\n"
            "**Taxation & Output Contract:**\n"
            "- Apply 7% sales tax on taxable items (`item.taxable !== false`) on the discounted taxable amount.\n"
            "- Return price breakdown: `{ subtotal, discount, shipping, tax, total, currency: 'USD' }` (rounded to 2 decimals)."
        ),
        "codeType": "problem-solving",
        "archetype": "problem-solving",
        "competencies": ["data-handling", "architecture", "performance"],
        "entryPoint": "calculateOrderTotal",
        "starterCode": starter,
        "solutionCode": solution,
        "visibleTests": visible_tests,
        "hiddenTests": hidden_tests,
        "answerSpec": {
            "type": "code_output",
            "value": "calculateOrderTotal implementation",
            "commonTrapTag": "tax-discount-order-inversion",
        },
        "answerPlain": "calculateOrderTotal implementation",
        "answerDisplay": "calculateOrderTotal(order)",
        "inputHint": "Implement in Cursor / VS Code and run tests in terminal",
        "checkpointHint": (
            "Apply discounts before tax and shipping, and calculate tax only on the discounted taxable amount."
        ),
        "commonTrapTag": "tax-discount-order-inversion",
        "steps": [
            {
                "latex": "\\text{Input Validation: } \\text{if (!order || !order.items.length) throw RangeError}",
                "explain": (
                    "Guard against invalid payloads early. Ensure every item has non-negative price and positive quantity."
                ),
            },
            {
                "latex": "\\text{Tax Base: } \\text{taxableDiscounted = taxableSubtotal - (discount \\times taxRatio)}",
                "explain": (
                    "Calculate sales tax on the net discounted taxable base rather than the pre-discount gross price."
                ),
            },
        ],
        "references": ["PRG-T01-C03-U03", "PRG-T01-C03-U01"],
        "form": "direct",
        "verify": {"solutionCode": solution, "trapValue": "tax computed on pre-discount subtotal (4.20 instead of 3.78)"},
    }


# ============================================================================
# ARCHETYPE 2: Debugging — In-Memory Async Cache with Stampede Prevention (Level 3)
# ============================================================================
def build_debugging_async_cache(rng: random.Random) -> dict:
    # Buggy starter code:
    # Bug 1: No in-flight deduplication (cache stampede under concurrency)
    # Bug 2: Returns raw cached object without defensive clone, allowing caller mutations to corrupt cache
    starter = """/**
 * In-Memory Async Cache with TTL.
 * 
 * KNOWN DEFECTS TO TRIAGE & FIX:
 * 1. Cache Stampede: Simultaneous concurrent requests for the same key fire multiple fetches
 *    instead of sharing a single in-flight Promise.
 * 2. State Mutation Leak: Callers mutating returned cache objects corrupt the internal cache.
 */
class AsyncCache {
  constructor(ttlMs = 1000) {
    this.ttlMs = ttlMs;
    this.cache = new Map();
  }

  async getOrFetch(key, fetcher) {
    const now = Date.now();
    const existing = this.cache.get(key);

    if (existing && existing.expiry > now) {
      // BUG: Returns raw reference! Caller mutations corrupt internal store
      return existing.value;
    }

    // BUG: Missing in-flight Promise deduplication! Concurrent calls execute fetcher multiple times
    const val = await fetcher(key);
    this.cache.set(key, { value: val, expiry: Date.now() + this.ttlMs });
    return val;
  }

  invalidate(key) {
    this.cache.delete(key);
  }

  clear() {
    this.cache.clear();
  }
}

module.exports = { AsyncCache };
"""

    solution = """class AsyncCache {
  constructor(ttlMs = 1000) {
    this.ttlMs = ttlMs;
    this.cache = new Map();
    this.inFlight = new Map();
  }

  async getOrFetch(key, fetcher) {
    const now = Date.now();
    const existing = this.cache.get(key);

    // 1. Cache Hit: Return defensive copy
    if (existing && existing.expiry > now) {
      return JSON.parse(JSON.stringify(existing.value));
    }

    // 2. In-Flight Hit: Wait for existing active fetch
    if (this.inFlight.has(key)) {
      const val = await this.inFlight.get(key);
      return JSON.parse(JSON.stringify(val));
    }

    // 3. Cache Miss: Execute single fetch and broadcast
    const fetchPromise = (async () => {
      try {
        const val = await fetcher(key);
        this.cache.set(key, { value: val, expiry: Date.now() + this.ttlMs });
        return val;
      } finally {
        this.inFlight.delete(key);
      }
    })();

    this.inFlight.set(key, fetchPromise);
    const res = await fetchPromise;
    return JSON.parse(JSON.stringify(res));
  }

  invalidate(key) {
    this.cache.delete(key);
    this.inFlight.delete(key);
  }

  clear() {
    this.cache.clear();
    this.inFlight.clear();
  }
}

module.exports = { AsyncCache };
"""

    visible_tests = [
        {
            "id": "v1",
            "name": "should deduplicate concurrent fetches for the same key (prevent cache stampede)",
            "testCode": """
            const cache = new AsyncCache(200);
            let fetchCount = 0;
            const slowFetcher = async (key) => {
              fetchCount++;
              await new Promise(r => setTimeout(r, 40));
              return { key, count: fetchCount };
            };

            const [r1, r2, r3] = await Promise.all([
              cache.getOrFetch('user:101', slowFetcher),
              cache.getOrFetch('user:101', slowFetcher),
              cache.getOrFetch('user:101', slowFetcher),
            ]);

            assert.strictEqual(fetchCount, 1, "Fetcher should be called exactly once for concurrent requests");
            assert.deepStrictEqual(r1, { key: 'user:101', count: 1 });
            assert.deepStrictEqual(r2, { key: 'user:101', count: 1 });
            assert.deepStrictEqual(r3, { key: 'user:101', count: 1 });
            """,
        },
        {
            "id": "v2",
            "name": "should isolate returned cached objects from external caller mutations",
            "testCode": """
            const cache = new AsyncCache(200);
            const fetcher = async () => ({ roles: ['viewer'], metadata: { active: true } });

            const firstResult = await cache.getOrFetch('user:roles', fetcher);
            firstResult.roles.push('superadmin');
            firstResult.metadata.active = false;

            const secondResult = await cache.getOrFetch('user:roles', fetcher);
            assert.deepStrictEqual(secondResult.roles, ['viewer'], "Cache must not be corrupted by caller mutation");
            assert.strictEqual(secondResult.metadata.active, true);
            """,
        },
        {
            "id": "v3",
            "name": "should refetch data once TTL expires",
            "testCode": """
            const cache = new AsyncCache(50);
            let fetchCount = 0;
            const fetcher = async () => ++fetchCount;

            assert.strictEqual(await cache.getOrFetch('counter', fetcher), 1);
            await new Promise(r => setTimeout(r, 70));
            assert.strictEqual(await cache.getOrFetch('counter', fetcher), 2, "Must refetch after TTL expires");
            """,
        },
    ]

    hidden_tests = [
        {
            "id": "h1",
            "name": "should clean up inFlight map even if fetcher throws an error",
            "testCode": """
            const cache = new AsyncCache(100);
            let attempts = 0;
            const failingFetcher = async () => {
              attempts++;
              throw new Error("Network timeout");
            };

            await assert.rejects(() => cache.getOrFetch('fail', failingFetcher), /Network timeout/);
            // Subsequent request should not be permanently locked
            await assert.rejects(() => cache.getOrFetch('fail', failingFetcher), /Network timeout/);
            assert.strictEqual(attempts, 2, "inFlight lock must be released on rejection");
            """,
        },
        {
            "id": "h2",
            "name": "should invalidate key and clear cache cleanly",
            "testCode": """
            const cache = new AsyncCache(500);
            let val = 10;
            await cache.getOrFetch('k1', async () => val);
            cache.invalidate('k1');
            val = 20;
            assert.strictEqual(await cache.getOrFetch('k1', async () => val), 20);
            """,
        },
    ]

    return {
        "category": "State Management & Concurrency",
        "context": "Async Cache Stampede Triage",
        "prompt": (
            "Diagnose and fix two critical defects in `AsyncCache`:\n\n"
            "**1. Cache Stampede (Concurrency Bug):**\n"
            "- Simultaneous calls to `getOrFetch(key, fetcher)` fire redundant `fetcher` calls.\n"
            "- Deduplicate in-flight Promises using an `inFlight` Map so all concurrent requests share the single active Promise.\n"
            "- Ensure `inFlight` key is deleted in a `finally` block even if the fetch fails.\n\n"
            "**2. State Mutation Leak (Defensive Copying):**\n"
            "- Returning cached references directly allows external callers to mutate internal cache state.\n"
            "- Defensively clone cached results before returning to callers."
        ),
        "codeType": "debugging",
        "archetype": "debugging",
        "competencies": ["state-management", "performance", "architecture"],
        "entryPoint": "AsyncCache",
        "starterCode": starter,
        "solutionCode": solution,
        "visibleTests": visible_tests,
        "hiddenTests": hidden_tests,
        "answerSpec": {
            "type": "code_output",
            "value": "AsyncCache debugging fix",
            "commonTrapTag": "race-condition-cache-stampede",
        },
        "answerPlain": "AsyncCache debugging fix",
        "answerDisplay": "AsyncCache.prototype.getOrFetch",
        "inputHint": "Open AsyncCache in VS Code, inspect failing concurrency tests, and implement inFlight deduplication",
        "checkpointHint": (
            "Store the active fetch Promise in an inFlight Map, and delete it inside a finally block."
        ),
        "commonTrapTag": "race-condition-cache-stampede",
        "steps": [
            {
                "latex": "\\text{Promise Sharing: } \\text{if (this.inFlight.has(key)) return this.inFlight.get(key)}",
                "explain": (
                    "Share pending fetch promises so concurrent readers await the same asynchronous network call."
                ),
            },
            {
                "latex": "\\text{Cleanup Invariant: } \\text{try \\{ ... \\} finally \\{ this.inFlight.delete(key); \\}}",
                "explain": (
                    "Always clean up in-flight entries inside a finally block to prevent permanent deadlocks on fetch errors."
                ),
            },
        ],
        "references": ["PRG-T01-C03-U05", "PRG-T01-C03-U04"],
        "form": "direct",
        "verify": {"solutionCode": solution, "trapValue": "fetchCount === 3 (duplicate concurrent fetches without inFlight Map)"},
    }
    

# ============================================================================
# ARCHETYPE 4: Code Modification & Refactoring — Legacy Subscription Billing (Level 3)
# ============================================================================
def build_refactor_legacy_subscription(rng: random.Random) -> dict:
    starter = """/**
 * LEGACY SUBSCRIPTION BILLING MODULE
 * 
 * MISSION:
 * 1. Maintain 100% backward compatibility with all existing legacy tests.
 * 2. Add support for the new 'family' plan:
 *    - Base price: $34.99 (includes 2 members).
 *    - Extra members: +$8.99 per member over 2, up to 6 members max.
 *    - If account.members > 6, throw RangeError('Family plan allows max 6 members').
 * 3. Add support for 'annualCommitment':
 *    - If account.annualCommitment is true, apply 15% discount on plan subtotal before tax.
 * 4. Refactor the tangled switch-statement into clean, decoupled architecture.
 */
function calculateMonthlyBill(account) {
  if (!account || !account.plan) {
    throw new TypeError('Account with valid plan required');
  }

  let planSubtotal = 0;
  if (account.plan === 'basic') {
    planSubtotal = 9.99;
  } else if (account.plan === 'pro') {
    planSubtotal = 24.99;
  } else if (account.plan === 'enterprise') {
    planSubtotal = 99.99;
    const seats = account.seats || 10;
    if (seats > 10) {
      planSubtotal += (seats - 10) * 5.00;
    }
  } else {
    throw new RangeError('Unknown subscription plan: ' + account.plan);
  }

  // TODO: Add support for 'family' plan and 'annualCommitment' discount
  const discount = 0;
  const taxableSubtotal = planSubtotal - discount;
  const tax = account.taxExempt ? 0 : Math.round(taxableSubtotal * 0.08 * 100) / 100;
  const total = Math.round((taxableSubtotal + tax) * 100) / 100;

  return { plan: account.plan, planSubtotal, discount, tax, total };
}

module.exports = { calculateMonthlyBill };
"""

    solution = """const PLAN_CONFIG = {
  basic: {
    basePrice: 9.99,
    calculateAddOns: () => 0,
  },
  pro: {
    basePrice: 24.99,
    calculateAddOns: () => 0,
  },
  enterprise: {
    basePrice: 99.99,
    calculateAddOns: (account) => {
      const seats = account.seats || 10;
      return seats > 10 ? (seats - 10) * 5.00 : 0;
    },
  },
  family: {
    basePrice: 34.99,
    calculateAddOns: (account) => {
      const members = account.members || 2;
      if (members > 6) {
        throw new RangeError('Family plan allows max 6 members');
      }
      return members > 2 ? (members - 2) * 8.99 : 0;
    },
  },
};

function calculateMonthlyBill(account) {
  if (!account || !account.plan) {
    throw new TypeError('Account with valid plan required');
  }

  const handler = PLAN_CONFIG[account.plan];
  if (!handler) {
    throw new RangeError('Unknown subscription plan: ' + account.plan);
  }

  const addOnCost = handler.calculateAddOns(account);
  const planSubtotal = Math.round((handler.basePrice + addOnCost) * 100) / 100;

  const discount = account.annualCommitment
    ? Math.round(planSubtotal * 0.15 * 100) / 100
    : 0;

  const taxableSubtotal = planSubtotal - discount;
  const tax = account.taxExempt ? 0 : Math.round(taxableSubtotal * 0.08 * 100) / 100;
  const total = Math.round((taxableSubtotal + tax) * 100) / 100;

  return { plan: account.plan, planSubtotal, discount, tax, total };
}

module.exports = { calculateMonthlyBill };
"""

    visible_tests = [
        {
            "id": "v1",
            "name": "legacy regression: should accurately bill basic, pro, and enterprise tiers",
            "testCode": """
            const basic = calculateMonthlyBill({ plan: 'basic' });
            assert.strictEqual(basic.planSubtotal, 9.99);
            assert.strictEqual(basic.total, 10.79);

            const pro = calculateMonthlyBill({ plan: 'pro', taxExempt: true });
            assert.strictEqual(pro.total, 24.99);

            const ent = calculateMonthlyBill({ plan: 'enterprise', seats: 15 });
            assert.strictEqual(ent.planSubtotal, 124.99, "Base 99.99 + 5 extra seats at $5 = 124.99");
            """,
        },
        {
            "id": "v2",
            "name": "new feature: should calculate family plan with member scaling and max 6 guard",
            "testCode": """
            const fam2 = calculateMonthlyBill({ plan: 'family', members: 2 });
            assert.strictEqual(fam2.planSubtotal, 34.99, "2 members included in base");

            const fam4 = calculateMonthlyBill({ plan: 'family', members: 4 });
            assert.strictEqual(fam4.planSubtotal, 52.97, "Base 34.99 + 2 extra members * 8.99 = 52.97");

            assert.throws(() => calculateMonthlyBill({ plan: 'family', members: 7 }), /RangeError/);
            """,
        },
        {
            "id": "v3",
            "name": "new feature: should apply 15% discount for annual commitment accounts",
            "testCode": """
            const annualFam = calculateMonthlyBill({
              plan: 'family',
              members: 4,
              annualCommitment: true,
            });
            assert.strictEqual(annualFam.planSubtotal, 52.97);
            assert.strictEqual(annualFam.discount, 7.95, "15% of 52.97 rounded to 2 decimals");
            assert.strictEqual(annualFam.tax, 3.60, "8% of 45.02 = 3.60");
            assert.strictEqual(annualFam.total, 48.62);
            """,
        },
    ]

    hidden_tests = [
        {
            "id": "h1",
            "name": "should throw TypeError if account or plan is missing",
            "testCode": """
            assert.throws(() => calculateMonthlyBill(null), /TypeError/);
            assert.throws(() => calculateMonthlyBill({}), /TypeError/);
            """,
        },
        {
            "id": "h2",
            "name": "should throw RangeError on unknown subscription plan",
            "testCode": """
            assert.throws(() => calculateMonthlyBill({ plan: 'ultimate_vip' }), /RangeError/);
            """,
        },
    ]

    return {
        "category": "Refactoring & Clean Architecture",
        "context": "Subscription Billing Engine",
        "prompt": (
            "Refactor `calculateMonthlyBill(account)` to support new business requirements without breaking existing plans:\n\n"
            "**New Plan: 'family':**\n"
            "- Base price: 34.99 USD (includes 2 members).\n"
            "- Add-on members: +8.99 USD per extra member over 2, up to 6 members max.\n"
            "- Guard Invariant: If `account.members > 6`, throw `RangeError('Family plan allows max 6 members')`.\n\n"
            "**New Feature: Annual Commitment:**\n"
            "- If `account.annualCommitment` is `true`, apply a 15% discount on the plan subtotal before tax.\n\n"
            "**Refactoring Objective:**\n"
            "- Keep all legacy plans (`basic`, `pro`, `enterprise`) 100% green.\n"
            "- Decouple the tangled `switch`/`if-else` statement into clean strategy configuration dictionaries."
        ),
        "codeType": "refactoring",
        "archetype": "refactoring",
        "competencies": ["architecture", "component-design", "typescript"],
        "entryPoint": "calculateMonthlyBill",
        "starterCode": starter,
        "solutionCode": solution,
        "visibleTests": visible_tests,
        "hiddenTests": hidden_tests,
        "answerSpec": {
            "type": "code_output",
            "value": "calculateMonthlyBill refactoring",
            "commonTrapTag": "legacy-coupling-regression",
        },
        "answerPlain": "calculateMonthlyBill refactoring",
        "answerDisplay": "calculateMonthlyBill(account)",
        "inputHint": "Refactor in VS Code, preserve existing plan behaviors, and add the family plan rule",
        "checkpointHint": (
            "Extract plan strategies or lookup tables to separate pricing calculation from invoice assembling."
        ),
        "commonTrapTag": "legacy-coupling-regression",
        "steps": [
            {
                "latex": "\\text{Strategy Pattern: } \\text{const PLAN_CONFIG = \\{ basic: \\{...\\}, family: \\{...\\} \\}}",
                "explain": (
                    "Replace nested if/else ladders with a dictionary of strategy configurations for easy extensibility."
                ),
            },
            {
                "latex": "\\text{Discount Invariant: } \\text{taxableSubtotal = planSubtotal - discount}",
                "explain": (
                    "Apply the annual commitment discount to the subtotal before computing sales tax."
                ),
            },
        ],
        "references": ["PRG-T01-C03-U07", "PRG-T01-C03-U01"],
        "form": "direct",
        "verify": {"solutionCode": solution, "trapValue": "RangeError: Unknown subscription plan: family"},
    }


# ============================================================================
# ARCHETYPE 5: Project-Based — Event-Driven Rate Limiter (Level 4)
# ============================================================================
def build_project_rate_limiter(rng: random.Random) -> dict:
    starter = """const EventEmitter = require('node:events');

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
"""

    solution = """const EventEmitter = require('node:events');

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
"""

    visible_tests = [
        {
            "id": "v1",
            "name": "should allow up to maxRequests within window and decrement remaining",
            "testCode": """
            const limiter = new RateLimiter({ maxRequests: 3, windowMs: 150 });
            const r1 = limiter.consume('client:A');
            const r2 = limiter.consume('client:A');
            const r3 = limiter.consume('client:A');

            assert.strictEqual(r1.allowed, true);
            assert.strictEqual(r1.remaining, 2);
            assert.strictEqual(r2.remaining, 1);
            assert.strictEqual(r3.remaining, 0);

            const r4 = limiter.consume('client:A');
            assert.strictEqual(r4.allowed, false);
            assert.strictEqual(r4.remaining, 0);
            assert.ok(r4.resetMs > 0, "resetMs should indicate time until window slides");
            """,
        },
        {
            "id": "v2",
            "name": "should emit 'blocked' event on rate limit breach",
            "testCode": """
            const limiter = new RateLimiter({ maxRequests: 1, windowMs: 100 });
            let blockedKey = null;
            let blockedReset = null;

            limiter.on('blocked', (key, resetMs) => {
              blockedKey = key;
              blockedReset = resetMs;
            });

            limiter.consume('ip:192.168.1.1'); // allowed
            limiter.consume('ip:192.168.1.1'); // blocked!

            assert.strictEqual(blockedKey, 'ip:192.168.1.1');
            assert.ok(blockedReset > 0);
            """,
        },
        {
            "id": "v3",
            "name": "should slide window over time and restore allowance",
            "testCode": """
            const limiter = new RateLimiter({ maxRequests: 1, windowMs: 50 });
            assert.strictEqual(limiter.consume('user:99').allowed, true);
            assert.strictEqual(limiter.consume('user:99').allowed, false);

            await new Promise(r => setTimeout(r, 65));
            assert.strictEqual(limiter.consume('user:99').allowed, true, "Allowance restored after window expires");
            """,
        },
    ]

    hidden_tests = [
        {
            "id": "h1",
            "name": "should track separate keys independently",
            "testCode": """
            const limiter = new RateLimiter({ maxRequests: 1, windowMs: 100 });
            assert.strictEqual(limiter.consume('user:1').allowed, true);
            assert.strictEqual(limiter.consume('user:1').allowed, false);
            assert.strictEqual(limiter.consume('user:2').allowed, true, "Separate keys must have independent quotas");
            """,
        },
        {
            "id": "h2",
            "name": "should reset quota when reset(key) is invoked",
            "testCode": """
            const limiter = new RateLimiter({ maxRequests: 1, windowMs: 500 });
            limiter.consume('keyA');
            limiter.reset('keyA');
            assert.strictEqual(limiter.consume('keyA').allowed, true);
            """,
        },
    ]

    return {
        "category": "Subsystem Architecture & Events",
        "context": "API Gateway Rate Limiter",
        "prompt": (
            "Build an event-driven `RateLimiter` class implementing a sliding window algorithm extending `EventEmitter`.\n\n"
            "**Constructor:**\n"
            "- `new RateLimiter({ maxRequests = 5, windowMs = 1000 })`\n\n"
            "**Methods & Invariants:**\n"
            "- `consume(key)`: Allows up to `maxRequests` within `windowMs`.\n"
            "- Returns `{ allowed: true, remaining: number, resetMs: number }`.\n"
            "- On limit breach: emit `'blocked'` event with `(key, resetMs)` and return `{ allowed: false, remaining: 0, resetMs }`.\n"
            "- `reset(key)`: Clears recorded history for the specified key."
        ),
        "codeType": "project-based",
        "archetype": "project-based",
        "competencies": ["state-management", "component-design", "performance"],
        "entryPoint": "RateLimiter",
        "starterCode": starter,
        "solutionCode": solution,
        "visibleTests": visible_tests,
        "hiddenTests": hidden_tests,
        "answerSpec": {
            "type": "code_output",
            "value": "RateLimiter implementation",
            "commonTrapTag": "rate-limit-window-leak",
        },
        "answerPlain": "RateLimiter implementation",
        "answerDisplay": "RateLimiter subsystem",
        "inputHint": "Implement RateLimiter in VS Code extending EventEmitter with sliding timestamp array",
        "checkpointHint": (
            "Filter timestamp arrays to drop entries older than windowMs before evaluating length."
        ),
        "commonTrapTag": "rate-limit-window-leak",
        "steps": [
            {
                "latex": "\\text{Sliding Window: } \\text{timestamps.filter(t => now - t < this.windowMs)}",
                "explain": (
                    "Discard expired timestamps older than the sliding window interval to reclaim quota and memory."
                ),
            },
            {
                "latex": "\\text{Event Dispatch: } \\text{this.emit('blocked', key, resetMs)}",
                "explain": (
                    "Trigger real-time telemetry events allowing consumers to log or trigger blacklists."
                ),
            },
        ],
        "references": ["PRG-T01-C03-U08", "PRG-T01-C03-U01"],
        "form": "direct",
        "verify": {"solutionCode": solution, "trapValue": "expired timestamps never evicted from window"},
    }


# ============================================================================
# ARCHETYPE 1: Problem Solving — Memoize Utility (Level 2)
# ============================================================================
def build_kata_memoize(rng: random.Random) -> dict:
    starter = """function memoize(fn, resolver) {
  // TODO: Cache results using a Map and resolver for cache keys
}

module.exports = { memoize };
"""

    solution = """function memoize(fn, resolver) {
  const cache = new Map();

  function memoized(...args) {
    const key = typeof resolver === 'function' ? resolver.apply(this, args) : args[0];
    if (cache.has(key)) {
      return cache.get(key);
    }
    const result = fn.apply(this, args);
    cache.set(key, result);
    return result;
  }

  memoized.cache = cache;
  return memoized;
}

module.exports = { memoize };
"""

    visible_tests = [
        {
            "id": "v1",
            "name": "should cache expensive computation and only execute original function once per key",
            "testCode": """
            let runs = 0;
            const fib = memoize((n) => {
              runs++;
              return n <= 1 ? n : n * 2;
            });
            assert.strictEqual(fib(5), 10);
            assert.strictEqual(fib(5), 10);
            assert.strictEqual(runs, 1, "Cached call should not re-run original function");
            """,
        },
        {
            "id": "v2",
            "name": "should correctly cache falsy return values (0, false, null, '') without re-evaluating",
            "testCode": """
            let calls = 0;
            const zeroFn = memoize((x) => {
              calls++;
              return 0;
            });
            assert.strictEqual(zeroFn('a'), 0);
            assert.strictEqual(zeroFn('a'), 0);
            assert.strictEqual(calls, 1, "0 is falsy but must be treated as a valid cache hit");
            """,
        },
    ]

    hidden_tests = [
        {
            "id": "h1",
            "name": "should use resolver function to compute composite cache keys",
            "testCode": """
            let runs = 0;
            const add = memoize((a, b) => { runs++; return a + b; }, (a, b) => `${a}:${b}`);
            assert.strictEqual(add(1, 2), 3);
            assert.strictEqual(add(1, 2), 3);
            assert.strictEqual(runs, 1);
            assert.strictEqual(add(2, 1), 3);
            assert.strictEqual(runs, 2, "Different key order should trigger computation");
            """,
        },
        {
            "id": "h2",
            "name": "should expose underlying cache Map on returned function",
            "testCode": """
            const fn = memoize((x) => x);
            assert.ok(fn.cache instanceof Map);
            """,
        },
    ]

    return {
        "category": "Reusable Generic Utilities",
        "context": "Function Caching & Memoization",
        "prompt": (
            "Implement `memoize(fn, resolver)` in JavaScript.\n\n"
            "**Behavioral Requirements:**\n"
            "- Returns a memoized function caching the result of calling `fn`.\n"
            "- If `resolver` is provided, use it to compute the cache key; otherwise default to `args[0]`.\n"
            "- Correctly cache falsy return values (`0`, `false`, `null`, `''`) without re-evaluating.\n"
            "- Expose the underlying cache `Map` on `memoized.cache`."
        ),
        "codeType": "problem-solving",
        "archetype": "problem-solving",
        "competencies": ["state-management", "performance"],
        "entryPoint": "memoize",
        "starterCode": starter,
        "solutionCode": solution,
        "visibleTests": visible_tests,
        "hiddenTests": hidden_tests,
        "answerSpec": {
            "type": "code_output",
            "value": "memoize implementation",
            "commonTrapTag": "unhandled-falsy-cache",
        },
        "answerPlain": "memoize implementation",
        "answerDisplay": "memoize(fn, resolver)",
        "inputHint": "Implement in Cursor / VS Code and run tests in terminal",
        "checkpointHint": (
            "Use Map.prototype.has(key) rather than checking if cache[key] is truthy to avoid re-evaluating falsy values."
        ),
        "commonTrapTag": "unhandled-falsy-cache",
        "steps": [
            {
                "latex": "\\text{Cache Data Structure: } \\text{const cache = new Map()}",
                "explain": (
                    "Use a Map instance to store cached values. Use 'cache.has(key)' to detect cached results "
                    "so that falsy returns like 0 or false are not mistakenly treated as cache misses."
                ),
            },
            {
                "latex": "\\text{Cache Key Resolution: } \\text{typeof resolver === 'function' ? resolver(...) : args[0]}",
                "explain": (
                    "If a custom resolver function is passed, call it with the arguments to compute the key; "
                    "otherwise default to args[0]."
                ),
            },
        ],
        "references": ["PRG-T01-C03-U05", "PRG-T01-C03-U04"],
        "form": "direct",
        "verify": {"solutionCode": solution, "trapValue": "if (cache.get(key)) treats falsy 0 as cache miss"},
    }


TEMPLATES = [
    {
        "key": "order_pricing_pipeline",
        "level": 2,
        "verificationLevel": "machine-verified",
        "trapTag": "tax-discount-order-inversion",
        "forms": {"direct": {"level": 2, "skill": "PRG-ARCH-PIPELINE-PRICING"}},
        "build": build_order_pricing_pipeline,
    },
    {
        "key": "debugging_async_cache",
        "level": 3,
        "verificationLevel": "machine-verified",
        "trapTag": "race-condition-cache-stampede",
        "forms": {"direct": {"level": 3, "skill": "PRG-ARCH-ASYNC-CACHE-RACE"}},
        "build": build_debugging_async_cache,
    },
    {
        "key": "refactor_legacy_subscription",
        "level": 3,
        "verificationLevel": "machine-verified",
        "trapTag": "legacy-coupling-regression",
        "forms": {"direct": {"level": 3, "skill": "PRG-ARCH-REFACTOR-SUBSCRIPTION"}},
        "build": build_refactor_legacy_subscription,
    },
    {
        "key": "project_rate_limiter",
        "level": 4,
        "verificationLevel": "machine-verified",
        "trapTag": "rate-limit-window-leak",
        "forms": {"direct": {"level": 4, "skill": "PRG-ARCH-PROJECT-RATE-LIMITER"}},
        "build": build_project_rate_limiter,
    },
    {
        "key": "kata_debounce",
        "level": 2,
        "verificationLevel": "machine-verified",
        "is_kata": True,
        "trapTag": "timer-cancellation-flaw",
        "forms": {"direct": {"level": 2, "skill": "PRG-KATA-DEBOUNCE"}},
        "build": build_kata_debounce,
    },
    {
        "key": "kata_groupby",
        "level": 1,
        "verificationLevel": "machine-verified",
        "is_kata": True,
        "trapTag": "empty-input-handling",
        "forms": {"direct": {"level": 1, "skill": "PRG-KATA-GROUPBY"}},
        "build": build_kata_groupby,
    },
    {
        "key": "kata_memoize",
        "level": 2,
        "verificationLevel": "machine-verified",
        "is_kata": True,
        "trapTag": "unhandled-falsy-cache",
        "forms": {"direct": {"level": 2, "skill": "PRG-KATA-MEMOIZE"}},
        "build": build_kata_memoize,
    },
]
