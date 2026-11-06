# -*- coding: utf-8 -*-
"""
Builder module for PRG-T00-C02 (JavaScript & TypeScript Baseline):
Generates production-grade, Gold Standard (v3) content for:
- PRG-T00-C02 (Chapter: JavaScript & TypeScript Baseline)
- PRG-T00-C02-U01 through U07 (7 Units)

Strictly adheres to Central Rules:
- Complete Practice Guide (Core Skills, Prior Units, Common Traps, Cross-Subject Connections)
- Active Recall Questions with toggles
- My Implementation & Mistake Log
- Native @Page mentions (zero unparsed [[ tokens)
- 100% English, zero markdown leaks
"""
import json
import re
from apply_rules_and_test_pages import (
    h2,
    h3,
    p_block,
    callout_block,
    bullet,
    num_item,
    todo_item,
    toggle_block,
    code_block,
    divider_block,
)

def build_prg_t00_c02(id_map):
    return [
        callout_block(
            "**Chapter Objective:** Establish empirical baseline literacy in JavaScript runtime semantics and foundational TypeScript compilation: variables, primitive vs reference types, lexical scope, array/object manipulation, DOM/browser events, Promises/async flow, and static type annotations.\n"
            "**Completion Criteria:** Complete an unassisted, strictly typed interactive DOM utility application with event listeners, asynchronous fetching, and immutable data transformations without copying tutorials.\n"
            "**Parent Topic:** [[PRG-T00]] | **Sources:** [[R003]] (`MDN JavaScript Guide`), [[R004]] (`TypeScript Handbook`)",
            id_map,
            color="blue_background",
        ),
        h2("1. Chapter Role & JavaScript Runtime Mental Model", id_map),
        p_block(
            "[[PRG-T00-C02]] provides the indispensable programming foundation for the entire software engineering curriculum. Before diving into execution contexts, closures, and prototype inheritance in [[PRG-T01]], or managing reactive component state in [[PRG-T02]], an engineer must develop an accurate mental model of how JavaScript executes code in memory:",
            id_map,
        ),
        num_item(
            "**Memory Allocation & Type Primitives:** JavaScript partitions values into immutable primitives stored by value (number, string, boolean, null, undefined, symbol, bigint) and mutable objects stored by reference address in the memory heap.",
            id_map,
        ),
        num_item(
            "**Lexical Scope & Call Stack:** Functions create execution boundaries. Variable lookup traverses inward-outward along the lexical scope chain governed by where functions are declared in source text.",
            id_map,
        ),
        num_item(
            "**Event-Driven Concurrency:** JavaScript is single-threaded and non-blocking. Synchronous call stack execution coordinates with the Event Loop, Microtask Queue (Promises), and Macrotask Queue (timers, I/O) to process asynchronous work.",
            id_map,
        ),
        num_item(
            "**Compile-Time Type Safety:** TypeScript acts as a static verification layer over JavaScript. It validates domain contracts at compile time before erasing all types into standard ECMAScript for execution.",
            id_map,
        ),
        divider_block(),
        h2("2. Core Architectural Principles", id_map),
        bullet("**Strict Immutability over In-Place Mutation:** Prefer pure transformations (`map`, `filter`, `slice`, spread syntax) over in-place mutations (`splice`, `push`, direct property assignment) to prevent unpredictable shared-state side effects.", id_map),
        bullet("**Defensive Value Narrowing:** Never assume remote or user input is valid. Distinguish between `null` (intentional absence) and `undefined` (uninitialized), and use strict equality (`===`) and nullish coalescing (`??`).", id_map),
        bullet("**Explicit Error Propagation:** Always handle asynchronous Promise rejections with `try/catch` or `.catch()`. Unhandled rejections terminate Node processes and crash UI pipelines.", id_map),
        divider_block(),
        h2("3. Learning Units in this Chapter (7 Units)", id_map),
        num_item("[[PRG-T00-C02-U01]] — **Variables, Types and Operators:** Primitive vs reference values, coercion traps, truthy/falsy semantics, strict equality, and nullish coalescing.", id_map),
        num_item("[[PRG-T00-C02-U02]] — **Functions and Scope:** Declarations, expressions, arrow functions, lexical scope boundaries, default parameters, and rest parameters.", id_map),
        num_item("[[PRG-T00-C02-U03]] — **Arrays and Objects:** Iteration protocols, transformation pipelines (`map`, `filter`, `reduce`), destructuring, and shallow vs deep copying.", id_map),
        num_item("[[PRG-T00-C02-U04]] — **DOM and Browser Events:** Document tree querying, element creation/mutation, event bubbling, capturing, event delegation, and event prevention.", id_map),
        num_item("[[PRG-T00-C02-U05]] — **Promises and Async/Await:** Asynchronous runtime mechanics, Promise states, `async/await` syntax, parallel execution with `Promise.all`, and error handling.", id_map),
        num_item("[[PRG-T00-C02-U06]] — **TypeScript Basics:** Static typing vs runtime execution, type annotations, interfaces, type aliases, basic union types, and the `tsc` compiler.", id_map),
        num_item("[[PRG-T00-C02-U07]] — **Reading and Debugging Existing Code:** Stack trace triage, Node/browser debugger tools, isolating reproducible minimal defects, and bug verification.", id_map),
        divider_block(),
        h2("4. Chapter Capstone Practice Blueprint", id_map),
        p_block("After studying the 7 Units in [[PRG-T00-C02]], use this blueprint to test and solidify your programming baseline:", id_map),
        bullet("**Task:** Build an interactive, strictly typed Task Tracker in TypeScript that runs natively in the browser without third-party frameworks.", id_map),
        bullet("**Invariants to Enforce:**", id_map, children=[
            bullet("Compile with `tsc --noEmit --strict` with zero type errors.", id_map),
            bullet("Manage task items immutably using array transformation methods (`map`, `filter`, `reduce`).", id_map),
            bullet("Fetch initial placeholder tasks from a remote mock API (`fetch`) with full `try/catch` error state handling.", id_map),
            bullet("Use event delegation on the task container rather than attaching individual event listeners per row.", id_map),
        ]),
        divider_block(),
        h2("5. Verification & Mastery Checklist", id_map),
        todo_item("Study all 7 Units from [[PRG-T00-C02-U01]] to [[PRG-T00-C02-U07]] with honest Mastery >= 3.", id_map),
        todo_item("Explain the exact memory difference between `const a = {}` and `const b = 'hello'` when passing them as function arguments.", id_map),
        todo_item("Demonstrate how `tsc` strips type annotations and why TypeScript cannot protect against malformed runtime API JSON payloads without defensive guards.", id_map),
    ]


def build_prg_t00_c02_u01(id_map):
    return [
        callout_block(
            "**Learning Objective:** Master JavaScript primitive vs reference data types, type coercion mechanics, truthy/falsy evaluation, strict equality (`===`), and modern nullish operators (`??`, `?.`).\n"
            "**Expected Output:** Write clean, defensive conditional logic that avoids implicit type coercion traps, correctly distinguishes `null` from `undefined`, and safely extracts deeply nested properties.\n"
            "**Parent:** [[PRG-T00]] → [[PRG-T00-C02]] | **Next Unit:** [[PRG-T00-C02-U02]] | **Source:** [[R003]] (`MDN JavaScript Guide`)",
            id_map,
            color="blue_background",
        ),
        h2("1. Core Concepts & Architectural Mental Model", id_map),
        bullet("**1. Primitive Types vs Reference Objects:**", id_map, children=[
            bullet("JavaScript has 7 primitive types: `string`, `number`, `boolean`, `null`, `undefined`, `symbol`, and `bigint`. Primitives are immutable and compared by value.", id_map),
            bullet("All other values are Objects (`Object`, `Array`, `Function`, `Date`, `Map`, `Set`). Objects are mutable and compared by memory reference address.", id_map),
        ]),
        bullet("**2. The Coercion Pitfall & Strict Equality (`===`):**", id_map, children=[
            bullet("Loose equality (`==`) performs implicit type coercion using the Abstract Equality Comparison Algorithm, leading to bizarre traps: `'' == 0` (true), `null == undefined` (true), `false == []` (true).", id_map),
            bullet("Professional code mandates strict equality (`===`), which checks both type and value without coercion.", id_map),
        ]),
        bullet("**3. Truthy vs Falsy Values:**", id_map, children=[
            bullet("Exactly 8 values evaluate to falsy in boolean contexts: `false`, `0`, `-0`, `0n`, `''` (empty string), `null`, `undefined`, and `NaN`. All other values, including empty arrays `[]` and empty objects `{}`, evaluate to truthy.", id_map),
        ]),
        bullet("**4. Modern Safe Operators: Nullish Coalescing (`??`) and Optional Chaining (`?.`):**", id_map, children=[
            bullet("`||` falls back on ANY falsy value (treating `0` or `''` as false, which causes bugs when `0` is a valid quantity or count).", id_map),
            bullet("`??` falls back ONLY if the left-hand operand is `null` or `undefined`, correctly preserving `0` and `false`.", id_map),
            bullet("`obj?.prop?.subProp` short-circuits to `undefined` if any intermediate property is `null` or `undefined`, preventing `TypeError: Cannot read properties of undefined`.", id_map),
        ]),
        divider_block(),
        h2("2. Code & Implementation Examples", id_map),
        h3("Example 1: Safe Property Extraction & Nullish Handling", id_map),
        code_block(
            "// DEFENSIVE VALUE HANDLING:\n"
            "interface UserConfig {\n"
            "  theme?: string;\n"
            "  maxRetries?: number;\n"
            "  notifications?: {\n"
            "    emailEnabled?: boolean;\n"
            "  };\n"
            "}\n\n"
            "function initializeApp(config?: UserConfig) {\n"
            "  // WRONG: if maxRetries is 0, || coerces to 3!\n"
            "  // const retries = config?.maxRetries || 3;\n\n"
            "  // CORRECT: nullish coalescing preserves 0 as a valid retry limit\n"
            "  const retries = config?.maxRetries ?? 3;\n"
            "  const theme = config?.theme ?? 'dark';\n"
            "  const isEmailActive = config?.notifications?.emailEnabled ?? false;\n\n"
            "  return { retries, theme, isEmailActive };\n"
            "}\n\n"
            "console.log(initializeApp({ maxRetries: 0 }));\n"
            "// Output: { retries: 0, theme: 'dark', isEmailActive: false }",
            "typescript",
        ),
        divider_block(),
        h2("3. Practice Guide", id_map),
        p_block("Use this blueprint to drill value types and operator invariants:", id_map),
        bullet("**1. Core Skills to Drill:**", id_map, children=[
            bullet("**Falsy Audit:** Inspect existing utility functions and identify where `||` was used instead of `??`, causing zero or empty strings to be accidentally overwritten.", id_map),
            bullet("**Reference Independence:** Write code that demonstrates that mutating an object assigned to a second variable modifies the original, whereas reassigning a primitive variable does not.", id_map),
        ]),
        bullet("**2. Combine with Prior Units:**", id_map, children=[
            bullet("**Bridge to [[PRG-T00-C01-U01]]:** Parsing query parameters from URLs returns strings (`'0'`, `'false'`). Because non-empty strings are truthy, `Boolean('false') === true`. Always parse explicitly.", id_map),
        ]),
        bullet("**3. Common Traps & Edge Cases to Test:**", id_map, children=[
            bullet("**`typeof null === 'object'` Bug:** Historical legacy bug in JS engine. Always check `val === null` explicitly.", id_map),
            bullet("**`NaN === NaN` is `false`:** `NaN` is the only value in JavaScript that is not equal to itself. Check with `Number.isNaN(val)`.", id_map),
        ]),
        bullet("**4. Cross-Subject & Real-World Connection:**", id_map, children=[
            bullet("**Bridge to [[PRG-T01-C02]]:** TypeScript Discriminated Unions rely on strict literal equality checks on discriminant properties (e.g. `type: 'success' | 'error'`).", id_map),
        ]),
        divider_block(),
        h2("4. Active Recall Questions", id_map),
        toggle_block("What is the exact technical difference between `a || b` and `a ?? b`?", [
            p_block("`a || b` checks whether `a` is truthy; if `a` is any falsy value (`0`, `''`, `false`, `null`, `undefined`, `NaN`), it evaluates to `b`. In contrast, `a ?? b` checks only whether `a` is nullish (`null` or `undefined`). If `a` is `0`, `false`, or `''`, `??` preserves `a`.", id_map),
        ], id_map),
        toggle_block("Why does `[1, 2] === [1, 2]` evaluate to `false` in JavaScript?", [
            p_block("Arrays are objects stored in the memory heap. When comparing objects with strict equality (`===`), JavaScript compares reference addresses in memory, not the structural contents. Because the two array literals allocate two separate heap addresses, the comparison evaluates to `false`.", id_map),
        ], id_map),
        divider_block(),
        h2("5. My Implementation & Mistake Log", id_map),
        todo_item("Review code for any occurrences of loose equality `==` and replace with `===`.", id_map),
        todo_item("Audit default configuration functions to ensure numerical `0` is not clobbered by `||`.", id_map),
    ]


def build_prg_t00_c02_u02(id_map):
    return [
        callout_block(
            "**Learning Objective:** Master JavaScript function forms (declarations, expressions, arrows), lexical scope boundaries, parameter defaults, rest parameters, and baseline closure mechanics.\n"
            "**Expected Output:** Write modular, pure functions with explicit parameter contracts, predictable lexical scope lookups, and clear closure encapsulation.\n"
            "**Parent:** [[PRG-T00]] → [[PRG-T00-C02]] | **Next Unit:** [[PRG-T00-C02-U03]] | **Source:** [[R003]] (`MDN JavaScript Guide`)",
            id_map,
            color="blue_background",
        ),
        h2("1. Core Concepts & Architectural Mental Model", id_map),
        bullet("**1. Function Declarations vs. Expressions vs. Arrow Functions:**", id_map, children=[
            bullet("**Function Declaration:** `function foo() {}` is hoisted completely to the top of its enclosing scope, allowing invocations before its lexical definition.", id_map),
            bullet("**Function Expression:** `const foo = function() {}` assigns an anonymous or named function to a variable. The variable declaration is hoisted, but remains uninitialized in the Temporal Dead Zone (TDZ).", id_map),
            bullet("**Arrow Function:** `const foo = () => {}` provides concise syntax and lexically binds `this` and `arguments` from its enclosing lexical context.", id_map),
        ]),
        bullet("**2. Lexical Scope & Block Scope:**", id_map, children=[
            bullet("Variables declared with `let` and `const` are block-scoped (`{ ... }`). Variables declared with legacy `var` are function-scoped and leak out of `if` blocks and loops.", id_map),
            bullet("Scope lookup is unidirectional: inner scopes have access to outer scopes, but outer scopes cannot access inner variables.", id_map),
        ]),
        bullet("**3. Closures (Introductory Mental Model):**", id_map, children=[
            bullet("A closure is the combination of a function bundled together with references to its surrounding lexical environment. When an inner function is returned or retained, it preserves access to outer variables even after the outer function has finished executing.", id_map),
        ]),
        bullet("**4. Parameter Handling: Defaults & Rest (`...args`):**", id_map, children=[
            bullet("Default parameters (`fn(timeout = 5000)`) execute only when the argument passed is `undefined`.", id_map),
            bullet("Rest parameters (`fn(first, ...rest)`) gather variable numbers of arguments into a genuine Array instance, replacing the legacy non-array `arguments` object.", id_map),
        ]),
        divider_block(),
        h2("2. Code & Implementation Examples", id_map),
        h3("Example 1: Factory Function with Lexical State Encapsulation (Closure)", id_map),
        code_block(
            "// CLOSURE COUNTER FACTORY:\n"
            "function createIdGenerator(prefix = 'id') {\n"
            "  let sequence = 0; // Private encapsulated state\n\n"
            "  return {\n"
            "    next() {\n"
            "      sequence += 1;\n"
            "      return `${prefix}_${sequence}`;\n"
            "    },\n"
            "    peek() {\n"
            "      return sequence;\n"
            "    },\n"
            "    reset() {\n"
            "      sequence = 0;\n"
            "    }\n"
            "  };\n"
            "}\n\n"
            "const userIds = createIdGenerator('user');\n"
            "console.log(userIds.next()); // 'user_1'\n"
            "console.log(userIds.next()); // 'user_2'\n"
            "console.log(userIds.peek()); // 2",
            "javascript",
        ),
        divider_block(),
        h2("3. Practice Guide", id_map),
        bullet("**1. Core Skills to Drill:**", id_map, children=[
            bullet("**Closure State Retention:** Build a `createRateLimiter` factory holding private token counts inside lexical scope.", id_map),
            bullet("**Parameter Boundary Test:** Verify that passing `null` to a function with a default parameter (`fn(port = 3000)`) binds `port = null`, not `3000` (defaults trigger only on `undefined`).", id_map),
        ]),
        bullet("**2. Combine with Prior Units:**", id_map, children=[
            bullet("**Bridge to [[PRG-T00-C02-U01]]:** Ensure functions do not mutate input reference objects unless explicitly designed as in-place mutators.", id_map),
        ]),
        bullet("**3. Common Traps & Edge Cases to Test:**", id_map, children=[
            bullet("**Loop Variable Closure Trap (Legacy `var`):** Using `for (var i = 0; ...)` with async callbacks causes all callbacks to share the final mutated value of `i`. `let` creates a fresh lexical binding per iteration.", id_map),
        ]),
        bullet("**4. Cross-Subject & Real-World Connection:**", id_map, children=[
            bullet("**Bridge to [[PRG-T01-C01]]:** Lexical scope and Execution Contexts are analyzed in depth in [[PRG-T01-C01-U01]] and [[PRG-T01-C01-U02]].", id_map),
            bullet("**Bridge to [[PRG-T02-C01]]:** React custom hooks (`useState`, `useEffect`) leverage JavaScript closures to preserve component state across renders.", id_map),
        ]),
        divider_block(),
        h2("4. Active Recall Questions", id_map),
        toggle_block("Why does `var` inside a `for` loop leak into outer scope, whereas `let` does not?", [
            p_block("`var` is function-scoped (or globally scoped if declared outside a function). It ignores curly-bracket `{ ... }` blocks such as loops and `if` statements. In contrast, `let` is block-scoped, confining the variable strictly to the loop body and creating a new binding per iteration.", id_map),
        ], id_map),
        toggle_block("When does a default parameter expression evaluate in JavaScript?", [
            p_block("Default parameters in JavaScript evaluate at call time (lazily), not when the function is defined. Furthermore, default parameters are evaluated only if the argument passed is strictly `undefined`.", id_map),
        ], id_map),
        divider_block(),
        h2("5. My Implementation & Mistake Log", id_map),
        todo_item("Eliminate all legacy `var` declarations in favor of `const` (preferred) or `let`.", id_map),
        todo_item("Implement a factory function that hides internal counters using private lexical scope.", id_map),
    ]


def build_prg_t00_c02_u03(id_map):
    return [
        callout_block(
            "**Learning Objective:** Master JavaScript array transformation pipelines (`map`, `filter`, `reduce`), object property manipulation, destructuring, spread syntax, and immutability invariants.\n"
            "**Expected Output:** Write expressive, side-effect-free data transformation pipelines that filter, group, aggregate, and normalize nested records without mutating input collections.\n"
            "**Parent:** [[PRG-T00]] → [[PRG-T00-C02]] | **Next Unit:** [[PRG-T00-C02-U04]] | **Source:** [[R003]] (`MDN JavaScript Guide`)",
            id_map,
            color="blue_background",
        ),
        h2("1. Core Concepts & Architectural Mental Model", id_map),
        bullet("**1. Pure Iteration Pipelines vs Imperative Loops:**", id_map, children=[
            bullet("`map(fn)`: Transforms each element 1:1 into a new array of identical length.", id_map),
            bullet("`filter(predicate)`: Selects elements satisfying a boolean predicate into a new array (0 to N elements).", id_map),
            bullet("`reduce(accumulatorFn, initialValue)`: Aggregates an array into any arbitrary single value, object, map, or grouped dictionary.", id_map),
        ]),
        bullet("**2. Object Destructuring & Rest/Spread Syntax:**", id_map, children=[
            bullet("`const { id, ...rest } = user;` extracts `id` and bundles all remaining properties into `rest`.", id_map),
            bullet("`const updated = { ...user, active: true };` creates a shallow clone with overridden properties without mutating `user`.", id_map),
        ]),
        bullet("**3. Shallow Copying vs Deep Copying Traps:**", id_map, children=[
            bullet("Spread syntax (`[...arr]`, `{ ...obj }`) creates a **shallow copy**. Nested objects or arrays are still referenced by the same memory pointer.", id_map),
            bullet("For true deep copies of JSON-serializable structures, use standard `structuredClone(obj)`.", id_map),
        ]),
        divider_block(),
        h2("2. Code & Implementation Examples", id_map),
        h3("Example 1: Immutable Data Grouping and Aggregation with `reduce`", id_map),
        code_block(
            "interface Transaction {\n"
            "  id: string;\n"
            "  category: string;\n"
            "  amount: number;\n"
            "}\n\n"
            "const transactions: Transaction[] = [\n"
            "  { id: 'tx1', category: 'groceries', amount: 42.50 },\n"
            "  { id: 'tx2', category: 'utilities', amount: 120.00 },\n"
            "  { id: 'tx3', category: 'groceries', amount: 18.25 }\n"
            "];\n\n"
            "// Pure aggregation: calculate category totals\n"
            "const totalsByCategory = transactions.reduce<Record<string, number>>(\n"
            "  (acc, tx) => {\n"
            "    const current = acc[tx.category] ?? 0;\n"
            "    return { ...acc, [tx.category]: Math.round((current + tx.amount) * 100) / 100 };\n"
            "  },\n"
            "  {}\n"
            ");\n\n"
            "console.log(totalsByCategory);\n"
            "// Output: { groceries: 60.75, utilities: 120 }",
            "typescript",
        ),
        divider_block(),
        h2("3. Practice Guide", id_map),
        bullet("**1. Core Skills to Drill:**", id_map, children=[
            bullet("**Pipeline Composition:** Chain `.filter()`, `.map()`, and `.sort()` cleanly to transform raw API responses into sorted display models.", id_map),
            bullet("**Accumulator Invariant:** Always provide an explicit `initialValue` to `.reduce()`. Calling reduce on an empty array without an initial value throws a runtime `TypeError`.", id_map),
        ]),
        bullet("**2. Combine with Prior Units:**", id_map, children=[
            bullet("**Bridge to [[PRG-T00-C02-U01]]:** Remember that object keys in JavaScript are strings or symbols. `obj[0]` accesses property `'0'`.", id_map),
        ]),
        bullet("**3. Common Traps & Edge Cases to Test:**", id_map, children=[
            bullet("**Array.prototype.sort() In-Place Mutation Trap:** `.sort()` mutates the original array in place and converts numbers to strings by default (sorting `[10, 2]` into `[10, 2]` because `'10' < '2'`). Always pass a comparator: `[...arr].sort((a, b) => a - b)`.", id_map),
        ]),
        bullet("**4. Cross-Subject & Real-World Connection:**", id_map, children=[
            bullet("**Bridge to [[PRG-T01-C03]]:** Problem decomposition in [[PRG-T01-C03-U02]] builds advanced data pipelines (grouping, partitioning, chunking).", id_map),
            bullet("**Bridge to [[PRG-T02-C02]]:** React state management strictly forbids in-place array mutation; React will not trigger re-renders unless the array reference changes.", id_map),
        ]),
        divider_block(),
        h2("4. Active Recall Questions", id_map),
        toggle_block("Why is `const sorted = arr.sort()` dangerous in production code?", [
            p_block("`Array.prototype.sort()` does NOT return a new array; it mutates `arr` in place and returns the same array reference. Any other part of the codebase referencing `arr` will have its ordering silently corrupted. Always shallow-copy before sorting: `const sorted = [...arr].sort((a, b) => a - b)`.", id_map),
        ], id_map),
        toggle_block("What happens if you call `.reduce()` on an empty array without an initialValue?", [
            p_block("JavaScript throws a runtime `TypeError: Reduce of empty array with no initial value`. Always provide an explicit initial accumulator value as the second argument to `.reduce()`.", id_map),
        ], id_map),
        divider_block(),
        h2("5. My Implementation & Mistake Log", id_map),
        todo_item("Audit array sorting operations to ensure input collections are never mutated in place.", id_map),
        todo_item("Implement a groupBy utility using pure `.reduce()` with explicit type annotations.", id_map),
    ]


def build_prg_t00_c02_u04(id_map):
    return [
        callout_block(
            "**Learning Objective:** Master the Browser Document Object Model (DOM), element selection/mutation, the event flow model (capturing, target, bubbling), event delegation, and form event handling.\n"
            "**Expected Output:** Build dynamic interactive user interfaces that manipulate the DOM safely, leverage event delegation for scalable performance, and prevent memory leaks.\n"
            "**Parent:** [[PRG-T00]] → [[PRG-T00-C02]] | **Next Unit:** [[PRG-T00-C02-U05]] | **Source:** [[R001]] (`MDN HTML`), [[R003]] (`MDN JavaScript Guide`)",
            id_map,
            color="blue_background",
        ),
        h2("1. Core Concepts & Architectural Mental Model", id_map),
        bullet("**1. The DOM Tree Structure:**", id_map, children=[
            bullet("The DOM represents HTML documents as a hierarchical node tree. The browser builds the DOM incrementally from raw HTML token streams.", id_map),
            bullet("Modern element querying standard: `document.querySelector(selector)` and `document.querySelectorAll(selector)`.", id_map),
        ]),
        bullet("**2. The 3 Phases of Event Flow:**", id_map, children=[
            bullet("1. **Capturing Phase:** Event travels downward from `window` through the document tree to the target element.", id_map),
            bullet("2. **Target Phase:** Event reaches the target element where listeners registered on target fire.", id_map),
            bullet("3. **Bubbling Phase:** Event bubbles upward from the target element back up to `window`.", id_map),
        ]),
        bullet("**3. Event Delegation Architecture:**", id_map, children=[
            bullet("Instead of attaching 100 individual event listeners to 100 table rows, attach a single listener to the common parent element (`<tbody>`) and inspect `event.target.closest('tr')` during the bubbling phase. This conserves memory and automatically handles dynamically inserted elements.", id_map),
        ]),
        bullet("**4. Controlling Event Propagation & Defaults:**", id_map, children=[
            bullet("`event.preventDefault()`: Prevents the browser's default action (e.g. form submission page refresh, anchor link navigation).", id_map),
            bullet("`event.stopPropagation()`: Halts the event from bubbling further up the DOM hierarchy.", id_map),
        ]),
        divider_block(),
        h2("2. Code & Implementation Examples", id_map),
        h3("Example 1: Scalable Event Delegation on Dynamic Lists", id_map),
        code_block(
            "// EVENT DELEGATION PATTERN:\n"
            "const userList = document.querySelector('#user-list');\n\n"
            "userList?.addEventListener('click', (event) => {\n"
            "  const target = event.target as HTMLElement;\n"
            "  const deleteBtn = target.closest<HTMLButtonElement>('button[data-action=\"delete\"]');\n\n"
            "  if (deleteBtn) {\n"
            "    const row = deleteBtn.closest('li');\n"
            "    const userId = row?.dataset.userId;\n"
            "    console.log(`Deleting user: ${userId}`);\n"
            "    row?.remove();\n"
            "  }\n"
            "});",
            "typescript",
        ),
        divider_block(),
        h2("3. Practice Guide", id_map),
        bullet("**1. Core Skills to Drill:**", id_map, children=[
            bullet("**Delegation Protocol:** Implement a dynamic shopping cart list where items can be added and removed using a single event listener on the parent container.", id_map),
            bullet("**Form Submission Trap:** Always call `event.preventDefault()` inside `'submit'` event listeners to prevent the browser from executing a full synchronous page reload.", id_map),
        ]),
        bullet("**2. Combine with Prior Units:**", id_map, children=[
            bullet("**Bridge to [[PRG-T00-C01-U02]]:** Respect semantic HTML forms and input elements (`<form>`, `<label>`, `<button type=\"submit\">`) so keyboard users can submit by pressing Enter.", id_map),
        ]),
        bullet("**3. Common Traps & Edge Cases to Test:**", id_map, children=[
            bullet("**`event.target` vs `event.currentTarget`:** `event.target` is the deepest element clicked (could be an `<i>` icon inside a button); `event.currentTarget` is the element to which the listener was attached.", id_map),
            bullet("**Memory Leak Trap:** Forgetting to clean up event listeners on removed elements when not using event delegation.", id_map),
        ]),
        bullet("**4. Cross-Subject & Real-World Connection:**", id_map, children=[
            bullet("**Bridge to [[PRG-T02-C01]]:** React SyntheticEvent system implements event delegation under the hood, attaching root event listeners to the React container root.", id_map),
        ]),
        divider_block(),
        h2("4. Active Recall Questions", id_map),
        toggle_block("What is the difference between `event.target` and `event.currentTarget`?", [
            p_block("`event.target` refers to the exact DOM element that triggered the event (the origin element, e.g. a `<span>` or icon clicked). `event.currentTarget` refers to the DOM element to which the event handler is currently attached (e.g. the parent container handling the bubbled event).", id_map),
        ], id_map),
        toggle_block("Why does event delegation save memory when rendering dynamic lists?", [
            p_block("Instead of allocating separate callback function closures and memory listeners for every single child item (which degrades performance as lists grow to thousands of items), event delegation attaches only a single listener to the parent element, catching bubbled events via `event.target.closest()`.", id_map),
        ], id_map),
        divider_block(),
        h2("5. My Implementation & Mistake Log", id_map),
        todo_item("Replace individual list item event listeners with a single parent event delegation handler.", id_map),
        todo_item("Verify all form submission handlers call `event.preventDefault()`.", id_map),
    ]


def build_prg_t00_c02_u05(id_map):
    return [
        callout_block(
            "**Learning Objective:** Master asynchronous JavaScript runtime mechanics: the Promise lifecycle (pending, fulfilled, rejected), `async/await` syntax, error propagation with `try/catch`, and concurrency coordination with `Promise.all`.\n"
            "**Expected Output:** Author robust asynchronous data fetching pipelines that handle network failures gracefully, coordinate parallel requests, and prevent unhandled promise rejections.\n"
            "**Parent:** [[PRG-T00]] → [[PRG-T00-C02]] | **Next Unit:** [[PRG-T00-C02-U06]] | **Source:** [[R003]] (`MDN JavaScript Guide`), [[R030]] (`MDN HTTP`)",
            id_map,
            color="blue_background",
        ),
        h2("1. Core Concepts & Architectural Mental Model", id_map),
        bullet("**1. The Asynchronous Event Loop & Microtasks:**", id_map, children=[
            bullet("JavaScript cannot execute network requests synchronously on the main thread without freezing the UI. Web APIs handle network I/O in the background and enqueue callbacks.", id_map),
            bullet("Promises schedule callbacks on the **Microtask Queue**, which executes immediately after the current synchronous script and before the next Macrotask (e.g. `setTimeout`).", id_map),
        ]),
        bullet("**2. The 3 States of a Promise:**", id_map, children=[
            bullet("`pending`: Initial state, neither fulfilled nor rejected.", id_map),
            bullet("`fulfilled`: Asynchronous operation succeeded, producing a resolved value.", id_map),
            bullet("`rejected`: Asynchronous operation failed, producing an error/reason.", id_map),
        ]),
        bullet("**3. `async/await` as Synchronous Syntactic Sugar:**", id_map, children=[
            bullet("An `async` function always returns a Promise.", id_map),
            bullet("The `await` operator pauses execution of the enclosing `async` function until the awaited Promise settles, allowing linear reading order without nested callback pyramids.", id_map),
        ]),
        bullet("**4. Parallel vs Sequential Execution:**", id_map, children=[
            bullet("Awaiting independent requests sequentially creates an unnecessary latency waterfall (`T_total = T1 + T2`).", id_map),
            bullet("Using `Promise.all([p1, p2])` fires requests concurrently, reducing latency to `T_total = max(T1, T2)`.", id_map),
        ]),
        divider_block(),
        h2("2. Code & Implementation Examples", id_map),
        h3("Example 1: Resilient Async Data Fetching with Parallel Coordination", id_map),
        code_block(
            "// PRODUCTION-GRADE ASYNC FETCH PIPELINE:\n"
            "interface User { id: string; name: string; }\n"
            "interface Order { id: string; total: number; }\n\n"
            "async function fetchDashboardData(userId: string) {\n"
            "  try {\n"
            "    // Fire both independent requests in parallel\n"
            "    const [userRes, ordersRes] = await Promise.all([\n"
            "      fetch(`/api/users/${userId}`),\n"
            "      fetch(`/api/users/${userId}/orders`)\n"
            "    ]);\n\n"
            "    // HTTP errors (404, 500) do NOT reject fetch() automatically!\n"
            "    if (!userRes.ok) throw new Error(`User API error: ${userRes.status}`);\n"
            "    if (!ordersRes.ok) throw new Error(`Orders API error: ${ordersRes.status}`);\n\n"
            "    const user: User = await userRes.json();\n"
            "    const orders: Order[] = await ordersRes.json();\n\n"
            "    return { user, orders };\n"
            "  } catch (error) {\n"
            "    console.error('Failed to load dashboard:', error);\n"
            "    throw error; // Re-throw or return fallback state\n"
            "  }\n"
            "}",
            "typescript",
        ),
        divider_block(),
        h2("3. Practice Guide", id_map),
        bullet("**1. Core Skills to Drill:**", id_map, children=[
            bullet("**Fetch Response Validation:** Always check `response.ok` before calling `response.json()`. `fetch()` only rejects on network loss, not on HTTP 404 or 500.", id_map),
            bullet("**Parallelization Audit:** Replace accidental sequential `await`s on independent API endpoints with `Promise.all()`.", id_map),
        ]),
        bullet("**2. Combine with Prior Units:**", id_map, children=[
            bullet("**Bridge to [[PRG-T00-C01-U01]]:** Map HTTP status codes (`401`, `403`, `500`) to appropriate user-facing error UI messages.", id_map),
        ]),
        bullet("**3. Common Traps & Edge Cases to Test:**", id_map, children=[
            bullet("**`Promise.all` Fast-Fail Trap:** If any Promise rejects in `Promise.all()`, the entire batch immediately rejects. Use `Promise.allSettled()` if you want all results regardless of individual failures.", id_map),
            bullet("**Floating Promise Trap:** Calling an async function without `await` or `.catch()` causes silent unhandled promise rejections.", id_map),
        ]),
        bullet("**4. Cross-Subject & Real-World Connection:**", id_map, children=[
            bullet("**Bridge to [[PRG-T01-C01-U06]] & [[PRG-T01-C01-U07]]:** Deep dive into the Microtask Queue and Promise cancellation in PRG-T01.", id_map),
            bullet("**Bridge to [[PRG-T03-C01]]:** Next.js Server Components and Server Actions execute asynchronous I/O across server-client boundaries.", id_map),
        ]),
        divider_block(),
        h2("4. Active Recall Questions", id_map),
        toggle_block("Does `window.fetch()` reject its Promise if the server responds with HTTP 404 Not Found?", [
            p_block("No! `fetch()` rejects its Promise ONLY if a network failure occurs (e.g. DNS resolution failure, network offline, connection reset). An HTTP `404` or `500` is considered a valid HTTP response and resolves the Promise with `response.ok === false`.", id_map),
        ], id_map),
        toggle_block("When should you choose `Promise.allSettled()` over `Promise.all()`?", [
            p_block("Use `Promise.all()` when all operations must succeed for the task to be valid (fail-fast semantics). Use `Promise.allSettled()` when tasks are independent and you want to inspect which succeeded and which failed without aborting the entire batch.", id_map),
        ], id_map),
        divider_block(),
        h2("5. My Implementation & Mistake Log", id_map),
        todo_item("Audit all `fetch()` calls to ensure `response.ok` is checked before parsing JSON.", id_map),
        todo_item("Wrap all asynchronous network operations in explicit `try/catch` error handlers.", id_map),
    ]


def build_prg_t00_c02_u06(id_map):
    return [
        callout_block(
            "**Learning Objective:** Master foundational TypeScript architecture: compile-time static type checking vs runtime type erasure, type annotations, interfaces, type aliases, union types, and the `tsc` compiler pipeline.\n"
            "**Expected Output:** Configure and author strictly typed TypeScript files under `strict: true`, define clear domain interfaces, and explain what happens to types during compilation.\n"
            "**Parent:** [[PRG-T00]] → [[PRG-T00-C02]] | **Next Unit:** [[PRG-T00-C02-U07]] | **Source:** [[R004]] (`TypeScript Handbook`)",
            id_map,
            color="blue_background",
        ),
        h2("1. Core Concepts & Architectural Mental Model", id_map),
        bullet("**1. Compile-Time Verification vs Runtime Type Erasure:**", id_map, children=[
            bullet("TypeScript runs strictly during compilation. It checks types, emits diagnostics, and then **strips away all types completely**, leaving clean JavaScript for the Node/browser engine to run.", id_map),
            bullet("Types have **zero runtime memory cost** and **zero runtime existence**. TypeScript cannot validate runtime data payloads received over the network without explicit runtime guards (e.g. Zod).", id_map),
        ]),
        bullet("**2. Basic Annotations & Type Inference:**", id_map, children=[
            bullet("Primitives: `string`, `number`, `boolean`, `null`, `undefined`.", id_map),
            bullet("Type Inference: TypeScript automatically infers types when initialized: `let count = 0;` infers `number` without requiring redundant `let count: number = 0;`.", id_map),
        ]),
        bullet("**3. Interfaces vs Type Aliases:**", id_map, children=[
            bullet("`interface User { id: string; name: string; }` describes object shapes and supports declaration merging.", id_map),
            bullet("`type ID = string | number;` defines unions, primitives, and complex computed types.", id_map),
        ]),
        bullet("**4. Union Types & Defensive Narrowing:**", id_map, children=[
            bullet("Union types (`string | null`) enforce that callers must handle both possibilities.", id_map),
            bullet("Type narrowing with `typeof` or `if (val !== null)` refines the type within the conditional block.", id_map),
        ]),
        divider_block(),
        h2("2. Code & Implementation Examples", id_map),
        h3("Example 1: Clean Domain Interface with Union State Narrowing", id_map),
        code_block(
            "// DOMAIN CONTRACT DEFINITION:\n"
            "interface Task {\n"
            "  id: string;\n"
            "  title: string;\n"
            "  status: 'pending' | 'in-progress' | 'completed';\n"
            "  dueDate?: string; // Optional property\n"
            "}\n\n"
            "function formatTaskLabel(task: Task): string {\n"
            "  // Type narrowing on union status\n"
            "  if (task.status === 'completed') {\n"
            "    return `[DONE] ${task.title}`;\n"
            "  }\n\n"
            "  const dateStr = task.dueDate ? ` (Due: ${task.dueDate})` : '';\n"
            "  return `[ACTIVE] ${task.title}${dateStr}`;\n"
            "}\n\n"
            "const task: Task = { id: 't1', title: 'Audit Foundation', status: 'in-progress' };\n"
            "console.log(formatTaskLabel(task));",
            "typescript",
        ),
        divider_block(),
        h2("3. Practice Guide", id_map),
        bullet("**1. Core Skills to Drill:**", id_map, children=[
            bullet("**Type Safety Invariant:** Enable `'strict': true` in `tsconfig.json`. This prohibits implicit `any` and enforces strict null checks (`strictNullChecks`).", id_map),
            bullet("**Compile-Time Check:** Run `tsc --noEmit` to verify code compiles with zero errors.", id_map),
        ]),
        bullet("**2. Combine with Prior Units:**", id_map, children=[
            bullet("**Bridge to [[PRG-T00-C02-U01]]:** Notice how TypeScript prevents `null` from being assigned to a `string` variable when `strictNullChecks` is active.", id_map),
        ]),
        bullet("**3. Common Traps & Edge Cases to Test:**", id_map, children=[
            bullet("**The `any` Trap:** Using `any` turns off the TypeScript type-checker completely for that expression, reintroducing runtime bugs. Avoid `any` at all costs; use `unknown` if the type is truly dynamic.", id_map),
            bullet("**Node 24 Native Type-Stripping Import Trap:** When using Node native TypeScript stripping, always use `import type { ... }` for pure types to prevent Node runtime import errors.", id_map),
        ]),
        bullet("**4. Cross-Subject & Real-World Connection:**", id_map, children=[
            bullet("**Bridge to [[PRG-T01-C02]]:** Advanced TypeScript (Generics, Discriminated Unions, Utility Types) is mastered in [[PRG-T01-C02]].", id_map),
            bullet("**Bridge to [[PRG-T02]] & [[PRG-T03]]:** React props and Next.js page params are authored as TypeScript interfaces.", id_map),
        ]),
        divider_block(),
        h2("4. Active Recall Questions", id_map),
        toggle_block("Do TypeScript type annotations exist in the JavaScript output executed by Node or the browser?", [
            p_block("No! TypeScript completely erases all type annotations, interfaces, and type aliases during compilation. The runtime executes pure ECMAScript and has zero awareness of TypeScript types.", id_map),
        ], id_map),
        toggle_block("Why is `unknown` safer than `any` in TypeScript?", [
            p_block("`any` completely disables the type checker, allowing you to call arbitrary methods or access properties without verification. In contrast, `unknown` forces you to perform explicit type narrowing (e.g. with `typeof` or type guards) before performing operations on the value.", id_map),
        ], id_map),
        divider_block(),
        h2("5. My Implementation & Mistake Log", id_map),
        todo_item("Configure `tsconfig.json` with `strict: true` and verify `tsc --noEmit` passes.", id_map),
        todo_item("Audit existing files to eliminate any explicit or implicit `any` types.", id_map),
    ]


def build_prg_t00_c02_u07(id_map):
    return [
        callout_block(
            "**Learning Objective:** Master systematic code reading, stack trace analysis, breakpoint debugging in Browser DevTools / VS Code, and isolating minimal reproducible bug scenarios.\n"
            "**Expected Output:** Read foreign codebases systematically, locate root causes of runtime exceptions using stack traces and breakpoints, and draft regression tests that prove the fix.\n"
            "**Parent:** [[PRG-T00]] → [[PRG-T00-C02]] | **Next Chapter:** [[PRG-T00-C03]] | **Source:** [[R003]] (`MDN JavaScript Guide`)",
            id_map,
            color="blue_background",
        ),
        h2("1. Core Concepts & Architectural Mental Model", id_map),
        bullet("**1. The Anatomy of an Error Stack Trace:**", id_map, children=[
            bullet("Error Name & Message: Identifies the exception type (`TypeError`, `RangeError`, `ReferenceError`) and the descriptive symptom.", id_map),
            bullet("Call Stack Frames: Read from top to bottom. The top frame indicates where the error exploded; lower frames show the sequence of function calls that led there.", id_map),
        ]),
        bullet("**2. The 4-Step Systematic Debugging Protocol:**", id_map, children=[
            bullet("1. **Reproduce:** Establish a deterministic, minimal set of inputs that reliably triggers the failure.", id_map),
            bullet("2. **Isolate:** Set breakpoints or log points to trace variable state right before the failure point.", id_map),
            bullet("3. **Identify Root Cause:** Distinguish between the superficial symptom (e.g. `undefined is not a function`) and the root architectural cause (e.g. missing API parameter).", id_map),
            bullet("4. **Verify & Regress:** Write an automated test reproducing the bug, apply the fix, and confirm all regression tests pass.", id_map),
        ]),
        bullet("**3. Modern Debugging Tools:**", id_map, children=[
            bullet("VS Code Debugger: Launch configurations with breakpoints, step-over (`F10`), step-into (`F11`), and watch expressions.", id_map),
            bullet("Browser DevTools Sources Panel: Conditional breakpoints, DOM mutation breakpoints, and pause on uncaught exceptions.", id_map),
        ]),
        divider_block(),
        h2("2. Code & Implementation Examples", id_map),
        h3("Example 1: Reading and Diagnosing a Real Stack Trace", id_map),
        code_block(
            "// STACK TRACE TRIAGE:\n"
            "// TypeError: Cannot read properties of undefined (reading 'length')\n"
            "//     at calculateAverage (/app/src/analytics.js:18:24)  <-- EXPLOSION POINT\n"
            "//     at processUserRecords (/app/src/analytics.js:34:12)\n"
            "//     at handleDashboardRequest (/app/src/server.js:45:9)\n\n"
            "// ROOT CAUSE ANALYSIS:\n"
            "// Line 18 in analytics.js called `items.length` without checking if `items` is an array.\n\n"
            "// FIXED DEFENSIVE CODE:\n"
            "function calculateAverage(items) {\n"
            "  if (!Array.isArray(items) || items.length === 0) {\n"
            "    return 0;\n"
            "  }\n"
            "  const sum = items.reduce((acc, val) => acc + val, 0);\n"
            "  return sum / items.length;\n"
            "}",
            "javascript",
        ),
        divider_block(),
        h2("3. Practice Guide", id_map),
        bullet("**1. Core Skills to Drill:**", id_map, children=[
            bullet("**Stack Trace Decoupling:** Given a 20-line stack trace from Node.js, immediately filter out internal Node core modules (`node:internal/...`) and focus on your application source files.", id_map),
            bullet("**Minimal Reproducer:** Strip down a 100-line buggy function into a 5-line standalone snippet that reproduces the defect in Node terminal.", id_map),
        ]),
        bullet("**2. Combine with Prior Units:**", id_map, children=[
            bullet("**Bridge to [[PRG-T00-C01-U08]]:** Use DevTools Console and Network tabs to correlate failed HTTP requests with JavaScript runtime exceptions.", id_map),
        ]),
        bullet("**3. Common Traps & Edge Cases to Test:**", id_map, children=[
            bullet("**Shotgun Debugging Trap:** Making random changes hoping the error disappears without understanding why. Always formulate a hypothesis and test it with a breakpoint or log.", id_map),
        ]),
        bullet("**4. Cross-Subject & Real-World Connection:**", id_map, children=[
            bullet("**Bridge to Code Standards:** Connects directly to our **Debugging Archetype** (`rules/04_code.md`) and the 6-Step Pedagogical Loop.", id_map),
            bullet("**Bridge to [[PRG-T08]]:** Automated testing in [[PRG-T08-C01]] formalizes bug reproduction via regression test suites.", id_map),
        ]),
        divider_block(),
        h2("4. Active Recall Questions", id_map),
        toggle_block("How should you read a call stack trace when an exception is thrown?", [
            p_block("Read from top to bottom. The top line gives the error type and descriptive message. The second line (top frame) indicates the exact file and line where the runtime crashed. Lower frames show the parent callers that triggered the function. Filter out framework/internal libraries to find the first frame under your source code control.", id_map),
        ], id_map),
        toggle_block("What is a minimal reproducible example (MRE)?", [
            p_block("An MRE is the smallest, simplest standalone piece of code that reliably produces the exact bug without extraneous dependencies, unrelated logic, or complex configuration. Isolating an MRE proves you have found the true root cause.", id_map),
        ], id_map),
        divider_block(),
        h2("5. My Implementation & Mistake Log", id_map),
        todo_item("Practice setting breakpoints in VS Code to inspect local variables at runtime.", id_map),
        todo_item("Diagnose and fix an unhandled exception using only stack trace analysis.", id_map),
    ]
