function summarizeTemperatures(readings) {
  const total = readings.reduce((runningTotal, reading) => runningTotal + reading, 0);
  return {
    min: Math.min(...readings),
    max: Math.max(...readings),
    average: Math.round((total / readings.length) * 10) / 10,
  };
}

module.exports = { summarizeTemperatures };
