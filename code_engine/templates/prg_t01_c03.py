# -*- coding: utf-8 -*-
"""
Kata and Utility Toolkit Problem Templates for PRG-T01-C03:
Problem Solving & Utility Toolkit (debounce, groupBy, memoize, deepClone).

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
]


# ============================================================================
# KATA 1: Debounce Function (Level 2 Standard Exam)
# ============================================================================
def build_kata_debounce(rng: random.Random) -> dict:
    default_delay = rng.choice([50, 60, 80])

    starter = """function debounce(fn, delay) {
  let timer = null;

  return function(...args) {
    // TODO: Clear previous timer and schedule new invocation
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
            debounced(2); // resets timer!
            await new Promise(r => setTimeout(r, {default_delay // 2}));
            assert.strictEqual(value, 0, "Should still be 0 before second delay expires");
            await new Promise(r => setTimeout(r, {default_delay // 2 + 20}));
            assert.strictEqual(value, 2, "Should record latest value 2");
            """,
        },
    ]

    hidden_tests = [
        {
            "id": "h1",
            "name": "should preserve execution 'this' context and multiple arguments",
            "testCode": f"""
            let received = null;
            const ctx = {{ multiplier: 10 }};
            const debounced = debounce(function(a, b) {{
              received = (this.multiplier || 1) * (a + b);
            }}, 30);
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
        "category": "Reusable Generic Utilities",
        "context": "Timing & High-Order Functions",
        "prompt": (
            "Implement a robust 'debounce(fn, delay)' utility function in JavaScript. "
            "The debounced function must delay invoking 'fn' until after 'delay' milliseconds have elapsed "
            "since the last time it was called, clearing any prior timers and preserving 'this' and arguments. "
            "You can write and test your solution in Cursor / VS Code or in the editor below."
        ),
        "codeType": "kata",
        "entryPoint": "debounce",
        "starterCode": starter,
        "solutionCode": solution,
        "visibleTests": visible_tests,
        "hiddenTests": hidden_tests,
        "answerSpec": {
            "type": "code_output",
            "value": "debounce function implementation",
            "commonTrapTag": "timer-cancellation-flaw",
        },
        "answerPlain": "debounce implementation",
        "answerDisplay": "debounce(fn, delay)",
        "inputHint": "Implement in Cursor / VS Code or in Studio and click Run Test Suite",
        "checkpointHint": (
            "Keep a single closure timer variable. Call clearTimeout(timer) on every invocation, then setTimeout."
        ),
        "commonTrapTag": "timer-cancellation-flaw",
        "steps": [
            {
                "latex": "\\text{Closure Scope: } \\text{let timer = null}",
                "explain": (
                    "Define a persistent 'timer' reference in the outer lexical scope. "
                    "Each invocation of the returned wrapper must clear the pending timer via 'clearTimeout(timer)'."
                ),
            },
            {
                "latex": "\\text{Context Preservation: } \\text{fn.apply(this, args)}",
                "explain": (
                    "Ensure 'this' and 'args' are passed faithfully to the target function when the timer fires "
                    "using an arrow function callback or caching 'const ctx = this'."
                ),
            },
        ],
        "references": ["PRG-T01-C03-U05", "PRG-T01-C01-U02"],
        "verify": {"solutionCode": solution},
    }


# ============================================================================
# KATA 2: GroupBy Array Transformation (Level 1 Foundation)
# ============================================================================
def build_kata_groupby(rng: random.Random) -> dict:
    starter = """function groupBy(array, iteratee) {
  // TODO: Return an object with keys generated by iteratee and values as arrays of items
}

module.exports = { groupBy };
"""

    solution = """function groupBy(array, iteratee) {
  if (!Array.isArray(array)) return {};
  const getKey = typeof iteratee === 'function' ? iteratee : (item) => item[iteratee];

  const result = {};
  for (const item of array) {
    const key = getKey(item);
    if (!Object.prototype.hasOwnProperty.call(result, key)) {
      result[key] = [];
    }
    result[key].push(item);
  }
  return result;
}

module.exports = { groupBy };
"""

    visible_tests = [
        {
            "id": "v1",
            "name": "should group elements by a property name string",
            "testCode": """
            const items = [
              { stage: 'dev', name: 'app1' },
              { stage: 'prod', name: 'app2' },
              { stage: 'dev', name: 'app3' },
            ];
            const grouped = groupBy(items, 'stage');
            assert.deepStrictEqual(grouped.dev, [
              { stage: 'dev', name: 'app1' },
              { stage: 'dev', name: 'app3' },
            ]);
            assert.deepStrictEqual(grouped.prod, [
              { stage: 'prod', name: 'app2' },
            ]);
            """,
        },
        {
            "id": "v2",
            "name": "should group elements by a custom callback function",
            "testCode": """
            const numbers = [6.1, 4.2, 6.3];
            const grouped = groupBy(numbers, Math.floor);
            assert.deepStrictEqual(grouped['6'], [6.1, 6.3]);
            assert.deepStrictEqual(grouped['4'], [4.2]);
            """,
        },
    ]

    hidden_tests = [
        {
            "id": "h1",
            "name": "should return empty object for empty array or non-array input without crashing",
            "testCode": """
            assert.deepStrictEqual(groupBy([], 'any'), {});
            assert.deepStrictEqual(groupBy(null, 'any'), {});
            assert.deepStrictEqual(groupBy(undefined, 'any'), {});
            """,
        },
        {
            "id": "h2",
            "name": "should group under 'undefined' string key if property does not exist on item",
            "testCode": """
            const items = [{ a: 1 }, { b: 2 }];
            const grouped = groupBy(items, 'a');
            assert.strictEqual(grouped['1'].length, 1);
            assert.strictEqual(grouped['undefined'].length, 1);
            """,
        },
    ]

    return {
        "category": "Array Transformations",
        "context": "Collection Grouping & Aggregation",
        "prompt": (
            "Implement 'groupBy(array, iteratee)' in JavaScript. "
            "It splits a collection into sets, grouped by the result of running each value through 'iteratee'. "
            "The 'iteratee' can be either a function (which receives each element) or a string property name. "
            "Return an object where keys are the grouping identifiers and values are arrays of matching items."
        ),
        "codeType": "kata",
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
        "answerDisplay": "groupBy(array, iteratee)",
        "inputHint": "Implement in Cursor / VS Code or in Studio and click Run Test Suite",
        "checkpointHint": (
            "Check if iteratee is a function or a property key. Initialize an empty array for each unseen key."
        ),
        "commonTrapTag": "empty-input-handling",
        "steps": [
            {
                "latex": "\\text{Key Resolver: } \\text{typeof iteratee === 'function'}",
                "explain": (
                    "Inspect the type of 'iteratee': if a function, invoke 'iteratee(item)'; "
                    "if a string, resolve by property lookup 'item[iteratee]'."
                ),
            },
            {
                "latex": "\\text{Accumulator: } \\text{result[key].push(item)}",
                "explain": (
                    "Initialize 'result[key] = []' if the key does not exist yet, then push the current element into that array."
                ),
            },
        ],
        "references": ["PRG-T01-C03-U02"],
        "verify": {"solutionCode": solution},
    }


# ============================================================================
# KATA 3: Memoize Utility with Cache (Level 2 Standard Exam)
# ============================================================================
def build_kata_memoize(rng: random.Random) -> dict:
    starter = """function memoize(fn, resolver) {
  // TODO: Cache results of function calls based on arguments
}

module.exports = { memoize };
"""

    solution = """function memoize(fn, resolver) {
  const cache = new Map();

  const memoized = function(...args) {
    const key = typeof resolver === 'function' ? resolver.apply(this, args) : args[0];
    if (cache.has(key)) {
      return cache.get(key);
    }
    const result = fn.apply(this, args);
    cache.set(key, result);
    return result;
  };

  memoized.cache = cache;
  return memoized;
}

module.exports = { memoize };
"""

    visible_tests = [
        {
            "id": "v1",
            "name": "should calculate result once and return cached value on subsequent calls with same argument",
            "testCode": """
            let runs = 0;
            const square = memoize((n) => { runs++; return n * n; });
            assert.strictEqual(square(5), 25);
            assert.strictEqual(square(5), 25);
            assert.strictEqual(runs, 1, "Underlying function must only run once for input 5");
            assert.strictEqual(square(4), 16);
            assert.strictEqual(runs, 2, "Underlying function must run for input 4");
            """,
        },
        {
            "id": "v2",
            "name": "should correctly cache falsy return values (e.g. 0, false, null, '')",
            "testCode": """
            let runs = 0;
            const getFalsy = memoize((type) => {
              runs++;
              if (type === 'zero') return 0;
              if (type === 'bool') return false;
              if (type === 'empty') return '';
              return null;
            });
            assert.strictEqual(getFalsy('zero'), 0);
            assert.strictEqual(getFalsy('zero'), 0);
            assert.strictEqual(runs, 1, "Should not recompute when return value is 0");
            """,
        },
    ]

    hidden_tests = [
        {
            "id": "h1",
            "name": "should support custom resolver for multiple arguments and preserve 'this' context",
            "testCode": """
            let runs = 0;
            const add = memoize(
              function(a, b) { runs++; return a + b + (this.offset || 0); },
              (a, b) => `${a},${b}`
            );
            const ctx = { offset: 10 };
            assert.strictEqual(add.call(ctx, 2, 3), 15);
            assert.strictEqual(add.call(ctx, 2, 3), 15);
            assert.strictEqual(runs, 1, "Must cache multi-arg call using resolver key");
            """,
        },
    ]

    return {
        "category": "Reusable Generic Utilities",
        "context": "Function Caching & Memoization",
        "prompt": (
            "Implement 'memoize(fn, resolver)' in JavaScript. "
            "It returns a memoized function that caches the result of calling 'fn'. "
            "If 'resolver' is provided, it determines the cache key for storing the result based on the arguments supplied. "
            "By default, the first argument provided to the memoized function is used as the map cache key. "
            "Ensure that falsy return values (0, false, null, '') are properly cached without re-evaluating."
        ),
        "codeType": "kata",
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
        "inputHint": "Implement in Cursor / VS Code or in Studio and click Run Test Suite",
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
                    "otherwise default to 'args[0]'."
                ),
            },
        ],
        "references": ["PRG-T01-C03-U05", "PRG-T01-C03-U04"],
        "verify": {"solutionCode": solution},
    }


TEMPLATES = [
    {
        "key": "kata_debounce",
        "level": 2,
        "trapTag": "timer-cancellation-flaw",
        "build": build_kata_debounce,
    },
    {
        "key": "kata_groupby",
        "level": 1,
        "trapTag": "empty-input-handling",
        "build": build_kata_groupby,
    },
    {
        "key": "kata_memoize",
        "level": 2,
        "trapTag": "unhandled-falsy-cache",
        "build": build_kata_memoize,
    },
]
