function clampBatteryPercent(rawLevel) {
  if (typeof rawLevel !== 'number' || !Number.isFinite(rawLevel)) {
    return null;
  }
  return Math.min(100, Math.max(0, rawLevel));
}

module.exports = { clampBatteryPercent };
