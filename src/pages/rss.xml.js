import { query } from '../db/mysql';
import { marked } from 'marked';

export const prerender = false;

const SITE = 'https://shengxia.dev';

const TYPE_META = {
  note:    { label: '📄', link: (n) => `${SITE}/notes/${n.id}` },
  project: { label: '🛠️', link: (n) => `${SITE}/projects/${n.slug || n.id}` },
  hobby:   { label: '🎨', link: (n) => `${SITE}/hobbies/${n.slug || n.id}` },
};

const SUPPORTED_TYPES = Object.keys(TYPE_META);

/** 对放入 XML 元素（非 CDATA）的值做实体转义 */
function escapeXml(str) {
  return (str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

/** 将 Markdown 渲染为 HTML 并处理相对路径 */
function renderHtml(md) {
  if (!md) return '';
  return marked.parse(md)
    .replace(/src="\/(?!\/)/g, `src="${SITE}/`);
}

/** 取前 N 个字符，尽量在段落边界截断 */
function truncateHtml(html, maxLen = 500) {
  if (!html || html.length <= maxLen) return html;
  const cut = html.lastIndexOf('</p>', maxLen);
  if (cut > maxLen * 0.6) return html.slice(0, cut + 4);
  return html.slice(0, maxLen).replace(/<[^>]*$/, '') + '…';
}

function buildDescription(n) {
  if (n.excerpt) return truncateHtml(renderHtml(n.excerpt));
  if (n.content) return truncateHtml(renderHtml(n.content));
  return n.title || '';
}

// ─── HTML 页面渲染 — 错位 Bento 风格 ──────────────────────────

const TYPE_COLORS = { note: '#3fb950', project: '#58a6ff', hobby: '#f0883e' };
const TYPE_LABELS = { note: '📄 笔记', project: '🛠️ 项目', hobby: '🎨 爱好' };
function tColor(t) { return TYPE_COLORS[t] || '#8b949e'; }
function tLabel(t) { return TYPE_LABELS[t] || '📄'; }

/** 根据索引分配网格跨度，产生错位感 */
function gridSpan(i) {
  // 第 1 个占 2 列宽 + 2 行高（主打），之后按 4 拍循环产生节奏
  const colSpan = i === 0 ? 2 : (i % 4 === 3 ? 2 : 1);
  const rowSpan = i === 0 ? 2 : (i % 5 === 2 ? 2 : 1);
  return { colSpan, rowSpan };
}

function renderHtmlPage(items) {
  const statGroups = {};
  for (const n of items) {
    const t = n.type || 'note';
    if (!statGroups[t]) statGroups[t] = 0;
    statGroups[t]++;
  }
  const statList = [
    { label: '笔记', count: statGroups.note || 0, color: '#3fb950', icon: '📄' },
    { label: '项目', count: statGroups.project || 0, color: '#58a6ff', icon: '🛠️' },
    { label: '爱好', count: statGroups.hobby || 0, color: '#f0883e', icon: '🎨' },
    { label: '总计', count: items.length, color: '#d29922', icon: '📡' },
  ];

  const cardsHtml = items.map((n, i) => {
    const { colSpan, rowSpan } = gridSpan(i);
    const color = tColor(n.type);
    const label = tLabel(n.type);
    const link = TYPE_META[n.type]?.link(n) || `${SITE}/notes/${n.id}`;
    const date = new Date(n.created_at).toLocaleDateString('zh-CN', {
      year: 'numeric', month: 'long', day: 'numeric',
    });
    const desc = buildDescription(n);
    const content = n.content ? renderHtml(n.content) : '';

    return `
    <article class="bc" style="--accent:${color};grid-column:span ${colSpan};grid-row:span ${rowSpan}" data-i="${i}">
      <div class="bc-top">
        <span class="bc-badge">${label}</span>
        <time class="bc-date">${date}</time>
        ${n.course ? `<span class="bc-course">${escapeXml(n.course)}</span>` : ''}
      </div>
      <h2 class="bc-title"><a href="${escapeXml(link)}" target="_blank">${escapeXml(n.title || '')}</a></h2>
      <div class="bc-desc">${desc}</div>
      ${content ? `
      <details class="bc-more">
        <summary>展开全文 ↓</summary>
        <div class="bc-body">${content}</div>
      </details>` : ''}
      <a href="${escapeXml(link)}" class="bc-read" target="_blank">阅读全文 →</a>
    </article>`;
  }).join('\n');

  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>RSS Feed — Guorui 的笔记与项目</title>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;600;700&display=swap"/>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, "Noto Sans SC", BlinkMacSystemFont, sans-serif;
      background: #0d1117;
      color: #e6edf3;
      line-height: 1.65;
      padding: 2rem 1rem;
    }
    .container { max-width: 960px; margin: 0 auto; }

    /* ── Header ── */
    .hd {
      text-align: center;
      padding-bottom: 2rem;
      border-bottom: 1px solid #21262d;
      margin-bottom: 2rem;
    }
    .hd h1 {
      font-size: 1.6rem;
      font-weight: 700;
      background: linear-gradient(135deg, #58a6ff, #3fb950, #f0883e, #d29922);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    .hd .sub { color: #8b949e; font-size: 0.875rem; margin-top: 0.4rem; }
    .hd .meta { color: #484f58; font-size: 0.8rem; margin-top: 0.25rem; }
    .hd .meta a { color: #f97316; text-decoration: none; }
    .hd .meta a:hover { text-decoration: underline; }

    /* ── Stats ── */
    .stats {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 0.75rem;
      margin-bottom: 1.5rem;
    }
    .stat {
      background: #161b22;
      border: 1px solid rgba(255,255,255,0.06);
      border-radius: 10px;
      padding: 0.8rem;
      text-align: center;
    }
    .stat .si { font-size: 1rem; }
    .stat .sn { font-size: 1.4rem; font-weight: 700; line-height: 1.2; }
    .stat .sl { font-size: 0.7rem; color: #8b949e; margin-top: 0.05rem; }

    /* ── Bento Grid ── */
    .grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 0.75rem;
    }

    .bc {
      background: #161b22;
      border: 1px solid #21262d;
      border-radius: 10px;
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      transition: border-color 0.2s, transform 0.15s, box-shadow 0.2s;
      position: relative;
      overflow: hidden;
    }
    /* 左上角色块装饰 */
    .bc::before {
      content: '';
      position: absolute;
      top: 0; left: 0;
      width: 3px;
      height: 100%;
      background: var(--accent);
      border-radius: 10px 0 0 10px;
      opacity: 0.5;
      transition: opacity 0.2s;
    }
    .bc:hover {
      border-color: var(--accent);
      transform: translateY(-2px);
      box-shadow: 0 0 20px color-mix(in srgb, var(--accent) 10%, transparent);
    }
    .bc:hover::before { opacity: 1; }

    .bc-top {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      flex-wrap: wrap;
      margin-bottom: 0.15rem;
    }
    .bc-badge {
      font-size: 0.7rem;
      padding: 0.05em 0.5em;
      border-radius: 4px;
      background: color-mix(in srgb, var(--accent) 20%, transparent);
      color: var(--accent);
      font-weight: 600;
      line-height: 1.6;
    }
    .bc-date { font-size: 0.72rem; color: #484f58; }
    .bc-course {
      font-size: 0.65rem;
      padding: 0.05em 0.5em;
      border-radius: 10px;
      background: #1c2128;
      color: #8b949e;
    }

    .bc-title { font-size: 1.05rem; font-weight: 600; line-height: 1.35; }
    .bc-title a { color: #e6edf3; text-decoration: none; }
    .bc-title a:hover { color: var(--accent); }

    .bc-desc {
      font-size: 0.85rem;
      color: #8b949e;
      line-height: 1.6;
      flex: 1;
    }
    .bc-desc p { margin: 0.3rem 0; }

    .bc-more { margin-top: 0.25rem; }
    .bc-more summary {
      font-size: 0.75rem;
      color: #484f58;
      cursor: pointer;
      user-select: none;
      display: inline-block;
    }
    .bc-more summary:hover { color: var(--accent); }

    .bc-body {
      margin-top: 0.6rem;
      padding-top: 0.6rem;
      border-top: 1px solid #21262d;
      font-size: 0.85rem;
      color: #c9d1d9;
      line-height: 1.7;
    }
    .bc-body img { max-width: 100%; border-radius: 4px; margin: 0.4rem 0; }
    .bc-body pre {
      background: #0d1117;
      border: 1px solid #21262d;
      border-radius: 4px;
      padding: 0.6rem 0.8rem;
      overflow-x: auto;
      font-size: 0.8rem;
      font-family: "Consolas", "SF Mono", "Fira Code", monospace;
      margin: 0.5rem 0;
    }
    .bc-body code {
      font-family: "Consolas", "SF Mono", "Fira Code", monospace;
      background: #1c2128;
      padding: 0.1em 0.3em;
      border-radius: 3px;
      font-size: 0.85em;
    }
    .bc-body pre code { background: none; padding: 0; }
    .bc-body blockquote {
      border-left: 3px solid #30363d;
      padding-left: 0.8rem;
      color: #8b949e;
      margin: 0.5rem 0;
    }
    .bc-body a { color: #58a6ff; }
    .bc-body h1, .bc-body h2, .bc-body h3 { margin: 0.8rem 0 0.4rem; color: #e6edf3; }
    .bc-body p { margin: 0.4rem 0; }
    .bc-body ul, .bc-body ol { padding-left: 1.4rem; margin: 0.4rem 0; }
    .bc-body li { margin: 0.2rem 0; }

    .bc-read {
      font-size: 0.75rem;
      color: #58a6ff;
      text-decoration: none;
      margin-top: 0.15rem;
      align-self: flex-start;
    }
    .bc-read:hover { text-decoration: underline; }

    /* ── Footer ── */
    .ft {
      text-align: center;
      padding: 2rem 0 1rem;
      color: #484f58;
      font-size: 0.8rem;
    }
    .ft a { color: #58a6ff; text-decoration: none; }
    .ft a:hover { text-decoration: underline; }

    /* ── Responsive ── */
    @media (max-width: 820px) {
      .grid { grid-template-columns: repeat(3, 1fr); gap: 0.65rem; }
      .stats { gap: 0.5rem; }
      .bc[data-i="0"] { grid-column: span 3; }
    }
    @media (max-width: 600px) {
      .grid { grid-template-columns: 1fr 1fr; gap: 0.5rem; }
      .stats { grid-template-columns: repeat(2, 1fr); }
      .bc { padding: 1rem; }
      .bc[data-i="0"] { grid-column: span 2; }
      .bc[style*="grid-column:span 2"] { grid-column: span 2; }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="hd">
      <h1>RSS · Guorui 的动态</h1>
      <p class="sub">软件工程笔记 · 课程项目 · 生活分享</p>
      <p class="meta">${items.length} 条内容 · <a href="/rss.xml">订阅 RSS</a></p>
    </div>

    <div class="stats">
      ${statList.map(s => `
      <div class="stat">
        <div class="si">${s.icon}</div>
        <div class="sn" style="color:${s.color}">${s.count}</div>
        <div class="sl">${s.label}</div>
      </div>`).join('\n')}
    </div>

    <div class="grid">
      ${cardsHtml}
    </div>

    <div class="ft">
      <a href="/">← 返回首页</a> · Powered by shengxia.dev
    </div>
  </div>
</body>
</html>`;
}

// ─── RSS XML 渲染 ──────────────────────────────────────────────

function renderRssXml(items) {
  const rssItems = items.map(n => {
    const meta = TYPE_META[n.type] || TYPE_META.note;
    const date = new Date(n.created_at).toUTCString();
    const updated = n.updated_at ? new Date(n.updated_at).toUTCString() : date;
    const desc = buildDescription(n);
    const link = escapeXml(meta.link(n));
    const title = n.title || '';
    const course = n.course ? escapeXml(n.course) : '';
    const fullHtml = n.content ? renderHtml(n.content) : '';

    return `
    <item>
      <title><![CDATA[${title}]]></title>
      <link>${link}</link>
      <guid isPermaLink="true">${link}</guid>
      <description><![CDATA[${desc}]]></description>
      <pubDate>${date}</pubDate>
      <updated>${updated}</updated>
      ${course ? `<category>${course}</category>` : ''}
      ${fullHtml ? `<content:encoded><![CDATA[${fullHtml}]]></content:encoded>` : ''}
    </item>`;
  }).join('\n');

  return `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>Guorui 的笔记与项目</title>
    <link>${SITE}</link>
    <description>童国睿的个人网站 — 软件工程学习笔记、项目记录与生活分享</description>
    <language>zh-cn</language>
    <atom:link href="${SITE}/rss.xml" rel="self" type="application/rss+xml"/>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    ${rssItems}
  </channel>
</rss>`;
}

// ─── 入口 ──────────────────────────────────────────────────────

export async function GET({ request }) {
  const items = await query(
    `SELECT id, title, slug, excerpt, content, course, type, created_at, updated_at
     FROM notes WHERE status='published' AND type IN (?)
     ORDER BY created_at DESC LIMIT 30`,
    [SUPPORTED_TYPES]
  );

  // 检测浏览器：Accept 包含 text/html 且不包含 application/rss+xml
  const accept = (request?.headers?.get('Accept') || '*/*').toLowerCase();
  const isBrowser = accept.includes('text/html') && !accept.includes('application/rss+xml');

  if (isBrowser) {
    return new Response(renderHtmlPage(items), {
      status: 200,
      headers: {
        'Content-Type': 'text/html; charset=utf-8',
        'Cache-Control': 'public, s-maxage=3600, stale-while-revalidate=300',
      },
    });
  }

  return new Response(renderRssXml(items), {
    status: 200,
    headers: {
      'Content-Type': 'application/rss+xml; charset=utf-8',
      'Cache-Control': 'public, s-maxage=3600, stale-while-revalidate=300',
    },
  });
}
