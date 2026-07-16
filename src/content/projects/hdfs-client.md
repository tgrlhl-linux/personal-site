---
title: "HDFS 客户端操作"
description: "基于 Hadoop 3.3.4 实现 11 个 HDFS 客户端操作，覆盖 CRUD、IO流、块读取、参数优先级"
date: 2026-04-26
tags: ["Java", "Hadoop", "HDFS", "大数据"]
category: "course"
status: "completed"
---

## 项目概述

大数据课程作业一：基于 Hadoop 3.3.4 分布式集群（1主2从），使用 Java API 实现 HDFS 客户端完整操作。

## 实现功能

- **目录操作**：创建、删除、递归遍历目录
- **文件操作**：上传、下载、重命名、删除
- **IO 流操作**：通过 FSDataInputStream/OutputStream 读写
- **块读取**：获取文件的块信息及位置
- **参数优先级**：代码配置 > 资源文件 > 集群默认配置

## 环境

- Hadoop 3.3.4 完全分布式集群（Linux）
- IDEA + Maven 在 Windows 端远程连接
- 11 个测试案例全部通过
