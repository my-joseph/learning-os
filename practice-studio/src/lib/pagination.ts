export type StudyViewMode = "quiz" | "review";

export interface StudyPosition {
  viewMode: StudyViewMode;
  index: number;
}

/**
 * Compute the next or previous position in the study sequence where the
 * Review view is the final step immediately after the last question/milestone.
 */
export function stepStudyPosition(
  current: StudyPosition,
  totalQuestions: number,
  direction: "prev" | "next"
): StudyPosition {
  if (totalQuestions <= 0) {
    return current;
  }

  const lastIndex = totalQuestions - 1;
  const clampedIndex = Math.max(0, Math.min(current.index, lastIndex));

  if (direction === "next") {
    if (current.viewMode === "review") {
      return { viewMode: "review", index: lastIndex };
    }
    if (clampedIndex < lastIndex) {
      return { viewMode: "quiz", index: clampedIndex + 1 };
    }
    return { viewMode: "review", index: lastIndex };
  }

  if (current.viewMode === "review") {
    return { viewMode: "quiz", index: lastIndex };
  }
  if (clampedIndex > 0) {
    return { viewMode: "quiz", index: clampedIndex - 1 };
  }
  return { viewMode: "quiz", index: 0 };
}
