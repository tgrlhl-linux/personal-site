import { query } from '../../../db/mysql';

export async function GET({ params }) {
  const id = parseInt(params.id);
  if (!id) {
    return new Response(JSON.stringify({ error: '无效的 ID' }), {
      status: 400, headers: { 'Content-Type': 'application/json' },
    });
  }

  const rows = await query('SELECT * FROM notes WHERE id = ?', [id]);
  if (rows.length === 0) {
    return new Response(JSON.stringify({ error: '笔记不存在' }), {
      status: 404, headers: { 'Content-Type': 'application/json' },
    });
  }

  return new Response(JSON.stringify(rows[0]), {
    headers: { 'Content-Type': 'application/json' },
  });
}

export async function PUT({ params, request }) {
  const id = parseInt(params.id);
  const body = await request.json();
  const { title, content, course, tags } = body;

  await query(
    'UPDATE notes SET title = ?, content = ?, course = ?, tags = ? WHERE id = ?',
    [title, content || '', course || '', JSON.stringify(tags || []), id]
  );

  return new Response(JSON.stringify({ success: true }), {
    headers: { 'Content-Type': 'application/json' },
  });
}

export async function DELETE({ params }) {
  const id = parseInt(params.id);
  await query('DELETE FROM notes WHERE id = ?', [id]);

  return new Response(JSON.stringify({ success: true }), {
    headers: { 'Content-Type': 'application/json' },
  });
}
