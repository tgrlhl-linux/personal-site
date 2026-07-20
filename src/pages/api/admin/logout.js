import { COOKIE_NAME } from '../../../lib/auth.js';

export async function POST({ cookies }) {
  cookies.delete(COOKIE_NAME, { path: '/' });
  return new Response(JSON.stringify({ success: true }), {
    headers: { 'Content-Type': 'application/json' },
  });
}
