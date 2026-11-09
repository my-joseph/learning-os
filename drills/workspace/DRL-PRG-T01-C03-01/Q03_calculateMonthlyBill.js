/**
 * LEGACY SUBSCRIPTION BILLING MODULE
 * 
 * MISSION:
 * 1. Maintain 100% backward compatibility with all existing legacy tests.
 * 2. Add support for the new 'family' plan:
 *    - Base price: $34.99 (includes 2 members).
 *    - Extra members: +$8.99 per member over 2, up to 6 members max.
 *    - If account.members > 6, throw RangeError('Family plan allows max 6 members').
 * 3. Add support for 'annualCommitment':
 *    - If account.annualCommitment is true, apply 15% discount on plan subtotal before tax.
 * 4. Refactor the tangled switch-statement into clean, decoupled architecture.
 */
function calculateMonthlyBill(account) {
  if (!account || !account.plan) {
    throw new TypeError('Account with valid plan required');
  }

  let planSubtotal = 0;
  if (account.plan === 'basic') {
    planSubtotal = 9.99;
  } else if (account.plan === 'pro') {
    planSubtotal = 24.99;
  } else if (account.plan === 'enterprise') {
    planSubtotal = 99.99;
    const seats = account.seats || 10;
    if (seats > 10) {
      planSubtotal += (seats - 10) * 5.00;
    }
  } else {
    throw new RangeError('Unknown subscription plan: ' + account.plan);
  }

  // TODO: Add support for 'family' plan and 'annualCommitment' discount
  const discount = 0;
  const taxableSubtotal = planSubtotal - discount;
  const tax = account.taxExempt ? 0 : Math.round(taxableSubtotal * 0.08 * 100) / 100;
  const total = Math.round((taxableSubtotal + tax) * 100) / 100;

  return { plan: account.plan, planSubtotal, discount, tax, total };
}

module.exports = { calculateMonthlyBill };
