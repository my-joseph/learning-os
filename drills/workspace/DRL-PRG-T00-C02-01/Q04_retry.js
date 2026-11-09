/**
 * Retries an asynchronous operation upon rejection with backoff delay.
 *
 * Requirements:
 * - If asyncFn() succeeds on attempt 1, resolve immediately without delay.
 * - On failure, wait delayMs before attempting again, up to `retries` additional times.
 * - Total attempts = retries + 1.
 * - If all attempts fail, reject with the error from the final attempt.
 *
 * @param {Function} asyncFn - Async function returning a Promise.
 * @param {number} [retries=3] - Number of retry attempts after initial failure.
 * @param {number} [delayMs=100] - Delay in milliseconds between attempts.
 * @returns {Promise<*>} - Resolves with the result or rejects with the last error.
 */
async function retry(asyncFn, retries = 3, delayMs = 100) {
  // TODO: Implement async retry logic
}

module.exports = { retry };
