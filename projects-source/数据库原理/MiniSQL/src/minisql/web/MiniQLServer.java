package minisql.web;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import minisql.MiniSQL;

import java.io.*;
import java.lang.management.ManagementFactory;
import java.net.InetSocketAddress;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Executors;

/**
 * MiniSQL Web Server — zero external dependencies.
 * Embeds a single-page web UI served via JDK's built-in HttpServer.
 */
public class MiniQLServer {

    private final MiniSQL miniSQL;
    private final String dataDir;
    private final int port;
    private int queryCount = 0;

    public static void main(String[] args) throws IOException {
        String dataDir = args.length > 0 ? args[0] : "data";
        int port = 9090;
        if (args.length > 1) {
            try { port = Integer.parseInt(args[1]); } catch (NumberFormatException e) { /* default */ }
        }

        MiniQLServer server = new MiniQLServer(dataDir, port);
        server.start();
    }

    public MiniQLServer(String dataDir, int port) {
        this.dataDir = dataDir;
        this.port = port;
        this.miniSQL = new MiniSQL(dataDir);
    }

    // ══════════════════════════════════════════════════════════════
    //  Server setup
    // ══════════════════════════════════════════════════════════════

    public void start() throws IOException {
        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);

        server.createContext("/api/query",  this::handleQuery);
        server.createContext("/api/stats",  this::handleStats);
        server.createContext("/api/tables", this::handleTables);
        server.createContext("/api/export", this::handleExport);
        server.createContext("/",           this::servePage);

        server.setExecutor(Executors.newCachedThreadPool());
        server.start();

        System.out.println("╔══════════════════════════════════════════════════╗");
        System.out.println("║  MiniQL Web Server                             ║");
        System.out.println("║  Open → http://localhost:" + port + (port < 10000 ? "                     ║" : "                    ║"));
        System.out.println("║  Data → " + dataDir + "                           ║");
        System.out.println("║  Ctrl+C to stop                                ║");
        System.out.println("╚══════════════════════════════════════════════════╝");

        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            System.out.println("\nServer stopped.");
            server.stop(0);
        }));
    }

    // ══════════════════════════════════════════════════════════════
    //  API handlers
    // ══════════════════════════════════════════════════════════════

    private void handleQuery(HttpExchange xchg) throws IOException {
        if (!"POST".equals(xchg.getRequestMethod())) {
            jsonResponse(xchg, 405, "{\"error\":\"POST required\"}");
            return;
        }

        String body = readBody(xchg);
        String sql = extractSql(body);
        if (sql.isEmpty()) {
            jsonResponse(xchg, 400, "{\"error\":\"empty sql\"}");
            return;
        }

        queryCount++;
        miniSQL.addHistory("> " + sql);

        String result;
        long startNs = System.nanoTime();
        try {
            result = miniSQL.execute(sql);
        } catch (Exception e) {
            result = "✗ " + e.getMessage();
        }
        long elapsedMs = (System.nanoTime() - startNs) / 1_000_000;

        miniSQL.addHistory(result);

        String type;
        if (result.startsWith("✗")) type = "error";
        else if (result.startsWith("✓")) type = "success";
        else type = "text";

        // Try to parse box-drawing table into structured data
        String jHeaders = "[]", jRows = "[]", jSummary = jsonStr("");
        if ("text".equals(type) && !result.isEmpty() && result.charAt(0) == '┌') {
            Map<String, Object> parsed = parseTable(result);
            if (parsed != null) {
                type = "table";
                jHeaders = jsonStrList((List<String>) parsed.get("headers"));
                jRows = jsonStrRows((List<List<String>>) parsed.get("rows"));
                jSummary = jsonStr((String) parsed.get("summary"));
            }
        }

        String json = String.format(
            "{\"sql\":%s,\"result\":%s,\"type\":%s,\"elapsed\":%d,\"headers\":%s,\"rows\":%s,\"summary\":%s}",
            jsonStr(sql), jsonStr(result), jsonStr(type), elapsedMs,
            jHeaders, jRows, jSummary
        );
        jsonResponse(xchg, 200, json);
    }

    private void handleStats(HttpExchange xchg) throws IOException {
        Runtime rt = Runtime.getRuntime();
        long used  = rt.totalMemory() - rt.freeMemory();
        long max   = rt.maxMemory();
        int threads = ManagementFactory.getThreadMXBean().getThreadCount();
        long uptime = ManagementFactory.getRuntimeMXBean().getUptime();

        // GC count
        long gcCount = 0;
        for (java.lang.management.GarbageCollectorMXBean g : ManagementFactory.getGarbageCollectorMXBeans()) {
            long c = g.getCollectionCount();
            if (c >= 0) gcCount += c;
        }

        String json = String.format(
            "{\"heapUsed\":%d,\"heapMax\":%d,\"threads\":%d,\"queries\":%d,\"uptime\":%d,\"gcCount\":%d}",
            used, max, threads, queryCount, uptime, gcCount
        );
        jsonResponse(xchg, 200, json);
    }

    private void handleTables(HttpExchange xchg) throws IOException {
        String result = miniSQL.execute("!tables");
        String json = "{\"content\":" + jsonStr(result) + "}";
        jsonResponse(xchg, 200, json);
    }

    private void handleExport(HttpExchange xchg) throws IOException {
        List<String> history = miniSQL.getHistory();
        String html = buildReportHtml(history);
        byte[] bytes = html.getBytes(StandardCharsets.UTF_8);

        xchg.getResponseHeaders().set("Content-Type", "text/html; charset=utf-8");
        xchg.getResponseHeaders().set("Content-Disposition", "attachment; filename=\"minisql-report.html\"");
        xchg.sendResponseHeaders(200, bytes.length);
        xchg.getResponseBody().write(bytes);
        xchg.close();
    }

    private void servePage(HttpExchange xchg) throws IOException {
        String path = xchg.getRequestURI().getPath();

        // Download exported report
        if (path.equals("/api/download") && xchg.getRequestURI().getQuery() != null) {
            String query = xchg.getRequestURI().getQuery();
            if (query.startsWith("file=")) {
                String file = URLDecoder.decode(query.substring(5), "UTF-8");
                File f = new File(dataDir, file);
                if (f.exists()) {
                    byte[] bytes = readBytes(f);
                    xchg.getResponseHeaders().set("Content-Type", "text/html; charset=utf-8");
                    xchg.sendResponseHeaders(200, bytes.length);
                    xchg.getResponseBody().write(bytes);
                    xchg.close();
                    return;
                }
            }
        }

        byte[] bytes = PAGE.getBytes(StandardCharsets.UTF_8);
        xchg.getResponseHeaders().set("Content-Type", "text/html; charset=utf-8");
        xchg.sendResponseHeaders(200, bytes.length);
        xchg.getResponseBody().write(bytes);
        xchg.close();
    }

    // ══════════════════════════════════════════════════════════════
    //  Helpers
    // ══════════════════════════════════════════════════════════════

    private static String readBody(HttpExchange xchg) throws IOException {
        try (InputStream is = xchg.getRequestBody();
             ByteArrayOutputStream bos = new ByteArrayOutputStream()) {
            byte[] buf = new byte[4096];
            int n;
            while ((n = is.read(buf)) != -1) bos.write(buf, 0, n);
            return new String(bos.toByteArray(), StandardCharsets.UTF_8);
        }
    }

    /** Crude JSON parser: extracts value of "sql" key. */
    private static String extractSql(String json) {
        int start = json.indexOf("\"sql\":\"");
        if (start == -1) return "";
        start += 7;
        StringBuilder sql = new StringBuilder();
        for (int i = start; i < json.length(); i++) {
            char c = json.charAt(i);
            if (c == '"') break;
            if (c == '\\' && i + 1 < json.length()) {
                char n = json.charAt(i + 1);
                if (n == '"')  { sql.append('"');  i++; }
                else if (n == '\\') { sql.append('\\'); i++; }
                else if (n == 'n')  { sql.append('\n'); i++; }
                else if (n == 't')  { sql.append('\t'); i++; }
                else sql.append(c);
            } else {
                sql.append(c);
            }
        }
        return sql.toString();
    }

    /** Escape a Java string as JSON string value (with surrounding quotes). */
    private static String jsonStr(String s) {
        if (s == null) return "null";
        StringBuilder sb = new StringBuilder("\"");
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            switch (c) {
                case '"':  sb.append("\\\""); break;
                case '\\': sb.append("\\\\"); break;
                case '\n': sb.append("\\n");  break;
                case '\r': sb.append("\\r");  break;
                case '\t': sb.append("\\t");  break;
                default:   sb.append(c);
            }
        }
        return sb.append('"').toString();
    }

    private static void jsonResponse(HttpExchange xchg, int code, String json) throws IOException {
        byte[] bytes = json.getBytes(StandardCharsets.UTF_8);
        xchg.getResponseHeaders().set("Content-Type", "application/json; charset=utf-8");
        xchg.sendResponseHeaders(code, bytes.length);
        xchg.getResponseBody().write(bytes);
        xchg.close();
    }

    private static String escapeHtml(String s) {
        StringBuilder sb = new StringBuilder(s.length());
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c == '&') sb.append("&amp;");
            else if (c == '<') sb.append("&lt;");
            else if (c == '>') sb.append("&gt;");
            else sb.append(c);
        }
        return sb.toString();
    }

    private static byte[] readBytes(File f) throws IOException {
        try (FileInputStream fis = new FileInputStream(f);
             ByteArrayOutputStream bos = new ByteArrayOutputStream()) {
            byte[] buf = new byte[8192];
            int n;
            while ((n = fis.read(buf)) != -1) bos.write(buf, 0, n);
            return bos.toByteArray();
        }
    }

    // ── Table parsing (box-drawing → structured data) ──

    /**
     * Parse Engine.formatTable() output into headers, rows, summary.
     *
     * Input format:
     *   ┌────┬─────────┬─────┐
     *   │ id │ name    │ age │
     *   ├────┼─────────┼─────┤
     *   │ 1  │ Alice   │ 20  │
     *   └────┴─────────┴─────┘
     *   N row(s)
     */
    static Map<String, Object> parseTable(String result) {
        String[] lines = result.split("\n");
        if (lines.length < 4) return null;

        // Find header line (contains │)
        int hdrIdx = -1;
        for (int i = 0; i < lines.length; i++) {
            if (lines[i].indexOf('│') >= 0) { hdrIdx = i; break; }
        }
        if (hdrIdx < 0) return null;

        List<String> headers = parseRow(lines[hdrIdx]);
        if (headers.isEmpty()) return null;

        // Must have a ├ ─ ┤ separator after header (distinguishes tables from
        // other ┌-prefixed output like the JVM Monitor banner)
        if (hdrIdx + 1 >= lines.length) return null;
        String sep = lines[hdrIdx + 1].trim();
        if (!sep.startsWith("├") && !sep.startsWith("┝")) return null;

        List<List<String>> rows = new java.util.ArrayList<>();
        for (int i = hdrIdx + 2; i < lines.length; i++) {
            String line = lines[i];
            if (line.isEmpty() || line.charAt(0) == '└' || line.charAt(0) == '┕') break;
            if (line.indexOf('│') < 0) break;
            // Skip separator lines (├ ─ ┤)
            if (line.charAt(0) == '├' || line.charAt(0) == '┝') continue;
            List<String> row = parseRow(line);
            if (row.size() == headers.size()) {
                rows.add(row);
            }
        }

        // Last non-empty line is summary ("N row(s)")
        String summary = "";
        for (int i = lines.length - 1; i >= 0; i--) {
            if (!lines[i].trim().isEmpty()) {
                summary = lines[i].trim();
                break;
            }
        }

        Map<String, Object> map = new java.util.LinkedHashMap<>();
        map.put("headers", headers);
        map.put("rows", rows);
        map.put("summary", summary);
        return map;
    }

    /** Split a │-delimited row into trimmed cell values. */
    private static List<String> parseRow(String line) {
        List<String> cells = new java.util.ArrayList<>();
        int prev = 0;
        while (true) {
            int idx = line.indexOf('│', prev);
            if (idx < 0) break;
            cells.add(line.substring(prev, idx).trim());
            prev = idx + 1;
        }
        // Remove first/last if they're empty (from outer │ delimiters)
        if (!cells.isEmpty() && cells.get(0).isEmpty()) cells.remove(0);
        if (!cells.isEmpty() && cells.get(cells.size() - 1).isEmpty()) cells.remove(cells.size() - 1);
        return cells;
    }

    /** Serialize List&lt;String&gt; as JSON array. */
    private static String jsonStrList(List<String> list) {
        StringBuilder sb = new StringBuilder("[");
        for (int i = 0; i < list.size(); i++) {
            if (i > 0) sb.append(',');
            sb.append(jsonStr(list.get(i)));
        }
        return sb.append(']').toString();
    }

    /** Serialize List&lt;List&lt;String&gt;&gt; as JSON 2-D array. */
    private static String jsonStrRows(List<List<String>> rows) {
        StringBuilder sb = new StringBuilder("[");
        for (int i = 0; i < rows.size(); i++) {
            if (i > 0) sb.append(',');
            sb.append(jsonStrList(rows.get(i)));
        }
        return sb.append(']').toString();
    }

    // ══════════════════════════════════════════════════════════════
    //  Report HTML generator (used by /api/export)
    // ══════════════════════════════════════════════════════════════

    private static String buildReportHtml(List<String> history) {
        StringBuilder h = new StringBuilder();
        h.append("<!DOCTYPE html><html lang=\"zh-CN\"><head><meta charset=\"UTF-8\">");
        h.append("<title>MiniSQL Report</title>");
        h.append("<style>");
        h.append("body{background:#1e1e1e;color:#d4d4d4;font-family:Consolas,monospace;padding:20px;max-width:900px;margin:0 auto;}");
        h.append("h1{color:#569cd6;border-bottom:1px solid #333;}");
        h.append(".s{color:#569cd6;font-weight:bold;}");
        h.append(".ok{color:#6a9955;}");
        h.append(".err{color:#f44747;}");
        h.append("pre{background:#1a1a1a;padding:8px;border-radius:4px;overflow-x:auto;}");
        h.append(".m{color:#808080;font-size:12px;}");
        h.append("hr{border:none;border-top:1px solid #333;}</style></head><body>");
        h.append("<h1>📊 MiniSQL Report</h1>");
        h.append("<p class=\"m\">Generated ").append(new java.util.Date()).append("</p><hr>");

        for (String line : history) {
            String esc = escapeHtml(line);
            if (line.startsWith("> ")) {
                h.append("<p class=\"s\">").append(esc).append("</p>");
            } else if (line.startsWith("✓")) {
                h.append("<p class=\"ok\">").append(esc).append("</p>");
            } else if (line.startsWith("✗")) {
                h.append("<p class=\"err\">").append(esc).append("</p>");
            } else if (!line.isEmpty()) {
                h.append("<pre>").append(esc).append("</pre>");
            }
        }
        h.append("</body></html>");
        return h.toString();
    }

    // ══════════════════════════════════════════════════════════════
    //  Embedded single-page frontend (HTML + CSS + JS)
    // ══════════════════════════════════════════════════════════════

    private static final String PAGE = buildPage();

    private static String buildPage() {
        StringBuilder p = new StringBuilder(8192);
        p.append("<!DOCTYPE html>");
        p.append("<html lang=\"zh-CN\">");
        p.append("<head>");
        p.append("<meta charset=\"UTF-8\">");
        p.append("<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">");
        p.append("<title>MiniSQL Notebook</title>");
        p.append(STYLE);
        p.append("</head>");
        p.append("<body>");

        // ── Header ──
        p.append("<header>");
        p.append("<div class=\"logo\">⚡ MiniSQL</div>");
        p.append("<div class=\"stats\" id=\"stats\">");
        p.append("  <span class=\"stat\">Heap <span id=\"heap-bg\"><span id=\"heap-fill\"></span></span>");
        p.append("         <span id=\"heap-label\">0 MB</span></span>");
        p.append("  <span class=\"stat\">Q <strong id=\"qcount\">0</strong></span>");
        p.append("  <span class=\"stat\">T <strong id=\"tc\">0</strong></span>");
        p.append("  <span class=\"stat\">GC <strong id=\"gc\">0</strong></span>");
        p.append("  <span class=\"stat\">Up <strong id=\"ut\">0s</strong></span>");
        p.append("</div>");
        p.append("</header>");

        // ── Output ──
        p.append("<main id=\"out\">");
        p.append("  <div id=\"empty\">");
        p.append("    <div class=\"empty-icon\">⌨</div>");
        p.append("    <div class=\"empty-text\">Type SQL below and press Ctrl+Enter to run</div>");
        p.append("    <div class=\"empty-hint\">Try: CREATE TABLE, INSERT, SELECT, DELETE</div>");
        p.append("  </div>");
        p.append("</main>");

        // ── Footer / Input ──
        p.append("<footer>");
        p.append("  <div class=\"input-row\">");
        p.append("    <textarea id=\"sql\" rows=\"1\" placeholder=\"Enter SQL, then Ctrl+Enter to execute\"></textarea>");
        p.append("    <button id=\"exec\">▶</button>");
        p.append("  </div>");
        p.append("  <div class=\"toolbar\">");
        p.append("    <button class=\"tb\" data-cmd=\"!tables\">📋 Tables</button>");
        p.append("    <button class=\"tb\" data-cmd=\"!stats\">📊 Stats</button>");
        p.append("    <button class=\"tb\" id=\"export-btn\">📄 Export</button>");
        p.append("    <button class=\"tb\" id=\"clear-btn\">🗑 Clear</button>");
        p.append("  </div>");
        p.append("</footer>");

        p.append("<script>");
        p.append(SCRIPT);
        p.append("</script>");
        p.append("</body></html>");
        return p.toString();
    }

    // language=CSS
    private static final String STYLE = "" +
        "<style>" +
        "*{margin:0;padding:0;box-sizing:border-box}" +
        "html,body{height:100%;background:#1e1e1e;color:#d4d4d4;font-family:system-ui,-apple-system,sans-serif;display:flex;flex-direction:column;overflow:hidden}" +

        /* header */
        "header{background:#2d2d2d;border-bottom:1px solid #3c3c3c;padding:6px 16px;display:flex;align-items:center;gap:20px;flex-shrink:0;min-height:40px}" +
        ".logo{font-size:15px;font-weight:600;color:#569cd6;white-space:nowrap;letter-spacing:.3px}" +
        ".stats{display:flex;gap:14px;font-size:12px;color:#888;flex-wrap:wrap}" +
        ".stat{white-space:nowrap;display:flex;align-items:center;gap:4px}" +
        ".stat strong{color:#d4d4d4}" +
        "#heap-bg{display:inline-block;width:60px;height:8px;background:#3c3c3c;border-radius:4px;overflow:hidden;vertical-align:middle}" +
        "#heap-fill{display:block;height:100%;width:0;background:linear-gradient(90deg,#4ec9b0,#6ccf9a);border-radius:4px;transition:width .6s ease}" +
        "#heap-label{font-variant-numeric:tabular-nums}" +

        /* output area */
        "main{flex:1;min-width:0;overflow:auto;padding:8px 12px;display:flex;flex-direction:column;gap:6px}" +

        "#empty{flex:1;min-width:0;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#555;gap:6px;user-select:none}" +
        ".empty-icon{font-size:42px}" +
        ".empty-text{font-size:14px;color:#666}" +
        ".empty-hint{font-size:12px;color:#444}" +

        /* query cards */
        ".card{min-width:0;border:1px solid #333;border-radius:6px;overflow:hidden;background:#252526;animation:fadeIn .15s ease}" +
        ".card-hd{min-width:0;padding:7px 12px;font-family:Consolas,'Courier New',monospace;font-size:13px;color:#569cd6;background:#1e1e1e;border-bottom:1px solid #333;overflow:auto;white-space:pre-wrap;word-break:break-word}" +
        ".card-bd{min-width:0;padding:7px 12px;font-family:Consolas,'Courier New',monospace;font-size:13px;overflow:auto}" +
        ".card-bd.ok{color:#6a9955}" +
        ".card-bd.err{color:#f44747;background:#2d1b1b}" +
        ".card-bd table{width:100%;border-collapse:collapse;font-family:Consolas,'Courier New',monospace;font-size:13px}" +
        ".card-bd th,.card-bd td{border:1px solid #444;padding:2px 10px;text-align:left;white-space:nowrap}" +
        ".card-bd th{background:#2d2d2d;color:#569cd6;font-weight:600}" +
        ".card-bd tr:nth-child(even){background:#2a2a2a}" +
        ".card-bd .summary{display:block;margin-top:2px;font-size:12px;color:#888}" +
        ".card-bd pre{margin:0;white-space:pre;font:inherit;line-height:1.4}" +
        ".card-bd .elapsed{display:block;margin-top:4px;font-size:11px;color:#555}" +

        /* footer */
        "footer{background:#2d2d2d;border-top:1px solid #3c3c3c;padding:8px 12px;flex-shrink:0}" +
        ".input-row{display:flex;gap:6px;align-items:flex-start}" +
        "#sql{flex:1;background:#3c3c3c;border:1px solid #555;border-radius:4px;padding:7px 10px;color:#d4d4d4;font-family:Consolas,monospace;font-size:14px;outline:none;resize:none;min-height:34px;max-height:120px;transition:border-color .15s}" +
        "#sql:focus{border-color:#569cd6}" +
        "#sql::placeholder{color:#666}" +
        "#exec{background:#0e639c;color:#fff;border:none;border-radius:4px;width:36px;height:34px;font-size:16px;cursor:pointer;display:flex;align-items:center;justify-content:center}" +
        "#exec:hover{background:#1177bb}" +
        ".toolbar{display:flex;gap:5px;margin-top:5px;flex-wrap:wrap}" +
        ".tb{background:#3c3c3c;color:#999;border:1px solid #555;border-radius:3px;padding:3px 9px;font-size:12px;cursor:pointer}" +
        ".tb:hover{background:#4c4c4c;color:#d4d4d4}" +

        /* scrollbar */
        "::-webkit-scrollbar{width:6px}::-webkit-scrollbar-track{background:transparent}" +
        "::-webkit-scrollbar-thumb{background:#444;border-radius:3px}" +
        "::-webkit-scrollbar-thumb:hover{background:#666}" +

        "@keyframes fadeIn{from{opacity:0;transform:translateY(-3px)}to{opacity:1;transform:translateY(0)}}" +
        ".loading .card-hd::after{content:'  ⟳';color:#666}" +
        "</style>";

    // language=JavaScript
    private static final String SCRIPT = "" +
        "(function(){" +
        "var sql=document.getElementById('sql'),out=document.getElementById('out'),execBtn=document.getElementById('exec');" +
        "var hist=[],hidx=0;" +
        "var EMPTY_HTML=document.getElementById('empty').outerHTML;" +

        /* helpers */
        "function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}" +
        "function scrollBottom(){setTimeout(function(){out.lastElementChild&&out.lastElementChild.scrollIntoView({behavior:'smooth'})},50)}" +

        /* add a result card */
        "function addCard(d){" +
        "  var q=d.sql,result=d.result,type=d.type,ms=d.elapsed;" +
        "  var empty=document.getElementById('empty');" +
        "  if(empty) empty.remove();" +
        "  var card=document.createElement('div');" +
        "  card.className='card';" +
        "  var hdr=document.createElement('div');" +
        "  hdr.className='card-hd';" +
        "  hdr.textContent='> '+q;" +
        "  var bd=document.createElement('div');" +
        "  bd.className='card-bd'+(type==='error'?' err':type==='success'?' ok':'');" +
        "  if(type==='table'&&d.headers&&d.headers.length){" +
        "    var t=document.createElement('table'),tr,th;" +
        "    tr=document.createElement('tr');" +
        "    for(var i=0;i<d.headers.length;i++){th=document.createElement('th');th.textContent=d.headers[i];tr.appendChild(th)}" +
        "    t.appendChild(tr);" +
        "    for(var r=0;r<d.rows.length;r++){" +
        "      tr=document.createElement('tr');" +
        "      for(var c=0;c<d.rows[r].length;c++){var td=document.createElement('td');td.textContent=d.rows[r][c];tr.appendChild(td)}" +
        "      t.appendChild(tr)" +
        "    }" +
        "    bd.appendChild(t);" +
        "    if(d.summary){var s=document.createElement('span');s.className='summary';s.textContent=d.summary;bd.appendChild(s)}" +
        "  }else if(result.charCodeAt(0)>=9472&&result.charCodeAt(0)<=9599){" +
        "    var p=document.createElement('pre');p.textContent=result;bd.appendChild(p)" +
        "  }else{bd.textContent=result}" +
        "  if(ms){var el=document.createElement('span');el.className='elapsed';el.textContent=ms+'ms';bd.appendChild(el)}" +
        "  card.appendChild(hdr);card.appendChild(bd);out.appendChild(card);scrollBottom()" +
        "}" +

        /* execute */
        "function exec(){" +
        "  var q=sql.value.trim();if(!q)return;" +
        "  hist.push(q);hidx=hist.length;" +
        "  sql.value='';sql.style.height='auto';" +
        "  var empty=document.getElementById('empty');if(empty)empty.remove();" +
        "  var card=document.createElement('div');card.className='card loading';" +
        "  var hdr=document.createElement('div');hdr.className='card-hd';hdr.textContent='> '+q;" +
        "  card.appendChild(hdr);out.appendChild(card);scrollBottom();" +
        "  fetch('/api/query',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sql:q})})" +
        "    .then(function(r){return r.json()})" +
        "    .then(function(d){card.remove();addCard(d);rfs()})" +
        "    .catch(function(e){card.remove();addCard({sql:q,result:'Network error: '+e.message,type:'error'})});" +
        "  sql.focus()" +
        "}" +

        /* refresh stats */
        "function rfs(){" +
        "  fetch('/api/stats').then(function(r){return r.json()}).then(function(d){" +
        "    if(d.heapMax>0){var p=Math.min(d.heapUsed/d.heapMax*100,100);document.getElementById('heap-fill').style.width=p+'%'}" +
        "    document.getElementById('heap-label').textContent=(d.heapUsed/1048576).toFixed(1)+'/'+(d.heapMax/1048576).toFixed(0)+'MB';" +
        "    document.getElementById('qcount').textContent=d.queries;" +
        "    document.getElementById('tc').textContent=d.threads;" +
        "    document.getElementById('gc').textContent=d.gcCount;" +
        "    var s=Math.floor(d.uptime/1000),m=Math.floor(s/60),h=Math.floor(m/60);" +
        "    document.getElementById('ut').textContent=(h>0?h+'h ':'')+(m%60)+'m '+(s%60)+'s'" +
        "  }).catch(function(){})" +
        "}" +

        /* events */
        "execBtn.addEventListener('click',exec);" +

        "sql.addEventListener('keydown',function(e){" +
        "  if(e.key==='Enter'&&(e.ctrlKey||e.metaKey)){e.preventDefault();exec()}" +
        "  else if(e.key==='ArrowUp'&&e.target.selectionStart===0&&e.target.selectionEnd===0){" +
        "    if(hidx>0){hidx--;sql.value=hist[hidx];e.preventDefault()}" +
        "  }else if(e.key==='ArrowDown'&&e.target.selectionStart===sql.value.length){" +
        "    if(hidx<hist.length-1){hidx++;sql.value=hist[hidx]}else{hidx=hist.length;sql.value=''}" +
        "  }" +
        "});" +

        /* auto-resize textarea */
        "sql.addEventListener('input',function(){this.style.height='auto';this.style.height=Math.min(this.scrollHeight,120)+'px'});" +

        /* toolbar buttons */
        "document.querySelectorAll('.tb[data-cmd]').forEach(function(btn){" +
        "  btn.addEventListener('click',function(){sql.value=btn.getAttribute('data-cmd');exec()})" +
        "});" +

        "document.getElementById('export-btn').addEventListener('click',function(){" +
        "  window.open('/api/export','_blank')" +
        "});" +

        "document.getElementById('clear-btn').addEventListener('click',function(){" +
        "  out.innerHTML=EMPTY_HTML;hist=[];hidx=0;" +
        "});" +

        /* initialise */
        "sql.focus();rfs();setInterval(rfs,3000);" +
        "})();";
}
