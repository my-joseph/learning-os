function pipe(...fns) {
  if (fns.length === 0) return (x) => x;
  return function(...args) {
    return fns.slice(1).reduce((acc, fn) => fn(acc), fns[0](...args));
  };
}

module.exports = { pipe };
