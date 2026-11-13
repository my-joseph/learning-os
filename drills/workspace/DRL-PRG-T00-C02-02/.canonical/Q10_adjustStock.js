function adjustStock(stockBySku, sku, delta) {
  return { ...stockBySku, [sku]: (stockBySku[sku] ?? 0) + delta };
}

module.exports = { adjustStock };
