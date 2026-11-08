"use client";

import React, { useState, useEffect } from "react";
import {
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  Lightbulb,
  RotateCcw,
  HelpCircle,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  PenLine,
} from "lucide-react";
import { Problem, MistakeTag, CheckResult } from "@/types/drill";
import { MathBlock } from "./MathRender";
import { FormattedText } from "./FormattedText";
import { StepRow } from "./StepRow";
import { VisualRenderer } from "./VisualRenderer";

interface MathProblemCardProps {
  problem: Problem;
  index: number;
  mistakeTags: MistakeTag[];
  activeStep: number | null;
  onInputChange: (val: string) => void;
  onCheckAnswer: () => Promise<void> | void;
  onSkip?: () => void;
  onToggleStepHighlight: (stepIdx: number) => void;
  onMarkDivergedStep: (stepIdx: number) => void;
  onSetScore: (score: number) => void;
  onToggleMistakeTag: (tagId: string) => void;
  onMistakeNoteChange: (note: string) => void;
  onResetProblem: () => void;
}

const getSafeMathPlaceholder = (hint?: string, problem?: Problem): string => {
  if (!hint) return "Enter final answer (press Enter to check)...";

  const acceptedList: string[] = [];
  if (problem?.answerSpec?.accepted) {
    for (const a of problem.answerSpec.accepted) {
      if (a !== undefined && a !== null) {
        acceptedList.push(String(a).toLowerCase().trim());
      }
    }
  }
  if (problem?.answerPlain) {
    acceptedList.push(String(problem.answerPlain).toLowerCase().trim());
  }
  if (problem?.answerDisplay) {
    const raw = String(problem.answerDisplay)
      .replace(/[\$\\]/g, "")
      .replace(/\\[a-zA-Z]+/g, "")
      .replace(/\^\{\\circ\}/g, "")
      .trim()
      .toLowerCase();
    if (raw) acceptedList.push(raw);
  }

  const lowerHint = hint.toLowerCase();
  const hasLeak = acceptedList.some((ans) => ans.length >= 2 && lowerHint.includes(ans));

  if (!hasLeak) return hint;

  const stripped = hint.replace(/\s*\([^)]*e\.g\.[^)]*\)/gi, "").trim();
  if (stripped && !acceptedList.some((ans) => ans.length >= 2 && stripped.toLowerCase().includes(ans))) {
    return stripped;
  }

  return "Enter final answer (press Enter to check)...";
};

export const MathProblemCard: React.FC<MathProblemCardProps> = ({
  problem,
  index,
  mistakeTags,
  activeStep,
  onInputChange,
  onCheckAnswer,
  onSkip,
  onToggleStepHighlight,
  onMarkDivergedStep,
  onSetScore,
  onToggleMistakeTag,
  onMistakeNoteChange,
  onResetProblem,
}) => {
  const [copied, setCopied] = useState(false);
  const [showHint, setShowHint] = useState(false);
  const [showSolution, setShowSolution] = useState(Boolean(problem.state.lastCheck));
  const [isChecking, setIsChecking] = useState(false);

  useEffect(() => {
    setShowSolution(Boolean(problem.state.lastCheck));
  }, [problem.id, problem.state.lastCheck]);

  const handleCopyCas = () => {
    if (!problem.plainText) return;
    navigator.clipboard.writeText(problem.plainText);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  };

  const triggerCheck = async () => {
    if (!problem.state.userInput.trim() || isChecking) return;
    setIsChecking(true);
    try {
      await onCheckAnswer();
      setShowSolution(true);
    } finally {
      setIsChecking(false);
    }
  };

  const score = problem.state.score;
  const lastCheck: CheckResult | null | undefined = problem.state.lastCheck;

  return (
    <article className="bg-white dark:bg-[#151924] border border-slate-200 dark:border-[#2c354d] rounded-2xl p-5 md:p-6 shadow-sm">
      {/* Header */}
      <div className="flex flex-wrap justify-between items-center gap-2 mb-4 pb-3 border-b border-slate-200 dark:border-[#2c354d]">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-bold text-base text-slate-900 dark:text-white">
            Problem {index + 1}{" "}
            <span className="text-slate-500 dark:text-slate-400 font-normal text-sm">
              ({problem.id})
            </span>
          </span>
          {problem.context && (
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-amber-50 dark:bg-amber-500/10 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-500/30">
              <FormattedText text={problem.context} />
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {problem.state.skipped && (
            <span className="text-xs px-2.5 py-1 rounded-full bg-amber-50 dark:bg-amber-500/10 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-500/30 font-medium">
              Skipped
            </span>
          )}
          <span className="text-xs px-2.5 py-1 rounded-full bg-slate-100 dark:bg-[#1d2333] text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-[#2c354d] font-medium">
            Level {problem.level}
          </span>
          <button
            type="button"
            title="Reset this question"
            onClick={onResetProblem}
            className="inline-flex items-center justify-center w-8 h-8 rounded-lg text-slate-500 dark:text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-500/10 border border-transparent hover:border-rose-200 dark:hover:border-rose-500/30 transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Prompt */}
      <div className="text-base text-slate-800 dark:text-slate-100 mb-4 leading-relaxed">
        <FormattedText text={problem.prompt} />
      </div>

      {/* Visual Engine: Render 2D/3D Diagram or Physics Visual */}
      {problem.visual && <VisualRenderer visual={problem.visual} />}

      {/* LaTeX Display Box + Compact Plain-Text Copy */}
      {(problem.display || problem.plainText) && (
        <div className="bg-slate-50 dark:bg-[#10141f] border border-slate-200 dark:border-[#2c354d] rounded-xl p-3.5 mb-4">
          {problem.display && (
            <div className="text-center overflow-x-auto text-slate-900 dark:text-slate-100">
              <MathBlock latex={problem.display} />
            </div>
          )}
          {problem.plainText && (
            <div
              className={`flex flex-wrap items-center justify-between gap-2 text-xs ${
                problem.display
                  ? "mt-2.5 pt-2.5 border-t border-slate-200/80 dark:border-[#232b3e]"
                  : ""
              }`}
            >
              <div className="flex items-center gap-1.5 text-slate-500 dark:text-slate-400 overflow-x-auto">
                <span className="font-medium shrink-0">Plain-Text / CAS:</span>
                <code className="font-mono text-indigo-700 dark:text-indigo-300 bg-indigo-50 dark:bg-indigo-950/50 border border-indigo-200/60 dark:border-indigo-800/40 px-2 py-0.5 rounded">
                  {problem.plainText}
                </code>
              </div>
              <button
                type="button"
                onClick={handleCopyCas}
                className="inline-flex items-center gap-1.5 h-7 px-2.5 rounded-md bg-white dark:bg-[#1d2333] hover:bg-indigo-50 dark:hover:bg-indigo-600/20 text-slate-700 dark:text-slate-300 hover:text-indigo-700 dark:hover:text-white border border-slate-200 dark:border-[#2c354d] transition-colors font-medium shrink-0"
              >
                {copied ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                    <span className="text-emerald-600 dark:text-emerald-400">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Copy Plain-Text</span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Workspace / Input Row */}
      <div className="flex flex-wrap gap-2.5 items-center mb-4">
        {problem.answerSpec.type === "choice" ? (
          <div className="flex flex-wrap gap-2 w-full mb-1">
            {problem.answerSpec.options?.map((opt) => {
              const isSelected = problem.state.userInput === opt.id;
              return (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => onInputChange(opt.id)}
                  className={`min-h-[38px] px-3.5 py-2 rounded-xl border text-sm font-semibold transition-all flex items-center gap-2 ${
                    isSelected
                      ? "bg-indigo-600 text-white border-indigo-600 shadow-sm"
                      : "bg-slate-50 dark:bg-[#1d2333] text-slate-800 dark:text-slate-200 border-slate-200 dark:border-[#2c354d] hover:border-indigo-400 dark:hover:border-indigo-400"
                  }`}
                >
                  <span
                    className={`inline-flex items-center justify-center w-5 h-5 rounded text-xs font-mono font-bold ${
                      isSelected
                        ? "bg-white/20 text-white"
                        : "bg-white dark:bg-[#141926] text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-[#2c354d]"
                    }`}
                  >
                    {opt.id}
                  </span>
                  <FormattedText text={opt.label} />
                </button>
              );
            })}
          </div>
        ) : (
          <input
            type="text"
            value={problem.state.userInput}
            onChange={(e) => onInputChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                triggerCheck();
              }
            }}
            placeholder={getSafeMathPlaceholder(problem.inputHint, problem)}
            className="flex-1 min-w-[240px] h-10 font-mono text-sm bg-white dark:bg-[#1d2333] text-slate-900 dark:text-slate-100 border border-slate-300 dark:border-[#2c354d] rounded-xl px-3.5 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500 placeholder:text-slate-400 dark:placeholder:text-slate-500"
          />
        )}

        <button
          type="button"
          onClick={triggerCheck}
          disabled={isChecking || !problem.state.userInput.trim()}
          className="inline-flex items-center gap-1.5 h-10 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-semibold transition-colors shadow-sm"
        >
          {isChecking ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Checking...</span>
            </>
          ) : (
            <>
              <Check className="w-4 h-4" />
              <span>Check Answer</span>
            </>
          )}
        </button>

        <button
          type="button"
          onClick={() => setShowHint(!showHint)}
          className="inline-flex items-center gap-1.5 h-10 px-3.5 rounded-xl bg-slate-100 dark:bg-[#1d2333] hover:bg-amber-50 dark:hover:bg-amber-500/10 text-slate-700 dark:text-slate-300 hover:text-amber-800 dark:hover:text-amber-300 border border-slate-200 dark:border-[#2c354d] text-sm font-medium transition-colors"
        >
          <Lightbulb className="w-4 h-4 text-amber-500 dark:text-amber-400" />
          <span>Hint</span>
        </button>

        <button
          type="button"
          onClick={() => setShowSolution(!showSolution)}
          className="inline-flex items-center gap-1.5 h-10 px-3.5 rounded-xl bg-slate-100 dark:bg-[#1d2333] hover:bg-slate-200/70 dark:hover:bg-indigo-600/20 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-[#2c354d] text-sm font-medium transition-colors"
        >
          {showSolution ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          <span>{showSolution ? "Hide Steps" : "Step-by-Step Solution"}</span>
        </button>

        {onSkip && (
          <button
            type="button"
            onClick={() => {
              setShowHint(true);
              setShowSolution(true);
              onSkip();
            }}
            title="Skip this question to inspect the solution and log concept gaps"
            className="inline-flex items-center gap-1.5 h-10 px-3.5 rounded-xl bg-slate-100 dark:bg-[#1d2333] hover:bg-rose-50 dark:hover:bg-rose-500/15 text-slate-600 dark:text-slate-300 hover:text-rose-700 dark:hover:text-rose-300 border border-slate-200 dark:border-[#2c354d] hover:border-rose-300 dark:hover:border-rose-500/40 text-sm font-medium transition-colors"
          >
            <HelpCircle className="w-4 h-4 text-rose-500 dark:text-rose-400" />
            <span>Skip</span>
          </button>
        )}
      </div>

      {/* Checkpoint Hint */}
      {showHint && (
        <div className="bg-amber-50 dark:bg-[#121826] border border-amber-200 dark:border-amber-500/30 rounded-xl p-3.5 mb-4 text-sm text-amber-900 dark:text-amber-200">
          <strong className="text-amber-700 dark:text-amber-400 font-semibold">
            Intermediate Checkpoint:
          </strong>{" "}
          <FormattedText text={problem.checkpointHint} />
        </div>
      )}

      {/* Answer Diagnostics Result */}
      {lastCheck && (
        <div
          className={`p-3.5 rounded-xl border mb-4 text-sm ${
            lastCheck.verdict === "correct"
              ? "bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-500/40 text-emerald-900 dark:text-emerald-200"
              : lastCheck.verdict === "equivalent_not_in_form" || lastCheck.verdict === "partial" || lastCheck.verdict === "skipped"
              ? "bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-500/40 text-amber-900 dark:text-amber-200"
              : "bg-rose-50 dark:bg-rose-950/40 border-rose-200 dark:border-rose-500/40 text-rose-900 dark:text-rose-200"
          }`}
        >
          <div className="flex items-center gap-2 font-semibold">
            {lastCheck.verdict === "correct" ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
            ) : lastCheck.verdict === "equivalent_not_in_form" || lastCheck.verdict === "partial" || lastCheck.verdict === "skipped" ? (
              <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
            ) : (
              <XCircle className="w-4 h-4 text-rose-600 dark:text-rose-400 shrink-0" />
            )}
            <span>{lastCheck.message}</span>
          </div>
          {lastCheck.components?.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-2">
              {lastCheck.components.map((c, i) => (
                <span
                  key={i}
                  className={`text-xs px-2 py-0.5 rounded font-mono font-medium ${
                    c.ok
                      ? "bg-emerald-100 dark:bg-emerald-900/60 text-emerald-800 dark:text-emerald-300"
                      : "bg-rose-100 dark:bg-rose-900/60 text-rose-800 dark:text-rose-300"
                  }`}
                >
                  {c.label}: {c.ok ? "PASS" : "FAIL"}
                </span>
              ))}
            </div>
          )}
          {lastCheck.diagnostics?.length > 0 && (
            <div className="mt-2 text-xs text-slate-700 dark:text-slate-300 space-y-1">
              {lastCheck.diagnostics.map((d, i) => (
                <div key={i}>
                  <strong className="text-amber-700 dark:text-amber-400">[{d.code}]:</strong> {d.message}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Step-by-Step Solution List */}
      {showSolution && (
        <div
          className={`bg-slate-50 dark:bg-[#10141f] border border-slate-200 dark:border-[#2c354d] rounded-xl p-4 mb-4 ${
            activeStep !== null ? "has-active" : ""
          }`}
        >
          <div className="flex flex-wrap justify-between items-center gap-2 mb-3 pb-2 border-b border-slate-200 dark:border-[#2c354d]">
            <span className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
              Step-by-Step Derivation (Click a step to compare with your scratchpad)
            </span>
            <span className="text-xs text-slate-600 dark:text-slate-400">
              Verified Final: <FormattedText text={`$${problem.answerDisplay}$`} />
            </span>
          </div>
          <div>
            {problem.steps.map((st, sIdx) => (
              <StepRow
                key={sIdx}
                step={st}
                index={sIdx}
                isActive={activeStep === sIdx}
                isDiverged={problem.state.divergedStep === sIdx}
                onToggleHighlight={() => onToggleStepHighlight(sIdx)}
                onMarkDiverged={() => onMarkDivergedStep(sIdx)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Unified Scoring, Mistake Tags & Custom Mistake Note Footer */}
      <div className="pt-3.5 border-t border-slate-200 dark:border-[#2c354d] space-y-3 text-xs">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-1.5">
            <span className="text-slate-600 dark:text-slate-400 font-medium mr-1">Score:</span>
            {[
              { val: 1, label: "1.0", activeCls: "bg-emerald-600 text-white border-emerald-600" },
              { val: 0.5, label: "0.5", activeCls: "bg-amber-600 text-white border-amber-600" },
              { val: 0, label: "0", activeCls: "bg-rose-600 text-white border-rose-600" },
            ].map((btn) => (
              <button
                key={btn.val}
                type="button"
                onClick={() => onSetScore(btn.val)}
                className={`h-8 px-3 rounded-lg font-semibold border transition-all ${
                  score === btn.val
                    ? `${btn.activeCls} ring-2 ring-indigo-500/40 shadow-sm`
                    : "bg-slate-100 dark:bg-[#1d2333] text-slate-700 dark:text-slate-300 border-slate-200 dark:border-[#2c354d] hover:border-slate-400"
                }`}
              >
                {btn.label}
              </button>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-slate-600 dark:text-slate-400 font-medium mr-1">Mistake Tags:</span>
            {mistakeTags.map((t) => {
              const hasTag = problem.state.mistakes.includes(t.id);
              return (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => onToggleMistakeTag(t.id)}
                  className={`min-h-[32px] py-1 px-3 rounded-full text-xs font-medium border transition-colors inline-flex items-center ${
                    hasTag
                      ? "bg-rose-100 dark:bg-rose-500/20 text-rose-800 dark:text-rose-300 border-rose-300 dark:border-rose-500/50 font-semibold"
                      : "bg-slate-100 dark:bg-[#1d2333] text-slate-600 dark:text-slate-400 border-slate-200 dark:border-[#2c354d] hover:border-slate-400"
                  }`}
                >
                  <FormattedText text={t.label} />
                </button>
              );
            })}
          </div>
        </div>

        {/* Custom Mistake Note Input (Flow 3.2) */}
        <div className="flex items-center gap-2 bg-slate-50 dark:bg-[#10141f] border border-slate-200 dark:border-[#2c354d] rounded-xl px-3 py-2 focus-within:border-rose-400 dark:focus-within:border-rose-500/60 transition-colors">
          <PenLine className="w-4 h-4 text-rose-500 dark:text-rose-400 shrink-0" />
          <input
            type="text"
            value={problem.state.mistakeNote || ""}
            onChange={(e) => onMistakeNoteChange(e.target.value)}
            placeholder="Add custom mistake note (e.g., forgot to evaluate exponent before multiplying, sign error)..."
            className="w-full bg-transparent text-xs md:text-sm text-slate-800 dark:text-slate-200 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none"
          />
        </div>
      </div>
    </article>
  );
};
