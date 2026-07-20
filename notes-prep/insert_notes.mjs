/**
 * 导入复习笔记到 TiDB Cloud
 *
 * 从 notes-prep/ 读取所有课程笔记 Markdown 文件，按前缀分类
 * 插入到数据库 notes 表（个人网站内容引擎）
 *
 * 用法：
 *   node notes-prep/insert_notes.mjs          # 正式导入
 *   node notes-prep/insert_notes.mjs --dry-run # 预览（不写入）
 */

import { readFileSync, readdirSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import mysql from 'mysql2/promise';

const __dirname = dirname(fileURLToPath(import.meta.url));
const NOTES_DIR = join(__dirname);

// ── 从 .env.local 读数据库配置 ──
function loadEnv(filePath) {
  const env = {};
  if (!existsSync(filePath)) return env;
  const text = readFileSync(filePath, 'utf-8');
  for (const line of text.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#') || !trimmed.includes('=')) continue;
    const eqIdx = trimmed.indexOf('=');
    const key = trimmed.slice(0, eqIdx).trim();
    let val = trimmed.slice(eqIdx + 1).trim();
    if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
      val = val.slice(1, -1);
    }
    env[key] = val;
  }
  return env;
}

const env = loadEnv(join(__dirname, '..', '.env.local'));

const COURSE_MAP = {
  OS: '操作系统',
  DB: '数据库原理',
  PROB: '概率论与数理统计',
  POL: '习近平新时代中国特色社会主义思想概论',
};

// ── 列出所有笔记文件 ──
function resolveNotes() {
  const files = readdirSync(NOTES_DIR)
    .filter(f => f.endsWith('.md') && f.includes('-'))
    .sort();

  return files.map(fn => {
    const prefix = fn.split('-')[0];
    const courseName = COURSE_MAP[prefix];
    const content = readFileSync(join(NOTES_DIR, fn), 'utf-8');
    const parts = fn.replace('.md', '').split('-');
    const num = parts[1];
    const name = parts.slice(2).join(' ');
    const title = `${prefix}-${num} ${name}`;
    return { fn, courseName, title, content, prefix };
  }).filter(n => n.courseName);
}

async function main() {
  const dryRun = process.argv.includes('--dry-run');
  const notes = resolveNotes();

  console.log(`📚 找到 ${notes.length} 篇笔记\n`);

  // 分类统计
  const byCourse = {};
  for (const n of notes) {
    if (!byCourse[n.courseName]) byCourse[n.courseName] = [];
    byCourse[n.courseName].push(n);
  }
  for (const [course, items] of Object.entries(byCourse)) {
    console.log(`  ${course}: ${items.length} 篇`);
  }

  if (dryRun) {
    console.log('\n📋 预览模式，未写入数据库。\n文件列表:');
    for (const n of notes) {
      console.log(`  [${n.courseName}] ${n.title}  (${n.content.length} 字)`);
    }
    console.log('\n✅ 要正式导入，不加 --dry-run 运行即可。');
    return;
  }

  // ── 正式导入 ──
  const DB_CONFIG = {
    host: env.DB_HOST || 'gateway01.ap-northeast-1.prod.aws.tidbcloud.com',
    port: parseInt(env.DB_PORT || '4000'),
    user: env.DB_USER || 'root',
    password: env.DB_PASSWORD || '',
    database: env.DB_NAME || 'personal_site',
    ssl: { rejectUnauthorized: true },
    connectTimeout: 15000,
  };

  console.log(`\n📦 目标: ${DB_CONFIG.host}:${DB_CONFIG.port}/${DB_CONFIG.database}`);
  console.log('⏳ 正在连接...\n');

  const conn = await mysql.createConnection(DB_CONFIG);
  console.log('✅ 已连接到 TiDB Cloud\n');

  let ok = 0, fail = 0;
  for (const n of notes) {
    try {
      const tags = JSON.stringify([n.courseName, '期末复习']);
      const [result] = await conn.execute(
        'INSERT INTO notes (title, content, course, tags) VALUES (?, ?, ?, ?)',
        [n.title, n.content, n.courseName, tags]
      );
      console.log(`  ✅ [${n.courseName}] ${n.title} → id=${result.insertId}`);
      ok++;
    } catch (err) {
      console.error(`  ❌ [${n.courseName}] ${n.title}: ${err.message}`);
      fail++;
    }
  }

  await conn.end();
  console.log(`\n✨ 完成。成功 ${ok}，失败 ${fail}。`);
}

main().catch(err => {
  console.error('💥 错误:', err.message);
  console.log('提示: 确保 .env.local 中有正确的 DB_HOST / DB_PORT / DB_USER / DB_PASSWORD / DB_NAME');
  console.log('先用 --dry-run 预览:  node notes-prep/insert_notes.mjs --dry-run');
  process.exit(1);
});
