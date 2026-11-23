"use client";

import React, { useMemo } from "react";
import { Copy, Check, FileCode2 } from "lucide-react";
import { CopyButton } from "@/components/ui/CopyButton";
import { Badge } from "@/components/ui/shadcn/Badge";
import { renderShikiLineTokens, useShikiTokens } from "@/components/HighlightedCode";
import {
  inferShikiLanguageFromFilename,
  normalizeShikiLanguage,
} from "@/lib/shiki";

export interface VSCodeBlockProps {
  code: string;
  language?: string;
  filename?: string;
  selectableLines?: boolean;
  selectedLine?: number | null;
  onSelectLine?: (line: number) => void;
}

interface LanguageBadge {
  label: string;
  className: string;
}

function getLanguageBadge(language: string, filename: string): LanguageBadge {
  const normalized = normalizeShikiLanguage(language);
  const resolved =
    normalized ??
    (language.trim().toLowerCase() === "javascript" || !language.trim()
      ? inferShikiLanguageFromFilename(filename)
      : null);

  switch (resolved) {
    case "typescript":
      return { label: "TS", className: "bg-[#3178c6] text-white" };
    case "tsx":
      return { label: "TSX", className: "bg-[#3178c6] text-white" };
    case "jsx":
      return { label: "JSX", className: "bg-[#f7df1e] text-black" };
    case "python":
      return { label: "PY", className: "bg-[#3776ab] text-white" };
    case "sql":
      return { label: "SQL", className: "bg-indigo-600 text-white" };
    case "bash":
      return { label: "SH", className: "bg-zinc-700 text-white" };
    case "json":
      return {
        label: "JSON",
        className: "bg-zinc-200 dark:bg-zinc-700 text-zinc-800 dark:text-zinc-200",
      };
    case "javascript":
      if (filename.toLowerCase().endsWith(".ts")) {
        return { label: "TS", className: "bg-[#3178c6] text-white" };
      }
      return { label: "JS", className: "bg-[#f7df1e] text-black" };
    default:
      return {
        label: "TXT",
        className: "bg-zinc-200 dark:bg-zinc-700 text-zinc-700 dark:text-zinc-200",
      };
  }
}

export function getSelectableLineRowProps(
  lineNum: number,
  selectableLines: boolean,
  isSelected: boolean,
  onSelectLine?: (line: number) => void
): React.HTMLAttributes<HTMLTableRowElement> {
  if (!selectableLines) {
    return {};
  }
  return {
    role: "button",
    tabIndex: 0,
    "aria-pressed": isSelected,
    "aria-label": `Select line ${lineNum}`,
    onClick: () => {
      onSelectLine?.(lineNum);
    },
    onKeyDown: (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        onSelectLine?.(lineNum);
      }
    },
  };
}

export const VSCodeBlock: React.FC<VSCodeBlockProps> = ({
  code,
  language = "javascript",
  filename = "solution.js",
  selectableLines = false,
  selectedLine = null,
  onSelectLine,
}) => {
  const trimmedCode = useMemo(() => code.trim(), [code]);
  const lines = useMemo(() => trimmedCode.split("\n"), [trimmedCode]);
  const highlightedLines = useShikiTokens(trimmedCode, language);
  const hasHighlightedTokens =
    Boolean(highlightedLines) && highlightedLines?.length === lines.length;

  const badge = getLanguageBadge(language, filename);

  return (
    <div className="bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl overflow-hidden shadow-sm mb-4 font-mono text-xs md:text-sm">
      {/* VS Code Window Top Title Bar */}
      <div className="flex items-center justify-between gap-2 px-3.5 py-2 bg-zinc-50 dark:bg-zinc-900 border-b border-zinc-200 dark:border-zinc-800 select-none">
        <div className="flex items-center gap-2.5 min-w-0 flex-1">
          <div className="flex items-center gap-1.5 shrink-0" aria-hidden="true">
            <span className="w-2.5 h-2.5 rounded-full bg-[#ff5f56]" />
            <span className="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]" />
            <span className="w-2.5 h-2.5 rounded-full bg-[#27c93f]" />
          </div>

          <div className="flex items-center gap-1.5 min-w-0 px-2.5 sm:px-3 py-1 bg-white dark:bg-zinc-950 border-t-2 border-t-indigo-600 dark:border-t-indigo-500 border-x border-x-zinc-200 dark:border-x-zinc-800 text-zinc-800 dark:text-zinc-200 text-xs font-sans rounded-t-sm">
            <Badge variant="status" className={`text-[10px] font-bold p-0 rounded shrink-0 ${badge.className}`}>
              {badge.label}
            </Badge>
            <span className="font-mono text-zinc-700 dark:text-zinc-300 truncate">
              {filename}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {selectableLines && (
            <Badge variant="status" className="text-xs font-sans px-2.5 py-0.5 rounded bg-zinc-50 dark:bg-zinc-900 text-zinc-600 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700">
              {selectedLine ? `Selected: Line ${selectedLine}` : "Click defective line in code"}
            </Badge>
          )}

          <CopyButton
            text={code}
            className="inline-flex items-center gap-1.5 text-xs text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white px-2.5 py-1 rounded bg-white dark:bg-zinc-800 hover:bg-zinc-100 dark:hover:bg-zinc-700 border border-zinc-200 dark:border-zinc-700 transition-colors"
            copiedContent={
              <>
                <Check className="w-3.5 h-3.5" />
                <span className="font-sans text-xs">Copied</span>
              </>
            }
          >
            <>
              <Copy className="w-3.5 h-3.5" />
              <span className="font-sans text-xs">Copy</span>
            </>
          </CopyButton>
        </div>
      </div>

      {/* Breadcrumbs Bar */}
      <div className="px-4 py-1 bg-zinc-50/70 dark:bg-zinc-950 border-b border-zinc-200 dark:border-zinc-800 text-xs font-sans text-zinc-500 dark:text-zinc-400 flex items-center gap-1.5 select-none">
        <FileCode2 className="w-3.5 h-3.5 text-zinc-400 dark:text-zinc-500" />
        <span>src</span>
        <span>&rsaquo;</span>
        <span className="text-zinc-700 dark:text-zinc-300">{filename}</span>
      </div>

      {/* Editor Body */}
      <div className="p-2 overflow-x-auto select-text leading-relaxed">
        <table className="w-full border-collapse">
          <tbody>
            {lines.map((line, idx) => {
              const lineNum = idx + 1;
              const isSelected = selectedLine === lineNum;
              const lineTokens = hasHighlightedTokens ? highlightedLines?.[idx] : undefined;

              return (
                <tr
                  key={lineNum}
                  {...getSelectableLineRowProps(
                    lineNum,
                    selectableLines,
                    isSelected,
                    onSelectLine
                  )}
                  className={`group transition-colors ${
                    selectableLines
                      ? "cursor-pointer hover:bg-zinc-100 dark:hover:bg-zinc-900 focus:outline-none focus-visible:bg-zinc-100 dark:focus-visible:bg-zinc-900"
                      : ""
                  } ${
                    isSelected
                      ? "bg-indigo-50 dark:bg-indigo-950/50 border-l-2 border-indigo-600 dark:border-indigo-500"
                      : "border-l-2 border-transparent"
                  }`}
                >
                  <td className="w-10 pr-4 text-right select-none text-zinc-400 dark:text-zinc-500 text-xs font-mono align-top group-hover:text-zinc-700 dark:group-hover:text-zinc-300">
                    {lineNum}
                  </td>

                  <td className="whitespace-pre font-mono text-xs md:text-sm pl-2 text-[#24292e] dark:text-[#e1e4e8]">
                    {lineTokens ? renderShikiLineTokens(lineTokens) : line}
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
