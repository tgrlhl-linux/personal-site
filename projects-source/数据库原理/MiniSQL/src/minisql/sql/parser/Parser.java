package minisql.sql.parser;

import minisql.sql.tokenizer.Token;
import minisql.sql.tokenizer.TokenType;
import minisql.type.Value;
import java.util.ArrayList;
import java.util.List;

public class Parser {
    private final List<Token> tokens;
    private int pos;

    public Parser(List<Token> tokens) { this.tokens = tokens; this.pos = 0; }

    public ASTNode parse() {
        Token t = peek();
        if (t == null) return null;
        switch (t.type) {
            case CREATE: return parseCreateTable();
            case INSERT: return parseInsert();
            case SELECT: return parseSelect();
            case DELETE: return parseDelete();
            default: throw new RuntimeException("Unexpected token: " + t.type + " (" + t.lexeme + ") at position " + t.position);
        }
    }

    // CREATE TABLE name (col1 TYPE, col2 TYPE, ...)
    private ASTNode.CreateTableStmt parseCreateTable() {
        consume(TokenType.CREATE); consume(TokenType.TABLE);
        String name = consume(TokenType.IDENTIFIER).lexeme;
        consume(TokenType.LPAREN);
        List<ASTNode.ColumnDef> columns = new ArrayList<>();
        while (!check(TokenType.RPAREN)) {
            String colName = consume(TokenType.IDENTIFIER).lexeme;
            TokenType typeTok = consumeAny(TokenType.INT, TokenType.STRING).type;
            Value.Type colType = typeTok == TokenType.INT ? Value.Type.INT : Value.Type.STRING;
            columns.add(new ASTNode.ColumnDef(colName, colType));
            if (check(TokenType.COMMA)) consume(TokenType.COMMA);
        }
        consume(TokenType.RPAREN);
        return new ASTNode.CreateTableStmt(name, columns);
    }

    // INSERT INTO name VALUES (v1, v2), (v3, v4), ...
    private ASTNode.InsertStmt parseInsert() {
        consume(TokenType.INSERT); consume(TokenType.INTO);
        String name = consume(TokenType.IDENTIFIER).lexeme;
        consume(TokenType.VALUES);
        List<List<Value>> rows = new ArrayList<>();
        do {
            consume(TokenType.LPAREN);
            List<Value> row = new ArrayList<>();
            while (!check(TokenType.RPAREN)) {
                if (check(TokenType.INTEGER_LITERAL))
                    row.add(new Value(Integer.parseInt(consume(TokenType.INTEGER_LITERAL).lexeme)));
                else if (check(TokenType.STRING_LITERAL))
                    row.add(new Value(consume(TokenType.STRING_LITERAL).lexeme));
                else throw new RuntimeException("Expected value literal");
                if (check(TokenType.COMMA)) consume(TokenType.COMMA);
            }
            consume(TokenType.RPAREN);
            rows.add(row);
        } while (check(TokenType.COMMA));
        return new ASTNode.InsertStmt(name, rows);
    }

    // SELECT col1, col2, ... FROM name WHERE expr
    private ASTNode.SelectStmt parseSelect() {
        consume(TokenType.SELECT);
        List<String> columns = new ArrayList<>();
        if (check(TokenType.STAR)) {
            consume(TokenType.STAR);
            columns.add("*");
        } else {
            columns.add(consume(TokenType.IDENTIFIER).lexeme);
            while (check(TokenType.COMMA)) {
                consume(TokenType.COMMA);
                columns.add(consume(TokenType.IDENTIFIER).lexeme);
            }
        }
        consume(TokenType.FROM);
        String name = consume(TokenType.IDENTIFIER).lexeme;
        ASTNode.Expr where = null;
        if (check(TokenType.WHERE)) {
            consume(TokenType.WHERE);
            where = parseExpr();
        }
        return new ASTNode.SelectStmt(columns, name, where);
    }

    // DELETE FROM name WHERE expr
    private ASTNode.DeleteStmt parseDelete() {
        consume(TokenType.DELETE); consume(TokenType.FROM);
        String name = consume(TokenType.IDENTIFIER).lexeme;
        consume(TokenType.WHERE);
        ASTNode.Expr where = parseExpr();
        return new ASTNode.DeleteStmt(name, where);
    }

    // Expression: term (OR term)*
    private ASTNode.Expr parseExpr() {
        ASTNode.Expr left = parseAnd();
        while (check(TokenType.OR)) {
            consume(TokenType.OR);
            left = new ASTNode.Expr.BinOp("OR", left, parseAnd());
        }
        return left;
    }

    // And: comparison (AND comparison)*
    private ASTNode.Expr parseAnd() {
        ASTNode.Expr left = parseComparison();
        while (check(TokenType.AND)) {
            consume(TokenType.AND);
            left = new ASTNode.Expr.BinOp("AND", left, parseComparison());
        }
        return left;
    }

    // Comparison: operand (op operand)?
    private ASTNode.Expr parseComparison() {
        ASTNode.Expr left = parseOperand();
        if (isComparisonOp(peek().type)) {
            Token op = consumeAny(TokenType.EQ, TokenType.NEQ, TokenType.GT, TokenType.GTE, TokenType.LT, TokenType.LTE);
            ASTNode.Expr right = parseOperand();
            left = new ASTNode.Expr.BinOp(op.lexeme, left, right);
        }
        return left;
    }

    // Operand: identifier | literal
    private ASTNode.Expr parseOperand() {
        Token t = peek();
        if (t.type == TokenType.IDENTIFIER) {
            consume(TokenType.IDENTIFIER);
            return new ASTNode.Expr.ColumnRef(t.lexeme);
        }
        if (t.type == TokenType.INTEGER_LITERAL) {
            consume(TokenType.INTEGER_LITERAL);
            return new ASTNode.Expr.Literal(new Value(Integer.parseInt(t.lexeme)));
        }
        if (t.type == TokenType.STRING_LITERAL) {
            consume(TokenType.STRING_LITERAL);
            return new ASTNode.Expr.Literal(new Value(t.lexeme));
        }
        throw new RuntimeException("Unexpected token in expression: " + t.type);
    }

    private boolean isComparisonOp(TokenType t) {
        return t == TokenType.EQ || t == TokenType.NEQ || t == TokenType.GT ||
               t == TokenType.GTE || t == TokenType.LT || t == TokenType.LTE;
    }

    private Token peek() { return pos < tokens.size() ? tokens.get(pos) : null; }
    private boolean check(TokenType t) { return peek() != null && peek().type == t; }
    private Token consume(TokenType t) {
        if (!check(t)) {
            Token p = peek();
            String found = p == null ? "EOF" : p.type + "(" + p.lexeme + ")";
            throw new RuntimeException("Expected " + t + " but got " + found + " at position " + (p != null ? p.position : pos));
        }
        return tokens.get(pos++);
    }
    private Token consumeAny(TokenType... types) {
        for (TokenType t : types) { if (check(t)) return tokens.get(pos++); }
        Token p = peek();
        String found = p == null ? "EOF" : p.type + "(" + p.lexeme + ")";
        throw new RuntimeException("Expected one of [types] but got " + found);
    }
}
