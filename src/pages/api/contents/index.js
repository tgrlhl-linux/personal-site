import { query } from '../../../db/mysql';

// Unified content API: GET /api/contents?type=note&course=...&q=...&page=...&limit=...
export async function GET({ url }) {
  const type = url.searchParams.get('type') || '';
  const course = url.searchParams.get('course') || '';
  const search = url.searchParams.get('q') || '';
  const page = parseInt(url.searchParams.get('page') || '1');
  const limit = parseInt(url.searchParams.get('limit') || '50');
  const offset = (page - 1) * limit;

  let where = "status = 'published'";
  const params = [];

  if (type) {
    where += ' AND type = ?';
    params.push(type);
  }
  if (course) {
    where += ' AND course = ?';
    params.push(course);
  }
  if (search) {
    where += ' AND (title LIKE ? OR content LIKE ? OR excerpt LIKE ?)';
    params.push(`%${search}%`, `%${search}%`, `%${search}%`);
  }

  const countRows = await query(`SELECT COUNT(*) AS total FROM notes WHERE ${where}`, params);
  const total = countRows[0].total;

  const rows = await query(
    `SELECT id, type, title, slug, LEFT(excerpt, 200) AS excerpt, course, tags, metadata, created_at, updated_at
     FROM notes WHERE ${where}
     ORDER BY created_at DESC LIMIT ? OFFSET ?`,
    [...params, limit, offset]
  );

  // Group by course/category
  const groups = {};
  for (const r of rows) {
    const key = r.course || '未分类';
    if (!groups[key]) groups[key] = { course: key, count: 0, items: [] };
    groups[key].count++;
    groups[key].items.push(r);
  }

  // Available courses for this type
  const typeFilter = type ? `AND type = '${type}'` : '';
  const courses = await query(
    `SELECT DISTINCT course FROM notes WHERE status='published' ${typeFilter} AND course IS NOT NULL AND course != '' ORDER BY course`
  );

  return new Response(JSON.stringify({
    contents: rows,
    groups: Object.values(groups),
    courses: courses.map(r => r.course),
    total,
    page,
    totalPages: Math.ceil(total / limit),
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
}
