package minisql.sql.engine;

import minisql.sql.parser.ASTNode;
import minisql.sql.storage.StorageManager;
import minisql.type.Value;
import java.util.*;

public class Engine {
    private final StorageManager storage;

    public Engine(StorageManager storage) { this.storage = storage; }

    public String execute(ASTNode stmt) {
        if (stmt instanceof ASTNode.CreateTableStmt) return execCreate((ASTNode.CreateTableStmt) stmt);
        if (stmt instanceof ASTNode.InsertStmt) return execInsert((ASTNode.InsertStmt) stmt);
        if (stmt instanceof ASTNode.SelectStmt) return execSelect((ASTNode.SelectStmt) stmt);
        if (stmt instanceof ASTNode.DeleteStmt) return execDelete((ASTNode.DeleteStmt) stmt);
        return "Unknown statement";
    }

    private String execCreate(ASTNode.CreateTableStmt stmt) {
        if (storage.tableExists(stmt.tableName))
            return "✗ Table '" + stmt.tableName + "' already exists";
        storage.createTable(stmt.tableName, stmt.columns);
        return "✓ Table '" + stmt.tableName + "' created";
    }

    private String execInsert(ASTNode.InsertStmt stmt) {
        if (!storage.tableExists(stmt.tableName))
            return "✗ Table '" + stmt.tableName + "' not found";
        List<ASTNode.ColumnDef> schema = storage.getSchema(stmt.tableName);
        for (List<Value> row : stmt.rows) {
            if (row.size() != schema.size())
                return "✗ Column count mismatch: expected " + schema.size() + " but got " + row.size();
            // Type coercion: if schema says INT but we got STRING, try to parse
            for (int i = 0; i < row.size(); i++) {
                if (schema.get(i).type == Value.Type.INT && row.get(i).getType() == Value.Type.STRING) {
                    try {
                        row.set(i, new Value(Integer.parseInt(row.get(i).asString())));
                    } catch (NumberFormatException e) {
                        return "✗ Cannot convert '" + row.get(i).asString() + "' to INT for column '" + schema.get(i).name + "'";
                    }
                }
            }
            storage.insertRow(stmt.tableName, row);
        }
        return "✓ " + stmt.rows.size() + " row(s) inserted";
    }

    private String execSelect(ASTNode.SelectStmt stmt) {
        if (!storage.tableExists(stmt.tableName))
            return "✗ Table '" + stmt.tableName + "' not found";
        List<ASTNode.ColumnDef> schema = storage.getSchema(stmt.tableName);
        List<List<Value>> allRows = storage.scanTable(stmt.tableName);

        // Determine which columns to show
        List<String> colNames;
        if (stmt.columns.size() == 1 && stmt.columns.get(0).equals("*")) {
            colNames = new ArrayList<>();
            for (ASTNode.ColumnDef c : schema) colNames.add(c.name);
        } else {
            colNames = stmt.columns;
        }

        // Build column index map
        Map<String, Integer> colIndex = new HashMap<>();
        for (int i = 0; i < schema.size(); i++) colIndex.put(schema.get(i).name, i);

        // Filter and project
        List<List<String>> resultRows = new ArrayList<>();
        for (List<Value> row : allRows) {
            // Build name->value map for WHERE
            Map<String, Value> rowMap = new HashMap<>();
            for (int i = 0; i < schema.size(); i++) rowMap.put(schema.get(i).name, row.get(i));

            WhereEvaluator evaluator = new WhereEvaluator(rowMap);
            if (!evaluator.evaluate(stmt.where)) continue;

            List<String> projected = new ArrayList<>();
            for (String col : colNames) {
                Integer idx = colIndex.get(col);
                if (idx != null && idx < row.size()) {
                    projected.add(row.get(idx).asString());
                } else {
                    projected.add("NULL");
                }
            }
            resultRows.add(projected);
        }

        // Format as table
        return formatTable(colNames, resultRows, resultRows.size() + " row(s)");
    }

    private String execDelete(ASTNode.DeleteStmt stmt) {
        if (!storage.tableExists(stmt.tableName))
            return "✗ Table '" + stmt.tableName + "' not found";
        List<ASTNode.ColumnDef> schema = storage.getSchema(stmt.tableName);
        List<List<Value>> allRows = storage.scanTable(stmt.tableName);

        List<Integer> toDelete = new ArrayList<>();
        for (int i = 0; i < allRows.size(); i++) {
            List<Value> row = allRows.get(i);
            Map<String, Value> rowMap = new HashMap<>();
            for (int j = 0; j < schema.size(); j++) rowMap.put(schema.get(j).name, row.get(j));

            WhereEvaluator evaluator = new WhereEvaluator(rowMap);
            if (evaluator.evaluate(stmt.where)) toDelete.add(i);
        }
        storage.deleteRows(stmt.tableName, toDelete);
        return "✓ " + toDelete.size() + " row(s) deleted";
    }

    private String formatTable(List<String> headers, List<List<String>> rows, String footer) {
        if (rows.isEmpty()) return "  (empty)";
        int[] widths = new int[headers.size()];
        for (int i = 0; i < headers.size(); i++) {
            widths[i] = headers.get(i).length();
            for (List<String> row : rows) {
                if (i < row.size()) widths[i] = Math.max(widths[i], row.get(i).length());
            }
            widths[i] = Math.min(widths[i], 40); // cap
        }

        StringBuilder sb = new StringBuilder();
        // Header separator
        sb.append("┌");
        for (int i = 0; i < headers.size(); i++) {
            if (i > 0) sb.append("┬");
            for (int j = 0; j < widths[i] + 2; j++) sb.append("─");
        }
        sb.append("┐\n");

        // Header row
        sb.append("│");
        for (int i = 0; i < headers.size(); i++) {
            String h = headers.get(i);
            sb.append(" ").append(h);
            for (int j = h.length(); j < widths[i] + 1; j++) sb.append(" ");
            sb.append("│");
        }
        sb.append("\n");

        // Separator
        sb.append("├");
        for (int i = 0; i < headers.size(); i++) {
            if (i > 0) sb.append("┼");
            for (int j = 0; j < widths[i] + 2; j++) sb.append("─");
        }
        sb.append("┤\n");

        // Data rows
        for (List<String> row : rows) {
            sb.append("│");
            for (int i = 0; i < headers.size(); i++) {
                String val = i < row.size() ? row.get(i) : "";
                sb.append(" ").append(val);
                for (int j = val.length(); j < widths[i] + 1; j++) sb.append(" ");
                sb.append("│");
            }
            sb.append("\n");
        }

        // Footer separator
        sb.append("└");
        for (int i = 0; i < headers.size(); i++) {
            if (i > 0) sb.append("┴");
            for (int j = 0; j < widths[i] + 2; j++) sb.append("─");
        }
        sb.append("┘\n");
        sb.append(footer);
        return sb.toString();
    }

    public StorageManager getStorage() { return storage; }
}
