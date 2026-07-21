<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:atom="http://www.w3.org/2005/Atom"
  xmlns:content="http://purl.org/rss/1.0/modules/content/"
  exclude-result-prefixes="atom content">

<xsl:output method="html" encoding="UTF-8" indent="yes"/>

<xsl:template match="/">
<html lang="zh-CN">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title><xsl:value-of select="rss/channel/title"/> — RSS Feed</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Noto Sans SC", "Segoe UI", sans-serif;
      background: #0d1117;
      color: #e6edf3;
      line-height: 1.7;
      padding: 2rem 1rem;
    }
    .container { max-width: 800px; margin: 0 auto; }

    /* Header */
    .feed-header {
      text-align: center;
      padding-bottom: 2rem;
      border-bottom: 1px solid #21262d;
      margin-bottom: 2rem;
    }
    .feed-header h1 {
      font-size: 1.5rem;
      font-weight: 700;
      background: linear-gradient(135deg, #58a6ff, #3fb950, #f0883e);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    .feed-header p { color: #8b949e; font-size: 0.875rem; margin-top: 0.5rem; }
    .feed-header .meta { color: #484f58; font-size: 0.75rem; margin-top: 0.25rem; }

    /* Item */
    .item {
      background: #161b22;
      border: 1px solid #21262d;
      border-radius: 8px;
      padding: 1.25rem 1.5rem;
      margin-bottom: 1rem;
      transition: border-color 0.2s;
    }
    .item:hover { border-color: #30363d; }

    .item h2 {
      font-size: 1.125rem;
      font-weight: 600;
      margin-bottom: 0.5rem;
    }
    .item h2 a {
      color: #58a6ff;
      text-decoration: none;
    }
    .item h2 a:hover { text-decoration: underline; }

    .item .date {
      font-size: 0.75rem;
      color: #484f58;
      margin-bottom: 0.75rem;
    }

    /* 针对不同 category 用不同颜色标记 */
    .item .category {
      display: inline-block;
      font-size: 0.7rem;
      padding: 1px 8px;
      border-radius: 10px;
      margin-right: 0.5rem;
      background: #1c2128;
      color: #8b949e;
    }

    .item .content {
      font-size: 0.9rem;
      color: #c9d1d9;
    }
    .item .content img { max-width: 100%; border-radius: 4px; margin: 0.5rem 0; }
    .item .content pre {
      background: #0d1117;
      border: 1px solid #21262d;
      border-radius: 4px;
      padding: 0.75rem 1rem;
      overflow-x: auto;
      font-size: 0.8rem;
      font-family: "Consolas", "SF Mono", "Fira Code", monospace;
      margin: 0.5rem 0;
    }
    .item .content code {
      font-family: "Consolas", "SF Mono", "Fira Code", monospace;
      background: #1c2128;
      padding: 0.1em 0.3em;
      border-radius: 3px;
      font-size: 0.85em;
    }
    .item .content pre code { background: none; padding: 0; }
    .item .content blockquote {
      border-left: 3px solid #30363d;
      padding-left: 1rem;
      color: #8b949e;
      margin: 0.5rem 0;
    }
    .item .content a { color: #58a6ff; }

    /* Excerpt vs full content toggle */
    .item .excerpt { margin-bottom: 0.5rem; }
    .item .full-content { display: none; margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid #21262d; }
    .item .toggle-btn {
      display: inline-block;
      font-size: 0.8rem;
      color: #8b949e;
      cursor: pointer;
      user-select: none;
    }
    .item .toggle-btn:hover { color: #58a6ff; }

    /* Footer */
    .feed-footer {
      text-align: center;
      padding: 2rem 0;
      color: #484f58;
      font-size: 0.8rem;
    }
    .feed-footer a { color: #58a6ff; text-decoration: none; }
  </style>
</head>
<body>
  <div class="container">
    <!-- Header -->
    <div class="feed-header">
      <h1><xsl:value-of select="rss/channel/title"/></h1>
      <p><xsl:value-of select="rss/channel/description"/></p>
      <div class="meta">
        共 <xsl:value-of select="count(rss/channel/item)"/> 条 ·
        <xsl:value-of select="rss/channel/language"/>
      </div>
    </div>

    <!-- Items -->
    <xsl:for-each select="rss/channel/item">
      <div class="item">
        <h2><a href="{link}" target="_blank"><xsl:value-of select="title"/></a></h2>
        <div class="date">
          <xsl:value-of select="pubDate"/>
        </div>
        <xsl:if test="category">
          <div class="category"><xsl:value-of select="category"/></div>
        </xsl:if>
        <!-- 渲染 description 中的 HTML -->
        <div class="content excerpt">
          <xsl:copy-of select="description/node()"/>
        </div>
        <!-- 如果有 content:encoded，可展开查看全文 -->
        <xsl:if test="content:encoded">
          <div class="content full-content">
            <xsl:copy-of select="content:encoded/node()"/>
          </div>
          <span class="toggle-btn" onclick="this.parentElement.querySelector('.full-content').style.display = this.parentElement.querySelector('.full-content').style.display === 'none' ? 'block' : 'none'; this.textContent = this.textContent === '展开全文 ▼' ? '收起全文 ▲' : '展开全文 ▼'">展开全文 ▼</span>
        </xsl:if>
      </div>
    </xsl:for-each>

    <div class="feed-footer">
      <a href="/">← 返回首页</a> ·
      Powered by <a href="https://shengxia.dev">shengxia.dev</a>
    </div>
  </div>
</body>
</html>
</xsl:template>

</xsl:stylesheet>
