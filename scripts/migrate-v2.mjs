/**
 * v2 迁移脚本：扩展 DB schema + 将 .md 内容导入数据库
 * 运行: node scripts/migrate-v2.mjs
 */
import mysql from 'mysql2/promise';
import { readFileSync, readdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

// ── DB 连接 ──
const conn = await mysql.createPool({
  host: 'gateway01.ap-northeast-1.prod.aws.tidbcloud.com',
  port: 4000,
  user: '28bKJwXcdrmiau1.root',
  password: 'UEB4Z0TNixwRvvzH',
  database: 'personal_site',
  ssl: { rejectUnauthorized: true },
  connectionLimit: 5,
});

try {
  // ── 1. 扩展表结构 ──
  console.log('🔄 扩展 notes 表...');
  const existingCols = await conn.query('SHOW COLUMNS FROM notes');
  const colNames = existingCols[0].map(c => c.Field);

  const addCol = async (name, def) => {
    if (!colNames.includes(name)) {
      await conn.query(`ALTER TABLE notes ADD COLUMN ${name} ${def}`);
      console.log(`  ✅ 添加字段: ${name}`);
    } else {
      console.log(`  ⏭️  已存在: ${name}`);
    }
  };

  await addCol('type', "VARCHAR(20) NOT NULL DEFAULT 'note' AFTER title");
  await addCol('slug', 'VARCHAR(200) AFTER type');
  await addCol('excerpt', 'VARCHAR(500) AFTER content');
  await addCol('metadata', 'JSON AFTER tags');
  await addCol('status', "VARCHAR(20) NOT NULL DEFAULT 'published' AFTER metadata");
  await addCol('display_order', 'INT DEFAULT 0 AFTER status');

  // Add indexes
  try {
    await conn.query('ALTER TABLE notes ADD INDEX idx_type_status (type, status)');
    console.log('  ✅ 添加索引: idx_type_status');
  } catch (e) {
    if (!e.message.includes('Duplicate')) throw e;
  }
  try {
    await conn.query('ALTER TABLE notes ADD INDEX idx_course (course)');
    console.log('  ✅ 添加索引: idx_course');
  } catch (e) {
    if (!e.message.includes('Duplicate')) throw e;
  }

  // ── 2. 为已有笔记生成 slug ──
  console.log('\n🔄 为笔记生成 slug...');
  const [notes] = await conn.query('SELECT id, title FROM notes WHERE type = ? AND (slug IS NULL OR slug = "")', ['note']);
  for (const n of notes) {
    const slug = n.title
      .replace(/^.*?·\s*/, '')    // 去掉 "操作系统 · " 前缀
      .replace(/\s+/g, '-')
      .replace(/[^\w一-鿿-]/g, '')
      .toLowerCase();
    await conn.query('UPDATE notes SET slug = ? WHERE id = ?', [`note-${n.id}-${slug}`, n.id]);
  }
  console.log(`  ✅ 更新 ${notes.length} 篇笔记`);

  // ── 3. 设置 excerpt ──
  console.log('\n🔄 设置 excerpt...');
  const [noExcerpt] = await conn.query('SELECT id, content FROM notes WHERE excerpt IS NULL OR excerpt = ""');
  for (const n of noExcerpt) {
    const text = (n.content || '')
      .replace(/#{1,6}\s/g, '')   // 去掉 markdown 标题标记
      .replace(/\*\*/g, '')
      .replace(/\n/g, ' ')
      .trim();
    const excerpt = text.substring(0, 150);
    await conn.query('UPDATE notes SET excerpt = ? WHERE id = ?', [excerpt, n.id]);
  }
  console.log(`  ✅ 更新 ${noExcerpt.length} 篇笔记`);

  // ── 4. 导入项目 ──
  console.log('\n🔄 导入项目...');
  const projectFiles = readdirSync(join(ROOT, 'src/content/projects')).filter(f => f.endsWith('.md'));
  for (const file of projectFiles) {
    const slug = file.replace('.md', '');
    const content = readFileSync(join(ROOT, 'src/content/projects', file), 'utf-8');

    // Parse frontmatter
    const fmMatch = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
    if (!fmMatch) continue;

    const fm = {};
    fmMatch[1].split('\n').forEach(line => {
      const [k, ...v] = line.split(':');
      const key = k.trim();
      const val = v.join(':').trim();
      if (key === 'tags') {
        fm[key] = JSON.parse(val.replace(/'/g, '"'));
      } else if (key === 'date') {
        fm[key] = val;
      } else {
        fm[key] = val.replace(/^"(.*)"$/, '$1');
      }
    });

    const body = fmMatch[2].trim();
    const excerpt = body.replace(/#{1,6}\s/g, '').replace(/\*\*/g, '').replace(/\n/g, ' ').trim().substring(0, 150);

    // Check if already exists
    const [existing] = await conn.query('SELECT id FROM notes WHERE type = ? AND slug = ?', ['project', slug]);
    if (existing.length > 0) {
      console.log(`  ⏭️  已存在: ${file}`);
      continue;
    }

    await conn.query(
      `INSERT INTO notes (type, title, slug, content, excerpt, course, tags, status, metadata, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        'project',
        fm.title || slug,
        slug,
        body,
        excerpt,
        fm.category || 'course',
        JSON.stringify(fm.tags || []),
        fm.status === 'in-progress' ? 'draft' : 'published',
        JSON.stringify({ date: fm.date || '', projectStatus: fm.status || 'completed' }),
        fm.date ? new Date(fm.date) : new Date(),
      ]
    );
    console.log(`  ✅ 导入: ${file}`);
  }

  // ── 5. 导入爱好 ──
  console.log('\n🔄 导入爱好...');
  const hobbyFiles = readdirSync(join(ROOT, 'src/content/hobbies')).filter(f => f.endsWith('.md'));
  for (const file of hobbyFiles) {
    const slug = file.replace('.md', '');
    const content = readFileSync(join(ROOT, 'src/content/hobbies', file), 'utf-8');

    const fmMatch = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
    if (!fmMatch) continue;

    const fm = {};
    fmMatch[1].split('\n').forEach(line => {
      const [k, ...v] = line.split(':');
      const key = k.trim();
      const val = v.join(':').trim();
      if (key === 'tags') {
        fm[key] = JSON.parse(val.replace(/'/g, '"'));
      } else if (key === 'date') {
        fm[key] = val;
      } else {
        fm[key] = val.replace(/^"(.*)"$/, '$1');
      }
    });

    const body = fmMatch[2].trim();
    const excerpt = body.replace(/#{1,6}\s/g, '').replace(/\*\*/g, '').replace(/\n/g, ' ').trim().substring(0, 150);

    const [existing] = await conn.query('SELECT id FROM notes WHERE type = ? AND slug = ?', ['hobby', slug]);
    if (existing.length > 0) {
      console.log(`  ⏭️  已存在: ${file}`);
      continue;
    }

    await conn.query(
      `INSERT INTO notes (type, title, slug, content, excerpt, course, tags, status, metadata, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        'hobby',
        fm.title || slug,
        slug,
        body,
        excerpt,
        '爱好',
        JSON.stringify(fm.tags || []),
        'published',
        JSON.stringify({ date: fm.date || '' }),
        fm.date ? new Date(fm.date) : new Date(),
      ]
    );
    console.log(`  ✅ 导入: ${file}`);
  }

  // ── 6. 验证 ──
  console.log('\n📊 迁移结果:');
  const [stats] = await conn.query(
    'SELECT type, COUNT(*) AS count, MIN(created_at) AS earliest FROM notes GROUP BY type ORDER BY FIELD(type, "note", "project", "hobby")'
  );
  for (const s of stats) {
    console.log(`  ${s.type}: ${s.count} 条`);
  }
  const [total] = await conn.query('SELECT COUNT(*) AS t FROM notes');
  console.log(`\n📦 总计: ${total[0].t} 条内容`);

  console.log('\n✅ 迁移完成！');
} catch (e) {
  console.error('❌ 迁移失败:', e.message);
  process.exit(1);
} finally {
  await conn.end();
}
