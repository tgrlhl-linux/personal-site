import { createHmac, createHash } from 'node:crypto';

function getSecret() {
  return import.meta.env.ADMIN_SECRET ||
    createHash('sha256').update(import.meta.env.ADMIN_PASSWORD || 'guorui2024').digest('hex');
}

const COOKIE_NAME = 'admin_token';
const MAX_AGE = 7 * 24 * 60 * 60; // 7 days in seconds

export function createToken(username) {
  const expiry = Math.floor(Date.now() / 1000) + MAX_AGE;
  const payload = `${username}:${expiry}`;
  const sig = createHmac('sha256', getSecret()).update(payload).digest('hex');
  return Buffer.from(`${payload}:${sig}`).toString('base64');
}

export function verifyToken(token) {
  try {
    const decoded = Buffer.from(token, 'base64').toString();
    const lastColon = decoded.lastIndexOf(':');
    if (lastColon < 0) return null;

    const signature = decoded.slice(lastColon + 1);
    const payload = decoded.slice(0, lastColon);
    const [username, expiryStr] = payload.split(':');

    if (!username || !expiryStr) return null;

    // Check expiry
    if (Math.floor(Date.now() / 1000) > parseInt(expiryStr)) return null;

    // Verify HMAC
    const expectedSig = createHmac('sha256', getSecret()).update(payload).digest('hex');
    if (signature !== expectedSig) return null;

    return username;
  } catch {
    return null;
  }
}

export { COOKIE_NAME, MAX_AGE };
