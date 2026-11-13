function applyDiscount(price, rate = 0.1) {
  return Math.round(price * (1 - rate) * 100) / 100;
}

module.exports = { applyDiscount };
