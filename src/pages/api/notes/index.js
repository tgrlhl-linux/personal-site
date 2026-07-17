import { query } from '../../../db/mysql';

export async function GET({ url }) {
  const search = url.searchParams.get('q') || '';
  const course = url.searchParams.get('course') || '';
  const page = parseInt(url.searchParams.get('page') || '1');
  const limit = 20;
  const offset = (page - 1) * limit;

  let where = '1=1';
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
    `SELECT id, title, LEFT(content, 200) AS excerpt, course, tags, created_at, updated_at
     FROM notes WHERE ${where}
     ORDER BY created_at DESC LIMIT ? OFFSET ?`,
    [...params, limit, offset]
  );

  const courses = await query('SELECT DISTINCT course FROM notes WHERE course IS NOT NULL AND course != "" ORDER BY course');

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

  const result = await query(
    'INSERT INTO notes (title, content, course, tags) VALUES (?, ?, ?, ?)',
    [title, content || '', course || '', JSON.stringify(tags || [])]
  );

  return new Response(JSON.stringify({ id: result.insertId, success: true }), {
    status: 201, headers: { 'Content-Type': 'application/json' },
  });
}
