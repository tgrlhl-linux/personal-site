export async function POST({ request, cookies }) {
  const body = await request.json();
  const { username, password } = body;

  const adminUser = import.meta.env.ADMIN_USERNAME || 'admin';
  const adminPass = import.meta.env.ADMIN_PASSWORD;

  if (username === adminUser && password === adminPass) {
    const token = Buffer.from(`${username}:${Date.now()}`).toString('base64');
    cookies.set('admin_token', token, {
      httpOnly: true,
      sameSite: 'lax',
      secure: true,
      path: '/',
      maxAge: 60 * 60 * 24 * 7, // 7 days
    });
    return new Response(JSON.stringify({ success: true }), {
      headers: { 'Content-Type': 'application/json' },
    });
  }

  return new Response(JSON.stringify({ error: '用户名或密码错误' }), {
    status: 401, headers: { 'Content-Type': 'application/json' },
  });
}
