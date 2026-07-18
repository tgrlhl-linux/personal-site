#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sqlite3
import os
import re

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'scores.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

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

def get_student_stats(db, student_id):
    cur = db.execute('''
        SELECT COUNT(*), SUM(s.numeric_score), AVG(s.numeric_score)
        FROM scores s
        WHERE s.student_id = ? AND s.numeric_score IS NOT NULL
    ''', (student_id,))
    row = cur.fetchone()
    count = row[0] or 0
    total = round(row[1] or 0, 2)
    avg = round(row[2] or 0, 2) if count > 0 else 0
    return total, avg, count

def get_gpa(db, student_id):
    cur = db.execute('''
        SELECT SUM(s.numeric_score * sub.credit) as weighted_sum,
               SUM(sub.credit) as total_credit
        FROM scores s
        JOIN subjects sub ON s.subject_id = sub.id
        WHERE s.student_id = ? AND s.numeric_score IS NOT NULL AND sub.credit > 0
    ''', (student_id,))
    row = cur.fetchone()
    ws = row[0] or 0
    tc = row[1] or 0
    if tc > 0:
        return round(ws / tc, 2), round(tc, 1)
    return 0, 0

def get_all_students(db, page=1, per_page=20, search='', class_id=None, role='admin', scope='*'):
    conditions = []
    params = []
    if search:
        conditions.append('(s.id LIKE ? OR s.name LIKE ?)')
        params.extend([f'%{search}%', f'%{search}%'])
    if class_id:
        conditions.append('s.class_id = ?')
        params.append(class_id)
    # 用户数据隔离
    scope_sql, scope_params = get_scope_filter_sql(role, scope, 's')
    if scope_sql:
        conditions.append(scope_sql[4:])  # 去掉开头的 AND
        params.extend(scope_params)
    where = 'WHERE ' + ' AND '.join(conditions) if conditions else ''
    total = db.execute(f'SELECT COUNT(*) FROM students s {where}', params).fetchone()[0]
    offset = (page - 1) * per_page
    students = db.execute(f'''
        SELECT s.id, s.name, c.name as class_name
        FROM students s
        LEFT JOIN classes c ON s.class_id = c.id
        {where}
        ORDER BY s.id
        LIMIT ? OFFSET ?
    ''', params + [per_page, offset]).fetchall()
    return students, total, page, (total + per_page - 1) // per_page

def get_student_detail(db, student_id):
    student = db.execute('''
        SELECT s.id, s.name, c.name as class_name, c.college, c.department
        FROM students s
        LEFT JOIN classes c ON s.class_id = c.id
        WHERE s.id = ?
    ''', (student_id,)).fetchone()
    if not student:
        return None, []
    scores = db.execute('''
        SELECT sub.id, sub.name, sub.credit, sc.raw_score, sc.numeric_score
        FROM subjects sub
        LEFT JOIN scores sc ON sc.subject_id = sub.id AND sc.student_id = ?
        ORDER BY sub.id
    ''', (student_id,)).fetchall()
    return student, scores

# ---------- 用户数据隔离 ----------
def get_scope_filter_sql(role, scope, table_alias='s'):
    """
    根据用户角色和数据范围，返回 (sql_snippet, params_list)
    用于追加到 SQL 查询的 WHERE 子句中，实现数据隔离。
    role: admin / teacher / student
    scope: '*' / '计科1801,计科1802' / '2018182811'
    table_alias: SQL 中学生表的别名，默认 's'
    """
    if role == 'admin' or not scope:
        return '', []
    if role == 'teacher':
        # scope = "计科1801,计科1802" → 只查这些班级的学生
        class_names = [c.strip() for c in scope.split(',')]
        placeholders = ','.join(['?'] * len(class_names))
        sql = f' AND {table_alias}.id IN (SELECT id FROM students WHERE class_id IN (SELECT id FROM classes WHERE name IN ({placeholders})))'
        return sql, class_names
    if role == 'student':
        # scope = "2018182811" → 只查自己
        return f' AND {table_alias}.id = ?', [scope]
    # 未知角色 → 无数据
    return ' AND 1=0', []
