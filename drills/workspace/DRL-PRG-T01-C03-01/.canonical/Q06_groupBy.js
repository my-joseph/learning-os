function groupBy(collection, iteratee) {
  if (!collection || !Array.isArray(collection)) {
    return {};
  }

  const getKey = typeof iteratee === 'function'
    ? iteratee
    : (item) => (item != null ? item[iteratee] : undefined);

  return collection.reduce((acc, item) => {
    const key = getKey(item);
    if (key !== undefined) {
      if (!acc[key]) {
        acc[key] = [];
      }
      acc[key].push(item);
    }
    return acc;
  }, {});
}

module.exports = { groupBy };
