"use client";

import React, { useState } from "react";
import { Copy, Check, FileCode2 } from "lucide-react";

interface VSCodeBlockProps {
  code: string;
  language?: string;
  filename?: string;
  selectableLines?: boolean;
  selectedLine?: number | null;
  onSelectLine?: (line: number) => void;
}

type TokenType =
  | "comment"
  | "string"
  | "keyword"
  | "control"
  | "builtin"
  | "method"
  | "number"
  | "constant"
  | "plain";

interface Token {
  type: TokenType;
  text: string;
}

const CONTROL_KEYWORDS = new Set([
  "if",
  "else",
  "for",
  "while",
  "return",
  "throw",
  "try",
  "catch",
  "finally",
  "switch",
  "case",
  "break",
  "continue",
]);

const GENERAL_KEYWORDS = new Set([
  "const",
  "let",
  "var",
  "function",
  "class",
  "constructor",
  "new",
  "async",
  "await",
  "static",
  "extends",
  "import",
  "export",
  "from",
  "typeof",
  "instanceof",
  "default",
]);

const CONSTANTS = new Set([
  "true",
  "false",
  "null",
  "undefined",
  "NaN",
  "Infinity",
  "this",
]);

const BUILTINS = new Set([
  "console",
  "Promise",
  "setTimeout",
  "setInterval",
  "clearTimeout",
  "queueMicrotask",
  "Object",
  "Array",
  "String",
  "Number",
  "Boolean",
  "Error",
  "TypeError",
]);

function tokenizeLine(line: string): Token[] {
  const tokens: Token[] = [];
  let i = 0;

  while (i < line.length) {
    if (line.slice(i, i + 2) === "//") {
      tokens.push({ type: "comment", text: line.slice(i) });
      break;
    }

    const ch = line[i];
    if (ch === "'" || ch === '"' || ch === "`") {
      const quote = ch;
      let j = i + 1;
      while (j < line.length) {
        if (line[j] === "\\" && j + 1 < line.length) {
          j += 2;
          continue;
        }
        if (line[j] === quote) {
          j++;
          break;
        }
        j++;
      }
      tokens.push({ type: "string", text: line.slice(i, j) });
      i = j;
      continue;
    }

    if (/\d/.test(ch) && (i === 0 || !/[a-zA-Z0-9_$]/.test(line[i - 1]))) {
      let j = i;
      while (j < line.length && /[\d.]/.test(line[j])) {
        j++;
      }
      tokens.push({ type: "number", text: line.slice(i, j) });
      i = j;
      continue;
    }

    if (/[a-zA-Z_$]/.test(ch)) {
      let j = i;
      while (j < line.length && /[a-zA-Z0-9_$]/.test(line[j])) {
        j++;
      }
      const word = line.slice(i, j);

      let k = j;
      while (k < line.length && /\s/.test(line[k])) k++;
      const isCall = k < line.length && line[k] === "(";

      if (CONTROL_KEYWORDS.has(word)) {
        tokens.push({ type: "control", text: word });
      } else if (GENERAL_KEYWORDS.has(word)) {
        tokens.push({ type: "keyword", text: word });
      } else if (CONSTANTS.has(word)) {
        tokens.push({ type: "constant", text: word });
      } else if (BUILTINS.has(word)) {
        tokens.push({ type: "builtin", text: word });
      } else if (isCall) {
        tokens.push({ type: "method", text: word });
      } else {
        tokens.push({ type: "plain", text: word });
      }

      i = j;
      continue;
    }

    tokens.push({ type: "plain", text: ch });
    i++;
  }

  return tokens;
}

const TOKEN_COLOR_MAP: Record<TokenType, string> = {
  comment: "#6a9955 italic",
  string: "#ce9178",
  keyword: "#569cd6",
  control: "#c586c0",
  builtin: "#4ec9b0",
  method: "#dcdcaa",
  number: "#b5cea8",
  constant: "#569cd6 font-bold",
  plain: "#d4d4d4",
};

export const VSCodeBlock: React.FC<VSCodeBlockProps> = ({
  code,
  language = "javascript",
  filename = "solution.js",
  selectableLines = false,
  selectedLine = null,
  onSelectLine,
}) => {
  const [copied, setCopied] = useState(false);

  const lines = code.trim().split("\n");

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  };

  const isTs = language.toLowerCase() === "typescript" || filename.endsWith(".ts");

  return (
    <div className="bg-white dark:bg-[#1e1e1e] border border-slate-200 dark:border-[#2d2d2d] rounded-xl overflow-hidden shadow-sm dark:shadow-xl mb-4 font-mono text-xs md:text-sm">
      {/* VS Code Window Top Title Bar */}
      <div className="flex items-center justify-between px-3.5 py-2 bg-slate-100 dark:bg-[#252526] border-b border-slate-200 dark:border-[#1f1f1f] select-none">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#ff5f56]" />
            <span className="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]" />
            <span className="w-2.5 h-2.5 rounded-full bg-[#27c93f]" />
          </div>

          <div className="flex items-center gap-1.5 px-3 py-1 bg-white dark:bg-[#1e1e1e] border-t-2 border-t-blue-600 dark:border-t-[#007acc] border-x border-x-slate-200 dark:border-x-[#282828] text-slate-800 dark:text-slate-200 text-xs font-sans rounded-t-sm">
            <span
              className={`text-[10px] font-bold px-1 rounded ${
                isTs ? "bg-[#3178c6] text-white" : "bg-[#f7df1e] text-black"
              }`}
            >
              {isTs ? "TS" : "JS"}
            </span>
            <span className="font-mono text-slate-700 dark:text-slate-300">{filename}</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {selectableLines && (
            <span className="text-xs font-sans px-2.5 py-0.5 rounded bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-500/30">
              {selectedLine ? `Selected: Line ${selectedLine}` : "Click defective line in code"}
            </span>
          )}

          <button
            type="button"
            onClick={handleCopy}
            className="inline-flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white px-2.5 py-1 rounded bg-white dark:bg-[#2d2d2d] hover:bg-slate-50 dark:hover:bg-[#383838] border border-slate-200 dark:border-[#3c3c3c] transition-colors"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                <span className="text-emerald-600 dark:text-emerald-400 font-sans text-xs">Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" />
                <span className="font-sans text-xs">Copy</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Breadcrumbs Bar */}
      <div className="px-4 py-1 bg-slate-50/70 dark:bg-[#1e1e1e] border-b border-slate-200 dark:border-[#2d2d2d] text-xs font-sans text-slate-500 flex items-center gap-1.5 select-none">
        <FileCode2 className="w-3.5 h-3.5 text-slate-400" />
        <span>src</span>
        <span>&rsaquo;</span>
        <span className="text-slate-700 dark:text-slate-300">{filename}</span>
      </div>

      {/* Editor Body */}
      <div className="p-2 overflow-x-auto select-text leading-relaxed">
        <table className="w-full border-collapse">
          <tbody>
            {lines.map((line, idx) => {
              const lineNum = idx + 1;
              const isSelected = selectedLine === lineNum;
              const tokens = tokenizeLine(line);

              return (
                <tr
                  key={lineNum}
                  onClick={() => {
                    if (selectableLines && onSelectLine) {
                      onSelectLine(lineNum);
                    }
                  }}
                  className={`group transition-colors ${
                    selectableLines
                      ? "cursor-pointer hover:bg-slate-100 dark:hover:bg-[#282828]"
                      : ""
                  } ${
                    isSelected
                      ? "bg-blue-50 dark:bg-[#264f78]/60 border-l-2 border-blue-600 dark:border-[#007acc]"
                      : "border-l-2 border-transparent"
                  }`}
                >
                  <td className="w-10 pr-4 text-right select-none text-slate-400 dark:text-[#858585] text-xs font-mono align-top group-hover:text-slate-700 dark:group-hover:text-slate-300">
                    {lineNum}
                  </td>

                  <td className="whitespace-pre font-mono text-xs md:text-sm pl-2">
                    {tokens.map((tok, tIdx) => {
                      const style = TOKEN_COLOR_MAP[tok.type];
                      const [color, ...extras] = style.split(" ");
                      const isItalic = extras.includes("italic");
                      const isBold = extras.includes("font-bold");

                      return (
                        <span
                          key={tIdx}
                          className={`vscode-token-${tok.type}`}
                          style={{
                            color,
                            fontStyle: isItalic ? "italic" : "normal",
                            fontWeight: isBold ? "bold" : "normal",
                          }}
                        >
                          {tok.text}
                        </span>
                      );
                    })}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
