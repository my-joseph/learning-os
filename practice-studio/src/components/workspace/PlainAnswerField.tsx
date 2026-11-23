"use client";

import React from "react";
import { Equal, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/shadcn/Input";
import { cn } from "@/lib/cn";

export const ANSWER_FIELD_CONTAINER_CLASS =
  "relative flex items-center min-h-[2.75rem] rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 transition-colors focus-within:border-indigo-600 dark:focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-600/20 dark:focus-within:ring-indigo-500/25";

export interface InlineCheckButtonProps {
  onClick: () => void;
  disabled: boolean;
  isChecking: boolean;
  embedded?: boolean;
}

/** Shared icon-only `=` check button (embedded inside answer input or standalone for line selection). */
export const InlineCheckButton: React.FC<InlineCheckButtonProps> = ({
  onClick,
  disabled,
  isChecking,
  embedded = true,
}) => {
  const posCls = embedded ? "absolute right-1.5 top-1/2 -translate-y-1/2 " : "";
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label="Check answer"
      title="Check (Enter)"
      className={`${posCls}inline-flex items-center justify-center w-8 h-8 rounded-lg bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-700 disabled:opacity-40 disabled:hover:bg-indigo-600 dark:disabled:hover:bg-indigo-600 text-white transition-colors shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 focus-visible:ring-offset-1`}
    >
      {isChecking ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : (
        <Equal className="w-4 h-4" />
      )}
    </button>
  );
};

export interface PlainAnswerFieldProps {
  inputRef?: React.RefObject<HTMLInputElement>;
  value: string;
  onChange: (val: string) => void;
  onCheck: () => void;
  placeholder: string;
  "aria-label": string;
  isChecking: boolean;
  locked?: boolean;
}

/** Shared plain-text answer input with embedded `=` check button. */
export const PlainAnswerField: React.FC<PlainAnswerFieldProps> = ({
  inputRef,
  value,
  onChange,
  onCheck,
  placeholder,
  "aria-label": ariaLabel,
  isChecking,
  locked = false,
}) => {
  return (
    <div className={ANSWER_FIELD_CONTAINER_CLASS}>
      <Input
        ref={inputRef}
        type="text"
        variant="embedded"
        value={value}
        readOnly={locked}
        aria-readonly={locked || undefined}
        onChange={(e) => {
          if (!locked) onChange(e.target.value);
        }}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            e.preventDefault();
            if (!locked) onCheck();
          }
        }}
        placeholder={placeholder}
        aria-label={ariaLabel}
        className={cn(
          "h-11 font-mono text-sm text-zinc-900 dark:text-zinc-100 pl-3.5 pr-12 py-2 placeholder:font-sans placeholder:text-zinc-400 dark:placeholder:text-zinc-500",
          locked && "opacity-75 cursor-default"
        )}
      />
      <InlineCheckButton
        onClick={onCheck}
        disabled={locked || isChecking || !value.trim()}
        isChecking={isChecking}
      />
    </div>
  );
};
