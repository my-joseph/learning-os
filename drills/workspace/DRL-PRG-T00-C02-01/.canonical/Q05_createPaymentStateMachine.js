function createPaymentStateMachine(options = {}) {
  let status = 'INITIAL';
  let orderId = null;
  let amount = null;

  return {
    dispatch(action) {
      if (!action || !action.type) throw new Error('INVALID_ACTION');

      if (status === 'INITIAL') {
        if (action.type === 'AUTHORIZE') {
          status = 'AUTHORIZED';
          orderId = action.orderId;
          amount = action.amount;
          return;
        }
        throw new Error('INVALID_STATE_TRANSITION');
      }

      if (status === 'AUTHORIZED') {
        if (action.type === 'CAPTURE') {
          status = 'SETTLED';
          return;
        }
        if (action.type === 'VOID') {
          status = 'VOIDED';
          return;
        }
        throw new Error('INVALID_STATE_TRANSITION');
      }

      // Terminal states SETTLED or VOIDED
      throw new Error('INVALID_STATE_TRANSITION');
    },

    getState() {
      return { status, orderId, amount };
    }
  };
}

module.exports = { createPaymentStateMachine };
