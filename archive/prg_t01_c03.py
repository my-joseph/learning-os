# -*- coding: utf-8 -*-
"""
Instructional content for PRG-T01-C03 Units (U01-U08).
Follows 'Learning System — AI Implementation Rules'.
No emojis in page body blocks.
"""

UNITS_C03 = {
    "PRG-T01-C03-U01": {
        "title": "Problem Decomposition",
        "chapter": "C03",
        "order": 1,
        "prereq": "PRG-T01-C01 (JS Runtime), PRG-T01-C02 (TypeScript Modeling)",
        "source": "R003 — MDN – JavaScript Guide (Functions) & R004 — TypeScript Handbook (More on Functions). Verified accessible (HTTP 200).",
        "concepts_title": "Engineering Strategy & Data Transformation Patterns",
        "concepts": [
            "Specify the Data Contract Before Writing Logic: Tutorial-dependent coding starts by typing loops immediately; engineering starts by defining exact input types, output types, invariants, and edge cases. Once the intermediate data types ('RawLogLine -> ParsedEvent -> AggregatedSummary') are defined, each step becomes trivial to write.",
            "Separate Pure Core Logic from Impure I/O Boundaries: Isolate deterministic data transformations (pure functions that take values and return new values with no side effects) from impure side effects (network fetches, file reads, clocks, random IDs, DOM mutations). Pure functions can be composed and unit-tested without mocks.",
            "Top-Down Pipeline Decomposition: Break any multi-step requirement into 3-5 small single-responsibility functions: (1) Parse/Validate inputs, (2) Normalize/Filter records, (3) Compute/Aggregate domain results, and (4) Format output."
        ],
        "code_lang": "typescript",
        "code": """export interface RawInvoiceRow {
  readonly id: string;
  readonly amountCents: number;
  readonly status: "paid" | "void" | "overdue";
}

export interface InvoiceReport {
  readonly paidCount: number;
  readonly overdueCount: number;
  readonly netRevenueCents: number;
}

// Step 1: Pure predicate
export const isActiveInvoice = (row: RawInvoiceRow): boolean =>
  row.status !== "void" && row.amountCents >= 0;

// Step 2: Pure aggregation over validated records
export function summarizeInvoices(rows: readonly RawInvoiceRow[]): InvoiceReport {
  const active = rows.filter(isActiveInvoice);
  return active.reduce<InvoiceReport>(
    (acc, row) => ({
      paidCount: acc.paidCount + (row.status === "paid" ? 1 : 0),
      overdueCount: acc.overdueCount + (row.status === "overdue" ? 1 : 0),
      netRevenueCents: acc.netRevenueCents + (row.status === "paid" ? row.amountCents : 0)
    }),
    { paidCount: 0, overdueCount: 0, netRevenueCents: 0 }
  );
}
""",
        "exercise": [
            "Implementation Task: Decompose a requirement that parses CSV-like transaction strings ('\"2026-11-01,DEPOSIT,1500\"'), discards malformed lines, and computes daily net balances into three pure, typed functions.",
            "Debugging Task: Refactor a monolithic 50-line function that mixes 'fetch()', 'new Date()', array mutations, and string formatting into a pure transformation core and a thin impure caller."
        ],
        "recall": [
            ("What two properties define a pure function, and why do pure functions simplify problem decomposition?", "1. Deterministic output (identical inputs always produce identical outputs), and 2. No side effects (no mutation of external state, arguments, or I/O). They can be reasoned about, composed, and tested in complete isolation."),
            ("Why should you define intermediate TypeScript types between pipeline stages before implementing function bodies?", "Intermediate types act as explicit checkpoints that verify each stage's output matches the next stage's expected input, catching design mismatches before writing implementation code."),
            ("How do you make a function that depends on the current time ('new Date()') or random numbers ('Math.random()') deterministic and easy to test?", "Pass the timestamp or random generator in as an explicit parameter with a default value (e.g., 'now: Date = new Date()') so callers and tests control the input."),
            ("What is a strong signal that a single function is doing too much and needs decomposition?", "When you need words like 'and'/'then' to describe what it does, when it mixes I/O with business calculations, or when it mutates variables across multiple nested loops.")
        ]
    },
    "PRG-T01-C03-U02": {
        "title": "Array Transformations",
        "chapter": "C03",
        "order": 2,
        "prereq": "PRG-T01-C03-U01 (Problem Decomposition)",
        "source": "R003 — MDN – JavaScript Guide (Indexed collections — Array methods) & R004 — TypeScript Handbook. Verified accessible (HTTP 200).",
        "concepts_title": "Engineering Strategy & Data Transformation Patterns",
        "concepts": [
            "Mutating vs. Non-Mutating Array Methods: Legacy methods like '.sort()', '.reverse()', and '.splice()' mutate the original array in place—causing subtle bugs when two components share the same array reference. Prefer non-mutating ES2023+ methods ('.toSorted()', '.toReversed()', '.toSpliced()', '.with()') or copy first ('[...items].sort(...)').",
            "Choosing the Right Operator ('map' vs. 'filter' vs. 'flatMap' vs. 'reduce'): Use '.map(fn)' for 1-to-1 projection; '.filter(pred)' for subset selection; '.flatMap(fn)' for 1-to-many or 0-or-1 conditional mapping+flattening in a single pass; and '.reduce(fn, init)' when folding an array into a single scalar, object, or grouped structure (always provide the initial accumulator value!).",
            "Short-Circuiting Predicates ('some', 'every', 'find'): Unlike '.filter()' (which scans the entire array and allocates a new array), '.some()', '.every()', and '.find()' stop iterating as soon as the condition is decided."
        ],
        "code_lang": "typescript",
        "code": """export interface Order {
  readonly id: string;
  readonly tags: readonly string[];
  readonly total: number;
}

// 1. Immutable sorting without mutating the caller's readonly array
export function sortOrdersByTotalDesc(orders: readonly Order[]): Order[] {
  return [...orders].sort((a, b) => b.total - a.total);
}

// 2. Using flatMap to extract and normalize nested tags in a single pass
export function extractUniqueNormalizedTags(orders: readonly Order[]): string[] {
  const allTags = orders.flatMap(order =>
    order.tags.map(tag => tag.trim().toLowerCase()).filter(Boolean)
  );
  return Array.from(new Set(allTags));
}
""",
        "exercise": [
            "Implementation Task: Write a pipeline that takes 'readonly Department[]' (each containing 'employees: readonly Employee[]'), flattens active employees using '.flatMap()', sorts them immutably by salary descending, and calculates total payroll with '.reduce()'.",
            "Debugging Task: Fix three bugs in a snippet: (1) '[10, 2, 30].sort()' sorting numbers lexicographically as strings, (2) 'items.sort(...)' mutating a 'readonly' input array, and (3) 'items.reduce((a, b) => a + b)' throwing 'TypeError: Reduce of empty array with no initial value'."
        ],
        "recall": [
            ("Why does '[10, 2, 30].sort()' return '[10, 2, 30]' instead of '[2, 10, 30]' in JavaScript?", "Because 'Array.prototype.sort()' converts elements to UTF-16 strings by default when no comparator function is provided. For numeric sorting, always pass '(a, b) => a - b'."),
            ("What happens if you call 'arr.reduce((acc, x) => acc + x)' on an empty array '[]' without passing an initial value?", "It throws a runtime 'TypeError: Reduce of empty array with no initial value'. Always provide an explicit initial value (e.g., '0')."),
            ("How does 'arr.flatMap(fn)' save both code and memory allocations when filtering and mapping simultaneously?", "Returning '[]' from 'flatMap' drops an item while returning '[transformed]' keeps and maps it in a single pass, avoiding an intermediate array allocation from '.filter().map()'."),
            ("Why helps annotating array parameters as 'readonly T[]' in TypeScript?", "It prevents the function body from accidentally calling in-place mutating methods like '.push()', '.pop()', '.splice()', or '.sort()' on the caller's array.")
        ]
    },
    "PRG-T01-C03-U03": {
        "title": "Object Transformations",
        "chapter": "C03",
        "order": 3,
        "prereq": "PRG-T01-C03-U02 (Array Transformations)",
        "source": "R003 — MDN – JavaScript Guide (Working with objects) & R004 — TypeScript Handbook (Object Types). Verified accessible (HTTP 200).",
        "concepts_title": "Engineering Strategy & Data Transformation Patterns",
        "concepts": [
            "The Entries Pipeline ('Object.entries' -> Array Methods -> 'Object.fromEntries'): Plain JavaScript objects lack '.map()' and '.filter()'. Convert an object into '[key, value]' pairs with 'Object.entries(obj)', transform or filter the entries using array methods, and rebuild a new immutable object with 'Object.fromEntries(...)'.",
            "Shallow Copy vs. Deep Copy ('{ ...obj }' vs. 'structuredClone'): Object spread ('{ ...user, role: \"admin\" }') and 'Object.assign' only copy top-level property references (shallow copy). Mutating 'copy.preferences.theme' still mutates 'original.preferences.theme'! Use immutable nested spreads for targeted state updates or 'structuredClone(obj)' for true deep copies of data.",
            "Safe Property Omission via Rest Destructuring: Instead of mutating an object with 'delete obj.password', use rest destructuring ('const { password, ...publicUser } = user;') to create a clean object without the omitted key."
        ],
        "code_lang": "typescript",
        "code": """// 1. Filtering nullish values from an object via Object.entries + Object.fromEntries
export function compactObject<T extends Record<string, unknown>>(
  obj: T
): Partial<T> {
  const keptEntries = Object.entries(obj).filter(
    ([, value]) => value !== null && value !== undefined
  );
  return Object.fromEntries(keptEntries) as Partial<T>;
}

// 2. Immutable nested state update without mutating original references
export interface AccountState {
  readonly id: string;
  readonly settings: {
    readonly notifications: boolean;
    readonly theme: "light" | "dark";
  };
}

export function toggleNotifications(state: AccountState): AccountState {
  return {
    ...state,
    settings: {
      ...state.settings,
      notifications: !state.settings.notifications
    }
  };
}
""",
        "exercise": [
            "Implementation Task: Write a 'mapObjectValues<T extends Record<string, V>, V, R>(obj: T, fn: (val: V, key: string) => R): Record<keyof T, R>' function using 'Object.entries' and 'Object.fromEntries'.",
            "Debugging Task: Diagnose and fix a state-corruption bug where 'const draft = { ...originalOrder }; draft.lineItems.push(newItem);' silently mutated 'originalOrder.lineItems'."
        ],
        "recall": [
            ("Why does 'const copy = { ...original }; copy.nested.count += 1;' mutate 'original.nested.count'?", "Because object spread ('{ ...original }') performs a shallow copy: it copies top-level primitive values, but copies only the memory reference for nested objects or arrays."),
            ("How does 'structuredClone(value)' improve upon the old 'JSON.parse(JSON.stringify(value))' deep-clone workaround?", "'structuredClone' preserves 'Date' objects, 'RegExp', 'Map', 'Set', 'ArrayBuffer', and circular references, whereas 'JSON.stringify' turns 'Date' into strings, strips 'undefined', and throws on circular references."),
            ("Why does TypeScript infer 'Object.keys(obj)' as 'string[]' instead of '(keyof T)[]'?", "Because structural subtyping allows an object typed as 'T' to possess extra runtime properties beyond those known at compile time in 'T'."),
            ("Why is 'const { secret, ...rest } = config' preferred over 'delete config.secret'?", "Rest destructuring leaves the input 'config' completely unmutated and returns a new object 'rest' whose static TypeScript type automatically omits the 'secret' property.")
        ]
    },
    "PRG-T01-C03-U04": {
        "title": "Map, Set and Common Data Structures",
        "chapter": "C03",
        "order": 4,
        "prereq": "PRG-T01-C03-U02 (Array Transformations), PRG-T01-C03-U03 (Object Transformations)",
        "source": "R003 — MDN – JavaScript Guide (Keyed collections — Map, WeakMap, Set, WeakSet). Verified accessible (HTTP 200).",
        "concepts_title": "Engineering Strategy & Data Transformation Patterns",
        "concepts": [
            "Eliminating O(n^2) Lookups with 'Map' and 'Set': Calling 'array.find(...)' or 'array.includes(...)' inside another loop results in quadratic O(n * m) time complexity. Indexing records into a 'Map<Key, Value>' or 'Set<Key>' first reduces each lookup to O(1) average time, turning O(n * m) joins into linear O(n + m).",
            "'Map' vs. Plain Objects: Unlike plain objects (which coerce all non-symbol keys to strings and inherit 'Object.prototype' keys like 'toString' or 'constructor'), a 'Map' accepts keys of ANY type (numbers, objects, functions), preserves insertion order, reports count in O(1) via '.size', and is safe against prototype pollution with untrusted user keys.",
            "'Set' Operations & 'WeakMap' Memory Safety: 'Set' stores unique values (using 'SameValueZero' equality, where 'NaN === NaN') and supports fast membership checks ('.has()'). 'WeakMap' requires object keys and holds them weakly—when a key object has no other references, its 'WeakMap' entry is garbage-collected automatically, preventing memory leaks in caches."
        ],
        "code_lang": "typescript",
        "code": """export interface User {
  readonly id: string;
  readonly name: string;
}

export interface Post {
  readonly id: string;
  readonly authorId: string;
  readonly title: string;
}

// O(U + P) linear join using Map instead of O(U * P) nested .find()
export function attachAuthorNames(
  posts: readonly Post[],
  users: readonly User[]
): Array<Post & { readonly authorName: string }> {
  const userNameById = new Map<string, string>(
    users.map(u => [u.id, u.name])
  );

  return posts.map(post => ({
    ...post,
    authorName: userNameById.get(post.authorId) ?? "Unknown Author"
  }));
}
""",
        "exercise": [
            "Implementation Task: Implement 'setDifference<T>(a: ReadonlySet<T>, b: ReadonlySet<T>): Set<T>' and 'setIntersection<T>(a: ReadonlySet<T>, b: ReadonlySet<T>): Set<T>' with O(|a|) time complexity.",
            "Debugging Task: Replace a slow O(n^2) duplicate detector that runs 'items.filter((x, i) => items.indexOf(x) !== i)' on 50,000 IDs with an O(n) 'Set'-based implementation."
        ],
        "recall": [
            ("What are three concrete advantages of 'new Map()' over a plain object '{}' for dynamic key-value dictionaries?", "1. Keys are not coerced to strings (numbers, objects, and functions stay distinct); 2. No inherited 'Object.prototype' keys ('toString', '__proto__') can collide with user keys; 3. '.size' is O(1) without allocating an 'Object.keys()' array."),
            ("Why does storing two distinct object literals with identical contents into a 'Set' ('set.add({ id: 1 }); set.add({ id: 1 });') result in 'set.size === 2'?", "Because 'Set' checks equality using 'SameValueZero', which compares object references (memory addresses), not deep structural equality."),
            ("How does converting a lookup array into a 'Map' or 'Set' before looping improve algorithmic complexity?", "An array '.find()' or '.includes()' is O(n) per lookup, making a loop over 'm' items O(m * n). Building a 'Map'/'Set' takes O(n) once, and each '.get()'/'.has()' lookup is O(1), reducing total time to O(m + n)."),
            ("When should you use a 'WeakMap' instead of a 'Map' for caching computed metadata about DOM nodes or request objects?", "When the cache should not keep the key objects alive in memory once the rest of the application drops all references to those objects. 'Map' holds strong references (causing memory leaks unless manually deleted), whereas 'WeakMap' allows garbage collection.")
        ]
    },
    "PRG-T01-C03-U05": {
        "title": "Reusable Generic Utilities",
        "chapter": "C03",
        "order": 5,
        "prereq": "PRG-T01-C02-U05 (Generics), PRG-T01-C03-U02..U04 (Transformations & Collections)",
        "source": "R003 — MDN – JavaScript Guide & R004 — TypeScript Handbook (Generics; Utility Types). Verified accessible (HTTP 200).",
        "concepts_title": "Engineering Strategy & Data Transformation Patterns",
        "concepts": [
            "Designing Ergonomic Generic Signatures: A great utility function infers its type parameters from arguments without requiring callers to pass explicit '<Type>' brackets, accepts 'readonly T[]' so both mutable and 'as const' arrays work, and returns a precise output type.",
            "Core Collection Utilities ('groupBy', 'keyBy', 'chunk', 'pick', 'omit'): Instead of rewriting ad-hoc grouping and slicing loops across features, build well-typed generic utilities once. Use 'K extends PropertyKey' for dictionary keys and 'K extends keyof T' for property selection.",
            "Higher-Order Function Utilities ('debounce', 'memoize'): Use 'Parameters<F>' and 'ReturnType<F>' (or '<Args extends unknown[], R>(fn: (...args: Args) => R)') to wrap functions while preserving their exact parameter list."
        ],
        "code_lang": "typescript",
        "code": """export function groupBy<T, K extends PropertyKey>(
  items: readonly T[],
  getKey: (item: T, index: number) => K
): Record<K, T[]> {
  const result = Object.create(null) as Record<K, T[]>;
  for (let i = 0; i < items.length; i++) {
    const item = items[i]!;
    const key = getKey(item, i);
    const group = result[key];
    if (group) {
      group.push(item);
    } else {
      result[key] = [item];
    }
  }
  return result;
}

export function chunk<T>(items: readonly T[], size: number): T[][] {
  if (!Number.isInteger(size) || size <= 0) {
    throw new RangeError(`chunk size must be a positive integer, got ${size}`);
  }
  const chunks: T[][] = [];
  for (let i = 0; i < items.length; i += size) {
    chunks.push(items.slice(i, i + size));
  }
  return chunks;
}

export function pick<T extends object, K extends keyof T>(
  obj: T,
  keys: readonly K[]
): Pick<T, K> {
  const out = {} as Pick<T, K>;
  for (const key of keys) {
    if (key in obj) {
      out[key] = obj[key];
    }
  }
  return out;
}
""",
        "exercise": [
            "Implementation Task: Implement a generic 'omit<T extends object, K extends keyof T>(obj: T, keys: readonly K[]): Omit<T, K>' and a generic 'keyBy<T, K extends PropertyKey>(items: readonly T[], getKey: (item: T) => K): Record<K, T>'.",
            "Debugging Task: Fix a 'groupBy' implementation that initializes 'const result = {}' and breaks when an item's key is '\"toString\"' or '\"constructor\"' (use 'Object.create(null)' or 'Object.hasOwn')."
        ],
        "recall": [
            ("Why should reusable array utility functions accept 'items: readonly T[]' instead of 'items: T[]'?", "In TypeScript, 'T[]' is a subtype of 'readonly T[]' (not the other way around). Accepting 'readonly T[]' allows callers to pass both normal mutable arrays and 'readonly' / 'as const' tuples, while also preventing the utility from mutating the caller's array."),
            ("In 'groupBy<T, K extends PropertyKey>', what is the built-in type 'PropertyKey'?", "'PropertyKey' is TypeScript's built-in alias for 'string | number | symbol'—the exact set of types valid as object property keys in JavaScript."),
            ("Why did 'groupBy' above use 'Object.create(null)' for its accumulator object instead of '{}'?", "With a normal '{}' object, checking 'if (result[key])' when 'key' happens to be '\"toString\"' or '\"valueOf\"' finds 'Object.prototype.toString' (a function, not an array) and crashes when calling '.push()'. 'Object.create(null)' has no prototype properties."),
            ("How do you preserve a wrapped function's exact parameter types in a higher-order utility like 'debounce'?", "Parameterize the argument tuple with '<Args extends unknown[]>(fn: (...args: Args) => void, delayMs: number): (...args: Args) => void'.")
        ]
    },
    "PRG-T01-C03-U06": {
        "title": "Error Handling and Edge Cases",
        "chapter": "C03",
        "order": 6,
        "prereq": "PRG-T01-C01-U08 (Error Handling Patterns), PRG-T01-C02-U07 (Discriminated Unions)",
        "source": "R003 — MDN – JavaScript Guide (Control flow and error handling) & R004 — TypeScript Handbook (Narrowing). Verified accessible (HTTP 200).",
        "concepts_title": "Engineering Strategy & Data Transformation Patterns",
        "concepts": [
            "Systematic Edge-Case Checklist: Before considering any utility complete, test its behavior against boundary inputs: (1) Empty inputs ('\"\"', '[]', '{}'), (2) Single-element collections, (3) Numeric extremes ('0', '-0', 'NaN', 'Infinity', negative numbers, floating-point precision '0.1 + 0.2'), and (4) Special strings (whitespace-only, Unicode emoji/surrogate pairs, prototype keys like '\"__proto__\"').",
            "Result<T, E> Discriminated Unions vs. Throwing Exceptions: In TypeScript, thrown exceptions are untyped—a function signature 'parse(raw: string): Config' gives no compile-time hint that it can throw. Returning an explicit 'Result<T, E> = { ok: true; value: T } | { ok: false; error: E }' for expected validation/parsing failures forces callers to handle errors via control-flow narrowing.",
            "Fail-Fast Precondition Assertions: For programmer errors (like passing 'chunkSize = -5' or 'NaN'), fail immediately at the top of the function with a descriptive 'RangeError' or 'TypeError' rather than entering an infinite loop or returning corrupted data."
        ],
        "code_lang": "typescript",
        "code": """export type Result<T, E = string> =
  | { readonly ok: true; readonly value: T }
  | { readonly ok: false; readonly error: E };

export function parsePortNumber(rawInput: string): Result<number, string> {
  const trimmed = rawInput.trim();
  if (trimmed.length === 0) {
    return { ok: false, error: "Port input cannot be empty" };
  }

  // Note: Number("   ") is 0, so always check empty string first!
  const port = Number(trimmed);
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    return {
      ok: false,
      error: `Port must be an integer between 1 and 65535 (received "${rawInput}")`
    };
  }

  return { ok: true, value: port };
}
""",
        "exercise": [
            "Implementation Task: Write a safe 'divideCentsEvenly(totalCents: number, parts: number): Result<number[], string>' utility that rejects non-integers, negative totals, or 'parts <= 0', and distributes remainder cents without losing a single cent to floating-point rounding.",
            "Debugging Task: Identify why 'if (typeof x === \"number\")' passes 'NaN' and 'Infinity' into a financial calculation, and fix the guard using 'Number.isFinite(x)'."
        ],
        "recall": [
            ("Why does 'typeof NaN === \"number\"' evaluate to 'true' in JavaScript, and what method should you use to verify a usable finite number?", "'NaN' is defined by IEEE 754 as a special numeric value of type 'number'. Always check 'Number.isFinite(val)' (or 'Number.isSafeInteger(val)' for integers) to exclude both 'NaN' and '+-Infinity'."),
            ("What does 'Number(\"   \")' or 'Number(\"\")' evaluate to in JavaScript, and how can that cause bugs in input validation?", "It evaluates to '0' (not 'NaN'!). If you only check '!Number.isNaN(Number(input))', empty or whitespace strings silently become the number '0'."),
            ("When should a utility return a 'Result<T, E>' discriminated union versus throwing an 'Error'?", "Return 'Result<T, E>' when failure is an expected domain outcome that callers must handle (e.g., parsing user input, validation, expected 404/conflict). Throw an 'Error' ('RangeError'/'TypeError') for violated programming preconditions or unexpected bugs."),
            ("Why should monetary calculations in JavaScript/TypeScript be performed in integer minor units (satang/cents) instead of decimal floats?", "IEEE 754 binary floating-point cannot represent base-10 fractions like '0.1' or '0.2' exactly ('0.1 + 0.2 === 0.30000000000000004'), causing cumulative rounding errors unless computed in integer cents.")
        ]
    },
    "PRG-T01-C03-U07": {
        "title": "Testing Utility Functions",
        "chapter": "C03",
        "order": 7,
        "prereq": "PRG-T01-C03-U05 (Reusable Generic Utilities), PRG-T01-C03-U06 (Error Handling and Edge Cases)",
        "source": "R003 (MDN JS Guide) & R004 (TS Handbook) verified accessible (HTTP 200). Supplementary Note: Because R003 and R004 focus on language semantics rather than test runner APIs, test runner syntax is supplemented using the standard Node.js built-in test runner ('node:test' & 'node:assert/strict').",
        "concepts_title": "Engineering Strategy & Verification Patterns",
        "concepts": [
            "Arrange — Act — Assert (AAA) Structure: Every clear unit test has three distinct steps: (1) Arrange—prepare input fixtures without shared mutable globals; (2) Act—invoke the utility under test; (3) Assert—verify the returned value (deep equality), verify that input arguments were NOT mutated, or verify the thrown error.",
            "Designing an Edge-Case Test Matrix: Never write just one 'happy path' test. Group tests into a systematic matrix: (a) Nominal/Happy path, (b) Empty & boundary inputs ('[]', '0', single item), (c) Immutability check (asserting 'deepStrictEqual' on the input before and after the call), and (d) Error/Rejection path ('assert.throws' / 'assert.rejects').",
            "Testing Asynchronous & Throwing Code: Use 'assert.throws(() => chunk(arr, 0), RangeError)' for synchronous errors (wrapping the call in a function!) and 'await assert.rejects( asyncFn(), { name: \"ServiceError\" } )' for rejected Promises."
        ],
        "code_lang": "typescript",
        "code": """// Supplementary standard: Node.js built-in test runner (node:test + node:assert/strict)
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { chunk } from "./utilities.js";

describe("chunk(items, size)", () => {
  it("splits an array into equal chunks and a smaller trailing chunk", () => {
    const input = Object.freeze([1, 2, 3, 4, 5]);
    const actual = chunk(input, 2);
    assert.deepStrictEqual(actual, [[1, 2], [3, 4], [5]]);
  });

  it("returns an empty array when given an empty array", () => {
    assert.deepStrictEqual(chunk([], 3), []);
  });

  it("does not mutate the caller input array", () => {
    const input = [10, 20, 30];
    const snapshot = [...input];
    chunk(input, 2);
    assert.deepStrictEqual(input, snapshot);
  });

  it("throws a RangeError when size is zero, negative, or non-integer", () => {
    assert.throws(() => chunk([1, 2], 0), RangeError);
    assert.throws(() => chunk([1, 2], -2), RangeError);
    assert.throws(() => chunk([1, 2], 1.5), RangeError);
  });
});
""",
        "exercise": [
            "Implementation Task: Write a complete unit test suite for 'groupBy', 'pick', and 'parsePortNumber' covering happy paths, empty inputs, prototype-key safety ('\"toString\"'), immutability, and error conditions.",
            "Debugging Task: Fix a false-positive test that used 'assert.equal(actualArray, [1, 2])' (failing on reference equality instead of 'deepStrictEqual') and an async test that forgot to 'await assert.rejects(...)'."
        ],
        "recall": [
            ("Why must the function call inside 'assert.throws(() => fn(badInput), RangeError)' be wrapped in an arrow function instead of 'assert.throws(fn(badInput))'?", "If you write 'assert.throws(fn(badInput))', 'fn(badInput)' executes immediately BEFORE 'assert.throws' is even called, crashing the test directly instead of letting 'assert.throws' catch and inspect the exception."),
            ("Why does 'assert.strictEqual([1, 2], [1, 2])' fail even though both arrays have the same elements?", "'strictEqual' uses 'Object.is' (reference equality for objects/arrays), and two array literals have different memory addresses. Use 'assert.deepStrictEqual' to compare array/object contents recursively."),
            ("How does freezing input fixtures with 'Object.freeze(input)' inside unit tests catch hidden bugs?", "If the utility function accidentally mutates its input array or object in place (e.g., via '.sort()' or 'delete obj.key'), 'Object.freeze' immediately throws a 'TypeError' in strict mode during the test."),
            ("What happens if you call 'assert.rejects(asyncFn())' inside an 'it()' test without 'await'?", "The test function returns before the Promise settles, causing either a false pass or an unhandled rejection after the test finishes.")
        ]
    },
    "PRG-T01-C03-U08": {
        "title": "Packaging and Documentation",
        "chapter": "C03",
        "order": 8,
        "prereq": "PRG-T01-C01-U05 (Modules), PRG-T01-C02-U08 (Strict Mode and tsconfig), PRG-T01-C03-U07 (Testing)",
        "source": "R004 — TypeScript Handbook (Modules; Declaration Files; tsconfig). Verified accessible (HTTP 200). Supplementary Note: npm 'package.json' exports and TSDoc tags are supplemented using official Node.js ESM and TypeScript declaration packaging conventions.",
        "concepts_title": "Engineering Strategy & Package Distribution Patterns",
        "concepts": [
            "Emitting JavaScript + Type Declarations ('.d.ts'): A reusable TypeScript package does not ship raw '.ts' source files as its main entry point; it compiles '.ts' into '.js' (for the Node/browser runtime) alongside '.d.ts' declaration files and '.d.ts.map' declaration source maps (so IDE 'Go to Definition' jumps to the original source).",
            "Modern 'package.json' Entry Points ('type: \"module\"' & 'exports'): Configure '\"type\": \"module\"' for native ES Modules and define the '\"exports\"' map with '\"types\"' listed FIRST inside the '\".\"' condition so TypeScript's 'NodeNext' resolver locates './dist/index.d.ts' before './dist/index.js'. Use '\"files\": [\"dist\"]' to publish only compiled artifacts.",
            "Self-Documenting APIs with TSDoc: Adding '/** ... */' TSDoc comments with '@param', '@returns', '@throws', and '@example' blocks directly above exported functions surfaces inline documentation and runnable code examples in every consumer's IDE autocomplete tooltip."
        ],
        "code_lang": "typescript",
        "code": """// 1. TSDoc-annotated public export in src/index.ts:
/**
 * Splits a readonly array into smaller arrays of at most `size` elements.
 *
 * @typeParam T - The element type of the input array.
 * @param items - The source array to split (never mutated).
 * @param size - Maximum length of each chunk (must be a positive integer).
 * @returns A new array of chunks.
 * @throws {RangeError} If `size` is not a positive integer.
 *
 * @example
 * ```ts
 * const pages = chunk(["a", "b", "c", "d", "e"], 2);
 * // => [["a", "b"], ["c", "d"], ["e"]]
 * ```
 */
export function chunk<T>(items: readonly T[], size: number): T[][] {
  if (!Number.isInteger(size) || size <= 0) {
    throw new RangeError(`Expected positive integer size, received ${size}`);
  }
  const out: T[][] = [];
  for (let i = 0; i < items.length; i += size) {
    out.push(items.slice(i, i + size));
  }
  return out;
}

// 2. Corresponding package.json & tsconfig.build.json configuration (Supplementary):
/*
// package.json
{
  "name": "@scope/toolkit",
  "version": "1.0.0",
  "type": "module",
  "files": ["dist"],
  "exports": {
    ".": {
      "types": "./dist/index.d.ts",
      "default": "./dist/index.js"
    }
  },
  "scripts": {
    "build": "tsc -p tsconfig.build.json",
    "test": "node --import tsx --test src/**/*.test.ts"
  }
}

// tsconfig.build.json
{
  "extends": "./tsconfig.json",
  "compilerOptions": {
    "noEmit": false,
    "outDir": "./dist",
    "rootDir": "./src",
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  },
  "include": ["src"],
  "exclude": ["src/**/*.test.ts"]
}
*/
""",
        "exercise": [
            "Implementation Task: Write TSDoc documentation (including '@param', '@returns', '@throws', and '@example') for your utility toolkit exports and configure a 'package.json' + 'tsconfig.build.json' that emits '.js', '.d.ts', and '.d.ts.map' into './dist'.",
            "Debugging Task: Fix a 'package.json' where consumers get 'Could not find a declaration file for module' under 'moduleResolution: \"NodeNext\"' because '\"types\"' was omitted or placed after '\"default\"' in the 'exports' map."
        ],
        "recall": [
            ("Why must the '\"types\"' condition appear BEFORE '\"default\"' inside a 'package.json' '\"exports\"' block?", "Node.js and TypeScript evaluate condition keys in 'exports' top-to-bottom. Since '\"default\"' matches every environment, placing '\"default\"' before '\"types\"' causes TypeScript to match '\"default\"' first and miss the specific '\"types\"' declaration path."),
            ("What is the purpose of enabling both '\"declaration\": true' and '\"declarationMap\": true' in 'tsconfig.build.json'?", "'declaration: true' generates '.d.ts' type definition files for package consumers; 'declarationMap: true' generates '.d.ts.map' files that map those definitions back to the original source lines."),
            ("Why should a library's 'package.json' include '\"files\": [\"dist\"]' and exclude '*.test.ts' in 'tsconfig.build.json'?", "To keep the published package small and clean—consumers only need the compiled 'dist/' artifacts, README, and package.json, not test suites or local configuration files."),
            ("In Semantic Versioning ('MAJOR.MINOR.PATCH'), which version number must you increment if you tighten a function parameter type or remove a property from an exported return type?", "You must increment 'MAJOR' (e.g., '1.x.x -> 2.0.0'), because narrowing accepted inputs or removing output properties is a breaking compile-time/runtime contract change for existing consumers.")
        ]
    }
}
