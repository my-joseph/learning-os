"use client";

import React, {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from "react";
import type { MathfieldElement } from "mathlive";
import { normalizeMathLiveAsciiMath, plainTextToLatex } from "@/lib/mathInput";
import { insertLatexIntoMathField } from "@/lib/mathPalette";
import "mathlive/static.css";
import "./mathlive-studio.css";

export interface MathLiveInputHandle {
  focus: () => void;
  select: () => void;
  getPlainText: () => string;
  insertLatex: (latex: string) => void;
}

export interface MathLiveInputProps {
  value: string;
  placeholder?: string;
  ariaLabel: string;
  variables?: readonly string[];
  disabled?: boolean;
  fieldRef?: React.MutableRefObject<MathLiveInputHandle | null>;
  onChange: (plainText: string) => void;
  onCheck: (plainText: string) => void;
  onFocus?: () => void;
  onEscape?: () => boolean;
}

function readFieldPlainText(
  mf: MathfieldElement | null,
  variables?: readonly string[]
): string {
  if (!mf) return "";
  try {
    const ascii = mf.getValue("ascii-math");
    return normalizeMathLiveAsciiMath(ascii, mf.value, variables);
  } catch {
    return (mf.value || "").trim();
  }
}

export const MathLiveInput = forwardRef<MathLiveInputHandle, MathLiveInputProps>(
  function MathLiveInput(
    {
      value,
      placeholder,
      ariaLabel,
      variables,
      disabled = false,
      fieldRef,
      onChange,
      onCheck,
      onFocus,
      onEscape,
    },
    ref
  ) {
    const mfRef = useRef<MathfieldElement | null>(null);
    const convertToLatexRef = useRef<((ascii: string) => string) | null>(null);
    const lastEmittedPlainRef = useRef<string>(value);
    const variablesRef = useRef(variables);
    variablesRef.current = variables;
    const onChangeRef = useRef(onChange);
    onChangeRef.current = onChange;
    const onCheckRef = useRef(onCheck);
    onCheckRef.current = onCheck;
    const onFocusRef = useRef(onFocus);
    onFocusRef.current = onFocus;
    const onEscapeRef = useRef(onEscape);
    onEscapeRef.current = onEscape;
    const disabledRef = useRef(disabled);
    disabledRef.current = disabled;

    const [ready, setReady] = useState(false);
    const [isEmpty, setIsEmpty] = useState(() => !value.trim());

    const handleObj = useMemo<MathLiveInputHandle>(
      () => ({
        focus: () => {
          mfRef.current?.focus();
        },
        select: () => {
          const mf = mfRef.current;
          if (!mf) return;
          mf.focus();
          try {
            mf.executeCommand("selectAll");
          } catch {
            // ignore if not mounted yet
          }
        },
        getPlainText: () => {
          if (!mfRef.current || !ready) return value;
          return readFieldPlainText(mfRef.current, variablesRef.current);
        },
        insertLatex: (latex: string) => {
          const mf = mfRef.current;
          if (!mf || !ready || disabledRef.current) return;
          insertLatexIntoMathField(mf, latex);
          setIsEmpty(!(mf.value || "").trim());
          const plain = readFieldPlainText(mf, variablesRef.current);
          if (plain !== lastEmittedPlainRef.current) {
            lastEmittedPlainRef.current = plain;
            onChangeRef.current(plain);
          }
        },
      }),
      [ready, value]
    );

    if (fieldRef) {
      fieldRef.current = handleObj;
    }

    useImperativeHandle(ref, () => handleObj, [handleObj]);

    useEffect(() => {
      let cancelled = false;
      let cleanup: (() => void) | undefined;

      (async () => {
        const ml = await import("mathlive");
        if (cancelled) return;
        const mf = mfRef.current;
        if (!mf) return;

        ml.MathfieldElement.fontsDirectory = null;
        ml.MathfieldElement.soundsDirectory = null;
        document.documentElement.style.setProperty("--ML__static-fonts", "true");
        convertToLatexRef.current = ml.convertAsciiMathToLatex;

        mf.smartFence = false;
        mf.smartSuperscript = true;
        mf.popoverPolicy = "off";
        // Turn off MathLive's floating virtual keyboard everywhere; Studio uses its own inline palette.
        mf.mathVirtualKeyboardPolicy = "manual";
        if (window.mathVirtualKeyboard?.visible) {
          window.mathVirtualKeyboard.hide({ animate: false });
        }
        mf.readOnly = disabledRef.current;
        mf.inlineShortcuts = {
          ...mf.inlineShortcuts,
          inf: {
            after: "nothing+digit+frac+surd+binop+relop+punct+array+openfence+closefence+space",
            value: "\\infty",
          },
          abs: "\\left|#?\\right|",
          cup: {
            after: "space+closefence",
            value: "\\cup",
          },
        };

        const initialLatex = plainTextToLatex(value, ml.convertAsciiMathToLatex);
        mf.value = initialLatex;
        lastEmittedPlainRef.current = value;
        setIsEmpty(!initialLatex.trim());

        const syncAndCheck = () => {
          const plain = readFieldPlainText(mf, variablesRef.current);
          if (plain !== lastEmittedPlainRef.current) {
            lastEmittedPlainRef.current = plain;
            onChangeRef.current(plain);
          }
          if (plain.trim() && !disabledRef.current) {
            onCheckRef.current(plain);
          }
        };

        const handleInput = () => {
          const plain = readFieldPlainText(mf, variablesRef.current);
          setIsEmpty(!(mf.value || "").trim());
          lastEmittedPlainRef.current = plain;
          onChangeRef.current(plain);
        };

        const handleKeyDown = (e: KeyboardEvent) => {
          if ((e.key === "Enter" || e.code === "NumpadEnter") && !e.shiftKey) {
            e.preventDefault();
            e.stopPropagation();
            syncAndCheck();
            return;
          }
          if (e.key === "Escape" && onEscapeRef.current?.()) {
            e.preventDefault();
            e.stopPropagation();
          }
        };

        const handleBeforeInput = (e: InputEvent) => {
          if (e.inputType === "insertLineBreak") {
            e.preventDefault();
            syncAndCheck();
          }
        };

        const handleFocus = () => {
          onFocusRef.current?.();
        };

        mf.addEventListener("input", handleInput);
        mf.addEventListener("keydown", handleKeyDown);
        mf.addEventListener("beforeinput", handleBeforeInput as EventListener);
        mf.addEventListener("focus", handleFocus);

        setReady(true);

        cleanup = () => {
          mf.removeEventListener("input", handleInput);
          mf.removeEventListener("keydown", handleKeyDown);
          mf.removeEventListener("beforeinput", handleBeforeInput as EventListener);
          mf.removeEventListener("focus", handleFocus);
          if (window.mathVirtualKeyboard?.visible) {
            window.mathVirtualKeyboard.hide({ animate: false });
          }
        };
      })();

      return () => {
        cancelled = true;
        if (fieldRef) fieldRef.current = null;
        cleanup?.();
      };
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Sync disabled/readOnly state
    useEffect(() => {
      if (!ready || !mfRef.current) return;
      mfRef.current.readOnly = disabled;
    }, [ready, disabled]);

    // Sync external value changes (e.g. Reset button or external state load) without fighting live LaTeX typing
    useEffect(() => {
      if (!ready || !mfRef.current || !convertToLatexRef.current) return;
      if (value === lastEmittedPlainRef.current) return;
      const nextLatex = plainTextToLatex(value, convertToLatexRef.current);
      mfRef.current.value = nextLatex;
      lastEmittedPlainRef.current = value;
      setIsEmpty(!nextLatex.trim());
    }, [ready, value]);

    return (
      <div className="relative flex items-center flex-1 min-w-0 min-h-[2.75rem] px-1.5 py-0.5">
        {!ready && (
          <div
            aria-hidden="true"
            className="w-full px-1 font-mono text-sm text-zinc-400 dark:text-zinc-500 truncate"
          >
            {value || placeholder || "Enter your answer…"}
          </div>
        )}
        {isEmpty && ready && placeholder && (
          <span
            aria-hidden="true"
            className="pointer-events-none absolute left-2.5 right-2 text-sm text-zinc-400 dark:text-zinc-500 truncate select-none"
          >
            {placeholder}
          </span>
        )}
        {React.createElement("math-field", {
          ref: mfRef,
          "aria-label": ariaLabel,
          "math-virtual-keyboard-policy": "manual",
          class: `studio-math-field flex-1 min-w-0 ${ready ? "" : "sr-only"}`,
        })}
      </div>
    );
  }
);

export default MathLiveInput;
