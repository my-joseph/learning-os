/**
 * Single source of truth for Practice Studio status & warning Tailwind class recipes.
 *
 * Every status-coloured component must import from this module rather than hard-coding
 * Tailwind palette classes (`emerald-*`, `amber-*`, `yellow-*`, `rose-*`).
 *
 * Underlying RGB tokens live in `src/app/globals.css` and are exposed via `tailwind.config.ts`.
 * Changing a status colour means editing one CSS variable in `globals.css`.
 */

export type StatusTone = "correct" | "assisted" | "wrong" | "skipped" | "notTried";

export interface StatusToneRecipe {
  /** CSS colour for chart fills or outlines. */
  chartColor: string;
  /** Filled/outlined circle for Stepper steps (includes group-hover). */
  solidCircle: string;
  /** Compact 16px status mark for SimilarTabStrip (no hover). */
  tabMark: string;
  /** Calm tinted container (bg + border) for result cards and sync banners. */
  softCard: string;
  /** Selected multiple-choice / line-choice option card tint and border. */
  choiceCard: string;
  /** Solid small badge/pill (choice letter badge, line number badge, destructive button). */
  solidBadge: string;
  /** Circular icon container (AnswerResultCard icon circle, DailyReviewPage end icon). */
  iconCircle: string;
  /** Readable status text colour on light/dark neutral surfaces (WCAG AA >= 4.5:1). */
  text: string;
  /** Compact 8–10px indicator dot/square (ReviewItemRow outcome node, DrillSwitcher dot). */
  dot: string;
  /** Active state for ProblemSelfEval score buttons and mistake tag chips. */
  selfScoreActive: string;
  /** Clickable outcome tile in Review & Sync SessionSummaryCard (includes hover). */
  tile: string;
}

interface AccentBorderToneRecipe extends StatusToneRecipe {
  border: string;
}

interface WrongStatusToneRecipe extends AccentBorderToneRecipe {
  /** Subtle framing border (StepRow diverged card border, SyncCard error details pre). */
  borderSoft: string;
  /** Hover text accent (StudioHeader Reset All, StepRow diverged button hover). */
  hoverText: string;
  /** Hover soft border (StepRow diverged button hover). */
  hoverBorderSoft: string;
}

type ReducedStatusToneRecipe = Omit<
  StatusToneRecipe,
  "choiceCard" | "solidBadge" | "selfScoreActive"
>;
type StatusToneRecipes = {
  correct: AccentBorderToneRecipe;
  assisted: StatusToneRecipe;
  wrong: WrongStatusToneRecipe;
  skipped: ReducedStatusToneRecipe;
  notTried: ReducedStatusToneRecipe;
};

export const statusTone: StatusToneRecipes = {
  correct: {
    chartColor: "rgb(var(--status-correct))",
    solidCircle:
      "bg-status-correct border-status-correct text-status-on-correct group-hover:brightness-95 dark:group-hover:brightness-110",
    tabMark: "bg-status-correct text-status-on-correct",
    softCard: "bg-status-correct-soft border border-status-correct/25",
    choiceCard: "bg-status-correct-soft border-status-correct/60",
    solidBadge: "bg-status-correct text-status-on-correct",
    iconCircle: "bg-status-correct/15 text-status-correct-text",
    text: "text-status-correct-text",
    dot: "bg-status-correct",
    selfScoreActive:
      "border-status-correct-text text-status-correct-text font-semibold bg-surface-panel",
    tile: "bg-status-correct text-status-on-correct border-status-correct hover:brightness-95 dark:hover:brightness-110",
    border: "border-status-correct-text",
  },
  assisted: {
    chartColor: "rgb(var(--status-assisted))",
    // Correct with help / after a wrong try / partial: same green as correct, but an
    // OUTLINE with no fill (learner 2026-11-19). Tune via --status-assisted in globals.css.
    solidCircle:
      "bg-transparent border-status-assisted text-status-assisted group-hover:bg-status-assisted/10",
    tabMark: "bg-transparent border-status border-status-assisted text-status-assisted",
    softCard: "bg-transparent border border-status-assisted/50",
    choiceCard: "bg-transparent border-status-assisted",
    solidBadge: "bg-transparent border border-status-assisted text-status-assisted",
    iconCircle: "bg-transparent border-[1.5px] border-status-assisted text-status-assisted",
    text: "text-status-on-assisted",
    dot: "bg-transparent ring-[1.5px] ring-inset ring-status-assisted",
    selfScoreActive:
      "border-status-assisted text-status-on-assisted font-semibold bg-surface-panel",
    tile: "bg-transparent text-status-on-assisted border-status-assisted hover:bg-status-assisted/10",
  },

  wrong: {
    chartColor: "rgb(var(--status-wrong))",
    solidCircle:
      "bg-status-wrong border-status-wrong text-status-on-wrong group-hover:brightness-95 dark:group-hover:brightness-110",
    tabMark: "bg-status-wrong text-status-on-wrong",
    softCard: "bg-status-wrong-soft border border-status-wrong/25",
    choiceCard: "bg-status-wrong-soft border-status-wrong/60",
    solidBadge: "bg-status-wrong text-status-on-wrong",
    iconCircle: "bg-status-wrong/15 text-status-wrong",
    text: "text-status-wrong",
    dot: "bg-status-wrong",
    selfScoreActive:
      "border-status-wrong text-status-wrong font-semibold bg-surface-panel",
    tile: "bg-status-wrong text-status-on-wrong border-status-wrong hover:brightness-95 dark:hover:brightness-110",
    border: "border-status-wrong",
    borderSoft: "border-status-wrong/40",
    hoverText: "hover:text-status-wrong",
    hoverBorderSoft: "hover:border-status-wrong/40",
  },
  skipped: {
    chartColor: "rgb(var(--status-skipped))",
    solidCircle:
      "border-dashed border-status-skipped bg-surface-raised text-muted group-hover:border-muted",
    tabMark: "border-status border-dashed border-status-skipped",
    softCard: "bg-zinc-50 dark:bg-zinc-800/50 border border-zinc-200 dark:border-zinc-700/60",
    iconCircle: "bg-zinc-200/80 dark:bg-zinc-700 text-zinc-600 dark:text-zinc-300",
    text: "text-zinc-500 dark:text-zinc-400",
    dot: "border border-dashed border-status-skipped bg-transparent",
    tile: "bg-transparent hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-600 dark:text-zinc-300 border-dashed border-status-skipped",
  },
  notTried: {
    chartColor: "rgb(var(--status-neutral))",
    solidCircle:
      "border-status-neutral bg-surface-raised text-muted group-hover:border-muted",
    tabMark: "border-status border-status-skipped",
    softCard: "bg-surface-panel border border-zinc-200 dark:border-zinc-800",
    iconCircle: "bg-zinc-100 dark:bg-zinc-800 text-zinc-500 dark:text-zinc-400",
    text: "text-zinc-500 dark:text-zinc-400",
    dot: "bg-status-neutral",
    tile: "bg-surface-panel hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-600 dark:text-zinc-400 border-zinc-200 dark:border-zinc-800",
  },
};

/** Muted untried tab mark for locked ghost tabs in SimilarTabStrip. */
export const MUTED_UNTRIED_TAB_MARK = "border-status border-status-neutral";

/** Destructive confirmation button recipe (ConfirmDialog). */
export const DESTRUCTIVE_BUTTON_CLS =
  "bg-status-wrong text-status-on-wrong hover:brightness-95 dark:hover:brightness-110";

/**
 * Non-status warning recipes (amber).
 * Independent of `statusTone` — strictly for operational warnings, paused timers,
 * pending/warn toasts, and hint left-borders. Never use for answer status.
 */
export const warningTone = {
  /** Warning text or icon colour (QuestionTimer paused, ToastStack pending/warn, SyncCard icon). */
  text: "text-warning",
  /** Warning text link with subtle hover feedback (SessionSummaryCard sync link). */
  textLink: "text-warning hover:opacity-80",
  /** Soft warning banner card (SyncCard degraded state). */
  softCard: "bg-warning-soft border border-warning/25",
  /** Subtle warning framing border (SyncCard degraded details pre). */
  borderSoft: "border-warning/25",
  /** Hint disclosure left-border (ProblemAssistSection). */
  leftBorder: "border-l-2 border-warning-border",
} as const;
