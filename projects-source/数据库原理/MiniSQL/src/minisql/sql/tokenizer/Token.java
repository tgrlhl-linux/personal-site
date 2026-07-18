package minisql.sql.tokenizer;

public class Token {
    public final TokenType type;
    public final String lexeme;
    public final int position;

    public Token(TokenType type, String lexeme, int position) {
        this.type = type;
        this.lexeme = lexeme;
        this.position = position;
    }

    @Override
    public String toString() {
        return type + (lexeme.isEmpty() ? "" : "(" + lexeme + ")");
    }
}
