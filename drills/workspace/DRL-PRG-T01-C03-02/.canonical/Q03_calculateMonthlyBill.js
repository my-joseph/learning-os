const PLAN_CONFIG = {
  basic: {
    basePrice: 9.99,
    calculateAddOns: () => 0,
  },
  pro: {
    basePrice: 24.99,
    calculateAddOns: () => 0,
  },
  enterprise: {
    basePrice: 99.99,
    calculateAddOns: (account) => {
      const seats = account.seats || 10;
      return seats > 10 ? (seats - 10) * 5.00 : 0;
    },
  },
  family: {
    basePrice: 34.99,
    calculateAddOns: (account) => {
      const members = account.members || 2;
      if (members > 6) {
        throw new RangeError('Family plan allows max 6 members');
      }
      return members > 2 ? (members - 2) * 8.99 : 0;
    },
  },
};

function calculateMonthlyBill(account) {
  if (!account || !account.plan) {
    throw new TypeError('Account with valid plan required');
  }

  const handler = PLAN_CONFIG[account.plan];
  if (!handler) {
    throw new RangeError('Unknown subscription plan: ' + account.plan);
  }

  const addOnCost = handler.calculateAddOns(account);
  const planSubtotal = Math.round((handler.basePrice + addOnCost) * 100) / 100;

  const discount = account.annualCommitment
    ? Math.round(planSubtotal * 0.15 * 100) / 100
    : 0;

  const taxableSubtotal = planSubtotal - discount;
  const tax = account.taxExempt ? 0 : Math.round(taxableSubtotal * 0.08 * 100) / 100;
  const total = Math.round((taxableSubtotal + tax) * 100) / 100;

  return { plan: account.plan, planSubtotal, discount, tax, total };
}

module.exports = { calculateMonthlyBill };
