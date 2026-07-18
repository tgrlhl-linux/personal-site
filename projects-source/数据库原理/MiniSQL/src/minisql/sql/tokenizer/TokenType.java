package minisql.sql.tokenizer;

public enum TokenType {
    // Keywords
    CREATE, TABLE, INSERT, INTO, VALUES, SELECT, FROM, WHERE,
    DELETE, AND, OR, NOT, INT, STRING,
    // Symbols
    STAR, COMMA, SEMICOLON, LPAREN, RPAREN,
    // Operators
    EQ, NEQ, GT, GTE, LT, LTE,
    // Values
    IDENTIFIER, INTEGER_LITERAL, STRING_LITERAL,
    // Special
    EOF, UNKNOWN
}
