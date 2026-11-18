/**
 * Inline math in drill text: `$...$` is math, `\$` is a literal dollar sign (money), inside or outside math.
 * Drill prompts write money as `$\$15$` or `\$15`; the ingest gate (math_engine/verify.check_text_safety)
 * already treats `\$` as a dollar sign, so the renderers must too.
 */

/** One `$...$` math token whose delimiters are not escaped; `\$` may appear inside it. */
export const MATH_TOKEN = String.raw`(?<!\\)\$(?:\\\$|[^$])+?(?<!\\)\$`;

/** Split text into plain and `$...$` segments (math segments keep their `$` delimiters). */
export function splitMath(text: string): string[] {
  return text.split(new RegExp(`(${MATH_TOKEN})`, "g")).filter(Boolean);
}

export function isMathSegment(seg: string): boolean {
  return seg.length > 2 && seg.startsWith("$") && seg.endsWith("$") && !seg.startsWith("\\$");
}

/** Plain text: `\$` shows as `$`. */
export function unescapeDollar(plain: string): string {
  return plain.replace(/\\\$/g, "$");
}

/** Plain-text math in figure labels (`y = sqrt(x - 3)`) as `$...$` LaTeX, like math_engine/figure_builder.py. */
export function toMathText(raw: string): string {
  if (raw.startsWith("$")) return raw;
  const tex = raw
    .replace(/\bcbrt\(([^()]*)\)/g, "\\sqrt[3]{$1}")
    .replace(/\bsqrt\(([^()]*)\)/g, "\\sqrt{$1}");
  return `$${tex}$`;
}

// Keep in sync with math_engine/latex_guard.py.
const KNOWN_MATH_FUNCTIONS = new Set([
  "sin", "cos", "tan", "cot", "sec", "csc",
  "arcsin", "arccos", "arctan", "arccot", "arcsec", "arccsc",
  "sinh", "cosh", "tanh", "coth", "sech", "csch",
  "asinh", "acosh", "atanh",
  "log", "ln", "lg", "exp",
  "min", "max", "inf", "sup", "lim", "limsup", "liminf",
  "gcd", "lcm", "deg", "det", "dim", "ker", "im", "arg",
  "mod", "bmod", "pmod", "sgn", "floor", "ceil", "round", "abs",
  "sqrt", "cbrt", "Re", "Im", "Pr", "hom",
]);

const THREE_LETTER_WORDS = new Set([
  "add", "age", "air", "all", "and", "any", "are", "arm", "ask",
  "bad", "bar", "bed", "big", "bit", "box", "bus", "but", "buy",
  "can", "car", "cat", "col", "cup", "cut", "day", "did", "div",
  "dog", "dot", "due", "end", "era", "far", "fee", "few", "fit",
  "fix", "for", "gap", "gas", "get", "had", "has", "her", "hex",
  "him", "his", "hot", "how", "hrs", "ice", "iff", "ill", "its",
  "job", "key", "law", "lay", "led", "leg", "let", "lie", "lot",
  "low", "map", "may", "men", "met", "mid", "mix", "net", "new",
  "non", "nor", "not", "now", "odd", "off", "oil", "old", "one",
  "our", "out", "own", "pay", "per", "put", "raw", "ray", "red",
  "row", "run", "sat", "saw", "say", "sea", "see", "set", "she",
  "six", "sky", "sub", "sum", "sun", "tax", "ten", "the", "til",
  "tip", "too", "top", "try", "two", "use", "val", "van", "var",
  "via", "was", "way", "who", "why", "won", "yes", "yet", "you",
]);

const SKIP_BRACE_ARG_COMMANDS = new Set([
  "text", "textrm", "textit", "textbf", "textsf", "texttt",
  "mathrm", "mathbf", "mathit", "mathsf", "mathtt", "mathcal",
  "mathbb", "mathfrak", "operatorname", "mbox", "hbox",
  "label", "ref", "tag", "color", "textcolor", "begin", "end",
]);

function isAsciiLetter(ch: string): boolean {
  const code = ch.charCodeAt(0);
  return (code >= 65 && code <= 90) || (code >= 97 && code <= 122);
}

function consumeBalancedBraces(tex: string, idx: number): number {
  const n = tex.length;
  let depth = 0;
  let i = idx;
  while (i < n) {
    const ch = tex[i];
    if (ch === "\\" && i + 1 < n) {
      i += 2;
      continue;
    }
    if (ch === "{") {
      depth += 1;
    } else if (ch === "}") {
      depth -= 1;
      if (depth === 0) return i + 1;
    }
    i += 1;
  }
  return n;
}

function unprotectedSlices(tex: string): Array<[number, number]> {
  const n = tex.length;
  const slices: Array<[number, number]> = [];
  let curStart: number | null = null;
  let i = 0;
  while (i < n) {
    if (tex[i] === "\\") {
      if (curStart !== null) {
        slices.push([curStart, i]);
        curStart = null;
      }
      if (i + 1 < n && isAsciiLetter(tex[i + 1])) {
        let j = i + 1;
        while (j < n && isAsciiLetter(tex[j])) j += 1;
        const cmd = tex.slice(i + 1, j);
        i = j;
        if (SKIP_BRACE_ARG_COMMANDS.has(cmd)) {
          let k = i;
          if (k < n && tex[k] === "*") k += 1;
          while (k < n && (tex[k] === " " || tex[k] === "\t")) k += 1;
          if (k < n && tex[k] === "{") {
            i = consumeBalancedBraces(tex, k);
          }
        }
      } else {
        i = Math.min(i + 2, n);
      }
    } else {
      if (curStart === null) curStart = i;
      i += 1;
    }
  }
  if (curStart !== null) slices.push([curStart, n]);
  return slices;
}

interface WordToken {
  start: number;
  end: number;
  base: string;
  isCand: boolean;
  isStrong: boolean;
  isBridge: boolean;
}

function isProseGap(gap: string, prevLen: number, currLen: number): boolean {
  if (!gap || !/^[ \t\n\r,;:!?\u2019'.-]+$/.test(gap)) return false;
  if (gap.includes("-") && gap !== "-") return false;
  if (prevLen === 2 && currLen === 2 && !/^\s+$/.test(gap) && gap !== "-") return false;
  return true;
}

function isEscapedSpace(tex: string, spaceIdx: number): boolean {
  let bs = 0;
  let k = spaceIdx - 1;
  while (k >= 0 && tex[k] === "\\") {
    bs += 1;
    k -= 1;
  }
  return bs % 2 === 1;
}

/** Find `[start, end)` spans of bare English prose words outside `\text{...}` in a LaTeX string. */
export function findBareWordSpansInLatex(tex: string): Array<[number, number]> {
  if (!tex) return [];
  const results: Array<[number, number]> = [];
  const tokenRe = /[A-Za-z]{2,}(?:['\u2019][A-Za-z]+)?|[A-Za-z]/g;

  for (const [sStart, sEnd] of unprotectedSlices(tex)) {
    const segment = tex.slice(sStart, sEnd);
    const tokens: WordToken[] = [];
    tokenRe.lastIndex = 0;
    let m: RegExpExecArray | null;
    while ((m = tokenRe.exec(segment)) !== null) {
      const raw = m[0];
      const base = raw.split(/['\u2019]/, 1)[0];
      const isSingle = base.length === 1;
      const isAllCaps = base.length >= 2 && base === base.toUpperCase() && base !== base.toLowerCase();
      const isKnownFn = KNOWN_MATH_FUNCTIONS.has(base);
      const isBridge = base === "a" || base === "I";
      const isCand = !isSingle && !isAllCaps && !isKnownFn;
      const isStrong =
        isCand && (base.length >= 4 || (base.length === 3 && THREE_LETTER_WORDS.has(base.toLowerCase())));
      tokens.push({
        start: sStart + m.index,
        end: sStart + m.index + raw.length,
        base,
        isCand,
        isStrong,
        isBridge,
      });
    }

    let i = 0;
    while (i < tokens.length) {
      const first = tokens[i];
      if (!first.isCand && !first.isBridge) {
        i += 1;
        continue;
      }
      const run: WordToken[] = [first];
      let j = i + 1;
      while (j < tokens.length) {
        const prev = run[run.length - 1];
        const curr = tokens[j];
        const gap = tex.slice(prev.end, curr.start);
        const currIsFnBridge =
          KNOWN_MATH_FUNCTIONS.has(curr.base) &&
          j + 1 < tokens.length &&
          (tokens[j + 1].isCand || tokens[j + 1].isBridge) &&
          isProseGap(tex.slice(curr.end, tokens[j + 1].start), curr.base.length, tokens[j + 1].base.length);
        if (!curr.isCand && !curr.isBridge && !currIsFnBridge) break;
        if (!isProseGap(gap, prev.base.length, curr.base.length)) break;
        run.push(curr);
        j += 1;
      }

      while (run.length > 0 && !run[0].isCand) {
        if (run.length >= 2 && run[1].isStrong) break;
        run.shift();
      }
      while (run.length > 0 && !run[run.length - 1].isCand) {
        run.pop();
      }

      const candCount = run.filter((t) => t.isCand).length;
      const hasStrong = run.some((t) => t.isStrong);
      if (run.length > 0 && (hasStrong || candCount >= 2)) {
        results.push([run[0].start, run[run.length - 1].end]);
        i = j;
      } else {
        i += 1;
      }
    }
  }
  return results;
}

/** Safety net for KaTeX: wrap any bare English word runs outside `\text{...}` in `\text{...}`. */
export function wrapBareWordsInLatex(tex: string): string {
  if (!tex) return tex;
  const spans = findBareWordSpansInLatex(tex);
  if (spans.length === 0) return tex;

  const expanded: Array<[number, number]> = [];
  const n = tex.length;
  for (let [start, end] of spans) {
    if (start > 0 && tex[start - 1] === " " && !isEscapedSpace(tex, start - 1)) {
      start -= 1;
    }
    if (end < n && tex[end] === " ") {
      end += 1;
    }
    if (expanded.length > 0 && start <= expanded[expanded.length - 1][1]) {
      expanded[expanded.length - 1][1] = Math.max(expanded[expanded.length - 1][1], end);
    } else {
      expanded.push([start, end]);
    }
  }

  let out = "";
  let pos = 0;
  for (const [start, end] of expanded) {
    if (start > pos) out += tex.slice(pos, start);
    out += `\\text{${tex.slice(start, end)}}`;
    pos = end;
  }
  if (pos < n) out += tex.slice(pos);
  return out;
}
