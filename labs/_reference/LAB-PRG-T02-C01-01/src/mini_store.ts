export type Listener = () => void;
export type StateUpdater<State> = Partial<State> | ((current: State) => Partial<State>);
export type MiniStore<State extends object> = {
  getState: () => State;
  setState: (update: StateUpdater<State>) => void;
  subscribe: (listener: Listener) => () => void;
};

export function createMiniStore<State extends object>(initialState: State): MiniStore<State> {
  let state = { ...initialState };
  const listeners = new Set<Listener>();

  function getState(): State {
    return state;
  }

  function setState(update: StateUpdater<State>): void {
    const patch = typeof update === "function" ? update(state) : update;
    const keys = Object.keys(patch) as Array<keyof State>;
    if (keys.every((key) => Object.is(state[key], patch[key]))) return;
    state = { ...state, ...patch };
    for (const listener of [...listeners]) listener();
  }

  function subscribe(listener: Listener): () => void {
    listeners.add(listener);
    return () => { listeners.delete(listener); };
  }

  return { getState, setState, subscribe };
}
