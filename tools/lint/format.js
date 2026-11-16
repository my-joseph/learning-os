import path from "node:path";

/**
 * Custom ESLint formatter outputting `file:line rule message` one per line.
 *
 * @param {Array<import("eslint").ESLint.LintResult>} results
 * @returns {string}
 */
export default function format(results) {
  const lines = [];
  const cwd = process.cwd();
  for (const result of results) {
    if (!result.messages || result.messages.length === 0) {
      continue;
    }
    const rel = path.relative(cwd, result.filePath) || result.filePath;
    for (const msg of result.messages) {
      const rule = msg.ruleId || "syntax";
      lines.push(`${rel}:${msg.line} ${rule} ${msg.message}`);
    }
  }
  return lines.join("\n");
}
