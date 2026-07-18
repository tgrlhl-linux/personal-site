package minisql.markdown;

import java.io.*;
import java.nio.file.*;
import java.util.List;

public class HtmlExporter {
    private final List<String> history;

    public HtmlExporter(List<String> history) { this.history = history; }

    public String export(String filePath) throws IOException {
        StringBuilder html = new StringBuilder();
        html.append("<!DOCTYPE html><html lang=\"zh-CN\"><head><meta charset=\"UTF-8\">");
        html.append("<title>MiniSQL Notebook Report</title>");
        html.append("<style>");
        html.append("body{background:#1e1e1e;color:#d4d4d4;font-family:'Consolas','Courier New',monospace;padding:20px;max-width:900px;margin:0 auto;}");
        html.append("h1{color:#569cd6;border-bottom:1px solid #333;padding-bottom:8px;}");
        html.append("h2{color:#4ec9b0;}");
        html.append(".sql{color:#569cd6;font-weight:bold;}");
        html.append(".output{color:#ce9178;}");
        html.append(".success{color:#6a9955;}");
        html.append(".error{color:#f44747;}");
        html.append("table{border-collapse:collapse;margin:10px 0;width:100%;}");
        html.append("th,td{border:1px solid #333;padding:6px 12px;text-align:left;}");
        html.append("th{background:#2d2d2d;color:#569cd6;}");
        html.append("tr:nth-child(even){background:#252525;}");
        html.append("pre{background:#1a1a1a;padding:10px;border-radius:4px;overflow-x:auto;}");
        html.append(".meta{color:#808080;font-size:12px;margin-top:20px;}");
        html.append("</style></head><body>");
        html.append("<h1>📊 MiniSQL Notebook Report</h1>");
        html.append("<p class=\"meta\">Generated: ").append(new java.util.Date().toString()).append("</p>");
        html.append("<hr>");

        for (String line : history) {
            if (line.startsWith("> ")) {
                html.append("<p><span class=\"sql\">&gt; ").append(escapeHtml(line.substring(2))).append("</span></p>");
            } else if (line.startsWith("✓")) {
                html.append("<p class=\"success\">").append(escapeHtml(line)).append("</p>");
            } else if (line.startsWith("✗")) {
                html.append("<p class=\"error\">").append(escapeHtml(line)).append("</p>");
            } else if (line.contains("──") || line.contains("│") || line.contains("┌") || line.contains("└") || line.contains("├")) {
                html.append("<pre>").append(escapeHtml(line)).append("</pre>");
            } else {
                html.append("<p class=\"output\">").append(escapeHtml(line)).append("</p>");
            }
        }

        html.append("<hr><p class=\"meta\">MiniSQL Notebook - End of Report</p>");
        html.append("</body></html>");

        Files.write(Paths.get(filePath), html.toString().getBytes("UTF-8"));
        return filePath;
    }

    private String escapeHtml(String s) {
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;");
    }
}
