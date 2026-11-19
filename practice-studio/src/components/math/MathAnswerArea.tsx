"use client";

import React, {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from "react";
import dynamic from "next/dynamic";
import { ChoiceOptionGroup } from "@/components/ChoiceOptionGroup";
import {
  ANSWER_FIELD_CONTAINER_CLASS,
  InlineCheckButton,
  PlainAnswerField,
} from "@/components/workspace/PlainAnswerField";
import type { MathLiveInputHandle } from "@/components/math/MathLiveInput";
import { MathPalette } from "@/components/math/MathPalette";
import { ChoiceResultStatus } from "@/lib/answerFeedback";
import {
  getUnitKeyboardProfile,
  isMathLiveSupportedAnswerSpec,
  MathInputMode,
  readMathInputMode,
  writeMathInputMode,
} from "@/lib/mathInput";
import { isTouchPrimaryDevice } from "@/lib/mathPalette";
import { AnswerSpec, ChoiceOption } from "@/types/drill";

const DynamicMathLiveInput = dynamic(
  () => import("@/components/math/MathLiveInput"),
  {
    ssr: false,
    loading: () => (
      <div className="flex-1 min-w-0 h-11 pl-3 pr-12 py-2 flex items-center text-sm text-zinc-400 dark:text-zinc-500">
        Loading math input…
      </div>
    ),
  }
);

export interface MathAnswerAreaHandle {
  focus: () => void;
  select: () => void;
  getPlainText: () => string;
  isPanelOpen: () => boolean;
  closePanel: () => void;
}

export interface MathAnswerAreaProps {
  itemKey: string;
  ariaLabel: string;
  value: string;
  answerSpec: AnswerSpec;
  prompt: string;
  inputHint?: string;
  placeholder: string;
  unitCode?: string;
  drillTitle?: string;
  isChecking: boolean;
  isChoice: boolean;
  hasLineChoice: boolean;
  choiceOptions?: ChoiceOption[];
  choiceLocked: boolean;
  checkingOptionId: string | null;
  choiceResultStatus: ChoiceResultStatus;
  onSelectChoice: (optId: string) => void;
  onChange: (val: string) => void;
  onCheck: (inputOverride?: string) => void;
}

/**
 * Reusable Math answer input area supporting choice options, MathLive + palette + Math/Plain
 * toggle (shared persisted mode), and plain-text input with embedded `=` check button.
 */
export const MathAnswerArea = forwardRef<MathAnswerAreaHandle, MathAnswerAreaProps>(
  function MathAnswerArea(
    {
      itemKey,
      ariaLabel,
      value,
      answerSpec,
      prompt,
      inputHint,
      placeholder,
      unitCode,
      drillTitle,
      isChecking,
      isChoice,
      hasLineChoice,
      choiceOptions,
      choiceLocked,
      checkingOptionId,
      choiceResultStatus,
      onSelectChoice,
      onChange,
      onCheck,
    },
    ref
  ) {
    const [inputMode, setInputMode] = useState<MathInputMode>("math");
    const [panelOpen, setPanelOpen] = useState(false);
    const answerInputRef = useRef<HTMLInputElement | null>(null);
    const mathLiveRef = useRef<MathLiveInputHandle | null>(null);

    useEffect(() => {
      setInputMode(readMathInputMode());
    }, []);

    useEffect(() => {
      if (isTouchPrimaryDevice()) {
        setPanelOpen(false);
      }
    }, [itemKey]);

    const isMathLiveSupported = isMathLiveSupportedAnswerSpec(answerSpec);
    const useMathLive = !isChoice && isMathLiveSupported && inputMode === "math";

    const keyboardProfile = useMemo(
      () =>
        getUnitKeyboardProfile({
          unitCode,
          drillTitle,
          prompt,
          inputHint,
        }),
      [unitCode, drillTitle, prompt, inputHint]
    );

    useImperativeHandle(
      ref,
      () => ({
        focus: () => {
          if (useMathLive) {
            mathLiveRef.current?.focus();
          } else {
            answerInputRef.current?.focus();
          }
        },
        select: () => {
          if (useMathLive) {
            mathLiveRef.current?.focus();
            mathLiveRef.current?.select();
            return;
          }
          answerInputRef.current?.focus();
          answerInputRef.current?.select();
        },
        getPlainText: () =>
          useMathLive ? mathLiveRef.current?.getPlainText() ?? value : value,
        isPanelOpen: () => panelOpen,
        closePanel: () => {
          setPanelOpen(false);
          if (useMathLive) {
            mathLiveRef.current?.focus();
          }
        },
      }),
      [panelOpen, useMathLive, value]
    );

    const handleInputModeChange = (nextMode: MathInputMode) => {
      if (nextMode === inputMode) {
        if (nextMode === "math") {
          mathLiveRef.current?.focus();
        } else {
          answerInputRef.current?.focus();
        }
        return;
      }

      if (nextMode === "plain") {
        const plain = mathLiveRef.current?.getPlainText();
        if (plain !== undefined && plain !== value) {
          onChange(plain);
        }
        setPanelOpen(false);
        setInputMode("plain");
        writeMathInputMode("plain");
        requestAnimationFrame(() => {
          answerInputRef.current?.focus();
        });
      } else {
        setInputMode("math");
        writeMathInputMode("math");
        requestAnimationFrame(() => {
          mathLiveRef.current?.focus();
        });
      }
    };

    const handleMathFieldFocus = useCallback(() => {
      if (isTouchPrimaryDevice()) {
        setPanelOpen(true);
      }
    }, []);

    const handleInsertLatex = useCallback((latex: string) => {
      mathLiveRef.current?.insertLatex(latex);
    }, []);

    return (
      <>
        {isChoice && !hasLineChoice && choiceOptions && (
          <ChoiceOptionGroup
            options={choiceOptions}
            selectedValue={value}
            onSelect={onSelectChoice}
            disabled={choiceLocked}
            checkingOptionId={checkingOptionId}
            resultStatus={choiceResultStatus}
            layout="wrap"
          />
        )}

        {!isChoice && isMathLiveSupported && (
          <div
            onKeyDown={(e) => {
              if (e.key === "Escape" && panelOpen) {
                e.preventDefault();
                setPanelOpen(false);
                mathLiveRef.current?.focus();
              }
            }}
            className="space-y-2"
          >
            {useMathLive ? (
              <div className={ANSWER_FIELD_CONTAINER_CLASS}>
                <DynamicMathLiveInput
                  value={value}
                  placeholder={placeholder}
                  ariaLabel={ariaLabel}
                  variables={answerSpec.variables}
                  disabled={isChecking}
                  fieldRef={mathLiveRef}
                  onChange={onChange}
                  onCheck={(plain) => onCheck(plain)}
                  onFocus={handleMathFieldFocus}
                  onEscape={() => {
                    if (!panelOpen) return false;
                    setPanelOpen(false);
                    return true;
                  }}
                />
                <InlineCheckButton
                  onClick={() => onCheck()}
                  disabled={isChecking || !value.trim()}
                  isChecking={isChecking}
                />
              </div>
            ) : (
              <PlainAnswerField
                inputRef={answerInputRef}
                value={value}
                onChange={onChange}
                onCheck={() => onCheck()}
                placeholder={placeholder}
                aria-label={ariaLabel}
                isChecking={isChecking}
              />
            )}

            <MathPalette
              inputMode={inputMode}
              onModeChange={handleInputModeChange}
              keyboardProfile={keyboardProfile}
              panelOpen={panelOpen}
              onTogglePanel={() => {
                setPanelOpen((prev) => !prev);
                mathLiveRef.current?.focus();
              }}
              onInsertLatex={handleInsertLatex}
              disabled={isChecking}
            />
          </div>
        )}

        {!isChoice && !isMathLiveSupported && (
          <PlainAnswerField
            inputRef={answerInputRef}
            value={value}
            onChange={onChange}
            onCheck={() => onCheck()}
            placeholder={placeholder}
            aria-label={ariaLabel}
            isChecking={isChecking}
          />
        )}
      </>
    );
  }
);
