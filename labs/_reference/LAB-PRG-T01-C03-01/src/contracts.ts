export class CacheConfigError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "CacheConfigError";
  }
}

export interface CacheEntry<K, V> {
  readonly key: K;
  value: V;
}

export interface CacheStats {
  readonly hits: number;
  readonly misses: number;
  readonly evictions: number;
  readonly size: number;
}

export interface LRUCache<K, V> {
  get(key: K): V | undefined;
  put(key: K, value: V): void;
  has(key: K): boolean;
  delete(key: K): boolean;
  size(): number;
  keysInRecencyOrder(): K[];
  stats(): CacheStats;
}

export interface TreeNode<T> {
  readonly id: string;
  readonly label: string;
  readonly tags: readonly string[];
  readonly children: readonly TreeNode<T>[];
  readonly data: T;
}

export interface TreeIndex<T> {
  findById(id: string): TreeNode<T> | null;
  findFirstByTag(tag: string): TreeNode<T> | null;
  collectPreorderIds(): string[];
  pathToId(id: string): string[] | null;
}

export function validateCapacity(capacity: number): number {
  if (!Number.isInteger(capacity) || capacity <= 0) {
    throw new CacheConfigError("Cache capacity must be a positive integer");
  }
  return capacity;
}
