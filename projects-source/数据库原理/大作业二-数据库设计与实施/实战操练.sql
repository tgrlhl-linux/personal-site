DROP DATABASE IF EXISTS sql_practice;
CREATE DATABASE sql_practice;
USE sql_practice;


CREATE TABLE Student (
    Sno VARCHAR(9) PRIMARY KEY,
    Sname VARCHAR(20),
    Ssex ENUM('F','M'),
    Sage SMALLINT,
    Sdept VARCHAR(20)
);


CREATE TABLE Course (
    Cno VARCHAR(4) PRIMARY KEY,
    Cname VARCHAR(40),
    Cpno VARCHAR(4),
    Ccredit INT
);


CREATE TABLE SC (
    Sno VARCHAR(9),
    Cno VARCHAR(4),
    Grade INT,
    PRIMARY KEY (Sno, Cno),
    FOREIGN KEY (Sno) REFERENCES Student(Sno),
    FOREIGN KEY (Cno) REFERENCES Course(Cno)
);


CREATE TABLE Teacher (
    Tno VARCHAR(6) PRIMARY KEY,
    Tname VARCHAR(20),
    Tsex ENUM('F','M'),
    Tage INT,
    Tdept VARCHAR(20),
    Ttitles VARCHAR(30),
    Twage INT,
    Tdno VARCHAR(6)
);

INSERT INTO Student VALUES
('202015121','LiYong','M',20,'CS'),
('202015122','LiuChen','F',19,'CS'),
('202015123','WangMing','F',18,'MA'),
('202015124','ChenXi','M',19,'MA'),
('202015125','ZhangLi','M',21,'IS'),
('202015126','OuyangLi','F',21,'FL');


INSERT INTO Course VALUES
('1','Database',NULL,4),
('2','Math',NULL,2),
('3','Information System','1',3),
('4','Operating System','5',4),
('5','Data Structure','6',4),
('6','PASCAL',NULL,4),
('7','Data Processing','2',2),
('8','DB_Design','7',2);


ALTER TABLE Course
ADD CONSTRAINT fk_course_cpno
FOREIGN KEY (Cpno) REFERENCES Course(Cno);

INSERT INTO SC VALUES
('202015121','1',92),
('202015121','2',85),
('202015121','3',88),
('202015122','1',NULL),
('202015122','2',90),
('202015122','3',80),
('202015123','2',50),
('202015123','3',70);


INSERT INTO Teacher VALUES
('110001','ZhongLin','F',27,'CS','Lecturer',2800,'110005'),
('110002','YangYi','M',42,'CS','Associate Professor',3500,'110005'),
('110003','ZhouQian','F',25,'CS','Lecturer',2800,'110005'),
('110005','ChenWenmao','M',40,'CS','Professor',4000,'110005'),
('120001','JiangNan','M',30,'IS','Associate Professor',3500,'120003'),
('120003','WangXiaofeng','M',41,'IS','Professor',4000,'120003'),
('120004','ZhangLei','F',35,'IS','Associate Professor',3500,'120003'),
('130001','ZhouJiayu','F',25,'MA','Lecturer',2800,'130003'),
('130003','WangMing','M',36,'MA','Professor',3500,'130003'),
('130004','WeiZhao','M',40,'MA','Associate Professor',3500,'130003'),
('140001','Wangli','M',32,'FL','Associate Professor',3500,'140005'),
('140002','ZhangXiaomei','F',27,'FL','Lecturer',2800,'140005'),
('140003','WuYa','F',27,'FL','Lecturer',2800,'140005'),
('140004','ChenShu','F',35,'FL','Associate Professor',3500,'140005'),
('140005','ZhouBing','M',44,'FL','Professor',4000,'140005');

-- 1.查询全体学生的姓名、性别、所在系。
SELECT Sname, Ssex, Sdept FROM student;

-- 2.查询该校所有不重复的系名。
SELECT DISTINCT Sdept FROM student;

-- 3.查询 CS 系男生的学号和姓名。
SELECT Sno,Sname FROM student WHERE Sdept = 'CS' AND Ssex = 'M';

-- 4.查询姓名以 Li 开头的学生。
SELECT * FROM student WHERE Sname LIKE 'Li%';

-- 5.查询成绩为空（缺考）的选课记录。
SELECT * FROM sc WHERE Grade IS NULL;

-- 6.查询年龄在 18~20 岁之间的学生姓名和年龄。
SELECT Sname, Sage FROM Student WHERE Sage BETWEEN 18 AND 20;

-- 7. 查询所在系为 IS 或 MA 的学生信息。
SELECT * FROM Student WHERE Sdept IN ('IS','MA');

-- 8. 查询所有课程，按学分降序排序。
SELECT * FROM course ORDER BY Ccredit DESC;

-- 9. 统计学生总人数、选课记录总数。
SELECT COUNT(*) AS 总人数 FROM Student;
SELECT COUNT(*) AS 选课记录总数 FROM SC;

-- 10. 统计每门课的选修人数和平均分。
SELECT Cno,COUNT(*) AS 人数, AVG(Grade) AS 平均分 FROM sc GROUP BY Cno;

-- 11. 统计每个学生的选课数和总成绩。
SELECT Sno,COUNT(*) AS 选课数, SUM(Grade) AS 总成绩 FROM SC GROUP BY Sno;

-- 12. 查询平均分大于 80 分的学生学号和平均分
SELECT Sno ,AVG(Grade) FROM SC GROUP BY Sno HAVING AVG(Grade)>80 ;

-- 13. 查询所有学生的姓名、课程号、成绩（只显示有选课的）。
SELECT student.Sname,sc.Cno,sc.Grade
FROM student
JOIN sc on student.sno=sc.sno;

-- 14. 查询所有学生的姓名、课程名、成绩（显示所有学生，包括没选课的）。
SELECT student.Sname,course.Cname,sc.Grade
FROM student
LEFT JOIN sc on student.sno=sc.sno
LEFT JOIN course on sc.cno=course.cno;

-- 15. 查询选修了 “Database” 课程的学生姓名和成绩。
SELECT student.Sname,sc.Grade
FROM student
LEFT JOIN sc ON student.sno=sc.sno
LEFT JOIN course ON course.cno=sc.cno
WHERE Cname="Database";

-- 16. 查询每个学生的总学分（没选课的显示 0）。
SELECT student.sno ,IFNULL(SUM(Ccredit),0) AS 总学分
FROM Student 
LEFT JOIN sc ON sc.sno=student.sno
LEFT JOIN course ON course.cno=sc.cno
GROUP BY student.sno;

-- 17. 查询和 LiuChen 同系的所有学生。
SELECT * FROM student
WHERE Sdept=(SELECT Sdept FROM student WHERE Sname='LiuChen');

-- 18. 查询没有选修任何课程的学生姓名。
SELECT Sname FROM student
WHERE Sno NOT IN(SELECT sno FROM sc);

-- 19. 查询选修了课程号为 1 且成绩高于该课程平均分的学生学号和成绩。
SELECT Sno,Grade FROM SC
WHERE Grade > (SELECT AVG(Grade) FROM SC WHERE Cno='1') 
AND Cno='1';

-- 20.创建一个视图 cs_student_view，包含 CS 系学生的学号、姓名、年龄，并查询这个视图。
CREATE VIEW  cs_student_view AS
SELECT Sno,Sname,Sage FROM Student WHERE Sdept='CS';

SELECT * FROM cs_student_view;

-- 一、基础单表（5 题）
-- 查询所有男学生（Ssex='M'）的姓名、年龄。
 SELECT Sname,Sage FROM Student WHERE Ssex='M'; 
-- 查询年龄大于 19 的女学生。
SELECT * FROM Student WHERE Sage > 19 AND Ssex='F';
-- 查询工资在 3000~4000 的教师。
SELECT * FROM Teacher WHERE Twage between 3000 AND 4000;
-- 查询课程名包含 'System' 的课程。
SELECT * FROM course WHERE Cname LIKE '%System%';
-- 查询没有先行课（Cpno 为空）的课程。
SELECT * FROM course WHERE Cpno IS NULL;

-- 二、分组聚合（5 题）
-- 统计每个系（Sdept）的女生人数。
SELECT Sdept,COUNT(*)
FROM student
WHERE Ssex='F'
group by Sdept;
-- 统计每门课的最高分、最低分。
SELECT Cno,MAX(GRADE),MIN(GRADE)
FROM sc
group by Cno;
-- 统计选课人数少于 3 的课程号。
SELECT Cno,COUNT(*)
FROM SC
GROUP BY Cno
HAVING COUNT(*)<3;
-- 统计 CS 系学生的平均年龄。
SELECT AVG(Sage) AS 平均年龄
FROM student
WHERE Sdept ='CS';
-- 统计总成绩大于 150 的学生学号。
SELECT Sno,SUM(GRADE)
FROM sc
GROUP BY Sno
HAVING SUM(GRADE)>150;

-- 三、多表连接（4 题）
-- 查询 CS 系学生的姓名、课程名、成绩。
SELECT sc.Grade,student.Sname,course.Cname
FROM student
JOIN sc ON student.Sno=sc.Sno
JOIN course ON course.Cno=sc.Cno
WHERE Sdept='CS';
-- 查询所有教师姓名、所在系、系主任姓名。(教师表自连接)
SELECT 
  t1.Tname AS 教师姓名,
  t1.Tdept AS 所在系,
  t2.Tname AS 系主任姓名
FROM Teacher t1
JOIN Teacher t2 
  ON t1.Tdno = t2.Tno;
-- 查询选修了 2 号课程且不及格的学生姓名。
SELECT Sname
FROM student 
JOIN sc ON sc.Sno=student.sno
WHERE Cno=2 AND Grade<60;
-- 查询没选任何课的学生姓名、所在系。
SELECT Sname, Sdept
FROM Student
LEFT JOIN SC ON Student.Sno = SC.Sno
WHERE SC.Sno IS NULL;

-- 四、子查询（3 题）
-- 查询年龄比 WangMing 大的学生。
SELECT *
FROM Student
WHERE Sage > (SELECT Sage FROM Student WHERE Sname='WangMing');
-- 查询和 ZhangLi 选课完全一样的学生学号。
SELECT Sno
FROM SC
WHERE Sno != (SELECT Sno FROM Student WHERE Sname='ZhangLi')
GROUP BY Sno
HAVING GROUP_CONCAT(Cno) = (
    SELECT GROUP_CONCAT(Cno)
    FROM SC
    WHERE Sno = (SELECT Sno FROM Student WHERE Sname='ZhangLi')
);
-- 查询平均工资最高的系名。
SELECT Tdept
FROM Teacher
GROUP BY Tdept
ORDER BY AVG(Twage) DESC
LIMIT 1;
-- 五、视图 + 小综合（2 题）
-- 创建不及格成绩视图（成绩 < 60），查询视图。
CREATE VIEW V_BuJiGe AS
SELECT * 
FROM SC
WHERE Grade < 60;
SELECT * FROM V_BuJiGe;
-- 查询每门课不及格人数，按人数降序。
SELECT Cno, COUNT(*) AS 不及格人数
FROM SC
WHERE Grade < 60
GROUP BY Cno
ORDER BY 不及格人数 DESC;