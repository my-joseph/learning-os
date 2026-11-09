// Hidden Trap Test Suite for DRL-PRG-T00-C02-01 Q01
const test = require('node:test');
const assert = require('node:assert');
const { sanitizeConfig } = require('../Q01_sanitizeConfig.js');


test("[Q01-HIDDEN-T01] should discard extraneous keys not present in schema", async () => {
  const schema = { allowed: true };
const raw = { allowed: false, maliciousPayload: 'DROP TABLE', token: 'secret' };
const result = sanitizeConfig(raw, schema);
assert.strictEqual(result.allowed, false);
assert.strictEqual(result.maliciousPayload, undefined);
assert.strictEqual(result.token, undefined);
assert.deepStrictEqual(Object.keys(result), ['allowed']);
});
