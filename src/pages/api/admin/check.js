import { verifyToken, COOKIE_NAME } from '../../../lib/auth.js';

export async function GET({ cookies }) {
  const token = cookies.get(COOKIE_NAME)?.value;
  const username = token ? verifyToken(token) : null;

  if (username) {
    return new Response(JSON.stringify({ authenticated: true, username }), {
      headers: { 'Content-Type': 'application/json' },
    });
  }

  return new Response(JSON.stringify({ authenticated: false }), {
    status: 401, headers: { 'Content-Type': 'application/json' },
  });
}
