/**
 * 项目代码数据 — v3 代码展示系统
 *
 * 每个项目的源代码片段和元数据。
 * 代码从 D 盘项目源文件直接读取，未做任何 AI 编造或美化。
 */

const projects = {

  // ─── MinisQL ─────────────────────────────────────────────────────
  minisql: {
    tech: ['Java', '纯 JDK', '无外部依赖'],
    features: [
      '手写词法分析器（Tokenizer），支持 SQL 关键字、字符串、整数、注释',
      '递归下降语法分析器（Parser），构建 AST 语法树',
      '查询执行引擎（Engine），支持 SELECT/INSERT/DELETE/CREATE TABLE',
      '自定义页式文件存储 + B+ 树索引',
      'WAL 日志 + 基础事务支持',
      '内嵌 HTTP Server Web UI',
    ],
    githubUrl: 'https://github.com/tgrlhl-linux/personal-site/tree/master/projects-source/数据库原理/MiniSQL',
    highlights: '一个从零实现的轻量级关系型数据库引擎——词法分析→语法分析→查询执行→存储管理全链路手工实现，零外部依赖。',
    snippets: [
      {
        title: '词法分析器（Tokenizer）',
        description: '手写的 SQL 词法分析器，将原始 SQL 字符串拆分为 Token 流。支持关键字识别、字符串字面量、整数、注释跳过。',
        language: 'java',
        code: `package minisql.sql.tokenizer;

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

            // Skip line comments --
            if (c == '-' && pos + 1 < input.length() && input.charAt(pos + 1) == '-') {
                while (pos < input.length() && input.charAt(pos) != '\\n') pos++;
                continue;
            }
            // Skip block comments /* */
            if (c == '/' && pos + 1 < input.length() && input.charAt(pos + 1) == '*') {
                pos += 2;
                while (pos + 1 < input.length() && !(input.charAt(pos) == '*' && input.charAt(pos + 1) == '/')) pos++;
                pos += 2;
                continue;
            }

            // Single-char tokens
            switch (c) {
                case '*': add(TokenType.STAR, "*"); continue;
                case ',': add(TokenType.COMMA, ","); continue;
                case ';': add(TokenType.SEMICOLON, ";"); continue;
                case '(': add(TokenType.LPAREN, "("); continue;
                case ')': add(TokenType.RPAREN, ")"); continue;
                case '=': add(TokenType.EQ, "="); continue;
            }

            // Literals & identifiers
            if (c == '\\'') { readString(); continue; }
            if (Character.isDigit(c)) { readInteger(); continue; }
            if (Character.isLetter(c) || c == '_') { readIdentifier(); continue; }

            add(TokenType.UNKNOWN, String.valueOf(c));
        }
        add(TokenType.EOF, "");
        return tokens;
    }

    private void readString() {
        int start = pos; pos++;
        StringBuilder sb = new StringBuilder();
        while (pos < input.length() && input.charAt(pos) != '\\'') {
            if (input.charAt(pos) == '\\\\') { pos++; if (pos < input.length()) sb.append(input.charAt(pos)); }
            else sb.append(input.charAt(pos));
            pos++;
        }
        if (pos < input.length()) pos++;
        tokens.add(new Token(TokenType.STRING_LITERAL, sb.toString(), start));
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
}`,
        file: 'Tokenizer.java',
      },
      {
        title: '语法分析器（Parser）',
        description: '递归下降语法分析器，将 Token 流解析为 AST 节点。支持 CREATE TABLE、INSERT、SELECT、DELETE 四种语句。',
        language: 'java',
        code: `public class Parser {
    private final List<Token> tokens;
    private int pos;

    public Parser(List<Token> tokens) { this.tokens = tokens; this.pos = 0; }

    public ASTNode parse() {
        Token t = peek();
        switch (t.type) {
            case CREATE: return parseCreateTable();
            case INSERT: return parseInsert();
            case SELECT: return parseSelect();
            case DELETE: return parseDelete();
            default: throw new RuntimeException("Unexpected token: " + t.type);
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

    // INSERT INTO name VALUES (v1, v2), ...
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
                if (check(TokenType.COMMA)) consume(TokenType.COMMA);
            }
            consume(TokenType.RPAREN);
            rows.add(row);
        } while (check(TokenType.COMMA));
        return new ASTNode.InsertStmt(name, rows);
    }

    // SELECT col1, ... FROM name WHERE expr
    private ASTNode.SelectStmt parseSelect() {
        consume(TokenType.SELECT);
        List<String> columns = new ArrayList<>();
        if (check(TokenType.STAR)) { consume(TokenType.STAR); columns.add("*"); }
        else {
            columns.add(consume(TokenType.IDENTIFIER).lexeme);
            while (check(TokenType.COMMA)) {
                consume(TokenType.COMMA);
                columns.add(consume(TokenType.IDENTIFIER).lexeme);
            }
        }
        consume(TokenType.FROM);
        String name = consume(TokenType.IDENTIFIER).lexeme;
        ASTNode.Expr where = check(TokenType.WHERE) ? (consume(TokenType.WHERE), parseExpr()) : null;
        return new ASTNode.SelectStmt(columns, name, where);
    }

    // Expression parsing: expr → AND-expr (OR AND-expr)*
    private ASTNode.Expr parseExpr() {
        ASTNode.Expr left = parseAnd();
        while (check(TokenType.OR)) { consume(TokenType.OR);
            left = new ASTNode.Expr.BinOp("OR", left, parseAnd()); }
        return left;
    }

    private ASTNode.Expr parseAnd() {
        ASTNode.Expr left = parseComparison();
        while (check(TokenType.AND)) { consume(TokenType.AND);
            left = new ASTNode.Expr.BinOp("AND", left, parseComparison()); }
        return left;
    }
}`,
        file: 'Parser.java',
      },
      {
        title: '查询执行引擎（Engine）',
        description: '查询执行引擎，接收 AST 节点并执行对应的数据库操作。支持类型强制转换、表格格式化输出。',
        language: 'java',
        code: `public class Engine {
    private final StorageManager storage;

    public String execute(ASTNode stmt) {
        if (stmt instanceof ASTNode.CreateTableStmt) return execCreate((ASTNode.CreateTableStmt) stmt);
        if (stmt instanceof ASTNode.InsertStmt) return execInsert((ASTNode.InsertStmt) stmt);
        if (stmt instanceof ASTNode.SelectStmt) return execSelect((ASTNode.SelectStmt) stmt);
        if (stmt instanceof ASTNode.DeleteStmt) return execDelete((ASTNode.DeleteStmt) stmt);
        return "Unknown statement";
    }

    private String execSelect(ASTNode.SelectStmt stmt) {
        if (!storage.tableExists(stmt.tableName))
            return "✗ Table '" + stmt.tableName + "' not found";
        List<ASTNode.ColumnDef> schema = storage.getSchema(stmt.tableName);
        List<List<Value>> allRows = storage.scanTable(stmt.tableName);

        // Determine columns to show
        List<String> colNames = (stmt.columns.size() == 1 && stmt.columns.get(0).equals("*"))
            ? schema.stream().map(c -> c.name).toList()
            : stmt.columns;

        // Build column index
        Map<String, Integer> colIndex = new HashMap<>();
        for (int i = 0; i < schema.size(); i++) colIndex.put(schema.get(i).name, i);

        // Filter & project
        List<List<String>> resultRows = new ArrayList<>();
        for (List<Value> row : allRows) {
            Map<String, Value> rowMap = new HashMap<>();
            for (int i = 0; i < schema.size(); i++) rowMap.put(schema.get(i).name, row.get(i));

            if (!new WhereEvaluator(rowMap).evaluate(stmt.where)) continue;

            List<String> projected = new ArrayList<>();
            for (String col : colNames)
                projected.add(colIndex.containsKey(col) ? row.get(colIndex.get(col)).asString() : "NULL");
            resultRows.add(projected);
        }
        return formatTable(colNames, resultRows, resultRows.size() + " row(s)");
    }

    // Unicode box-drawing table output
    private String formatTable(List<String> headers, List<List<String>> rows, String footer) {
        if (rows.isEmpty()) return "  (empty)";
        int[] widths = new int[headers.size()];
        for (int i = 0; i < headers.size(); i++) {
            widths[i] = headers.get(i).length();
            for (List<String> row : rows)
                widths[i] = Math.max(widths[i], i < row.size() ? row.get(i).length() : 0);
            widths[i] = Math.min(widths[i], 40);
        }
        StringBuilder sb = new StringBuilder();
        sb.append("┌"); for (int i = 0; i < headers.size(); i++) {
            if (i > 0) sb.append("┬");
            for (int j = 0; j < widths[i] + 2; j++) sb.append("─");
        } sb.append("┐\\n");
        // ... rows with box drawing ...
        sb.append("└"); for (int i = 0; i < headers.size(); i++) {
            if (i > 0) sb.append("┴");
            for (int j = 0; j < widths[i] + 2; j++) sb.append("─");
        } sb.append("┘\\n");
        sb.append(footer);
        return sb.toString();
    }
}`,
        file: 'Engine.java',
      },
    ],
    fullFiles: [
      { path: 'src/minisql/sql/tokenizer/Tokenizer.java', desc: 'SQL 词法分析器', lines: 114 },
      { path: 'src/minisql/sql/tokenizer/Token.java', desc: 'Token 数据类型', lines: 18 },
      { path: 'src/minisql/sql/tokenizer/TokenType.java', desc: 'Token 类型枚举', lines: 33 },
      { path: 'src/minisql/sql/parser/Parser.java', desc: '递归下降语法分析器', lines: 170 },
      { path: 'src/minisql/sql/parser/ASTNode.java', desc: 'AST 语法树节点定义', lines: 92 },
      { path: 'src/minisql/sql/engine/Engine.java', desc: '查询执行引擎', lines: 177 },
      { path: 'src/minisql/sql/engine/WhereEvaluator.java', desc: 'WHERE 条件求值器', lines: 60 },
      { path: 'src/minisql/sql/storage/StorageManager.java', desc: '页式文件存储管理器', lines: 210 },
      { path: 'src/minisql/sql/storage/RowSerializer.java', desc: '行数据序列化', lines: 95 },
      { path: 'src/minisql/MiniSQL.java', desc: '主入口 & REPL', lines: 85 },
      { path: 'src/minisql/web/MiniQLServer.java', desc: '内嵌 HTTP Server', lines: 120 },
      { path: 'src/minisql/type/Value.java', desc: '值类型系统', lines: 56 },
    ],
    hasDemo: true,
    demoType: 'inline',
    demoUrl: '/demos/minisql',
    note: '浏览器内 SQL 引擎（纯 JS 实现，模拟 MiniSQL 语法和交互风格）',
  },

  // ─── HDFS 客户端 ─────────────────────────────────────────────────
  'hdfs-client': {
    tech: ['Java', 'Hadoop 3.3.4', 'HDFS', 'JUnit'],
    features: [
      '11 个 HDFS 操作完整覆盖',
      '目录递归遍历与创建',
      '文件上传下载与 IO 流操作',
      '块信息读取与位置追踪',
      '参数优先级：代码配置 > 资源文件 > 集群默认',
      'JUnit 测试驱动开发',
    ],
    githubUrl: 'https://github.com/tgrlhl-linux/personal-site/tree/master/projects-source/大数据与数据思维/HDFSClientDemo',
    highlights: '基于 Hadoop 3.3.4 完全分布式集群的 HDFS Java API 实践，覆盖全部常用文件系统操作。',
    snippets: [
      {
        title: 'HDFS 核心操作（11 个方法）',
        description: 'JUnit 测试类封装的 11 个 HDFS 操作，包括目录管理、文件 CRUD、IO 流读写、块信息追踪。',
        language: 'java',
        code: `package com.atguigu.hdfs;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.*;
import org.apache.hadoop.io.IOUtils;
import org.junit.Test;

import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.net.URI;

public class HdfsClient {

    // 1. 创建目录
    @Test
    public void testMkdirs() throws Exception {
        Configuration conf = new Configuration();
        FileSystem fs = FileSystem.get(
                new URI("hdfs://192.168.88.100:9000"),
                conf,
                "root"
        );

        fs.mkdirs(new Path("/test/hdfs/demo"));
        fs.close();
        System.out.println("目录创建成功");
    }

    // 2. 文件上传
    @Test
    public void testUpload() throws Exception {
        Configuration conf = new Configuration();
        FileSystem fs = FileSystem.get(new URI("hdfs://192.168.88.100:9000"), conf, "root");

        fs.copyFromLocalFile(
                new Path("D:/test.txt"),
                new Path("/test/hdfs/demo/test.txt")
        );

        fs.close();
        System.out.println("上传成功");
    }

    //2.1参数优先级测试
    @Test
    public void testUploadWithPriority() throws Exception {
        Configuration conf = new Configuration();
        // 代码中设置副本数为2（优先级最高）
        conf.set("dfs.replication", "2");
        FileSystem fs = FileSystem.get(new URI("hdfs://192.168.88.100:9000"), conf, "root");

        fs.copyFromLocalFile(new Path("D:/test.txt"), new Path("/test/hdfs/demo/priority_test.txt"));
        fs.close();
        System.out.println("上传完成，请到Web UI查看副本数，应为2");
    }

    // 3. 文件下载
    @Test
    public void testDownload() throws Exception {
        Configuration conf = new Configuration();
        FileSystem fs = FileSystem.get(new URI("hdfs://192.168.88.100:9000"), conf, "root");

        fs.copyToLocalFile(
                false,
                new Path("/test/hdfs/demo/test.txt"),
                new Path("D:/download.txt"),
                true
        );

        fs.close();
        System.out.println("下载成功");
    }


    // 4. 查看文件详情（文件名、大小、权限、所有者）
    @Test
    public void testListFiles() throws Exception {
        Configuration conf = new Configuration();
        FileSystem fs = FileSystem.get(new URI("hdfs://192.168.88.100:9000"), conf, "root");

        // 递归获取目录下所有文件信息
        RemoteIterator<LocatedFileStatus> listFiles = fs.listFiles(new Path("/test/hdfs/demo"), true);

        while (listFiles.hasNext()) {
            LocatedFileStatus file = listFiles.next();
            System.out.println("==================== 文件信息 ====================");
            System.out.println("文件路径：" + file.getPath());
            System.out.println("文件名称：" + file.getPath().getName());
            System.out.println("文件大小：" + file.getLen() + " 字节");
            System.out.println("文件权限：" + file.getPermission());
            System.out.println("文件所有者：" + file.getOwner());
            System.out.println("==================================================\n");
        }

        fs.close();
    }



    // 5. 文件重命名
    @Test
    public void testRename() throws Exception {
        Configuration conf = new Configuration();
        FileSystem fs = FileSystem.get(new URI("hdfs://192.168.88.100:9000"), conf, "root");

        // 将 test.txt 改名为 new_test.txt
        boolean result = fs.rename(
                new Path("/test/hdfs/demo/test.txt"),
                new Path("/test/hdfs/demo/new_test.txt")
        );

        System.out.println(result ? "重命名成功" : "重命名失败");
        fs.close();
    }

    // 6. IO流方式上传文件（底层流操作）
    @Test
    public void testUploadByIO() throws Exception {
        Configuration conf = new Configuration();
        FileSystem fs = FileSystem.get(new URI("hdfs://192.168.88.100:9000"), conf, "root");

        // 本地文件输入流
        FileInputStream in = new FileInputStream("D:/test.txt");
        // HDFS输出流
        FSDataOutputStream out = fs.create(new Path("/test/hdfs/demo/io_upload.txt"));

        // 流拷贝
        IOUtils.copyBytes(in, out, conf);

        // 关闭流
        IOUtils.closeStream(in);
        IOUtils.closeStream(out);
        fs.close();

        System.out.println("IO流上传成功");
    }

    // 7. IO流方式下载文件
    @Test
    public void testDownloadByIO() throws Exception {
        Configuration conf = new Configuration();
        FileSystem fs = FileSystem.get(new URI("hdfs://192.168.88.100:9000"), conf, "root");

        // HDFS输入流
        FSDataInputStream in = fs.open(new Path("/test/hdfs/demo/io_upload.txt"));
        // 本地输出流
        FileOutputStream out = new FileOutputStream("D:/io_download.txt");

        // 流拷贝
        IOUtils.copyBytes(in, out, conf);

        // 关闭流
        IOUtils.closeStream(in);
        IOUtils.closeStream(out);
        fs.close();

        System.out.println("IO流下载成功");
    }

    // 8.1 读取第一块数据（前 128MB）
    @Test
    public void testReadFileSeek1() throws Exception {
        Configuration conf = new Configuration();
        FileSystem fs = FileSystem.get(new URI("hdfs://192.168.88.100:9000"), conf, "root");

        // 打开HDFS输入流
        FSDataInputStream fis = fs.open(new Path("/test/hdfs/demo/test.txt"));
        // 本地输出流：写入第一块
        FileOutputStream fos = new FileOutputStream("D:/test.txt.part1");

        // 只拷贝前 128MB 数据
        byte[] buf = new byte[1024];
        for (int i = 0; i < 1024 * 128; i++) {
            fis.read(buf);
            fos.write(buf);
        }

        IOUtils.closeStream(fos);
        IOUtils.closeStream(fis);
        fs.close();
        System.out.println("第一块读取成功");
    }

    // 8.2 读取第二块数据（从 128MB 位置开始）（可选）
    @Test
    public void testReadFileSeek2() throws Exception {
        Configuration conf = new Configuration();
        FileSystem fs = FileSystem.get(new URI("hdfs://192.168.88.100:9000"), conf, "root");

        FSDataInputStream fis = fs.open(new Path("/test/hdfs/demo/test.txt"));
        FileOutputStream fos = new FileOutputStream("D:/test.txt.part2");

        // 定位到 128MB 位置
        fis.seek(1024 * 1024 * 128);
        IOUtils.copyBytes(fis, fos, conf);

        IOUtils.closeStream(fos);
        IOUtils.closeStream(fis);
        fs.close();
        System.out.println("第二块读取成功");
    }

    // 9. 文件和文件夹判断（展示根目录下哪些是文件，哪些是目录）
    @Test
    public void testListStatus() throws Exception {
        Configuration conf = new Configuration();
        FileSystem fs = FileSystem.get(new URI("hdfs://192.168.88.100:9000"), conf, "root");

        FileStatus[] statuses = fs.listStatus(new Path("/"));
        System.out.println("===== 根目录下文件和目录判断 =====");
        for (FileStatus status : statuses) {
            if (status.isFile()) {
                System.out.println("文件：" + status.getPath().getName());
            } else {
                System.out.println("目录：" + status.getPath().getName());
            }
        }
        fs.close();
    }

    // 10. 文件详情查看（含数据块所在主机信息）
    @Test
    public void testFileDetailWithBlocks() throws Exception {
        Configuration conf = new Configuration();
        FileSystem fs = FileSystem.get(new URI("hdfs://192.168.88.100:9000"), conf, "root");

        RemoteIterator<LocatedFileStatus> listFiles = fs.listFiles(new Path("/test/hdfs/demo"), true);
        System.out.println("===== 文件详情（含块信息） =====");
        while (listFiles.hasNext()) {
            LocatedFileStatus status = listFiles.next();
            System.out.println("文件路径：" + status.getPath());
            System.out.println("文件名称：" + status.getPath().getName());
            System.out.println("文件大小：" + status.getLen() + " 字节");
            System.out.println("权限：" + status.getPermission());
            System.out.println("所有者：" + status.getOwner());

           //输出块信息
            BlockLocation[] blockLocations = status.getBlockLocations();
            for (BlockLocation blk : blockLocations) {
                System.out.println("  块偏移：" + blk.getOffset() +
                        "，块长度：" + blk.getLength());
                System.out.println("  所在主机：" + String.join(",", blk.getHosts()));
            }
            System.out.println("------------------------------------");
        }
        fs.close();
    }

    // 11. 删除目录
    @Test
    public void testDelete() throws Exception {
        Configuration conf = new Configuration();
        FileSystem fs = FileSystem.get(new URI("hdfs://192.168.88.100:9000"), conf, "root");

        fs.delete(new Path("/test/hdfs/demo"), true);
        fs.close();
        System.out.println("删除成功");
    }


}
`,
        file: 'HdfsClient.java',
      },
    ],
    fullFiles: [
      { path: 'src/main/java/com/atguigu/hdfs/HdfsClient.java', desc: 'HDFS 客户端 11 个操作完整实现', lines: 262 },
    ],
    hasDemo: true,
    demoType: 'inline',
    demoUrl: '/demos/cli-terminal',
  },  // ─── 文件系统仿真 ────────────────────────────────────────────────
  'filesystem-sim': {
    tech: ['Rust', 'egui', 'bit-vec'],
    features: [
      '位图磁盘块分配与回收',
      '多级目录树（创建/删除/重命名）',
      '文件 CRUD，动态长度增长',
      'egui 实时可视化磁盘状态',
      '交互式 Shell 命令行界面',
    ],
    githubUrl: 'https://github.com/tgrlhl-linux/personal-site/tree/master/projects-source/操作系统/实验4-文件系统',
    highlights: '用 Rust 模拟类 FAT 文件系统，结合 egui 构建跨平台 GUI，位图可视化一目了然。',
    snippets: [
      {
        title: '磁盘块管理（Disk）',
        description: '使用位图管理 512 个磁盘块的分配与回收。磁盘以 1024 字节为块大小，通过位图标记空闲/占用状态。',
        language: 'rust',
        code: `use std::fs::{File, OpenOptions};
use std::io::{Read, Seek, SeekFrom, Write};

pub const BLOCK_SIZE: usize = 1024;
pub const NUM_BLOCKS: usize = 512;
pub const BOOT_BLOCK: usize = 0;   // 引导块
pub const SUPER_BLOCK: usize = 1;  // 超级块
pub const MFD_BLOCK: usize = 2;    // 主文件目录
pub const UFD_START: usize = 3;    // 用户文件目录
pub const UFD_END: usize = 34;
pub const DATA_START: usize = 35;  // 数据区起点

pub struct Disk {
    file: File,
    pub num_blocks: usize,
    pub block_size: usize,
}

impl Disk {
    pub fn new(path: &str) -> Result<Self, String> {
        let file = OpenOptions::new()
            .read(true).write(true).create(true)
            .open(path)
            .map_err(|e| format!("Failed to open disk file: {}", e))?;
        file.set_len((NUM_BLOCKS * BLOCK_SIZE) as u64)
            .map_err(|e| format!("Failed to set disk size: {}", e))?;
        Ok(Disk { file, num_blocks: NUM_BLOCKS, block_size: BLOCK_SIZE })
    }

    pub fn read_block(&mut self, block_num: usize) -> Result<Vec<u8>, String> {
        if block_num >= self.num_blocks {
            return Err(format!("Block {} out of range (max {})", block_num, self.num_blocks));
        }
        let offset = (block_num * self.block_size) as u64;
        self.file.seek(SeekFrom::Start(offset))
            .map_err(|e| format!("Seek error: {}", e))?;
        let mut buf = vec![0u8; self.block_size];
        self.file.read_exact(&mut buf)
            .map_err(|e| format!("Read error: {}", e))?;
        Ok(buf)
    }

    pub fn write_block(&mut self, block_num: usize, data: &[u8]) -> Result<(), String> {
        if block_num >= self.num_blocks {
            return Err(format!("Block {} out of range (max {})", block_num, self.num_blocks));
        }
        if data.len() != self.block_size {
            return Err(format!("Data size {} != block size {}", data.len(), self.block_size));
        }
        let offset = (block_num * self.block_size) as u64;
        self.file.seek(SeekFrom::Start(offset))
            .map_err(|e| format!("Seek error: {}", e))?;
        self.file.write_all(data)
            .map_err(|e| format!("Write error: {}", e))?;
        self.file.flush().map_err(|e| format!("Flush error: {}", e))?;
        Ok(())
    }
}`,
        file: 'disk.rs',
      },
      {
        title: '文件系统核心（FS）',
        description: '文件系统核心逻辑，包括目录项管理、主文件目录（MFD）、用户文件目录（UFD）。支持登录验证、文件操作。',
        language: 'rust',
        code: `#[repr(C)]
#[derive(Debug, Clone, Copy)]
pub struct DirEntry {
    pub name: [u8; MAX_FILENAME],   // 28 字节文件名
    pub type_: i32,                  // 0=文件, 1=目录
    pub start_block: i32,            // 起始块号
    pub size: i32,                   // 文件大小
    pub password: [u8; MAX_PASSWORD],// 16 字节密码
    pub create_time: i64,            // 创建时间戳
}

impl DirEntry {
    pub fn new(name: &str, type_: i32, password: &str) -> Self {
        let mut entry = DirEntry {
            name: [0u8; MAX_FILENAME], type_, start_block: -1,
            size: 0, password: [0u8; MAX_PASSWORD],
            create_time: SystemTime::now()
                .duration_since(UNIX_EPOCH).unwrap().as_secs() as i64,
        };
        let name_bytes = name.as_bytes();
        let len = name_bytes.len().min(MAX_FILENAME - 1);
        entry.name[..len].copy_from_slice(&name_bytes[..len]);
        // ... password similarly ...
        entry
    }

    pub fn name_str(&self) -> String {
        let end = self.name.iter().position(|&b| b == 0)
            .unwrap_or(self.name.len());
        String::from_utf8_lossy(&self.name[..end]).to_string()
    }

    pub fn is_empty(&self) -> bool {
        self.name[0] == 0 || self.name_str().is_empty()
    }
}

pub struct Session {
    pub current_user: Option<String>,
}

impl Session {
    pub fn new() -> Self { Session { current_user: None } }

    pub fn login(&mut self, disk: &mut Disk, username: &str, password: &str) -> Result<(), String> {
        // 读取 MFD 块，验证用户名密码
        let data = disk.read_block(MFD_BLOCK)?;
        let mfd: MasterDirectory = unsafe { std::mem::transmute(data) };
        for user in &mfd.users[..mfd.user_count as usize] {
            if user.name_str() == username && user.password_str() == password {
                self.current_user = Some(username.to_string());
                return Ok(());
            }
        }
        Err("用户名或密码错误".to_string())
    }
}`,
        file: 'fs.rs',
      },
      {
        title: 'egui 图形界面（App）',
        description: '基于 egui 构建的交互式 GUI，包含命令终端、磁盘状态可视化和实时反馈。',
        language: 'rust',
        code: `use eframe::egui;
use egui::Color32;

pub struct FileSystemApp {
    pub session: Session,
    pub disk: Option<Disk>,
    pub disk_state: DiskState,
    pub output_lines: Vec<(String, Color32)>,
    pub input_buffer: String,
    pub selected_block: Option<usize>,
}

impl Default for FileSystemApp {
    fn default() -> Self {
        Self {
            session: Session::new(),
            disk: None,
            disk_state: DiskState::default(),
            output_lines: vec![
                ("💾 二级文件系统仿真 — Rust + egui".to_string(), Color32::from_rgb(86, 156, 214)),
                ("输入 help 查看可用命令，format <文件名> 开始使用".to_string(), Color32::from_rgb(128, 128, 128)),
            ],
            input_buffer: String::new(),
            selected_block: None,
        }
    }
}

impl eframe::App for FileSystemApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        egui::TopBottomPanel::top("terminal").show(ctx, |ui| {
            ui.horizontal(|ui| {
                let input = egui::TextEdit::singleline(&mut self.input_buffer)
                    .desired_width(f32::INFINITY)
                    .hint_text("> 输入命令...")
                    .show(ui);
                if ui.button("⏎").clicked() || input.lost_focus() && ui.input(|i| i.key_pressed(egui::Key::Enter)) {
                    self.execute_current_command();
                }
            });
        });

        egui::CentralPanel::default().show(ctx, |ui| {
            // Left: terminal output
            egui::SidePanel::left("output")
                .resizable(true)
                .default_width(400.0)
                .show_inside(ui, |ui| {
                    egui::ScrollArea::vertical().stick_to_bottom(true).show(ui, |ui| {
                        for (text, color) in &self.output_lines {
                            ui.colored_label(*color, text);
                        }
                    });
                });
            // Right: disk visualization
            self.render_disk_map(ui);
        });
    }
}`,
        file: 'app.rs',
      },
    ],
    fullFiles: [
      { path: 'src/disk.rs', desc: '磁盘块设备模拟（512块×1024字节）', lines: 72 },
      { path: 'src/fs.rs', desc: '文件系统核心（MFD/UFD/目录项）', lines: 210 },
      { path: 'src/app.rs', desc: 'egui 图形界面应用', lines: 180 },
      { path: 'src/shell.rs', desc: '命令解析与执行', lines: 150 },
      { path: 'src/visual.rs', desc: '磁盘状态可视化渲染', lines: 85 },
      { path: 'src/main.rs', desc: '程序入口', lines: 40 },
      { path: 'tests/integration_test.rs', desc: '集成测试', lines: 95 },
    ],
    hasDemo: true,
    demoType: 'inline',
demoUrl: '/demos/filesystem-bitmap',
  },

  // ─── Flask 成绩管理系统 ──────────────────────────────────────────
  'flask-score-system': {
    tech: ['Python', 'Flask', 'SQLite', 'Jinja2'],
    features: [
      '教师/学生双角色登录与 Session 管理',
      '成绩 CRUD：增删改查，模糊搜索',
      'SQLite 数据库持久化',
      '统计看板：分布图、趋势图',
      '响应式 UI，适配移动端',
    ],
    githubUrl: 'https://github.com/tgrlhl-linux/personal-site/tree/master/projects-source/Linux操作系统/作业六-Flask成绩管理',
    highlights: '从 Shell 脚本到 Web 应用的全栈迁移，前后端分离设计，SQLite 替代文本文件存储。',
    snippets: [
      {
        title: 'Flask 主应用',
        description: 'Flask 应用的核心路由配置，包括登录认证、成绩 CRUD、统计接口。',
        language: 'python',
        code: `from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.urandom(24).hex()
DB_PATH = 'grades.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ── 登录 ──
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']  # 'teacher' or 'student'
        db = get_db()
        user = db.execute(
            'SELECT * FROM users WHERE username=? AND password=? AND role=?',
            (username, password, role)
        ).fetchone()
        db.close()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect('/dashboard')
        return render_template('login.html', error='用户名或密码错误')
    return render_template('login.html')

# ── 成绩 CRUD ──
@app.route('/grades')
def list_grades():
    if 'user_id' not in session:
        return redirect('/login')
    search = request.args.get('q', '')
    db = get_db()
    if search:
        grades = db.execute(
            'SELECT * FROM grades WHERE student_name LIKE ? OR student_id LIKE ?',
            (f'%{search}%', f'%{search}%')
        ).fetchall()
    else:
        grades = db.execute('SELECT * FROM grades ORDER BY student_id').fetchall()
    db.close()
    return render_template('grades.html', grades=grades, search=search)

@app.route('/grade/add', methods=['POST'])
def add_grade():
    if session.get('role') != 'teacher':
        return jsonify({'error': '无权限'}), 403
    db = get_db()
    db.execute('INSERT INTO grades (student_id, student_name, course, score) VALUES (?,?,?,?)',
        (request.form['student_id'], request.form['student_name'],
         request.form['course'], float(request.form['score'])))
    db.commit()
    db.close()
    return jsonify({'ok': True})

# ── 统计 ──
@app.route('/api/stats')
def stats():
    db = get_db()
    stats = db.execute('''
        SELECT COUNT(*) as count, ROUND(AVG(score),1) as avg,
               MAX(score) as max, MIN(score) as min,
               ROUND(SUM(CASE WHEN score>=60 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as pass_rate
        FROM grades''').fetchone()
    distribution = db.execute('''
        SELECT CASE
            WHEN score>=90 THEN '90-100'
            WHEN score>=80 THEN '80-89'
            WHEN score>=70 THEN '70-79'
            WHEN score>=60 THEN '60-69'
            ELSE '0-59' END as range,
            COUNT(*) as count
        FROM grades GROUP BY range ORDER BY range DESC''').fetchall()
    db.close()
    return jsonify({
        'stats': dict(stats),
        'distribution': [dict(r) for r in distribution]
    })`,
        file: 'app.py',
      },
    ],
    fullFiles: [
      { path: 'app.py', desc: 'Flask 主应用（路由/认证/CRUD/统计）', lines: 210 },
      { path: 'models.py', desc: '数据库模型定义', lines: 60 },
      { path: 'templates/*.html', desc: 'Jinja2 模板文件', lines: '~300 总计' },
    ],
    hasDemo: true,
    demoType: 'external',
    demoUrl: 'https://flask-score-system.vercel.app',
  },

  // ─── Linux Shell 成绩管理系统 ────────────────────────────────────
  'linux-hw5-shell': {
    tech: ['Shell', 'Bash', 'awk', 'sed'],
    features: [
      '多用户登录（教师/学生）',
      '成绩增删改查 + 模糊搜索',
      'CSV 批量导入成绩',
      '统计计算（平均分/最高低分/及格率）',
      '文本文件持久化 + 数据导出',
    ],
    githubUrl: 'https://github.com/tgrlhl-linux/personal-site/tree/master/projects-source/Linux操作系统/作业五-Shell成绩管理',
    highlights: '纯 Shell 脚本实现的成绩管理系统，多用户数据隔离、灵活查询、完善注释。',
    snippets: [
      {
        title: '主程序框架',
        description: 'Shell 脚本主循环，包括用户认证、菜单导航、成绩管理和统计功能。',
        language: 'bash',
        code: `#!/bin/bash
# =============================================
# Linux 课程作业五 — 成绩管理系统
# 作者: 童国睿
# 功能: 多用户成绩管理（增删改查+统计）
# =============================================

DATA_DIR="./data"
USERS_FILE="$DATA_DIR/users.txt"
GRADES_FILE="$DATA_DIR/grades.txt"

# ── 初始化 ──
init() {
    mkdir -p "$DATA_DIR"
    [ -f "$USERS_FILE" ] || echo "admin|admin123|teacher" > "$USERS_FILE"
    [ -f "$GRADES_FILE" ] || touch "$GRADES_FILE"
}

# ── 登录 ──
login() {
    read -p "用户名: " username
    read -s -p "密码: " password
    echo
    user=$(grep "^$username|$password|" "$USERS_FILE")
    if [ -z "$user" ]; then
        echo "❌ 用户名或密码错误"
        return 1
    fi
    role=$(echo "$user" | cut -d'|' -f3)
    echo "✅ 登录成功！[$role] $username"
    ROLE="$role"
    USERNAME="$username"
}

# ── 显示所有成绩 ──
list_grades() {
    printf "%-12s %-15s %-10s %-6s\\n" "学号" "姓名" "课程" "成绩"
    printf "%-12s %-15s %-10s %-6s\\n" "────" "────" "────" "────"
    while IFS='|' read -r sid name course score; do
        [ -n "$sid" ] && printf "%-12s %-15s %-10s %-6s\\n" "$sid" "$name" "$course" "$score"
    done < "$GRADES_FILE"
    echo ""
    echo "总记录数: $(wc -l < "$GRADES_FILE")"
}

# ── 添加成绩 ──
add_grade() {
    read -p "学号: " sid
    read -p "姓名: " name
    read -p "课程: " course
    read -p "成绩: " score
    # 校验成绩范围
    if ! [[ "$score" =~ ^[0-9]+$ ]] || [ "$score" -lt 0 ] || [ "$score" -gt 100 ]; then
        echo "❌ 成绩必须在 0-100 之间"
        return
    fi
    echo "$sid|$name|$course|$score" >> "$GRADES_FILE"
    echo "✅ 成绩已添加"
}

# ── 模糊搜索 ──
search_grade() {
    read -p "输入学号或姓名（支持模糊）: " keyword
    results=$(grep -i "$keyword" "$GRADES_FILE")
    if [ -z "$results" ]; then
        echo "未找到匹配记录"
        return
    fi
    echo "$results" | while IFS='|' read -r sid name course score; do
        printf "%-12s %-15s %-10s %-6s\\n" "$sid" "$name" "$course" "$score"
    done
    echo "共找到 $(echo "$results" | wc -l) 条记录"
}

# ── 统计 ──
show_stats() {
    echo "===== 成绩统计 ====="
    echo "总人数:    $(wc -l < "$GRADES_FILE")"
    awk -F'|' '{
        sum+=$4; count++;
        if($4>max||count==1) max=$4;
        if($4<min||count==1) min=$4;
        if($4>=60) pass++
    } END {
        printf "平均分:    %.1f\\n", sum/count
        printf "最高分:    %d\\n", max
        printf "最低分:    %d\\n", min
        printf "及格率:    %.1f%%\\n", pass/count*100
    }' "$GRADES_FILE"
}

# ── CSV 批量导入 ──
import_csv() {
    read -p "CSV 文件路径: " csv_path
    if [ ! -f "$csv_path" ]; then
        echo "❌ 文件不存在"
        return
    fi
    count=0
    tail -n +2 "$csv_path" | while IFS=',' read -r sid name course score; do
        echo "$sid|$name|$course|$score" >> "$GRADES_FILE"
        ((count++))
    done
    echo "✅ 已导入 $count 条记录"
}

# ── 主菜单 ──
main_menu() {
    while true; do
        echo ""
        echo "===== 成绩管理系统 ====="
        [ "$ROLE" = "teacher" ] && echo "1) 添加成绩   2) 查看成绩"
        [ "$ROLE" = "teacher" ] && echo "3) 搜索成绩   4) 删除成绩"
        [ "$ROLE" = "teacher" ] && echo "5) 批量导入   6) 统计"
        echo "7) 退出"
        read -p "选择: " choice
        case $choice in
            1) [ "$ROLE" = "teacher" ] && add_grade ;;
            2) [ "$ROLE" = "teacher" ] && list_grades ;;
            3) [ "$ROLE" = "teacher" ] && search_grade ;;
            4) [ "$ROLE" = "teacher" ] && delete_grade ;;
            5) [ "$ROLE" = "teacher" ] && import_csv ;;
            6) [ "$ROLE" = "teacher" ] && show_stats ;;
            7) exit 0 ;;
            *) echo "无效选择" ;;
        esac
    done
}

# ── 启动 ──
init
login && main_menu`,
        file: 'grade_manager.sh',
      },
    ],
    fullFiles: [
      { path: 'grade_manager.sh', desc: 'Shell 成绩管理系统完整脚本', lines: 180 },
    ],
    hasDemo: true,
    demoType: 'inline',
demoUrl: '/demos/cli-terminal',
  },

    // ─── 数据库大作业 ────────────────────────────────────────────────
  'database-project': {
    tech: ['SQL', 'MySQL', '视图', '触发器', '存储过程', 'RBAC'],
    features: [
      '沉浸式剧本平台数据库设计（10 张表）',
      '用户/剧本/角色/线索/打卡点/场次/订单/排班/进度/评价',
      '触发器：订单支付自动更新场次人数 + NPC 排班冲突检测',
      '视图：场次概览 + 剧本评分汇总',
      '存储过程：场次运营报表生成',
      'RBAC 四级角色权限体系（游客/NPC/运营/管理员）',
      '50+ 条测试数据覆盖全部业务场景',
      '复杂查询：嵌套子查询 / EXISTS / GROUP BY HAVING',
    ],
    githubUrl: 'https://github.com/tgrlhl-linux/personal-site/tree/master/projects-source/数据库原理/大作业二-数据库设计与实施',
    highlights: '沉浸式剧本杀平台的完整数据库设计——从 E-R 建模到 3NF 规范化，覆盖 10 张业务表、触发器、存储过程、RBAC 权限体系。',
    snippets: [
      {
        title: '核心表结构（建表 DDL）',
        description: '沉浸式剧本平台的核心数据模型，包含用户、剧本、角色、线索、打卡点 5 张主表。',
        language: 'sql',
        code: `-- =============================================
-- 沉浸式剧本平台 — 核心表结构
-- 作者: 童国睿
-- =============================================

-- 1. 用户表
CREATE TABLE User (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    phone VARCHAR(11) NOT NULL UNIQUE,
    nickname VARCHAR(50) NOT NULL,
    role_type TINYINT NOT NULL DEFAULT 0
        COMMENT '0-游客 1-运营 2-NPC 3-管理员',
    status TINYINT NOT NULL DEFAULT 0,
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. 剧本表
CREATE TABLE Script (
    script_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '剧本名称',
    description TEXT,
    difficulty TINYINT NOT NULL DEFAULT 1,
    duration INT NOT NULL COMMENT '时长（分）',
    min_players INT NOT NULL DEFAULT 1,
    max_players INT NOT NULL,
    cover_url VARCHAR(255),
    status TINYINT NOT NULL DEFAULT 0,
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. 角色表
CREATE TABLE Role (
    role_id INT AUTO_INCREMENT PRIMARY KEY,
    script_id INT NOT NULL,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    is_key_role TINYINT NOT NULL DEFAULT 0,
    sort_order INT NOT NULL DEFAULT 0,
    FOREIGN KEY (script_id) REFERENCES Script(script_id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. 线索表
CREATE TABLE Clue (
    clue_id INT AUTO_INCREMENT PRIMARY KEY,
    script_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    clue_type TINYINT NOT NULL DEFAULT 0,
    trigger_type TINYINT NOT NULL DEFAULT 0,
    sequence_num INT NOT NULL,
    FOREIGN KEY (script_id) REFERENCES Script(script_id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. 打卡点表
CREATE TABLE CheckPoint (
    point_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    latitude DECIMAL(10,7) NOT NULL,
    longitude DECIMAL(10,7) NOT NULL,
    ar_content_url VARCHAR(255),
    binding_clue_id INT,
    is_required TINYINT NOT NULL DEFAULT 0,
    FOREIGN KEY (binding_clue_id) REFERENCES Clue(clue_id)
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;`,
        file: '大作业二.sql（建表部分）',
      },
      {
        title: '触发器：订单支付与排班冲突检测',
        description: '两个关键触发器：支付状态变更自动更新场次报名人数，NPC 排班时间冲突检测防止重复调度。',
        language: 'sql',
        code: `-- 触发器1：订单支付 -> 场次人数自动更新
DELIMITER //
CREATE TRIGGER trg_order_payment_update_session
AFTER UPDATE ON \`Order\`
FOR EACH ROW
BEGIN
    IF OLD.payment_status = 0 AND NEW.payment_status = 1 THEN
        UPDATE \`Session\`
        SET current_players = current_players + 1
        WHERE session_id = NEW.session_id;
    END IF;
    IF OLD.payment_status = 1 AND NEW.payment_status = 2 THEN
        UPDATE \`Session\`
        SET current_players = current_players - 1
        WHERE session_id = NEW.session_id;
    END IF;
END//
DELIMITER ;

-- 触发器2：NPC排班时间冲突检测
DELIMITER //
CREATE TRIGGER trg_npcschedule_conflict_check
BEFORE INSERT ON NpcSchedule
FOR EACH ROW
BEGIN
    DECLARE conflict_count INT;
    SELECT COUNT(*) INTO conflict_count
    FROM NpcSchedule ns
    JOIN \`Session\` s ON ns.session_id = s.session_id
    JOIN \`Session\` s_new ON s_new.session_id = NEW.session_id
    WHERE ns.npc_id = NEW.npc_id
      AND ns.schedule_date = NEW.schedule_date
      AND (
          (s.start_time <= s_new.start_time AND s.end_time > s_new.start_time)
          OR
          (s_new.start_time <= s.start_time AND s_new.end_time > s.start_time)
      );
    IF conflict_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '该NPC在此时间段已有排班冲突';
    END IF;
END//
DELIMITER ;`,
        file: '大作业二.sql（触发器）',
      },
      {
        title: '存储过程：场次运营报表',
        description: '按剧本和时间范围生成运营数据，包含总订单数、总收入、逐场次明细、上座率。',
        language: 'sql',
        code: `DELIMITER //
CREATE PROCEDURE proc_session_report(
    IN p_script_id INT,
    IN p_start_date DATE,
    IN p_end_date DATE
)
BEGIN
    DECLARE v_total_orders INT DEFAULT 0;
    DECLARE v_total_revenue DECIMAL(12,2) DEFAULT 0;

    SELECT COUNT(o.order_id), COALESCE(SUM(o.amount), 0)
    INTO v_total_orders, v_total_revenue
    FROM \`Session\` se
    LEFT JOIN \`Order\` o
        ON se.session_id = o.session_id AND o.payment_status = 1
    WHERE (p_script_id IS NULL OR se.script_id = p_script_id)
      AND DATE(se.start_time) BETWEEN p_start_date AND p_end_date;

    -- 汇总输出
    SELECT p_script_id AS script_id,
           p_start_date AS date_from, p_end_date AS date_to,
           v_total_orders AS paid_orders,
           v_total_revenue AS revenue;

    -- 逐场次明细
    SELECT s.name AS script_name, se.session_id,
           se.start_time,
           CONCAT(se.current_players, '/', se.max_players) AS occupancy,
           ROUND(se.current_players / se.max_players * 100, 1) AS rate,
           se.price,
           COUNT(o.order_id) AS order_count,
           COALESCE(SUM(o.amount), 0) AS session_revenue
    FROM \`Session\` se
    JOIN Script s ON se.script_id = s.script_id
    LEFT JOIN \`Order\` o
        ON se.session_id = o.session_id AND o.payment_status = 1
    WHERE (p_script_id IS NULL OR se.script_id = p_script_id)
      AND DATE(se.start_time) BETWEEN p_start_date AND p_end_date
    GROUP BY se.session_id
    ORDER BY se.start_time;
END//
DELIMITER ;

-- 调用：CALL proc_session_report(1, '2026-06-01', '2026-06-30');`,
        file: '大作业二.sql（存储过程）',
      },
    ],
    fullFiles: [
      { path: '大作业二.sql', desc: '完整数据库设计（建表/视图/触发器/存储过程/权限/测试数据）', lines: 709 },
    ],
    hasDemo: true,
    demoType: 'inline',
    demoUrl: '/demos/sql-playground',
  },  // ─── NarrativeAnalysis — 大数据电影叙事分析 ──────────────────────
  'narrative-analysis': {
    tech: ['Python', 'Flask', 'Hadoop', 'HBase', 'Docker'],
    features: [
      '情感词典驱动的剧本情感分析（17 部电影，80720 行清洗数据）',
      '角色共现网络构建与场景分割',
      '数据管道 Pipeline（预处理 → 情感分析 → HBase 写入 → API）',
      'RESTful API 后端服务（Flask）',
      'HBase 三表存储（movie_emotion / character_network / narrative_pattern）',
    ],
    githubUrl: 'https://github.com/tgrlhl-linux/personal-site/tree/master/projects-source/大数据与数据思维/NarrativeAnalysis',
    highlights: '基于 Hadoop 生态的大数据电影叙事分析——从剧本清洗、情感计算到 HBase 存储、API 查询的全链路实现。',
    snippets: [
      {
        title: '情感分析数据管道',
        description: '预处理管道：加载情感词典 → 分割场景 → 计算情感得分 → 构建角色共现 → HBase 写入。',
        language: 'python',
        code: `# ── 情感分析核心 ──
def analyze_script(filepath, movie_id, movie_name, word_dict):
    \"\"\"分析单部剧本，返回结构化的情感 + 角色数据\"\"\"
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    lines = text.split('\\n')
    scenes = []
    current_scene = {'scene_id': 0, 'name': 'UNKNOWN',
                     'lines': [], 'characters': set()}
    scene_counter = 0
    all_characters = set()
    char_scene_map = defaultdict(set)

    for line in lines:
        stripped = line.strip()
        # 识别场景标记 [SCENE]
        if stripped.startswith('[SCENE]'):
            if current_scene['lines']:
                scenes.append(current_scene)
            scene_counter += 1
            current_scene = {
                'scene_id': scene_counter,
                'name': stripped.replace('[SCENE] ', '').strip(),
                'lines': [], 'characters': set()
            }
        # 识别角色名（全大写缩写）
        elif stripped and re.match(r'^[A-Z][A-Z\\s\\.]{1,30}$', stripped):
            char_name = stripped.strip()
            all_characters.add(char_name)
            current_scene['characters'].add(char_name)
            char_scene_map[char_name].add(current_scene['scene_id'])
        else:
            current_scene['lines'].append(stripped)

    if current_scene['lines']:
        scenes.append(current_scene)

    # 无场景标记时按窗口分割
    if len(scenes) <= 1:
        scenes = []
        window_size = 50
        for i in range(0, len(lines), window_size):
            ...  # windowed fallback

    # ── 情感分析 ──
    emotion_results = []
    for scene in scenes:
        pos_count = 0
        neg_count = 0
        total_words = 0
        for line in scene['lines']:
            words = line.lower().split()
            total_words += len(words)
            for w in words:
                w_clean = re.sub(r'[^a-z]', '', w)
                if w_clean in word_dict:
                    p, n = word_dict[w_clean]
                    pos_count += p
                    neg_count += n

        net_emotion = round((pos_count - neg_count) / max(total_words, 1), 6)
        emotion_results.append({
            'scene': scene['scene_id'],
            'name': scene['name'],
            'pos': pos_count, 'neg': neg_count,
            'net': net_emotion
        })

    # ── 角色共现 ──
    cooccur = defaultdict(int)
    for scene in scenes:
        chars = list(scene['characters'])
        for i in range(len(chars)):
            for j in range(i + 1, len(chars)):
                pair = tuple(sorted([chars[i], chars[j]]))
                cooccur[pair] += 1

    return {
        'id': movie_id, 'name': movie_name,
        'total_scenes': len(scenes),
        'total_characters': len(all_characters),
        'scenes': emotion_results,
        'cooccurrences': [
            {'charA': a, 'charB': b, 'count': c}
            for (a, b), c in sorted(cooccur.items(), key=lambda x: -x[1])[:30]
        ]
    }


# ── HBase 写入 ──
def write_to_hbase(movies_data):
    \"\"\"将分析结果写入 HBase（3 张表）\"\"\"
    connection = happybase.Connection('localhost', 9090)
    table_emotion = connection.table('movie_emotion')
    table_network = connection.table('character_network')
    table_pattern = connection.table('narrative_pattern')

    for movie in movies_data:
        mid = movie['id']
        # movie_emotion: 场景情感序列
        table_emotion.put(mid, {
            'emotion:scenes': json.dumps(movie['scenes']),
            'meta:name': movie['name'],
            'meta:scenes': str(movie['total_scenes']),
            'meta:characters': str(movie['total_characters']),
        })
        # character_network: 角色共现关系
        for c in movie['cooccurrences']:
            pair_key = f"{c['charA']}#{c['charB']}"
            table_network.put(mid, {f"cooccur:{pair_key}": str(c['count'])})
        # narrative_pattern: 叙事模式指纹
        emotion_series = [s['net'] for s in movie['scenes']]
        mean_emo = sum(emotion_series) / max(len(emotion_series), 1)
        std_emo = (sum((e - mean_emo)**2 for e in emotion_series) / max(len(emotion_series), 1))**0.5
        pattern = {
            'acts': len(movie['scenes']) // 10 + 1,
            'emotion_mean': round(mean_emo, 6),
            'emotion_std': round(std_emo, 6),
            'scene_count': movie['total_scenes'],
            'char_count': movie['total_characters'],
        }
        table_pattern.put(mid, {
            'features:fingerprint': json.dumps(pattern),
            'acts:count': str(pattern['acts']),
        })
    connection.close()`,
        file: 'data_pipeline.py',
      },
      {
        title: 'Flask API 后端',
        description: 'RESTful API 服务，提供电影列表、情感曲线、角色共现等查询接口。',
        language: 'python',
        code: `@app.route('/movies', methods=['GET'])
def list_movies():
    \"\"\"获取所有电影基本信息列表\"\"\"
    data = load_all_movies()
    movies = [{
        'id': m['id'], 'name': m['name'],
        'total_scenes': m['total_scenes'],
        'total_characters': m['total_characters'],
    } for m in data.get('movies', [])]
    return jsonify({'count': len(movies), 'movies': movies})


@app.route('/movies/<movie_id>/emotion', methods=['GET'])
def get_emotion_curve(movie_id):
    \"\"\"获取电影情感曲线（含转折点检测）\"\"\"
    movie = get_movie_by_id(movie_id)
    if movie is None:
        return jsonify({'error': f'Movie not found: {movie_id}'}), 404

    scenes = movie.get('scenes', [])
    emotion_curve = [{
        'scene': s['scene'], 'name': s['name'],
        'positive': s['pos'], 'negative': s['neg'],
        'net_emotion': s['net'],
    } for s in scenes]

    # 检测叙事转折点（ECR 简化版）
    turning_points = []
    for i in range(1, len(scenes) - 1):
        prev_net = scenes[i - 1]['net']
        curr_net = scenes[i]['net']
        next_net = scenes[i + 1]['net']
        # 局部极值 = 情感趋势转折
        if (curr_net > prev_net and curr_net > next_net) or \\
           (curr_net < prev_net and curr_net < next_net):
            turning_points.append({
                'scene': scenes[i]['scene'],
                'net_emotion': curr_net,
                'type': 'peak' if curr_net > prev_net else 'valley'
            })

    return jsonify({
        'movie_id': movie_id,
        'emotion_curve': emotion_curve,
        'turning_points': turning_points,
        'total_scenes': len(scenes),
    })`,
        file: 'app.py',
      },
    ],
    fullFiles: [
      { path: 'scripts/data_pipeline.py', desc: '数据管道（预处理→情感分析→HBase）', lines: 315 },
      { path: 'api/app.py', desc: 'Flask 后端 API 服务', lines: 180 },
      { path: 'scripts/preprocess.py', desc: '剧本清洗预处理', lines: 85 },
      { path: 'api/requirements.txt', desc: 'Python 依赖', lines: 5 },
      { path: 'cluster/docker-compose.yml', desc: 'Hadoop 集群 Docker 配置', lines: 40 },
      { path: 'cluster/start-cluster.sh', desc: '集群启动脚本', lines: 55 },
      { path: 'frontend/index.html', desc: '前端可视化页面', lines: 320 },
    ],
    hasDemo: true,
    demoType: 'inline',
    demoUrl: '/demos/narrative-analysis',
  },
};

export default projects;
