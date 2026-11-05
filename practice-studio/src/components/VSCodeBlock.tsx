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

// Token types for VS Code Dark+ theme
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
    // Single-line comment
    if (line.slice(i, i + 2) === "//") {
      tokens.push({ type: "comment", text: line.slice(i) });
      break;
    }

    // String literals: ', ", `
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

    // Number literals
    if (/\d/.test(ch) && (i === 0 || !/[a-zA-Z0-9_$]/.test(line[i - 1]))) {
      let j = i;
      while (j < line.length && /[\d.]/.test(line[j])) {
        j++;
      }
      tokens.push({ type: "number", text: line.slice(i, j) });
      i = j;
      continue;
    }

    // Word tokens: keywords, identifiers, functions
    if (/[a-zA-Z_$]/.test(ch)) {
      let j = i;
      while (j < line.length && /[a-zA-Z0-9_$]/.test(line[j])) {
        j++;
      }
      const word = line.slice(i, j);

      // Check if immediately followed by '(' -> function/method invocation
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

    // Punctuation and whitespace
    tokens.push({ type: "plain", text: ch });
    i++;
  }

  return tokens;
}

const TOKEN_COLOR_MAP: Record<TokenType, string> = {
  comment: "#6a9955 italic", // VS Code Green italic
  string: "#ce9178", // VS Code Orange / Salmon
  keyword: "#569cd6", // VS Code Blue
  control: "#c586c0", // VS Code Magenta / Purple
  builtin: "#4ec9b0", // VS Code Teal / Cyan
  method: "#dcdcaa", // VS Code Yellow
  number: "#b5cea8", // VS Code Light Green
  constant: "#569cd6 font-bold", // VS Code Blue bold
  plain: "#d4d4d4", // VS Code Off-white
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
    <div className="bg-[#1e1e1e] border border-[#2d2d2d] rounded-xl overflow-hidden shadow-2xl mb-4 font-mono text-xs md:text-sm">
      {/* VS Code Window Top Title Bar */}
      <div className="flex items-center justify-between px-3.5 py-2 bg-[#252526] border-b border-[#1f1f1f] select-none">
        {/* Mac Window Dots + Active Tab */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#ff5f56]" />
            <span className="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]" />
            <span className="w-2.5 h-2.5 rounded-full bg-[#27c93f]" />
          </div>

          <div className="flex items-center gap-1.5 px-3 py-1 bg-[#1e1e1e] border-t border-t-[#007acc] border-x border-x-[#282828] text-slate-200 text-xs font-sans rounded-t-sm">
            <span
              className={`text-[10px] font-bold px-1 rounded ${
                isTs ? "bg-[#3178c6] text-white" : "bg-[#f7df1e] text-black"
              }`}
            >
              {isTs ? "TS" : "JS"}
            </span>
            <span className="font-mono text-slate-300">{filename}</span>
          </div>
        </div>

        {/* Right Action Icons: Copy & Language */}
        <div className="flex items-center gap-2">
          {selectableLines && (
            <span className="text-[11px] font-sans px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/30">
              Click any line to select
            </span>
          )}

          <button
            type="button"
            onClick={handleCopy}
            className="vscode-copy-btn inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white px-2.5 py-1 rounded bg-[#2d2d2d] hover:bg-[#383838] border border-[#3c3c3c] transition-colors"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-400 font-sans text-[11px]">Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" />
                <span className="font-sans text-[11px]">Copy</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Breadcrumbs Bar */}
      <div className="px-4 py-1 bg-[#1e1e1e] border-b border-[#2d2d2d] text-[11px] font-sans text-slate-500 flex items-center gap-1.5 select-none">
        <FileCode2 className="w-3 h-3 text-slate-400" />
        <span>src</span>
        <span>&rsaquo;</span>
        <span className="text-slate-300">{filename}</span>
        {selectableLines && selectedLine && (
          <>
            <span>&rsaquo;</span>
            <span className="text-sky-400 font-mono font-semibold">
              Selected: Line {selectedLine}
            </span>
          </>
        )}
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
                      ? "cursor-pointer hover:bg-[#282828]"
                      : ""
                  } ${
                    isSelected
                      ? "bg-[#264f78]/60 border-l-2 border-[#007acc]"
                      : "border-l-2 border-transparent"
                  }`}
                >
                  {/* Line Number Gutter */}
                  <td className="w-10 pr-4 text-right select-none text-[#858585] text-xs font-mono align-top group-hover:text-slate-300">
                    {lineNum}
                  </td>

                  {/* Code Line Content */}
                  <td className="whitespace-pre font-mono text-xs md:text-sm pl-2">
                    {tokens.map((tok, tIdx) => {
                      const style = TOKEN_COLOR_MAP[tok.type];
                      const [color, ...extras] = style.split(" ");
                      const isItalic = extras.includes("italic");
                      const isBold = extras.includes("font-bold");

                      return (
                        <span
                          key={tIdx}
                          className={`tok-${tok.type}`}
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
