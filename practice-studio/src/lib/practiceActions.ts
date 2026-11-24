type PracticeAction =
  | { action: "reset" | "reset-all" | "start-review" | "hint" | "setup" | "steps" }
  | { action: "toggle-mistake"; tag: string }
  | { action: "self-score"; score: number | null }
  | { action: "skip"; input: string; durationMs: number; countHint?: boolean };

interface PracticeActionResult {
  ok?: boolean;
  cycleStartedAt?: string;
  eventId?: string;
  ts?: string;
}

const pending = new Map<string, Promise<PracticeActionResult | null>>();

export async function waitForPracticeAction(drillId: string, qid: string): Promise<void> {
  await pending.get(drillId + "/" + qid);
}

export function sendPracticeAction(
  drillId: string,
  qid: string,
  action: PracticeAction,
  cycleStartedAt?: string | null,
  fetchFn: typeof fetch = fetch
): Promise<PracticeActionResult | null> {
  const key = drillId + "/" + qid;
  const request = (pending.get(key) ?? Promise.resolve(null)).then(async () => {
    try {
      const res = await fetchFn("/api/reveal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ drillId, qid, cycleStartedAt, ...action }),
      });
      return res.ok ? (await res.json()) as PracticeActionResult : null;
    } catch {
      return null;
    }
  });
  pending.set(key, request);
  void request.then(() => {
    if (pending.get(key) === request) pending.delete(key);
  });
  return request;
}
