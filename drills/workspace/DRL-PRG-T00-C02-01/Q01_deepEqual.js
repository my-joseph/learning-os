/**
 * Performs a deep comparison between two values to determine if they are equivalent.
 *
 * Requirements:
 * - Primitives: Strict equality, except NaN which should equal NaN (Object.is behavior).
 * - Objects & Arrays: Recursively compare enumerable own properties and elements.
 * - Array vs Object: [1, 2] is NOT deeply equal to { '0': 1, '1': 2 }.
 * - Null / Undefined: null is NOT equal to undefined or {}.
 *
 * @param {*} a - The value to compare.
 * @param {*} b - The other value to compare.
 * @returns {boolean} - Returns true if values are equivalent, else false.
 */
function deepEqual(a, b) {
  if (Object.is(a, b)) return true;
  if (
    typeof a !== "object" ||
    a === null ||
    typeof b !== "object" ||
    b === null
  ) {
    return false;
  }
  if (Array.isArray(a) !== Array.isArray(b)) return false;
  const keysA = Object.keys(a);
  const keysB = Object.keys(b);
  if (keysA.length !== keysB.length) return false;
  for (const key of keysA) {
    if (!Object.prototype.hasOwnProperty.call(b, key)) return false;
    if (!deepEqual(a[key], b[key])) return false;
  }
  return true;
}

module.exports = { deepEqual };
