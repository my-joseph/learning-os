function countValidQuantities(rawQuantities) {
  let validCount = 0;
  for (const quantity of rawQuantities) {
    if (typeof quantity === 'number' && Number.isInteger(quantity) && quantity >= 0) {
      validCount += 1;
    }
  }
  return validCount;
}

module.exports = { countValidQuantities };
