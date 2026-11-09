function sanitizeConfig(rawConfig, schema) {
  const sanitized = {};
  const safeRaw = rawConfig || {};
  for (const [key, defaultVal] of Object.entries(schema)) {
    const rawVal = safeRaw[key];
    sanitized[key] = (rawVal !== null && rawVal !== undefined) ? rawVal : defaultVal;
  }
  return sanitized;
}

module.exports = { sanitizeConfig };
