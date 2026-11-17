export interface ListHandle<T> {
  readonly value: T;
}

export interface DoublyLinkedList<T> {
  pushFront(value: T): ListHandle<T>;
  moveToFront(handle: ListHandle<T>): void;
  popBack(): T | undefined;
  remove(handle: ListHandle<T>): boolean;
  size(): number;
  toArray(): T[];
}

export function createDoublyLinkedList<T>(): DoublyLinkedList<T> {
  throw new Error("TODO [M2]: implement encapsulated doubly-linked list");
}
