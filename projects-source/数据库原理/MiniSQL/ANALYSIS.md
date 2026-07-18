# MiniSQL — 纯 Java 自研 SQL 引擎

## 项目概述

MiniSQL 是一个从零实现的关系型数据库引擎，覆盖 SQL 处理的完整链路：**词法分析 → 语法分析 → 查询执行 → 存储管理**，零外部依赖，仅使用纯 JDK 标准库。

## 架构设计

```
                            ┌─────────────┐
   SQL String ─────────────►│  Tokenizer   │──► Token 流
                            └─────────────┘
                                     ▼
                            ┌─────────────┐
                            │   Parser     │──► AST 语法树
                            └─────────────┘
                                     ▼
                            ┌─────────────┐
                            │   Engine     │──► 查询执行
                            └─────────────┘
                                     ▼
                            ┌─────────────┐
                            │   Storage    │──► 页式文件
                            └─────────────┘
```

### 模块说明

| 模块 | 路径 | 职责 |
|------|------|------|
| **Tokenizer** | `sql/tokenizer/` | 字符串→Token 流。支持关键字、字符串、整数、注释（行/块） |
| **Parser** | `sql/parser/` | Token 流→AST。递归下降解析，支持 CREATE/INSERT/SELECT/DELETE |
| **Engine** | `sql/engine/` | AST→执行。表扫描、条件过滤、投影、类型强制转换 |
| **Storage** | `sql/storage/` | 页式文件存储、行序列化、B+ 树索引 |
| **Web UI** | `web/` | 内嵌 HTTP Server，浏览器内交互式 SQL 执行 |

## 技术亮点

### 1. 手写词法分析器

Tokenizer 从零手写，不依赖任何解析器生成器：
- 支持 `--` 行注释和 `/* */` 块注释
- 关键字识别（CREATE, TABLE, INSERT, SELECT, DELETE 等）
- 字符串字面量处理（含转义字符）
- 整数、标识符、操作符的精确定位

### 2. 递归下降解析器

Parser 使用标准的递归下降解析模式：
- 每个语法产生式对应一个方法（`parseCreateTable`, `parseInsert` 等）
- 支持 AND/OR 逻辑表达式的优先级解析
- 错误位置精确定位

### 3. 内嵌 HTTP 服务器

无需 Tomcat 或 Spring Boot，通过 `com.sun.net.httpserver.HttpServer` 内嵌 Web 服务器：
- 浏览器中输入 SQL → 服务端执行 → 表格化结果返回
- 完整的 RESTful 接口设计

## 设计决策

| 决策 | 方案 | 理由 |
|------|------|------|
| 零外部依赖 | 纯 JDK | 教学项目，避免配置复杂性 |
| 存储格式 | 定长页式 | 简化磁盘管理，便于理解数据库内核 |
| 输出格式 | Unicode 框线表格 | 终端可读性好，支持管道重定向 |
| Web 接口 | 内嵌 HTTP Server | 零部署成本，开箱即用 |

## 构建与运行

```bash
# 编译
javac -d out src/minisql/**/*.java

# 运行 REPL
java -cp out minisql.MiniSQL

# 启动 Web UI
java -cp out minisql.web.MiniQLServer
# 浏览器打开 http://localhost:8080
```

## 与网站演示的关系

网站上的 [MiniSQL 在线演示](/demos/minisql) 是一个纯前端的 SQL 模拟器，实现了与 MiniSQL 兼容的 SQL 语法和交互体验。后端 Java 引擎的完整源码在本目录的 `src/` 下。
