import mysql from 'mysql2/promise';
const conn = await mysql.createConnection({
  host: process.env.DB_HOST,
  port: parseInt(process.env.DB_PORT || '4000'),
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME || 'personal_site',
  ssl: { rejectUnauthorized: true }
});
const [rows] = await conn.query("SELECT type, status, course, COUNT(*) as count FROM notes GROUP BY type, status, course WITH ROLLUP");
console.log('=== 内容统计 ===');
rows.forEach(r => console.log(`  ${r.type||'ALL'}/${r.status||'ALL'} ${r.course||''}: ${r.count}`));
const [recent] = await conn.query("SELECT id, title, course, created_at FROM notes WHERE type=? ORDER BY created_at DESC LIMIT 10", ['note']);
console.log('\n=== 最近 10 篇笔记 ===');
recent.forEach(r => console.log(`  [${r.id}] ${r.title} (${r.course||'无分类'}) ${r.created_at}`));
const [prepped] = await conn.query("SELECT COUNT(*) as c FROM notes WHERE type='note'");
console.log('\n=== 数据库笔记总览 ===');
console.log(`  笔记总数: ${prepped[0].c} 篇 | notes-prep: 29 篇 | 差额: ${29 - prepped[0].c} 篇`);
const [hobbies] = await conn.query("SELECT COUNT(*) as c FROM notes WHERE type='hobby'");
console.log(`  Hobbies: ${hobbies[0].c} 条`);
const [timeline] = await conn.query("SELECT COUNT(*) as c FROM notes WHERE type='timeline_event'");
console.log(`  Timeline: ${timeline[0].c} 条`);
const [courses] = await conn.query("SELECT course, COUNT(*) as c FROM notes WHERE type='note' AND status='published' GROUP BY course ORDER BY c DESC");
console.log('\n=== 已发布笔记课程分布 ===');
courses.forEach(r => console.log(`  ${r.course||'无分类'}: ${r.c} 篇`));
await conn.end();
