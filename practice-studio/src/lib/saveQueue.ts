import type { DrillDocument } from "../types/drill";

export const DEFAULT_SAVE_TIMEOUT_MS = 15_000;

export interface SaveQueueOptions {
  fetchFn?: typeof fetch;
  debounceMs?: number;
  timeoutMs?: number;
}

export interface SaveQueue {
  /** Schedule a debounced autosave; latest document always wins. */
  enqueue(doc: DrillDocument): void;
  /**
   * Persist immediately through the serialized save queue, cancelling any pending
   * debounce timer so the same document is never posted twice. Resolves once the
   * POST containing this version (or a newer superseding document) has finished.
   */
  saveNow(doc?: DrillDocument): Promise<boolean>;
  /** Flush any pending debounced save and wait until all in-flight saves finish. */
  flush(): Promise<boolean>;
  /** Cancel any pending debounce timer without firing a network request. */
  dispose(): void;
}

interface Waiter {
  targetVersion: number;
  resolve: (ok: boolean) => void;
}

/**
 * Single ordered save queue for `/api/save-state`:
 * - Serializes POST requests so an earlier slow request can never overtake a newer one.
 * - Coalesces intermediate snapshots so the latest document always wins.
 * - Flushes the previous drill immediately if a different `drillId` is enqueued.
 * - Lets callers (e.g. reveal or Notion sync) await the exact save that unlocks their next step.
 */
export function createSaveQueue(options: SaveQueueOptions = {}): SaveQueue {
  const fetchFn = options.fetchFn ?? fetch;
  const debounceMs = options.debounceMs ?? 400;
  const timeoutMs = options.timeoutMs ?? DEFAULT_SAVE_TIMEOUT_MS;

  let timer: ReturnType<typeof setTimeout> | null = null;
  let pendingDoc: DrillDocument | null = null;
  const switchedDocs: DrillDocument[] = [];
  let version = 0;
  let completedVersion = 0;
  let lastOk = true;
  let draining: Promise<void> | null = null;
  const waiters: Waiter[] = [];

  const clearTimer = () => {
    if (timer !== null) {
      clearTimeout(timer);
      timer = null;
    }
  };

  const resolveReadyWaiters = () => {
    for (let i = waiters.length - 1; i >= 0; i -= 1) {
      if (waiters[i].targetVersion <= completedVersion) {
        const w = waiters[i];
        waiters.splice(i, 1);
        w.resolve(lastOk);
      }
    }
  };

  const postDoc = async (doc: DrillDocument): Promise<boolean> => {
    const controller = typeof AbortController !== "undefined" ? new AbortController() : null;
    let timeoutHandle: ReturnType<typeof setTimeout> | null = null;
    try {
      const fetchPromise = fetchFn("/api/save-state", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(doc),
        ...(controller ? { signal: controller.signal } : {}),
      });
      if (typeof timeoutMs === "number" && Number.isFinite(timeoutMs) && timeoutMs > 0) {
        const timeoutPromise = new Promise<never>((_, reject) => {
          timeoutHandle = setTimeout(() => {
            timeoutHandle = null;
            controller?.abort();
            reject(new Error("Save timed out"));
          }, timeoutMs);
        });
        fetchPromise.catch(() => {});
        const res = await Promise.race([fetchPromise, timeoutPromise]);
        return res.ok;
      }
      const res = await fetchPromise;
      return res.ok;
    } catch {
      return false;
    } finally {
      if (timeoutHandle !== null) {
        clearTimeout(timeoutHandle);
        timeoutHandle = null;
      }
    }
  };

  const startDrain = (): Promise<void> => {
    if (draining) return draining;
    draining = (async () => {
      try {
        while (switchedDocs.length > 0 || pendingDoc !== null) {
          if (switchedDocs.length > 0) {
            const prevDrillDoc = switchedDocs.shift()!;
            await postDoc(prevDrillDoc);
            continue;
          }
          const docToSave = pendingDoc!;
          const docVersion = version;
          pendingDoc = null;
          const ok = await postDoc(docToSave);
          completedVersion = Math.max(completedVersion, docVersion);
          lastOk = ok;
          resolveReadyWaiters();
        }
      } finally {
        draining = null;
        if (switchedDocs.length > 0) {
          void startDrain();
        }
      }
    })();
    return draining;
  };

  const queueDoc = (doc: DrillDocument) => {
    if (pendingDoc && pendingDoc.drillId !== doc.drillId) {
      switchedDocs.push(pendingDoc);
      pendingDoc = null;
      clearTimer();
      void startDrain();
    }
    pendingDoc = doc;
    version += 1;
  };

  const enqueue = (doc: DrillDocument) => {
    queueDoc(doc);
    clearTimer();
    timer = setTimeout(() => {
      timer = null;
      void startDrain();
    }, debounceMs);
  };

  const saveNow = (doc?: DrillDocument): Promise<boolean> => {
    if (doc) {
      queueDoc(doc);
    }
    clearTimer();
    const targetVersion = version;
    if (
      targetVersion <= completedVersion &&
      !draining &&
      switchedDocs.length === 0 &&
      pendingDoc === null
    ) {
      return Promise.resolve(lastOk);
    }
    return new Promise<boolean>((resolve) => {
      waiters.push({ targetVersion, resolve });
      void startDrain();
    });
  };

  const flush = (): Promise<boolean> => saveNow();

  const dispose = () => {
    clearTimer();
  };

  return {
    enqueue,
    saveNow,
    flush,
    dispose,
  };
}
