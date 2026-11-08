// Auto-generated visible test suite for DRL-PRG-T01-C03-02 Q03
const test = require('node:test');
const assert = require('node:assert');
const { calculateMonthlyBill } = require('./Q03_calculateMonthlyBill.js');


test("[Q03-T01] legacy regression: should accurately bill basic, pro, and enterprise tiers", async () => {
  const basic = calculateMonthlyBill({ plan: 'basic' });
            assert.strictEqual(basic.planSubtotal, 9.99);
            assert.strictEqual(basic.total, 10.79);

            const pro = calculateMonthlyBill({ plan: 'pro', taxExempt: true });
            assert.strictEqual(pro.total, 24.99);

            const ent = calculateMonthlyBill({ plan: 'enterprise', seats: 15 });
            assert.strictEqual(ent.planSubtotal, 124.99, "Base 99.99 + 5 extra seats at $5 = 124.99");
});

test("[Q03-T02] new feature: should calculate family plan with member scaling and max 6 guard", async () => {
  const fam2 = calculateMonthlyBill({ plan: 'family', members: 2 });
            assert.strictEqual(fam2.planSubtotal, 34.99, "2 members included in base");

            const fam4 = calculateMonthlyBill({ plan: 'family', members: 4 });
            assert.strictEqual(fam4.planSubtotal, 52.97, "Base 34.99 + 2 extra members * 8.99 = 52.97");

            assert.throws(() => calculateMonthlyBill({ plan: 'family', members: 7 }), /RangeError/);
});

test("[Q03-T03] new feature: should apply 15% discount for annual commitment accounts", async () => {
  const annualFam = calculateMonthlyBill({
              plan: 'family',
              members: 4,
              annualCommitment: true,
            });
            assert.strictEqual(annualFam.planSubtotal, 52.97);
            assert.strictEqual(annualFam.discount, 7.95, "15% of 52.97 rounded to 2 decimals");
            assert.strictEqual(annualFam.tax, 3.60, "8% of 45.02 = 3.60");
            assert.strictEqual(annualFam.total, 48.62);
});
