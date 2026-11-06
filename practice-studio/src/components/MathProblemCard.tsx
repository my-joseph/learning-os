"use client";

import React, { useState } from "react";
import { Copy, Check, ChevronDown, ChevronUp, Lightbulb, RotateCcw } from "lucide-react";
import { Problem, MistakeTag, CheckResult } from "@/types/drill";
import { MathBlock } from "./MathRender";
import { FormattedText } from "./FormattedText";
import { NotionBadge } from "./NotionBadge";
import { StepRow } from "./StepRow";
import { VisualRenderer } from "./VisualRenderer";

interface MathProblemCardProps {
  problem: Problem;
  index: number;
  mistakeTags: MistakeTag[];
  activeStep: number | null;
  onInputChange: (val: string) => void;
  onCheckAnswer: () => void;
  onToggleStepHighlight: (stepIdx: number) => void;
  onMarkDivergedStep: (stepIdx: number) => void;
  onSetScore: (score: number) => void;
  onToggleMistakeTag: (tagId: string) => void;
  onResetProblem: () => void;
}

const getSafeMathPlaceholder = (hint?: string, problem?: Problem): string => {
  if (!hint) return "Type final answer or solve on paper...";

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

  return "Type final answer or solve on paper...";
};

export const MathProblemCard: React.FC<MathProblemCardProps> = ({
  problem,
  index,
  mistakeTags,
  activeStep,
  onInputChange,
  onCheckAnswer,
  onToggleStepHighlight,
  onMarkDivergedStep,
  onSetScore,
  onToggleMistakeTag,
  onResetProblem,
}) => {
  const [copied, setCopied] = useState(false);
  const [showHint, setShowHint] = useState(false);
  const [showSolution, setShowSolution] = useState(false);

  const handleCopyCas = () => {
    if (!problem.plainText) return;
    navigator.clipboard.writeText(problem.plainText);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  };

  const score = problem.state.score;
  const lastCheck: CheckResult | null | undefined = problem.state.lastCheck;

  return (
    <article className="bg-[#151924] border border-[#2c354d] rounded-2xl p-5 mb-5 shadow-sm">
      {/* Header */}
      <div className="flex flex-wrap justify-between items-center gap-2 mb-3 pb-2.5 border-b border-[#2c354d]">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-bold text-base text-indigo-200">
            Problem {index + 1}{" "}
            <span className="text-slate-400 font-normal">({problem.id})</span>
          </span>
          {problem.context && (
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/30">
              <FormattedText text={problem.context} />
            </span>
          )}
          {problem.referenceBadges?.map((b) => (
            <NotionBadge key={b.code} badge={b} />
          ))}
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            title="Reset this question"
            onClick={onResetProblem}
            className="p-1 rounded-md text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#1d2333] text-slate-400 border border-[#2c354d]">
            Level {problem.level}
          </span>
        </div>
      </div>

      {/* Prompt */}
      <div className="text-sm md:text-base text-slate-100 mb-3">
        <FormattedText text={problem.prompt} />
      </div>

      {/* Visual Engine: Render 2D/3D Diagram or Physics Visual */}
      {problem.visual && <VisualRenderer visual={problem.visual} />}

      {/* LaTeX Display Box */}
      {problem.display && (
        <div className="bg-[#10141f] border border-[#2c354d] rounded-xl p-3 mb-3.5 text-center overflow-x-auto">
          <MathBlock latex={problem.display} />
        </div>
      )}

      {/* Plain Text CAS */}
      {problem.plainText && (
        <div className="flex flex-wrap items-center justify-between gap-2 bg-[#10131d] border border-dashed border-[#2c354d] rounded-lg px-3 py-2 mb-3.5 text-xs text-slate-300">
          <span>
            <strong className="text-slate-400">Plain-Text / CAS Input:</strong>{" "}
            <code className="font-mono text-indigo-300 bg-indigo-950/40 px-1.5 py-0.5 rounded">
              {problem.plainText}
            </code>
          </span>
          <button
            type="button"
            onClick={handleCopyCas}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-[#1d2333] hover:bg-indigo-600/20 text-slate-300 hover:text-white border border-[#2c354d] transition-colors"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            {copied ? "Copied" : "Copy"}
          </button>
        </div>
      )}

      {/* Workspace / Input Row */}
      <div className="flex flex-wrap gap-2.5 items-center mb-3">
        {problem.answerSpec.type === "choice" ? (
          <div className="flex flex-wrap gap-2">
            {problem.answerSpec.options?.map((opt) => {
              const isSelected = problem.state.userInput === opt.id;
              return (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => {
                    onInputChange(opt.id);
                  }}
                  className={`px-3 py-1.5 rounded-lg border text-sm font-semibold transition-all ${
                    isSelected
                      ? "bg-indigo-600 text-white border-indigo-500 shadow-sm"
                      : "bg-[#1d2333] text-slate-300 border-[#2c354d] hover:border-indigo-400"
                  }`}
                >
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
              if (e.key === "Enter") onCheckAnswer();
            }}
            placeholder={getSafeMathPlaceholder(problem.inputHint, problem)}
            className="flex-1 min-w-[240px] font-mono text-sm bg-[#1d2333] text-slate-100 border border-[#2c354d] rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500"
          />
        )}

        <button
          type="button"
          onClick={onCheckAnswer}
          className="px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition-colors shadow-sm"
        >
          Check Answer
        </button>

        <button
          type="button"
          onClick={() => setShowHint(!showHint)}
          className="inline-flex items-center gap-1 px-3 py-2 rounded-lg bg-[#1d2333] hover:bg-indigo-600/20 text-slate-300 border border-[#2c354d] text-sm font-medium transition-colors"
        >
          <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
          Checkpoint Hint
        </button>

        <button
          type="button"
          onClick={() => setShowSolution(!showSolution)}
          className="inline-flex items-center gap-1 px-3 py-2 rounded-lg bg-[#1d2333] hover:bg-indigo-600/20 text-slate-300 border border-[#2c354d] text-sm font-medium transition-colors"
        >
          {showSolution ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          {showSolution ? "Hide Solution" : "Reveal Step-by-Step Solution"}
        </button>
      </div>

      {/* Checkpoint Hint */}
      {showHint && (
        <div className="bg-[#121826] border border-amber-500/30 rounded-xl p-3 mb-3.5 text-xs text-amber-200">
          <strong className="text-amber-400">Intermediate Checkpoint:</strong>{" "}
          <FormattedText text={problem.checkpointHint} />
        </div>
      )}

      {/* Answer Diagnostics Result */}
      {lastCheck && (
        <div
          className={`p-3 rounded-xl border mb-3.5 text-xs ${
            lastCheck.verdict === "correct"
              ? "bg-emerald-950/40 border-emerald-500/40 text-emerald-200"
              : lastCheck.verdict === "equivalent_not_in_form" || lastCheck.verdict === "partial"
              ? "bg-amber-950/40 border-amber-500/40 text-amber-200"
              : "bg-rose-950/40 border-rose-500/40 text-rose-200"
          }`}
        >
          <div className="font-semibold mb-1">{lastCheck.message}</div>
          {lastCheck.components?.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-1.5">
              {lastCheck.components.map((c, i) => (
                <span
                  key={i}
                  className={`text-xs px-2 py-0.5 rounded font-mono ${
                    c.ok ? "bg-emerald-900/60 text-emerald-300" : "bg-rose-900/60 text-rose-300"
                  }`}
                >
                  {c.label}: {c.ok ? "PASS" : "FAIL"}
                </span>
              ))}
            </div>
          )}
          {lastCheck.diagnostics?.length > 0 && (
            <div className="mt-2 text-xs text-slate-300 space-y-1">
              {lastCheck.diagnostics.map((d, i) => (
                <div key={i}>
                  <strong className="text-amber-400">[{d.code}]:</strong> {d.message}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Step-by-Step Solution List */}
      {showSolution && (
        <div className="bg-[#10141f] border border-[#2c354d] rounded-xl p-3.5 mb-3.5">
          <div className="flex justify-between items-center mb-2.5 pb-1.5 border-b border-[#2c354d]">
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              Step-by-Step Derivation
            </span>
            <span className="text-xs text-slate-400">
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

      {/* Bottom Bar: Manual Scoring + Mistake Tags */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2.5 border-t border-[#2c354d] text-xs">
        <div className="flex items-center gap-1.5">
          <span className="text-slate-400 mr-1">Score:</span>
          {[
            { val: 1, label: "1.0", cls: "bg-emerald-600 hover:bg-emerald-500 text-white" },
            { val: 0.5, label: "0.5", cls: "bg-amber-600 hover:bg-amber-500 text-white" },
            { val: 0, label: "0", cls: "bg-rose-600 hover:bg-rose-500 text-white" },
          ].map((btn) => (
            <button
              key={btn.val}
              type="button"
              onClick={() => onSetScore(btn.val)}
              className={`px-2 py-0.5 rounded font-semibold transition-colors ${
                score === btn.val
                  ? "ring-2 ring-white " + btn.cls
                  : "bg-[#1d2333] text-slate-400 hover:text-white"
              }`}
            >
              {btn.label}
            </button>
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-slate-400 mr-1">Mistake Tags:</span>
          {mistakeTags.map((t) => {
            const hasTag = problem.state.mistakes.includes(t.id);
            return (
              <button
                key={t.id}
                type="button"
                onClick={() => onToggleMistakeTag(t.id)}
                className={`px-2 py-0.5 rounded-full text-xs font-medium border transition-colors ${
                  hasTag
                    ? "bg-rose-500/20 text-rose-300 border-rose-500/50 font-semibold"
                    : "bg-[#1d2333] text-slate-400 border-[#2c354d] hover:border-slate-500"
                }`}
              >
                {t.label}
              </button>
            );
          })}
        </div>
      </div>
    </article>
  );
};
