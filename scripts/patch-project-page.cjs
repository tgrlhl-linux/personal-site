const fs = require('fs');
let c = fs.readFileSync('src/pages/projects/[...slug].astro', 'utf-8');

// 1. Add marked import
c = c.replace(
  "import projectCode from '../../data/projectCode';",
  "import projectCode from '../../data/projectCode';\nimport { marked } from 'marked';\n\nmarked.setOptions({ breaks: true, gfm: true });"
);

// 2. Add server-side rendering
c = c.replace(
  "function codeLines(code) { return (code||'').split('\\n').length; }",
  "function codeLines(code) { return (code||'').split('\\n').length; }\n\n// Pre-render analysis markdown server-side\nlet renderedAnalysis = '';\nif (analysisContent) {\n  renderedAnalysis = marked.parse(analysisContent);\n}"
);

// 3. Replace analysis content div
c = c.replace(
  '<div class="pd-card-body pd-analysis" id="analysisContent">{analysisContent}</div>',
  '<div class="pd-card-body pd-analysis" set:html={renderedAnalysis}></div>'
);

// 4. Remove client-side marked code (keep copy code)
const clientScriptStart = "    <script>\n      import { marked } from 'marked';\n      marked.setOptions({ breaks: true, gfm: true });\n\n      // Render analysis report markdown\n      const analysisEl = document.getElementById('analysisContent');\n      if (analysisEl) analysisEl.innerHTML = marked.parse(analysisEl.textContent);\n\n      // Render project content\n      const contentEl = document.getElementById('projectContent');\n      if (contentEl) contentEl.innerHTML = marked.parse(contentEl.textContent);\n";
c = c.replace(clientScriptStart, '');

// 5. Remove CDN highlight.js CSS and inline script
c = c.replace(
  '\n    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">\n    <script is:inline>\n    (function(){\n      var s=document.createElement(\'script\');\n      s.src=\'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js\';\n      s.onload=function(){\n        var langs=[\'java\',\'python\',\'rust\',\'bash\',\'sql\',\'javascript\',\'xml\'];\n        var loaded=0;\n        langs.forEach(function(l){\n          var ls=document.createElement(\'script\');\n          ls.src=\'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/\'+l+\'.min.js\';\n          ls.onload=ls.onerror=function(){loaded++;if(loaded>=langs.length)highlight();};\n          document.head.appendChild(ls);\n        });\n        setTimeout(highlight,3000);\n        function highlight(){\n          document.querySelectorAll(\'.pd-code-block code\').forEach(function(el){\n            if(typeof hljs!==\'undefined\')hljs.highlightElement(el);\n          });\n        }\n      };\n      document.head.appendChild(s);\n    })();\n    </script>',
  ''
);

// 6. Add highlight.js CSS import to frontmatter
c = c.replace(
  "import { marked } from 'marked';",
  "import { marked } from 'marked';\nimport 'highlight.js/styles/github-dark.css';"
);

fs.writeFileSync('src/pages/projects/[...slug].astro', c);
console.log('Done - file patched');
