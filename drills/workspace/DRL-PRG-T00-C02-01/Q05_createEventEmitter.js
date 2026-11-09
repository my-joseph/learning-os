/**
 * Creates an event emitter supporting subscription, emission, once-listeners, and unsubscription.
 *
 * Requirements:
 * - on(event, listener): Adds listener; returns an unsubscribe() function.
 * - emit(event, ...args): Calls all listeners registered for event with args synchronously.
 * - once(event, listener): Listener fires once, then unregisters itself automatically.
 * - listenerCount(event): Returns active count of listeners for event.
 *
 * @returns {Object} Emitter instance.
 */
function createEventEmitter() {
  // TODO: Implement event emitter
}

module.exports = { createEventEmitter };
