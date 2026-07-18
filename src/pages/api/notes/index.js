import { query } from '../../../db/mysql';

export async function GET({ url }) {
  const search = url.searchParams.get('q') || '';
  const course = url.searchParams.get('course') || '';
  const page = parseInt(url.searchParams.get('page') || '1');
  const limit = parseInt(url.searchParams.get('limit') || '50');
  const offset = (page - 1) * limit;

  let where = "type = 'note' AND status = 'published'";
  const params = [];

  if (search) {
    where += ' AND (title LIKE ? OR content LIKE ?)';
    params.push(`%${search}%`, `%${search}%`);
  }
  if (course) {
    where += ' AND course = ?';
    params.push(course);
  }

  const countRows = await query(`SELECT COUNT(*) AS total FROM notes WHERE ${where}`, params);
  const total = countRows[0].total;

  const rows = await query(
    `SELECT id, title, slug, LEFT(excerpt, 200) AS excerpt, course, tags, metadata, created_at, updated_at
     FROM notes WHERE ${where}
     ORDER BY created_at DESC LIMIT ? OFFSET ?`,
    [...params, limit, offset]
  );

  const courses = await query(
    `SELECT DISTINCT course FROM notes WHERE type='note' AND status='published' AND course IS NOT NULL AND course != '' ORDER BY course`
  );

  return new Response(JSON.stringify({
    notes: rows,
    courses: courses.map(r => r.course),
    total,
    page,
    totalPages: Math.ceil(total / limit),
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
}

export async function POST({ request }) {
  const body = await request.json();
  const { title, content, course, tags } = body;

  if (!title) {
    return new Response(JSON.stringify({ error: '标题不能为空' }), {
      status: 400, headers: { 'Content-Type': 'application/json' },
    });
  }

  const slug = 'note-' + Date.now();
  const excerpt = (content || '').replace(/#{1,6}\s/g, '').replace(/\*\*/g, '').replace(/\n/g, ' ').trim().substring(0, 150);

  const result = await query(
    `INSERT INTO notes (type, title, slug, content, excerpt, course, tags, status)
     VALUES ('note', ?, ?, ?, ?, ?, ?, 'published')`,
    [title, slug, content || '', excerpt, course || '', JSON.stringify(tags || [])]
  );

  return new Response(JSON.stringify({ id: result.insertId, success: true }), {
    status: 201, headers: { 'Content-Type': 'application/json' },
  });
}
