"use client";

import React from "react";
import { ArrowDown, ArrowLeft, ArrowRight, BarChart3, Gauge } from "lucide-react";
import {
  Bar,
  BarChart,
  Cell,
  Customized,
  Pie,
  PieChart,
  XAxis,
  YAxis,
} from "recharts";
import type { DrillDocument, Problem } from "@/types/drill";
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import {
  classifyReviewOutcome,
  formatDuration,
  getQuestionLabel,
  getReviewOutcomeMeta,
  type GroupedReviewSummary,
  type ReviewOutcome,
} from "@/lib/reviewOutcome";
import { countRightItems, type SessionPattern } from "@/lib/reviewRow";
import { scoreProblem } from "@/lib/scoring";
import { formatSyncTimestamp } from "@/lib/sessionSummary";
import { statusTone, warningTone } from "@/lib/statusTone";
import { plainTitle } from "@/lib/titleText";

export type EffectiveSyncPhase =
  | "idle"
  | "syncing"
  | "synced"
  | "changed"
  | "degraded"
  | "error"
  | "offline"
  | "dryRun";

export interface SessionSummaryCardProps {
  drill: DrillDocument;
  groups: GroupedReviewSummary<Problem>;
  durationMs: number;
  pattern: SessionPattern | null;
  effectiveSyncPhase: EffectiveSyncPhase;
  syncedAt?: string | null;
  isLab: boolean;
  isCode: boolean;
  hasAnyAttempt: boolean;
  onJumpToRow: (probId: string, inCorrectGroup: boolean) => void;
  onScrollToSync: () => void;
  onBackToQuiz: () => void;
  onStartFirst: () => void;
  defaultView?: "gauge" | "bars";
}

const SCORE_VIEW_STORAGE_KEY = "review-sync-score-view";

function formatPoints(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

const SCORE_CHART_CONFIG = {
  wrong: { label: "Wrong", color: "rgb(var(--status-wrong))" },
  wrongMuted: { label: "Needs review", color: "rgb(var(--status-wrong) / 0.45)" },
  accent: { label: "In progress", color: "rgb(var(--accent))" },
  correct: { label: "Strong", color: "rgb(var(--status-correct))" },
  neutral: { label: "Not answered", color: "rgb(var(--status-neutral))" },
  assisted: { label: "Assisted / partial", color: "rgb(var(--status-assisted))" },
  skipped: { label: "Skipped", color: "rgb(var(--status-skipped))" },
};

const SCORE_BANDS = ["wrong", "wrongMuted", "accent", "correct"] as const;

function scoreBandIndex(ratio: number): number {
  return Math.min(SCORE_BANDS.length - 1, Math.floor(Math.max(0, ratio) * SCORE_BANDS.length));
}

function scoreBandTextClass(ratio: number): string {
  const band = SCORE_BANDS[scoreBandIndex(ratio)];
  if (band === "correct") return statusTone.correct.text;
  if (band === "accent") return "text-accent";
  if (band === "wrongMuted") return "text-status-wrong/70";
  return statusTone.wrong.text;
}

function scoreColorVariable(ratio: number): string {
  return `var(--color-${SCORE_BANDS[scoreBandIndex(ratio)]})`;
}

interface ScorePointerProps {
  width?: number;
  height?: number;
  ratio: number;
  color: string;
}

const ScorePointer: React.FC<ScorePointerProps> = ({ width = 320, height = 200, ratio, color }) => {
  const radius = Math.min(width, height) * 0.39;
  const angle = Math.PI * (1 - Math.max(0, Math.min(1, ratio)));
  const cx = width / 2 + radius * Math.cos(angle);
  const cy = height * 0.78 - radius * Math.sin(angle);
  return (
    <circle
      data-score-marker="true"
      cx={cx}
      cy={cy}
      r={8}
      className="fill-white dark:fill-zinc-900"
      stroke={color}
      strokeWidth={4}
    />
  );
};

interface ScoreBarDatum {
  id: string;
  label: string;
  score: number;
  displayScore: number;
  outcome: ReviewOutcome;
  inCorrectGroup: boolean;
  color: string;
  status: string;
}

function scoreBarColor(outcome: ReviewOutcome): string {
  switch (outcome) {
    case "correct_first":
      return "var(--color-correct)";
    case "assisted_or_partial":
      return "var(--color-assisted)";
    case "wrong":
      return "var(--color-wrong)";
    case "skipped":
      return "var(--color-skipped)";
    default:
      return "var(--color-neutral)";
  }
}

const TILE_COLORS: Record<ReviewOutcome, string> = {
  correct_first: statusTone.correct.tile,
  assisted_or_partial: statusTone.assisted.tile,
  wrong: statusTone.wrong.tile,
  skipped: statusTone.skipped.tile,
  awaiting_review:
    "bg-zinc-50 hover:bg-zinc-100 dark:bg-zinc-950 dark:hover:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border-zinc-400 dark:border-zinc-500",
  unanswered: statusTone.notTried.tile,
};

function syncStatusLinkText(
  phase: EffectiveSyncPhase,
  syncedAt: string | null | undefined,
  isLab: boolean
): { label: string; showArrow: boolean; toneClass: string } {
  if (isLab) {
    return {
      label: "Submit from terminal",
      showArrow: true,
      toneClass: "text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100",
    };
  }
  switch (phase) {
    case "syncing":
      return {
        label: "Syncing…",
        showArrow: false,
        toneClass: "text-zinc-500 dark:text-zinc-400",
      };
    case "synced": {
      const { relativeLabel } = formatSyncTimestamp(syncedAt);
      return {
        label: relativeLabel ? `Synced ${relativeLabel}` : "Synced",
        showArrow: false,
        toneClass: `${statusTone.correct.text} hover:opacity-80`,
      };
    }
    case "changed":
      return {
        label: "Changed since sync",
        showArrow: true,
        toneClass: warningTone.textLink,
      };
    case "degraded":
      return {
        label: "Saved locally · retry",
        showArrow: true,
        toneClass: warningTone.textLink,
      };
    case "error":
    case "offline":
      return {
        label: phase === "offline" ? "Offline · retry" : "Couldn't sync",
        showArrow: true,
        toneClass: `${statusTone.wrong.text} hover:opacity-80`,
      };
    case "dryRun":
      return {
        label: "Not written (dry run)",
        showArrow: true,
        toneClass: "text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100",
      };
    default:
      return {
        label: "Not synced yet",
        showArrow: true,
        toneClass: "text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100",
      };
  }
}

/** Section A: Session summary card with verdict sentence, labelled outcome strip, pattern line, and sync status link. */
export const SessionSummaryCard: React.FC<SessionSummaryCardProps> = ({
  drill,
  groups,
  durationMs,
  pattern,
  effectiveSyncPhase,
  syncedAt,
  isLab,
  isCode,
  hasAnyAttempt,
  onJumpToRow,
  onScrollToSync,
  onBackToQuiz,
  onStartFirst,
  defaultView,
}) => {
  const [scoreView, setScoreView] = React.useState<"gauge" | "bars">(defaultView ?? "gauge");
  const [viewReady, setViewReady] = React.useState(defaultView !== undefined);
  React.useEffect(() => {
    if (defaultView !== undefined) {
      setScoreView(defaultView);
      setViewReady(true);
      return;
    }
    try {
      const storedView = window.localStorage.getItem(SCORE_VIEW_STORAGE_KEY);
      if (storedView === "gauge" || storedView === "bars") setScoreView(storedView);
    } catch {
      // Storage can be unavailable in private browsing or restricted test environments.
    }
    setViewReady(true);
  }, [defaultView]);
  React.useEffect(() => {
    if (!viewReady || defaultView !== undefined) return;
    try {
      window.localStorage.setItem(SCORE_VIEW_STORAGE_KEY, scoreView);
    } catch {
      // Keep the view usable when storage is unavailable.
    }
  }, [defaultView, scoreView, viewReady]);
  const drillTitle = plainTitle(drill.unitTitle) || drill.unitCode;
  const totalCount = drill.problems.length;
  const rightCount = countRightItems(drill.problems);
  const points = drill.problems.reduce(
    (sum, problem) => sum + (scoreProblem(problem.state, { isPrg: isCode || isLab }).score ?? 0),
    0
  );
  const firstTryCount = groups.firstTryCount;
  const allFirstTry = totalCount > 0 && firstTryCount === totalCount;
  const scoreRatio = totalCount > 0 ? Math.max(0, Math.min(1, points / totalCount)) : 0;
  const scoreTone = hasAnyAttempt ? scoreBandTextClass(scoreRatio) : statusTone.notTried.text;
  const scoreStatus = !hasAnyAttempt
    ? "Not started"
    : allFirstTry
      ? "All first-try"
      : rightCount === totalCount
        ? "Strong"
        : rightCount > 0
          ? "In progress"
          : "Needs review";
  const formattedTime = durationMs > 0 ? formatDuration(durationMs) : null;
  const statusLink = syncStatusLinkText(effectiveSyncPhase, syncedAt, isLab);

  const firstLabel =
    totalCount > 0 ? getQuestionLabel(drill.problems[0].id, 0, isLab) : isLab ? "M1" : "Q1";
  const backLabel = isLab
    ? "Back to milestones"
    : isCode
    ? "Back to problems"
    : "Back to questions";
  const outcomeGroupLabel = isLab
    ? "Milestone outcomes"
    : isCode
    ? "Problem outcomes"
    : "Question outcomes";

  return (
    <section
      aria-labelledby="review-sync-heading"
      className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-4 sm:p-6 space-y-4"
    >
      {/* Top row: h1 title + right-aligned quiet sync status link */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2">
        <div className="min-w-0 space-y-0.5">
          <h1
            id="review-sync-heading"
            className="text-lg font-semibold text-zinc-900 dark:text-zinc-100 tracking-tight break-words"
          >
            {drillTitle}
          </h1>
          <p className="font-display text-xs text-zinc-500 dark:text-zinc-400">
            {drill.unitCode}
          </p>
        </div>

        <button
          type="button"
          onClick={onScrollToSync}
          className={`self-start sm:self-auto inline-flex items-center gap-1 min-h-[44px] sm:min-h-[32px] text-xs transition-colors rounded-md py-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 shrink-0 ${statusLink.toneClass}`}
        >
          <span className="font-display tabular-nums">{statusLink.label}</span>
          {statusLink.showArrow && <ArrowDown className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />}
        </button>
      </div>

      <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50/70 dark:bg-zinc-950/40 p-3 sm:p-4 space-y-3">
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs text-zinc-500 dark:text-zinc-400">Session score</p>
          <div role="group" aria-label="Score view" className="inline-flex rounded-lg border border-zinc-200 dark:border-zinc-700 p-0.5">
            {(["gauge", "bars"] as const).map((view) => {
              const Icon = view === "gauge" ? Gauge : BarChart3;
              const label = view === "gauge" ? "Gauge" : "Bars";
              return (
                <button
                  key={view}
                  type="button"
                  aria-pressed={scoreView === view}
                  onClick={() => setScoreView(view)}
                  className={`inline-flex items-center gap-1.5 min-h-[36px] px-2.5 rounded-md text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 ${scoreView === view ? "bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 shadow-sm" : "text-zinc-500 dark:text-zinc-400 hover:text-zinc-800 dark:hover:text-zinc-200"}`}
                >
                  <Icon className="w-3.5 h-3.5" aria-hidden="true" />
                  {label}
                </button>
              );
            })}
          </div>
        </div>

        {scoreView === "gauge" ? (
          <div className="grid grid-cols-1 sm:grid-cols-[minmax(0,1fr)_auto] items-center gap-3">
            <div className="relative mx-auto w-full max-w-[320px]" aria-label={`${formatPoints(points)} earned points`}>
              <ChartContainer
                config={SCORE_CHART_CONFIG}
                className="w-full"
                aspectRatio={1.6}
                initialDimension={{ width: 320, height: 200 }}
                role="img"
                aria-label="Segmented score gauge"
              >
                <PieChart>
                  <Pie
                    data={hasAnyAttempt
                      ? SCORE_BANDS.map((band) => ({ name: band, value: 1 }))
                      : [{ name: "neutral", value: 1 }]}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="78%"
                    innerRadius="62%"
                    outerRadius="78%"
                    startAngle={180}
                    endAngle={0}
                    paddingAngle={hasAnyAttempt ? 5 : 0}
                    cornerRadius={8}
                    stroke="none"
                    isAnimationActive={false}
                  >
                    {(hasAnyAttempt ? SCORE_BANDS : ["neutral"] as const).map((band) => (
                      <Cell key={band} fill={`var(--color-${band})`} />
                    ))}
                  </Pie>
                  {hasAnyAttempt && (
                    <Customized
                      component={
                        <ScorePointer ratio={scoreRatio} color={scoreColorVariable(scoreRatio)} />
                      }
                    />
                  )}
                </PieChart>
              </ChartContainer>
              <div className="pointer-events-none absolute inset-x-0 bottom-1 text-center">
                <div className={`font-display font-bold tabular-nums text-4xl leading-none ${scoreTone}`}>
                  {formatPoints(points)}
                </div>
                <div className="mt-1 text-sm text-zinc-600 dark:text-zinc-300">
                  {hasAnyAttempt ? "Your total score" : "Nothing answered yet"}
                </div>
              </div>
            </div>
            <div className="flex sm:flex-col items-center sm:items-end justify-between sm:justify-center gap-1 text-sm text-zinc-600 dark:text-zinc-300">
              <span className="font-semibold text-zinc-800 dark:text-zinc-200">{scoreStatus}</span>
              <span>{hasAnyAttempt ? `${rightCount} of ${totalCount} right` : "Ready when you are"}</span>
              {allFirstTry && <span>All {totalCount} right on the first try</span>}
              {!allFirstTry && firstTryCount > 0 && <span>{firstTryCount} on the first try</span>}
              {formattedTime && <span className="font-display tabular-nums">{formattedTime}</span>}
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="flex items-baseline justify-end gap-3">
              <span className={`font-display font-bold tabular-nums text-2xl ${scoreTone}`}>{formatPoints(points)}</span>
              <span className="text-xs text-zinc-500 dark:text-zinc-400">{formattedTime ?? "Your total score"}</span>
            </div>
            <ChartContainer
              config={SCORE_CHART_CONFIG}
              className="w-full min-w-0"
              aspectRatio={2.4}
              initialDimension={{ width: 480, height: 200 }}
              role="img"
              aria-label={isLab ? "Score by milestone" : isCode ? "Score by problem" : "Score by question"}
            >
              <BarChart
                data={drill.problems.map((prob, idx): ScoreBarDatum => {
                const result = scoreProblem(prob.state, { isPrg: isCode || isLab });
                const outcome = classifyReviewOutcome(prob.state);
                const earned = result.score ?? 0;
                const label = getQuestionLabel(prob.id, idx, isLab);
                const meta = getReviewOutcomeMeta(outcome).label.toLowerCase();
                return {
                  id: prob.id,
                  label,
                  score: earned,
                  displayScore: Math.max(earned, 0.12),
                  outcome,
                  inCorrectGroup: outcome === "correct_first",
                  color: scoreBarColor(outcome),
                  status: meta,
                };
              })}
                margin={{ top: 12, right: 12, bottom: 0, left: 0 }}
                barCategoryGap="24%"
              >
                <XAxis
                  dataKey="label"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: "rgb(var(--status-neutral))", fontSize: 11 }}
                  interval={0}
                />
                <YAxis hide domain={[0, 1]} />
                <ChartTooltip
                  cursor={{ fill: "rgb(var(--status-neutral) / 0.16)" }}
                  content={
                    <ChartTooltipContent
                      formatter={(_value, _name, item) => {
                        const datum = item.payload as ScoreBarDatum | undefined;
                        return datum
                          ? `${formatPoints(datum.score)} ${datum.score === 1 ? "pt" : "pts"} · ${datum.status}`
                          : "0 pts";
                      }}
                    />
                  }
                />
                <Bar
                  dataKey="displayScore"
                  name="Earned score"
                  radius={[8, 8, 4, 4]}
                  isAnimationActive={false}
                  onClick={(entry: ScoreBarDatum) => onJumpToRow(entry.id, entry.inCorrectGroup)}
                  cursor="pointer"
                >
                  {drill.problems.map((prob) => {
                    const outcome = classifyReviewOutcome(prob.state);
                    return <Cell key={prob.id} fill={scoreBarColor(outcome)} />;
                  })}
                </Bar>
              </BarChart>
            </ChartContainer>
          </div>
        )}
      </div>

      {/* Labelled outcome strip (no legend — tooltips + aria-labels + rows carry the meaning) */}
      {totalCount > 0 && (
        <div
          role="group"
          aria-label={outcomeGroupLabel}
          className="flex flex-wrap items-center gap-1.5"
        >
          {drill.problems.map((prob, idx) => {
            const outcome = classifyReviewOutcome(prob.state);
            const meta = getReviewOutcomeMeta(outcome);
            const qLabel = getQuestionLabel(prob.id, idx, isLab);
            const tooltip = `${qLabel} · ${meta.label.toLowerCase()}`;
            return (
              <button
                key={prob.id}
                type="button"
                onClick={() => onJumpToRow(prob.id, outcome === "correct_first")}
                title={tooltip}
                aria-label={tooltip}
                className={`min-w-[44px] sm:min-w-[36px] min-h-[44px] sm:min-h-[32px] px-2 rounded-lg border font-display text-xs font-semibold tabular-nums inline-flex items-center justify-center transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 ${TILE_COLORS[outcome]}`}
              >
                {qLabel}
              </button>
            );
          })}
        </div>
      )}

      {/* Pattern line — only when a trap or mistake tag repeats >= 2 times */}
      {pattern && (
        <p className="text-sm text-zinc-700 dark:text-zinc-300 leading-snug">
          <span>
            {pattern.kind === "trap" ? "Same trap " : "Same mistake "}
            {pattern.count === 2 ? (
              "twice"
            ) : (
              <span className="font-display tabular-nums">{pattern.count}×</span>
            )}
            :{" "}
          </span>
          <span className="font-semibold text-zinc-900 dark:text-zinc-100">
            {pattern.label}
          </span>{" "}
          <span className="font-display text-xs text-zinc-500 dark:text-zinc-400">
            ({pattern.itemLabels.join(", ")})
          </span>
        </p>
      )}

      {/* Footer row: Start Q1 primary when nothing attempted (drills), plus quiet Back link */}
      <div className="pt-2 border-t border-zinc-200/80 dark:border-zinc-800/80 flex flex-wrap items-center justify-between gap-3">
        <button
          type="button"
          onClick={onBackToQuiz}
          className="inline-flex items-center gap-1.5 min-h-[44px] sm:min-h-[32px] px-1 rounded-lg text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
        >
          <ArrowLeft className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
          <span>{backLabel}</span>
        </button>

        {!hasAnyAttempt && totalCount > 0 && (
          <button
            type="button"
            onClick={onStartFirst}
            className={
              isLab
                ? "inline-flex items-center justify-center gap-1.5 min-h-[44px] sm:min-h-[36px] px-3.5 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200 hover:border-zinc-300 dark:hover:border-zinc-700 text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
                : "inline-flex items-center justify-center gap-1.5 min-h-[44px] sm:min-h-[36px] px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-700 text-white text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
            }
          >
            <span>Start {firstLabel}</span>
            <ArrowRight className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
          </button>
        )}
      </div>
    </section>
  );
};
