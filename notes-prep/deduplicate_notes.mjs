#!/usr/bin/env node
/**
 * 去重迁移脚本：删除 v1 旧版笔记（"课程名 · " 格式），保留 v2（"前缀-编号" 格式）
 *
 * 用法：
 *   node deduplicate_notes.mjs              # 执行去重
 *   node deduplicate_notes.mjs --dry-run     # 预览
 *
 * 背景：数据库中有两套笔记，v2 是 v1 的超集或内容一致
 *   v1: "操作系统 · 01 操作系统引论" (旧)
 *   v2: "OS-01 操作系统引论" (新，内容更完整)
 */

import mysql from 'mysql2/promise';

const DB_CONFIG = {
  host: process.env.DB_HOST || 'gateway01.ap-northeast-1.prod.aws.tidbcloud.com',
  port: parseInt(process.env.DB_PORT || '4000'),
  user: process.env.DB_USER || '28bKJwXcdrmiau1.root',
  password: process.env.DB_PASSWORD || 'UEB4Z0TNixwRvvzH',
  database: process.env.DB_NAME || 'personal_site',
  ssl: { rejectUnauthorized: true },
};

const isDryRun = process.argv.includes('--dry-run');

async function main() {
  const conn = await mysql.createConnection(DB_CONFIG);
  console.log(isDryRun ? '=== DRY RUN ===\n' : '=== DEDUP ===\n');

  // 查找所有 v1 格式的笔记（"课程名 · 编号 名称"）
  const [v1Rows] = await conn.query(
    "SELECT id, title, course FROM notes WHERE type='note' AND status='published' AND title LIKE '%·%' ORDER BY course, id"
  );

  console.log(`找到 ${v1Rows.length} 篇 v1 旧版笔记\n`);

  // 按课程分组显示
  const groups = {};
  for (const r of v1Rows) {
    if (!groups[r.course]) groups[r.course] = [];
    groups[r.course].push(r);
  }
  for (const [course, items] of Object.entries(groups)) {
    console.log(`  [${course}] ${items.length} 篇`);
  }

  if (isDryRun) {
    console.log('\n✅ Dry-run 完成，未执行删除。');
    await conn.end();
    return;
  }

  // 删除 v1 旧版
  for (const r of v1Rows) {
    await conn.execute("DELETE FROM notes WHERE id = ?", [r.id]);
    console.log(`  ✗ 删除 id=${r.id}  "${r.title}"`);
  }

  console.log(`\n✅ 共删除 ${v1Rows.length} 篇旧版笔记`);

  // 添加唯一索引防止未来重复（先检查是否已存在）
  const [idxCheck] = await conn.query("SHOW INDEX FROM notes WHERE Key_name = 'idx_title_course'");
  if (idxCheck.length === 0) {
    try {
      await conn.execute("ALTER TABLE notes ADD UNIQUE INDEX idx_title_course (title(190), course(100))");
      console.log('  ✓ 添加唯一索引 idx_title_course (title+courser)');
    } catch (e) {
      console.log('  ⚠ 添加索引失败（可能还有残留重复）:', e.message);
    }
  } else {
    console.log('  ✓ 唯一索引已存在');
  }

  await conn.end();
}

main().catch(e => {
  console.error('❌ 失败:', e.message);
  process.exit(1);
});
