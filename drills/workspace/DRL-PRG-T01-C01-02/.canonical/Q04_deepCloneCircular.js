function deepCloneCircular(target, seen = new Map()) {
  if (target === null || typeof target !== 'object') {
    return target;
  }

  if (seen.has(target)) {
    return seen.get(target);
  }

  const clone = Array.isArray(target) ? [] : {};
  seen.set(target, clone);

  for (const [key, val] of Object.entries(target)) {
    clone[key] = deepCloneCircular(val, seen);
  }

  return clone;
}

module.exports = { deepCloneCircular };
