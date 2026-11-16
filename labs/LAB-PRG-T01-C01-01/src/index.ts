export type EventMap = object;
export type Listener<Payload> = (_payload: Payload) => void;

export class TinyEventEmitter<Events extends EventMap> {
  on<EventName extends keyof Events>(_event: EventName, _listener: Listener<Events[EventName]>): () => void {
    throw new Error("TODO [M2]: register a listener");
  }

  off<EventName extends keyof Events>(_event: EventName, _listener: Listener<Events[EventName]>): void {
    throw new Error("TODO [M2]: remove a listener");
  }

  emit<EventName extends keyof Events>(_event: EventName, _payload: Events[EventName]): void {
    throw new Error("TODO [M2]: deliver an event");
  }
}

export type TaskOutcome<Result> = { status: "fulfilled"; value: Result } | { status: "rejected"; reason: unknown };

export class PromisePool {
  constructor(_concurrency: number) {
    throw new Error("TODO [M3]: configure task concurrency");
  }

  run<Result>(_tasks: Array<() => Promise<Result> | Result>, _signal?: AbortSignal): Promise<Array<TaskOutcome<Result>>> {
    throw new Error("TODO [M3]: coordinate task execution");
  }
}
