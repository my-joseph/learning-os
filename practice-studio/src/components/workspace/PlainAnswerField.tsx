"use client";

import React from "react";
import { Equal, Loader2 } from "lucide-react";
import { IconButton } from "@/components/ui/shadcn/Button";
import { Input } from "@/components/ui/shadcn/Input";

export const ANSWER_FIELD_CONTAINER_CLASS =
  "relative flex items-center min-h-control-answer sm:min-h-touch rounded-xl border border-border-control bg-surface-raised transition-colors focus-within:border-accent-field focus-within:ring-2 focus-within:ring-accent-field/20 dark:focus-within:ring-accent-field/25";

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
  return (
    <IconButton
      tone="answerCheck"
      hitArea="answer"
      size="sm"
      loading={isChecking}
      onClick={onClick}
      disabled={disabled}
      aria-label="Check answer"
      title="Check (Enter)"
      className={embedded ? "absolute right-0 sm:right-space-1_5 top-1/2 -translate-y-1/2" : undefined}
    >
      {isChecking ? (
        <Loader2 className="size-space-4 animate-spin" aria-hidden="true" />
      ) : (
        <Equal className="size-space-4" aria-hidden="true" />
      )}
    </IconButton>
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
        variant="answer"
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
        className={locked ? "opacity-muted cursor-default" : undefined}
      />
      <InlineCheckButton
        onClick={onCheck}
        disabled={locked || isChecking || !value.trim()}
        isChecking={isChecking}
      />
    </div>
  );
};
