import { validateCapacity } from "./contracts.ts";
import type { CacheEntry, CacheStats, LRUCache } from "./contracts.ts";
import { createDoublyLinkedList } from "./linkedList.ts";
import type { ListHandle } from "./linkedList.ts";

class LRUCacheImpl<K, V> implements LRUCache<K, V> {
  readonly #maxEntries: number;
  readonly #index = new Map<K, ListHandle<CacheEntry<K, V>>>();
  readonly #order = createDoublyLinkedList<CacheEntry<K, V>>();
  #hits = 0;
  #misses = 0;
  #evictions = 0;

  constructor(capacity: number) {
    this.#maxEntries = validateCapacity(capacity);
  }

  get(key: K): V | undefined {
    const handle = this.#index.get(key);
    if (handle === undefined) {
      this.#misses += 1;
      return undefined;
    }
    this.#hits += 1;
    this.#order.moveToFront(handle);
    return handle.value.value;
  }

  put(key: K, value: V): void {
    const existing = this.#index.get(key);
    if (existing !== undefined) {
      existing.value.value = value;
      this.#order.moveToFront(existing);
      return;
    }
    if (this.#order.size() >= this.#maxEntries) {
      const evicted = this.#order.popBack();
      if (evicted !== undefined) {
        this.#index.delete(evicted.key);
        this.#evictions += 1;
      }
    }
    const handle = this.#order.pushFront({ key, value });
    this.#index.set(key, handle);
  }

  has(key: K): boolean {
    return this.#index.has(key);
  }

  delete(key: K): boolean {
    const handle = this.#index.get(key);
    if (handle === undefined) {
      return false;
    }
    this.#index.delete(key);
    return this.#order.remove(handle);
  }

  size(): number {
    return this.#order.size();
  }

  keysInRecencyOrder(): K[] {
    return this.#order.toArray().map((entry) => entry.key);
  }

  stats(): CacheStats {
    return {
      hits: this.#hits,
      misses: this.#misses,
      evictions: this.#evictions,
      size: this.#order.size(),
    };
  }
}

export function createLRUCache<K, V>(capacity: number): LRUCache<K, V> {
  return new LRUCacheImpl<K, V>(capacity);
}
