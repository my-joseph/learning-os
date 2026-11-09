function flatten(array, depth = 1) {
  if (!Array.isArray(array)) return [];
  if (depth <= 0) return array.slice();
  const result = [];
  for (const item of array) {
    if (Array.isArray(item) && depth > 0) {
      result.push(...flatten(item, depth - 1));
    } else {
      result.push(item);
    }
  }
  return result;
}

module.exports = { flatten };
