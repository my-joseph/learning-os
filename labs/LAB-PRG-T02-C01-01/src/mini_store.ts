export type Listener = () => void;
export type StateUpdater<State> = Partial<State> | ((current: State) => Partial<State>);
export type MiniStore<State extends object> = {
  getState: () => State;
  setState: (update: StateUpdater<State>) => void;
  subscribe: (listener: Listener) => () => void;
};

export function createMiniStore<State extends object>(_initialState: State): MiniStore<State> {
  throw new Error("TODO [M1]: Create an isolated external store with readable state and subscriptions.");
}
