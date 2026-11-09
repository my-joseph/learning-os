function composeAsyncMiddleware(middlewares) {
  return function(context) {
    let lastIndex = -1;

    function dispatch(i) {
      if (i <= lastIndex) {
        return Promise.reject(new Error('next() called multiple times'));
      }
      lastIndex = i;
      const fn = middlewares[i];
      if (!fn) {
        return Promise.resolve();
      }
      try {
        return Promise.resolve(fn(context, () => dispatch(i + 1)));
      } catch (err) {
        return Promise.reject(err);
      }
    }

    return dispatch(0);
  };
}

module.exports = { composeAsyncMiddleware };
