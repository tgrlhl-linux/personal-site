package minisql.sql.parser;

import minisql.type.Value;
import java.util.List;

public abstract class ASTNode {
    // Statement types
    public static class CreateTableStmt extends ASTNode {
        public final String tableName;
        public final List<ColumnDef> columns;
        public CreateTableStmt(String tableName, List<ColumnDef> columns) {
            this.tableName = tableName; this.columns = columns;
        }
    }

    public static class InsertStmt extends ASTNode {
        public final String tableName;
        public final List<List<Value>> rows;
        public InsertStmt(String tableName, List<List<Value>> rows) {
            this.tableName = tableName; this.rows = rows;
        }
    }

    public static class SelectStmt extends ASTNode {
        public final List<String> columns;
        public final String tableName;
        public final Expr where;
        public SelectStmt(List<String> columns, String tableName, Expr where) {
            this.columns = columns; this.tableName = tableName; this.where = where;
        }
    }

    public static class DeleteStmt extends ASTNode {
        public final String tableName;
        public final Expr where;
        public DeleteStmt(String tableName, Expr where) {
            this.tableName = tableName; this.where = where;
        }
    }

    // Column definition
    public static class ColumnDef {
        public final String name;
        public final Value.Type type;
        public ColumnDef(String name, Value.Type type) { this.name = name; this.type = type; }
    }

    // Expression tree for WHERE clause
    public abstract static class Expr {
        public static class ColumnRef extends Expr { public final String name; public ColumnRef(String name) { this.name = name; } }
        public static class Literal extends Expr { public final Value value; public Literal(Value v) { this.value = v; } }
        public static class BinOp extends Expr {
            public final Expr left, right;
            public final String op; // =, !=, >, >=, <, <=, AND, OR
            public BinOp(String op, Expr left, Expr right) { this.op = op; this.left = left; this.right = right; }
        }
    }
}
