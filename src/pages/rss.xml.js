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
  // 在 maxLen 附近找一个段落边界截断
  const cut = html.lastIndexOf('</p>', maxLen);
  if (cut > maxLen * 0.6) return html.slice(0, cut + 4);
  return html.slice(0, maxLen).replace(/<[^>]*$/, '') + '…';
}

function buildDescription(n) {
  if (n.excerpt) return truncateHtml(renderHtml(n.excerpt));
  if (n.content) return truncateHtml(renderHtml(n.content));
  return n.title || '';
}

export async function GET() {
  const items = await query(
    `SELECT id, title, slug, excerpt, content, course, type, created_at, updated_at
     FROM notes WHERE status='published' AND type IN (?)
     ORDER BY created_at DESC LIMIT 30`,
    [SUPPORTED_TYPES]
  );

  const rssItems = items.map(n => {
    const meta = TYPE_META[n.type] || TYPE_META.note;
    const date = new Date(n.created_at).toUTCString();
    const updated = n.updated_at ? new Date(n.updated_at).toUTCString() : date;
    const desc = buildDescription(n);
    const link = escapeXml(meta.link(n));
    const title = n.title || '';
    const course = n.course ? escapeXml(n.course) : '';

    // 全文 HTML（用于 content:encoded）
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

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
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

  return new Response(xml, {
    status: 200,
    headers: {
      'Content-Type': 'application/rss+xml; charset=utf-8',
      'Cache-Control': 'public, s-maxage=3600, stale-while-revalidate=300',
    },
  });
}
