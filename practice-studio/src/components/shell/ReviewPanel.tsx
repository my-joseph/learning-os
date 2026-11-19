"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowLeft,
  ArrowUpRight,
  ChevronDown,
  Flag,
  PenLine,
  RefreshCw,
  Send,
} from "lucide-react";
import { DrillDocument, Problem } from "@/types/drill";
import { canRevealVerifiedAnswer, hasSubstantiveAttempt } from "@/lib/reviewGuard";
import { isLabId } from "@/lib/routes";
import {
  OUTCOME_META,
  classifyReviewOutcome,
  ensureExpandedRow,
  formatDuration,
  getQuestionLabel,
  getReviewOutcomeMeta,
  groupReviewProblems,
  toSingleLinePrompt,
  toggleExpandedRow,
  type GroupedReviewItem,
} from "@/lib/reviewOutcome";
import { FormattedText } from "@/components/FormattedText";
import { MathFigure } from "@/components/MathFigure";
import { Reveal } from "@/components/motion/Reveal";

interface ReviewPanelProps {
  currentDrill: DrillDocument;
  liveScore: number;
  maxScore: number;
  accuracyPct: number;
  skippedCount: number;
  computedPracticeStatus: "Graded" | "Needs Retry";
  isSyncing: boolean;
  totalDurationMs?: number;
  initialExpandedIds?: string[];
  onStatusOverrideChange: (status: "Graded" | "Needs Retry") => void;
  onBackToQuiz: () => void;
  onConfirmSync: () => void;
  onSelectQuestion: (idx: number) => void;
  onSetScore: (probId: string, score: number | null) => void;
  onToggleMistakeTag: (probId: string, tagId: string) => void;
  onMistakeNoteChange: (probId: string, note: string) => void;
}

const SCORE_OPTIONS = [
  {
    val: 1,
    label: "1.0",
    activeCls:
      "border-emerald-700 dark:border-emerald-400 text-emerald-700 dark:text-emerald-400 font-semibold",
  },
  {
    val: 0.5,
    label: "0.5",
    activeCls:
      "border-amber-700 dark:border-amber-400 text-amber-700 dark:text-amber-400 font-semibold",
  },
  {
    val: 0,
    label: "0",
    activeCls:
      "border-rose-600 dark:border-rose-400 text-rose-600 dark:text-rose-400 font-semibold",
  },
] as const;

const LEGEND_ITEMS = [
  { key: "correct_first", label: "First try" },
  { key: "assisted_or_partial", label: "Assisted" },
  { key: "wrong", label: "Wrong" },
  { key: "skipped", label: "Skipped" },
  { key: "unanswered", label: "Unanswered" },
] as const;

/** Pre-Sync review and edit panel for checking scores, mistake tags, and notes before syncing to Notion. */
export const ReviewPanel: React.FC<ReviewPanelProps> = ({
  currentDrill,
  liveScore,
  maxScore,
  accuracyPct,
  computedPracticeStatus,
  isSyncing,
  totalDurationMs: totalDurationMsOverride,
  initialExpandedIds,
  onStatusOverrideChange,
  onBackToQuiz,
  onConfirmSync,
  onSelectQuestion,
  onSetScore,
  onToggleMistakeTag,
  onMistakeNoteChange,
}) => {
  const [showCorrect, setShowCorrect] = useState(false);
  const [expandedIds, setExpandedIds] = useState<Record<string, boolean>>(() => {
    const initial: Record<string, boolean> = {};
    for (const id of initialExpandedIds ?? []) {
      initial[id] = true;
    }
    return initial;
  });
  const [pendingScrollId, setPendingScrollId] = useState<string | null>(null);
  const [highlightedId, setHighlightedId] = useState<string | null>(null);
  const rowRefs = useRef<Map<string, HTMLDivElement>>(new Map());

  const isLab = isLabId(currentDrill.drillId);
  const isCode = currentDrill.subject === "PRG" && !isLab;
  const drillTitle = currentDrill.unitTitle || currentDrill.unitCode;
  const mistakeTags = currentDrill.mistakeTags || [];

  const backLabel = isLab
    ? "Back to milestones"
    : isCode
    ? "Back to problems"
    : "Back to questions";
  const allFirstTryText = isLab
    ? "All milestones were completed on the first try."
    : isCode
    ? "All problems were solved on the first try."
    : "All questions were answered correctly on the first try.";
  const outcomeGroupLabel = isLab
    ? "Milestone outcomes"
    : isCode
    ? "Problem outcomes"
    : "Question outcomes";

  useEffect(() => {
    setShowCorrect(false);
    const initial: Record<string, boolean> = {};
    for (const id of initialExpandedIds ?? []) {
      initial[id] = true;
    }
    setExpandedIds(initial);
    setPendingScrollId(null);
    setHighlightedId(null);
  }, [currentDrill.drillId, initialExpandedIds]);

  useEffect(() => {
    if (!pendingScrollId) return;
    const timer = window.setTimeout(() => {
      const el =
        rowRefs.current.get(pendingScrollId) ??
        document.getElementById(`review-row-${pendingScrollId}`);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
        setHighlightedId(pendingScrollId);
      }
      setPendingScrollId(null);
    }, 60);
    return () => window.clearTimeout(timer);
  }, [pendingScrollId, showCorrect]);

  useEffect(() => {
    if (!highlightedId) return;
    const timer = window.setTimeout(() => setHighlightedId(null), 1200);
    return () => window.clearTimeout(timer);
  }, [highlightedId]);

  const {
    needsAttention,
    correct,
    firstTryCount,
    unansweredCount,
    totalDurationMs: recordedDurationMs,
  } = useMemo(
    () => groupReviewProblems(currentDrill.problems),
    [currentDrill.problems]
  );
  const totalDurationMs = totalDurationMsOverride ?? recordedDurationMs;

  const firstTryPct =
    maxScore > 0 ? Math.round((firstTryCount / maxScore) * 100) : 0;

  const handleJumpToRow = (probId: string, inCorrectGroup: boolean) => {
    if (inCorrectGroup && !showCorrect) {
      setShowCorrect(true);
    }
    setExpandedIds((prev) => ensureExpandedRow(prev, probId));
    setPendingScrollId(probId);
  };

  const renderQuestionRow = ({
    problem: prob,
    index: idx,
    outcome,
  }: GroupedReviewItem<Problem>) => {
    const pScore = prob.state.score;
    const meta = getReviewOutcomeMeta(outcome);
    const qLabel = getQuestionLabel(prob.id, idx, isLab);
    const singleLinePrompt = toSingleLinePrompt(prob.prompt);
    const isHighlighted = highlightedId === prob.id;
    const isExpanded = Boolean(expandedIds[prob.id]);
    const panelId = `review-panel-${prob.id}`;
    const isAttempted = hasSubstantiveAttempt(prob.state);

    const hasVerifiedAnswer = Boolean(prob.answerPlain || prob.answerDisplay);
    const latestReview = prob.state.reviews?.[prob.state.reviews.length - 1];
    const hasAnswerText = Boolean(prob.state.userInput || prob.state.lastTestReport);
    const isQuietUnanswered = outcome === "unanswered" && !hasAnswerText;
    const learnerAnswerText =
      prob.state.userInput ||
      (prob.state.lastTestReport
        ? `${prob.state.lastTestReport.passedCount}/${prob.state.lastTestReport.totalCount} tests passed`
        : "Not answered yet");
    const hasFigure = Boolean(prob.figure || prob.visual);

    return (
      <div
        key={prob.id}
        id={`review-row-${prob.id}`}
        ref={(el) => {
          if (el) rowRefs.current.set(prob.id, el);
          else rowRefs.current.delete(prob.id);
        }}
        className={`px-4 py-4 sm:px-6 grid grid-cols-[64px_minmax(0,1fr)] gap-x-2.5 items-start transition-colors ${
          isHighlighted ? "bg-indigo-50/70 dark:bg-indigo-950/25" : ""
        }`}
      >
        {/* Column 1: status node + question/milestone label (fixed width, top-aligned) */}
        <div className="flex items-center gap-2 pt-1 min-w-0">
          <span
            title={meta.label}
            aria-hidden="true"
            className={`w-2.5 h-2.5 rounded-[3px] shrink-0 ${meta.nodeClassName}`}
          />

          <button
            type="button"
            onClick={() => onSelectQuestion(idx)}
            title={`Open ${qLabel}`}
            className="inline-flex items-center gap-0.5 text-xs font-mono font-semibold text-zinc-900 dark:text-zinc-100 hover:text-indigo-600 dark:hover:text-indigo-400 shrink-0 transition-colors"
          >
            <span>{qLabel}</span>
            <ArrowUpRight className="w-3 h-3 text-zinc-500 dark:text-zinc-400" />
          </button>
        </div>

        {/* Column 2: in-place expandable prompt + figure + answer/result + bottom note & score line */}
        <div className="min-w-0 space-y-2">
          <div>
            <button
              type="button"
              onClick={() => setExpandedIds((prev) => toggleExpandedRow(prev, prob.id))}
              aria-expanded={isExpanded}
              aria-controls={panelId}
              title={isExpanded ? `Collapse ${qLabel} prompt` : `Expand ${qLabel} prompt`}
              className="w-full min-w-0 flex items-start justify-between gap-2 text-left rounded-md py-0.5 text-zinc-800 dark:text-zinc-200 hover:text-zinc-950 dark:hover:text-zinc-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 transition-colors"
            >
              <span
                className={`block min-w-0 flex-1 text-sm leading-relaxed break-words ${
                  isExpanded ? "" : "truncate"
                }`}
              >
                <FormattedText text={isExpanded ? prob.prompt : singleLinePrompt} />
              </span>
              <ChevronDown
                aria-hidden="true"
                className={`w-4 h-4 mt-1 text-zinc-500 dark:text-zinc-400 shrink-0 transition-transform duration-150 ${
                  isExpanded ? "rotate-180" : ""
                }`}
              />
            </button>

            <Reveal show={isExpanded}>
              <div id={panelId} className={hasFigure ? "pt-2" : undefined}>
                {hasFigure && (
                  <MathFigure
                    figure={prob.figure || prob.visual!}
                    className="w-full"
                  />
                )}
              </div>
            </Reveal>
          </div>

          <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1 text-xs">
            {isQuietUnanswered ? (
              <span className="italic text-zinc-500 dark:text-zinc-400">
                Not answered yet
              </span>
            ) : (
              <>
                <div className="min-w-0 break-words">
                  <span className="text-zinc-500 dark:text-zinc-400">Your answer: </span>
                  <span className="font-mono text-zinc-800 dark:text-zinc-200">
                    {learnerAnswerText}
                  </span>
                </div>

                <div className="min-w-0 break-words">
                  {hasVerifiedAnswer ? (
                    <>
                      <span className="text-zinc-500 dark:text-zinc-400">Verified: </span>
                      {canRevealVerifiedAnswer(prob.state) ? (
                        <span className="font-mono text-emerald-700 dark:text-emerald-400">
                          {prob.answerPlain || prob.answerDisplay}
                        </span>
                      ) : (
                        <span className="italic text-zinc-500 dark:text-zinc-400">
                          Not answered yet
                        </span>
                      )}
                    </>
                  ) : (
                    <>
                      <span className="text-zinc-500 dark:text-zinc-400">Result: </span>
                      <span className={`font-medium ${meta.textClassName}`}>
                        {latestReview
                          ? `${meta.label} (review: ${latestReview.verdict})`
                          : meta.label}
                      </span>
                    </>
                  )}
                </div>
              </>
            )}

            {typeof prob.state.divergedStep === "number" && (
              <span className="inline-flex items-center gap-1 text-rose-600 dark:text-rose-400 font-medium">
                <Flag className="w-3 h-3" />
                <span>Diverged at step {prob.state.divergedStep + 1}</span>
              </span>
            )}
          </div>

          {isAttempted && (
            <div className="space-y-2">
              {mistakeTags.length > 0 && (
                <div className="flex flex-wrap items-center gap-1.5">
                  {mistakeTags.map((t) => {
                    const hasTag = prob.state.mistakes.includes(t.id);
                    return (
                      <button
                        key={t.id}
                        type="button"
                        onClick={() => onToggleMistakeTag(prob.id, t.id)}
                        aria-pressed={hasTag}
                        className={`min-h-[24px] py-0.5 px-2.5 rounded-full text-[11px] font-medium border transition-colors inline-flex items-center ${
                          hasTag
                            ? "border-rose-600 dark:border-rose-400 text-rose-700 dark:text-rose-300 bg-white dark:bg-zinc-900 font-semibold"
                            : "bg-white dark:bg-zinc-900 text-zinc-500 dark:text-zinc-400 border-zinc-200 dark:border-zinc-800 hover:border-zinc-300 dark:hover:border-zinc-700"
                        }`}
                      >
                        <FormattedText text={t.label} />
                      </button>
                    );
                  })}
                </div>
              )}

              <div className="flex flex-wrap sm:flex-nowrap items-center gap-2">
                <div className="flex-1 min-w-[180px] flex items-center gap-2 bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-lg px-2.5 py-1.5 transition-colors focus-within:border-indigo-600 dark:focus-within:border-indigo-400 focus-within:ring-2 focus-within:ring-indigo-600/20 dark:focus-within:ring-indigo-400/25">
                  <PenLine className="w-3.5 h-3.5 text-zinc-500 dark:text-zinc-400 shrink-0" />
                  <input
                    type="text"
                    value={prob.state.mistakeNote || ""}
                    onChange={(e) => onMistakeNoteChange(prob.id, e.target.value)}
                    placeholder={`Note for ${qLabel}…`}
                    aria-label={`Note for ${qLabel}`}
                    className="w-full min-w-0 bg-transparent text-xs text-zinc-800 dark:text-zinc-200 placeholder:text-zinc-500 dark:placeholder:text-zinc-400 focus:outline-none"
                  />
                </div>

                {currentDrill.subject !== "PRG" && (
                  <div className="flex items-center gap-1 shrink-0">
                    {SCORE_OPTIONS.map((btn) => (
                      <button
                        key={btn.val}
                        type="button"
                        onClick={() => onSetScore(prob.id, btn.val)}
                        aria-label={`Set ${qLabel} score to ${btn.label}`}
                        aria-pressed={pScore === btn.val}
                        className={`h-7 px-2 rounded-md text-[11px] font-mono border transition-colors ${
                          pScore === btn.val
                            ? `${btn.activeCls} bg-zinc-50 dark:bg-zinc-950`
                            : "bg-white dark:bg-zinc-900 text-zinc-500 dark:text-zinc-400 border-zinc-200 dark:border-zinc-800 hover:border-zinc-300 dark:hover:border-zinc-700"
                        }`}
                      >
                        {btn.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="max-w-[720px] mx-auto space-y-6">
      {/* 1. Summary card */}
      <section className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-4 sm:p-6 space-y-4">
        <div className="space-y-1">
          <h1 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100 tracking-tight">
            {drillTitle}
          </h1>
          <p className="font-mono text-xs text-zinc-500 dark:text-zinc-400">
            {currentDrill.unitCode}
          </p>
        </div>

        <div className="space-y-3">
          <div className="flex items-baseline gap-2.5">
            <span className="text-3xl sm:text-4xl font-semibold font-sans tabular-nums tracking-tight text-zinc-900 dark:text-zinc-100">
              {liveScore} / {maxScore}
            </span>
            <span className="text-sm font-sans tabular-nums text-zinc-500 dark:text-zinc-400">
              ({accuracyPct}%)
            </span>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
            <div
              role="group"
              aria-label={outcomeGroupLabel}
              className="flex flex-wrap items-center -m-1.5"
            >
              {currentDrill.problems.map((prob, idx) => {
                const outcome = classifyReviewOutcome(prob.state);
                const meta = getReviewOutcomeMeta(outcome);
                const qLabel = getQuestionLabel(prob.id, idx, isLab);
                const tooltip = `${qLabel} — ${meta.label}`;
                return (
                  <button
                    key={prob.id}
                    type="button"
                    onClick={() =>
                      handleJumpToRow(prob.id, outcome === "correct_first")
                    }
                    title={tooltip}
                    aria-label={tooltip}
                    className="group inline-flex items-center justify-center w-6 h-6 rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
                  >
                    <span
                      aria-hidden="true"
                      className={`w-2.5 h-2.5 rounded-[3px] transition-transform group-hover:scale-125 ${meta.nodeClassName}`}
                    />
                  </button>
                );
              })}
            </div>

            <div
              aria-hidden="true"
              className="flex flex-wrap items-center gap-x-2.5 gap-y-1 sm:gap-x-3 text-[11px] text-zinc-500 dark:text-zinc-400"
            >
              {LEGEND_ITEMS.map((item) => (
                <span key={item.key} className="inline-flex items-center gap-1 whitespace-nowrap">
                  <span
                    className={`w-2 h-2 rounded-[2px] ${OUTCOME_META[item.key].nodeClassName}`}
                  />
                  <span>{item.label}</span>
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="pt-3.5 border-t border-zinc-200/80 dark:border-zinc-800/80 flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-zinc-500 dark:text-zinc-400">
          <div className="flex items-center gap-1.5">
            <span>First-try</span>
            <span className="font-mono font-medium tabular-nums text-zinc-900 dark:text-zinc-100">
              {firstTryPct}%
            </span>
          </div>

          <div className="flex items-center gap-1.5">
            <span>Time</span>
            <span className="font-mono font-medium tabular-nums text-zinc-900 dark:text-zinc-100">
              {formatDuration(totalDurationMs)}
            </span>
          </div>

          <div className="flex items-center gap-2 sm:ml-auto">
            <span>Status</span>
            <div className="inline-flex rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950 p-0.5">
              {(["Graded", "Needs Retry"] as const).map((st) => {
                const active = computedPracticeStatus === st;
                return (
                  <button
                    key={st}
                    type="button"
                    onClick={() => onStatusOverrideChange(st)}
                    aria-pressed={active}
                    className={`px-2 py-0.5 rounded-md text-xs transition-colors ${
                      active
                        ? "bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 font-medium shadow-sm"
                        : "text-zinc-500 dark:text-zinc-400 hover:text-zinc-800 dark:hover:text-zinc-200"
                    }`}
                  >
                    {st}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* 2. Primary action */}
      <section className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl px-4 py-4 sm:px-6 space-y-2">
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            type="button"
            onClick={onConfirmSync}
            disabled={isSyncing || maxScore === 0}
            className="inline-flex items-center gap-2 h-10 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-700 disabled:opacity-50 text-white text-sm font-medium transition-colors shrink-0"
          >
            {isSyncing ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Syncing…</span>
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                <span>Sync to Notion</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={onBackToQuiz}
            className="inline-flex items-center gap-1.5 h-10 px-2.5 rounded-xl text-zinc-600 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-sm font-medium transition-colors shrink-0"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>{backLabel}</span>
          </button>

          {unansweredCount > 0 && (
            <p className="text-xs text-amber-700 dark:text-amber-400">
              {unansweredCount} unanswered — sync anyway or finish first.
            </p>
          )}
        </div>

        <p className="text-xs text-zinc-500 dark:text-zinc-400">
          Writes your score, mistake tags, notes, and spaced-review schedule for{" "}
          <span className="font-mono">{currentDrill.unitCode}</span> to Notion.
        </p>
      </section>

      {/* 3. Question / problem / milestone list */}
      <section className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl overflow-hidden">
        <div className="px-4 py-3 sm:px-6 bg-zinc-50/70 dark:bg-zinc-950/50 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
            Needs attention
          </h2>
          <span className="text-xs font-mono tabular-nums text-zinc-500 dark:text-zinc-400">
            {needsAttention.length}
          </span>
        </div>

        {needsAttention.length > 0 ? (
          <div className="divide-y divide-zinc-200 dark:divide-zinc-800">
            {needsAttention.map((item) => renderQuestionRow(item))}
          </div>
        ) : (
          <p className="px-4 py-4 sm:px-6 text-sm text-zinc-500 dark:text-zinc-400">
            {allFirstTryText}
          </p>
        )}

        {correct.length > 0 && (
          <div className="border-t border-zinc-200 dark:border-zinc-800">
            <button
              type="button"
              onClick={() => setShowCorrect((prev) => !prev)}
              aria-expanded={showCorrect}
              className="w-full px-4 py-3 sm:px-6 bg-zinc-50/70 dark:bg-zinc-950/50 hover:bg-zinc-100/70 dark:hover:bg-zinc-900 flex items-center justify-between text-left transition-colors"
            >
              <span className="inline-flex items-center gap-2 text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                <ChevronDown
                  className={`w-4 h-4 text-zinc-500 dark:text-zinc-400 transition-transform duration-150 ${
                    showCorrect ? "rotate-0" : "-rotate-90"
                  }`}
                />
                <span>Correct</span>
              </span>
              <span className="text-xs font-mono tabular-nums text-zinc-500 dark:text-zinc-400">
                {correct.length}
              </span>
            </button>

            <Reveal show={showCorrect}>
              <div className="divide-y divide-zinc-200 dark:divide-zinc-800 border-t border-zinc-200 dark:border-zinc-800">
                {correct.map((item) => renderQuestionRow(item))}
              </div>
            </Reveal>
          </div>
        )}
      </section>
    </div>
  );
};
