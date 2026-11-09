function aggregateCategoryRevenue(transactions) {
  const revenue = {};
  for (const tx of transactions) {
    if (tx.status === 'completed') {
      revenue[tx.category] = (revenue[tx.category] || 0) + tx.amount;
    } else if (tx.status === 'refunded') {
      revenue[tx.category] = (revenue[tx.category] || 0) - tx.amount;
    }
  }
  for (const cat of Object.keys(revenue)) {
    revenue[cat] = Math.round(revenue[cat] * 100) / 100;
  }
  return revenue;
}

module.exports = { aggregateCategoryRevenue };
