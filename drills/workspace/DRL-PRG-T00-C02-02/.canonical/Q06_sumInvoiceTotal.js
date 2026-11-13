function sumInvoiceTotal(taxRate, ...lineAmounts) {
  const subtotal = lineAmounts.reduce((runningTotal, amount) => runningTotal + amount, 0);
  return Math.round(subtotal * (1 + taxRate) * 100) / 100;
}

module.exports = { sumInvoiceTotal };
