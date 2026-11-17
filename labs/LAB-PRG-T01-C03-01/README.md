# LAB-PRG-T01-C03-01 — LRUCache & TreeIndex

## Scenario

Build two in-memory data structures for a catalog query engine: an O(1) least-recently-used cache backed by a doubly-linked list and a Map, and a DFS/BFS tree index for hierarchical category lookup without mutating caller trees.

## Milestones

### M1 — Node & Cache Contracts

Define cache entry/stats interfaces, tree node types, `CacheConfigError`, and `validateCapacity(capacity)` validating positive integers.

Run this milestone's visible checks with `npm run test:m1` and all checks with `npm run check:m1`.

### M2 — Doubly-Linked List Operations

Implement `createDoublyLinkedList<T>()` with `pushFront`, `moveToFront`, `popBack`, `remove`, `size`, and `toArray`. Keep internal node pointers encapsulated so callers cannot mutate link invariants directly; `remove(handle)` returns `false` if the handle is already detached or belongs to another list, and `moveToFront(handle)` is a no-op on detached handles.

Run this milestone's visible checks with `npm run test:m2` and all checks with `npm run check:m2`.

### M3 — O(1) `get`/`put` LRU Cache Eviction

Implement `createLRUCache<K, V>(capacity)` combining a `Map` and doubly-linked list for constant-time lookup, recency promotion on read and update, and tail eviction when exceeding capacity. Track `hits` (incremented only by `get` hits, not `put` updates), `misses`, and `evictions`.

Run this milestone's visible checks with `npm run test:m3` and all checks with `npm run check:m3`.

### M4 — Recursive DFS/BFS Tree Search

Implement `createTreeIndex<T>(root)` supporting `findById` (DFS), `findFirstByTag` (BFS shortest-depth), `collectPreorderIds` (DFS preorder), and `pathToId` without mutating the source tree.

Run this milestone's visible checks with `npm run test:m4` and all checks with `npm run check:m4`.

## Commands

- `npm test` runs all visible milestone tests.
- `npm run check` runs tests, lint, and typecheck.
- `npm run test:m1` / `npm run check:m1` run one milestone; use `m2`, `m3`, or `m4` for the others.
- `npm run review -- m1` prints the review request for the milestone.
- Ask Claude Code: `ตรวจโค้ด LAB-PRG-T01-C03-01 M1` (replace `M1` with the milestone being reviewed).
