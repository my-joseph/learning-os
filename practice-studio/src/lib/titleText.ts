/**
 * Strip inline Markdown backtick markers from curriculum/drill titles
 * (e.g. "`this` and Binding" -> "this and Binding") and trim whitespace.
 */
export function plainTitle(title: string | null | undefined): string {
  if (typeof title !== "string") return "";
  return title.replace(/`/g, "").trim();
}
