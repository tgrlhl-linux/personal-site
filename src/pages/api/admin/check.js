export async function GET({ cookies }) {
  const token = cookies.get('admin_token')?.value;
  const adminUser = import.meta.env.ADMIN_USERNAME || 'admin';

  if (token) {
    try {
      const decoded = Buffer.from(token, 'base64').toString();
      const [username] = decoded.split(':');
      if (username === adminUser) {
        return new Response(JSON.stringify({ authenticated: true }), {
          headers: { 'Content-Type': 'application/json' },
        });
      }
    } catch {}
  }

  return new Response(JSON.stringify({ authenticated: false }), {
    status: 401, headers: { 'Content-Type': 'application/json' },
  });
}
