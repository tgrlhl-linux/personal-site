#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sqlite3
import os
import re

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'scores.db')
CSV_PATH = os.path.join(os.path.dirname(__file__), '作业六题目一数据.csv')

CLASS_MAP = {
    '0': '计科1801', '1': '计科1801',
    '2': '计科1802', '3': '计科1802',
    '4': '软件1801', '5': '软件1801',
    '6': '软件1802', '7': '软件1802',
    '8': '网工1801', '9': '人工1801',
}

COLLEGE_DEPT = {
    '计科1801': ('信息科学与工程学院', '计算机科学系'),
    '计科1802': ('信息科学与工程学院', '计算机科学系'),
    '软件1801': ('信息科学与工程学院', '软件工程系'),
    '软件1802': ('信息科学与工程学院', '软件工程系'),
    '网工1801': ('信息科学与工程学院', '网络工程系'),
    '人工1801': ('信息科学与工程学院', '人工智能系'),
}

def grade_to_numeric(raw):
    if raw is None:
        return None
    raw = str(raw).strip()
    if not raw:
        return None
    mapping = {
        '优秀': 95, '优': 95,
        '良好': 85, '良': 85,
        '中等': 75, '中': 75,
        '及格': 65, '及': 65,
        '不及格': 55,
    }
    if raw in mapping:
        return mapping[raw]
    m = re.search(r'(\d+(?:\.\d+)?)', raw)
    if m:
        return float(m.group(1))
    return None

def extract_credit(subject_name):
    m = re.search(r'\[([\d.]+)\]', subject_name)
    if m:
        return float(m.group(1))
    return 0

def get_class_for_student(sid):
    last = str(sid)[-1] if sid else '0'
    return CLASS_MAP.get(last, '未分配')

def init_database():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            college TEXT,
            department TEXT
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
            raw_score TEXT,
            numeric_score REAL,
            UNIQUE(student_id, subject_id)
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'teacher', 'student')),
            scope TEXT DEFAULT '*'
                -- 数据范围: * 全部 | class1,class2 老师管辖班级 | 学号 学生本人
        );
    ''')
    class_id_map = {}
    for cls_name, (college, dept) in COLLEGE_DEPT.items():
        c.execute('INSERT OR IGNORE INTO classes (name, college, department) VALUES (?, ?, ?)',
                  (cls_name, college, dept))
    for row in c.execute('SELECT id, name FROM classes'):
        class_id_map[row[1]] = row[0]
    default_users = [
        ('admin', 'admin123', 'admin', '*'),
        ('zhanglao', '123456', 'teacher', '计科1801,计科1802'),
        ('wanglao', '123456', 'teacher', '软件1801,软件1802'),
    ]
    for u, p, r, s in default_users:
        c.execute('INSERT OR IGNORE INTO users (username, password, role, scope) VALUES (?, ?, ?, ?)', (u, p, r, s))
    if not os.path.exists(CSV_PATH):
        print(f'[ERROR] CSV not found: {CSV_PATH}')
        conn.close()
        return False
    with open(CSV_PATH, 'r', encoding='gbk') as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    if not lines:
        print('[ERROR] CSV is empty')
        conn.close()
        return False
    header = lines[0]
    columns = header.split(',')
    print(f'[INFO] CSV columns: {len(columns)}, rows: {len(lines)-1}')
    subject_cols = columns[5:]
    for col in subject_cols:
        col = col.strip().strip('\r')
        credit = extract_credit(col)
        c.execute('INSERT OR IGNORE INTO subjects (name, credit) VALUES (?, ?)', (col, credit))
    subject_ids = {}
    for row in c.execute('SELECT id, name FROM subjects'):
        subject_ids[row[1]] = row[0]
    import_count = 0
    for line in lines[1:]:
        vals = line.split(',')
        if len(vals) < 5:
            continue
        sid = vals[0].strip()
        sname = vals[1].strip()
        if not sid or not sname:
            continue
        cls_name = get_class_for_student(sid)
        cls_id = class_id_map.get(cls_name, None)
        c.execute('INSERT OR IGNORE INTO students (id, name, class_id) VALUES (?, ?, ?)',
                  (sid, sname, cls_id))
        for idx, col_name in enumerate(subject_cols):
            col_name = col_name.strip().strip('\r')
            if idx + 5 < len(vals):
                raw = vals[idx + 5].strip()
                if raw:
                    numeric = grade_to_numeric(raw)
                    subj_id = subject_ids.get(col_name)
                    if subj_id:
                        c.execute('INSERT OR REPLACE INTO scores (student_id, subject_id, raw_score, numeric_score) VALUES (?, ?, ?, ?)',
                                  (sid, subj_id, raw, numeric))
        import_count += 1
    conn.commit()
    conn.close()
    print(f'[DONE] Imported {import_count} students')
    return True

if __name__ == '__main__':
    init_database()
