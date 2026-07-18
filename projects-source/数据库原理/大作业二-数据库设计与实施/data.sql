CREATE DATABASE IF NOT EXISTS test1; 
USE test1;
CREATE TABLE Student          
       (Sno       Varchar(9) PRIMARY KEY,                            
        Sname  Varchar(20) UNIQUE,             
        Ssex      Enum('F','M'),  
        Sage     Smallint,
        Sdept    Varchar(20)
        );


CREATE TABLE Course
       (Cno       Varchar(4) PRIMARY KEY,
        Cname  Varchar(40),            
        Cpno     Varchar(4) ,              	                      
        Ccredit  Enum('1','2','3','4','5'),
        FOREIGN KEY (Cpno) REFERENCES Course(Cno) 
        );



CREATE TABLE  SC
       (Sno      Varchar(9), 
        Cno      Varchar(4),  
        Grade   Smallint,
        PRIMARY KEY (Sno,Cno),    
        FOREIGN KEY (Sno) REFERENCES Student(Sno),  
        FOREIGN KEY (Cno) REFERENCES Course(Cno)
       );


CREATE TABLE Teacher          
      (Tno       Varchar(6) PRIMARY KEY,           
       Tname  Varchar(20),            
       Tsex      Enum('F','M'),
       Tage     Smallint,
       Tdept    Varchar(20),
       Ttitles   Varchar(20),
       Twage  Int,
       Tdno    Varchar(6),
       FOREIGN KEY (Tdno) REFERENCES  Teacher(Tno)
       );


INSERT INTO Course(Cno,Cname,Cpno,Ccredit)
VALUES('1','Database',NULL,4);
INSERT INTO Course(Cno,Cname,Cpno,Ccredit)
VALUES('2','Math',NULL,2);
INSERT INTO Course(Cno,Cname,Cpno,Ccredit)
VALUES('3','Information System',NULL,4);
INSERT INTO Course(Cno,Cname,Cpno,Ccredit)
VALUES('4','Operating System',NULL,3);
INSERT INTO Course(Cno,Cname,Cpno,Ccredit)
VALUES('5','Data Structure',NULL,4);
INSERT INTO Course(Cno,Cname,Cpno,Ccredit)
VALUES('6','Data Processing',NULL,2);
INSERT INTO Course(Cno,Cname,Cpno,Ccredit)
VALUES('7','PASCAL',NULL,4);
INSERT INTO Course(Cno,Cname,Cpno,Ccredit)
VALUES('8','DB_Design',NULL,2);

SET SQL_SAFE_UPDATES = 0;
UPDATE Course SET Cpno='5' WHERE Cno='1';
UPDATE Course SET Cpno='1' WHERE Cno='3';
UPDATE Course SET Cpno='6' WHERE Cno='4';
UPDATE Course SET Cpno='7' WHERE Cno='5';
UPDATE Course SET Cpno='6' WHERE Cno='7';
UPDATE Course SET Cpno='1' WHERE Cno='8';

INSERT INTO Student(Sno,Sname,Ssex,Sage,Sdept)
VALUES('202015121','LiYong','M',20,'CS');
INSERT INTO Student(Sno,Sname,Ssex,Sage,Sdept)
VALUES('202015122','liuChen','F',19,'CS');
INSERT INTO Student(Sno,Sname,Ssex,Sage,Sdept)
VALUES('202015123','WangMing','F',18,'MA');
INSERT INTO Student(Sno,Sname,Ssex,Sage,Sdept)
VALUES('202015124','ChenXi','M',20,'MA');
INSERT INTO Student(Sno,Sname,Ssex,Sage,Sdept)
VALUES('202015125','ZhangLi','M',19,'IS');
INSERT INTO Student(Sno,Sname,Ssex,Sage,Sdept)
VALUES('202015126','OuyangLi','F',21,'FL');

INSERT INTO SC(Sno,Cno,Grade)VALUES('202015121','1',92);
INSERT INTO SC(Sno,Cno,Grade)VALUES('202015121','2',85);
INSERT INTO SC(Sno,Cno,Grade)VALUES('202015121','3',88);
INSERT INTO SC(Sno,Cno,Grade)VALUES('202015122','2',90);
INSERT INTO SC(Sno,Cno,Grade)VALUES('202015122','3',80);
INSERT INTO SC(Sno,Cno,Grade)VALUES('202015122','1',NULL);
INSERT INTO SC(Sno,Cno,Grade)VALUES('202015123','2',50);
INSERT INTO SC(Sno,Cno,Grade)VALUES('202015123','3',70);



INSERT INTO Teacher(Tno,Tname,Tsex,Tage,Tdept,Ttitles,Twage,Tdno)
VALUES('110001','ZhongLin','F',27,'CS','Lecturer',2800,NULL);
INSERT INTO Teacher(Tno,Tname,Tsex,Tage,Tdept,Ttitles,Twage,Tdno)
VALUES('110002','YangYi','M',42,'CS','Associate Professor',3500,NULL);
INSERT INTO Teacher(Tno,Tname,Tsex,Tage,Tdept,Ttitles,Twage,Tdno)
VALUES('110003','ZhouQian','F',25,'CS','Lecturer',2800,NULL);
INSERT INTO Teacher(Tno,Tname,Tsex,Tage,Tdept,Ttitles,Twage,Tdno)
VALUES('110005','ChenWenmao','M',48,'CS','Professor',4000,NULL);
INSERT INTO Teacher(Tno,Tname,Tsex,Tage,Tdept,Ttitles,Twage,Tdno)
VALUES('120001','JiangNan','M',30,'IS','Associate Professor',3500,NULL);
INSERT INTO Teacher(Tno,Tname,Tsex,Tage,Tdept,Ttitles,Twage,Tdno)
VALUES('120002','LiuYang','M',28,'IS','Lecturer',2800,NULL);
INSERT INTO Teacher(Tno,Tname,Tsex,Tage,Tdept,Ttitles,Twage,Tdno)
VALUES('120003','WangMing','M',44,'IS','Professor',4000,NULL);
INSERT INTO Teacher(Tno,Tname,Tsex,Tage,Tdept,Ttitles,Twage,Tdno)
VALUES('120004','ZhangLei','F',35,'IS','Associate Professor',3500,NULL);
INSERT INTO Teacher(Tno,Tname,Tsex,Tage,Tdept,Ttitles,Twage,Tdno)
VALUES('130001','ZhouJiayu','F',25,'MA','Lecturer',2800,NULL);
INSERT INTO Teacher(Tno,Tname,Tsex,Tage,Tdept,Ttitles,Twage,Tdno)
VALUES('130002','WangLi','M',30,'MA','Lecturer',2800,NULL);
INSERT INTO Teacher(Tno,Tname,Tsex,Tage,Tdept,Ttitles,Twage,Tdno)
VALUES('130003','WangXiaofeng','M',35,'MA','Associate Professor',3500,NULL);
INSERT INTO Teacher(Tno,Tname,Tsex,Tage,Tdept,Ttitles,Twage,Tdno)
VALUES('130004','WeiZhao','M',40,'MA','Associate Professor',3500,NULL);
INSERT INTO Teacher(Tno,Tname,Tsex,Tage,Tdept,Ttitles,Twage,Tdno)
VALUES('140001','Wangli','M',32,'FL','Associate Professor',3500,NULL);
INSERT INTO Teacher(Tno,Tname,Tsex,Tage,Tdept,Ttitles,Twage,Tdno)
VALUES('140002','ZhangXiaomei','F',27,'FL','Lecturer',2800,NULL);
INSERT INTO Teacher(Tno,Tname,Tsex,Tage,Tdept,Ttitles,Twage,Tdno)
VALUES('140003','WuYa','F',27,'FL','Lecturer',2800,NULL);
INSERT INTO Teacher(Tno,Tname,Tsex,Tage,Tdept,Ttitles,Twage,Tdno)
VALUES('140004','ChenShu','F',35,'FL','Associate Professor',3500,NULL);
INSERT INTO Teacher(Tno,Tname,Tsex,Tage,Tdept,Ttitles,Twage,Tdno)
VALUES('140005','ZhouBing','M',44,'FL','Professor',4000,NULL);



UPDATE Teacher SET Tdno='110005' WHERE Tdept='CS';

UPDATE Teacher SET Tdno='120003' WHERE Tdept='IS';

UPDATE Teacher SET Tdno='130003' WHERE Tdept='MA';

UPDATE Teacher SET Tdno='140005' WHERE Tdept='FL';






















