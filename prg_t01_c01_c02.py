# -*- coding: utf-8 -*-
"""
Instructional content for PRG-T01 Topic, Chapters C01-C03, and Units C01 (U01-U08) & C02 (U01-U09).
Follows 'Learning System — AI Implementation Rules'.
No emojis in page body blocks.
"""

TOPIC_DATA = {
    "full_id": "PRG-T01",
    "title": "JavaScript & TypeScript Engineering",
    "goal": "Write reliable JavaScript and TypeScript without relying on tutorials.",
    "prerequisites": "PRG-T00 — Foundation Audit (HTML/CSS/DOM fundamentals, Git workflow, HTTP basics, and CLI debugging)",
    "overview": [
        "JavaScript & TypeScript Engineering bridges the gap between copying working snippets from tutorials and engineering reliable, maintainable application code from first principles.",
        "To write production software independently, an engineer must hold two mental models simultaneously: the JavaScript runtime model (how the engine allocates memory, resolves lexical scope, binds 'this', delegates through prototypes, and schedules asynchronous microtasks/macrotasks) and the TypeScript static type model (how types act as sets of values, how control-flow narrowing refines types, and how generics and discriminated unions encode domain invariants at compile time).",
        "Finally, those two models converge in practical problem solving: decomposing ambiguous requirements into pure data transformations, selecting appropriate data structures (Array, Object, Map, Set), handling edge cases explicitly, and packaging tested utilities."
    ],
    "outcomes": [
        "Trace and predict JavaScript runtime behavior across lexical closures, dynamic 'this' binding, prototype delegation, ES modules, and the event loop (microtasks vs. macrotasks) without guessing.",
        "Design strict TypeScript domain models and API contracts using union types, custom type guards, generics, built-in utility types, and exhaustive discriminated unions under 'strict: true'.",
        "Decompose complex data transformation problems into composable, immutable array/object/collection pipelines with explicit error boundaries.",
        "Author, test, document, and package a reusable TypeScript utility toolkit that handles real-world edge cases."
    ],
    "chapters_summary": [
        ("PRG-T01-C01 — JavaScript Deep Dive (8 Units)", "Focuses on runtime execution semantics: Execution Context & Scope (U01), Closures (U02), 'this' & Binding (U03), Prototypes & Inheritance (U04), Modules (U05), Promises & Async/Await (U06), Event Loop & Concurrency (U07), and Error Handling Patterns (U08). Must be completed first so TypeScript types are grounded in actual runtime behavior."),
        ("PRG-T01-C02 — TypeScript for Application Code (9 Units)", "Layers compile-time guarantees over JavaScript: Type Annotations & Inference (U01), Primitive/Literal/Object Types (U02), Union Types (U03), Type Narrowing & Guards (U04), Generics (U05), Utility Types (U06), Discriminated Unions (U07), Strict Mode & tsconfig (U08), and Typing Functions & API Responses (U09)."),
        ("PRG-T01-C03 — Problem Solving & Utility Toolkit (8 Units)", "Synthesizes runtime JS and static TS into practical software engineering: Problem Decomposition (U01), Array Transformations (U02), Object Transformations (U03), Map/Set & Data Structures (U04), Reusable Generic Utilities (U05), Error Handling & Edge Cases (U06), Testing Utility Functions (U07), and Packaging & Documentation (U08).")
    ],
    "resources": [
        ("R003 — MDN – JavaScript Guide (https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide)", "Status: URL Accessible | Content Accessible | Content Verified (HTTP 200). Primary authoritative reference for PRG-T01-C01 and runtime data structures/transformations in PRG-T01-C03."),
        ("R004 — TypeScript Handbook (https://www.typescriptlang.org/docs/handbook/intro.html)", "Status: URL Accessible | Content Accessible | Content Verified (HTTP 200). Primary authoritative reference for PRG-T01-C02 and generic utility typing in PRG-T01-C03."),
        ("Source Gap & Supplementary Note", "R003 and R004 comprehensively cover JavaScript runtime semantics and TypeScript language features, but do not directly cover automated test runner workflows (PRG-T01-C03-U07) or npm package distribution/TSDoc conventions (PRG-T01-C03-U08). Those two units explicitly distinguish supplementary engineering standards (Node.js built-in test runner / Vitest and package.json exports) from R003/R004 content.")
    ],
    "final_review": [
        "Can you explain the difference between a runtime ReferenceError/TypeError in JavaScript and a compile-time type error in TypeScript, and how strict mode bridges the two?",
        "Given an untyped asynchronous data-fetching module with subtle race conditions and mutation bugs, can you refactor it into a strictly typed, immutable, tested TypeScript module without consulting a tutorial?",
        "Review all 25 Units in the linked Learning Units view: verify that every Unit marked 'Done' has an honest Mastery (0-4) score and a scheduled Next Review date."
    ]
}

CHAPTERS_DATA = {
    "PRG-T01-C01": {
        "title": "JavaScript Deep Dive",
        "objective": "Master scope, closures, this, prototypes, modules, promises and event loop.",
        "criteria": "Explain and demonstrate async flow, closures and object behavior.",
        "role": "Serves as the runtime foundation of PRG-T01. Because TypeScript compiles down to JavaScript and erases all types at runtime, you cannot debug memory leaks, stale closures, lost 'this' context, or async race conditions unless you understand how the JavaScript engine executes code.",
        "mental_model_title": "Runtime Mental Model & Concept Map",
        "mental_model_points": [
            "Lexical Environment & Call Stack (U01 -> U02): Every function invocation creates an Execution Context with a Lexical Environment. Because scope chains are wired where functions are defined (lexically), inner functions retain live references to outer bindings even after the outer stack frame pops (Closures).",
            "Object Delegation & Dynamic Context (U03 -> U04): Unlike lexical scope, 'this' is determined at call time based on how a function is invoked (implicit, explicit, 'new', or lexical arrow). Property lookups walk the [[Prototype]] chain via delegation rather than copying class blueprints.",
            "Module Encapsulation (U05): ES Modules provide file-level lexical scope, live read-only bindings, and deterministic static dependency graphs.",
            "Asynchronous Scheduling & Failure Propagation (U06 -> U07 -> U08): Single-threaded JavaScript achieves concurrency via the Event Loop—draining the entire Microtask Queue (Promise reactions, queueMicrotask) after each task before picking the next Macrotask (timers, I/O), while propagating synchronous throws and asynchronous rejections through structured error boundaries."
        ],
        "units_sequence": [
            "PRG-T01-C01-U01 — Execution Context and Scope: Hoisting, TDZ, lexical environment, and call stack.",
            "PRG-T01-C01-U02 — Closures: Lexical environment retention, private state, and loop capture pitfalls.",
            "PRG-T01-C01-U03 — this and Binding: Call-site rules, call/apply/bind, and arrow function lexical 'this'.",
            "PRG-T01-C01-U04 — Prototypes and Inheritance: [[Prototype]] chain, Object.create, and ES6 class sugar.",
            "PRG-T01-C01-U05 — Modules and Module Systems: ESM vs. CJS, live bindings, and circular dependency behavior.",
            "PRG-T01-C01-U06 — Promises and Async/Await: Promise states, chaining, combinators (all, allSettled, race, any), and async/await.",
            "PRG-T01-C01-U07 — Event Loop and Concurrency: Call stack, microtask queue vs. macrotask queue, and starvation.",
            "PRG-T01-C01-U08 — Error Handling Patterns: Custom Error subclasses, error cause chains, and async rejection handling."
        ],
        "resources": [
            "R003 — MDN – JavaScript Guide (https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide): Verified accessible (HTTP 200). Covers expressions, closures, 'this', inheritance and the prototype chain, JavaScript modules, using promises, and concurrency model / event loop."
        ],
        "challenge_title": "Chapter Integration Lab: Async & Closure Diagnostic Suite",
        "challenge_points": [
            "Build a 'createRateLimitedQueue(concurrency)' utility using closures to maintain private active/pending queues without global variables.",
            "Ensure methods preserve 'this' when passed as callbacks or use closure-bound functions.",
            "Predict and verify with logs the exact execution order of synchronous setup, Promise microtasks, and setTimeout macrotasks.",
            "Wrap task execution in structured error handling that preserves original stack traces via 'new Error(msg, { cause })'."
        ]
    },
    "PRG-T01-C02": {
        "title": "TypeScript for Application Code",
        "objective": "Use unions, narrowing, generics, utility types, discriminated unions and strict mode.",
        "criteria": "Model API responses and domain entities with safe types.",
        "role": "Builds directly on PRG-T01-C01 by teaching you how to express JavaScript runtime invariants in TypeScript's static type system so invalid states become unrepresentable at compile time.",
        "mental_model_title": "Type System Architecture & Set-Theoretic Mental Model",
        "mental_model_points": [
            "Types as Sets of Values (U01 -> U02 -> U03): A type defines the set of possible runtime values ('never' is the empty set, literal '\"ok\"' is a single-element set, 'string' is all strings, 'unknown' is the universal set). Union ('A | B') is set union; intersection ('A & B') is set intersection.",
            "Control-Flow Narrowing (U04 -> U07): Because values often start as broad unions, TypeScript inspects runtime checks ('typeof', 'in', 'instanceof', user-defined type predicates, and discriminant property checks) to narrow the type within conditional branches and enforce exhaustiveness via 'never'.",
            "Type-Level Functions & Transformations (U05 -> U06): Generics parameterize types so relationships between inputs and outputs are preserved without losing specificity (unlike 'any'). Built-in utility types ('Partial', 'Pick', 'Omit', 'Record', 'ReturnType') transform existing types without duplication.",
            "Compiler Strictness & Boundary Contracts (U08 -> U09): 'strict' mode flags ('strictNullChecks', 'noImplicitAny', 'useUnknownInCatchVariables') eliminate silent unsoundness, while typed API response wrappers bridge untrusted external JSON ('unknown') and trusted domain models."
        ],
        "units_sequence": [
            "PRG-T01-C02-U01 — Type Annotations and Type Inference: Explicit annotations vs. inference, widening, and 'as const'.",
            "PRG-T01-C02-U02 — Primitive, Literal and Object Types: Structural typing, excess property checks, 'readonly', and index signatures.",
            "PRG-T01-C02-U03 — Union Types: Modeling alternative shapes and shared member access rules.",
            "PRG-T01-C02-U04 — Type Narrowing and Guards: Control-flow analysis, 'typeof'/'in', and 'x is T' predicates.",
            "PRG-T01-C02-U05 — Generics: Type parameters, constraints ('extends'), and key constraints ('K extends keyof T').",
            "PRG-T01-C02-U06 — Utility Types: 'Partial', 'Required', 'Readonly', 'Pick', 'Omit', 'Record', 'ReturnType', 'Parameters'.",
            "PRG-T01-C02-U07 — Discriminated Unions: Tagged unions, state machines, and 'assertNever' exhaustiveness checking.",
            "PRG-T01-C02-U08 — Strict Mode and tsconfig: Critical compiler flags and module resolution settings.",
            "PRG-T01-C02-U09 — Typing Functions and API Responses: Function overloads, callbacks, generic fetch wrappers, and runtime validation boundaries."
        ],
        "resources": [
            "R004 — TypeScript Handbook (https://www.typescriptlang.org/docs/handbook/intro.html): Verified accessible (HTTP 200). Covers Everyday Types, Narrowing, More on Functions, Object Types, Generics, Keyof/Typeof operators, Utility Types, and tsconfig reference."
        ],
        "challenge_title": "Chapter Modeling Lab: Type-Safe API Client & Domain State",
        "challenge_points": [
            "Define a discriminated union 'AsyncState<T, E>' representing 'idle', 'loading', 'success', and 'error' states without impossible boolean combinations.",
            "Write a generic 'requestJson<T>(url: string, guard: (data: unknown) => data is T): Promise<Result<T, ApiError>>' function under 'strict: true'.",
            "Derive creation and patch payload types from a core domain entity using 'Omit', 'Pick', and 'Partial' without duplicating property definitions."
        ]
    },
    "PRG-T01-C03": {
        "title": "Problem Solving & Utility Toolkit",
        "objective": "Practice decomposition, array/object transformations, error handling and reusable utilities.",
        "criteria": "Publish a small typed utility package or CLI with tests.",
        "role": "Integrates the runtime mastery of C01 and the static type mastery of C02 into daily engineering craftsmanship: breaking down complex problems, transforming collections immutably, choosing optimal data structures, handling edge cases, and shipping tested, documented utility modules.",
        "mental_model_title": "Toolkit Engineering Workflow & Design Principles",
        "mental_model_points": [
            "Decomposition & Input-Output Contracts (U01): Before writing code, specify exact input types, output types, invariants, and edge cases; break complex workflows into small, composable, single-responsibility pure functions.",
            "Immutable Collection Pipelines & Data Structure Selection (U02 -> U03 -> U04): Transform arrays and objects without mutating caller inputs, and replace O(n^2) nested array scans with O(1) 'Map' and 'Set' lookups.",
            "Generic Abstraction & Defensive Edge-Case Design (U05 -> U06): Extract reusable generic helpers ('groupBy', 'keyBy', 'chunk', 'retry') that preserve caller types while explicitly handling empty inputs, 'null'/'undefined', 'NaN', and boundary conditions.",
            "Verification & Distribution (U07 -> U08): Prove correctness with automated unit tests covering happy paths, boundaries, and error paths, then package with clean TypeScript declaration files ('.d.ts') and TSDoc."
        ],
        "units_sequence": [
            "PRG-T01-C03-U01 — Problem Decomposition: Breaking requirements into pure steps, invariants, and data contracts.",
            "PRG-T01-C03-U02 — Array Transformations: Immutable 'map', 'filter', 'reduce', 'flatMap', and 'toSorted' pipelines.",
            "PRG-T01-C03-U03 — Object Transformations: 'Object.entries', 'Object.fromEntries', shallow vs. deep cloning, and structural updates.",
            "PRG-T01-C03-U04 — Map, Set and Common Data Structures: 'Map' vs. plain objects, 'Set' operations, 'WeakMap', and time complexity.",
            "PRG-T01-C03-U05 — Reusable Generic Utilities: Designing type-safe 'groupBy', 'pick', 'omit', 'debounce', and 'retry'.",
            "PRG-T01-C03-U06 — Error Handling and Edge Cases: Boundary values, Result pattern vs. exceptions, and defensive validation.",
            "PRG-T01-C03-U07 — Testing Utility Functions: Arrange-Act-Assert, edge-case test matrices, and testing async/throwing code.",
            "PRG-T01-C03-U08 — Packaging and Documentation: 'package.json' exports, '.d.ts' generation, semantic versioning, and TSDoc."
        ],
        "resources": [
            "R003 — MDN – JavaScript Guide (https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide): Verified accessible (HTTP 200). Covers Indexed Collections (Array), Keyed Collections (Map, Set, WeakMap, WeakSet), and working with objects.",
            "R004 — TypeScript Handbook (https://www.typescriptlang.org/docs/handbook/intro.html): Verified accessible (HTTP 200). Covers generic constraints, utility types, and declaration emit.",
            "Source Gap Note (U07 & U08): Automated unit testing frameworks and npm package publishing are supplemented beyond R003/R004 using standard Node.js/TypeScript ecosystem conventions (annotated explicitly inside U07 and U08)."
        ],
        "challenge_title": "Chapter Capstone Project: Typed Utility Library with Tests",
        "challenge_points": [
            "Implement a cohesive TypeScript utility library containing at least 5 generic utilities ('groupBy', 'chunk', 'pick', 'omit', 'retryAsync').",
            "Write a comprehensive test suite covering normal inputs, empty collections, unicode/special keys, and async rejection retries.",
            "Configure 'tsconfig.json' and 'package.json' to emit both JS and '.d.ts' declarations with TSDoc comments and examples."
        ]
    }
}

UNITS_C01_C02 = {
    "PRG-T01-C01-U01": {
        "title": "Execution Context and Scope",
        "chapter": "C01",
        "order": 1,
        "prereq": "PRG-T00 — Foundation Audit",
        "source": "R003 — MDN – JavaScript Guide (Grammar and types; Functions). Verified accessible (HTTP 200).",
        "concepts_title": "Runtime Mechanics & Mental Model",
        "concepts": [
            "Execution Context Phases: Every time the JavaScript engine runs global code, a function, or an ES module, it creates an Execution Context in two phases: (1) Creation Phase—sets up the Lexical Environment, binds declarations, and initializes 'var' to 'undefined' while leaving 'let'/'const' uninitialized inside the Temporal Dead Zone (TDZ); (2) Execution Phase—executes statements line by line and assigns values.",
            "Lexical (Static) Scope vs. Call Stack: Scope is determined by where functions and blocks are physically written in source code (lexical nesting), NOT by where they are called on the Call Stack. Each Lexical Environment holds an Environment Record (local bindings) and an outer reference pointing to its parent lexical scope.",
            "Declaration Semantics ('const' vs. 'let' vs. 'var'): 'let' and 'const' are block-scoped ('{ ... }') and remain in the TDZ from the start of the block until their declaration line is evaluated. 'var' is function-scoped (ignoring 'if'/'for' blocks) and hoisted with a default value of 'undefined'. Function declarations ('function fn() {}') are hoisted with their full body, whereas function expressions ('const fn = () => {}') obey the TDZ of their binding."
        ],
        "code_lang": "javascript",
        "code": """// 1. Hoisting & Temporal Dead Zone (TDZ)
console.log(legacyCount); // undefined (var is hoisted and initialized to undefined)
// console.log(modernCount); // ReferenceError: Cannot access 'modernCount' before initialization (TDZ)

var legacyCount = 10;
let modernCount = 20;

// 2. Lexical Scope vs. Call Stack Order
const mode = "lexical-global";

function printMode() {
  // Resolves 'mode' via the outer lexical environment where printMode was defined,
  // NOT the caller's environment on the call stack.
  return mode;
}

function callerWrapper() {
  const mode = "caller-local";
  return printMode();
}

console.log(callerWrapper()); // "lexical-global"
""",
        "exercise": [
            "Implementation Task: Write a small diagnostic script demonstrating three distinct variable shadowing levels (module/global, function, and 'if' block) and annotate which Lexical Environment resolves each identifier.",
            "Debugging Task: Given a legacy 'for (var i = 0; i < 3; i++)' loop that schedules callbacks or mutates shared state across blocks, explain why 'var' leaks out of the loop block and refactor it using block-scoped 'let'/'const'."
        ],
        "recall": [
            ("What happens during the Creation Phase of an Execution Context for 'var', 'let'/'const', and 'function' declarations?", "During creation, 'function' declarations are stored in the environment record with their complete function object; 'var' bindings are created and initialized to 'undefined'; 'let' and 'const' bindings are created but remain uninitialized in the Temporal Dead Zone (TDZ) until execution reaches their declaration."),
            ("Why does a function defined in Module A that is invoked inside Module B resolve free variables from Module A instead of Module B?", "Because JavaScript uses lexical (static) scoping: a function's outer environment reference is set when the function is created based on its physical location in source code, independent of the runtime call stack."),
            ("Does 'const' make an object or array immutable in JavaScript?", "No. 'const' only prevents rebinding the identifier to a different memory reference. The properties or elements of the referenced object/array can still be mutated unless frozen with 'Object.freeze'."),
            ("How does the Temporal Dead Zone (TDZ) catch bugs that 'var' hoisting silently hides?", "Accessing a 'let' or 'const' binding before its declaration throws an immediate 'ReferenceError' instead of silently evaluating to 'undefined' and propagating 'NaN' or subtle logic bugs downstream.")
        ]
    },
    "PRG-T01-C01-U02": {
        "title": "Closures",
        "chapter": "C01",
        "order": 2,
        "prereq": "PRG-T01-C01-U01 (Execution Context and Scope)",
        "source": "R003 — MDN – JavaScript Guide (Closures). Verified accessible (HTTP 200).",
        "concepts_title": "Runtime Mechanics & Mental Model",
        "concepts": [
            "What a Closure Actually Is: A closure is the combination of a function and a persistent reference to the Lexical Environment in which that function was created. When an inner function is returned or passed outside its enclosing function, the garbage collector keeps the outer Lexical Environment alive in heap memory as long as the inner function is reachable.",
            "Live Bindings, Not Snapshots: Closures capture live variable bindings in the outer Environment Record, not frozen copies of values at the moment the inner function was created. If the outer variable changes later, the closure reads the updated value unless a new block scope ('let') or parameter scope was created per iteration.",
            "Practical Engineering Uses & Memory Caveats: Closures power data encapsulation (private state without classes), function factories, partial application, and memoization/debouncing. However, unintentionally capturing large DOM nodes or buffers inside long-lived event listeners prevents garbage collection."
        ],
        "code_lang": "javascript",
        "code": """// 1. Data Encapsulation with Independent Closure Instances
function createBoundedCounter(initial = 0, max = 10) {
  let count = initial; // Private to each createBoundedCounter call

  return {
    increment() {
      if (count < max) count += 1;
      return count;
    },
    getValue() {
      return count;
    }
  };
}

const counterA = createBoundedCounter(0, 2);
const counterB = createBoundedCounter(5, 10);
console.log(counterA.increment(), counterA.increment(), counterA.increment()); // 1, 2, 2
console.log(counterB.getValue()); // 5 (completely isolated environment)

// 2. Live Binding Pitfall vs. Per-Iteration Block Scope
const handlersVar = [];
for (var i = 0; i < 3; i++) {
  handlersVar.push(() => i); // All 3 closures share the single function-scoped 'i'
}
console.log(handlersVar.map(fn => fn())); // [3, 3, 3]

const handlersLet = [];
for (let j = 0; j < 3; j++) {
  handlersLet.push(() => j); // 'for (let j...)' creates a fresh lexical binding per iteration
}
console.log(handlersLet.map(fn => fn())); // [0, 1, 2]
""",
        "exercise": [
            "Implementation Task: Implement a 'once(fn)' higher-order function using a closure that executes 'fn' on the first call, caches its return value in private closure state, and returns the cached value on all subsequent calls.",
            "Debugging Task: Diagnose a ' stale closure' bug where an interval callback logs an outdated configuration value because it captured an old binding from an outer render/setup call, and fix it so it reads the latest state."
        ],
        "recall": [
            ("Why doesn't the outer function's local variable get garbage-collected when the outer function finishes executing and pops off the Call Stack?", "Because the returned inner function holds an internal '[[Environment]]' reference to the outer Lexical Environment record; as long as the inner function is reachable from a root, the GC keeps that environment record in heap memory."),
            ("Do closures capture the value of a variable at the time the closure is created, or a reference to the variable binding?", "They capture a reference to the variable binding in the Lexical Environment. Any mutation to that binding before the closure runs will be visible when the closure executes."),
            ("Why do two calls to 'createBoundedCounter()' not overwrite each other's 'count' variable?", "Every invocation of 'createBoundedCounter()' allocates a brand-new Lexical Environment record on the heap, so each returned object closes over its own separate 'count' binding."),
            ("How does 'for (let i = 0; ...)' solve the classic loop closure bug compared to 'for (var i = 0; ...)'?", "In a 'for (let ...)' loop, the JS specification creates a new Lexical Environment for each iteration of the loop body and copies the incremented value into the new binding, whereas 'var' creates only one shared binding for the entire enclosing function.")
        ]
    },
    "PRG-T01-C01-U03": {
        "title": "this and Binding",
        "chapter": "C01",
        "order": 3,
        "prereq": "PRG-T01-C01-U01, PRG-T01-C01-U02",
        "source": "R003 — MDN – JavaScript Guide (Functions; Working with objects). Verified accessible (HTTP 200).",
        "concepts_title": "Runtime Mechanics & Mental Model",
        "concepts": [
            "Call-Site Determination (Dynamic Context): Unlike scope (which is lexical), 'this' inside a regular 'function' is bound dynamically at runtime based on HOW the function is called (its call-site), following four precedence rules from highest to lowest:",
            "Precedence Hierarchy: (1) 'new' Binding ('new Fn()')—'this' is the newly constructed object; (2) Explicit Binding ('fn.call(ctx, ...)', 'fn.apply(ctx, args)', 'fn.bind(ctx)')—'this' is forced to 'ctx'; (3) Implicit/Method Binding ('obj.fn()')—'this' is the receiver object 'obj' to the left of the dot at call time; (4) Default Binding ('fn()')—'this' is 'undefined' in strict mode (and ES modules) or 'globalThis' in sloppy mode.",
            "Arrow Functions & Lexical 'this': Arrow functions ('() => {}') do NOT have their own 'this', 'arguments', or 'prototype'. They resolve 'this' lexically from the enclosing scope just like a normal variable, and '.call()', '.apply()', or '.bind()' cannot override an arrow function's 'this'."
        ],
        "code_lang": "javascript",
        "code": """"use strict";

const timerService = {
  label: "OrderProcessor",
  count: 0,

  // Pitfall: Passing a method reference strips the receiver ('obj.') at the call site
  tickMethod() {
    this.count += 1;
    return `${this.label}: ${this.count}`;
  },

  // Solution A: Arrow function inside a method inherits the method's 'this' lexically
  startWithArrow() {
    const callback = () => this.tickMethod();
    return callback();
  }
};

const detachedTick = timerService.tickMethod;
// detachedTick(); // TypeError: Cannot read properties of undefined (reading 'count')

// Solution B: Explicit binding with .bind() or .call()
const boundTick = timerService.tickMethod.bind(timerService);
console.log(boundTick()); // "OrderProcessor: 1"
console.log(timerService.tickMethod.call({ label: "Custom", count: 99 })); // "Custom: 100"
console.log(timerService.startWithArrow()); // "OrderProcessor: 2"
""",
        "exercise": [
            "Implementation Task: Write a small 'EventEmitter' or controller class where a method is passed as a callback to 'Array.prototype.map' or 'setTimeout', and demonstrate fixing lost 'this' context using both '.bind()' and a lexical arrow wrapper.",
            "Debugging Task: Explain why defining an object literal method as an arrow function ('const user = { name: \"Ada\", greet: () => this.name }') fails to read 'user.name' and fix the bug."
        ],
        "recall": [
            ("What are the four call-site rules for 'this' in a regular function, ordered from highest to lowest precedence?", "1. 'new' binding ('new fn()'), 2. Explicit binding ('call', 'apply', 'bind'), 3. Implicit method binding ('obj.fn()'), 4. Default binding ('fn()' -> 'undefined' in strict mode)."),
            ("Why does 'const fn = obj.method; fn();' lose its 'this' binding even though 'method' was defined inside 'obj'?", "Because 'this' in a regular function depends solely on the call-site expression. Calling 'fn()' is a plain unprefixed invocation (Default Binding), so 'this' becomes 'undefined' in strict mode."),
            ("What happens if you call 'arrowFn.call(otherObj)' on an arrow function?", "The 'otherObj' argument is completely ignored for 'this'. Arrow functions have no '[[ThisMode]]' binding of their own and always look up 'this' in their enclosing lexical environment."),
            ("Why does an arrow function defined directly as a property on an object literal ('const obj = { run: () => this }') NOT bind 'this' to 'obj'?", "Object literals '{ ... }' do not create a new lexical scope or 'this' binding; the arrow function inherits 'this' from the surrounding module or function scope outside 'obj'.")
        ]
    },
    "PRG-T01-C01-U04": {
        "title": "Prototypes and Inheritance",
        "chapter": "C01",
        "order": 4,
        "prereq": "PRG-T01-C01-U03 (this and Binding)",
        "source": "R003 — MDN – JavaScript Guide (Inheritance and the prototype chain). Verified accessible (HTTP 200).",
        "concepts_title": "Runtime Mechanics & Mental Model",
        "concepts": [
            "Prototype Delegation Chain: Every JavaScript object has an internal '[[Prototype]]' link (inspected via 'Object.getPrototypeOf(obj)') pointing either to another object or to 'null'. When reading 'obj.prop', the engine checks 'obj's own properties first; if missing, it walks up the '[[Prototype]]' chain until it finds the property or reaches 'Object.prototype -> null'.",
            "Property Shadowing & Mutation vs. Lookup: Reading a property traverses the prototype chain, but writing 'obj.prop = value' creates or updates an OWN property directly on 'obj' (unless 'prop' is a setter on the prototype). Shared methods belong on the prototype so thousands of instances share one function in memory.",
            "ES6 'class' Syntax as Prototype Sugar: 'class Sub extends Base' sets up two prototype links under the hood: 'Sub.prototype.[[Prototype]] === Base.prototype' (for instance method delegation) and 'Sub.[[Prototype]] === Base' (for static method delegation). 'Object.create(proto)' creates a clean object whose '[[Prototype]]' is explicitly set to 'proto' (or 'null' for dictionary maps)."
        ],
        "code_lang": "javascript",
        "code": """// 1. ES6 Class Hierarchy & Underlying Prototype Links
class HttpClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl; // Own property on each instance
  }
  buildUrl(path) {
    // Shared on HttpClient.prototype
    return `${this.baseUrl.replace(/\\/+$/, "")}/${path.replace(/^\\/+/, "")}`;
  }
}

class AuthenticatedClient extends HttpClient {
  constructor(baseUrl, token) {
    super(baseUrl);
    this.token = token;
  }
  getHeaders() {
    return { Authorization: `Bearer ${this.token}` };
  }
}

const client = new AuthenticatedClient("https://api.example.com/", "sec_123");
console.log(client.buildUrl("/users")); // "https://api.example.com/users"
console.log(Object.hasOwn(client, "baseUrl")); // true (own property)
console.log(Object.hasOwn(client, "buildUrl")); // false (delegated via prototype chain)
console.log(Object.getPrototypeOf(client) === AuthenticatedClient.prototype); // true
console.log(Object.getPrototypeOf(AuthenticatedClient.prototype) === HttpClient.prototype); // true
""",
        "exercise": [
            "Implementation Task: Implement a two-level class hierarchy ('StorageAdapter' -> 'MemoryStorageAdapter') and write a helper 'inspectChain(instance)' that walks 'Object.getPrototypeOf' until 'null', returning the array of constructor names and own property keys at each level.",
            "Debugging Task: Fix a bug where a developer attached a shared array (' Base.prototype.items = [] ') on a prototype, causing 'instanceA.items.push(1)' to pollute 'instanceB.items'."
        ],
        "recall": [
            ("What is the difference between 'fn.prototype' and 'Object.getPrototypeOf(obj)'?", "'fn.prototype' is an object property on a constructor function that gets assigned as the '[[Prototype]]' of instances created with 'new fn()'. 'Object.getPrototypeOf(obj)' returns the actual internal '[[Prototype]]' link of any object 'obj'."),
            ("Why is 'Object.hasOwn(obj, key)' preferred over the 'in' operator ('key in obj') when checking object dictionary keys?", "The 'in' operator checks the entire prototype chain (so '\"toString\" in {}' is 'true'), whereas 'Object.hasOwn(obj, key)' only returns 'true' if 'key' is an own property directly on 'obj'."),
            ("Why does putting a mutable array or object on a prototype cause bugs across instances, while putting a primitive number on a prototype does not when reassigned?", "Mutating 'instance.arr.push(x)' reads 'arr' from the prototype and mutates the shared array in place. Reassigning 'instance.count = 2' creates a new own property 'count' on 'instance', shadowing the prototype property."),
            ("What is the prototype of an object created with 'Object.create(null)' and when is it useful?", "Its '[[Prototype]]' is 'null' (it does not inherit from 'Object.prototype'), making it immune to prototype pollution when used as a pure string-keyed dictionary.")
        ]
    },
    "PRG-T01-C01-U05": {
        "title": "Modules and Module Systems",
        "chapter": "C01",
        "order": 5,
        "prereq": "PRG-T01-C01-U01 (Execution Context and Scope)",
        "source": "R003 — MDN – JavaScript Guide (JavaScript modules). Verified accessible (HTTP 200).",
        "concepts_title": "Runtime Mechanics & Mental Model",
        "concepts": [
            "ES Modules (ESM) vs. CommonJS (CJS): ESM ('import'/'export') is the official language standard: imports are static (parsed before execution, enabling bundler tree-shaking), top-level 'this' is 'undefined', strict mode is always on, and top-level 'await' is supported. CommonJS ('require'/'module.exports') is dynamic and synchronous at runtime.",
            "Singleton Evaluation & Live Read-Only Bindings: Each module specifier is evaluated only ONCE per realm and cached in the module map; every importer receives the same singleton module instance. Furthermore, ESM exports are LIVE read-only bindings—if the exporting module updates an exported 'let' variable via an exported function, importers immediately observe the new value, though importers cannot reassign the imported binding directly.",
            "Named vs. Default Exports & Dynamic 'import()': Named exports ('export function parse() {}') enforce consistent symbol names across the codebase and simplify refactoring and tree-shaking. 'import(\"./feature.js\")' returns a Promise for lazy code-splitting at runtime."
        ],
        "code_lang": "javascript",
        "code": """// --- counterModule.js (ESM) ---
export let activeConnections = 0;

export function openConnection() {
  activeConnections += 1; // Mutates the live binding inside the defining module
  return activeConnections;
}

export function closeConnection() {
  activeConnections = Math.max(0, activeConnections - 1);
  return activeConnections;
}

// --- app.js (ESM Importer) ---
// import { activeConnections, openConnection } from "./counterModule.js";
// console.log(activeConnections); // 0
// openConnection();
// console.log(activeConnections); // 1 (live binding reflects updated value!)
// activeConnections = 99;         // TypeError: Assignment to constant variable (read-only view)

// Lazy loading a heavy module on demand:
async function runReportIfNeeded(shouldRun) {
  if (!shouldRun) return null;
  const { generateReport } = await import("./heavyReport.js");
  return generateReport();
}
""",
        "exercise": [
            "Implementation Task: Structure a 3-file ES Module mini-feature ('config.js', 'logger.js', 'main.js') using named exports, demonstrating singleton module initialization and dynamic 'await import()' for an optional plugin.",
            "Debugging Task: Diagnose a circular dependency bug where Module A imports a value from Module B and calls it at the top level before Module B finishes evaluating its 'const' initialization (hitting the TDZ)."
        ],
        "recall": [
            ("What does it mean that ES Module imports are 'live read-only bindings' compared to CommonJS 'require()'?", "In CommonJS, 'const { count } = require(\"./mod\")' copies the primitive value at the moment 'require' runs. In ESM, 'import { count } from \"./mod.js\"' creates a live view into the exporting module's Environment Record—changes made inside 'mod.js' are immediately visible to the importer, but the importer cannot reassign 'count'."),
            ("If three different files import './dbClient.js', how many times does the top-level code inside './dbClient.js' execute?", "Exactly once. The runtime caches the evaluated module record in its module map and shares the same exports across all importers."),
            ("Why do static 'import' and 'export' declarations enable tree-shaking in bundlers whereas dynamic 'require(variable)' calls do not?", "Static 'import'/'export' statements must appear at the top level with string literal specifiers, allowing the bundler to build the complete dependency graph and prune unused exports via static AST analysis before running any code."),
            ("Why should 'index.js' barrel files that re-export everything ('export * from ...') be used cautiously in large applications?", "Importing a single helper from an unoptimized barrel file can force the runtime or test runner to load and evaluate every module re-exported by the barrel, slowing startup and increasing circular dependency risks.")
        ]
    },
    "PRG-T01-C01-U06": {
        "title": "Promises and Async/Await",
        "chapter": "C01",
        "order": 6,
        "prereq": "PRG-T01-C01-U02 (Closures), PRG-T01-C01-U05 (Modules)",
        "source": "R003 — MDN – JavaScript Guide (Using promises). Verified accessible (HTTP 200).",
        "concepts_title": "Runtime Mechanics & Mental Model",
        "concepts": [
            "Promise State Machine: A Promise represents the eventual result of an asynchronous operation and transitions irreversibly once: 'pending' -> either 'fulfilled' (with a 'value') OR 'rejected' (with a 'reason'). Once settled, its state and value can never change.",
            "Chaining & 'async'/'await' Semantics: Every '.then()', '.catch()', and '.finally()' returns a brand-new Promise. An 'async' function ALWAYS wraps its return value in 'Promise.resolve()'. The 'await' keyword pauses execution of the 'async' function body, unwraps the awaited Promise, and resumes the remainder of the function inside a microtask.",
            "Concurrency Combinators (Sequential vs. Parallel): Using 'await fetch(a); await fetch(b);' in a loop runs independent requests sequentially (slow). Use 'Promise.all([p1, p2])' (fail-fast if any rejects), 'Promise.allSettled([p1, p2])' (waits for all and returns '{ status, value | reason }' objects), 'Promise.race([p1, timeout])' (first to settle wins), or 'Promise.any([p1, p2])' (first to fulfill wins; rejects with 'AggregateError' only if all reject)."
        ],
        "code_lang": "javascript",
        "code": """// 1. Sequential Pitfall vs. Concurrent Execution with Timeout
function withTimeout(promise, ms) {
  let timerId;
  const timeoutPromise = new Promise((_, reject) => {
    timerId = setTimeout(() => reject(new Error(`Timed out after ${ms}ms`)), ms);
  });
  return Promise.race([promise, timeoutPromise]).finally(() => clearTimeout(timerId));
}

async function fetchUserProfilesConcurrently(userIds, fetchUser) {
  // Launch all independent requests in parallel rather than awaiting inside a for-loop
  const results = await Promise.allSettled(
    userIds.map(id => withTimeout(fetchUser(id), 2000))
  );

  const succeeded = [];
  const failed = [];
  for (const [index, res] of results.entries()) {
    if (res.status === "fulfilled") {
      succeeded.push(res.value);
    } else {
      failed.push({ userId: userIds[index], error: res.reason.message });
    }
  }
  return { succeeded, failed };
}
""",
        "exercise": [
            "Implementation Task: Write a 'fetchWithRetry(fn, { retries, delayMs })' async utility that awaits 'fn()', catches transient failures, waits 'delayMs' using a Promise-wrapped 'setTimeout', and rethrows the final error if all attempts fail.",
            "Debugging Task: Identify and fix two bugs in a function that uses 'array.forEach(async item => { await save(item); })' (ignoring returned promises) and 'return await work()' without 'try/catch' vs. inside 'try/catch'."
        ],
        "recall": [
            ("Compare 'Promise.all', 'Promise.allSettled', 'Promise.race', and 'Promise.any' when one of three input promises rejects immediately.", "'Promise.all' rejects immediately; 'Promise.allSettled' waits for the other two to settle and resolves with an array of status objects; 'Promise.race' rejects immediately because the rejecting promise settled first; 'Promise.any' ignores the single rejection and resolves as soon as either of the other two fulfills."),
            ("Why does 'try { return someAsyncFn(); } catch (err) { ... }' inside an 'async' function NOT catch rejections from 'someAsyncFn()' unless you write 'return await someAsyncFn()'?", "Without 'await', the 'async' function simply returns the pending Promise and exits the 'try' block before the Promise rejects. Using 'return await' inside 'try' pauses the function until the Promise settles so rejections enter the local 'catch' block."),
            ("Why does 'items.forEach(async (item) => await process(item))' fail to wait for asynchronous operations to finish?", "'Array.prototype.forEach' invokes the callback synchronously for each element and completely discards the Promise returned by the 'async' callback. Use 'for (const item of items)' for sequential execution or 'await Promise.all(items.map(...))' for parallel execution."),
            ("When does the executor function passed to 'new Promise((resolve, reject) => { ... })' run?", "The executor function runs synchronously and immediately when 'new Promise(...)' is called; only the '.then'/'.catch' reactions scheduled on the Promise run asynchronously as microtasks.")
        ]
    },
    "PRG-T01-C01-U07": {
        "title": "Event Loop and Concurrency",
        "chapter": "C01",
        "order": 7,
        "prereq": "PRG-T01-C01-U06 (Promises and Async/Await)",
        "source": "R003 — MDN – JavaScript Guide (Concurrency model and the event loop). Verified accessible (HTTP 200).",
        "concepts_title": "Runtime Mechanics & Mental Model",
        "concepts": [
            "Single-Threaded Run-to-Completion & Non-Blocking I/O: JavaScript executes on a single Call Stack (one synchronous frame at a time), while the host environment (Browser Web APIs or Node.js libuv) handles timers, network I/O, and file system tasks off-thread and enqueues callbacks when ready.",
            "Microtask Queue vs. Macrotask (Task) Queue Priority: After the synchronous Call Stack becomes completely empty, the Event Loop ALWAYS drains the entire Microtask Queue ('Promise.then/catch/finally' continuations, 'await' continuations, 'queueMicrotask', 'MutationObserver') until it is 100% empty—including new microtasks queued while draining—BEFORE picking the next single Macrotask ('setTimeout', 'setInterval', I/O callbacks, UI events).",
            "Event Loop Starvation & UI Jank: Long-running synchronous CPU loops block the Call Stack, and infinitely recursive 'queueMicrotask' / 'Promise.resolve().then(...)' chains starve the Macrotask Queue and prevent browser rendering or I/O callbacks from ever running."
        ],
        "code_lang": "javascript",
        "code": """// Predict and verify the exact 1 -> 6 execution order:
const order = [];

order.push("1: sync start");

setTimeout(() => {
  order.push("6: macrotask (setTimeout 0)");
  console.log(order.join(" -> "));
}, 0);

Promise.resolve()
  .then(() => {
    order.push("3: microtask 1 (Promise.then)");
    queueMicrotask(() => {
      order.push("5: nested microtask (runs BEFORE macrotask!)");
    });
  })
  .then(() => {
    order.push("4: microtask 2 (chained .then)");
  });

order.push("2: sync end");
// Output:
// 1: sync start -> 2: sync end -> 3: microtask 1 (Promise.then) -> 4: microtask 2 (chained .then) -> 5: nested microtask (runs BEFORE macrotask!) -> 6: macrotask (setTimeout 0)
""",
        "exercise": [
            "Implementation Task: Write a cooperative batch processor 'processInChunks(items, chunkSize, fn)' that processes 'chunkSize' items synchronously and then yields to the Macrotask Queue via 'await new Promise(r => setTimeout(r, 0))' so timers and I/O are never starved.",
            "Debugging Task: Trace a snippet mixing 'async/await', 'new Promise' executor logs, 'queueMicrotask', and 'setTimeout(..., 0)' and explain step-by-step why a 'setTimeout(..., 0)' takes much longer than 0ms when microtasks or heavy sync work are queued."
        ],
        "recall": [
            ("When the Call Stack finishes executing a synchronous script, in what order does the Event Loop process the Microtask Queue and Macrotask Queue?", "It first drains every single item in the Microtask Queue (including any new microtasks enqueued during microtask execution) until the Microtask Queue is empty; only then does it dequeue and execute one Macrotask."),
            ("In an 'async' function, which part executes synchronously on the current Call Stack and which part is scheduled as a microtask?", "Everything inside the 'async' function up to the first 'await' expression (including evaluating the operand of 'await') executes synchronously on the current Call Stack; the code after 'await' is scheduled as a microtask once the awaited Promise settles."),
            ("Why does recursive 'queueMicrotask' starve 'setTimeout(..., 0)' whereas recursive 'setTimeout(..., 0)' does not starve microtasks?", "Because the Event Loop will not move to the next Macrotask until the Microtask Queue is completely empty. If each microtask enqueues another microtask, the Microtask Queue never empties."),
            ("What does the delay parameter '0' in 'setTimeout(fn, 0)' actually guarantee?", "It guarantees a MINIMUM delay (not an exact delay): 'fn' will be placed on the Macrotask Queue and will only execute after the current Call Stack clears, all pending microtasks drain, and any earlier macrotasks finish.")
        ]
    },
    "PRG-T01-C01-U08": {
        "title": "Error Handling Patterns",
        "chapter": "C01",
        "order": 8,
        "prereq": "PRG-T01-C01-U04 (Prototypes), PRG-T01-C01-U06 (Promises and Async/Await)",
        "source": "R003 — MDN – JavaScript Guide (Control flow and error handling). Verified accessible (HTTP 200).",
        "concepts_title": "Runtime Mechanics & Mental Model",
        "concepts": [
            "Operational Errors vs. Programmer Bugs: Operational errors are expected runtime failure modes (network timeout, 404 response, invalid user input) that must be handled gracefully and communicated to callers. Programmer bugs ('TypeError: undefined is not a function') indicate broken code invariants.",
            "Custom Error Subclasses & Error Chaining ('cause'): Subclassing 'Error' ('class HttpError extends Error') lets 'catch' blocks distinguish failure types via 'instanceof' and attach structured metadata ('statusCode', 'endpoint'). Always pass '{ cause: originalError }' when rethrowing a higher-level error so the original stack trace is preserved.",
            "Cleanup Guarantees & Unhandled Rejections: 'finally' runs whether the 'try' block returns, throws, or completes normally—making it essential for releasing locks, timers, or connections. Never swallow errors with an empty 'catch {}'."
        ],
        "code_lang": "javascript",
        "code": """class ServiceError extends Error {
  constructor(message, { code, statusCode = 500, cause } = {}) {
    super(message, { cause });
    this.name = "ServiceError";
    this.code = code;
    this.statusCode = statusCode;
  }
}

async function loadOrderDetails(orderId, apiClient) {
  try {
    const raw = await apiClient.fetchOrder(orderId);
    if (!raw) {
      throw new ServiceError(`Order ${orderId} not found`, {
        code: "ORDER_NOT_FOUND",
        statusCode: 404
      });
    }
    return raw;
  } catch (err) {
    if (err instanceof ServiceError) throw err; // Already structured
    // Wrap low-level network/parse error while preserving original cause chain
    throw new ServiceError(`Failed to load order ${orderId}`, {
      code: "ORDER_FETCH_FAILED",
      statusCode: 502,
      cause: err
    });
  }
}
""",
        "exercise": [
            "Implementation Task: Create a 'DatabaseError' and 'ValidationError' class hierarchy using 'super(message, { cause })', and write an error boundary handler that maps each error class to a safe user-facing response while logging the full '.cause' chain.",
            "Debugging Task: Fix a module that throws raw strings ('throw \"failed\"') and swallows errors in 'catch (e) { console.log(e); }' causing callers to proceed with 'undefined' data."
        ],
        "recall": [
            ("Why should you always throw 'Error' instances (or subclasses) rather than throwing raw strings or plain objects?", "'Error' instances automatically capture the runtime Call Stack trace ('.stack'), have standard '.name' and '.message' properties, and work with 'instanceof Error' checks across libraries."),
            ("What problem does 'new Error(\"High-level message\", { cause: err })' solve when catching and rethrowing errors across layers?", "It adds contextual information from the higher layer without destroying the original low-level error object and its stack trace, which remain inspectable via 'error.cause'."),
            ("If a 'try' block executes 'return \"success\"' and the 'finally' block executes 'return \"override\"' (or throws), what happens?", "A 'return' or 'throw' inside 'finally' overrides any 'return' or 'throw' from the 'try' or 'catch' block—which is why 'finally' should only perform cleanup side effects and never 'return'."),
            ("When catching an error in 'catch (err)', why should a function rethrow 'err' if it does not know how to recover from that specific error type?", "Swallowing an unexpected error hides broken invariants and causes the program to continue executing in a corrupted state with 'undefined' return values.")
        ]
    },
    "PRG-T01-C02-U01": {
        "title": "Type Annotations and Type Inference",
        "chapter": "C02",
        "order": 1,
        "prereq": "PRG-T01-C01 (JavaScript Deep Dive)",
        "source": "R004 — TypeScript Handbook (The Basics; Everyday Types). Verified accessible (HTTP 200).",
        "concepts_title": "Type System Semantics & Compiler Rules",
        "concepts": [
            "Type Erasure & Compile-Time Verification: TypeScript annotations exist purely at compile time. Once type checking succeeds, the compiler erases all type syntax to produce standard JavaScript—meaning types have zero runtime overhead and do not automatically validate runtime JSON inputs.",
            "Type Inference & Literal Widening: When you initialize 'let status = \"idle\"', TypeScript widens the inferred type to 'string' because 'let' can be reassigned. When you initialize 'const status = \"idle\"', TypeScript infers the narrow literal type '\"idle\"' because 'const' cannot be rebound. For objects/arrays, 'as const' freezes all nested properties to 'readonly' literal types.",
            "When to Annotate Explicitly vs. Rely on Inference: Always annotate function parameters (which cannot be inferred without context), public function return types (to enforce intentional API contracts and prevent accidental return-type drift), and empty collections ('const items: User[] = []'). Let TypeScript infer local variables initialized from typed expressions."
        ],
        "code_lang": "typescript",
        "code": """// 1. Widening vs. Literal Inference vs. 'as const'
let mutableRole = "admin";       // Inferred as: string (widened)
const fixedRole = "admin";       // Inferred as: "admin" (literal type)

const ROLES = ["admin", "editor", "viewer"] as const;
// Inferred as: readonly ["admin", "editor", "viewer"]
type Role = (typeof ROLES)[number]; // "admin" | "editor" | "viewer"

// 2. Explicit Function Boundary Contracts + Local Inference
interface TaxBreakdown {
  subtotal: number;
  tax: number;
  total: number;
}

export function calculateTax(amount: number, rate = 0.07): TaxBreakdown {
  const tax = Number((amount * rate).toFixed(2)); // Inferred as number
  return {
    subtotal: amount,
    tax,
    total: amount + tax
  };
}
""",
        "exercise": [
            "Implementation Task: Define an immutable configuration object using 'as const' and extract a union type of its route keys and status codes without repeating string literals.",
            "Debugging Task: Fix a snippet where passing 'const req = { url: \"/api\", method: \"GET\" }' into 'fetchData(req.url, req.method)' fails with 'Argument of type string is not assignable to parameter of type \"GET\" | \"POST\"'."
        ],
        "recall": [
            ("Why does 'const cfg = { method: \"GET\" }' infer 'cfg.method' as 'string' instead of '\"GET\"', whereas 'const method = \"GET\"' infers '\"GET\"'?", "Because object properties remain mutable even when the object variable is declared with 'const' ('cfg.method = \"POST\"' is legal JS), so TypeScript widens property types unless you use 'as const' or an explicit type annotation."),
            ("Why is it good engineering practice to annotate the return type of exported functions even when TypeScript could infer it?", "Explicit return types act as a compile-time contract at the function boundary: they catch accidental return-type changes inside the implementation, produce clearer error locations, and speed up type checking across modules."),
            ("What happens to TypeScript type annotations and interfaces when your code is compiled and executed in Node.js or the browser?", "They are completely erased during compilation. They do not exist at runtime and cannot be inspected with JavaScript's runtime operators."),
            ("Why is 'any' dangerous compared to letting TypeScript infer types or using 'unknown'?", "'any' disables the type checker for that value and contagiously spreads through property accesses and function calls, allowing runtime 'TypeError' crashes to slip past compilation.")
        ]
    },
    "PRG-T01-C02-U02": {
        "title": "Primitive, Literal and Object Types",
        "chapter": "C02",
        "order": 2,
        "prereq": "PRG-T01-C02-U01 (Type Annotations and Type Inference)",
        "source": "R004 — TypeScript Handbook (Everyday Types; Object Types). Verified accessible (HTTP 200).",
        "concepts_title": "Type System Semantics & Compiler Rules",
        "concepts": [
            "Structural Subtyping (Duck Typing): TypeScript checks type compatibility based on the SHAPE (properties and their types) of an object, not the name of its interface or class (unlike nominal languages like Java). If type 'DetailedUser' has all required properties of 'BasicUser', a 'DetailedUser' variable is assignable to 'BasicUser'.",
            "Excess Property Checks on Fresh Object Literals: Although extra properties are allowed when assigning a variable of a wider type, TypeScript runs special Excess Property Checks when you pass a fresh object literal directly ('createUser({ name: \"Ada\", nam: \"typo\" })') to catch misspelled optional properties.",
            "Modifiers ('?', 'readonly') & 'interface' vs. 'type': Optional properties ('email?: string') allow 'string | undefined'. 'readonly id: string' prevents property mutation at compile time. Use 'interface' or 'type' consistently for object shapes; note that only 'type' can alias primitives, unions, and tuples."
        ],
        "code_lang": "typescript",
        "code": """export interface UserProfile {
  readonly id: string;
  username: string;
  bio?: string; // string | undefined
}

export type Environment = "development" | "staging" | "production";
export type CoordinateTuple = readonly [latitude: number, longitude: number];

function formatProfile(user: UserProfile): string {
  // user.id = "new_id"; // Compile Error: Cannot assign to 'id' because it is a read-only property
  const suffix = user.bio ? ` (${user.bio})` : "";
  return `@${user.username}${suffix}`;
}

// Structural typing: extra properties on an existing variable are permitted
const adminRecord = { id: "u_1", username: "ada", role: "admin" };
console.log(formatProfile(adminRecord)); // Valid! Shape satisfies UserProfile
""",
        "exercise": [
            "Implementation Task: Model an 'OrderItem' and 'Order' object hierarchy using 'readonly' identifiers, optional discount fields, literal currency types ('\"THB\" | \"USD\"'), and a fixed-length tuple for '[minQty, maxQty]'.",
            "Debugging Task: Explain why 'const opts = { timeout: 1000, timout: 500 }; run(opts);' passes structural typing when 'timeout' is optional, and show how typing 'const opts: RunOptions = ...' catches the typo immediately."
        ],
        "recall": [
            ("What is structural typing in TypeScript, and how does it differ from nominal typing?", "Structural typing determines compatibility solely by whether an object has the required properties and matching value types, regardless of what interface or class name was used to declare it."),
            ("Why does TypeScript reject 'render({ width: 100, heigth: 200 })' when passed as an inline object literal, yet allow 'const box = { width: 100, heigth: 200 }; render(box);'?", "Fresh object literals undergo Excess Property Checking because an unreferenced extra property on a literal is almost always a typo, whereas passing an existing variable uses standard structural subtype compatibility."),
            ("Does the 'readonly' modifier on a TypeScript property call 'Object.freeze()' at runtime?", "No. 'readonly' is enforced strictly at compile time by the TypeScript checker and is erased in the emitted JavaScript."),
            ("What are two capabilities of 'type' aliases that 'interface' declarations cannot express?", "'type' can define union types ('type Status = \"ok\" | \"err\"'), primitive aliases, and tuple types directly, whereas 'interface' can only describe object/function shapes.")
        ]
    },
    "PRG-T01-C02-U03": {
        "title": "Union Types",
        "chapter": "C02",
        "order": 3,
        "prereq": "PRG-T01-C02-U02 (Primitive, Literal and Object Types)",
        "source": "R004 — TypeScript Handbook (Everyday Types — Union Types). Verified accessible (HTTP 200).",
        "concepts_title": "Type System Semantics & Compiler Rules",
        "concepts": [
            "Set Union vs. Accessible Members: A union type 'A | B' represents values that belong to set 'A', set 'B', or both. Because a value of type 'A | B' is only guaranteed at runtime to have the properties common to BOTH 'A' and 'B', TypeScript only allows direct un-narrowed access to the intersection of their members.",
            "Replacing Loose Booleans & Nullable Strings: Instead of modeling mutually exclusive domain states with multiple loose booleans or arbitrary strings, unions of string/number literals ('type PaymentMethod = \"card\" | \"promptpay\" | \"bank_transfer\"') restrict values to valid domain possibilities.",
            "Union Distribution Over Arrays: Pay close attention to parentheses: '(string | number)[]' is an array containing a mix of strings and numbers, whereas 'string[] | number[]' is either an array of ONLY strings or an array of ONLY numbers."
        ],
        "code_lang": "typescript",
        "code": """type Identifier = string | number;

function normalizeId(id: Identifier): string {
  // Only methods shared by BOTH string and number (like .toString()) are accessible before narrowing:
  // return id.toUpperCase(); // Compile Error: Property 'toUpperCase' does not exist on type 'number'
  return typeof id === "string" ? id.trim().toUpperCase() : `ID_${id}`;
}

// Array Union Distinction:
const mixedList: (string | number)[] = ["A1", 102, "B3"];
const homogeneousList: string[] | number[] = ["A1", "B3"]; // Cannot mix strings and numbers
""",
        "exercise": [
            "Implementation Task: Write a 'formatDuration(input: number | string | { minutes: number; seconds: number }): string' function that accepts three union representations of duration and normalizes them into '\"MM:SS\"'.",
            "Debugging Task: Fix a function taking 'items: string[] | number[]' where calling 'items.push(...)' or '.map(...)' fails due to homogeneous array union ambiguity."
        ],
        "recall": [
            ("Why can you only access properties shared by ALL members of a union type 'A | B' before narrowing?", "Because at runtime the value could be either an 'A' or a 'B'. Only properties that exist on both 'A' and 'B' are guaranteed to be safe to access without first checking which member is present."),
            ("What is the difference between 'string | null | undefined' under 'strictNullChecks: true' vs. 'strictNullChecks: false'?", "With 'strictNullChecks: true', 'null' and 'undefined' are distinct types and must be explicitly included in a union ('string | null') and narrowed before calling string methods."),
            ("Explain the difference between 'type A = (string | number)[]' and 'type B = string[] | number[]'.", "'A' is a single array whose elements can individually be strings or numbers ('[1, \"a\"]'). 'B' is a union of two homogeneous array types: either every element is a string, or every element is a number."),
            ("What does the union 'T | never' simplify to in TypeScript's type system, and why?", "It simplifies to 'T', because 'never' represents the empty set of values, and the union of any set 'T' with the empty set is 'T'.")
        ]
    },
    "PRG-T01-C02-U04": {
        "title": "Type Narrowing and Guards",
        "chapter": "C02",
        "order": 4,
        "prereq": "PRG-T01-C02-U03 (Union Types)",
        "source": "R004 — TypeScript Handbook (Narrowing). Verified accessible (HTTP 200).",
        "concepts_title": "Type System Semantics & Compiler Rules",
        "concepts": [
            "Control-Flow Analysis (CFA): TypeScript tracks 'if'/'else', 'switch', early 'return', and 'throw' branches to refine a broad union type (like 'string | number | null') into a more specific subtype within a code block.",
            "Built-in Runtime Type Guards: (1) 'typeof x === \"string\"' for primitives (remember 'typeof null === \"object\"'!); (2) Truthiness narrowing ('if (x)')—watch out for falsy valid values like '0' or '\"\"'; (3) Equality checks ('x !== null && x !== undefined'); (4) '\"prop\" in obj' for object shapes; (5) 'err instanceof Error' for class instances; (6) 'Array.isArray(x)' for arrays.",
            "User-Defined Type Predicates ('x is T'): When narrowing logic is extracted into a helper function (especially for validating 'unknown' API inputs or filtering arrays with '.filter(isNonNull)'), return a type predicate 'function isUser(val: unknown): val is User' so the compiler narrows the caller's variable."
        ],
        "code_lang": "typescript",
        "code": """export interface ApiUser {
  id: string;
  email: string;
}

// Custom Type Guard narrowing 'unknown' -> 'ApiUser'
export function isApiUser(value: unknown): value is ApiUser {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  return typeof record.id === "string" && typeof record.email === "string";
}

// Generic non-nullish predicate for .filter()
export function isDefined<T>(value: T | null | undefined): value is T {
  return value !== null && value !== undefined;
}

const rawItems: (string | null | undefined)[] = ["alpha", null, "beta", undefined];
const cleanItems: string[] = rawItems.filter(isDefined); // Narrowed to string[]!
""",
        "exercise": [
            "Implementation Task: Write a user-defined type guard 'isValidConfig(input: unknown): input is AppConfig' that checks nested properties safely without throwing runtime errors on 'null' or primitives.",
            "Debugging Task: Fix a bug where 'if (amount)' was used to narrow 'amount: number | undefined', accidentally treating 'amount = 0' as missing data."
        ],
        "recall": [
            ("Why does 'if (typeof val === \"object\")' NOT narrow 'val: Record<string, unknown> | null' to a non-null object?", "Because in JavaScript, 'typeof null' evaluates to '\"object\"' for historical reasons. You must explicitly check 'typeof val === \"object\" && val !== null'."),
            ("When is a user-defined type predicate ('val is T') necessary instead of returning a plain 'boolean'?", "When narrowing checks are moved into a helper function (or passed as a callback to 'Array.prototype.filter'), TypeScript does not propagate narrowing across function boundaries unless the return type is annotated as 'val is T'."),
            ("What is the danger of using truthiness narrowing ('if (value)') on a variable of type 'string | number | undefined'?", "Valid values like the number '0', 'NaN', or the empty string '\"\"' are falsy in JavaScript, so 'if (value)' will take the falsy branch and misclassify valid data as 'undefined'."),
            ("What responsibility do you take on when writing a 'val is T' type predicate?", "The compiler trusts your boolean implementation completely; if your runtime check is incomplete (e.g., forgetting to check a required field), TypeScript will narrow the type to 'T' anyway, creating unsoundness.")
        ]
    },
    "PRG-T01-C02-U05": {
        "title": "Generics",
        "chapter": "C02",
        "order": 5,
        "prereq": "PRG-T01-C02-U04 (Type Narrowing and Guards)",
        "source": "R004 — TypeScript Handbook (Generics). Verified accessible (HTTP 200).",
        "concepts_title": "Type System Semantics & Compiler Rules",
        "concepts": [
            "Type Parameters Preserve Relationships: Generics act as type-level variables ('<T>') that capture the exact type provided by the caller and thread it through parameters and return types—preserving full type safety without duplicating functions or losing information to 'any'/'unknown'.",
            "Generic Constraints ('extends') & 'keyof': An unconstrained '<T>' could be anything, so you cannot access 'item.id' unless you constrain it: '<T extends { id: string }>'. Combining generics with 'keyof' ('<T, K extends keyof T>(obj: T, key: K): T[K]') guarantees at compile time that 'key' exists on 'obj' and returns the exact property type 'T[K]'.",
            "Golden Rule of Generics: A type parameter '<T>' should appear at least twice in a signature (to relate two arguments, or an argument and the return type). If '<T>' only appears once and is unconstrained, a simpler concrete or union type is usually clearer."
        ],
        "code_lang": "typescript",
        "code": """// 1. Relating Object Type 'T' and Key Type 'K' with Indexed Access 'T[K]'
export function pluckProperty<T extends object, K extends keyof T>(
  items: readonly T[],
  key: K
): T[K][] {
  return items.map(item => item[key]);
}

const invoices = [
  { id: "inv_1", total: 1200, paid: true },
  { id: "inv_2", total: 850, paid: false }
];

const totals = pluckProperty(invoices, "total"); // Inferred as: number[]
// pluckProperty(invoices, "missing"); // Compile Error: '"missing"' is not assignable to '"id" | "total" | "paid"'
""",
        "exercise": [
            "Implementation Task: Write a generic function 'indexById<T extends { id: string | number }>(items: readonly T[]): Record<T[\"id\"], T>' that converts an array of entities into a keyed lookup dictionary.",
            "Debugging Task: Refactor a helper 'function wrapInArray(val: unknown): unknown[]' into a generic function so callers retain literal and object types without manual type assertions."
        ],
        "recall": [
            ("How does a generic function 'function first<T>(arr: readonly T[]): T | undefined' differ from 'function first(arr: readonly unknown[]): unknown'?", "With '<T>', calling 'first([\"a\", \"b\"])' infers 'T = string' and returns 'string | undefined'. With 'unknown[]', the caller always receives 'unknown' and loses the element type."),
            ("Why does 'function getLength<T>(arg: T) { return arg.length; }' fail to compile, and how do you fix it?", "Because an unconstrained 'T' could be a 'number' or 'boolean' which has no '.length' property. Fix it by adding a constraint: 'function getLength<T extends { length: number }>(arg: T): number'."),
            ("What does the constraint '<T, K extends keyof T>' guarantee when accessing 'obj[key]'?", "It guarantees at compile time that 'key' is a valid property name of 'T', and TypeScript infers the expression 'obj[key]' as the exact indexed access type 'T[K]'."),
            ("When is a generic type parameter unnecessary (an anti-pattern)?", "When the type parameter '<T>' appears only once in the function signature (for example, 'function log<T extends { name: string }>(item: T): void') and is never used to relate multiple parameters or the return type.")
        ]
    },
    "PRG-T01-C02-U06": {
        "title": "Utility Types",
        "chapter": "C02",
        "order": 6,
        "prereq": "PRG-T01-C02-U05 (Generics)",
        "source": "R004 — TypeScript Handbook (Utility Types). Verified accessible (HTTP 200).",
        "concepts_title": "Type System Semantics & Compiler Rules",
        "concepts": [
            "Deriving Types from a Single Source of Truth: Instead of manually maintaining separate interfaces for 'User', 'CreateUserInput', 'UpdateUserInput', and 'PublicUserSummary' (which drift out of sync when fields change), use TypeScript's built-in generic utility types to derive them automatically.",
            "Object Mapping Utilities: 'Partial<T>' makes all properties optional; 'Required<T>' makes all properties required; 'Readonly<T>' makes all properties read-only; 'Pick<T, K>' selects a subset of keys; 'Omit<T, K>' removes specified keys; 'Record<K, V>' constructs an object map with key type 'K' and value type 'V'.",
            "Union & Function Utilities: 'Exclude<Union, ExcludedMembers>' and 'Extract<Union, Match>' filter union types, 'NonNullable<T>' strips 'null | undefined', and 'ReturnType<typeof fn>' / 'Parameters<typeof fn>' extract types directly from function values."
        ],
        "code_lang": "typescript",
        "code": """export interface Article {
  readonly id: string;
  title: string;
  content: string;
  publishedAt: string | null;
  authorId: string;
}

// 1. Derive Create & Patch DTOs from Article (Single Source of Truth)
export type CreateArticleInput = Omit<Article, "id" | "publishedAt">;
export type UpdateArticlePatch = Partial<Pick<Article, "title" | "content" | "publishedAt">>;
export type ArticleCardSummary = Pick<Article, "id" | "title" | "publishedAt">;

// 2. Exhaustive Lookup Dictionary with Record<K, V>
export type OrderStatus = "pending" | "paid" | "shipped" | "cancelled";
export const STATUS_LABELS: Record<OrderStatus, string> = {
  pending: "Awaiting Payment",
  paid: "Payment Confirmed",
  shipped: "In Transit",
  cancelled: "Order Cancelled"
};
""",
        "exercise": [
            "Implementation Task: Given a domain entity 'Product', derive 'CreateProductDto', 'UpdateProductDto' (where 'id' and 'createdAt' cannot be modified), and a 'Record<ProductCategory, Product[]>' catalog index.",
            "Debugging Task: Explain why 'Partial<User>' only makes top-level properties optional (shallow) and show how to type a safe patch payload when nested objects are updated."
        ],
        "recall": [
            ("Why is deriving 'UpdateUserDto = Partial<Omit<User, \"id\" | \"createdAt\">>' superior to writing a separate 'interface UpdateUserDto' by hand?", "When a property is added or its type changes on 'User', derived types automatically stay synchronized, whereas a manually duplicated interface can silently fall out of date."),
            ("What is the difference between 'Omit<T, K>' (for object properties) and 'Exclude<U, E>' (for union members)?", "'Omit<T, K>' operates on an object type 'T' and produces a new object type without keys 'K'. 'Exclude<U, E>' operates on a union type 'U' and removes union members assignable to 'E'."),
            ("How does 'Record<OrderStatus, HandlerFn>' help catch bugs when a new member is added to the 'OrderStatus' union?", "TypeScript requires a 'Record<UnionKey, V>' object literal to include a key for EVERY member of the union; adding a new status to 'OrderStatus' immediately flags a compile error on every incomplete lookup table."),
            ("When is 'ReturnType<typeof createStore>' especially useful?", "When interacting with factory functions or third-party functions that infer a complex return type without exporting a named interface for it.")
        ]
    },
    "PRG-T01-C02-U07": {
        "title": "Discriminated Unions",
        "chapter": "C02",
        "order": 7,
        "prereq": "PRG-T01-C02-U03 (Union Types), PRG-T01-C02-U04 (Type Narrowing)",
        "source": "R004 — TypeScript Handbook (Narrowing — Discriminated unions & Exhaustiveness checking). Verified accessible (HTTP 200).",
        "concepts_title": "Type System Semantics & Compiler Rules",
        "concepts": [
            "Making Impossible States Unrepresentable: A baggy object like '{ loading: boolean; data?: User; error?: Error }' allows 8 combinations, including impossible states like '{ loading: true, data: user, error: err }' or '{ loading: false }' with neither data nor error. A Discriminated (Tagged) Union replaces loose optional fields with explicit state variants that share a single literal discriminant property (e.g., 'status' or 'kind').",
            "Automatic Variant Narrowing: When every member of a union has a common property with distinct literal types ('status: \"idle\" | \"loading\" | \"success\" | \"error\"'), checking 'if (state.status === \"success\")' or switching on 'state.status' narrows the entire object to that exact variant, granting safe access to variant-specific fields ('state.data').",
            "Compile-Time Exhaustiveness Checking with 'never': Adding a 'default' branch that passes the remaining value to 'assertNever(x: never): never' guarantees that if a new variant is added to the union later, every unhandled 'switch' statement fails at compile time."
        ],
        "code_lang": "typescript",
        "code": """export type AsyncResult<T, E = string> =
  | { readonly status: "idle" }
  | { readonly status: "loading"; readonly startedAt: number }
  | { readonly status: "success"; readonly data: T }
  | { readonly status: "error"; readonly error: E; readonly retryable: boolean };

export function assertNever(value: never): never {
  throw new Error(`Unhandled discriminated union member: ${JSON.stringify(value)}`);
}

export function renderStatusBanner(state: AsyncResult<string[]>): string {
  switch (state.status) {
    case "idle":
      return "Ready to load items.";
    case "loading":
      return `Loading since ${state.startedAt}...`;
    case "success":
      return `Loaded ${state.data.length} items.`; // 'state.data' is guaranteed to exist!
    case "error":
      return `Error: ${state.error} (Retryable: ${state.retryable})`;
    default:
      return assertNever(state); // Compile error if any case above is omitted!
  }
}
""",
        "exercise": [
            "Implementation Task: Model a payment processing event stream ('PaymentInitiated | PaymentCaptured | PaymentRefunded | PaymentFailed') as a discriminated union and write a reducer function with 'assertNever' exhaustiveness checking.",
            "Debugging Task: Refactor a legacy '{ isSuccess: boolean; payload?: Order; errorMessage?: string }' response type into a discriminated union and eliminate all non-null assertions ('!')."
        ],
        "recall": [
            ("What two ingredients are required for TypeScript to treat a union of object types as a discriminated union?", "1. Every member of the union must share a common property name (the discriminant, such as 'status' or 'type'), and 2. That property must have a distinct literal (or unit) type in each variant."),
            ("Why is a discriminated union safer than an interface with optional 'data?: T' and 'error?: Error' properties?", "With optional properties, checking 'if (!res.error)' does NOT narrow 'res.data' to 'T' (it stays 'T | undefined'), tempting developers to use unsafe 'res.data!' assertions. A discriminated union ties the presence of 'data' directly to 'status === \"success\"'."),
            ("How does 'assertNever(state)' in the 'default' branch of a 'switch' statement catch future bugs at compile time?", "Once all known union variants are handled in 'case' branches, TypeScript narrows 'state' in 'default' to the empty set 'never'. If someone later adds a new variant to the union without updating the 'switch', 'state' in 'default' has that new variant's type, which is not assignable to 'never'."),
            ("What happens if one variant in a discriminated union types the discriminant property as 'type: string' instead of a literal like 'type: \"created\"'?", "It breaks exhaustiveness and narrowing because 'string' overlaps with all other string literal tags, preventing TypeScript from ruling out that variant in 'else'/'default' branches.")
        ]
    },
    "PRG-T01-C02-U08": {
        "title": "Strict Mode and tsconfig",
        "chapter": "C02",
        "order": 8,
        "prereq": "PRG-T01-C02-U01 through PRG-T01-C02-U07",
        "source": "R004 — TypeScript Handbook (tsconfig Reference / Strict Mode). Verified accessible (HTTP 200).",
        "concepts_title": "Type System Semantics & Compiler Rules",
        "concepts": [
            "The 'strict: true' Family: Enabling '\"strict\": true' in 'tsconfig.json' activates the core soundness flags: 'noImplicitAny' (forbids untyped parameters defaulting to 'any'), 'strictNullChecks' (separates 'null'/'undefined' from other types), 'strictFunctionTypes' (enforces contravariant parameter checking), 'strictBindCallApply', 'strictPropertyInitialization', and 'useUnknownInCatchVariables' (types 'catch (err)' as 'unknown' instead of 'any').",
            "Additional High-Value Safety Flags Not Included in 'strict': Even with 'strict: true', array/record indexing 'arr[99]' returns 'T' instead of 'T | undefined'. Enabling '\"noUncheckedIndexedAccess\": true' forces 'arr[i]' and 'record[key]' to include '| undefined', catching out-of-bounds bugs at compile time. '\"exactOptionalPropertyTypes\": true' distinguishes missing keys from keys explicitly set to 'undefined'.",
            "Target, Module & Type-Checking vs. Bundling: 'target' controls which JS syntax features are downleveled; 'module' and 'moduleResolution' ('\"NodeNext\"' for Node.js ESM or '\"Bundler\"' for Vite/Next.js) control how imports resolve; '\"noEmit\": true' runs 'tsc' purely as a type-checker in CI pipelines."
        ],
        "code_lang": "typescript",
        "code": """// Recommended strict application tsconfig.json structure:
/*
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,
    "noEmit": true,
    "isolatedModules": true,
    "skipLibCheck": true
  }
}
*/

// Impact of "noUncheckedIndexedAccess": true and "useUnknownInCatchVariables": true
export function getFirstKeyword(keywords: readonly string[]): string {
  const first = keywords[0]; // Typed as 'string | undefined' under noUncheckedIndexedAccess!
  if (first === undefined) {
    return "default";
  }
  return first.toLowerCase();
}

export function parseJsonSafe(raw: string): unknown {
  try {
    return JSON.parse(raw);
  } catch (err: unknown) {
    // Under useUnknownInCatchVariables, 'err' is 'unknown' and must be narrowed:
    const msg = err instanceof Error ? err.message : String(err);
    throw new Error(`Invalid JSON: ${msg}`);
  }
}
""",
        "exercise": [
            "Implementation Task: Audit a sample 'tsconfig.json' and write code snippets demonstrating the exact compile-time errors caught by 'strictNullChecks', 'noUncheckedIndexedAccess', and 'useUnknownInCatchVariables'.",
            "Debugging Task: Take a loosely typed function that compiles under 'strict: false' (with implicit 'any' parameters, unchecked 'dict[key].trim()', and 'catch (e) { return e.message }') and make it compile cleanly under strict settings."
        ],
        "recall": [
            ("Which specific checks are turned on by setting '\"strict\": true' in 'tsconfig.json'?", "'noImplicitAny', 'strictNullChecks', 'strictFunctionTypes', 'strictBindCallApply', 'strictPropertyInitialization', 'noImplicitThis', 'alwaysStrict', and 'useUnknownInCatchVariables'."),
            ("Why is '\"noUncheckedIndexedAccess\": true' important even when '\"strict\": true' is already enabled?", "'strict: true' still types 'const item = arr[0]' or 'dict[key]' as 'T' rather than 'T | undefined', hiding runtime 'TypeError' crashes when an array is empty or a record key is missing."),
            ("Why does 'useUnknownInCatchVariables' type 'catch (err)' as 'unknown' instead of 'Error'?", "Because in JavaScript, any value can be thrown ('throw \"string\"', 'throw null', 'throw { code: 400 }'), so assuming 'err' is always an 'Error' instance is unsound without an 'instanceof Error' check."),
            ("When should 'moduleResolution' be set to '\"NodeNext\"' versus '\"Bundler\"'?", "Use '\"NodeNext\"' when building code executed directly by Node.js (which enforces ESM file extensions and package.json 'exports' rules); use '\"Bundler\"' when a bundler like Vite, Webpack, or Next.js resolves imports.")
        ]
    },
    "PRG-T01-C02-U09": {
        "title": "Typing Functions and API Responses",
        "chapter": "C02",
        "order": 9,
        "prereq": "PRG-T01-C02-U04 (Type Guards), PRG-T01-C02-U05 (Generics), PRG-T01-C02-U07 (Discriminated Unions)",
        "source": "R004 — TypeScript Handbook (More on Functions). Verified accessible (HTTP 200).",
        "concepts_title": "Type System Semantics & Compiler Rules",
        "concepts": [
            "Untrusted Network Boundaries ('response.json()'): By default, 'fetch().then(r => r.json())' returns 'Promise<any>'. Casting it directly via 'as User' is a lie to the compiler: if the backend changes a field or returns an error payload, your code crashes at runtime. Always treat parsed JSON at external boundaries as 'unknown' and validate it with a type guard or schema validator before returning 'T'.",
            "Function Type Expressions, Callbacks & 'void': In callback types like '(item: T, index: number) => void', a caller is allowed to pass a callback that accepts FEWER arguments ('item => ...'), and a return type of 'void' in a callback type means the caller ignores the return value.",
            "Function Overloads vs. Union Signatures: When the return type depends on the input type in a way a single union cannot express, use function overload signatures above a general implementation signature—or prefer a generic/discriminated union return type when simpler."
        ],
        "code_lang": "typescript",
        "code": """export type ApiResponse<T> =
  | { readonly ok: true; readonly status: number; readonly data: T }
  | { readonly ok: false; readonly status: number; readonly error: string };

export type TypeGuard<T> = (input: unknown) => input is T;

export async function fetchTypedJson<T>(
  url: string,
  guard: TypeGuard<T>,
  init?: RequestInit
): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(url, init);
    const raw: unknown = await response.json();

    if (!response.ok) {
      return {
        ok: false,
        status: response.status,
        error: `HTTP ${response.status}`
      };
    }

    if (!guard(raw)) {
      return {
        ok: false,
        status: response.status,
        error: "Response payload failed runtime schema validation"
      };
    }

    return { ok: true, status: response.status, data: raw };
  } catch (err: unknown) {
    return {
      ok: false,
      status: 0,
      error: err instanceof Error ? err.message : "Network failure"
    };
  }
}
""",
        "exercise": [
            "Implementation Task: Use 'fetchTypedJson<T>' above to implement a 'getUserOrders(userId: string)' client function with a runtime type guard for 'Order[]' and exhaustive caller handling.",
            "Debugging Task: Replace an unsafe 'const data = (await res.json()) as UserProfile' implementation that crashes on HTTP 500 JSON error bodies with a validated 'ApiResponse<UserProfile>' contract."
        ],
        "recall": [
            ("Why is 'const user = (await response.json()) as User' dangerous in production TypeScript applications?", "Type assertions ('as User') are erased at compile time and perform zero runtime validation. If the server returns an error object or changes a field type, 'user' has the wrong runtime shape and crashes downstream."),
            ("How does combining 'unknown' with a 'TypeGuard<T>' ('(val: unknown) => val is T') make 'fetch' wrappers genuinely type-safe?", "Treating parsed JSON as 'unknown' prevents unvalidated property access, and passing it through 'guard(raw)' verifies the actual runtime structure before narrowing 'raw' to 'T'."),
            ("Why does TypeScript allow '[1, 2, 3].map(x => x * 2)' even though 'Array.prototype.map' expects a callback with three parameters '(value, index, array)'?", "In JavaScript, ignoring trailing arguments is always safe, so TypeScript permits a function with fewer parameters to be assigned to a callback type that provides more arguments."),
            ("When should you prefer a simple union parameter over multiple function overload signatures?", "Whenever the return type does not change based on which union member was passed in (e.g., 'function getLen(x: string | unknown[]): number' is cleaner than two separate overloads that both return 'number').")
        ]
    }
}
