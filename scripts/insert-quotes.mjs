import fs from 'fs';
import { query, getPool } from '../src/db/mysql.js';

// Load .env.local manually since this runs outside Astro
const envRaw = fs.readFileSync('.env.local', 'utf-8');
for (const line of envRaw.split('\n')) {
  const trimmed = line.trim();
  if (!trimmed || trimmed.startsWith('#')) continue;
  const eqIdx = trimmed.indexOf('=');
  if (eqIdx === -1) continue;
  const key = trimmed.slice(0, eqIdx).trim();
  const val = trimmed.slice(eqIdx + 1).trim();
  process.env[key] = val;
}

const poems = [
  {
    title: '我也有我的平仄',
    slug: 'wo-ye-you-wo-de-ping-ze',
    content: `我不算谁的附庸
也不是某段的支流河
比起这些
我更想成为顷刻间的滂沱
旷野里乍起的风波
又或是
唐朝遗风外悬着的唯一月色
人生本就是一首待写的诗歌
而他们的文字浅薄
不该被潦草地印刷着
所以在我笔下哎
一重山有一重山的错落
我也有我的平仄`,
    excerpt: '我不算谁的附庸，也不是某段的支流河，比起这些，我更想成为顷刻间的滂沱，旷野里乍起的风波，又或是，唐朝遗风外悬着的唯一月色……一重山有一重山的错落，我也有我的平仄',
    tags: ['现代诗', '自我', '山'],
  },
  {
    title: '自由是座万人朝圣的神山',
    slug: 'zi-you-shi-zuo-wan-ren-chao-sheng-de-shen-shan',
    content: `命运让我留在这里
我的眼睛变成湖泊
眼泪变成湖水
淤青长成一座座峰峦
我用沉默丈量生与死的距离
灵魂碎成经幡
我叩首再叩首
岁月不改
前路漫漫
桎梏里
自由也是座万人朝圣的神山`,
    excerpt: '命运让我留在这里，我的眼睛变成湖泊，眼泪变成湖水，淤青长成一座座峰峦，我用沉默丈量生与死的距离，灵魂碎成经幡……桎梏里，自由也是座万人朝圣的神山',
    tags: ['现代诗', '自由', '山'],
  },
];

try {
  for (const p of poems) {
    await query(
      `INSERT IGNORE INTO notes (type, title, slug, content, excerpt, course, tags, status)
       VALUES ('quote', ?, ?, ?, ?, '', ?, 'published')`,
      [p.title, p.slug, p.content, p.excerpt, JSON.stringify(p.tags)]
    );
    console.log(`✅ 已插入: ${p.title}`);
  }
  console.log('\n✨ 两句诗都已入库！');
} catch (err) {
  console.error('插入失败:', err);
} finally {
  const pool = getPool();
  await pool.end();
}
