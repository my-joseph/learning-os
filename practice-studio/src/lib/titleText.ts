/**
 * Strip inline Markdown backtick markers from curriculum/drill titles
 * (e.g. "`this` and Binding" -> "this and Binding") and trim whitespace.
 */
export function plainTitle(title: string | null | undefined): string {
  if (typeof title !== "string") return "";
  return title.replace(/`/g, "").trim();
}

const TRAP_PREFIX_RE = /^(?:t\d+-)?(?:c\d+-)?(?:u\d+-)?/i;

/**
 * Plain-language name from a trap tag (mirrors `scripts.weak_spots.trap_name`):
 * e.g. `t02-c01-u01-i-squared-positive-one-trap` -> `I squared positive one`.
 */
export function trapName(trapId: string | null | undefined): string {
  const clean = plainTitle(trapId);
  if (!clean) return "";
  const words = clean
    .toLowerCase()
    .replace(TRAP_PREFIX_RE, "")
    .replace(/-trap$/i, "")
    .replace(/-/g, " ")
    .trim();
  if (!words) return clean;
  const [first, ...rest] = words.split(" ");
  const prefix = /^[a-z]{2,}$/.test(first) && /^[A-Z0-9]+-/.test(clean)
    ? first.toUpperCase()
    : first.slice(0, 1).toUpperCase() + first.slice(1);
  return [prefix, ...rest].join(" ");
}

export const trapTitle = trapName;

