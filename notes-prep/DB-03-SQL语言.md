# DB-03 SQL语言

## 一、SQL概述

SQL（Structured Query Language）是关系数据库的标准语言。它集数据定义、数据操纵、数据查询和数据控制功能于一体，是一种"全功能"的数据库语言。SQL语言非常简洁——核心命令只有九个单词（SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, GRANT, REVOKE），但能完成几乎所有数据库操作。

## 二、数据定义（DDL）

### 2.1 基本表的操作

创建表时需要指定表名、列名、数据类型和完整性约束。

```sql
CREATE TABLE Student (
    Sno   CHAR(6) PRIMARY KEY,
    Sname CHAR(8) NOT NULL,
    Sage  INT,
    Ssex  ENUM('F', 'M'),
    Sdept CHAR(10),
    FOREIGN KEY (Sdept) REFERENCES Dept(Dno)
);
```

这段DDL语句创建了一个"学生表"，其中Sno是主码（实体完整性），Sname不能为空（用户定义完整性），Sdept是外码引用Dept表（参照完整性）。

修改表结构和删除表：
```sql
ALTER TABLE Student ADD COLUMN Email VARCHAR(50);
ALTER TABLE Student DROP COLUMN Email;
ALTER TABLE Student MODIFY COLUMN Sage SMALLINT;
DROP TABLE Student;
```

### 2.2 索引

索引是加快数据检索速度的重要手段。它可以建立在表的一列或多列上。

```sql
CREATE UNIQUE INDEX idx_sno ON Student(Sno);
CREATE INDEX idx_dept ON Student(Sdept);
DROP INDEX idx_sno ON Student;
```

UNIQUE索引要求被索引的列的值不能重复，这与主码约束类似。索引虽然能加速查询，但会降低更新操作的速度（因为每次更新都需要同步修改索引），所以索引并非越多越好。

## 三、数据查询（DQL）

查询是SQL中使用最频繁的操作，其基本结构为SELECT-FROM-WHERE。

### 3.1 单表查询

```sql
-- 查询所有列
SELECT * FROM Student;

-- 查询指定列
SELECT Sname, Sage FROM Student;

-- 带条件查询
SELECT Sname FROM Student WHERE Sdept = 'CS' AND Sage < 20;

-- 排序
SELECT Sno, Grade FROM SC WHERE Cno = '3' ORDER BY Grade DESC;

-- 用别名
SELECT Sname AS 姓名, Sage AS 年龄 FROM Student;

-- 消除重复
SELECT DISTINCT Sdept FROM Student;
```

### 3.2 聚集函数与分组

SQL提供了五个常用的聚集函数：COUNT（计数）、SUM（求和）、AVG（平均值）、MAX（最大值）、MIN（最小值）。它们通常与GROUP BY子句配合使用。

```sql
-- 统计学生总人数
SELECT COUNT(*) FROM Student;

-- 统计各课程的平均分
SELECT Cno, AVG(Grade) FROM SC GROUP BY Cno;

-- HAVING对分组结果进行筛选
SELECT Sno FROM SC
GROUP BY Sno
HAVING COUNT(*) > 2;
```

这里有一个容易混淆的地方：**WHERE子句用于分组前筛选行，HAVING子句用于分组后筛选组**。WHERE在GROUP BY之前执行，HAVING在GROUP BY之后执行。

### 3.3 连接查询

连接查询是SQL中最重要也是最常用的操作。当查询需要从多个表中获取数据时，就需要使用连接。

```sql
-- 内连接（等值连接）
SELECT Student.Sno, Sname, Cno, Grade
FROM Student, SC
WHERE Student.Sno = SC.Sno;

-- 复合条件连接
SELECT Student.Sno, Sname
FROM Student, SC
WHERE Student.Sno = SC.Sno
  AND SC.Cno = '2'
  AND SC.Grade > 90;
```

### 3.4 嵌套查询

嵌套查询是指一个SELECT语句中内嵌了另一个SELECT语句。内层查询的结果作为外层查询的条件。

```sql
-- IN子查询：找出与"刘晨"同系的学生
SELECT Sno, Sname, Sdept
FROM Student
WHERE Sdept IN (
    SELECT Sdept FROM Student WHERE Sname = '刘晨'
);

-- EXISTS子查询：找出选修了1号课程的学生
SELECT Sname FROM Student
WHERE EXISTS (
    SELECT * FROM SC
    WHERE SC.Sno = Student.Sno AND Cno = '1'
);
```

EXISTS和NOT EXISTS用于测试子查询的结果是否为空。它们通常比IN更灵活，可以实现"全称量词"的操作（如"找出选修了所有课程的学生"）。

## 四、数据更新（DML）

```sql
-- 插入
INSERT INTO Student VALUES ('95020', '陈冬', '男', 'IS', 18);

-- 更新（将所有学生年龄加1）
UPDATE Student SET Sage = Sage + 1;

-- 带子查询的更新
UPDATE SC SET Grade = 0
WHERE Sno IN (SELECT Sno FROM Student WHERE Sdept = 'CS');

-- 删除
DELETE FROM SC WHERE Cno = '2';
```

## 五、视图

视图是从一个或多个基本表中导出的虚表。视图不存储实际数据，只保存了定义。对视图的查询会在执行时实时转换为对基本表的查询。视图的主要作用是：简化查询（将复杂的查询定义为视图）、提供安全保护（只暴露需要的数据）和维护数据独立性。

```sql
CREATE VIEW IS_Student AS
SELECT Sno, Sname, Sage FROM Student WHERE Sdept = 'IS';

DROP VIEW IS_Student;
```

视图的可更新性有限制：包含聚集函数、DISTINCT、GROUP BY、多表连接的视图通常不能更新。

## 六、授权控制

```sql
GRANT SELECT ON TABLE Student TO U1;
GRANT ALL PRIVILEGES ON TABLE Student TO U2 WITH GRANT OPTION;
REVOKE SELECT ON TABLE Student FROM U1;
```

WITH GRANT OPTION允许用户将获得的权限再授予其他用户。
