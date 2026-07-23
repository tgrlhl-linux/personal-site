import { query } from '../db/mysql';
import { marked } from 'marked';

export const prerender = false;

const SITE = 'https://shengxia.dev';

const TYPE_META = {
  note:    { label: '📄', link: (n) => `${SITE}/notes/${n.id}` },
  project: { label: '🛠️', link: (n) => `${SITE}/projects/${n.slug || n.id}` },
  hobby:   { label: '🎨', link: (n) => `${SITE}/hobbies/${n.slug || n.id}` },
  quote:   { label: '💬', link: (n) => `${SITE}/quotes/${n.slug || n.id}` },
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

// ─── HTML 页面渲染 — 主流列表风格 ─────────────────────────────

const TYPE_COLORS = { note: '#3fb950', project: '#58a6ff', hobby: '#f0883e', quote: '#bc8cff' };
function tColor(t) { return TYPE_COLORS[t] || '#8b949e'; }
function tLabel(t) { return { note: '笔记', project: '项目', hobby: '爱好', quote: '拾句' }[t] || '笔记'; }

function renderHtmlPage(items) {
  const cardsHtml = items.map((n, i) => {
    const color = tColor(n.type);
    const link = TYPE_META[n.type]?.link(n) || `${SITE}/notes/${n.id}`;
    const date = new Date(n.created_at).toLocaleDateString('zh-CN', {
      year: 'numeric', month: 'long', day: 'numeric',
    });
    const desc = buildDescription(n) || '';
    const content = n.content ? renderHtml(n.content) : '';

    return `
    <article class="entry" style="--accent:${color}">
      <div class="entry-meta">
        <span class="entry-type" style="color:${color}">${tLabel(n.type)}</span>
        <span class="entry-dot">·</span>
        <time class="entry-date">${date}</time>
        ${n.course ? `<span class="entry-course">${escapeXml(n.course)}</span>` : ''}
      </div>
      <h2 class="entry-title"><a href="${escapeXml(link)}" target="_blank">${escapeXml(n.title || '')}</a></h2>
      <div class="entry-desc">${desc}</div>
      ${content ? `
      <details class="entry-details">
        <summary>展开全文</summary>
        <div class="entry-body">${content}</div>
      </details>` : ''}
      <a href="${escapeXml(link)}" class="entry-link" target="_blank">阅读全文 →</a>
    </article>`;
  }).join('\n');

  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>RSS Feed — Guorui</title>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;600;700&display=swap"/>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, "Noto Sans SC", BlinkMacSystemFont, sans-serif;
      background: #0d1117;
      color: #e6edf3;
      line-height: 1.7;
    }

    /* ── Layout ── */
    .wrap { max-width: 720px; margin: 0 auto; padding: 0 1.5rem; }

    /* ── Header ── */
    .hd {
      padding: 2.5rem 0 1.5rem;
      border-bottom: 1px solid #21262d;
      margin-bottom: 1.5rem;
    }
    .hd h1 { font-size: 1.4rem; font-weight: 700; }
    .hd-hint { font-size: 0.8rem; color: #8b949e; margin-top: 0.3rem; }
    .hd-meta {
      display: flex; gap: 1rem; margin-top: 0.6rem;
      font-size: 0.78rem; color: #484f58;
    }
    .hd-meta a { color: #f97316; text-decoration: none; }
    .hd-meta a:hover { text-decoration: underline; }

    /* ── Entry List ── */
    .entry {
      padding: 1.1rem 0;
      border-bottom: 1px solid #21262d;
      transition: opacity 0.15s;
    }
    .entry:last-of-type { border-bottom: none; }

    .entry-meta {
      display: flex;
      align-items: center;
      gap: 0.3rem;
      font-size: 0.78rem;
      margin-bottom: 0.35rem;
    }
    .entry-type { font-weight: 600; font-size: 0.72rem; }
    .entry-dot { color: #30363d; }
    .entry-date { color: #484f58; }
    .entry-course {
      font-size: 0.68rem;
      padding: 0.05em 0.5em;
      border-radius: 8px;
      background: #1c2128;
      color: #8b949e;
    }

    .entry-title { font-size: 1.1rem; font-weight: 600; line-height: 1.4; }
    .entry-title a { color: #e6edf3; text-decoration: none; }
    .entry-title a:hover { color: var(--accent, #58a6ff); }

    .entry-desc {
      margin-top: 0.35rem;
      font-size: 0.88rem;
      color: #8b949e;
      line-height: 1.6;
    }
    .entry-desc p { margin: 0.3rem 0; }

    .entry-details { margin-top: 0.4rem; }
    .entry-details summary {
      font-size: 0.78rem;
      color: #484f58;
      cursor: pointer;
      user-select: none;
      display: inline-block;
    }
    .entry-details summary:hover { color: var(--accent, #58a6ff); }

    .entry-body {
      margin-top: 0.6rem;
      padding-top: 0.6rem;
      border-top: 1px solid #21262d;
      font-size: 0.88rem;
      color: #c9d1d9;
      line-height: 1.7;
    }
    .entry-body img { max-width: 100%; border-radius: 4px; margin: 0.5rem 0; }
    .entry-body pre {
      background: #0d1117;
      border: 1px solid #21262d;
      border-radius: 4px;
      padding: 0.6rem 0.8rem;
      overflow-x: auto;
      font-size: 0.82rem;
      font-family: "Consolas", "SF Mono", "Fira Code", monospace;
      margin: 0.5rem 0;
    }
    .entry-body code {
      font-family: "Consolas", "SF Mono", "Fira Code", monospace;
      background: #1c2128;
      padding: 0.1em 0.3em;
      border-radius: 3px;
      font-size: 0.85em;
    }
    .entry-body pre code { background: none; padding: 0; }
    .entry-body blockquote {
      border-left: 3px solid #30363d;
      padding-left: 0.8rem;
      color: #8b949e;
      margin: 0.5rem 0;
    }
    .entry-body a { color: #58a6ff; }
    .entry-body h1, .entry-body h2, .entry-body h3 { margin: 0.8rem 0 0.4rem; color: #e6edf3; }
    .entry-body p { margin: 0.4rem 0; }
    .entry-body ul, .entry-body ol { padding-left: 1.4rem; margin: 0.4rem 0; }

    .entry-link {
      display: inline-block;
      margin-top: 0.4rem;
      font-size: 0.78rem;
      color: #484f58;
      text-decoration: none;
      transition: color 0.15s;
    }
    .entry-link:hover { color: var(--accent, #58a6ff); }

    /* ── Footer ── */
    .ft {
      padding: 1.5rem 0 2.5rem;
      text-align: center;
      font-size: 0.78rem;
      color: #484f58;
    }
    .ft a { color: #58a6ff; text-decoration: none; }
    .ft a:hover { text-decoration: underline; }
  </style>
</head>
<body>
  <div class="wrap">
    <header class="hd">
      <h1>RSS · 最近更新</h1>
      <p class="hd-hint">${items.length} 条内容 · 来自 Guorui 的个人网站</p>
      <div class="hd-meta">
        <span>📄 笔记 ${items.filter(n => n.type === 'note').length}</span>
        <span>🛠️ 项目 ${items.filter(n => n.type === 'project').length}</span>
        <span>🎨 爱好 ${items.filter(n => n.type === 'hobby').length}</span>
        <span>💬 拾句 ${items.filter(n => n.type === 'quote').length}</span>
        <a href="/rss.xml">订阅 →</a>
      </div>
    </header>

    ${cardsHtml}

    <footer class="ft">
      <a href="/">← 返回首页</a>
    </footer>
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
