/** Format a review due date as "Tomorrow" or a short local calendar date. */
export function formatReviewDueDate(dateStr?: string | null, today: string = formatLocalDate()): string {
  if (!dateStr || !/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) return "—";
  const [year, month, day] = dateStr.split("-").map(Number);
  const target = new Date(year, month - 1, day);
  const [todayYear, todayMonth, todayDay] = today.split("-").map(Number);
  const current = new Date(todayYear, todayMonth - 1, todayDay);
  const diff = Math.round((target.getTime() - current.getTime()) / 86_400_000);
  if (diff === 1) return "Tomorrow";
  return target.toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" });
}

function formatLocalDate(date: Date = new Date()): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}
