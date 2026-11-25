"use client";

import React, { useEffect, useMemo, useState } from "react";
import { Check, Copy } from "lucide-react";
import type { ThemedToken } from "shiki/core";
import { CopyButton } from "@/components/ui/CopyButton";
import {
  CodeBlock as CodeBlockRoot,
  CodeBlockActions,
  CodeBlockContent,
  CodeBlockHeader,
  CodeBlockLine,
  CodeBlockTitle,
} from "@/components/ui/shadcn/CodeBlock";
import { cn } from "@/lib/cn";
import { normalizeShikiLanguage } from "@/lib/shikiLanguages";
import { getRegisteredShikiHighlighter } from "@/lib/shikiRegistry";
import { renderShikiLineTokens } from "@/lib/shikiTokens";

type CodeBlockProps = { className?: string; language?: string | null } & (
  | { variant?: "snippet" | "wrapped"; code: string }
  | { variant: "inline-example"; input: string; output: string }
  | {
      variant: "full-file";
      code: string;
      filename: string;
      selectableLines?: boolean;
      selectedLine?: number | null;
      onSelectLine?: (line: number) => void;
    }
);

function useShikiTokens(code: string, language?: string | null): ThemedToken[][] | null {
  const highlighter = getRegisteredShikiHighlighter();
  const normalizedLang = normalizeShikiLanguage(language);
  const syncTokens = useMemo(
    () => highlighter?.highlightTokensSync(code, normalizedLang),
    [highlighter, code, normalizedLang]
  );
  const requestKey = normalizedLang ? `${normalizedLang}:${code}` : null;
  const [asyncResult, setAsyncResult] = useState<{
    key: string;
    tokens: ThemedToken[][];
  } | null>(null);

  useEffect(() => {
    if (!highlighter || !requestKey || syncTokens) return;
    let cancelled = false;
    void highlighter.highlightCode(code, normalizedLang).then((tokens) => {
      if (!cancelled && tokens) setAsyncResult({ key: requestKey, tokens });
    });
    return () => {
      cancelled = true;
    };
  }, [highlighter, code, normalizedLang, requestKey, syncTokens]);

  return syncTokens ?? (requestKey === asyncResult?.key ? asyncResult.tokens : null);
}

function SyntaxCode({ code, language }: { code: string; language?: string | null }) {
  const tokens = useShikiTokens(code, language);
  if (!tokens || tokens.length !== code.split("\n").length) return <>{code}</>;

  return (
    <>
      {tokens.map((lineTokens, index) => (
        <React.Fragment key={index}>
          {index > 0 ? "\n" : null}
          {renderShikiLineTokens(lineTokens)}
        </React.Fragment>
      ))}
    </>
  );
}

function getSelectableLineProps(
  lineNumber: number,
  isSelected: boolean,
  onSelectLine?: (line: number) => void
): React.HTMLAttributes<HTMLSpanElement> {
  return {
    role: "button",
    tabIndex: 0,
    "aria-pressed": isSelected,
    "aria-label": `Select line ${lineNumber}`,
    onClick: () => onSelectLine?.(lineNumber),
    onKeyDown: (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        onSelectLine?.(lineNumber);
      }
    },
  };
}

function FullFileBlock({
  code,
  language = "javascript",
  filename,
  selectableLines,
  selectedLine,
  onSelectLine,
  className,
}: Extract<CodeBlockProps, { variant: "full-file" }>) {
  const displayedCode = code.trim();
  const lines = displayedCode.split("\n");
  const tokens = useShikiTokens(displayedCode, language);
  const highlightedLines = tokens?.length === lines.length ? tokens : null;

  return (
    <CodeBlockRoot variant="full" className={className} data-code-variant="full-file">
      <CodeBlockHeader>
        <CodeBlockTitle title={filename}>{filename}</CodeBlockTitle>
        <CodeBlockActions>
          <CopyButton
            text={code}
            className="min-h-touch gap-space-1_5 px-space-2 text-xs text-muted hover:bg-surface-hover hover:text-foreground sm:min-h-control-sm"
            copiedContent={
              <>
                <Check aria-hidden="true" className="size-space-3_5" />
                <span>Copied</span>
              </>
            }
          >
            <Copy aria-hidden="true" className="size-space-3_5" />
            <span>Copy</span>
          </CopyButton>
        </CodeBlockActions>
      </CodeBlockHeader>

      {selectableLines && (
        <p className="px-space-3_5 pt-space-2 text-xs text-muted" aria-live="polite">
          {selectedLine ? `Selected: Line ${selectedLine}` : "Select the defective line"}
        </p>
      )}

      <CodeBlockContent lineNumbers aria-label={filename}>
        {lines.map((line, index) => {
          const lineNumber = index + 1;
          const isSelected = selectedLine === lineNumber;
          return (
            <CodeBlockLine
              key={lineNumber}
              number={lineNumber}
              variant={isSelected ? "highlighted" : "default"}
              className={selectableLines ? cn(
                "cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-accent",
                !isSelected && "hover:bg-surface-hover"
              ) : undefined}
              {...(selectableLines ? getSelectableLineProps(lineNumber, isSelected, onSelectLine) : {})}
            >
              {highlightedLines && line ? renderShikiLineTokens(highlightedLines[index]) : line}
            </CodeBlockLine>
          );
        })}
      </CodeBlockContent>
    </CodeBlockRoot>
  );
}

export function CodeBlock(props: CodeBlockProps) {
  const { className, language, variant = "snippet" } = props;

  if (props.variant === "full-file") return <FullFileBlock {...props} />;

  if (props.variant === "inline-example") {
    return (
      <CodeBlockRoot className={className} data-code-variant={variant}>
        <CodeBlockContent wrap>
          <span className="block">
            <span className="select-none text-muted">Input: </span>
            <span><SyntaxCode code={props.input} language={language} /></span>
          </span>
          <span className="mt-space-1 block">
            <span className="select-none text-muted">Output: </span>
            <span><SyntaxCode code={props.output} language={language} /></span>
          </span>
        </CodeBlockContent>
      </CodeBlockRoot>
    );
  }

  return (
    <CodeBlockRoot
      className={cn(variant === "snippet" && "my-space-2", className)}
      data-code-variant={variant}
    >
      <CodeBlockContent wrap={variant === "wrapped"}>
        <SyntaxCode code={props.code} language={language} />
      </CodeBlockContent>
    </CodeBlockRoot>
  );
}
