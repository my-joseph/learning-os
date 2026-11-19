export interface StatusMessage {
  text: string;
  type: "pass" | "warn" | "fail";
}

export type DrillFilter = "ALL" | "UNFINISHED" | "GRADED";

export type ViewMode = "quiz" | "review";

export type PracticeStatusOverride = "Graded" | "Needs Retry" | null;

/** Options passed from a Skip button to the drill skip handler. */
export type SkipOptions = {
  /** The skip auto-opens the hint; count it in the same save as the skip. */
  countHint?: boolean;
};
