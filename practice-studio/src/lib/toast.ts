import type { StatusMessage } from "@/hooks/types";

export const TOAST_DURATION_MS: Record<StatusMessage["type"], number> = {
  pass: 4000,
  warn: 6000,
  fail: 8000,
};

export interface ToastItem {
  id: string;
  message: StatusMessage;
}

/** Returns true when a StatusMessage represents an ongoing operation (ends with "..."). */
export function isInProgressToast(message: StatusMessage): boolean {
  return message.text.trimEnd().endsWith("...");
}

/**
 * Pure auto-dismiss timing rule for status toasts:
 * - Messages ending with "..." (in-progress) stay until replaced (`null`).
 * - `pass`: 4000 ms, `warn`: 6000 ms, `fail`: 8000 ms.
 */
export function getToastDurationMs(message: StatusMessage): number | null {
  if (isInProgressToast(message)) {
    return null;
  }
  return TOAST_DURATION_MS[message.type];
}

/** Append a new toast while replacing any prior in-progress ("...") toast. */
export function enqueueToast(
  queue: ToastItem[],
  message: StatusMessage,
  id: string
): ToastItem[] {
  const withoutInProgress = queue.filter((item) => !isInProgressToast(item.message));
  return [...withoutInProgress, { id, message }];
}

/** Remove a toast by id. */
export function dismissToast(queue: ToastItem[], id: string): ToastItem[] {
  return queue.filter((item) => item.id !== id);
}
