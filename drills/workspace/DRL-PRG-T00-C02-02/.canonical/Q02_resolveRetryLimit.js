function resolveRetryLimit(settings) {
  return settings?.maxRetries ?? 3;
}

module.exports = { resolveRetryLimit };
