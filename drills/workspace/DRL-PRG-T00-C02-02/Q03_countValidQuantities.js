function countValidQuantities(rawQuantities) {
  return (rawQuantities || []).filter((qty) => qty >= 0);
}

module.exports = { countValidQuantities };
