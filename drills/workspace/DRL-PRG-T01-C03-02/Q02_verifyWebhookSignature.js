const crypto = require('crypto');

function verifyWebhookSignature(payload, signatureHeader, secret, toleranceSeconds = 300) {
  const parts = signatureHeader.split(',');
  let timestamp = null;
  let signatureHex = null;

  for (const part of parts) {
    const [key, val] = part.split('=');
    if (key === 't') timestamp = parseInt(val, 10);
    if (key === 'v1') signatureHex = val;
  }

  if (!timestamp || !signatureHex) return false;

  const expectedHex = crypto.createHmac('sha256', secret).update(`${timestamp}.${payload}`).digest('hex');
  return expectedHex === signatureHex;
}

module.exports = { verifyWebhookSignature };
