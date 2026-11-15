import { ChoiceOption } from "@/types/drill";

export interface ParsedLineChoiceItem {
  option: ChoiceOption;
  lineNumber: number;
  label: string;
  content: string;
}

export interface ParsedLineChoicePrompt {
  intro: string;
  items: ParsedLineChoiceItem[];
  outro: string;
}

const LINE_RE = /^Line\s+(\d+)\s*:\s*(.*)$/i;
const OPT_LINE_RE = /^Line\s+(\d+)$/i;

/**
 * Detects prompts with sequential `Line N: ...` rows whose numbers match all
 * `answerSpec.options`, allowing the line list and choice selector to share a single UI.
 */
export function parseLineChoicePrompt(
  prompt: string,
  options?: ChoiceOption[]
): ParsedLineChoicePrompt | null {
  if (!prompt || !options || options.length === 0) return null;

  const lines = prompt.split("\n");
  const introLines: string[] = [];
  const outroLines: string[] = [];
  const parsedMap = new Map<number, string>();

  let phase: "intro" | "lines" | "outro" = "intro";

  for (const rawLine of lines) {
    const trimmed = rawLine.trim();
    const match = trimmed.match(LINE_RE);

    if (match) {
      if (phase === "outro") {
        // Non-contiguous Line blocks fall back to standard prompt + choice buttons
        return null;
      }
      phase = "lines";
      const lineNum = Number(match[1]);
      if (parsedMap.has(lineNum)) return null;
      parsedMap.set(lineNum, match[2]);
    } else {
      if (phase === "lines") {
        phase = "outro";
      }
      if (phase === "intro") {
        introLines.push(rawLine);
      } else {
        outroLines.push(rawLine);
      }
    }
  }

  if (parsedMap.size !== options.length) return null;

  const items: ParsedLineChoiceItem[] = [];
  for (const opt of options) {
    const labelMatch = opt.label.trim().match(OPT_LINE_RE);
    const lineNum = labelMatch
      ? Number(labelMatch[1])
      : /^\d+$/.test(opt.id.trim())
      ? Number(opt.id.trim())
      : NaN;

    if (!Number.isFinite(lineNum) || !parsedMap.has(lineNum)) {
      return null;
    }

    items.push({
      option: opt,
      lineNumber: lineNum,
      label: opt.label,
      content: parsedMap.get(lineNum)!,
    });
  }

  return {
    intro: introLines.join("\n").trim(),
    items,
    outro: outroLines.join("\n").trim(),
  };
}
