export type EventMap = object;
export type Listener<Payload> = (_payload: Payload) => void;

type Entry = { callback: (value: unknown) => void; active: boolean };
const sharedListeners = new Map<PropertyKey, Entry[]>();

export class TinyEventEmitter<Events extends EventMap> {
  on<EventName extends keyof Events>(event: EventName, listener: Listener<Events[EventName]>): () => void {
    const records = sharedListeners.get(event) ?? [];
    const record: Entry = { callback: listener as (value: unknown) => void, active: true };
    records.push(record);
    sharedListeners.set(event, records);
    return () => { record.active = false; };
  }

  off<EventName extends keyof Events>(event: EventName, listener: Listener<Events[EventName]>): void {
    for (const record of sharedListeners.get(event) ?? []) {
      if (record.callback === listener) record.active = false;
    }
  }

  emit<EventName extends keyof Events>(event: EventName, payload: Events[EventName]): void {
    const records = [...(sharedListeners.get(event) ?? [])];
    for (const record of records) {
      if (record.active) record.callback(payload);
    }
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
