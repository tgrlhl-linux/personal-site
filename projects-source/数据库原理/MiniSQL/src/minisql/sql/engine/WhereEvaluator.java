package minisql.sql.engine;

import minisql.sql.parser.ASTNode;
import minisql.sql.storage.StorageManager;
import minisql.type.Value;
import java.util.List;
import java.util.Map;

public class WhereEvaluator {
    private final Map<String, Value> row;

    public WhereEvaluator(Map<String, Value> row) { this.row = row; }

    public boolean evaluate(ASTNode.Expr expr) {
        if (expr == null) return true;
        if (expr instanceof ASTNode.Expr.Literal) {
            return true; // truthy
        }
        if (expr instanceof ASTNode.Expr.ColumnRef) {
            return true; // just a reference, used in comparison
        }
        if (expr instanceof ASTNode.Expr.BinOp) {
            ASTNode.Expr.BinOp bin = (ASTNode.Expr.BinOp) expr;
            if (bin.op.equals("AND")) return evaluate(bin.left) && evaluate(bin.right);
            if (bin.op.equals("OR")) return evaluate(bin.left) || evaluate(bin.right);
            // Comparison operators
            Value left = evalExpr(bin.left);
            Value right = evalExpr(bin.right);
            if (left == null || right == null) return false;
            switch (bin.op) {
                case "=": return left.eq(right);
                case "!=": return left.neq(right);
                case ">": return left.gt(right);
                case ">=": return left.gte(right);
                case "<": return left.lt(right);
                case "<=": return left.lte(right);
            }
        }
        return true;
    }

    private Value evalExpr(ASTNode.Expr expr) {
        if (expr instanceof ASTNode.Expr.Literal) return ((ASTNode.Expr.Literal) expr).value;
        if (expr instanceof ASTNode.Expr.ColumnRef) return row.get(((ASTNode.Expr.ColumnRef) expr).name);
        if (expr instanceof ASTNode.Expr.BinOp) {
            ASTNode.Expr.BinOp bin = (ASTNode.Expr.BinOp) expr;
            Value l = evalExpr(bin.left);
            Value r = evalExpr(bin.right);
            if (l == null || r == null) return null;
            switch (bin.op) {
                case "=": return new Value(l.eq(r) ? 1 : 0);
                case "!=": return new Value(l.neq(r) ? 1 : 0);
                case ">": return new Value(l.gt(r) ? 1 : 0);
                case ">=": return new Value(l.gte(r) ? 1 : 0);
                case "<": return new Value(l.lt(r) ? 1 : 0);
                case "<=": return new Value(l.lte(r) ? 1 : 0);
            }
        }
        return null;
    }
}
