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
