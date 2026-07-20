import { query } from '../db/mysql';

export const prerender = false;

const siteUrl = 'https://shengxia.dev';

const TYPE_META = {
  note:    { label: '📄', link: (n) => `${siteUrl}/notes/${n.id}` },
  project: { label: '🛠️', link: (n) => `${siteUrl}/projects/${n.slug || n.id}` },
  hobby:   { label: '🎨', link: (n) => `${siteUrl}/hobbies/${n.slug || n.id}` },
};

function xmlEscape(str) {
  return (str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function buildDescription(n) {
  // Use excerpt first, then fallback to first 300 chars of content
  if (n.excerpt) return xmlEscape(n.excerpt);
  if (n.content) {
    const clean = n.content.replace(/[#*_`\[\]]/g, '').replace(/\n+/g, ' ').trim();
    return xmlEscape(clean.substring(0, 300));
  }
  return xmlEscape(n.title);
}

export async function GET() {
  const items = await query(
    `SELECT id, title, slug, excerpt, content, course, type, created_at, updated_at
     FROM notes WHERE status='published'
     ORDER BY created_at DESC LIMIT 30`
  );

  const rssItems = items.map(n => {
    const meta = TYPE_META[n.type] || TYPE_META.note;
    const date = new Date(n.created_at).toUTCString();
    const updated = n.updated_at ? new Date(n.updated_at).toUTCString() : date;
    const desc = buildDescription(n);
    const title = xmlEscape(n.title);
    const link = meta.link(n);

    return `
    <item>
      <title><![CDATA[${title}]]></title>
      <link>${link}</link>
      <guid isPermaLink="true">${link}</guid>
      <description><![CDATA[${desc}]]></description>
      <pubDate>${date}</pubDate>
      ${n.course ? `<category>${xmlEscape(n.course)}</category>` : ''}
    </item>`;
  }).join('\n');

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Guorui 的学习笔记</title>
    <link>${siteUrl}</link>
    <description>童国睿的个人网站 — 软件工程学习笔记、项目记录与生活分享</description>
    <language>zh-cn</language>
    <atom:link href="${siteUrl}/rss.xml" rel="self" type="application/rss+xml"/>
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
