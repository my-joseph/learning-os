function createEventEmitter() {
  const events = new Map();

  return {
    on(event, listener) {
      if (!events.has(event)) {
        events.set(event, []);
      }
      const listeners = events.get(event);
      listeners.push(listener);

      return function unsubscribe() {
        const idx = listeners.indexOf(listener);
        if (idx !== -1) {
          listeners.splice(idx, 1);
        }
        if (listeners.length === 0) {
          events.delete(event);
        }
      };
    },

    emit(event, ...args) {
      if (!events.has(event)) return false;
      const listeners = [...events.get(event)];
      for (const fn of listeners) {
        fn(...args);
      }
      return true;
    },

    once(event, listener) {
      const unsubscribe = this.on(event, (...args) => {
        unsubscribe();
        listener(...args);
      });
      return unsubscribe;
    },

    listenerCount(event) {
      return events.has(event) ? events.get(event).length : 0;
    },
  };
}

module.exports = { createEventEmitter };
