"use client";

import React from "react";
import {
  ArrowUpRight,
  Check,
  ChevronDown,
  Copy,
  Flag,
  PenLine,
  RotateCcw,
} from "lucide-react";
import type { MistakeTag, Problem } from "@/types/drill";
import { CARD_STYLES, getSubstantiveAttemptCount, type ResultCardTone } from "@/lib/answerFeedback";
import { canRevealVerifiedAnswer, hasSubstantiveAttempt } from "@/lib/reviewGuard";
import { maxAllowedSelfScore, scoreProblem } from "@/lib/scoring";
import { similarUnlock } from "@/lib/similarTabs";
import {
  formatDuration,
  getQuestionLabel,
  getReviewOutcomeMeta,
  type ReviewOutcome,
} from "@/lib/reviewOutcome";
import {
  lastAnswerText,
  latestReviewVerdict,
  matchedTraps,
  normaliseTestReport,
  rowReason,
  shortRowTitle,
  verifiedAnswerLabel,
} from "@/lib/reviewRow";
import { getReviewRequest } from "@/lib/studioRules";
import { statusTone } from "@/lib/statusTone";
import { statusSymbolClass } from "@/lib/statusSymbol";
import { trapName } from "@/lib/titleText";
import { FormattedText } from "@/components/FormattedText";
import { MathFigure } from "@/components/MathFigure";
import { Reveal } from "@/components/motion/Reveal";
import { ListDot } from "@/components/ui/ListDot";
import { CopyButton } from "@/components/ui/CopyButton";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/shadcn/Collapsible";
import { Input } from "@/components/ui/shadcn/Input";
import { ProblemSelfEval } from "@/components/workspace/ProblemSelfEval";

export interface ReviewItemRowProps {
  drillId: string;
  problem: Problem;
  index: number;
  outcome: ReviewOutcome;
  isLab: boolean;
  isCode: boolean;
  isGotRightRow?: boolean;
  mistakeTags: MistakeTag[];
  expanded: boolean;
  highlighted?: boolean;
  disabled?: boolean;
  rowRef?: (el: HTMLDivElement | null) => void;
  onToggle: () => void;
  onOpen: () => void;
  onTrySimilar?: () => void;
  onSetScore: (score: number | null) => void;
  onToggleMistakeTag: (tagId: string) => void;
  onMistakeNoteChange: (note: string) => void;
  onRevisitNoteChange: (note: string) => void;
}

function toneForOutcome(outcome: ReviewOutcome): ResultCardTone {
  if (outcome === "correct_first") return "correct";
  if (outcome === "assisted_or_partial") return "assisted";
  if (outcome === "skipped") return "skipped";
  if (outcome === "awaiting_review" || outcome === "unanswered") return "inputError";
  return "wrong";
}

/** Compact math or PRG/lab result summary shown inside an expanded Review & Sync row. */
const ReviewItemResult: React.FC<{
  problem: Problem;
  outcome: ReviewOutcome;
  isCode: boolean;
  isLab: boolean;
}> = ({ problem, outcome, isCode, isLab }) => {
  const state = problem.state;

  if (isCode || isLab) {
    const testRep = normaliseTestReport(state?.lastTestReport);
    const rev = latestReviewVerdict(state);
    const passed = testRep.passed ?? rev.testsPassed;
    const total = testRep.total ?? rev.testsTotal;

    const testsKind: "pass" | "fail" | "none" =
      passed !== null && total !== null
        ? total > 0 && passed === total
          ? "pass"
          : "fail"
        : testRep.hasData
        ? testRep.allPassed
          ? "pass"
          : "fail"
        : "none";

    const lintKind: "pass" | "fail" | "none" =
      rev.lintCount === null ? "none" : rev.lintCount === 0 ? "pass" : "fail";
    const typesKind: "pass" | "fail" | "none" =
      rev.typecheckCount === null ? "none" : rev.typecheckCount === 0 ? "pass" : "fail";
    const revKind: "pass" | "fail" | "none" =
      rev.status === "pass" ? "pass" : rev.status === "revise" ? "fail" : "none";

    return (
      <div className="space-y-2.5">
        <div
          role="status"
          aria-label="Check and review status"
          className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs py-2.5 px-3.5 rounded-xl bg-surface-panel border border-zinc-200 dark:border-zinc-800"
        >
          <span>
            <span className="text-zinc-500 dark:text-zinc-400">Tests </span>
            {passed !== null && total !== null ? (
              <span className={`font-sans tabular-nums ${statusSymbolClass(testsKind)}`}>
                {passed}/{total}
              </span>
            ) : testRep.hasData ? (
              <span className={statusSymbolClass(testsKind)}>Tests run</span>
            ) : (
              <span className={statusSymbolClass("none")}>–</span>
            )}
            {isLab && testRep.hiddenTotal !== null && testRep.hiddenTotal > 0 && (
              <span className="ml-1.5 text-zinc-500 dark:text-zinc-400 font-sans tabular-nums">
                · hidden {testRep.hiddenPassed ?? 0}/{testRep.hiddenTotal}
              </span>
            )}
          </span>

          <span>
            <span className="text-zinc-500 dark:text-zinc-400">Lint </span>
            <span className={`font-sans tabular-nums ${statusSymbolClass(lintKind)}`}>
              {lintKind === "none" ? "–" : lintKind === "pass" ? "✓" : `✗ ${rev.lintCount}`}
            </span>
          </span>

          <span>
            <span className="text-zinc-500 dark:text-zinc-400">Types </span>
            <span className={`font-sans tabular-nums ${statusSymbolClass(typesKind)}`}>
              {typesKind === "none"
                ? "–"
                : typesKind === "pass"
                ? "✓"
                : `✗ ${rev.typecheckCount}`}
            </span>
          </span>

          <span>
            <span className="text-zinc-500 dark:text-zinc-400">Review </span>
            <span className={statusSymbolClass(revKind)}>
              {rev.status === "not_requested" ? "–" : rev.status}
            </span>
            {rev.isUnknownVerdict && rev.rawVerdict && (
              <span className="ml-1 text-zinc-500 dark:text-zinc-400">({rev.rawVerdict})</span>
            )}
          </span>
        </div>

        {rev.findings.length > 0 && (
          <ul aria-label="Review findings" className="space-y-1.5 text-xs text-zinc-700 dark:text-zinc-300">
            {rev.findings.map((finding, fIdx) => (
              <li key={`${finding.check}-${fIdx}`} className="flex items-start gap-2 leading-relaxed">
                <ListDot kind="info" />
                <span className="min-w-0 break-words">
                  <code className="inline-code mr-space-1_5">
                    {finding.check}
                  </code>
                  {finding.note && <FormattedText text={finding.note} density="compact" />}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    );
  }

  // Math result card (reusing AnswerResultCard CARD_STYLES tones, compact variant)
  const tone = toneForOutcome(outcome);
  const answerText = lastAnswerText(problem);
  const verifiedText = canRevealVerifiedAnswer(state) ? verifiedAnswerLabel(problem) : "";
  const traps = matchedTraps(state);
  const tries = getSubstantiveAttemptCount(state);
  const hints = state?.hintsRevealed ?? 0;
  const duration = typeof state?.durationMs === "number" && state.durationMs > 0
    ? formatDuration(state.durationMs)
    : null;

  const metaParts: React.ReactNode[] = [];
  if (traps.length > 0) {
    metaParts.push(
      <span key="trap">
        <span className="text-zinc-500 dark:text-zinc-400">Trap: </span>
        <span className="font-semibold text-zinc-900 dark:text-zinc-100">
          {traps.map((t) => trapName(t)).join(", ")}
        </span>
      </span>
    );
  }
  if (tries > 0) {
    metaParts.push(
      <span key="tries">
        <span className="text-zinc-500 dark:text-zinc-400">Tries </span>
        <span className="font-sans tabular-nums text-zinc-800 dark:text-zinc-200">{tries}</span>
      </span>
    );
  }
  if (hints > 0) {
    metaParts.push(
      <span key="hints">
        <span className="text-zinc-500 dark:text-zinc-400">Hints </span>
        <span className="font-sans tabular-nums text-zinc-800 dark:text-zinc-200">{hints}</span>
      </span>
    );
  }
  if (duration) {
    metaParts.push(
      <span key="time" className="font-sans tabular-nums text-zinc-700 dark:text-zinc-300">
        {duration}
      </span>
    );
  }

  return (
    <div className={`rounded-xl p-3 sm:p-3.5 space-y-1.5 text-xs ${CARD_STYLES[tone]}`}>
      <div className="flex flex-wrap items-baseline gap-x-5 gap-y-1">
        <div className="min-w-0 break-words">
          <span className="text-zinc-500 dark:text-zinc-400">Your answer: </span>
          <span className="font-sans tabular-nums font-semibold text-zinc-900 dark:text-zinc-100">
            {outcome === "skipped" && !answerText
              ? "Skipped"
              : answerText ? <FormattedText text={answerText} /> : "Not recorded"}
          </span>
        </div>

        {verifiedText && (
          <div className="min-w-0 break-words">
            <span className="text-zinc-500 dark:text-zinc-400">Verified answer: </span>
            <span className={`font-sans tabular-nums font-semibold ${statusTone.correct.text}`}>
              <FormattedText text={verifiedText} />
            </span>
          </div>
        )}
      </div>

      {typeof state?.divergedStep === "number" && (
        <div className={`inline-flex items-center gap-1.5 ${statusTone.wrong.text} font-normal`}>
          <Flag className="w-3 h-3 shrink-0" aria-hidden="true" />
          <span>
            Went off track at step{" "}
            <span className="font-sans tabular-nums">{state.divergedStep + 1}</span>
          </span>
        </div>
      )}

      {metaParts.length > 0 && (
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-zinc-600 dark:text-zinc-300">
          {metaParts.map((part, idx) => (
            <React.Fragment key={idx}>
              {idx > 0 && (
                <span aria-hidden="true" className="text-zinc-400 dark:text-zinc-500">
                  ·
                </span>
              )}
              {part}
            </React.Fragment>
          ))}
        </div>
      )}
    </div>
  );
};

/** Single expandable row in Section B ("To review") or Section C ("Got right"). */
export const ReviewItemRow: React.FC<ReviewItemRowProps> = ({
  drillId,
  problem,
  index,
  outcome,
  isLab,
  isCode,
  isGotRightRow = false,
  mistakeTags,
  expanded,
  highlighted = false,
  disabled = false,
  rowRef,
  onToggle,
  onOpen,
  onTrySimilar,
  onSetScore,
  onToggleMistakeTag,
  onMistakeNoteChange,
  onRevisitNoteChange,
}) => {

  const meta = getReviewOutcomeMeta(outcome);
  const qLabel = getQuestionLabel(problem.id, index, isLab);
  const title = shortRowTitle(problem);
  const reason = rowReason(problem, outcome, isCode, isLab);
  const panelId = `review-panel-${problem.id}`;
  const isAttempted = hasSubstantiveAttempt(problem.state);
  const hasFigure = Boolean(problem.figure || problem.visual);

  const hasRecordedNote = Boolean(
    problem.state?.mistakeNote?.trim() || problem.state?.revisitNote?.trim()
  );
  const hasRecordedTags = Boolean((problem.state?.mistakes?.length ?? 0) > 0);

  const testRep = normaliseTestReport(problem.state?.lastTestReport);
  const rev = latestReviewVerdict(problem.state);
  const canCopyReviewRequest =
    (isCode || isLab) && testRep.allPassed && rev.status !== "pass" && Boolean(drillId);
  const reviewRequestCmd = getReviewRequest(drillId, problem.id);

  const unansweredActionLabel = isLab
    ? `Start ${qLabel}`
    : isCode
    ? `Open ${qLabel}`
    : `Answer ${qLabel}`;

  return (
    <Collapsible
      id={`review-row-${problem.id}`}
      ref={rowRef}
      open={expanded}
      onOpenChange={(nextOpen) => {
        if (nextOpen !== expanded) onToggle();
      }}
      className={`transition-colors motion-reduce:transition-none ${
        highlighted ? "bg-indigo-50/70 dark:bg-indigo-950/25" : ""
      }`}
    >
      {/* Collapsed summary header (~48px height, wraps cleanly at 390px) */}
      <CollapsibleTrigger asChild>
        <button
          type="button"
          aria-controls={panelId}
          className="w-full min-h-[48px] px-4 py-3 sm:px-6 flex items-start sm:items-center justify-between gap-3 text-left hover:bg-zinc-50/80 dark:hover:bg-zinc-800/40 transition-colors motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
        >
          <div className="min-w-0 flex-1 flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-3">
            <div className="flex items-center gap-2.5 min-w-0">
              <span
                title={meta.label}
                aria-hidden="true"
                className={`w-2.5 h-2.5 rounded-[3px] shrink-0 ${meta.nodeClassName}`}
              />
              <span className="font-sans tabular-nums text-xs font-semibold text-zinc-900 dark:text-zinc-100 shrink-0">
                {qLabel}
              </span>
              <span className="min-w-0 truncate text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                <FormattedText text={title} />
              </span>
            </div>

            <span className="pl-5 sm:pl-0 text-xs text-zinc-500 dark:text-zinc-400 break-words sm:truncate min-w-0">
              {reason}
            </span>
          </div>

          <div className="flex items-center gap-2 shrink-0 pt-0.5 sm:pt-0">
            {hasRecordedNote && (
              <span
                title="Note recorded"
                aria-label="Note recorded"
                className="text-zinc-500 dark:text-zinc-400"
              >
                <PenLine className="w-3.5 h-3.5" aria-hidden="true" />
              </span>
            )}
            {hasRecordedTags && (
              <span
                title="Mistake tag recorded"
                aria-label="Mistake tag recorded"
                className={`w-2 h-2 rounded-full ${statusTone.wrong.dot} shrink-0`}
              />
            )}
            <ChevronDown
              aria-hidden="true"
              className={`w-4 h-4 text-zinc-500 dark:text-zinc-400 shrink-0 transition-transform duration-150 motion-reduce:transition-none ${
                expanded ? "rotate-180" : ""
              }`}
            />
          </div>
        </button>
      </CollapsibleTrigger>

      {/* Expanded detail (inside the row, no card-in-card, pl-[72px] on desktop, full width on mobile) */}
      <CollapsibleContent id={panelId}>
        <Reveal show={expanded}>
          {expanded && (
            <div className="px-4 pb-4 sm:px-6 sm:pb-5 sm:pl-[72px] space-y-4 text-sm">
              {/* 1. Full prompt & figure (never display set-up, steps, hints, or reference solution) */}
              <div className="space-y-3">
                <div className="text-sm leading-relaxed text-zinc-800 dark:text-zinc-200 break-words">
                  <FormattedText text={problem.prompt} />
                </div>
                {hasFigure && (
                  <MathFigure
                    figure={problem.figure || problem.visual!}
                    className="w-full"
                  />
                )}
              </div>

              {/* 2. Unanswered vs Attempted content */}
              {outcome === "unanswered" ? (
                <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs">
                  <span className="text-zinc-500 dark:text-zinc-400">Not tried yet</span>
                  <button
                    type="button"
                    onClick={onOpen}
                    className="inline-flex items-center gap-1 min-h-[44px] sm:min-h-[28px] text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 rounded-md"
                  >
                    <span>{unansweredActionLabel}</span>
                    <ArrowUpRight className="w-3.5 h-3.5" aria-hidden="true" />
                  </button>
                </div>
              ) : (
                <>
                  <ReviewItemResult
                    problem={problem}
                    outcome={outcome}
                    isCode={isCode}
                    isLab={isLab}
                  />

                  {/* 3. Record block (only after substantive attempt/skip) */}
                  {isAttempted && (
                    <div className="space-y-3">
                      {!isGotRightRow && (
                        <ProblemSelfEval
                          hasAttempt={isAttempted}
                          showSelfScore={!isCode && !isLab}
                          disabled={disabled}
                          maxScore={maxAllowedSelfScore(problem.state, { isPrg: isCode || isLab })}
                          skipped={Boolean(problem.state.skipped)}
                          score={scoreProblem(problem.state, { isPrg: isCode || isLab }).score}
                          mistakes={problem.state.mistakes || []}
                          mistakeNote={problem.state.mistakeNote}
                          mistakeTags={mistakeTags}
                          noteAriaLabel={`Note for ${qLabel}`}
                          onSetScore={onSetScore}
                          onToggleMistakeTag={onToggleMistakeTag}
                          onMistakeNoteChange={onMistakeNoteChange}
                        />
                      )}

                      {/* Revisit note stays in learner progress; the Notion drill page does not display it. */}
                      <div className="flex items-center gap-2 bg-surface-panel dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl px-3 py-2 transition-colors focus-within:border-indigo-600 dark:focus-within:border-indigo-400 focus-within:ring-2 focus-within:ring-indigo-600/20 dark:focus-within:ring-indigo-400/25">
                        <RotateCcw
                          className="w-3.5 h-3.5 text-zinc-500 dark:text-zinc-400 shrink-0"
                          aria-hidden="true"
                        />
                        <Input
                          type="text"
                          variant="embedded"
                          disabled={disabled}
                          value={problem.state.revisitNote || ""}
                          onChange={(e) => onRevisitNoteChange(e.target.value)}
                          aria-label={`Revisit note for ${qLabel}`}
                          placeholder="Next time I will…"
                          className="text-xs"
                        />
                      </div>
                    </div>
                  )}

                  {/* 4. Row actions as quiet text links */}
                  <div className="flex flex-wrap items-center gap-x-5 gap-y-1 pt-0.5">
                    <button
                      type="button"
                      onClick={onOpen}
                      className="inline-flex items-center gap-1 min-h-[44px] sm:min-h-[28px] text-xs font-normal text-zinc-700 dark:text-zinc-300 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 rounded-md"
                    >
                      <span>Open {qLabel}</span>
                      <ArrowUpRight className="w-3.5 h-3.5" aria-hidden="true" />
                    </button>

                    {!isCode && !isLab && problem.hasVariants && onTrySimilar && similarUnlock(problem.state) && (
                      <button
                        type="button"
                        onClick={onTrySimilar}
                        className="inline-flex items-center gap-1 min-h-[44px] sm:min-h-[28px] text-xs font-normal text-zinc-700 dark:text-zinc-300 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 rounded-md"
                      >
                        <span>Try a similar question</span>
                      </button>
                    )}

                    {canCopyReviewRequest && (
                      <CopyButton
                        text={reviewRequestCmd}
                        className="inline-flex items-center gap-1.5 min-h-[44px] sm:min-h-[28px] text-xs font-normal text-zinc-700 dark:text-zinc-300 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 rounded-md"
                        timeoutMs={1500}
                        requireClipboard
                        copiedContent={
                          <>
                            <Check className="w-3.5 h-3.5" aria-hidden="true" />
                            <span>Copied review request</span>
                          </>
                        }
                      >
                        <>
                          <Copy className="w-3.5 h-3.5" aria-hidden="true" />
                          <span>Copy review request</span>
                        </>
                      </CopyButton>
                    )}
                  </div>
                </>
              )}
            </div>
          )}
        </Reveal>
      </CollapsibleContent>
    </Collapsible>
  );
};
