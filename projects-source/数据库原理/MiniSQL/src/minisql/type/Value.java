package minisql.type;

public class Value implements Comparable<Value> {
    public enum Type { INT, STRING }

    private final Type type;
    private final Object data;

    public Value(int v) { this.type = Type.INT; this.data = v; }
    public Value(String v) { this.type = Type.STRING; this.data = v; }
    public Value(String v, Type t) {
        this.type = t;
        this.data = t == Type.INT ? Integer.parseInt(v.trim()) : v;
    }

    public Type getType() { return type; }
    public int asInt() { return (int) data; }
    public String asString() { return type == Type.STRING ? (String) data : String.valueOf(data); }

    @Override
    public int compareTo(Value o) {
        if (type == Type.INT && o.type == Type.INT)
            return Integer.compare(asInt(), o.asInt());
        return asString().compareTo(o.asString());
    }

    public boolean eq(Value o) { return compareTo(o) == 0; }
    public boolean gt(Value o) { return compareTo(o) > 0; }
    public boolean lt(Value o) { return compareTo(o) < 0; }
    public boolean gte(Value o) { return compareTo(o) >= 0; }
    public boolean lte(Value o) { return compareTo(o) <= 0; }
    public boolean neq(Value o) { return compareTo(o) != 0; }

    @Override
    public String toString() { return asString(); }
}
