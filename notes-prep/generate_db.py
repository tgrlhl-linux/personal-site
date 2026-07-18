#!/usr/bin/env python3
"""Generate database principle notes."""

import os

OUT = r'E:\Claudecode\personal-site\notes-prep'

def w(filename, content):
    path = os.path.join(OUT, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'  OK {filename}')

# SVG: Three-level schema structure
SVG_SCHEMA = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 580 200" width="100%" height="200">
  <rect x="20" y="10" rx="5" ry="5" width="540" height="40" fill="#e3f2fd" stroke="#1976d2" stroke-width="1.5"/>
  <text x="160" y="34" text-anchor="middle" font-size="12" fill="#1565c0" font-weight="bold">外模式（用户视图）</text>
  <text x="370" y="34" text-anchor="middle" font-size="11" fill="#555">用户的局部数据视图</text>
  <line x1="290" y1="50" x2="290" y2="65" stroke="#555" stroke-width="1.5" marker-end="url(#dsa)"/>
  <text x="300" y="62" font-size="10" fill="#e65100">外模式/模式映象 → 逻辑独立性</text>
  <rect x="20" y="70" rx="5" ry="5" width="540" height="40" fill="#e8f5e9" stroke="#43a047" stroke-width="1.5"/>
  <text x="160" y="94" text-anchor="middle" font-size="12" fill="#2e7d32" font-weight="bold">模式（逻辑视图）</text>
  <text x="370" y="94" text-anchor="middle" font-size="11" fill="#555">全体数据的逻辑结构</text>
  <line x1="290" y1="110" x2="290" y2="125" stroke="#555" stroke-width="1.5" marker-end="url(#dsa)"/>
  <text x="300" y="122" font-size="10" fill="#e65100">模式/内模式映象 → 物理独立性</text>
  <rect x="20" y="130" rx="5" ry="5" width="540" height="40" fill="#fff3e0" stroke="#e65100" stroke-width="1.5"/>
  <text x="160" y="154" text-anchor="middle" font-size="12" fill="#e65100" font-weight="bold">内模式（存储视图）</text>
  <text x="370" y="154" text-anchor="middle" font-size="11" fill="#555">数据的物理存储方式</text>
  <defs><marker id="dsa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="#555"/></marker></defs>
</svg>'''

SVG_FD = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 160" width="100%" height="160">
  <text x="10" y="22" font-size="14" font-weight="bold" fill="#333">函数依赖分类</text>
  <text x="20" y="45" font-size="13" fill="#555">X → Y</text>
  <line x1="100" y1="45" x2="200" y2="65" stroke="#999" stroke-width="1"/>
  <line x1="100" y1="45" x2="400" y2="65" stroke="#999" stroke-width="1"/>
  <text x="120" y="70" font-size="12" fill="#2e7d32">非平凡依赖</text>
  <text x="320" y="70" font-size="12" fill="#1565c0">平凡依赖</text>
  <text x="120" y="85" font-size="10" fill="#999">Y &#x2288; X</text>
  <text x="320" y="85" font-size="10" fill="#999">Y &#x2286; X</text>
  <line x1="200" y1="90" x2="170" y2="110" stroke="#999" stroke-width="1"/>
  <line x1="200" y1="90" x2="280" y2="110" stroke="#999" stroke-width="1"/>
  <text x="130" y="118" font-size="12" fill="#e65100">完全函数依赖</text>
  <text x="240" y="118" font-size="12" fill="#e65100">部分函数依赖</text>
  <text x="130" y="133" font-size="10" fill="#999">X' &#x2192; Y 不存在</text>
  <text x="240" y="133" font-size="10" fill="#999">&#x2203;X' 使 X' &#x2192; Y</text>
  <line x1="300" y1="90" x2="350" y2="110" stroke="#999" stroke-width="1"/>
  <text x="370" y="118" font-size="12" fill="#e65100">传递函数依赖</text>
  <text x="370" y="133" font-size="10" fill="#999">X&#x2192;Y, Y&#x2192;Z, Y&#x2192;X</text>
</svg>'''

print("=== 生成数据库原理笔记 ===")

# DB-00 目录
w('DB-00-目录与总览.md', '''# 《数据库系统原理》期末复习笔记 · 目录

> 基于软工 24 级复习 PPT、2022-2023 期末试卷及复习题整理

| 章节 | 内容 | 难度 |
|------|------|------|
| [DB-01 绪论](DB-01-绪论.md) | 核心概念、三级模式、数据模型、E-R图 | ⭐⭐ |
| [DB-02 关系数据库](DB-02-关系数据库.md) | 关系代数、完整性约束、集合/专门运算 | ⭐⭐⭐⭐ |
| [DB-03 SQL语言](DB-03-SQL语言.md) | DDL/DML/DQL、连接/嵌套/集合查询、视图、授权 | ⭐⭐⭐⭐ |
| [DB-04 数据库安全性与完整性](DB-04-安全性与完整性.md) | 存取控制、触发器、约束 | ⭐⭐⭐ |
| [DB-05 关系数据理论](DB-05-关系数据理论.md) | 函数依赖、范式判定、闭包算法、最小依赖集 | ⭐⭐⭐⭐⭐ |
| [DB-06 数据库设计](DB-06-数据库设计.md) | 设计阶段、E-R图转关系模式 | ⭐⭐⭐ |

> **复习建议**：DB-02（关系代数表达式）和 DB-05（范式判定+闭包计算）为必考大题。
> DB-03（SQL）覆盖选择题+填空题+SQL语句书写题。
''')

# DB-01
w('DB-01-绪论.md', f'''# DB-01 绪论

## 一、核心概念

| 概念 | 定义 |
|------|------|
| **数据 Data** | 描述事物的符号记录 |
| **数据库 DB** | 长期存储在计算机内、有组织、可共享的大量数据集合 |
| **数据库管理系统 DBMS** | 位于用户与 OS 之间的数据管理软件 |
| **数据库系统 DBS** | DB + DBMS + 应用系统 + DBA + 用户 |

## 二、DBMS 主要功能

```
1. 数据定义          2. 数据组织存储和管理
3. 数据操纵          4. 事务管理和运行管理
5. 数据库的建立和维护
```

## 三、数据管理发展

```
人工管理 → 文件系统 → 数据库系统

数据库系统特点：
① 数据结构化 ② 共享性高、冗余度低
③ 数据独立性高 ④ DBMS 统一管理和控制
```

## 四、数据独立性

{SVG_SCHEMA}

**逻辑独立性**：模式改变 → 修改外模式/模式映象 → 应用程序不变

**物理独立性**：存储结构改变 → 修改模式/内模式映象 → 应用程序不变

## 五、数据模型三要素

```
① 数据结构   ② 数据操作   ③ 数据约束条件
```

## 六、E-R 模型

| 图形 | 含义 |
|------|------|
| 矩形 | 实体型 |
| 椭圆 | 属性 |
| 菱形 | 联系（标 1:1, 1:n, m:n） |

**联系类型**：
- 1:1 — 班级与班主任
- 1:n — 班级与学生
- m:n — 学生与课程

## 七、典型例题

**例题**：企业数据库做了两项操作：
① 迁移数据存储硬盘
② 为核心表增加新字段

两项操作均未影响前端业务程序。请写出对应的两大特性。

> **答**：
> ① **物理独立性**：物理存储位置改变，应用程序不受影响
> ② **逻辑独立性**：表结构增加字段，应用程序不受影响
''')

# DB-02
w('DB-02-关系数据库.md', '''# DB-02 关系数据库

## 一、基本概念

```
关系 = 二维表（行=元组，列=属性）
候选码 = 能唯一标识元组的最小属性组
主码 = 选定的候选码
外码 = 引用其他表主码的属性
全码 = 所有属性都是候选码
```

## 二、三类完整性约束

| 完整性 | 规则 | 例子 |
|--------|------|------|
| **实体完整性** | 主属性不能取空值 | 学号不能为空 |
| **参照完整性** | 外码取空值或对应主码值 | 专业号必须是专业表中存在的 |
| **用户定义完整性** | 特定语义约束 | 性别只能取男/女 |

## 三、传统集合运算

| 运算 | 含义 | 条件 |
|------|------|------|
| 并 (R&#x222A;S) | 两关系所有元组 | 同属性域 |
| 交 (R&#x2229;S) | 两关系共有元组 | 同属性域 |
| 差 (R&#x2212;S) | R有S无的元组 | 同属性域 |
| 笛卡尔积 (R&#x00D7;S) | 所有组合 | 任意 |

## 四、专门关系运算

| 运算 | 符号 | 含义 |
|------|------|------|
| **选择** | &#x03C3;<sub>条件</sub>(R) | 选取满足条件的行 |
| **投影** | &#x03C0;<sub>列</sub>(R) | 选取指定列 |
| **等值连接** | R &#x22C8;<sub>A=B</sub> S | 等值条件连接，保留重复列 |
| **自然连接** | R &#x22C8; S | 同名属性等值，去重复列 |
| **除** | R &#x00F7; S | 包含S中所有值的X分量 |

## 五、综合查询例题

设有关系模式：
```
Student(Sno, Sname, Ssex, Sage, Sdept)
Course(Cno, Cname, Cpno, Credit)
SC(Sno, Cno, Grade)
```

**例1**：查询选修了2号课程的学生姓名
> &#x03C0;<sub>Sname</sub>(&#x03C3;<sub>Cno='2'</sub>(SC &#x22C8; Student))

**例2**：查询选修了所有课程的学生学号
> &#x03C0;<sub>Sno,Cno</sub>(SC) &#x00F7; &#x03C0;<sub>Cno</sub>(Course)

**例3**：查询没有不及格课程的学生学号和姓名
> &#x03C0;<sub>Sno,Sname</sub>(Student) &#x2212; &#x03C0;<sub>Sno,Sname</sub>(&#x03C3;<sub>Grade&lt;60</sub>(Student &#x22C8; SC))

**例4**：查询选修了"数据库原理"的学生姓名
> &#x03C0;<sub>Sname</sub>(&#x03C3;<sub>Cname='数据库原理'</sub>(Course &#x22C8; SC &#x22C8; Student))

**例5**：查询至少选修了95001选修的所有课程的学生学号（除法的典型应用）
> 设 S = &#x03C0;<sub>Cno</sub>(&#x03C3;<sub>Sno='95001'</sub>(SC))
> 结果 = &#x03C0;<sub>Sno,Cno</sub>(SC) &#x00F7; S

> 注意：等值连接与自然连接的区别——等值连接不要求同名属性，不自动去重列；自然连接要求同名属性且去重。
''')

# DB-03
w('DB-03-SQL语言.md', '''# DB-03 SQL 语言

## 一、SQL 特点

```
① 综合统一 ② 高度非过程化 ③ 面向集合 ④ 两种使用方式 ⑤ 语言简洁
```

## 二、数据定义 DDL

```sql
-- 创建表
CREATE TABLE Student (
  Sno   CHAR(6) PRIMARY KEY,
  Sname CHAR(8) NOT NULL,
  Sage  INT,
  Ssex  ENUM('F','M'),
  Sdept CHAR(10),
  FOREIGN KEY (Sdept) REFERENCES Dept(Dno)
);

-- 修改表
ALTER TABLE Student ADD COLUMN Email VARCHAR(50);
ALTER TABLE Student DROP COLUMN Email;

-- 删除表
DROP TABLE Student;

-- 索引
CREATE UNIQUE INDEX idx_sno ON Student(Sno);
CREATE CLUSTER INDEX idx_dept ON Student(Sdept);
DROP INDEX idx_sno ON Student;
```

## 三、数据查询 DQL

### 基本结构
```sql
SELECT [ALL|DISTINCT] <目标列>
FROM <表名>
[WHERE <条件>]
[GROUP BY <列名> [HAVING <条件>]]
[ORDER BY <列名> [ASC|DESC]];
```

### 单表查询
```sql
-- 条件查询
SELECT * FROM Student WHERE Sdept = 'CS';

-- 多重条件
SELECT Sname FROM Student WHERE Sdept = 'CS' AND Sage < 20;

-- 排序
SELECT Sno, Grade FROM SC WHERE Cno = '3' ORDER BY Grade DESC;

-- 聚集函数
SELECT COUNT(*) FROM Student;                        -- 总人数
SELECT AVG(Grade) FROM SC WHERE Cno = '1';           -- 平均分
```

### 分组查询
```sql
-- 各课程选课人数
SELECT Cno, COUNT(Sno) AS 人数
FROM SC
GROUP BY Cno;

-- 选修2门以上课程的学生学号
SELECT Sno FROM SC
GROUP BY Sno
HAVING COUNT(*) > 2;
```

### 连接查询
```sql
-- 等值连接
SELECT Student.*, SC.*
FROM Student, SC
WHERE Student.Sno = SC.Sno;

-- 复合条件连接：2号课程成绩>90的学生
SELECT Student.Sno, Sname
FROM Student, SC
WHERE Student.Sno = SC.Sno
  AND SC.Cno = '2'
  AND SC.Grade > 90;
```

### 嵌套查询
```sql
-- IN 子查询：与刘晨同系的学生
SELECT Sno, Sname, Sdept
FROM Student
WHERE Sdept IN (
  SELECT Sdept FROM Student WHERE Sname = '刘晨'
);

-- EXISTS：选修了1号课程的学生姓名
SELECT Sname FROM Student
WHERE EXISTS (
  SELECT * FROM SC
  WHERE SC.Sno = Student.Sno AND Cno = '1'
);
```

### 集合查询
```sql
SELECT * FROM Student WHERE Sdept = 'CS'
UNION
SELECT * FROM Student WHERE Sage <= 19;
```

## 四、数据更新 DML

```sql
-- 插入
INSERT INTO Student VALUES ('95020', '陈冬', '男', 'IS', 18);

-- 更新（所有学生年龄+1）
UPDATE Student SET Sage = Sage + 1;

-- 带子查询的更新（CS系学生成绩置零）
UPDATE SC SET Grade = 0
WHERE Sno IN (SELECT Sno FROM Student WHERE Sdept = 'CS');

-- 删除
DELETE FROM SC WHERE Cno = '2';
DELETE FROM SC;       -- 所有选课记录
```

## 五、视图

```sql
-- 创建视图
CREATE VIEW IS_Student AS
SELECT Sno, Sname, Sage
FROM Student
WHERE Sdept = 'IS';

-- 删除视图
DROP VIEW IS_Student;
```

> 视图是虚表，只存定义不存数据。基表数据变化，视图查询结果也随之变化。
> **可更新的视图**：行列子集视图（单表，不含聚集/分组/DISTINCT）
> **不可更新的视图**：含聚集函数、多表连接、GROUP BY 的视图

## 六、授权与回收

```sql
-- 授权
GRANT SELECT ON TABLE Student TO U1;
GRANT ALL PRIVILEGES ON TABLE Student, Course TO U2, U3;
GRANT SELECT ON TABLE SC TO PUBLIC;
GRANT UPDATE(Sno), SELECT ON TABLE Student TO U4 WITH GRANT OPTION;

-- 回收
REVOKE UPDATE(Sno) ON TABLE Student FROM U4;
```

## 七、典型例题

**例题**：建立一个包含完整性定义的选课表SC

```sql
CREATE TABLE SC (
  SNO   CHAR(9) NOT NULL,
  CNO   CHAR(4) NOT NULL,
  GRADE SMALLINT,
  PRIMARY KEY (SNO, CNO),
  FOREIGN KEY (SNO) REFERENCES Student(SNO),
  FOREIGN KEY (CNO) REFERENCES Course(CNO)
);
```
这里 (SNO, CNO) 为联合主码，同时 SNO 和 CNO 分别为参照 Student 表和 Course 表的外码。
''')

# DB-04
w('DB-04-安全性与完整性.md', '''# DB-04 数据库安全性与完整性

## 一、数据库安全性

### 安全性控制常用方法

```
用户标识和鉴别 → 存取控制 → 视图机制 → 审计 → 数据加密
```

### 存取控制类型

| 类型 | 特点 |
|------|------|
| **自主存取控制 DAC** | 用户可自主授予/收回权限（GRANT/REVOKE） |
| **强制存取控制 MAC** | 基于敏感度标记，系统统一控制 |

### 敏感度标记等级

```
绝密(Top Secret) > 机密(Secret) > 可信(Confidential) > 公开(Public)
```

## 二、数据库完整性

### 完整性控制机制功能

```
① 定义约束条件 ② 检查是否违背 ③ 违约处理
```

### 约束定义

```sql
-- 列级约束
CREATE TABLE STUDENT (
  SNO  CHAR(6) PRIMARY KEY,
  SN   CHAR(8) UNIQUE,
  AGE  NUMERIC(2),
  SEX  ENUM('男', '女'),
  DEPT CHAR(10)
);

-- CONSTRAINT 命名子句
CREATE TABLE SC (
  SNO CHAR(9),
  CNO CHAR(4),
  GRADE SMALLINT,
  CONSTRAINT PK_SC PRIMARY KEY (SNO, CNO),
  CONSTRAINT FK_SNO FOREIGN KEY (SNO) REFERENCES Student(SNO),
  CONSTRAINT FK_CNO FOREIGN KEY (CNO) REFERENCES Course(CNO),
  CONSTRAINT CK_GRADE CHECK (GRADE >= 0 AND GRADE <= 100)
);
```

### 触发器

```sql
CREATE TRIGGER <触发器名>
{BEFORE | AFTER} <事件> ON <表名>
FOR EACH {ROW | STATEMENT}
[WHEN <条件>]
<触发动作体>;
```

触发器是由事件驱动的特殊存储过程，服务器自动激活，用于更精细更复杂的完整性控制。

## 三、典型例题

**例题**：在学生选课数据库中有以下两张表：学生表和系别表。若删除系别表中"计算机软件"的信息，会引起什么问题？数据库可采用哪些违约处理策略？

> **答**：学生表中有外码引用了系别表的主码。删除系别后，学生表中的对应学生就成为"孤立"记录。
>
> 违约处理策略：
> 1. **拒绝删除**（NO ACTION / RESTRICT）— 默认，有引用则不允许删除
> 2. **级联删除**（CASCADE）— 自动删除所有引用该系的学生记录
> 3. **置空值**（SET NULL）— 将被删系引用的学生外码置为 NULL
''')

# DB-05
w('DB-05-关系数据理论.md', f'''# DB-05 关系数据理论

## 一、函数依赖

{SVG_FD}

## 二、范式判定

```
范式包含关系：
5NF &#x2282; 4NF &#x2282; BCNF &#x2282; 3NF &#x2282; 2NF &#x2282; 1NF
```

| 范式 | 要求 | 检查重点 |
|------|------|---------|
| **1NF** | 属性不可再分 | 无复合属性 |
| **2NF** | 1NF + 非主属性完全依赖于码 | 检查部分函数依赖 |
| **3NF** | 2NF + 非主属性不传递依赖于码 | 检查传递函数依赖 |
| **BCNF** | 所有决定因素都含码 | 检查所有函数依赖 |

## 三、属性集闭包算法

```
输入：属性集 X，函数依赖集 F
输出：X&#x207A;

result = X
while (result 有变化) {{
  for each (Y &#x2192; Z) in F {{
    if Y &#x2286; result then result = result &#x222A; Z
  }}
}}
return result
```

**例题**：R<U,F>, U=ABCDE, F={{AB&#x2192;C, B&#x2192;D, C&#x2192;E, EC&#x2192;B, AC&#x2192;B}}，求(AB)&#x207A;

```
(AB)&#x207A;
初始：AB
AB&#x2192;C → ABC
B&#x2192;D  → ABCD
C&#x2192;E  → ABCDE
= ABCDE = U  ✓
```

## 四、候选码求解

```
步骤：
① 找出 L 类（只在左边）、R 类（只在右边）、LR 类（两边）、N 类（都不在）
② 候选码必含所有 L+N 类属性
③ 从 L+N 类出发求闭包
④ 若闭包 ≠ U，逐步加入 LR 类属性扩展
```

**例题**：R(U,F), U={{A,B,C,D,E}}, F={{AB&#x2192;C, B&#x2192;D, C&#x2192;E, EC&#x2192;B, AC&#x2192;B}}

```
L类：A     R类：D     LR类：B,C,E
(AB)&#x207A; = ABCDE ✓  (AC)&#x207A; = ACEBD ✓
候选码：AB, AC
主属性：A, B, C
非主属性：D, E

因 B&#x2192;D 存在部分依赖（D部分依赖于码AB），所以最高为 1NF ❌
```

## 五、最小函数依赖集

### 求解步骤

```
① 右部分解为单属性（右边只剩一个属性）
② 去除冗余函数依赖（逐个检查是否多余）
③ 左边化简（左边有多属性时检查能否缩减）
```

**例题**：求 F = {{A&#x2192;BC, E&#x2192;C, D&#x2192;AEF, ABF&#x2192;BD}} 的最小依赖集

```
① 右部分解：
   F = {{A&#x2192;B, A&#x2192;C, E&#x2192;C, D&#x2192;A, D&#x2192;E, D&#x2192;F, ABF&#x2192;B, ABF&#x2192;D}}

② 去除冗余：ABF&#x2192;B 是冗余的（平凡依赖，B&#x2286;ABF）

③ 左边化简：AF&#x2192;D 替代 ABF&#x2192;D（因为 (AF)&#x207A; = {{ABFD}}，AF 即可决定 D）

结果：Fm = {{A&#x2192;B, A&#x2192;C, E&#x2192;C, D&#x2192;A, D&#x2192;E, D&#x2192;F, AF&#x2192;D}}
```

## 六、自编练习题

**题目**：设有关系模式 R(U,F)，U={{ABCDE}}, F={{A&#x2192;BC, CD&#x2192;E, B&#x2192;D}}。求：
(1) 候选码
(2) 最高范式

**验证**：

```
(1) L类：A     R类：E     LR类：B,C,D
(A)&#x207A;：
初始 A
A&#x2192;BC → ABC
B&#x2192;D  → ABCD
CD&#x2192;E → ABCDE = U ✓
候选码：A

(2) 主属性：A    非主属性：B,C,D,E
非主属性是否完全依赖于A？A&#x2192;BC 完全，B&#x2192;D 传递（A&#x2192;B, B&#x2192;D），CD&#x2192;E 完全
检查 2NF：B, C, D, E 均由 A 决定，无部分依赖 ✓
检查 3NF：B&#x2192;D  存在传递依赖 A&#x2192;B, B&#x2192;D → D 传递依赖于 A ✗
最高范式：2NF ✅
```
''')

# DB-06
w('DB-06-数据库设计.md', '''# DB-06 数据库设计

## 一、设计阶段

```
需求分析 → 概念结构设计 → 逻辑结构设计 → 物理设计 → 实施 → 运行维护
```

| 阶段 | 产出 | 独立于DBMS？ |
|------|------|-------------|
| 需求分析 | 需求说明书、数据字典 | 是 |
| 概念结构设计 | E-R 图 | 是 |
| 逻辑结构设计 | 关系模式 | 否（需考虑DBMS） |
| 物理设计 | 存储结构、索引 | 否 |

## 二、E-R 图转关系模式

```
① 每个实体 → 一个关系模式（实体的属性=关系属性，实体的码=关系的码）
② 1:n 联系 → 1端主码加入n端作为外码
③ 1:1 联系 → 任选一端主码加入另一端
④ m:n 联系 → 独立关系模式，码=两端码组合
⑤ 多元联系 → 独立关系模式，码=各实体码组合
```

## 三、数据字典包括

```
数据项、数据结构、数据流、数据存储、处理过程
```

## 四、典型例题

**例题**：E-R 图向关系模型转换

```
仓库（仓库号，面积，电话）
零件（零件号，名称，规格，单价）
供应商（供应商号，姓名，地址，电话）
项目（项目号，预算，开工日期）
职工（职工号，姓名，年龄，职称）

联系：
- 仓库1:n存放零件（库存量属性），m:n存放在关系→库存（仓库号，零件号，库存量）
- 仓库1:n有职工 → 职工关系中加外码 仓库号
- 供应商m:n供应m:n项目→供应（供应商号，项目号，零件号，供应量）
- 职工间1:n领导关系（自联系）→ 职工表中加 领导职工号 外码
```

> 转换结果的关系模式：
> ```
> 仓库(仓库号, 面积, 电话)
> 零件(零件号, 名称, 规格, 单价)
> 供应商(供应商号, 姓名, 地址, 电话)
> 项目(项目号, 预算, 开工日期)
> 职工(职工号, 姓名, 年龄, 职称, 仓库号, 领导职工号)
> 库存(仓库号, 零件号, 库存量)
> 供应(供应商号, 项目号, 零件号, 供应量)
> ```
''')

print("数据库笔记生成完毕！")
