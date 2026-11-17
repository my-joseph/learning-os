export interface StatusMessage {
  text: string;
  type: "pass" | "warn" | "fail";
}

export type DrillFilter = "ALL" | "UNFINISHED" | "GRADED";

export type ViewMode = "quiz" | "review";

export type PracticeStatusOverride = "Graded" | "Needs Retry" | null;
