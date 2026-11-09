// Auto-generated visible test suite for DRL-PRG-T00-C02-01 Q01
const test = require('node:test');
const assert = require('node:assert');
const { sanitizeConfig } = require('./Q01_sanitizeConfig.js');


test("[Q01-T01] should preserve legitimate falsy values like zero, false, and empty string", async () => {
  const schema = { retries: 3, debug: true, prefix: 'APP_' };
const raw = { retries: 0, debug: false, prefix: '' };
const result = sanitizeConfig(raw, schema);
assert.strictEqual(result.retries, 0);
assert.strictEqual(result.debug, false);
assert.strictEqual(result.prefix, '');
});

test("[Q01-T02] should use default values when properties are null, undefined, or missing", async () => {
  const schema = { port: 8080, host: 'localhost', ssl: false };
const raw = { port: null, host: undefined };
const result = sanitizeConfig(raw, schema);
assert.strictEqual(result.port, 8080);
assert.strictEqual(result.host, 'localhost');
assert.strictEqual(result.ssl, false);
});
