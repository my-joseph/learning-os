export type EventMap = object;
export type Listener<Payload> = (payload: Payload) => void;

export class TinyEventEmitter<Events extends EventMap> {
  private readonly listeners = new Map<keyof Events, Set<Listener<unknown>>>();

  on<EventName extends keyof Events>(event: EventName, listener: Listener<Events[EventName]>): () => void {
    const eventListeners = this.listeners.get(event) ?? new Set<Listener<unknown>>();
    eventListeners.add(listener as Listener<unknown>);
    this.listeners.set(event, eventListeners);
    return () => this.off(event, listener);
  }

  off<EventName extends keyof Events>(event: EventName, listener: Listener<Events[EventName]>): void {
    const eventListeners = this.listeners.get(event);
    eventListeners?.delete(listener as Listener<unknown>);
    if (eventListeners?.size === 0) this.listeners.delete(event);
  }

  emit<EventName extends keyof Events>(event: EventName, payload: Events[EventName]): void {
    const eventListeners = this.listeners.get(event);
    if (!eventListeners) return;
    for (const listener of [...eventListeners]) listener(payload);
  }
}

export type TaskOutcome<Result> = { status: "fulfilled"; value: Result } | { status: "rejected"; reason: unknown };

function cancellationReason(signal: AbortSignal): unknown {
  return signal.reason ?? new DOMException("The operation was aborted", "AbortError");
}

function rejectedOutcomes<Result>(count: number, reason: unknown): Array<TaskOutcome<Result>> {
  return Array.from({ length: count }, () => ({ status: "rejected", reason }));
}

export class PromisePool {
  private readonly concurrency: number;

  constructor(concurrency: number) {
    if (!Number.isInteger(concurrency) || concurrency < 1) {
      throw new RangeError("Concurrency must be a positive integer");
    }
    this.concurrency = concurrency;
  }

  async run<Result>(tasks: Array<() => Promise<Result> | Result>, signal?: AbortSignal): Promise<Array<TaskOutcome<Result>>> {
    if (tasks.length === 0) return [];
    if (signal?.aborted) return rejectedOutcomes(tasks.length, cancellationReason(signal));

    const outcomes = new Array<TaskOutcome<Result>>(tasks.length);
    let nextTask = 0;
    let cancelled = false;
    const markCancelled = () => { cancelled = true; };
    signal?.addEventListener("abort", markCancelled, { once: true });

    const runWorker = async () => {
      while (nextTask < tasks.length) {
        if (cancelled || signal?.aborted) {
          const remaining = rejectedOutcomes<Result>(tasks.length - nextTask, cancellationReason(signal!));
          outcomes.splice(nextTask, remaining.length, ...remaining);
          nextTask = tasks.length;
          return;
        }
        const taskIndex = nextTask;
        nextTask += 1;
        try {
          const value = await tasks[taskIndex]!();
          outcomes[taskIndex] = { status: "fulfilled", value };
        } catch (reason) {
          outcomes[taskIndex] = { status: "rejected", reason };
        }
      }
    };

    try {
      await Promise.all(Array.from({ length: Math.min(this.concurrency, tasks.length) }, () => runWorker()));
      return outcomes;
    } finally {
      signal?.removeEventListener("abort", markCancelled);
    }
  }
}
