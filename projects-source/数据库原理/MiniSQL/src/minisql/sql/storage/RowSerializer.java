package minisql.sql.storage;

import minisql.sql.parser.ASTNode;
import minisql.type.Value;
import java.io.*;
import java.util.*;

public class RowSerializer {
    private final List<ASTNode.ColumnDef> schema;

    public RowSerializer(List<ASTNode.ColumnDef> schema) { this.schema = schema; }

    public byte[] serialize(List<Value> row) throws IOException {
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        DataOutputStream dos = new DataOutputStream(bos);
        for (int i = 0; i < schema.size(); i++) {
            Value v = row.get(i);
            if (schema.get(i).type == Value.Type.INT) {
                dos.writeInt(v.asInt());
            } else {
                byte[] bytes = v.asString().getBytes("UTF-8");
                dos.writeShort(bytes.length);
                dos.write(bytes);
            }
        }
        return bos.toByteArray();
    }

    public List<Value> deserialize(byte[] data, int offset) throws IOException {
        ByteArrayInputStream bis = new ByteArrayInputStream(data, offset, data.length - offset);
        DataInputStream dis = new DataInputStream(bis);
        List<Value> row = new ArrayList<>();
        for (ASTNode.ColumnDef col : schema) {
            if (col.type == Value.Type.INT) {
                row.add(new Value(dis.readInt()));
            } else {
                int len = dis.readShort() & 0xFFFF;
                byte[] strBytes = new byte[len];
                dis.readFully(strBytes);
                row.add(new Value(new String(strBytes, "UTF-8")));
            }
        }
        return row;
    }

    public int rowSize() {
        int size = 0;
        for (ASTNode.ColumnDef col : schema) {
            size += col.type == Value.Type.INT ? 4 : 2 + 256; // STRING: short(2) + max 256
        }
        return size;
    }
}
