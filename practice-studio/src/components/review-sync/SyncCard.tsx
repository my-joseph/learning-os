"use client";

import React, { useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  ArrowUpRight,
  Check,
  ChevronDown,
  Copy,
  RefreshCw,
  Send,
  Terminal,
  WifiOff,
} from "lucide-react";
import type { SyncState } from "@/hooks/useProgressSync";
import type { ProblemJumpTarget } from "@/lib/reviewRow";
import {
  formatShortDate,
  formatSyncTimestamp,
  type SyncPreview,
} from "@/lib/sessionSummary";
import { statusTone, warningTone } from "@/lib/statusTone";
import { Reveal } from "@/components/motion/Reveal";
import { ListDot } from "@/components/ui/ListDot";
import type { EffectiveSyncPhase } from "./SessionSummaryCard";

export interface SyncCardProps {
  preview: SyncPreview;
  syncState: SyncState;
  effectiveSyncPhase: EffectiveSyncPhase;
  syncedAt?: string | null;
  drillPageId?: string | null;
  changedCount: number;
  isLab: boolean;
  labId?: string;
  labSummary?: { passed: number; revise: number; notTried: number; total: number };
  l4Challenge?: ProblemJumpTarget | null;
  onSync: () => void;
  onStatusOverrideChange: (status: "Graded" | "Needs Retry") => void;
  onAnswerFirstUnanswered?: () => void;
  onOpenL4Challenge?: (index: number) => void;
}

function firstLine(text?: string | null): string {
  if (!text) return "";
  const trimmed = text.trim();
  const nl = trimmed.indexOf("\n");
  const single = nl >= 0 ? trimmed.slice(0, nl).trim() : trimmed;
  return single.length > 140 ? `${single.slice(0, 137)}…` : single;
}

function notionPageUrl(pageId?: string | null): string | null {
  if (!pageId) return null;
  const clean = pageId.trim();
  if (!clean || clean.startsWith("mock-")) return null;
  return `https://www.notion.so/${clean.replace(/-/g, "")}`;
}

/** Section D: Sync to Notion card (all sync states) or Submit lab card for project labs. */
export const SyncCard: React.FC<SyncCardProps> = ({
  preview,
  syncState,
  effectiveSyncPhase,
  syncedAt,
  drillPageId,
  changedCount,
  isLab,
  labId,
  labSummary,
  l4Challenge,
  onSync,
  onStatusOverrideChange,
  onAnswerFirstUnanswered,
  onOpenL4Challenge,
}) => {
  const [showLines, setShowLines] = useState(false);
  const [showErrorDetails, setShowErrorDetails] = useState(false);
  const [copiedError, setCopiedError] = useState(false);
  const [copiedSubmitCmd, setCopiedSubmitCmd] = useState(false);

  // Lab variant: terminal submission only — never calls drill sync.
  if (isLab) {
    const safeLabId = labId || "LAB";
    const submitCommand = `cd labs/${safeLabId} && npm run submit`;
    const handleCopySubmit = () => {
      if (typeof navigator !== "undefined" && navigator.clipboard) {
        void navigator.clipboard.writeText(submitCommand);
      }
      setCopiedSubmitCmd(true);
      window.setTimeout(() => setCopiedSubmitCmd(false), 1500);
    };

    const total = labSummary?.total ?? preview.summary.maxScore;
    const passed = labSummary?.passed ?? 0;
    const revise = labSummary?.revise ?? 0;
    const notTried = labSummary?.notTried ?? total;

    return (
      <section
        id="review-sync-section"
        aria-labelledby="sync-card-heading"
        className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-4 sm:p-6 space-y-4"
      >
        <div className="space-y-1">
          <h2
            id="sync-card-heading"
            className="text-sm font-semibold text-zinc-900 dark:text-zinc-100"
          >
            Submit lab
          </h2>
          <p className="text-sm text-zinc-600 dark:text-zinc-300">
            <span className="font-display font-semibold tabular-nums text-zinc-900 dark:text-zinc-100">
              {passed}
            </span>{" "}
            of{" "}
            <span className="font-display font-semibold tabular-nums text-zinc-900 dark:text-zinc-100">
              {total}
            </span>{" "}
            milestones passed
            {revise > 0 && (
              <>
                {" · "}
                <span className="font-display tabular-nums">{revise}</span>{" "}
                needs revision
              </>
            )}
            {notTried > 0 && (
              <>
                {" · "}
                <span className="font-display tabular-nums">{notTried}</span>{" "}
                not tried
              </>
            )}
          </p>
        </div>

        <div className="flex items-center gap-2.5 rounded-xl bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 px-3.5 py-3 overflow-x-auto">
          <Terminal className="w-4 h-4 text-zinc-500 dark:text-zinc-400 shrink-0" aria-hidden="true" />
          <code className="font-mono text-xs text-zinc-900 dark:text-zinc-100 whitespace-nowrap">
            {submitCommand}
          </code>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center gap-2.5">
          <button
            type="button"
            onClick={handleCopySubmit}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 min-h-[44px] sm:h-10 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-700 text-white text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 shrink-0"
          >
            {copiedSubmitCmd ? (
              <>
                <Check className="w-4 h-4" aria-hidden="true" />
                <span>Copied submit command</span>
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" aria-hidden="true" />
                <span>Copy submit command</span>
              </>
            )}
          </button>

          <p className="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
            Runs every test (including hidden ones) and records the result in Notion.
          </p>
        </div>
      </section>
    );
  }

  const { summary } = preview;
  const isGraded = summary.practiceStatus === "Graded";
  const toggleTargetStatus: "Graded" | "Needs Retry" = isGraded ? "Needs Retry" : "Graded";
  const toggleLabel = isGraded ? "Mark as needs retry" : "Mark as graded";

  const isSyncing = effectiveSyncPhase === "syncing";
  const syncTime = formatSyncTimestamp(syncedAt || syncState.at);
  const notionUrl = notionPageUrl(drillPageId || syncState.drillPageId);

  const unitReviewEntries = syncState.unitReviews
    ? Object.entries(syncState.unitReviews)
    : [];
  const prevUnitByCode = new Map(
    preview.coveredUnits.map((u) => [u.unitCode, u])
  );

  const errorFullText = syncState.message || "Notion sync failed.";
  const errorBrief = firstLine(errorFullText);

  const handleCopyError = () => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      void navigator.clipboard.writeText(errorFullText);
    }
    setCopiedError(true);
    window.setTimeout(() => setCopiedError(false), 1500);
  };

  return (
    <section
      id="review-sync-section"
      aria-labelledby="sync-card-heading"
      className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-4 sm:p-6 space-y-4"
    >
      <h2
        id="sync-card-heading"
        className="text-sm font-semibold text-zinc-900 dark:text-zinc-100"
      >
        Sync to Notion
      </h2>

      {/* Exact payload preview (hidden only when showing the calm post-sync summary, still visible while syncing/changed/error) */}
      {preview.hasAnyAttempt && effectiveSyncPhase !== "synced" && (
        <ul aria-label="Sync preview" className="space-y-2.5 text-sm text-zinc-700 dark:text-zinc-300">
          {/* 1. Drill result + status toggle */}
          <li className="flex items-start gap-2.5 leading-relaxed">
            <ListDot kind="info" />
            <div className="min-w-0 flex-1 flex flex-wrap items-baseline gap-x-2 gap-y-1">
              <span>Drill result:</span>
              <span className="font-display font-semibold tabular-nums text-zinc-900 dark:text-zinc-100">
                {summary.score} / {summary.maxScore} points ({summary.accuracyPct}%)
              </span>
              <span aria-hidden="true" className="text-zinc-400 dark:text-zinc-500">
                ·
              </span>
              <span>
                Status{" "}
                <span className="font-semibold text-zinc-900 dark:text-zinc-100">
                  {isGraded ? "Graded" : "Needs retry"}
                </span>{" "}
                <span className="text-xs text-zinc-500 dark:text-zinc-400">
                  ({preview.statusReason})
                </span>
              </span>
              {preview.hasAnyAttempt && <button
                type="button"
                disabled={isSyncing}
                onClick={() => onStatusOverrideChange(toggleTargetStatus)}
                className="inline-flex items-center min-h-[44px] sm:min-h-[32px] text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:text-indigo-600 dark:hover:text-indigo-400 underline underline-offset-2 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 rounded disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {toggleLabel}
              </button>}
            </div>
          </li>

          {/* 2. Mistake categories */}
          <li className="flex items-start gap-2.5 leading-relaxed">
            <ListDot kind="info" />
            <div className="min-w-0 flex-1 flex flex-wrap items-center gap-1.5">
              <span>Mistake categories:</span>
              {preview.mistakeCategories.length > 0 ? (
                preview.mistakeCategories.map((cat) => (
                  <span
                    key={cat}
                    className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-zinc-100 dark:bg-zinc-800 text-zinc-800 dark:text-zinc-200 border border-zinc-200 dark:border-zinc-700"
                  >
                    {cat}
                  </span>
                ))
              ) : (
                <span className="text-zinc-500 dark:text-zinc-400">No mistakes logged</span>
              )}
            </div>
          </li>

          {/* 3. Mistake log lines + Show lines disclosure */}
          <li className="flex items-start gap-2.5 leading-relaxed">
            <ListDot kind="info" />
            <div className="min-w-0 flex-1 space-y-1.5">
              <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
                <span>Mistake log:</span>
                {preview.logLines.length > 0 ? (
                  <>
                    <span>
                      <span className="font-display font-semibold tabular-nums text-zinc-900 dark:text-zinc-100">
                        {preview.logLines.length}
                      </span>{" "}
                      {preview.logLines.length === 1 ? "line" : "lines"} added to{" "}
                      <span className="italic text-zinc-900 dark:text-zinc-100">
                        {preview.unitTitle}
                      </span>
                    </span>
                    <button
                      type="button"
                      onClick={() => setShowLines((prev) => !prev)}
                      aria-expanded={showLines}
                      aria-controls="sync-preview-log-lines"
                      className="inline-flex items-center gap-0.5 min-h-[44px] sm:min-h-[32px] text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 rounded"
                    >
                      <span>{showLines ? "Hide lines" : "Show lines"}</span>
                      <ChevronDown
                        aria-hidden="true"
                        className={`w-3.5 h-3.5 transition-transform duration-150 ${
                          showLines ? "rotate-180" : ""
                        }`}
                      />
                    </button>
                  </>
                ) : (
                  <span className="text-zinc-500 dark:text-zinc-400">
                    No diverged steps logged.
                  </span>
                )}
              </div>

              <Reveal show={showLines && preview.logLines.length > 0}>
                {showLines && preview.logLines.length > 0 && (
                  <ul
                    id="sync-preview-log-lines"
                    className="rounded-xl bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 px-3 py-2.5 space-y-1 text-xs text-zinc-700 dark:text-zinc-300"
                  >
                    {preview.logLines.map((line, i) => (
                      <li key={i} className="flex items-start gap-2 break-words">
                        <ListDot kind="info" />
                        <span className="min-w-0 break-words">{line}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </Reveal>
            </div>
          </li>

          {/* 4. Review schedule ("now" cached values for every covered unit) */}
          <li className="flex items-start gap-2.5 leading-relaxed">
            <ListDot kind="info" />
            <div className="min-w-0 flex-1 space-y-1">
              <p>
                <span>Review schedule: Mastery and next review for </span>
                {preview.coveredUnits.map((u, idx) => (
                  <React.Fragment key={u.unitCode}>
                    {idx > 0 && ", "}
                    <span className="font-display font-semibold text-zinc-900 dark:text-zinc-100">
                      {u.unitCode}
                    </span>
                  </React.Fragment>
                ))}
                <span> are recalculated from all your practice</span>
              </p>

              {preview.coveredUnits.some(
                (u) => u.mastery !== null || u.nextReview !== null
              ) && (
                <div className="space-y-0.5 text-xs text-zinc-500 dark:text-zinc-400">
                  {preview.coveredUnits.map((u) => {
                    if (u.mastery === null && !u.nextReview) return null;
                    const showCode = preview.coveredUnits.length > 1;
                    return (
                      <p key={u.unitCode}>
                        {showCode && (
                          <span className="font-display text-zinc-700 dark:text-zinc-300 mr-1.5">
                            {u.unitCode}
                          </span>
                        )}
                        <span>now </span>
                        {u.mastery !== null && (
                          <>
                            <span>Mastery </span>
                            <span className="font-display tabular-nums text-zinc-700 dark:text-zinc-300">
                              {u.mastery}
                            </span>
                          </>
                        )}
                        {u.mastery !== null && u.nextReview && <span> · </span>}
                        {u.nextReview && (
                          <>
                            <span>next review </span>
                            <span className="font-display tabular-nums text-zinc-700 dark:text-zinc-300">
                              {formatShortDate(u.nextReview)}
                            </span>
                          </>
                        )}
                      </p>
                    );
                  })}
                </div>
              )}
            </div>
          </li>

          {/* 5. Unanswered items notice */}
          {preview.unansweredCount > 0 && (
            <li className="flex items-start gap-2.5 leading-relaxed">
              <ListDot kind="info" />
              <div className="min-w-0 flex-1 flex flex-wrap items-baseline gap-x-2 gap-y-1">
                <span>
                  <span className="font-display font-semibold tabular-nums text-zinc-900 dark:text-zinc-100">
                    {preview.unansweredCount}
                  </span>{" "}
                  not tried. They are sent as not tried.
                </span>
                {onAnswerFirstUnanswered && (
                  <button
                    type="button"
                    onClick={onAnswerFirstUnanswered}
                    className="inline-flex items-center min-h-[44px] sm:min-h-[32px] text-xs font-medium text-indigo-600 dark:text-indigo-400 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 rounded"
                  >
                    Answer them first
                  </button>
                )}
              </div>
            </li>
          )}
        </ul>
      )}

      {/* Status & action region (aria-live for assistive tech) */}
      <div aria-live="polite" className="space-y-3">
        {/* Changed since sync banner */}
        {effectiveSyncPhase === "changed" && (
          <div className="rounded-xl bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 px-3.5 py-2.5 text-xs text-zinc-700 dark:text-zinc-300">
            You changed{" "}
            <span className="font-display font-semibold tabular-nums text-zinc-900 dark:text-zinc-100">
              {changedCount}
            </span>{" "}
            {changedCount === 1 ? "thing" : "things"} since the last sync.
          </div>
        )}

        {/* Synced state (soft correct tint) */}
        {effectiveSyncPhase === "synced" && (
          <div className={`rounded-xl ${statusTone.correct.softCard} p-4 space-y-3`}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className={`inline-flex items-center gap-2 text-sm font-semibold ${statusTone.correct.text}`}>
                <Check className="w-4 h-4 shrink-0" aria-hidden="true" />
                <span>
                  Synced to Notion
                  {syncTime.shortTime && (
                    <>
                      {" · "}
                      <span className="font-display tabular-nums">{syncTime.shortTime}</span>
                    </>
                  )}
                </span>
              </div>

              {notionUrl && (
                <a
                  href={notionUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`inline-flex items-center gap-1 min-h-[44px] sm:min-h-[32px] text-xs font-medium ${statusTone.correct.text} hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 rounded`}
                >
                  <span>Open in Notion</span>
                  <ArrowUpRight className="w-3.5 h-3.5" aria-hidden="true" />
                </a>
              )}
            </div>

            {unitReviewEntries.length > 0 && (
              <div className="space-y-1.5 text-xs text-zinc-700 dark:text-zinc-300">
                {unitReviewEntries.map(([code, upd]) => {
                  const prevUnit = prevUnitByCode.get(code);
                  const label = prevUnit?.title || code;
                  const prevMastery = prevUnit?.mastery;
                  return (
                    <div key={code} className="space-y-1">
                      <p>
                        <span className="font-semibold text-zinc-900 dark:text-zinc-100">
                          {label}
                        </span>
                        {" · Mastery "}
                        <span className="font-display font-semibold tabular-nums text-zinc-900 dark:text-zinc-100">
                          {prevMastery !== null && prevMastery !== undefined
                            ? `${prevMastery} → ${upd.mastery}`
                            : upd.mastery}
                        </span>
                        {upd.nextReview && (
                          <>
                            {" · next review "}
                            <span className="font-display tabular-nums text-zinc-900 dark:text-zinc-100">
                              {formatShortDate(upd.nextReview)}
                            </span>
                          </>
                        )}
                      </p>
                      {upd.masteryCap?.capped && upd.masteryCap.reason && (
                        <p className="flex flex-wrap items-center gap-x-3 gap-y-1 text-zinc-600 dark:text-zinc-400">
                          <span>
                            Capped at{" "}
                            <span className="font-display tabular-nums">{upd.mastery}</span>
                            {" · "}
                            {upd.masteryCap.reason}
                          </span>
                          {l4Challenge && onOpenL4Challenge && (
                            <button
                              type="button"
                              onClick={() => onOpenL4Challenge(l4Challenge.index)}
                              className="inline-flex items-center gap-1 min-h-[44px] sm:min-h-[32px] font-medium text-indigo-600 dark:text-indigo-400 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 rounded"
                            >
                              <span>Try an L4 challenge</span>
                              <ArrowRight className="w-3 h-3" aria-hidden="true" />
                            </button>
                          )}
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            <div>
              <button
                type="button"
                onClick={onSync}
                disabled={isSyncing}
                className="inline-flex items-center justify-center gap-1.5 min-h-[44px] sm:h-9 px-3.5 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white/90 dark:bg-zinc-900/80 hover:bg-white dark:hover:bg-zinc-900 text-zinc-800 dark:text-zinc-200 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
              >
                <span>Sync again</span>
              </button>
            </div>
          </div>
        )}

        {/* Degraded / saved locally (warning tint) */}
        {effectiveSyncPhase === "degraded" && (
          <div className={`rounded-xl ${warningTone.softCard} p-4 space-y-3`}>
            <div className="flex items-start gap-2.5 text-sm text-zinc-800 dark:text-zinc-200">
              <AlertTriangle
                className={`w-4 h-4 mt-0.5 ${warningTone.text} shrink-0`}
                aria-hidden="true"
              />
              <div className="min-w-0 flex-1 space-y-1.5">
                <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
                  <span className="font-semibold text-zinc-900 dark:text-zinc-100">
                    Saved locally. Notion wasn&apos;t updated:
                  </span>
                  <span className="text-xs text-zinc-700 dark:text-zinc-300 break-words">
                    {errorBrief}
                  </span>
                  <button
                    type="button"
                    onClick={() => setShowErrorDetails((prev) => !prev)}
                    aria-expanded={showErrorDetails}
                    className="inline-flex items-center gap-0.5 min-h-[44px] sm:min-h-[32px] text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 rounded"
                  >
                    <span>Details</span>
                    <ChevronDown
                      aria-hidden="true"
                      className={`w-3.5 h-3.5 transition-transform duration-150 ${
                        showErrorDetails ? "rotate-180" : ""
                      }`}
                    />
                  </button>
                </div>

                <Reveal show={showErrorDetails}>
                  {showErrorDetails && (
                    <pre className={`font-mono text-xs bg-white/80 dark:bg-zinc-950/80 border ${warningTone.borderSoft} rounded-lg p-2.5 overflow-x-auto whitespace-pre-wrap break-words text-zinc-700 dark:text-zinc-300`}>
                      {errorFullText}
                    </pre>
                  )}
                </Reveal>
              </div>
            </div>

            <div>
              <button
                type="button"
                onClick={onSync}
                disabled={isSyncing}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 min-h-[44px] sm:h-10 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-700 text-white text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
              >
                <RefreshCw className="w-4 h-4" aria-hidden="true" />
                <span>Retry</span>
              </button>
            </div>
          </div>
        )}

        {/* Error or Offline (soft wrong tint) */}
        {(effectiveSyncPhase === "error" || effectiveSyncPhase === "offline") && (
          <div className={`rounded-xl ${statusTone.wrong.softCard} p-4 space-y-3`}>
            <div className="flex items-start gap-2.5 text-sm text-zinc-800 dark:text-zinc-200">
              {effectiveSyncPhase === "offline" ? (
                <WifiOff
                  className={`w-4 h-4 mt-0.5 ${statusTone.wrong.text} shrink-0`}
                  aria-hidden="true"
                />
              ) : (
                <AlertTriangle
                  className={`w-4 h-4 mt-0.5 ${statusTone.wrong.text} shrink-0`}
                  aria-hidden="true"
                />
              )}
              <div className="min-w-0 flex-1 space-y-1.5">
                <p className="font-semibold text-zinc-900 dark:text-zinc-100">
                  {effectiveSyncPhase === "offline"
                    ? "You're offline. Nothing was lost: your progress is saved locally."
                    : "Couldn't sync. Nothing was lost: your progress is saved locally."}
                </p>

                {effectiveSyncPhase === "error" && (
                  <>
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs">
                      <span className="text-zinc-700 dark:text-zinc-300 break-words">
                        {errorBrief}
                      </span>
                      <button
                        type="button"
                        onClick={() => setShowErrorDetails((prev) => !prev)}
                        aria-expanded={showErrorDetails}
                        className="inline-flex items-center gap-0.5 min-h-[44px] sm:min-h-[32px] font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 rounded"
                      >
                        <span>Details</span>
                        <ChevronDown
                          aria-hidden="true"
                          className={`w-3.5 h-3.5 transition-transform duration-150 ${
                            showErrorDetails ? "rotate-180" : ""
                          }`}
                        />
                      </button>
                      <button
                        type="button"
                        onClick={handleCopyError}
                        className="inline-flex items-center gap-1 min-h-[44px] sm:min-h-[32px] font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 rounded"
                      >
                        {copiedError ? (
                          <>
                            <Check className={`w-3 h-3 ${statusTone.correct.text}`} aria-hidden="true" />
                            <span>Copied</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-3 h-3" aria-hidden="true" />
                            <span>Copy error</span>
                          </>
                        )}
                      </button>
                    </div>

                    <Reveal show={showErrorDetails}>
                      {showErrorDetails && (
                        <pre className={`font-mono text-xs bg-white/80 dark:bg-zinc-950/80 border ${statusTone.wrong.borderSoft} rounded-lg p-2.5 overflow-x-auto whitespace-pre-wrap break-words text-zinc-700 dark:text-zinc-300`}>
                          {errorFullText}
                        </pre>
                      )}
                    </Reveal>
                  </>
                )}
              </div>
            </div>

            <div>
              <button
                type="button"
                onClick={onSync}
                disabled={isSyncing}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 min-h-[44px] sm:h-10 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-700 text-white text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
              >
                <RefreshCw className="w-4 h-4" aria-hidden="true" />
                <span>Retry</span>
              </button>
            </div>
          </div>
        )}

        {/* Pilot / dry-run state (zinc tint, never stamps syncedAt) */}
        {effectiveSyncPhase === "dryRun" && (
          <div className="rounded-xl bg-zinc-50 dark:bg-zinc-800/50 border border-zinc-200 dark:border-zinc-700/60 p-4 space-y-2.5">
            <p className="text-sm text-zinc-800 dark:text-zinc-200">
              {syncState.isPilot
                ? "Pilot mode: nothing was written to Notion."
                : "Dry run: nothing was written to Notion."}
            </p>
            <button
              type="button"
              onClick={onSync}
              disabled={isSyncing}
              className="inline-flex items-center justify-center gap-1.5 min-h-[44px] sm:h-9 px-3.5 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200 hover:border-zinc-300 dark:hover:border-zinc-600 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
            >
              <span>Sync again</span>
            </button>
          </div>
        )}

        {/* Idle / Syncing / Changed primary action */}
        {(effectiveSyncPhase === "idle" ||
          effectiveSyncPhase === "syncing" ||
          effectiveSyncPhase === "changed") && (
          <div className="flex flex-col sm:flex-row sm:items-center gap-2.5">
            <button
              type="button"
              onClick={onSync}
              disabled={isSyncing || !preview.hasAnyAttempt || preview.summary.maxScore === 0}
              className={
                !preview.hasAnyAttempt || preview.summary.maxScore === 0
                  ? "w-full sm:w-auto inline-flex items-center justify-center gap-2 min-h-[44px] sm:h-10 px-4 rounded-xl bg-zinc-100 dark:bg-zinc-800 text-zinc-500 dark:text-zinc-400 border border-zinc-200 dark:border-zinc-700 text-sm font-medium cursor-not-allowed shrink-0"
                  : "w-full sm:w-auto inline-flex items-center justify-center gap-2 min-h-[44px] sm:h-10 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-700 disabled:opacity-60 text-white text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 shrink-0"
              }
            >
              {isSyncing ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" aria-hidden="true" />
                  <span>Syncing…</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" aria-hidden="true" />
                  <span>
                    {effectiveSyncPhase === "changed" ? "Sync changes" : "Sync to Notion"}
                  </span>
                </>
              )}
            </button>

            <p className="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
              {!preview.hasAnyAttempt
                ? "Nothing to sync yet — answer at least one question"
                : "Your progress is already saved on this computer."}
            </p>
          </div>
        )}
      </div>
    </section>
  );
};
