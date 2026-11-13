# -*- coding: utf-8 -*-
"""
Parameterized Problem Templates for PRG-T01-C01: JavaScript Deep Dive.
Chapter: PRG-T01-C01 (Scope, Closures, this, Prototypes, Modules, Promises, Event Loop, Errors).

All templates are executed and verified against a live Node.js subprocess before being accepted.
"""

import random

from code_engine.verify import run_node

TITLE = "JavaScript Deep Dive"
CHAPTER_CODE = "PRG-T01-C01"
TOPIC_CODE = "PRG-T01"

MISTAKE_TAGS = [
    {
        "id": "microtask-order",
        "name": "Microtask vs Macrotask Queue Order",
        "label": "Microtask Queue Priority",
        "autoFrom": ["microtask-order"],
    },
    {
        "id": "var-vs-let-scope",
        "name": "var vs let Lexical Scope in Loops",
        "label": "Loop Variable Scope",
        "autoFrom": ["var-vs-let-scope"],
    },
    {
        "id": "stale-closure",
        "name": "Stale Closure Reference",
        "label": "Stale Closure",
        "autoFrom": ["stale-closure"],
    },
    {
        "id": "this-binding-lost",
        "name": "Lost this Binding in Detached Method / Callback",
        "label": "Lost this Binding",
        "autoFrom": ["this-binding-lost"],
    },
    {
        "id": "prototype-mutation",
        "name": "Prototype Object Mutation vs Own Property Shadowing",
        "label": "Prototype Mutation",
        "autoFrom": ["prototype-mutation"],
    },
    {
        "id": "unhandled-rejection",
        "name": "Promise Rejection and Catch Return Flow",
        "label": "Promise Catch Flow",
        "autoFrom": ["unhandled-rejection"],
    },
    {
        "id": "hoisting-order",
        "name": "Declaration Hoisting and Temporal Dead Zone",
        "label": "Hoisting & TDZ",
        "autoFrom": ["hoisting-order"],
    },
]


# ============================================================================
# TEMPLATE 1: Scope & Hoisting Output Prediction (Level 1 Foundation)
# ============================================================================
def build_scope_hoisting_loop(rng: random.Random) -> dict:
    use_var = rng.choice([True, False])
    n = rng.choice([3, 4, 5])
    idx_a = 0
    idx_b = n - 1

    var_keyword = "var" if use_var else "let"
    code = (
        f"const funcs = [];\n"
        f"for ({var_keyword} i = 0; i < {n}; i++) {{\n"
        f"  funcs.push(() => i);\n"
        f"}}\n"
        f"console.log(funcs[{idx_a}]());\n"
        f"console.log(funcs[{idx_b}]());"
    )

    stdout, stderr, exit_code = run_node(code)
    if exit_code != 0:
        raise RuntimeError(f"Template execution failed: {stderr}")

    lines = stdout.splitlines()
    answer_plain = ", ".join(lines)

    step1_explain = f"The loop declares the iterator variable using '{var_keyword}'. " + (
        f"Because 'var' is function-scoped (or global), only a single binding of 'i' exists. "
        f"When the loop finishes, 'i' holds the terminal value {n}."
        if use_var
        else f"Because 'let' is block-scoped, a new lexical environment binding for 'i' is created for every loop iteration, "
        f"capturing the specific value (0 through {n - 1}) in each closure."
    )

    step2_explain = f"Executing funcs[{idx_a}]() yields {lines[0]}, and funcs[{idx_b}]() yields {lines[1]}."

    return {
        "category": "Scope and Closures",
        "context": f"Variable Scope ({var_keyword})",
        "prompt": (
            "Predict the exact terminal output when the following JavaScript snippet executes. "
            "Note the variable declaration used in the loop header."
        ),
        "codeSnippet": code,
        "language": "javascript",
        "codeType": "predict-output",
        "answerSpec": {
            "type": "code_output",
            "tokens": lines,
            "value": answer_plain,
            "commonTrapTag": "var-vs-let-scope",
        },
        "answerPlain": answer_plain,
        "answerDisplay": answer_plain,
        "inputHint": "e.g. 10, 20 (enter numbers separated by comma or space)",
        "checkpointHint": (
            f"Check whether '{var_keyword}' creates a new binding per iteration or reuses a shared single binding."
        ),
        "commonTrapTag": "var-vs-let-scope",
        "steps": [
            {"latex": f"\\text{{Binding Strategy: }} {var_keyword}", "explain": step1_explain},
            {"latex": f"\\text{{Output: }} [{lines[0]}, {lines[1]}]", "explain": step2_explain},
        ],
        "references": ["PRG-T01-C01-U01", "PRG-T01-C01-U02"],
        "verify": {"source": answer_plain},
    }


# ============================================================================
# TEMPLATE 2: Event Loop & Concurrency Interleaving (Level 2 Standard Exam)
# ============================================================================
def build_event_loop_concurrency(rng: random.Random) -> dict:
    code = (
        "// Task A: Synchronous log\n"
        "console.log('A');\n\n"
        "// Task B: Macrotask (setTimeout 0ms)\n"
        "setTimeout(() => {\n"
        "  console.log('B');\n"
        "}, 0);\n\n"
        "// Task C: Microtask (Promise)\n"
        "Promise.resolve().then(() => {\n"
        "  console.log('C');\n"
        "});\n\n"
        "// Task D: Microtask (queueMicrotask)\n"
        "queueMicrotask(() => {\n"
        "  console.log('D');\n"
        "});\n\n"
        "// Task E: Synchronous log\n"
        "console.log('E');"
    )

    stdout, stderr, exit_code = run_node(code)
    if exit_code != 0:
        raise RuntimeError(f"Event Loop snippet failed: {stderr}")

    lines = stdout.splitlines()
    answer_plain = ", ".join(lines)

    return {
        "category": "Event Loop and Concurrency",
        "context": "Call Stack vs Microtasks vs Macrotasks",
        "prompt": (
            "Trace the execution of Tasks [A, B, C, D, E] through the Call Stack, Microtask Queue, and Task Queue. "
            "Predict the exact letter sequence printed to the console."
        ),
        "codeSnippet": code,
        "language": "javascript",
        "codeType": "predict-output",
        "answerSpec": {
            "type": "code_output",
            "tokens": lines,
            "value": answer_plain,
            "commonTrapTag": "microtask-order",
        },
        "answerPlain": answer_plain,
        "answerDisplay": answer_plain,
        "inputHint": "e.g. A, B, C, D, E (enter letters separated by comma or space)",
        "checkpointHint": (
            "Determine which tasks run synchronously on the Call Stack, then drain Microtasks (C, D) before Macrotasks (B)."
        ),
        "commonTrapTag": "microtask-order",
        "steps": [
            {
                "latex": "\\text{Call Stack (Synchronous): A, E}",
                "explain": (
                    "Top-level statements execute first synchronously on the Call Stack: "
                    "Task A logs immediately, Task B (setTimeout) is queued to the Task Queue, "
                    "Task C (Promise.then) is queued to the Microtask Queue, Task D (queueMicrotask) is queued to the Microtask Queue, "
                    "and Task E logs synchronously on the Call Stack."
                ),
            },
            {
                "latex": "\\text{Microtask Queue: C, D}",
                "explain": (
                    "Once the Call Stack empties, the JavaScript engine drains the Microtask Queue completely before picking any Macrotask: "
                    "Task C (Promise) logs, followed by Task D (queueMicrotask)."
                ),
            },
            {
                "latex": "\\text{Task Queue (Macrotask): B}",
                "explain": (
                    "Only after the Microtask Queue is completely drained does the event loop execute the next Macrotask: "
                    "Task B (setTimeout callback) runs and logs."
                ),
            },
        ],
        "references": ["PRG-T01-C01-U07", "PRG-T01-C01-U06"],
        "verify": {"source": answer_plain},
    }


# ============================================================================
# TEMPLATE 3: Promise Chaining & Error Recovery (Level 2 Standard Exam)
# ============================================================================
def build_promise_async_flow(rng: random.Random) -> dict:
    threshold = rng.choice([10, 20, 50])
    input_val = rng.choice([5, 15, 25, 60])
    factor = rng.choice([2, 3])
    fallback = rng.choice([100, 200])
    addend = rng.choice([1, 5, 10])

    code = (
        f"async function compute(n) {{\n"
        f"  if (n < {threshold}) {{\n"
        f"    throw new Error('below_threshold');\n"
        f"  }}\n"
        f"  return n * {factor};\n"
        f"}}\n\n"
        f"compute({input_val})\n"
        f"  .catch(() => {fallback})\n"
        f"  .then(val => {{\n"
        f"    console.log(val + {addend});\n"
        f"  }});"
    )

    stdout, stderr, exit_code = run_node(code)
    if exit_code != 0:
        raise RuntimeError(f"Promise flow snippet failed: {stderr}")

    lines = stdout.splitlines()
    answer_plain = ", ".join(lines)

    is_below = input_val < threshold
    step1_explain = (
        f"Because input {input_val} < {threshold}, compute throws an Error, returning a rejected Promise."
        if is_below
        else f"Because input {input_val} >= {threshold}, compute succeeds and returns resolved Promise({input_val * factor})."
    )

    step2_explain = (
        f"The .catch() handler intercepts the rejection and returns {fallback}, converting the chain back to a resolved Promise. "
        f"The downstream .then() receives {fallback} and logs {fallback} + {addend} = {lines[0]}."
        if is_below
        else f"The .catch() is skipped because the Promise resolved. "
        f"The .then() handler receives {input_val * factor} and logs {input_val * factor} + {addend} = {lines[0]}."
    )

    return {
        "category": "Promises and Error Handling",
        "context": "Promise Rejection Recovery",
        "prompt": (
            "Analyze the asynchronous execution flow below. Predict the single integer printed to the terminal."
        ),
        "codeSnippet": code,
        "language": "javascript",
        "codeType": "predict-output",
        "answerSpec": {
            "type": "code_output",
            "tokens": lines,
            "value": answer_plain,
            "commonTrapTag": "unhandled-rejection",
        },
        "answerPlain": answer_plain,
        "answerDisplay": answer_plain,
        "inputHint": "e.g. 42 (enter the resulting output)",
        "checkpointHint": ("Check whether the async function throws or returns, and whether .catch handles it."),
        "commonTrapTag": "unhandled-rejection",
        "steps": [
            {
                "latex": f"\\text{{Initial Call: }} \\text{{compute}}({input_val})",
                "explain": step1_explain,
            },
            {
                "latex": f"\\text{{Chain Resolution: }} \\text{{Output}} = {lines[0]}",
                "explain": step2_explain,
            },
        ],
        "references": ["PRG-T01-C01-U06", "PRG-T01-C01-U08"],
        "verify": {"source": answer_plain},
    }


# ============================================================================
# TEMPLATE 4: Find the Bug — Lost 'this' Binding (Level 3 Trap & Diagnostic)
# ============================================================================
def build_find_bug_this_binding(rng: random.Random) -> dict:
    name = rng.choice(["Alice", "Bob", "Charlie"])
    role = rng.choice(["Engineer", "Architect", "Designer"])

    code = (
        f"class Service {{\n"
        f"  constructor(name, role) {{\n"
        f"    this.name = name;\n"
        f"    this.role = role;\n"
        f"  }}\n"
        f"  getDetails() {{\n"
        f"    return `${{this.name}} (${{this.role}})`;\n"
        f"  }}\n"
        f"}}\n"
        f"const s = new Service('{name}', '{role}');\n"
        f"const execute = s.getDetails;\n"
        f"console.log(execute());"
    )

    # Bug is at line 11 (extracting method reference detaches this receiver)
    correct_line = 11

    # Fixed code snippet for verification
    fixed_code = (
        f"class Service {{\n"
        f"  constructor(name, role) {{\n"
        f"    this.name = name;\n"
        f"    this.role = role;\n"
        f"  }}\n"
        f"  getDetails() {{\n"
        f"    return `${{this.name}} (${{this.role}})`;\n"
        f"  }}\n"
        f"}}\n"
        f"const s = new Service('{name}', '{role}');\n"
        f"const execute = s.getDetails.bind(s);\n"
        f"console.log(execute());"
    )

    return {
        "category": "this and Binding",
        "context": "Detached Method Reference",
        "prompt": (
            "The following JavaScript code snippet throws a TypeError: Cannot read properties of undefined (reading 'name') "
            "when executed in strict mode. Identify the line number where the reference is extracted without its receiver context."
        ),
        "codeSnippet": code,
        "language": "javascript",
        "codeType": "find-bug",
        "answerSpec": {
            "type": "line_number",
            "correctLine": correct_line,
            "flawExplanation": (
                f"Line {correct_line} assigns the method reference directly to 'execute' without preserving its context ('s'). "
                f"When invoked at line 12 as execute(), 'this' is undefined in strict mode."
            ),
            "commonTrapTag": "this-binding-lost",
        },
        "answerPlain": str(correct_line),
        "answerDisplay": f"Line {correct_line}",
        "inputHint": "e.g. 4 (click on the line above or enter line number)",
        "checkpointHint": ("Look for where the function reference is decoupled from its parent object."),
        "commonTrapTag": "this-binding-lost",
        "steps": [
            {
                "latex": f"\\text{{Root Cause at Line }} {correct_line}",
                "explain": (
                    f"At line {correct_line}, 'const execute = s.getDetails' strips the receiver ('s') from the function reference. "
                    f"In JavaScript, class methods operate in strict mode by default."
                ),
            },
            {
                "latex": "\\text{{Invocation at Line 12}}",
                "explain": (
                    "When execute() is invoked as a plain function call without a dot notation receiver, "
                    "'this' defaults to undefined, causing property access 'this.name' on line 7 to crash."
                ),
            },
            {
                "latex": "\\text{{Remediation}}",
                "explain": (
                    "To fix this defect, explicitly bind the receiver: 's.getDetails.bind(s)' or wrap in an arrow function: '() => s.getDetails()'."
                ),
            },
        ],
        "references": ["PRG-T01-C01-U03"],
        "verify": {
            "fixedSnippet": fixed_code,
            "source": str(correct_line),
        },
    }


# ============================================================================
# TEMPLATE 5: Prototype Chain Mutation vs Shadowing (Level 4 Applied Synthesis)
# ============================================================================
def build_prototype_chain_mutation(rng: random.Random) -> dict:
    val_proto = rng.choice([10, 20, 50])
    val_child = rng.choice([100, 200, 500])
    tag = rng.choice(["itemA", "itemB", "itemC"])

    code = (
        f"const proto = {{ config: {val_proto}, tags: ['init'] }};\n"
        f"const child = Object.create(proto);\n"
        f"child.config = {val_child};\n"
        f"child.tags.push('{tag}');\n"
        f"console.log(proto.config);\n"
        f"console.log(proto.tags.length);\n"
        f"console.log(child.config);"
    )

    stdout, stderr, exit_code = run_node(code)
    if exit_code != 0:
        raise RuntimeError(f"Prototype snippet failed: {stderr}")

    lines = stdout.splitlines()
    answer_plain = ", ".join(lines)

    return {
        "category": "Prototypes and Inheritance",
        "context": "Prototype Mutation vs Own Property Shadowing",
        "prompt": (
            "Analyze the prototype relationship created via Object.create. "
            "Predict the three outputs printed to the console in order."
        ),
        "codeSnippet": code,
        "language": "javascript",
        "codeType": "predict-output",
        "answerSpec": {
            "type": "code_output",
            "tokens": lines,
            "value": answer_plain,
            "commonTrapTag": "prototype-mutation",
        },
        "answerPlain": answer_plain,
        "answerDisplay": answer_plain,
        "inputHint": "e.g. 5, 1, 50 (enter the 3 printed numbers separated by comma or space)",
        "checkpointHint": (
            "Differentiate between assigning a new property on child vs mutating an object referenced on proto."
        ),
        "commonTrapTag": "prototype-mutation",
        "steps": [
            {
                "latex": f"\\text{{Property Assignment: }} \\text{{child.config}} = {val_child}",
                "explain": (
                    f"Direct assignment 'child.config = {val_child}' creates an own property on 'child'. "
                    f"It shadows the prototype property without modifying 'proto.config', so proto.config remains {lines[0]}."
                ),
            },
            {
                "latex": f"\\text{{Array Mutation: }} \\text{{child.tags.push}}('{tag}')",
                "explain": (
                    "Because 'child' does not have its own 'tags' property, the lookup traverses the prototype chain to 'proto.tags'. "
                    f"Calling .push('{tag}') mutates the single shared array on the prototype, increasing proto.tags.length to {lines[1]}."
                ),
            },
            {
                "latex": f"\\text{{Own Property Read: }} \\text{{child.config}} = {lines[2]}",
                "explain": (f"Reading child.config retrieves its own shadowed property, evaluating to {lines[2]}."),
            },
        ],
        "references": ["PRG-T01-C01-U04"],
        "verify": {"source": answer_plain},
    }


TEMPLATES = [
    {
        "key": "scope_hoisting_loop",
        "level": 1,
        "trapTag": "var-vs-let-scope",
        "build": build_scope_hoisting_loop,
    },
    {
        "key": "event_loop_concurrency",
        "level": 2,
        "trapTag": "microtask-order",
        "build": build_event_loop_concurrency,
    },
    {
        "key": "promise_async_flow",
        "level": 2,
        "trapTag": "unhandled-rejection",
        "build": build_promise_async_flow,
    },
    {
        "key": "find_bug_this_binding",
        "level": 3,
        "trapTag": "this-binding-lost",
        "build": build_find_bug_this_binding,
    },
    {
        "key": "prototype_chain_mutation",
        "level": 4,
        "trapTag": "prototype-mutation",
        "build": build_prototype_chain_mutation,
    },
]
