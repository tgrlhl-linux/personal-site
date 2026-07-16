---
title: "Flask 成绩管理系统（Web）"
description: "将 Shell 成绩管理系统迁移到 Flask Web 框架，实现浏览器交互、数据库持久化"
date: 2026-06-10
tags: ["Python", "Flask", "SQLite", "Web"]
category: "course"
status: "completed"
---

## 项目概述

从 Shell 脚本版本迁移到 Python Flask 框架的 Web 版成绩管理系统，前后端分离设计。

## 核心功能

- **登录注册**：教师/学生双角色，Session 会话管理
- **CRUD**：通过 Web 界面完成成绩的增删改查
- **SQLite 存储**：使用关系数据库替代文本文件，支持复杂查询
- **统计看板**：可视化展示班级成绩分布、趋势图
- **响应式 UI**：适配桌面和移动端

## 技术栈

- **后端**：Flask + SQLite + Jinja2 模板
- **前端**：HTML5 + CSS3 + 原生 JavaScript
- **部署**：支持 `gunicorn` 部署到 Linux 服务器
