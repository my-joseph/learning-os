function createSandboxContext(parentConfig = {}) {
  const localStore = new Map();

  return {
    get(key) {
      if (localStore.has(key)) {
        return localStore.get(key);
      }
      return parentConfig[key];
    },
    set(key, value) {
      localStore.set(key, value);
    },
    has(key) {
      return localStore.has(key) || (key in parentConfig);
    }
  };
}

module.exports = { createSandboxContext };
