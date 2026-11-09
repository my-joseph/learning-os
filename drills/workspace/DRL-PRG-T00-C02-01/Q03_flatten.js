/**
 * Flattens an array up to the specified depth without mutating the input array.
 * Do NOT use Array.prototype.flat.
 *
 * Requirements:
 * - Default depth is 1.
 * - If depth <= 0, return a shallow copy of the array.
 * - If depth is Infinity, completely flatten all nested levels.
 * - Preserves all falsy values (0, false, null, undefined, '').
 *
 * @param {Array} array - The array to flatten.
 * @param {number} [depth=1] - The maximum recursion depth.
 * @returns {Array} - The new flattened array.
 */
function flatten(array, depth = 1) {
  // TODO: Implement recursive flattening
}

module.exports = { flatten };
