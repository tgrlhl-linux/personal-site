# Flask 成绩管理系统

## 项目概述

从 Shell 版成绩管理迁移到 Flask Web 框架的全栈重构。后端使用 Flask + SQLite，前端使用 Jinja2 模板引擎，实现了完整的成绩管理系统，包含数据隔离、权限控制、批量操作和多维度统计报表。

## 架构设计

系统分为三个层次：

路由层（app.py）处理所有 HTTP 请求和响应，包含登录、仪表盘、学生管理、成绩查询、排序、统计报表、批量录入和用户管理等 10+ 个端点。使用装饰器 login_required 统一处理登录校验和角色鉴权。

数据层（models.py + init_db.py）封装 SQLite 数据库操作。models.py 提供 get_db() 连接管理，以及学生统计、GPA 计算、数据隔离过滤等工具函数。init_db.py 负责从 CSV 导入初始数据并构建四张核心表（classes/students/subjects/scores）及用户表。

视图层（templates/）包含 10 个 Jinja2 模板，采用 base.html 继承机制实现一致的布局风格。仪表盘展示关键统计数据，学生列表支持分页和搜索。

## 技术亮点

数据隔离的 SQL 级实现：get_scope_filter_sql() 函数根据用户角色动态生成 SQL WHERE 片段。admin 返回空条件（不限），teacher 生成班级 IN 子查询，student 生成学号等值条件。这个 SQL 片段追加到所有查询末尾，从数据库层面保证数据安全，而非在应用层过滤。

CSV 到 SQLite 的自动迁移：init_db.py 启动时自动读取 CSV 文件，解析页眉中的学分信息（[学分] 格式），构建 subjects 表，逐行导入学生成绩。学号末位自动映射班级归属，一次性完成全量数据初始化。

批量录入的前后端联动：前端支持多行输入"学号 成绩"，AJAX 调用后端后先展示预览（显示学生姓名、当前值、新值），用户确认后才写入数据库。这种预览-确认模式大幅降低了误操作风险。

## 设计决策

从 Shell 版迁移到 Web 版时，保留了完全相同的权限模型（admin/teacher/student 三级）和数据隔离逻辑，但将实现从函数级别提升到 SQL 级别，确保无论通过什么入口访问数据，隔离都生效。SQLite 的选择延续了零依赖的简洁性，无需额外数据库服务。

## 关键代码解读

```python
def get_scope_filter_sql(role, scope, table_alias='s'):
    if role == 'admin' or not scope:
        return '', []
    if role == 'teacher':
        sql = f' AND {table_alias}.id IN (SELECT id FROM students WHERE class_id IN (SELECT id FROM classes WHERE name IN ({placeholders})))'
        return sql, class_names
    if role == 'student':
        return f' AND {table_alias}.id = ?', [scope]
```

该函数是权限系统的核心，通过动态拼接 SQL 条件实现数据隔离。teacher 角色的子查询实现了从 scope（班级名列表）到学生 ID 的间接映射，无需在应用层缓存班级-学生关系。这种模式的优点是查询由 SQLite 优化器处理，且无法被应用层绕过。
