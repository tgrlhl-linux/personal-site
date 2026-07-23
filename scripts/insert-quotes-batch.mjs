import { readFileSync } from 'fs';
const envRaw = readFileSync('.env.local', 'utf-8');
for (const line of envRaw.split('\n')) {
  const trimmed = line.trim();
  if (!trimmed || trimmed.startsWith('#')) continue;
  const eqIdx = trimmed.indexOf('=');
  if (eqIdx === -1) continue;
  process.env[trimmed.slice(0, eqIdx).trim()] = trimmed.slice(eqIdx + 1).trim();
}

const { query, getPool } = await import('../src/db/mysql.js');

const quotes = [
  {
    title: '苦杏仁的气味 — 马尔克斯',
    slug: 'ku-xing-ren-de-qi-wei',
    author: '加西亚·马尔克斯',
    source: '霍乱时期的爱情',
    content: `不可避免，苦杏仁的气味总是让他想起爱情受阻后的命运。
刚一走进还处在昏暗之中的房间，胡维纳尔·乌尔比诺医生就察觉出这种味道`,
    tags: ['小说', '加西亚·马尔克斯'],
  },
  {
    title: '人间婆娑 — 慕容雪村',
    slug: 'ren-jian-po-suo',
    author: '慕容雪村',
    source: '原谅我红尘颠倒',
    content: `想人间婆娑，全无着落
看万般红紫，过眼成灰`,
    tags: ['小说', '慕容雪村'],
  },
  {
    title: '一把剑的回忆 — 博尔赫斯',
    slug: 'yi-ba-jian-de-hui-yi',
    author: '博尔赫斯',
    source: '深沉的玫瑰',
    content: `我也是一把剑的回忆
是弥散成金黄的孤寂的夕阳
阴影和空虚的缅想`,
    tags: ['诗歌', '博尔赫斯'],
  },
  {
    title: '每一次呼吸都像是一场盛世 — 陶立夏',
    slug: 'mei-yi-ci-hu-xi',
    author: '陶立夏',
    source: '',
    content: `院中的桂花开了
每一次呼吸都像是一场盛世`,
    tags: ['散文', '陶立夏'],
  },
  {
    title: '他也是另一个人的幻影 — 博尔赫斯',
    slug: 'ta-ye-shi-ling-yi-ge-ren-de-huan-ying',
    author: '博尔赫斯',
    source: '环形废墟',
    content: `他朝火焰走去
火焰没有吞噬他的皮肉
而是不烫不灼地安慰他，淹没了他
他宽慰地，惭愧地，害怕地知道
他自己也是一个幻影
另一个人梦中的幻影`,
    tags: ['小说', '博尔赫斯'],
  },
  {
    title: '站在世界的尽头 — 川端康成',
    slug: 'zhan-zai-shi-jie-de-jin-tou',
    author: '川端康成',
    source: '雪国',
    content: `他觉得自己好似站在世界的尽头
银河仿若一束巨大的流光
从身上流淌而去
彻骨的冷寂
又伴随着难言的魅惑与悸动`,
    tags: ['小说', '川端康成'],
  },
  {
    title: '花事阑珊 — 渡边淳一',
    slug: 'hua-shi-lan-shan',
    author: '渡边淳一',
    source: '失乐园',
    content: `无论何年何月，樱花都像行色匆匆的行人那样倏忽而逝
惹人生发怜惜之情
再没有花事阑珊时节看落花更凄寂的事了
季节像同樱花交替一样转向初夏
带来了日久天长，同时带来了百花齐放`,
    tags: ['小说', '渡边淳一'],
  },
  {
    title: '生命一纸嶙峋 — 邱陌',
    slug: 'sheng-ming-yi-zhi-lin-xun',
    author: '邱陌',
    source: '',
    content: `我不求处处春水决堤
只需几载光阴，几座黎明
再给我足够长的时间
将自由和疾病都写进眼睛
出逃吗？世界给我们判了无期徒刑
生命一纸嶙峋，正好撰我页页山青`,
    tags: ['现代诗', '邱陌'],
  },
  {
    title: '要一个黄昏 — 余秀华',
    slug: 'yao-yi-ge-huang-hun',
    author: '余秀华',
    source: '黄昏',
    content: `要一个黄昏，满是风
和正在落下的夕阳
如此，足够我爱这泥泞破碎的人间`,
    tags: ['诗歌', '余秀华'],
  },
  {
    title: '孤独国 — 周梦蝶',
    slug: 'gu-du-guo',
    author: '周梦蝶',
    source: '孤独国',
    content: `昨夜，我又梦见我
赤裸裸地跌坐在负雪的山峰上
这里的气候黏在冬天与春天的接口处
这里的雪是温柔如天鹅绒的
这里没有嬲骚的市声
只有时间嚼着时间的反刍的微响
这里没有人面兽
只有曼陀罗花，橄榄树和玉蝴蝶
白昼幽阒窈窕如夜，夜比白昼更绮丽，丰实，光灿
这里的寒冷如酒，封藏着诗和美
甚至虚空，也懂得无言对谈`,
    tags: ['诗歌', '周梦蝶'],
  },
];

let count = 0;
for (const q of quotes) {
  const sourceTag = q.source ? `《${q.source}》` : '';
  const fullExcerpt = `${q.author}${sourceTag}：${q.content.split('\n')[0].slice(0, 40)}…`;
  try {
    await query(
      `INSERT IGNORE INTO notes (type, title, slug, content, excerpt, course, tags, status)
       VALUES ('quote', ?, ?, ?, ?, '', ?, 'published')`,
      [q.title, q.slug, q.content, fullExcerpt, JSON.stringify(q.tags)]
    );
    console.log(`✅ ${++count}. ${q.title}`);
  } catch (err) {
    console.log(`❌ ${q.title}: ${err.message}`);
  }
}

console.log(`\n✨ 共写入 ${count} 条摘句`);
const pool = getPool();
await pool.end();
