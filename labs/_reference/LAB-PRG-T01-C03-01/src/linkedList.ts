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

class InternalNode<T> {
  readonly value: T;
  prev: InternalNode<T> | null = null;
  next: InternalNode<T> | null = null;
  attached = false;

  constructor(value: T) {
    this.value = value;
  }

  attachAfterClear(oldHead: InternalNode<T> | null): void {
    this.prev = null;
    this.next = oldHead;
    this.attached = true;
  }

  setPrev(node: InternalNode<T> | null): void {
    this.prev = node;
  }

  setNext(node: InternalNode<T> | null): void {
    this.next = node;
  }

  reset(): void {
    this.prev = null;
    this.next = null;
    this.attached = false;
  }
}

class LinkedListImpl<T> implements DoublyLinkedList<T> {
  #head: InternalNode<T> | null = null;
  #tail: InternalNode<T> | null = null;
  #count = 0;
  readonly #nodeByHandle = new WeakMap<ListHandle<T>, InternalNode<T>>();

  #attachFront(node: InternalNode<T>): void {
    const oldHead = this.#head;
    node.attachAfterClear(oldHead);
    if (oldHead !== null) {
      oldHead.setPrev(node);
    }
    this.#head = node;
    if (this.#tail === null) {
      this.#tail = node;
    }
    this.#count += 1;
  }

  #detachNode(node: InternalNode<T>): void {
    if (node.prev !== null) {
      node.prev.setNext(node.next);
    } else {
      this.#head = node.next;
    }
    if (node.next !== null) {
      node.next.setPrev(node.prev);
    } else {
      this.#tail = node.prev;
    }
    node.reset();
    this.#count -= 1;
  }

  pushFront(value: T): ListHandle<T> {
    const node = new InternalNode(value);
    const handle: ListHandle<T> = { value };
    this.#nodeByHandle.set(handle, node);
    this.#attachFront(node);
    return handle;
  }

  moveToFront(handle: ListHandle<T>): void {
    const node = this.#nodeByHandle.get(handle);
    if (node === undefined || !node.attached || this.#head === node) {
      return;
    }
    this.#detachNode(node);
    this.#attachFront(node);
  }

  popBack(): T | undefined {
    const victim = this.#tail;
    if (victim === null) {
      return undefined;
    }
    this.#detachNode(victim);
    return victim.value;
  }

  remove(handle: ListHandle<T>): boolean {
    const node = this.#nodeByHandle.get(handle);
    if (node === undefined || !node.attached) {
      return false;
    }
    this.#detachNode(node);
    return true;
  }

  size(): number {
    return this.#count;
  }

  toArray(): T[] {
    const result: T[] = [];
    let current = this.#head;
    while (current !== null) {
      result.push(current.value);
      current = current.next;
    }
    return result;
  }
}

export function createDoublyLinkedList<T>(): DoublyLinkedList<T> {
  return new LinkedListImpl<T>();
}
