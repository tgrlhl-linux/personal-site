package minisql.sql.tokenizer;

import java.util.ArrayList;
import java.util.List;

public class Tokenizer {
    private final String input;
    private int pos;
    private List<Token> tokens;

    public Tokenizer(String input) { this.input = input; this.pos = 0; }

    public List<Token> tokenize() {
        tokens = new ArrayList<>();
        while (pos < input.length()) {
            char c = input.charAt(pos);
            if (Character.isWhitespace(c)) { pos++; continue; }

            if (c == '-' && pos + 1 < input.length() && input.charAt(pos + 1) == '-') {
                while (pos < input.length() && input.charAt(pos) != '\n') pos++;
                continue;
            }
            if (c == '/' && pos + 1 < input.length() && input.charAt(pos + 1) == '*') {
                pos += 2;
                while (pos + 1 < input.length() && !(input.charAt(pos) == '*' && input.charAt(pos + 1) == '/')) pos++;
                pos += 2;
                continue;
            }

            switch (c) {
                case '*': add(TokenType.STAR, "*"); continue;
                case ',': add(TokenType.COMMA, ","); continue;
                case ';': add(TokenType.SEMICOLON, ";"); continue;
                case '(': add(TokenType.LPAREN, "("); continue;
                case ')': add(TokenType.RPAREN, ")"); continue;
                case '=': add(TokenType.EQ, "="); continue;
                case '!':
                    if (peek() == '=') { pos++; add(TokenType.NEQ, "!="); }
                    else add(TokenType.UNKNOWN, "!");
                    continue;
                case '>':
                    if (peek() == '=') { pos++; add(TokenType.GTE, ">="); }
                    else add(TokenType.GT, ">");
                    continue;
                case '<':
                    if (peek() == '=') { pos++; add(TokenType.LTE, "<="); }
                    else add(TokenType.LT, "<");
                    continue;
                case '\'': readString(); continue;
            }

            if (Character.isDigit(c)) { readInteger(); continue; }
            if (Character.isLetter(c) || c == '_') { readIdentifier(); continue; }

            add(TokenType.UNKNOWN, String.valueOf(c));
        }
        add(TokenType.EOF, "");
        return tokens;
    }

    private char peek() { return pos + 1 < input.length() ? input.charAt(pos + 1) : '\0'; }

    private void add(TokenType type, String lexeme) {
        tokens.add(new Token(type, lexeme, pos));
        pos++;
    }

    private void readString() {
        int start = pos;
        pos++; // skip opening '
        StringBuilder sb = new StringBuilder();
        while (pos < input.length() && input.charAt(pos) != '\'') {
            if (input.charAt(pos) == '\\') { pos++; if (pos < input.length()) sb.append(input.charAt(pos)); }
            else sb.append(input.charAt(pos));
            pos++;
        }
        if (pos < input.length()) pos++; // skip closing '
        tokens.add(new Token(TokenType.STRING_LITERAL, sb.toString(), start));
    }

    private void readInteger() {
        int start = pos;
        while (pos < input.length() && Character.isDigit(input.charAt(pos))) pos++;
        tokens.add(new Token(TokenType.INTEGER_LITERAL, input.substring(start, pos), start));
    }

    private void readIdentifier() {
        int start = pos;
        while (pos < input.length() && (Character.isLetterOrDigit(input.charAt(pos)) || input.charAt(pos) == '_')) pos++;
        String word = input.substring(start, pos);
        TokenType keyword = keywordOf(word);
        tokens.add(new Token(keyword, word, start));
    }

    private TokenType keywordOf(String word) {
        switch (word.toUpperCase()) {
            case "CREATE": return TokenType.CREATE;
            case "TABLE": return TokenType.TABLE;
            case "INSERT": return TokenType.INSERT;
            case "INTO": return TokenType.INTO;
            case "VALUES": return TokenType.VALUES;
            case "SELECT": return TokenType.SELECT;
            case "FROM": return TokenType.FROM;
            case "WHERE": return TokenType.WHERE;
            case "DELETE": return TokenType.DELETE;
            case "AND": return TokenType.AND;
            case "OR": return TokenType.OR;
            case "NOT": return TokenType.NOT;
            case "INT": return TokenType.INT;
            case "STRING": return TokenType.STRING;
            default: return TokenType.IDENTIFIER;
        }
    }
}
