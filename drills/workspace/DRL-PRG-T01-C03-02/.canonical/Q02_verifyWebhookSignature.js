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

  const currentSec = Math.floor(Date.now() / 1000);
  if (Math.abs(currentSec - timestamp) > toleranceSeconds) {
    return false;
  }

  const expectedHex = crypto.createHmac('sha256', secret).update(`${timestamp}.${payload}`).digest('hex');
  const expectedBuf = Buffer.from(expectedHex, 'utf8');
  const signatureBuf = Buffer.from(signatureHex, 'utf8');

  if (expectedBuf.length !== signatureBuf.length) {
    return false;
  }

  return crypto.timingSafeEqual(expectedBuf, signatureBuf);
}

module.exports = { verifyWebhookSignature };
