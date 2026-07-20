import { createToken, COOKIE_NAME, MAX_AGE } from '../../../lib/auth.js';

export async function POST({ request, cookies }) {
  const body = await request.json();
  const { username, password } = body;

  const adminUser = import.meta.env.ADMIN_USERNAME || 'admin';
  const adminPass = import.meta.env.ADMIN_PASSWORD;

  if (username === adminUser && password === adminPass) {
    const token = createToken(username);
    cookies.set(COOKIE_NAME, token, {
      httpOnly: true,
      sameSite: 'lax',
      secure: true,
      path: '/',
      maxAge: MAX_AGE,
    });
    return new Response(JSON.stringify({ success: true }), {
      headers: { 'Content-Type': 'application/json' },
    });
  }

  return new Response(JSON.stringify({ error: '用户名或密码错误' }), {
    status: 401, headers: { 'Content-Type': 'application/json' },
  });
}
