async function retryWithExponentialBackoff(asyncOperation, options = {}) {
  const maxRetries = options.maxRetries !== undefined ? options.maxRetries : 3;
  const baseDelayMs = options.baseDelayMs !== undefined ? options.baseDelayMs : 10;
  const maxDelayMs = options.maxDelayMs !== undefined ? options.maxDelayMs : 200;
  const isRetryable = options.isRetryable || (() => true);

  let attempt = 0;
  while (true) {
    try {
      return await asyncOperation();
    } catch (err) {
      if (!isRetryable(err) || attempt >= maxRetries) {
        throw err;
      }
      const delay = Math.min(maxDelayMs, baseDelayMs * Math.pow(2, attempt));
      await new Promise(resolve => setTimeout(resolve, delay));
      attempt++;
    }
  }
}

module.exports = { retryWithExponentialBackoff };
