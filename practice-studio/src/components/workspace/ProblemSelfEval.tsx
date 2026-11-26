"use client";

import React from "react";
import { PenLine, RotateCcw } from "lucide-react";
import { FormattedText } from "@/components/FormattedText";
import { Button } from "@/components/ui/shadcn/Button";
import { Input } from "@/components/ui/shadcn/Input";
import { statusTone } from "@/lib/statusTone";
import { MistakeTag } from "@/types/drill";

export interface ProblemSelfEvalProps {
  hasAttempt: boolean;
  showSelfScore?: boolean;
  disabled?: boolean;
  /** Maximum score allowed by Rule 3 (self-score may only lower auto-computed scores). */
  maxScore?: 1 | 0.5 | 0 | null;
  /** True when the problem is skipped (self-score cannot raise or clear skipped). */
  skipped?: boolean;
  score: number | null;
  mistakes: string[];
  mistakeNote?: string;
  mistakeTags: MistakeTag[];
  noteAriaLabel: string;
  onSetScore: (score: number | null) => void;
  onToggleMistakeTag: (tagId: string) => void;
  onMistakeNoteChange: (note: string) => void;
  revisitNote?: string;
  onRevisitNoteChange?: (note: string) => void;
}

const SELF_SCORE_BUTTONS = [
  {
    val: 1,
    label: "1.0",
    activeCls: statusTone.correct.selfScoreActive,
  },
  {
    val: 0.5,
    label: "0.5",
    activeCls: statusTone.assisted.selfScoreActive,
  },
  {
    val: 0,
    label: "0",
    activeCls: statusTone.wrong.selfScoreActive,
  },
] as const;

/** Shared self-score buttons, mistake tag chips, and mistake note input shown after an attempt. */
export const ProblemSelfEval: React.FC<ProblemSelfEvalProps> = ({
  hasAttempt,
  showSelfScore = true,
  disabled = false,
  maxScore,
  skipped = false,
  score,
  mistakes,
  mistakeNote,
  mistakeTags,
  noteAriaLabel,
  onSetScore,
  onToggleMistakeTag,
  onMistakeNoteChange,
  revisitNote,
  onRevisitNoteChange,
}) => {
  if (!hasAttempt) {
    return null;
  }

  return (
    <div className="pt-space-4 border-t border-border space-y-space-3 text-xs text-muted">
      <div className="flex flex-wrap items-center justify-between gap-space-3">
        {showSelfScore && (
          <div className="flex items-center gap-space-1_5">
            <span className="mr-space-1">Self-score:</span>
            {SELF_SCORE_BUTTONS.map((btn) => {
              const exceedsCap =
                skipped ||
                (maxScore !== undefined && (maxScore === null || btn.val > maxScore));
              const btnDisabled = disabled || exceedsCap;
              return (
                <Button
                  key={btn.val}
                  type="button"
                  disabled={btnDisabled}
                  onClick={() => onSetScore(btn.val)}
                  aria-pressed={score === btn.val}
                  variant="assistScore"
                  size="assistScore"
                  className={score === btn.val ? btn.activeCls : undefined}
                >
                  {btn.label}
                </Button>
              );
            })}
          </div>
        )}

        {mistakeTags.length > 0 && (
          <div className="flex flex-wrap items-center gap-space-1_5">
            <span className="mr-space-1">Mistake:</span>
            {mistakeTags.map((t) => {
              const hasTag = mistakes.includes(t.id);
              return (
                <Button
                  key={t.id}
                  type="button"
                  disabled={disabled}
                  onClick={() => onToggleMistakeTag(t.id)}
                  aria-pressed={hasTag}
                  variant="assistTag"
                  size="assistTag"
                  className={hasTag ? statusTone.wrong.selfScoreActive : undefined}
                >
                  <FormattedText text={t.label} />
                </Button>
              );
            })}
          </div>
        )}
      </div>

      <NoteField
        icon={PenLine}
        label={noteAriaLabel}
        placeholder="Note what went wrong (optional)…"
        value={mistakeNote}
        disabled={disabled}
        onChange={onMistakeNoteChange}
      />
      {onRevisitNoteChange && (
        <NoteField
          icon={RotateCcw}
          label="Revisit note"
          placeholder="Next time I will…"
          value={revisitNote}
          disabled={disabled}
          onChange={onRevisitNoteChange}
        />
      )}
    </div>
  );
};

function NoteField({
  icon: Icon,
  label,
  placeholder,
  value,
  disabled,
  onChange,
}: {
  icon: typeof PenLine;
  label: string;
  placeholder: string;
  value?: string;
  disabled: boolean;
  onChange: (note: string) => void;
}) {
  return (
    <div className="flex items-center gap-space-2 bg-surface-panel dark:bg-surface-raised border border-border rounded-xl px-space-3 py-space-2 transition-colors focus-within:border-accent focus-within:ring-2 focus-within:ring-accent/20 dark:focus-within:ring-accent/25">
      <Icon aria-hidden="true" className="size-space-3_5 text-muted shrink-0" />
      <Input
        type="text"
        variant="embedded"
        disabled={disabled}
        value={value || ""}
        onChange={(event) => onChange(event.target.value)}
        aria-label={label}
        placeholder={placeholder}
        className="text-xs"
      />
    </div>
  );
}
