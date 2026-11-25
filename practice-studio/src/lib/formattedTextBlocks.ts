type TableAlign = "left" | "center" | "right" | undefined;

export type ProseBlock =
  | { kind: "paragraph"; lines: string[] }
  | { kind: "heading"; level: number; text: string }
  | { kind: "list"; ordered: boolean; items: { number?: number; blocks: ProseBlock[] }[] }
  | { kind: "table"; cells: string[][]; align: TableAlign[] }
  | { kind: "quote"; blocks: ProseBlock[] }
  | { kind: "rule" }
  | { kind: "math"; latex: string }
  | { kind: "code"; info: string; code: string };

function listMarker(line: string) {
  const match = /^([ \t]*)(?:[-*+]|(\d{1,9})[.)])[ \t]+(.+)$/.exec(line);
  if (!match) return null;
  return {
    depth: match[1].length,
    number: match[2] === undefined ? undefined : Number(match[2]),
    content: match[3],
    contentOffset: line.length - match[3].length,
  };
}

function indentation(line: string) {
  return line.length - line.trimStart().length;
}

function isRule(line: string) {
  return /^(?:-(?: *-){2,}|\*(?: *\*){2,}|_(?: *_){2,})$/.test(line);
}

function tableCells(line: string) {
  if (!/(?<!\\)\|/.test(line)) return null;
  return line.trim().replace(/^\||(?<!\\)\|$/g, "")
    .split(/(?<!\\)\|/).map((cell) => cell.replace(/\\\|/g, "|").trim());
}

function blockAt(lines: string[], start: number): { block: ProseBlock; end: number } | null {
  const line = lines[start].trim();
  const next = lines[start + 1]?.trim() ?? "";

  const fence = /^```(.*)$/.exec(line);
  if (fence) {
    let end = start + 1;
    while (end < lines.length && !lines[end].trim().startsWith("```")) end++;
    return {
      block: { kind: "code", info: fence[1].trim(), code: lines.slice(start + 1, end).join("\n") },
      end: Math.min(end + 1, lines.length),
    };
  }

  const display = /^(?:\$\$|\\\[)/.exec(line)?.[0];
  if (display) {
    const close = display === "$$" ? "$$" : "\\]";
    if (line.length > 4 && line.endsWith(close)) {
      return { block: { kind: "math", latex: line.slice(2, -2).trim() }, end: start + 1 };
    }
    if (line === display) {
      let end = start + 1;
      while (end < lines.length && lines[end].trim() !== close) end++;
      if (end < lines.length) {
        return { block: { kind: "math", latex: lines.slice(start + 1, end).join("\n") }, end: end + 1 };
      }
    }
  }

  const heading = /^(#{1,6})\s+(.+)$/.exec(line);
  if (heading) {
    return { block: { kind: "heading", level: heading[1].length, text: heading[2] }, end: start + 1 };
  }

  // Older prompts use standalone labels above lists instead of Markdown headings.
  const boldLabel = /^\*\*([^*]+)\*\*(:?)$/.exec(line);
  const plainLabel = /^[A-Z][\w-]*(?: (?:[A-Z][\w-]*|and|of|the|for))*:$/.test(line);
  if ((boldLabel || plainLabel) && (listMarker(next) || (!next && listMarker(lines[start + 2] ?? "")))) {
    const text = boldLabel ? boldLabel[1] + boldLabel[2] : line;
    return { block: { kind: "heading", level: 4, text }, end: start + 1 };
  }

  if (isRule(line)) return { block: { kind: "rule" }, end: start + 1 };

  if (/^>(?:\s|$)/.test(line)) {
    let end = start;
    const quoted: string[] = [];
    while (end < lines.length && /^>(?:\s|$)/.test(lines[end].trimStart())) {
      quoted.push(lines[end].trimStart().replace(/^> ?/, ""));
      end++;
    }
    return { block: { kind: "quote", blocks: parseBlocks(quoted) }, end };
  }

  const marker = listMarker(lines[start]);
  if (marker) {
    const ordered = marker.number !== undefined;
    const items: Extract<ProseBlock, { kind: "list" }>["items"] = [];
    let end = start;
    while (end < lines.length) {
      const item = listMarker(lines[end]);
      if (!item || item.depth !== marker.depth || (item.number !== undefined) !== ordered) break;

      const content = [item.content];
      end++;
      while (end < lines.length) {
        if (!lines[end].trim()) {
          let following = end + 1;
          while (following < lines.length && !lines[following].trim()) following++;
          if (following === lines.length) break;
          if (indentation(lines[following]) <= marker.depth && !listMarker(lines[following])) break;
          content.push("");
          end = following;
        }
        const indent = indentation(lines[end]);
        if (indent <= marker.depth) break;
        content.push(lines[end].slice(Math.min(indent, item.contentOffset)));
        end++;
      }
      items.push({ number: item.number, blocks: parseBlocks(content) });
    }
    return { block: { kind: "list", ordered, items }, end };
  }

  const header = tableCells(line);
  const divider = tableCells(next);
  if (header && divider?.length === header.length && divider.every((cell) => /^:?-{3,}:?$/.test(cell))) {
    const align = divider.map((cell) => cell.endsWith(":")
      ? cell.startsWith(":") ? "center" : "right"
      : cell.startsWith(":") ? "left" : undefined);
    const cells = [header];
    let end = start + 2;
    while (end < lines.length) {
      const row = tableCells(lines[end]);
      if (row?.length !== header.length) break;
      cells.push(row);
      end++;
    }
    return { block: { kind: "table", align, cells }, end };
  }

  return null;
}

function parseBlocks(lines: string[]): ProseBlock[] {
  const blocks: ProseBlock[] = [];
  let paragraph: string[] = [];

  function flushParagraph() {
    if (!paragraph.length) return;
    blocks.push({ kind: "paragraph", lines: paragraph });
    paragraph = [];
  }

  let index = 0;
  while (index < lines.length) {
    if (!lines[index].trim()) {
      flushParagraph();
      index++;
      continue;
    }
    const result = blockAt(lines, index);
    if (result) {
      flushParagraph();
      blocks.push(result.block);
      index = result.end;
    } else {
      paragraph.push(lines[index]);
      index++;
    }
  }
  flushParagraph();
  return blocks;
}

export function parseFormattedText(text: string): ProseBlock[] {
  return parseBlocks(text.split(/\r?\n/));
}
