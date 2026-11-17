import type { TreeIndex, TreeNode } from "./contracts.ts";

function searchDfsById<T>(node: TreeNode<T> | null, targetId: string): TreeNode<T> | null {
  if (node === null) {
    return null;
  }
  if (node.id === targetId) {
    return node;
  }
  for (const child of node.children) {
    const found = searchDfsById(child, targetId);
    if (found !== null) {
      return found;
    }
  }
  return null;
}

function collectPreorder<T>(node: TreeNode<T> | null, out: string[]): void {
  if (node === null) {
    return;
  }
  out.push(node.id);
  for (const child of node.children) {
    collectPreorder(child, out);
  }
}

function findPathDfs<T>(node: TreeNode<T> | null, targetId: string, trail: string[]): boolean {
  if (node === null) {
    return false;
  }
  trail.push(node.id);
  if (node.id === targetId) {
    return true;
  }
  for (const child of node.children) {
    if (findPathDfs(child, targetId, trail)) {
      return true;
    }
  }
  trail.pop();
  return false;
}

export function createTreeIndex<T>(root: TreeNode<T> | null): TreeIndex<T> {
  return {
    findById(id: string): TreeNode<T> | null {
      return searchDfsById(root, id);
    },
    findFirstByTag(tag: string): TreeNode<T> | null {
      if (root === null) {
        return null;
      }
      const queue: TreeNode<T>[] = [root];
      for (let head = 0; head < queue.length; head += 1) {
        const current = queue[head];
        if (current.tags.includes(tag)) {
          return current;
        }
        for (const child of current.children) {
          queue.push(child);
        }
      }
      return null;
    },
    collectPreorderIds(): string[] {
      const ids: string[] = [];
      collectPreorder(root, ids);
      return ids;
    },
    pathToId(id: string): string[] | null {
      const trail: string[] = [];
      return findPathDfs(root, id, trail) ? trail : null;
    },
  };
}
