import { useSyncExternalStore } from "react";
import type { MiniStore } from "./mini_store.ts";

export function useStore<State extends object, Selection>(
  store: MiniStore<State>,
  selector: (state: State) => Selection
): Selection {
  return useSyncExternalStore(
    store.subscribe,
    () => selector(store.getState()),
    () => selector(store.getState())
  );
}
