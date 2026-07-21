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

// ─── HTML 页面渲染 ────────────────────────────────────────────

function typeColor(type) {
  switch (type) {
    case 'note':    return '#3fb950';
    case 'project': return '#58a6ff';
    case 'hobby':   return '#f0883e';
    default:        return '#8b949e';
  }
}

function typeLabel(type) {
  return TYPE_META[type]?.label || '';
}

function renderHtmlPage(items) {
  const itemHtml = items.map(n => {
    const content = n.content ? renderHtml(n.content) : '';
    const desc = buildDescription(n);
    const link = TYPE_META[n.type]?.link(n) || `${SITE}/notes/${n.id}`;
    const date = new Date(n.created_at).toLocaleDateString('zh-CN', {
      year: 'numeric', month: 'long', day: 'numeric',
    });
    const color = typeColor(n.type);
    const label = typeLabel(n.type);

    return `
    <article class="item" style="--accent:${color}">
      <div class="item-header">
        <span class="type-tag">${label}</span>
        <time class="date">${date}</time>
      </div>
      <h2><a href="${escapeXml(link)}" target="_blank">${escapeXml(n.title || '')}</a></h2>
      ${n.course ? `<span class="course-tag">${escapeXml(n.course)}</span>` : ''}
      <div class="desc">${desc}</div>
      ${content ? `
      <details class="full-content">
        <summary>展开全文</summary>
        <div class="body">${content}</div>
      </details>` : ''}
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
      line-height: 1.7;
      padding: 2rem 1rem;
    }
    .container { max-width: 760px; margin: 0 auto; }

    .header {
      text-align: center;
      padding-bottom: 2rem;
      border-bottom: 1px solid #21262d;
      margin-bottom: 2rem;
    }
    .header h1 {
      font-size: 1.5rem;
      font-weight: 700;
      background: linear-gradient(135deg, #58a6ff, #3fb950, #f0883e);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    .header .sub {
      color: #8b949e;
      font-size: 0.875rem;
      margin-top: 0.5rem;
    }
    .header .meta {
      color: #484f58;
      font-size: 0.8rem;
      margin-top: 0.25rem;
    }

    .item {
      background: #161b22;
      border: 1px solid #21262d;
      border-radius: 8px;
      padding: 1.25rem 1.5rem;
      margin-bottom: 1rem;
      transition: border-color 0.2s;
    }
    .item:hover { border-color: var(--accent, #30363d); }

    .item-header {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      margin-bottom: 0.5rem;
    }
    .type-tag {
      font-size: 0.75rem;
      padding: 0 6px;
      border-radius: 4px;
      background: var(--accent);
      color: #0d1117;
      font-weight: 600;
      line-height: 1.5;
    }
    .date { font-size: 0.8rem; color: #484f58; }

    .item h2 { font-size: 1.1rem; font-weight: 600; margin-bottom: 0.4rem; }
    .item h2 a { color: #e6edf3; text-decoration: none; }
    .item h2 a:hover { color: var(--accent); }

    .course-tag {
      display: inline-block;
      font-size: 0.72rem;
      padding: 1px 8px;
      border-radius: 10px;
      background: #1c2128;
      color: #8b949e;
      margin-bottom: 0.6rem;
    }

    .desc {
      font-size: 0.9rem;
      color: #c9d1d9;
      line-height: 1.65;
    }

    .full-content { margin-top: 0.75rem; }
    .full-content summary {
      font-size: 0.8rem;
      color: #8b949e;
      cursor: pointer;
      user-select: none;
    }
    .full-content summary:hover { color: #58a6ff; }

    .body {
      margin-top: 0.75rem;
      padding-top: 0.75rem;
      border-top: 1px solid #21262d;
      font-size: 0.9rem;
      color: #c9d1d9;
      line-height: 1.7;
    }
    .body img { max-width: 100%; border-radius: 4px; margin: 0.5rem 0; }
    .body pre {
      background: #0d1117;
      border: 1px solid #21262d;
      border-radius: 4px;
      padding: 0.75rem 1rem;
      overflow-x: auto;
      font-size: 0.82rem;
      font-family: "Consolas", "SF Mono", "Fira Code", monospace;
      margin: 0.6rem 0;
    }
    .body code {
      font-family: "Consolas", "SF Mono", "Fira Code", monospace;
      background: #1c2128;
      padding: 0.1em 0.3em;
      border-radius: 3px;
      font-size: 0.85em;
    }
    .body pre code { background: none; padding: 0; }
    .body blockquote {
      border-left: 3px solid #30363d;
      padding-left: 1rem;
      color: #8b949e;
      margin: 0.6rem 0;
    }
    .body a { color: #58a6ff; }
    .body h1, .body h2, .body h3, .body h4 {
      margin: 1rem 0 0.5rem;
      color: #e6edf3;
    }
    .body p { margin: 0.5rem 0; }
    .body ul, .body ol { padding-left: 1.5rem; margin: 0.5rem 0; }
    .body li { margin: 0.25rem 0; }

    .footer {
      text-align: center;
      padding: 2rem 0 1rem;
      color: #484f58;
      font-size: 0.8rem;
    }
    .footer a { color: #58a6ff; text-decoration: none; }
    .footer a:hover { text-decoration: underline; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Guorui 的笔记与项目</h1>
      <p class="sub">童国睿的个人网站 — 软件工程学习笔记、项目记录与生活分享</p>
      <p class="meta">共 ${items.length} 条 · <a href="/rss.xml" style="color:#f97316">订阅 RSS</a></p>
    </div>
    ${itemHtml}
    <div class="footer">
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
