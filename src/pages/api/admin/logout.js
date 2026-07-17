export async function POST({ cookies }) {
  cookies.delete('admin_token', { path: '/' });
  return new Response(JSON.stringify({ success: true }), {
    headers: { 'Content-Type': 'application/json' },
  });
}
