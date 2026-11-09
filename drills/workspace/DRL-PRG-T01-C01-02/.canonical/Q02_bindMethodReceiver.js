function bindMethodReceiver(targetInstance, methodNames) {
  for (const name of methodNames) {
    if (typeof targetInstance[name] === 'function') {
      targetInstance[name] = targetInstance[name].bind(targetInstance);
    }
  }
  return targetInstance;
}

module.exports = { bindMethodReceiver };
