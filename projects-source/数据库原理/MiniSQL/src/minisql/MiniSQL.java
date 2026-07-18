package minisql;

import minisql.sql.tokenizer.*;
import minisql.sql.parser.*;
import minisql.sql.engine.*;
import minisql.sql.storage.*;
import minisql.markdown.HtmlExporter;
import minisql.monitor.JvmMonitor;

import java.io.*;
import java.util.*;

public class MiniSQL {
    private final Engine engine;
    private final StorageManager storage;
    private final List<String> history = new ArrayList<>();
    private final String dataDir;
    private int queryCount = 0;

    public MiniSQL(String dataDir) {
        this.dataDir = dataDir;
        this.storage = new StorageManager(dataDir);
        this.engine = new Engine(storage);
    }

    public String execute(String input) {
        input = input.trim();
        if (input.isEmpty()) return "";

        // Built-in commands
        if (input.startsWith("!")) return execBuiltin(input);

        // SQL statement
        try {
            Tokenizer tokenizer = new Tokenizer(input);
            List<Token> tokens = tokenizer.tokenize();
            if (tokens.isEmpty() || tokens.get(0).type == TokenType.EOF) return "";

            Parser parser = new Parser(tokens);
            ASTNode stmt = parser.parse();
            queryCount++;
            return engine.execute(stmt);
        } catch (Exception e) {
            return "✗ " + e.getMessage();
        }
    }

    private String execBuiltin(String input) {
        String[] parts = input.split("\\s+", 2);
        String cmd = parts[0].toLowerCase();

        switch (cmd) {
            case "!help":
                return "Built-in commands:\n" +
                       "  !help        - Show this help\n" +
                       "  !stats       - Show JVM stats\n" +
                       "  !tables      - List all tables\n" +
                       "  !export <fn> - Export session to HTML\n" +
                       "  !clear       - Clear screen (history)\n" +
                       "  !quit        - Exit";
            case "!stats":
                return JvmMonitor.getStats(queryCount);
            case "!tables":
                List<String> tables = storage.listTables();
                if (tables.isEmpty()) return "  (no tables)";
                StringBuilder sb = new StringBuilder("Tables:\n");
                for (String t : tables) {
                    List<minisql.sql.parser.ASTNode.ColumnDef> schema = storage.getSchema(t);
                    sb.append("  ├ ").append(t).append(" (");
                    for (int i = 0; i < schema.size(); i++) {
                        if (i > 0) sb.append(", ");
                        sb.append(schema.get(i).name).append(" ").append(schema.get(i).type);
                    }
                    sb.append(")\n");
                }
                return sb.toString();
            case "!export":
                if (parts.length < 2) return "✗ Usage: !export <filename>";
                try {
                    String path = dataDir + File.separator + parts[1];
                    new HtmlExporter(history).export(path);
                    return "✓ Exported to " + path;
                } catch (IOException e) {
                    return "✗ Export failed: " + e.getMessage();
                }
            case "!clear":
                history.clear();
                return "CLEARED";
            case "!quit":
                return "BYE";
            default:
                return "✗ Unknown command: " + cmd + ". Type !help for commands.";
        }
    }

    public void addHistory(String line) { history.add(line); }
    public List<String> getHistory() { return history; }

    // ── REPL ──

    public static void main(String[] args) {
        String dataDir = args.length > 0 ? args[0] : "data";
        MiniSQL miniSQL = new MiniSQL(dataDir);

        Scanner scanner = new Scanner(System.in);
        System.out.println("╔══════════════════════════════════════════════╗");
        System.out.println("║   MiniSQL Notebook - Interactive SQL       ║");
        System.out.println("║   Type SQL or !help for built-in commands   ║");
        System.out.println("╚══════════════════════════════════════════════╝");

        while (true) {
            System.out.print("\nMiniSQL > ");
            String input;
            try {
                input = scanner.nextLine();
            } catch (NoSuchElementException e) { break; }

            if (input.trim().isEmpty()) continue;

            miniSQL.addHistory("> " + input);
            String result = miniSQL.execute(input);

            if (result.equals("CLEARED")) {
                // Clear console (simple approach)
                for (int i = 0; i < 50; i++) System.out.println();
                continue;
            }
            if (result.equals("BYE")) {
                System.out.println("Goodbye!");
                break;
            }

            if (!result.isEmpty()) {
                System.out.println(result);
                miniSQL.addHistory(result);
            }
        }
        scanner.close();
    }
}
