package minisql.sql.storage;

import minisql.sql.parser.ASTNode;
import minisql.type.Value;
import java.io.*;
import java.util.*;
import java.nio.charset.StandardCharsets;

public class StorageManager {
    private final String dataDir;
    private final Map<String, TableInfo> tables = new LinkedHashMap<>();

    private static class TableInfo {
        final List<ASTNode.ColumnDef> columns;
        final List<byte[]> rows = new ArrayList<>();
        RowSerializer serializer;

        TableInfo(List<ASTNode.ColumnDef> columns) {
            this.columns = columns;
            this.serializer = new RowSerializer(columns);
        }
    }

    public StorageManager(String dataDir) {
        this.dataDir = dataDir;
        new File(dataDir).mkdirs();
        loadMetadata();
    }

    // ── Metadata ──

    private File metaFile() { return new File(dataDir, "metadata.db"); }

    private void loadMetadata() {
        File f = metaFile();
        if (!f.exists()) return;
        try (BufferedReader br = new BufferedReader(new InputStreamReader(new FileInputStream(f), "UTF-8"))) {
            String line;
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty()) continue;
                String[] parts = line.split("\\|");
                String tname = parts[0];
                List<ASTNode.ColumnDef> cols = new ArrayList<>();
                for (int i = 1; i < parts.length; i++) {
                    String[] kv = parts[i].split(":");
                    cols.add(new ASTNode.ColumnDef(kv[0], kv[1].equals("INT") ? Value.Type.INT : Value.Type.STRING));
                }
                tables.put(tname, new TableInfo(cols));
            }
        } catch (IOException e) { /* ignore */ }
        // Load row data for each table
        for (Map.Entry<String, TableInfo> e : tables.entrySet()) {
            loadRows(e.getKey(), e.getValue());
        }
    }

    private void saveMetadata() {
        try (BufferedWriter bw = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(metaFile()), "UTF-8"))) {
            for (Map.Entry<String, TableInfo> e : tables.entrySet()) {
                bw.write(e.getKey());
                for (ASTNode.ColumnDef col : e.getValue().columns) {
                    bw.write("|" + col.name + ":" + (col.type == Value.Type.INT ? "INT" : "STRING"));
                }
                bw.newLine();
            }
        } catch (IOException ex) { ex.printStackTrace(); }
    }

    // ── Row I/O ──

    private File tableFile(String name) { return new File(dataDir, name + ".tbl"); }

    private void loadRows(String name, TableInfo info) {
        File f = tableFile(name);
        if (!f.exists()) return;
        try (RandomAccessFile raf = new RandomAccessFile(f, "r")) {
            info.rows.clear();
            byte[] lenBuf = new byte[2];
            while (raf.read(lenBuf) == 2) {
                int len = ((lenBuf[0] & 0xFF) << 8) | (lenBuf[1] & 0xFF);
                byte[] rowData = new byte[len];
                raf.readFully(rowData);
                info.rows.add(rowData);
            }
        } catch (IOException e) { e.printStackTrace(); }
    }

    private void saveRows(String name, TableInfo info) {
        try (DataOutputStream dos = new DataOutputStream(new BufferedOutputStream(new FileOutputStream(tableFile(name))))) {
            for (byte[] row : info.rows) {
                // Write length prefix (2 bytes) + data
                if (row.length > 0xFFFF) continue;
                dos.writeShort(row.length);
                dos.write(row);
            }
            dos.flush();
        } catch (IOException e) { e.printStackTrace(); }
    }

    // ── Public API ──

    public boolean tableExists(String name) { return tables.containsKey(name); }

    public void createTable(String name, List<ASTNode.ColumnDef> columns) {
        tables.put(name, new TableInfo(columns));
        saveMetadata();
    }

    public List<ASTNode.ColumnDef> getSchema(String name) {
        TableInfo info = tables.get(name);
        return info != null ? info.columns : null;
    }

    public synchronized void insertRow(String name, List<Value> row) {
        TableInfo info = tables.get(name);
        if (info == null) throw new RuntimeException("Table not found: " + name);
        try {
            byte[] data = info.serializer.serialize(row);
            info.rows.add(data);
            saveRows(name, info);
        } catch (IOException e) { throw new RuntimeException("Serialize error: " + e.getMessage()); }
    }

    public synchronized List<List<Value>> scanTable(String name) {
        TableInfo info = tables.get(name);
        if (info == null) return Collections.emptyList();
        List<List<Value>> result = new ArrayList<>();
        for (byte[] rowData : info.rows) {
            try {
                result.add(info.serializer.deserialize(rowData, 0));
            } catch (IOException e) { /* skip corrupt row */ }
        }
        return result;
    }

    public synchronized void deleteRows(String name, List<Integer> indices) {
        TableInfo info = tables.get(name);
        if (info == null) return;
        Set<Integer> removeSet = new HashSet<>(indices);
        List<byte[]> remaining = new ArrayList<>();
        for (int i = 0; i < info.rows.size(); i++) {
            if (!removeSet.contains(i)) remaining.add(info.rows.get(i));
        }
        info.rows.clear();
        info.rows.addAll(remaining);
        saveRows(name, info);
    }

    public List<String> listTables() { return new ArrayList<>(tables.keySet()); }
}
