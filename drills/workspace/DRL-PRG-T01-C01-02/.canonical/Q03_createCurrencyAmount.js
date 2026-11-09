function createCurrencyAmount(amount, currency) {
  return {
    amount,
    currency,
    [Symbol.toPrimitive](hint) {
      if (hint === 'string') {
        return `${amount} ${currency}`;
      }
      return amount;
    },
    valueOf() {
      return amount;
    },
    toString() {
      return `${amount} ${currency}`;
    }
  };
}

module.exports = { createCurrencyAmount };
