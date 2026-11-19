import type { AnswerSpec, Problem } from "@/types/drill";

export type MathInputMode = "math" | "plain";

export const MATH_INPUT_MODE_STORAGE_KEY = "practice_studio_math_input_mode";

/**
 * AnswerSpec types whose expected answers map cleanly to MathLive WYSIWYG math
 * input and normalise into the plain-text syntax accepted by `math_engine/answer_check.py`.
 * `choice` uses auto-submit option buttons; `text` and unknown types stay plain text.
 */
export const SUPPORTED_MATH_ANSWER_TYPES = new Set<string>([
  "number",
  "complex",
  "expression",
  "solution_set",
  "interval",
  "tuple",
  "vector",
]);

/** Return true when a problem's answerSpec should use the MathLive input by default. */
export function isMathLiveSupportedAnswerSpec(
  answerSpec?: Pick<AnswerSpec, "type"> | null
): boolean {
  const type = answerSpec?.type;
  if (!type) return false;
  return SUPPORTED_MATH_ANSWER_TYPES.has(type);
}

export interface UnitKeyboardProfile {
  trig: boolean;
  log: boolean;
}

/**
 * Determine whether the current unit/question needs trig or log virtual-keyboard keys.
 * Uses only learner-visible metadata (unitCode, drillTitle, prompt, inputHint) — never answerSpec.value.
 */
export function getUnitKeyboardProfile(options: {
  unitCode?: string | null;
  drillTitle?: string | null;
  prompt?: string | null;
  inputHint?: string | null;
}): UnitKeyboardProfile {
  const unitCode = options.unitCode || "";
  const title = options.drillTitle || "";
  const promptText = `${options.prompt || ""}\n${options.inputHint || ""}`;

  const trig =
    /MTH-T02-C0[6-9]/i.test(unitCode) ||
    /\b(trig|trigonometr|sine|cosine|tangent|unit circle|periodic|polar|inverse trig)\b/i.test(title) ||
    /\\(?:sin|cos|tan|arcsin|arccos|arctan)\b|\b(?:sin|cos|tan|arcsin|arccos|arctan)\s*\(/i.test(promptText);

  const log =
    /MTH-T02-C05/i.test(unitCode) ||
    /\b(log|logarithm|logarithmic|exponential)\b/i.test(title) ||
    /\\(?:ln|log)\b|\b(?:ln|log)\s*\(/i.test(promptText);

  return { trig, log };
}

/** Read preferred math input mode ("math" | "plain") safely from localStorage. */
export function readMathInputMode(): MathInputMode {
  if (typeof window === "undefined") return "math";
  try {
    const saved = window.localStorage.getItem(MATH_INPUT_MODE_STORAGE_KEY);
    return saved === "plain" ? "plain" : "math";
  } catch {
    return "math";
  }
}

/** Persist preferred math input mode safely in localStorage. */
export function writeMathInputMode(mode: MathInputMode): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(MATH_INPUT_MODE_STORAGE_KEY, mode);
  } catch {
    // ignore storage access/quota errors
  }
}

const KNOWN_FUNCTIONS = new Set([
  "sqrt",
  "sin",
  "cos",
  "tan",
  "ln",
  "log",
  "abs",
  "Abs",
  "exp",
  "re",
  "im",
  "conjugate",
  "diff",
  "floor",
  "round",
]);

// Ordered longest-first for greedy identifier splitting (e.g. "pi" before "p", "sqrt" before "s").
const ATOMIC_IDENTIFIERS = [
  "conjugate",
  "infinity",
  "sqrt",
  "floor",
  "round",
  "diff",
  "Abs",
  "abs",
  "sin",
  "cos",
  "tan",
  "exp",
  "log",
  "inf",
  "ln",
  "pi",
  "oo",
  "re",
  "im",
];

function readBalancedDelim(
  str: string,
  openIdx: number,
  openCh: string,
  closeCh: string
): { content: string; endIdx: number } | null {
  if (str[openIdx] !== openCh) return null;
  let depth = 0;
  for (let i = openIdx; i < str.length; i++) {
    if (str[i] === openCh) depth++;
    else if (str[i] === closeCh) {
      depth--;
      if (depth === 0) {
        return { content: str.slice(openIdx + 1, i), endIdx: i };
      }
    }
  }
  return null;
}

function readBalancedGroup(
  str: string,
  openIdx: number
): { content: string; endIdx: number } | null {
  return readBalancedDelim(str, openIdx, "(", ")");
}

/** Convert MathLive's `root(n)(expr)` into `sqrt(expr)` (for n=2) or `(expr)^(1/(n))`. */
function replaceRootCalls(input: string): string {
  let out = input;
  for (let pass = 0; pass < 16; pass++) {
    const match = /\broot\s*\(/.exec(out);
    if (!match) break;
    const nOpen = match.index + match[0].length - 1;
    const nGroup = readBalancedGroup(out, nOpen);
    if (!nGroup) break;
    let cursor = nGroup.endIdx + 1;
    while (cursor < out.length && /\s/.test(out[cursor])) cursor++;
    const exprGroup = readBalancedGroup(out, cursor);
    if (!exprGroup) break;

    const indexTrimmed = nGroup.content.trim();
    const replacement =
      indexTrimmed === "2"
        ? `sqrt(${exprGroup.content})`
        : `(${exprGroup.content})^(1/(${indexTrimmed}))`;

    out = out.slice(0, match.index) + replacement + out.slice(exprGroup.endIdx + 1);
  }
  return out;
}

/**
 * Convert MathLive/ASCII-math `log _<base>(arg)` (parenthesised `_(base)`,
 * braced `_{base}`, or single-token `_2` / `_b` / `_10`, optionally raised
 * to a power like `log _2^2(x)`) into SymPy-compatible `log(arg, base)`.
 */
function replaceLogBaseCalls(input: string): string {
  let out = input;
  let searchFrom = 0;
  for (let pass = 0; pass < 32; pass++) {
    const re = /(?<![A-Za-z])log\s*_\s*/g;
    re.lastIndex = searchFrom;
    const match = re.exec(out);
    if (!match) break;

    const baseStart = match.index + match[0].length;
    let baseContent = "";
    let cursor = baseStart;

    if (out[baseStart] === "(") {
      const baseGroup = readBalancedDelim(out, baseStart, "(", ")");
      if (!baseGroup) {
        searchFrom = baseStart;
        continue;
      }
      baseContent = baseGroup.content.trim();
      cursor = baseGroup.endIdx + 1;
    } else if (out[baseStart] === "{") {
      const baseGroup = readBalancedDelim(out, baseStart, "{", "}");
      if (!baseGroup) {
        searchFrom = baseStart;
        continue;
      }
      baseContent = baseGroup.content.trim();
      cursor = baseGroup.endIdx + 1;
    } else {
      const tokenMatch = /^(?:\d+(?:\.\d+)?|pi|[A-Za-z])/.exec(out.slice(baseStart));
      if (!tokenMatch) {
        searchFrom = baseStart;
        continue;
      }
      baseContent = tokenMatch[0];
      cursor = baseStart + tokenMatch[0].length;
    }

    if (!baseContent) {
      searchFrom = cursor;
      continue;
    }

    while (cursor < out.length && /\s/.test(out[cursor])) cursor++;

    let exp: string | null = null;
    if (out[cursor] === "^") {
      const expMatch = /^\^\s*(\([^)]+\)|\{[^}]+\}|-?\d+|[A-Za-z])/.exec(out.slice(cursor));
      if (expMatch) {
        const rawExp = expMatch[1];
        exp = rawExp.startsWith("{") && rawExp.endsWith("}")
          ? `(${rawExp.slice(1, -1)})`
          : rawExp;
        cursor += expMatch[0].length;
        while (cursor < out.length && /\s/.test(out[cursor])) cursor++;
      }
    }

    const argGroup = readBalancedGroup(out, cursor);
    if (!argGroup) {
      searchFrom = cursor;
      continue;
    }

    const baseCall = `log(${argGroup.content}, ${baseContent})`;
    const replacement = exp ? `(${baseCall})^${exp}` : baseCall;
    out = out.slice(0, match.index) + replacement + out.slice(argGroup.endIdx + 1);
    searchFrom = match.index + (exp ? 5 : 4);
  }
  return out;
}

/** Convert `sin ^2(x)` into `(sin(x))^2`. */
function replaceTrigPowers(input: string): string {
  let out = input;
  for (let pass = 0; pass < 16; pass++) {
    const match = /\b(sin|cos|tan|ln|log)\s*\^\s*(\([^)]+\)|-?\d+|[A-Za-z])\s*\(/.exec(out);
    if (!match) break;
    const fnName = match[1];
    const exp = match[2];
    const argOpen = match.index + match[0].length - 1;
    const argGroup = readBalancedGroup(out, argOpen);
    if (!argGroup) break;

    const replacement = `(${fnName}(${argGroup.content}))^${exp}`;
    out = out.slice(0, match.index) + replacement + out.slice(argGroup.endIdx + 1);
  }
  return out;
}

/** Convert paired `|expr|` bars (including nested `||x|-1|` and `|a|+|b|`) to `abs(expr)`. */
function replaceAbsBars(input: string): string {
  if (!input.includes("|")) return input;

  interface StackEntry {
    outIndex: number;
    parenDepth: number;
  }

  const out: string[] = [];
  const barStack: StackEntry[] = [];
  let parenDepth = 0;
  let lastNonSpace = "";

  for (let i = 0; i < input.length; i++) {
    const ch = input[i];
    if (ch === "(" || ch === "[" || ch === "{") {
      parenDepth++;
      out.push(ch);
      lastNonSpace = ch;
    } else if (ch === ")" || ch === "]" || ch === "}") {
      parenDepth = Math.max(0, parenDepth - 1);
      out.push(ch);
      lastNonSpace = ch;
    } else if (ch === "|") {
      const top = barStack[barStack.length - 1];
      const canClose =
        Boolean(top) &&
        top.parenDepth === parenDepth &&
        lastNonSpace !== "" &&
        !"+-*/^=<>,([{|:".includes(lastNonSpace);

      if (canClose) {
        barStack.pop();
        out.push(")");
        lastNonSpace = ")";
      } else {
        barStack.push({ outIndex: out.length, parenDepth });
        out.push("abs(");
        lastNonSpace = "(";
      }
    } else {
      out.push(ch);
      if (!/\s/.test(ch)) {
        lastNonSpace = ch;
      }
    }
  }

  // Revert any unclosed bars back to literal `|` rather than producing malformed `abs(`.
  for (const unclosed of barStack) {
    out[unclosed.outIndex] = "|";
  }

  return out.join("");
}

type TokenKind = "number" | "ident" | "lparen" | "rparen" | "union" | "logic" | "op";

interface MathToken {
  kind: TokenKind;
  value: string;
}

function tokenizeForMul(expr: string, extraVars: readonly string[]): MathToken[] {
  const tokens: MathToken[] = [];
  const atomicList = [...extraVars, ...ATOMIC_IDENTIFIERS].sort((a, b) => b.length - a.length);
  let i = 0;

  while (i < expr.length) {
    const ch = expr[i];
    if (/\s/.test(ch)) {
      i++;
      continue;
    }

    // Multi-char operators
    if (
      expr.startsWith("+-", i) ||
      expr.startsWith("<=", i) ||
      expr.startsWith(">=", i) ||
      expr.startsWith("!=", i)
    ) {
      tokens.push({ kind: "op", value: expr.slice(i, i + 2) });
      i += 2;
      continue;
    }

    // Numbers
    const numMatch = /^\d+(?:\.\d+)?/.exec(expr.slice(i));
    if (numMatch) {
      tokens.push({ kind: "number", value: numMatch[0] });
      i += numMatch[0].length;
      continue;
    }

    // Subscripted variable like x_1 (used in solution_set inputs)
    const subMatch = /^[A-Za-z]+_\d+/.exec(expr.slice(i));
    if (subMatch) {
      tokens.push({ kind: "ident", value: subMatch[0] });
      i += subMatch[0].length;
      continue;
    }

    // Alphabetic identifiers / keywords
    if (/[A-Za-z]/.test(ch)) {
      const rest = expr.slice(i);
      const wordMatch = /^[A-Za-z]+/.exec(rest)!;
      const word = wordMatch[0];

      // Union operator U / u between interval brackets or standalone
      const prev = tokens[tokens.length - 1];
      let lookaheadIdx = i + 1;
      while (lookaheadIdx < expr.length && /\s/.test(expr[lookaheadIdx])) lookaheadIdx++;
      const nextCh = expr[lookaheadIdx] || "";
      if (
        (word === "U" || word === "u") &&
        prev?.kind === "rparen" &&
        "([{".includes(nextCh)
      ) {
        tokens.push({ kind: "union", value: "U" });
        i += 1;
        continue;
      }

      if ((word === "or" || word === "and") && (!prev || prev.kind !== "number")) {
        tokens.push({ kind: "logic", value: word });
        i += word.length;
        continue;
      }

      // Split concatenated alphabetic run greedily into known atomic identifiers or single letters
      let pos = 0;
      while (pos < word.length) {
        const sub = word.slice(pos);
        const atomic = atomicList.find((id) => sub.startsWith(id));
        if (atomic) {
          const normalizedAtom =
            atomic === "inf" || atomic === "infinity" ? "oo" : atomic;
          tokens.push({ kind: "ident", value: normalizedAtom });
          pos += atomic.length;
        } else {
          tokens.push({ kind: "ident", value: word[pos] });
          pos += 1;
        }
      }
      i += word.length;
      continue;
    }

    if ("([{".includes(ch)) {
      tokens.push({ kind: "lparen", value: ch });
      i++;
      continue;
    }
    if (")]}".includes(ch)) {
      tokens.push({ kind: "rparen", value: ch });
      i++;
      continue;
    }

    tokens.push({ kind: "op", value: ch });
    i++;
  }

  return tokens;
}

function insertExplicitMultiplication(expr: string, extraVars: readonly string[] = []): string {
  const tokens = tokenizeForMul(expr, extraVars);
  if (tokens.length === 0) return "";

  const parts: string[] = [];
  for (let i = 0; i < tokens.length; i++) {
    const t1 = tokens[i];
    if (t1.kind === "union") {
      parts.push(" U ");
      continue;
    }
    if (t1.kind === "logic") {
      parts.push(` ${t1.value} `);
      continue;
    }
    parts.push(t1.value);
    if (t1.value === ",") {
      parts.push(" ");
      continue;
    }

    if (i + 1 < tokens.length) {
      const t2 = tokens[i + 1];
      if (t2.kind === "union" || t2.kind === "logic") continue;

      const t1LeftMul =
        t1.kind === "number" ||
        t1.kind === "rparen" ||
        t1.kind === "ident";
      const t2RightMul =
        t2.kind === "number" ||
        t2.kind === "ident" ||
        t2.kind === "lparen";

      if (t1LeftMul && t2RightMul) {
        const isFuncCall =
          t1.kind === "ident" && KNOWN_FUNCTIONS.has(t1.value) && t2.value === "(";
        // Preserve bracket-bracket interval adjacency only if separated by union/comma;
        // e.g. `(x+1)(x-2)` or `2(x+1)` or `2*pi*i` gets `*`.
        if (!isFuncCall) {
          parts.push("*");
        }
      }
    }
  }

  return parts.join("").replace(/\s+/g, " ").trim();
}

/**
 * Normalise MathLive's `ascii-math` output (optionally guided by raw LaTeX)
 * into the plain-text syntax accepted by `math_engine/answer_check.py`.
 */
export function normalizeMathLiveAsciiMath(
  asciiMath: string,
  latex?: string,
  variables: readonly string[] = []
): string {
  if (latex && latex.includes("\\placeholder{}")) {
    const skeletonStripped = latex
      .replace(/\\placeholder\{\}/g, "")
      .replace(/\\(?:left|right|frac|sqrt|cdot|times|pm|le|ge|ne|infty|cup|pi)\b/g, "")
      .replace(/[\\{}()[\]\s_^+\-*/,=.<>|]/g, "");
    if (!skeletonStripped) {
      return "";
    }
  }

  let s = (asciiMath || "").replace(/[\u200b\u00a0]/g, " ").trim();
  if (!s) return "";

  // Strip stray LaTeX delimiters and map Unicode math operators to checker ASCII equivalents.
  s = s
    .replace(/\\left\b/g, "")
    .replace(/\\right\b/g, "")
    .replace(/\\\{/g, "{")
    .replace(/\\\}/g, "}")
    .replace(/[\u2212\u2013]/g, "-")
    .replace(/[\u00d7\u00b7\u22c5]/g, "*")
    .replace(/\u00f7/g, "/")
    .replace(/\u03c0/g, "pi")
    .replace(/\u221e/g, "oo")
    .replace(/\u222a/g, " U ")
    .replace(/[\u27e8\u3008]/g, "<")
    .replace(/[\u27e9\u3009]/g, ">")
    .replace(/\u2264/g, "<=")
    .replace(/\u2265/g, ">=")
    .replace(/\u2260/g, "!=")
    .replace(/\u00b1/g, "+-")
    .replace(/²/g, "^2")
    .replace(/³/g, "^3")
    .replace(/\*\*/g, "^");

  // Convert MathLive ascii-math structural forms to SymPy-compatible expressions.
  s = replaceTrigPowers(s);
  s = replaceLogBaseCalls(s);
  s = replaceRootCalls(s);
  s = s.replace(
    /\b(sqrt|sin|cos|tan|ln|log|abs|Abs|exp|re|im|conjugate|diff|floor|round)\s+\(/g,
    "$1("
  );
  s = replaceAbsBars(s);

  return insertExplicitMultiplication(s, variables);
}

function splitTopLevelCommas(str: string): string[] {
  const parts: string[] = [];
  let depth = 0;
  let start = 0;
  for (let i = 0; i < str.length; i++) {
    const ch = str[i];
    if ("([{".includes(ch)) depth++;
    else if (")]}".includes(ch)) depth = Math.max(0, depth - 1);
    else if (ch === "," && depth === 0) {
      parts.push(str.slice(start, i).trim());
      start = i + 1;
    }
  }
  parts.push(str.slice(start).trim());
  return parts;
}

function tryIntervalPlainToLatex(
  trimmed: string,
  convertAsciiMathToLatexFn: (ascii: string) => string
): string | null {
  if (!/^[[(]/.test(trimmed) || !/[\])]$/.test(trimmed)) return null;
  // Split top-level union pieces joined by U / u / ∪
  const pieces: string[] = [];
  let i = 0;
  let expectPiece = true;
  while (i < trimmed.length) {
    while (i < trimmed.length && /\s/.test(trimmed[i])) i++;
    if (i >= trimmed.length) break;
    if (expectPiece) {
      const open = trimmed[i];
      if (open !== "(" && open !== "[") return null;
      const start = i;
      let depth = 0;
      while (i < trimmed.length) {
        const c = trimmed[i];
        if ("([{".includes(c)) depth++;
        else if (")]}".includes(c)) {
          depth--;
          if (depth === 0) {
            i++;
            break;
          }
        }
        i++;
      }
      if (depth !== 0) return null;
      pieces.push(trimmed.slice(start, i));
      expectPiece = false;
    } else {
      if (trimmed[i] === "\u222a") {
        i++;
        expectPiece = true;
      } else if (
        (trimmed[i] === "U" || trimmed[i] === "u") &&
        (i + 1 === trimmed.length || !/[A-Za-z0-9_]/.test(trimmed[i + 1]))
      ) {
        i++;
        expectPiece = true;
      } else {
        return null;
      }
    }
  }
  if (expectPiece || pieces.length === 0) return null;

  const latexPieces: string[] = [];
  for (const piece of pieces) {
    const open = piece[0];
    const close = piece[piece.length - 1];
    const inner = piece.slice(1, -1);
    const endpoints = splitTopLevelCommas(inner);
    if (endpoints.length !== 2) return null;
    const leftLatex = plainTextToLatex(endpoints[0], convertAsciiMathToLatexFn);
    const rightLatex = plainTextToLatex(endpoints[1], convertAsciiMathToLatexFn);
    latexPieces.push(`\\left${open}${leftLatex}, ${rightLatex}\\right${close}`);
  }
  return latexPieces.join("\\cup ");
}

/**
 * Convert plain-text checker input back into LaTeX for populating `<math-field>`
 * when restoring saved answers or toggling from plain text to Math input.
 */
export function plainTextToLatex(
  plain: string,
  convertAsciiMathToLatexFn: (ascii: string) => string
): string {
  const trimmed = (plain || "").trim();
  if (!trimmed) return "";

  const intervalLatex = tryIntervalPlainToLatex(trimmed, convertAsciiMathToLatexFn);
  if (intervalLatex !== null) return intervalLatex;

  const prepped = trimmed
    .replace(/\*\*/g, "^")
    .replace(/\u2212|\u2013/g, "-")
    .replace(/\u00b1/g, "+-")
    .replace(/\u2264/g, "<=")
    .replace(/\u2265/g, ">=")
    .replace(/\u2260/g, "!=")
    .replace(/\u03c0/g, "pi")
    .replace(/\u221e/g, "oo")
    .replace(/\binfinity\b|\binf\b/gi, "oo")
    .replace(/\u222a/g, " union ")
    .replace(/(?<=[)\]}])\s*[Uu]\s*(?=[([{])/g, " union ")
    .replace(/\s+[Uu]\s+/g, " union ");

  return convertAsciiMathToLatexFn(prepped);
}

export function getProblemPlaceholder(problem?: Problem): string {
  if (problem?.placeholder) return problem.placeholder;
  if (problem?.inputHint) return problem.inputHint;
  if (problem?.answerSpec?.type === "interval") {
    return "Enter interval, e.g. [a, b) or (-inf, a) U (a, inf)…";
  }
  return "Enter your answer…";
}
