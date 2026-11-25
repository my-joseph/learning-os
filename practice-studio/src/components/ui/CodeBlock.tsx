"use client";

import React, { useEffect, useId, useMemo, useState, useSyncExternalStore } from "react";
import { Check, Copy, WrapText } from "lucide-react";
import type { ThemedToken } from "shiki/core";
import { CopyButton } from "@/components/ui/CopyButton";
import {
  CodeBlock as CodeBlockRoot,
  CodeBlockActions,
  CodeBlockContent,
  CodeBlockFooter,
  CodeBlockHeader,
  CodeBlockLine,
  CodeBlockTitle,
} from "@/components/ui/shadcn/CodeBlock";
import { IconButton } from "@/components/ui/shadcn/Button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/shadcn/Tooltip";
import { cn } from "@/lib/cn";
import { normalizeShikiLanguage } from "@/lib/shikiLanguages";
import { getRegisteredShikiHighlighter } from "@/lib/shikiRegistry";
import { renderShikiLineTokens } from "@/lib/shikiTokens";
import { statusTone } from "@/lib/statusTone";

type CodeBlockProps = { className?: string; language?: string | null } & (
  | { variant?: "snippet" | "wrapped"; code: string }
  | { variant: "inline-example"; input: string; output: string }
  | {
      variant: "terminal";
      code: string;
      title?: string;
      exitCode?: number;
      status?: { label: string; passed: boolean };
      /** Pre-styled terminal lines; `code` stays the plain text that Copy copies. */
      children?: React.ReactNode;
    }
  | {
      variant: "full-file";
      code: string;
      filename: string;
      highlightedLines?: ReadonlyArray<readonly [first: number, last: number]>;
      preserveWhitespace?: boolean;
      selectableLines?: boolean;
      selectedLine?: number | null;
      onSelectLine?: (line: number) => void;
    }
);

const WRAP_STORAGE_KEY = "practice_studio_code_wrap";
const WRAP_CHANGE_EVENT = "practice-studio:code-wrap";
let unsavedWrap: boolean | null = null;

function readWrapPreference(): boolean | null {
  if (unsavedWrap !== null) return unsavedWrap;
  try {
    const stored = window.localStorage.getItem(WRAP_STORAGE_KEY);
    return stored === "true" ? true : stored === "false" ? false : null;
  } catch {
    return null;
  }
}

function subscribeToWrapPreference(onChange: () => void) {
  window.addEventListener(WRAP_CHANGE_EVENT, onChange);
  window.addEventListener("storage", onChange);
  return () => {
    window.removeEventListener(WRAP_CHANGE_EVENT, onChange);
    window.removeEventListener("storage", onChange);
  };
}

function writeWrapPreference(wrap: boolean) {
  try {
    window.localStorage.setItem(WRAP_STORAGE_KEY, String(wrap));
    unsavedWrap = null;
  } catch {
    unsavedWrap = wrap;
  }
  window.dispatchEvent(new window.Event(WRAP_CHANGE_EVENT));
}

function useWrapPreference(defaultWrap = false) {
  return useSyncExternalStore(subscribeToWrapPreference, readWrapPreference, () => null) ?? defaultWrap;
}

function CodeHeader({
  title,
  code,
  wrap,
  contentId,
}: {
  title: string;
  code: string;
  wrap: boolean;
  contentId: string;
}) {
  const wrapLabel = wrap ? "Unwrap" : "Wrap lines";
  return (
    <CodeBlockHeader>
      <CodeBlockTitle title={title}>{title}</CodeBlockTitle>
      <CodeBlockActions>
        <Tooltip>
          <TooltipTrigger asChild>
            <IconButton
              size="sm"
              tone="secondary"
              hitArea="padded"
              selected={wrap}
              aria-label={wrapLabel}
              aria-pressed={wrap}
              aria-controls={contentId}
              onClick={() => writeWrapPreference(!wrap)}
            >
              <WrapText aria-hidden="true" className="size-space-3_5" />
            </IconButton>
          </TooltipTrigger>
          <TooltipContent>{wrapLabel}</TooltipContent>
        </Tooltip>
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
  );
}

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
  highlightedLines,
  preserveWhitespace,
  selectableLines,
  selectedLine,
  onSelectLine,
  className,
}: Extract<CodeBlockProps, { variant: "full-file" }>) {
  const wrap = useWrapPreference();
  const contentId = useId();
  const displayedCode = preserveWhitespace ? code : code.trim();
  const lines = displayedCode.split("\n");
  const tokens = useShikiTokens(displayedCode, language);
  const lineTokens = tokens?.length === lines.length ? tokens : null;

  return (
    <CodeBlockRoot variant="full" className={className} data-code-variant="full-file">
      <CodeHeader title={filename} code={code} wrap={wrap} contentId={contentId} />

      {selectableLines && (
        <p className="px-space-3_5 pt-space-2 text-xs text-muted" aria-live="polite">
          {selectedLine ? `Selected: Line ${selectedLine}` : "Select the defective line"}
        </p>
      )}

      <CodeBlockContent id={contentId} lineNumbers wrap={wrap} aria-label={filename}>
        {lines.map((line, index) => {
          const lineNumber = index + 1;
          const isSelected = selectedLine === lineNumber;
          const isHighlighted = isSelected || highlightedLines?.some(
            ([first, last]) => first <= lineNumber && lineNumber <= last
          );
          return (
            <CodeBlockLine
              key={lineNumber}
              number={lineNumber}
              variant={isHighlighted ? "highlighted" : "default"}
              className={selectableLines ? cn(
                "cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-accent",
                !isSelected && "hover:bg-surface-hover"
              ) : undefined}
              {...(selectableLines ? getSelectableLineProps(lineNumber, isSelected, onSelectLine) : {})}
            >
              {lineTokens && line ? renderShikiLineTokens(lineTokens[index]) : line}
            </CodeBlockLine>
          );
        })}
      </CodeBlockContent>
    </CodeBlockRoot>
  );
}

function TerminalBlock({
  className,
  code,
  title = "Terminal",
  exitCode,
  status,
  children,
}: Extract<CodeBlockProps, { variant: "terminal" }>) {
  const wrap = useWrapPreference(true);
  const contentId = useId();
  const footer = status ?? (exitCode === undefined
    ? undefined
    : { label: `Exit code ${exitCode}`, passed: exitCode === 0 });

  return (
    <CodeBlockRoot variant="terminal" className={className} data-code-variant="terminal">
      <CodeHeader title={title} code={code} wrap={wrap} contentId={contentId} />
      <CodeBlockContent id={contentId} wrap={wrap} aria-label={title}>
        {children ?? code.split("\n").map((line, index) => (
          <React.Fragment key={index}>
            {index > 0 && "\n"}
            {line.startsWith("$ ") ? (
              <><span className="text-muted">$ </span>{line.slice(2)}</>
            ) : line}
          </React.Fragment>
        ))}
      </CodeBlockContent>
      {footer && (
        <CodeBlockFooter className={footer.passed ? statusTone.correct.text : statusTone.wrong.text}>
          {footer.label}
        </CodeBlockFooter>
      )}
    </CodeBlockRoot>
  );
}

export function CodeBlock(props: CodeBlockProps) {
  const { className, language, variant = "snippet" } = props;

  if (props.variant === "full-file") return <FullFileBlock {...props} />;
  if (props.variant === "terminal") return <TerminalBlock {...props} />;

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
