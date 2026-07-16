---
title: "MiniSQL — 纯 Java SQL 引擎"
description: "从零实现的轻量级关系型数据库，支持 SQL 解析、查询执行、事务管理，无任何外部依赖"
date: 2026-06-10
tags: ["Java", "SQL", "数据库", "编译器"]
category: "course"
status: "completed"
---

## 项目概述

MiniSQL 是一个 **纯 Java 实现的轻量级关系型数据库引擎**，零外部依赖，完整覆盖 SQL 执行的全链路。

## 核心功能

- **词法/语法分析**：手写 Lexer + Parser，将 SQL 文本解析为 AST
- **查询执行**：支持 SELECT / INSERT / UPDATE / DELETE / CREATE TABLE / DROP TABLE
- **存储引擎**：自定义页式文件存储，支持 B+ 树索引
- **事务管理**：基础的 ACID 支持，WAL 日志
- **Web UI**：内嵌 HTTP Server，通过浏览器交互

## 技术特点

- 零依赖 —— 除 JDK 标准库外不使用任何第三方库
- 分层架构 —— 解析层 → 优化层 → 执行层 → 存储层清晰分离
- 支持 JDBC-like 接口调用
