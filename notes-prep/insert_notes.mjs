import { readFileSync, readdirSync } from 'fs';
import { join } from 'path';
import mysql from 'mysql2/promise';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));

const NOTES_DIR = join(__dirname);
const DB_CONFIG = {
  host: 'gateway01.ap-northeast-1.prod.aws.tidbcloud.com',
  port: 4000,
  user: '28bKJwXcdrmiau1.root',
  password: 'UEB4Z0TNixwRvvzH',
  database: 'personal_site',
  ssl: { rejectUnauthorized: true },
  connectTimeout: 15000,
};

const COURSE_MAP = {
  OS: '操作系统',
  DB: '数据库原理',
  PROB: '概率论与数理统计',
  POL: '习近平新时代中国特色社会主义思想概论',
};

async function main() {
  const dryRun = process.argv.includes('--dry-run');

  try {
    const conn = await mysql.createConnection(DB_CONFIG);
    console.log('Connected to TiDB Cloud.\n');

    const files = readdirSync(NOTES_DIR)
      .filter(f => f.endsWith('.md') && f.includes('-'))
      .sort();

    let count = 0;
    for (const fn of files) {
      const prefix = fn.split('-')[0];
      const courseName = COURSE_MAP[prefix];
      if (!courseName) continue;

      const content = readFileSync(join(NOTES_DIR, fn), 'utf-8');

      // Build title from filename
      const parts = fn.replace('.md', '').split('-');
      const num = parts[1];
      const titleParts = parts.slice(2);
      const name = titleParts.join(' ');
      const title = `${prefix}-${num} ${name}`;

      const tags = JSON.stringify([courseName, '期末复习']);

      if (dryRun) {
        console.log(`[${courseName}] ${title} (${content.length} chars)`);
        count++;
        continue;
      }

      try {
        const [result] = await conn.execute(
          'INSERT INTO notes (title, content, course, tags) VALUES (?, ?, ?, ?)',
          [title, content, courseName, tags]
        );
        console.log(`  OK [${courseName}] ${title} -> id=${result.insertId}`);
        count++;
      } catch (err) {
        console.error(`  ERR [${courseName}] ${title}: ${err.message}`);
      }
    }

    await conn.end();
    console.log(`\nDone. Inserted ${count} notes.`);

  } catch (err) {
    console.error('Connection failed:', err.message);
    console.log('Use --dry-run to preview without inserting.');
    process.exit(1);
  }
}

main();
