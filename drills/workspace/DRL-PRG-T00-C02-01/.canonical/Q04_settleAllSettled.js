function settleAllSettled(taskFns) {
  const promises = taskFns.map(fn => {
    return Promise.resolve()
      .then(() => fn())
      .then(value => ({ status: 'fulfilled', value }))
      .catch(reason => ({ status: 'rejected', reason }));
  });
  return Promise.all(promises);
}

module.exports = { settleAllSettled };
