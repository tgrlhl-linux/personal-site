import { query } from '../db/mysql';

export const prerender = false;

export async function GET() {
  const notes = await query(
    "SELECT id, title, excerpt, course, created_at, updated_at FROM notes WHERE type='note' AND status='published' ORDER BY created_at DESC LIMIT 20"
  );

  const siteUrl = 'https://shengxia.dev';

  const items = notes.map(n => {
    const date = new Date(n.created_at).toUTCString();
    const updated = n.updated_at ? new Date(n.updated_at).toUTCString() : date;
    const desc = (n.excerpt || n.title || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const title = (n.title || '').replace(/&/g, '&amp;').replace(/</g, '&lt;');
    return `
    <item>
      <title><![CDATA[${title}]]></title>
      <link>${siteUrl}/notes/${n.id}</link>
      <guid isPermaLink="true">${siteUrl}/notes/${n.id}</guid>
      <description><![CDATA[${desc}]]></description>
      <pubDate>${date}</pubDate>
      <updated>${updated}</updated>
      ${n.course ? `<category>${n.course.replace(/&/g, '&amp;')}</category>` : ''}
    </item>`;
  }).join('\n');

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>Guorui 的笔记</title>
    <link>${siteUrl}</link>
    <description>童国睿的个人网站 — 软件工程学习笔记与项目记录</description>
    <language>zh-cn</language>
    <atom:link href="${siteUrl}/rss.xml" rel="self" type="application/rss+xml"/>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    ${items}
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
