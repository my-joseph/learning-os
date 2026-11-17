import type { LRUCache } from "./contracts.ts";

export function createLRUCache<K, V>(_capacity: number): LRUCache<K, V> {
  throw new Error("TODO [M3]: implement O(1) LRU cache with Map and DoublyLinkedList");
}
