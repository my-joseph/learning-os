"use client";

import React, {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from "react";
import { Keyboard } from "lucide-react";
import type {
  MathfieldElement,
  VirtualKeyboardInterface,
  VirtualKeyboardKeycap,
  VirtualKeyboardLayout,
} from "mathlive";
import {
  normalizeMathLiveAsciiMath,
  plainTextToLatex,
  UnitKeyboardProfile,
} from "@/lib/mathInput";
import "./mathlive-studio.css";

export interface MathLiveInputHandle {
  focus: () => void;
  select: () => void;
  getPlainText: () => string;
}

export interface MathLiveInputProps {
  value: string;
  placeholder?: string;
  ariaLabel: string;
  variables?: readonly string[];
  keyboardProfile: UnitKeyboardProfile;
  disabled?: boolean;
  fieldRef?: React.MutableRefObject<MathLiveInputHandle | null>;
  onChange: (plainText: string) => void;
  onCheck: (plainText: string) => void;
}

function buildCompactKeyboardLayout(
  profile: UnitKeyboardProfile
): VirtualKeyboardLayout {
  const rows: Array<Array<string | Partial<VirtualKeyboardKeycap>>> = [];

  if (profile.trig || profile.log) {
    const topicRow: Array<string | Partial<VirtualKeyboardKeycap>> = [];
    if (profile.trig) {
      topicRow.push(
        { latex: "\\sin", insert: "\\sin(#0)", class: "small" },
        { latex: "\\cos", insert: "\\cos(#0)", class: "small" },
        { latex: "\\tan", insert: "\\tan(#0)", class: "small" },
        { latex: "\\theta" }
      );
    }
    if (profile.log) {
      topicRow.push(
        { latex: "\\ln", insert: "\\ln(#0)", class: "small" },
        { latex: "\\log", insert: "\\log(#0)", class: "small" },
        { latex: "\\log_{#?}", insert: "\\log_{#?}(#0)", class: "small" },
        { latex: "e^{#?}", insert: "e^{#0}", class: "small" }
      );
    }
    rows.push(topicRow);
  }

  rows.push(
    [
      { latex: "\\frac{#@}{#?}", insert: "\\frac{#@}{#?}", class: "small" },
      { latex: "#@^{#?}", insert: "#@^{#?}", class: "small" },
      { latex: "\\sqrt{#0}", insert: "\\sqrt{#0}", class: "small" },
      { latex: "\\sqrt[#?]{#0}", insert: "\\sqrt[#?]{#0}", class: "small" },
      { latex: "\\left|#0\\right|", insert: "\\left|#0\\right|", class: "small" },
      { latex: "\\pi" },
      { latex: "i" },
      { latex: "\\pm" },
      { latex: "\\infty" },
    ],
    [
      "(",
      ")",
      { latex: "[", variants: ["\\{"] },
      { latex: "]", variants: ["\\}"] },
      ",",
      "\\le",
      "\\ge",
      "\\ne",
      { latex: "\\cup" },
    ],
    ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
    [
      { latex: "x", variants: ["y", "k", "n"] },
      "+",
      "-",
      "=",
      ".",
      "[left]",
      "[right]",
      { label: "[backspace]", class: "action hide-shift", width: 1.0 },
      { label: "[return]", class: "action hide-shift", width: 1.0 },
      { label: "[hide-keyboard]", width: 1.0 },
    ]
  );

  return {
    id: "studio-compact",
    label: "Math",
    displayEditToolbar: false,
    layers: [
      {
        style: `
          div.studio-vk-backdrop {
            display: flex;
            justify-content: center;
          }
          div.studio-vk-container {
            --keycap-height: 36px;
            --keycap-max-width: 48px;
            --keycap-font-size: 15px;
            --keycap-small-font-size: 12px;
            --keycap-gap: 3px;
            background: var(--keyboard-background);
            padding: 8px 6px 8px 6px;
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
            border: 1px solid var(--keyboard-border);
            border-bottom: none;
            box-shadow: 0 -4px 24px rgb(0 0 0 / 12%);
            max-width: 540px;
            width: 100%;
            box-sizing: border-box;
          }
        `,
        backdrop: "studio-vk-backdrop",
        container: "studio-vk-container",
        rows,
      },
    ],
  };
}

function applyKeyboardConfig(
  vk: (VirtualKeyboardInterface & EventTarget) | undefined,
  profile: UnitKeyboardProfile
): void {
  if (!vk) return;
  vk.editToolbar = "none";
  vk.layouts = [buildCompactKeyboardLayout(profile)];
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
      keyboardProfile,
      disabled = false,
      fieldRef,
      onChange,
      onCheck,
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
    const disabledRef = useRef(disabled);
    disabledRef.current = disabled;
    const keyboardProfileRef = useRef(keyboardProfile);
    keyboardProfileRef.current = keyboardProfile;

    const [ready, setReady] = useState(false);
    const [isEmpty, setIsEmpty] = useState(() => !value.trim());
    const [vkVisible, setVkVisible] = useState(false);

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
        mf.mathVirtualKeyboardPolicy = "auto";
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

        applyKeyboardConfig(window.mathVirtualKeyboard, keyboardProfileRef.current);

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
          }
        };

        const handleBeforeInput = (e: InputEvent) => {
          if (e.inputType === "insertLineBreak") {
            e.preventDefault();
            syncAndCheck();
          }
        };

        const handleFocus = () => {
          applyKeyboardConfig(window.mathVirtualKeyboard, keyboardProfileRef.current);
        };

        const handleVkToggle = () => {
          setVkVisible(Boolean(window.mathVirtualKeyboard?.visible));
        };

        mf.addEventListener("input", handleInput);
        mf.addEventListener("keydown", handleKeyDown);
        mf.addEventListener("beforeinput", handleBeforeInput as EventListener);
        mf.addEventListener("focus", handleFocus);
        window.mathVirtualKeyboard?.addEventListener(
          "virtual-keyboard-toggle",
          handleVkToggle
        );

        setVkVisible(Boolean(window.mathVirtualKeyboard?.visible));
        setReady(true);

        cleanup = () => {
          mf.removeEventListener("input", handleInput);
          mf.removeEventListener("keydown", handleKeyDown);
          mf.removeEventListener("beforeinput", handleBeforeInput as EventListener);
          mf.removeEventListener("focus", handleFocus);
          window.mathVirtualKeyboard?.removeEventListener(
            "virtual-keyboard-toggle",
            handleVkToggle
          );
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

    // Keep keyboard layout synced when switching between units/problems
    useEffect(() => {
      if (!ready) return;
      applyKeyboardConfig(window.mathVirtualKeyboard, keyboardProfile);
    }, [ready, keyboardProfile]);

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

    const handleToggleKeyboard = () => {
      const vk = window.mathVirtualKeyboard;
      const mf = mfRef.current;
      if (!vk || !mf) return;
      if (vk.visible) {
        vk.hide();
      } else {
        applyKeyboardConfig(vk, keyboardProfile);
        mf.focus();
        vk.show();
      }
    };

    return (
      <div className="relative flex items-center flex-1 min-w-0 min-h-[2.75rem] bg-white dark:bg-zinc-950 border border-zinc-300 dark:border-zinc-700 rounded-xl pl-2.5 pr-1.5 py-1 focus-within:ring-2 focus-within:ring-indigo-600/25 dark:focus-within:ring-indigo-500/30 focus-within:border-indigo-600 dark:focus-within:border-indigo-500 transition-colors">
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
            className="pointer-events-none absolute left-3.5 right-10 text-sm text-zinc-400 dark:text-zinc-500 truncate select-none"
          >
            {placeholder}
          </span>
        )}
        {React.createElement("math-field", {
          ref: mfRef,
          "aria-label": ariaLabel,
          class: `studio-math-field flex-1 min-w-0 ${ready ? "" : "sr-only"}`,
        })}
        <button
          type="button"
          onMouseDown={(e) => e.preventDefault()}
          onClick={handleToggleKeyboard}
          disabled={!ready || disabled}
          aria-label="Toggle math keyboard"
          aria-pressed={vkVisible}
          title="Math keyboard"
          className={`inline-flex items-center justify-center w-8 h-8 rounded-lg transition-colors shrink-0 ${
            vkVisible
              ? "text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/60"
              : "text-zinc-400 dark:text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800"
          } disabled:opacity-40`}
        >
          <Keyboard className="w-4 h-4" />
        </button>
      </div>
    );
  }
);

export default MathLiveInput;
