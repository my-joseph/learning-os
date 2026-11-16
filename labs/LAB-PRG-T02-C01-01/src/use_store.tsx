import { useSyncExternalStore } from "react";
import type { MiniStore } from "./mini_store.ts";

export function useStore<State extends object, Selection>(
  _store: MiniStore<State>,
  _selector: (state: State) => Selection
): Selection {
  void useSyncExternalStore;
  throw new Error("TODO [M3]: Subscribe to the selected external-store snapshot.");
}
