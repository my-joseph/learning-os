import type { ProblemState, TestRunReport } from "../types/drill";
import { scoreProblem } from "./scoring";

export function isContextSlug(context?: string): boolean {
  return Boolean(context && /^[a-z0-9]+(?:_[a-z0-9]+)+$/.test(context));
}

export function getPrgScore(
  report: TestRunReport | null,
  reviews: ProblemState["reviews"],
  state?: Partial<ProblemState> | null
): number | null {
  return scoreProblem(
    {
      ...state,
      lastTestReport: report,
      reviews: reviews ?? state?.reviews ?? [],
    },
    { isPrg: true, ignoreStateScore: true }
  ).score;
}

export function getReviewRequest(drillId: string, questionId: string): string {
  return `ตรวจโค้ด ${drillId} ${questionId}`;
}

export function hasCheckpointHint(hint?: string): boolean {
  return Boolean(hint?.trim());
}

export function resolveTheme(saved: string | null, prefersDark: boolean): "light" | "dark" {
  if (saved === "light" || saved === "dark") return saved;
  return prefersDark ? "dark" : "light";
}

export const THEME_INIT_SCRIPT = `
  (function() {
    try {
      var saved = localStorage.getItem('practice_studio_theme');
      var theme = (${resolveTheme.toString()})(saved, window.matchMedia('(prefers-color-scheme: dark)').matches);
      document.documentElement.classList.toggle('light', theme === 'light');
      document.documentElement.classList.toggle('dark', theme === 'dark');
    } catch (e) {}
  })();
`;
