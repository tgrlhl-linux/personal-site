#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vercel Serverless 入口 — Flask 成绩管理系统

SQLite 在 Vercel 无服务器环境中为临时存储，冷启动时自动重建 demo 数据。
"""
import sys, os, sqlite3

# 确保能找到父目录的模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models import DB_PATH

def seed_demo_data():
    """创建数据库与 demo 数据（不依赖 CSV 文件）"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()

    # 建表
    c.executescript('''
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            college TEXT, department TEXT
        );
        CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            class_id INTEGER REFERENCES classes(id)
        );
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            credit REAL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT REFERENCES students(id),
            subject_id INTEGER REFERENCES subjects(id),
            raw_score TEXT, numeric_score REAL,
            UNIQUE(student_id, subject_id)
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin','teacher','student')),
            scope TEXT DEFAULT '*'
        );
    ''')

    # Demo 数据
    classes = [('计科1801','信息科学与工程学院','计算机科学系'),
               ('计科1802','信息科学与工程学院','计算机科学系'),
               ('软件1801','信息科学与工程学院','软件工程系'),
               ('软件1802','信息科学与工程学院','软件工程系')]
    class_ids = {}
    for name, col, dept in classes:
        c.execute('INSERT OR IGNORE INTO classes (name,college,department) VALUES (?,?,?)', (name,col,dept))
    for row in c.execute('SELECT id,name FROM classes'):
        class_ids[row[1]] = row[0]

    subjects = [('高等数学[5]',5), ('线性代数[3]',3), ('C语言程序设计[4]',4),
                ('数据结构[4]',4), ('操作系统[3]',3), ('数据库原理[3]',3)]
    subj_ids = {}
    for name, cred in subjects:
        c.execute('INSERT OR IGNORE INTO subjects (name,credit) VALUES (?,?)', (name,cred))
    for row in c.execute('SELECT id,name FROM subjects'):
        subj_ids[row[1]] = row[0]

    students = [
        ('2018182801','张三','计科1801'), ('2018182802','李四','计科1801'),
        ('2018182803','王五','计科1802'), ('2018182804','赵六','软件1801'),
        ('2018182805','钱七','软件1802'),
    ]
    for sid, name, cls in students:
        c.execute('INSERT OR IGNORE INTO students (id,name,class_id) VALUES (?,?,?)',
                  (sid, name, class_ids.get(cls)))

    import random
    random.seed(42)
    for sid, _, _ in students:
        for subj_id in subj_ids.values():
            score = round(random.uniform(55, 100), 1)
            c.execute('INSERT OR IGNORE INTO scores (student_id,subject_id,raw_score,numeric_score) VALUES (?,?,?,?)',
                      (sid, subj_id, str(score), score))

    users = [('admin','admin123','admin','*'),
             ('zhanglao','123456','teacher','计科1801,计科1802'),
             ('wanglao','123456','teacher','软件1801,软件1802'),
             ('2018182801','123456','student','2018182801')]
    for u, p, r, s in users:
        c.execute('INSERT OR IGNORE INTO users (username,password,role,scope) VALUES (?,?,?,?)', (u,p,r,s))

    conn.commit()
    conn.close()
    print("[INFO] Demo 数据库已初始化 — 5名学生 × 6门课")

if not os.path.exists(DB_PATH):
    print("[INFO] 首次部署，创建 demo 数据库...")
    seed_demo_data()

from app import app as application

# Vercel 要求导出名为 app
app = application
