#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify

sys.path.insert(0, os.path.dirname(__file__))
from models import get_db, grade_to_numeric, get_student_stats, get_gpa, get_all_students, get_student_detail, get_scope_filter_sql

app = Flask(__name__)
app.secret_key = 'linux_zuoye6_secret_key_2026'
app.template_folder = os.path.join(os.path.dirname(__file__), 'templates')
app.static_folder = os.path.join(os.path.dirname(__file__), 'static')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        db = get_db()
        user = db.execute(
            'SELECT * FROM users WHERE username = ? AND password = ?',
            (username, password)
        ).fetchone()
        db.close()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['scope'] = user['scope'] or '*'
            flash(f'登录成功！欢迎 {username}', 'success')
            return redirect(url_for('dashboard'))
        flash('用户名或密码错误！', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('已退出登录', 'info')
    return redirect(url_for('login'))

def login_required(roles=None):
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('请先登录！', 'error')
                return redirect(url_for('login'))
            if roles and session.get('role') not in roles:
                flash('权限不足！需要角色：' + '/'.join(roles), 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
@login_required()
def dashboard():
    db = get_db()
    role = session.get('role', 'admin')
    scope = session.get('scope', '*')
    scope_sql, scope_params = get_scope_filter_sql(role, scope, 's')

    # 根据用户数据范围过滤学生总数
    total_students = db.execute(f'SELECT COUNT(*) FROM students s WHERE 1=1{scope_sql}', scope_params).fetchone()[0]
    total_subjects = db.execute('SELECT COUNT(*) FROM subjects').fetchone()[0]
    total_classes = db.execute('SELECT COUNT(*) FROM classes').fetchone()[0]
    total_scores = db.execute(f'SELECT COUNT(*) FROM scores WHERE student_id IN (SELECT id FROM students s WHERE 1=1{scope_sql})', scope_params).fetchone()[0]

    class_stats = db.execute(f'''
        SELECT c.name, COUNT(s.id) as cnt
        FROM classes c LEFT JOIN students s ON s.class_id = c.id
        WHERE 1=1{scope_sql}
        GROUP BY c.id ORDER BY c.name
    ''', scope_params).fetchall()

    recent = db.execute(f'''
        SELECT s.id, s.name, c.name as cls
        FROM students s LEFT JOIN classes c ON s.class_id = c.id
        WHERE 1=1{scope_sql}
        ORDER BY s.id DESC LIMIT 5
    ''', scope_params).fetchall()
    db.close()
    return render_template('dashboard.html',
                           total_students=total_students,
                           total_subjects=total_subjects,
                           total_classes=total_classes,
                           total_scores=total_scores,
                           class_stats=class_stats,
                           recent=recent)

@app.route('/students')
@login_required()
def student_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    class_id = request.args.get('class_id', type=int)
    db = get_db()
    # 带数据隔离的学生列表
    role = session.get('role', 'admin')
    scope = session.get('scope', '*')
    students, total, page_num, total_pages = get_all_students(
        db, page=page, per_page=20, search=search, class_id=class_id,
        role=role, scope=scope)
    # 班级列表也要按老师权限过滤
    scope_sql, scope_params = get_scope_filter_sql(role, scope, 's')
    classes = db.execute(f'''
        SELECT DISTINCT c.id, c.name FROM classes c
        JOIN students s ON s.class_id = c.id
        WHERE 1=1{scope_sql} ORDER BY c.name
    ''', scope_params).fetchall()
    db.close()
    return render_template('students.html', students=students, total=total,
                           page=page_num, total_pages=total_pages,
                           search=search, class_id=class_id, classes=classes)

@app.route('/students/add', methods=['GET', 'POST'])
@login_required(roles=['admin', 'teacher'])
def add_student():
    db = get_db()
    subjects = db.execute('SELECT id, name, credit FROM subjects ORDER BY id').fetchall()
    # 老师只能看到管辖的班级
    role = session.get('role', 'admin')
    scope = session.get('scope', '*')
    if role == 'teacher':
        class_names = [c.strip() for c in scope.split(',')]
        placeholders = ','.join(['?'] * len(class_names))
        classes = db.execute(f'SELECT id, name FROM classes WHERE name IN ({placeholders}) ORDER BY name', class_names).fetchall()
    else:
        classes = db.execute('SELECT id, name FROM classes ORDER BY name').fetchall()
    if request.method == 'POST':
        sid = request.form.get('sid', '').strip()
        name = request.form.get('name', '').strip()
        class_id = request.form.get('class_id', type=int)
        if not sid or not name:
            flash('学号和姓名不能为空！', 'error')
            db.close()
            return render_template('student_form.html', subjects=subjects, classes=classes, mode='add')
        existing = db.execute('SELECT id FROM students WHERE id = ?', (sid,)).fetchone()
        if existing:
            flash(f'学号 {sid} 已存在！', 'error')
            db.close()
            return render_template('student_form.html', subjects=subjects, classes=classes, mode='add')
        # 自动分配班级
        if not class_id:
            from init_db import get_class_for_student
            cls_name = get_class_for_student(sid)
            row = db.execute('SELECT id FROM classes WHERE name = ?', (cls_name,)).fetchone()
            class_id = row[0] if row else None
        # 老师只能添加自己管辖班级的学生
        if role == 'teacher':
            allowed_ids = [c['id'] for c in classes]
            if class_id not in allowed_ids:
                flash('权限不足！只能添加您管辖班级的学生。', 'error')
                db.close()
                return render_template('student_form.html', subjects=subjects, classes=classes, mode='add')
        db.execute('INSERT INTO students (id, name, class_id) VALUES (?, ?, ?)', (sid, name, class_id))
        for subj in subjects:
            raw = request.form.get(f'score_{subj["id"]}', '').strip()
            if raw:
                numeric = grade_to_numeric(raw)
                db.execute('INSERT OR REPLACE INTO scores (student_id, subject_id, raw_score, numeric_score) VALUES (?, ?, ?, ?)',
                           (sid, subj['id'], raw, numeric))
        db.commit()
        db.close()
        flash(f'学生 {name} ({sid}) 已添加！', 'success')
        return redirect(url_for('student_list'))
    db.close()
    return render_template('student_form.html', subjects=subjects, classes=classes, mode='add')

@app.route('/students/<student_id>/edit', methods=['GET', 'POST'])
@login_required(roles=['admin', 'teacher'])
def edit_student(student_id):
    db = get_db()
    student = db.execute('SELECT * FROM students WHERE id = ?', (student_id,)).fetchone()
    if not student:
        flash('学生不存在！', 'error')
        db.close()
        return redirect(url_for('student_list'))
    # 老师只能编辑管辖班级的学生
    role = session.get('role', 'admin')
    scope = session.get('scope', '*')
    scope_sql, scope_params = get_scope_filter_sql(role, scope)
    if scope_sql:
        check = db.execute(f'SELECT s.id FROM students s WHERE s.id = ?{scope_sql}', [student_id] + scope_params).fetchone()
        if not check:
            flash('权限不足！该学生不属于您管辖的班级。', 'error')
            db.close()
            return redirect(url_for('student_list'))
    subjects = db.execute('SELECT id, name, credit FROM subjects ORDER BY id').fetchall()
    if role == 'teacher':
        class_names = [c.strip() for c in scope.split(',')]
        placeholders = ','.join(['?'] * len(class_names))
        classes = db.execute(f'SELECT id, name FROM classes WHERE name IN ({placeholders}) ORDER BY name', class_names).fetchall()
    else:
        classes = db.execute('SELECT id, name FROM classes ORDER BY name').fetchall()
    scores_data = {}
    for sc in db.execute('SELECT subject_id, raw_score FROM scores WHERE student_id = ?', (student_id,)).fetchall():
        scores_data[sc['subject_id']] = sc['raw_score'] or ''
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        class_id = request.form.get('class_id', type=int)
        if not name:
            flash('姓名不能为空！', 'error')
            db.close()
            return render_template('student_form.html', student=student, subjects=subjects,
                                   classes=classes, scores_data=scores_data, mode='edit')
        db.execute('UPDATE students SET name = ?, class_id = ? WHERE id = ?', (name, class_id, student_id))
        for subj in subjects:
            raw = request.form.get(f'score_{subj["id"]}', '').strip()
            if raw:
                numeric = grade_to_numeric(raw)
                db.execute('INSERT OR REPLACE INTO scores (student_id, subject_id, raw_score, numeric_score) VALUES (?, ?, ?, ?)',
                           (student_id, subj['id'], raw, numeric))
            else:
                db.execute('DELETE FROM scores WHERE student_id = ? AND subject_id = ?', (student_id, subj['id']))
        db.commit()
        db.close()
        flash('修改成功！', 'success')
        return redirect(url_for('student_detail', student_id=student_id))
    db.close()
    return render_template('student_form.html', student=student, subjects=subjects,
                           classes=classes, scores_data=scores_data, mode='edit')

@app.route('/students/<student_id>')
@login_required()
def student_detail(student_id):
    db = get_db()
    # 学生只能查自己，老师只能查管辖班级
    role = session.get('role', 'admin')
    scope = session.get('scope', '*')
    scope_sql, scope_params = get_scope_filter_sql(role, scope)
    if scope_sql:
        check = db.execute(f'SELECT s.id FROM students s WHERE s.id = ?{scope_sql}', [student_id] + scope_params).fetchone()
        if not check:
            flash('权限不足！无法查看该学生的信息。', 'error')
            db.close()
            return redirect(url_for('student_list'))
    student, scores = get_student_detail(db, student_id)
    if not student:
        flash('学生不存在！', 'error')
        db.close()
        return redirect(url_for('student_list'))
    total, avg, count = get_student_stats(db, student_id)
    gpa, total_credit = get_gpa(db, student_id)
    db.close()
    return render_template('student_detail.html', student=student, scores=scores,
                           total=total, avg=avg, count=count, gpa=gpa, total_credit=total_credit)

@app.route('/students/<student_id>/delete', methods=['POST'])
@login_required(roles=['admin', 'teacher'])
def delete_student(student_id):
    db = get_db()
    # 老师只能删除管辖班级的学生
    role = session.get('role', 'admin')
    scope = session.get('scope', '*')
    scope_sql, scope_params = get_scope_filter_sql(role, scope)
    if scope_sql:
        check = db.execute(f'SELECT s.id FROM students s WHERE s.id = ?{scope_sql}', [student_id] + scope_params).fetchone()
        if not check:
            flash('权限不足！该学生不属于您管辖的班级。', 'error')
            db.close()
            return redirect(url_for('student_list'))
    student = db.execute('SELECT name FROM students WHERE id = ?', (student_id,)).fetchone()
    if not student:
        flash('学生不存在！', 'error')
        db.close()
        return redirect(url_for('student_list'))
    db.execute('DELETE FROM scores WHERE student_id = ?', (student_id,))
    db.execute('DELETE FROM students WHERE id = ?', (student_id,))
    db.commit()
    db.close()
    flash(f'已删除 {student["name"]} ({student_id})', 'success')
    return redirect(url_for('student_list'))

@app.route('/query', methods=['GET', 'POST'])
@login_required()
def query_page():
    db = get_db()
    role = session.get('role', 'admin')
    scope = session.get('scope', '*')
    scope_sql, scope_params = get_scope_filter_sql(role, scope, 's')
    subjects = db.execute('SELECT id, name FROM subjects ORDER BY id').fetchall()
    results = None
    query_type = None
    if request.method == 'POST':
        query_type = request.form.get('query_type', '1')
        if query_type == '1':
            sid = request.form.get('sid', '').strip()
            if sid:
                # 学生只能查自己，老师只能查管辖班级
                if scope_sql:
                    check = db.execute(f'SELECT s.id FROM students s WHERE s.id = ?{scope_sql}', [sid] + scope_params).fetchone()
                    if not check:
                        flash('权限不足！无法查看该学生的信息。', 'error')
                        db.close()
                        return render_template('query.html', subjects=subjects, results=None, query_type=query_type)
                student, scores = get_student_detail(db, sid)
                if student:
                    total, avg, count = get_student_stats(db, sid)
                    gpa, tc = get_gpa(db, sid)
                    results = {'student': student, 'scores': scores, 'total': total, 'avg': avg, 'count': count, 'gpa': gpa, 'total_credit': tc}
        elif query_type == '2':
            keyword = request.form.get('keyword', '').strip()
            if keyword:
                rows = db.execute(f'''
                    SELECT s.id, s.name, c.name as class_name
                    FROM students s LEFT JOIN classes c ON s.class_id = c.id
                    WHERE s.name LIKE ?{scope_sql} ORDER BY s.id
                ''', [f'%{keyword}%'] + scope_params).fetchall()
                if rows:
                    results = []
                    for r in rows:
                        t, a, c = get_student_stats(db, r['id'])
                        results.append({**dict(r), 'total': t, 'avg': a, 'count': c})
        elif query_type == '3':
            subject_id = request.form.get('subject_id', type=int)
            min_score = request.form.get('min_score', type=float)
            max_score = request.form.get('max_score', type=float)
            if subject_id:
                subj = db.execute('SELECT name FROM subjects WHERE id = ?', (subject_id,)).fetchone()
                if subj:
                    sql = f'''
                        SELECT s.id, s.name, c.name as class_name, sc.raw_score, sc.numeric_score
                        FROM scores sc JOIN students s ON sc.student_id = s.id
                        LEFT JOIN classes c ON s.class_id = c.id
                        WHERE sc.subject_id = ? AND sc.numeric_score IS NOT NULL{scope_sql}
                    '''
                    params = [subject_id] + scope_params
                    if min_score is not None:
                        sql += ' AND sc.numeric_score >= ?'
                        params.append(min_score)
                    if max_score is not None:
                        sql += ' AND sc.numeric_score <= ?'
                        params.append(max_score)
                    sql += ' ORDER BY sc.numeric_score DESC'
                    rows = db.execute(sql, params).fetchall()
                    if rows:
                        results = {'subject_name': subj['name'], 'rows': rows}
        elif query_type == '4':
            name_kw = request.form.get('name_kw', '').strip()
            subj_id = request.form.get('subj_id', type=int)
            min_s = request.form.get('min_s', type=float)
            max_s = request.form.get('max_s', type=float)
            sql = f'''
                SELECT DISTINCT s.id, s.name, c.name as class_name
                FROM students s LEFT JOIN classes c ON s.class_id = c.id WHERE 1=1{scope_sql}
            '''
            params = scope_params.copy()
            if name_kw:
                sql += ' AND s.name LIKE ?'
                params.append(f'%{name_kw}%')
            if subj_id:
                sql += ' AND s.id IN (SELECT student_id FROM scores WHERE subject_id = ? AND numeric_score IS NOT NULL)'
                params.append(subj_id)
                if min_s is not None:
                    sql += ' AND s.id IN (SELECT student_id FROM scores WHERE subject_id = ? AND numeric_score >= ?)'
                    params.extend([subj_id, min_s])
                if max_s is not None:
                    sql += ' AND s.id IN (SELECT student_id FROM scores WHERE subject_id = ? AND numeric_score <= ?)'
                    params.extend([subj_id, max_s])
            sql += ' ORDER BY s.id'
            rows = db.execute(sql, params).fetchall()
            if rows:
                results = []
                for r in rows:
                    t, a, c = get_student_stats(db, r['id'])
                    results.append({**dict(r), 'total': t, 'avg': a, 'count': c})
    db.close()
    return render_template('query.html', subjects=subjects, results=results, query_type=query_type)

@app.route('/sort', methods=['GET', 'POST'])
@login_required()
def sort_page():
    db = get_db()
    role = session.get('role', 'admin')
    scope = session.get('scope', '*')
    scope_sql, scope_params = get_scope_filter_sql(role, scope, 's')
    subjects = db.execute('SELECT id, name FROM subjects ORDER BY id').fetchall()
    results = None
    sort_by = None
    order = 'desc'
    if request.method == 'POST':
        sort_by = request.form.get('sort_by', 'total')
        order = request.form.get('order', 'desc')
        subject_id = request.form.get('subject_id', type=int)
        if sort_by == 'subject' and subject_id:
            subj = db.execute('SELECT name FROM subjects WHERE id = ?', (subject_id,)).fetchone()
            if subj:
                sql = f'''
                    SELECT s.id, s.name, c.name as class_name, sc.raw_score, sc.numeric_score
                    FROM scores sc JOIN students s ON sc.student_id = s.id
                    LEFT JOIN classes c ON s.class_id = c.id
                    WHERE sc.subject_id = ? AND sc.numeric_score IS NOT NULL{scope_sql}
                    ORDER BY sc.numeric_score {{}}
                '''.format('DESC' if order == 'desc' else 'ASC')
                results = {'title': f'sorted by {subj["name"]}', 'rows': db.execute(sql, [subject_id] + scope_params).fetchall(), 'type': 'subject'}
        elif sort_by == 'total':
            sql = f'''
                SELECT s.id, s.name, c.name as class_name,
                       ROUND(SUM(sc.numeric_score), 2) as total,
                       COUNT(sc.id) as cnt, ROUND(AVG(sc.numeric_score), 2) as avg
                FROM students s LEFT JOIN classes c ON s.class_id = c.id
                LEFT JOIN scores sc ON sc.student_id = s.id AND sc.numeric_score IS NOT NULL
                WHERE 1=1{scope_sql}
                GROUP BY s.id ORDER BY total {{}}
            '''.format('DESC' if order == 'desc' else 'ASC')
            rows = db.execute(sql, scope_params).fetchall()
            results = {'title': 'sorted by total score', 'rows': rows, 'type': 'total'}
        elif sort_by == 'average':
            sql = f'''
                SELECT s.id, s.name, c.name as class_name,
                       ROUND(AVG(sc.numeric_score), 2) as avg,
                       COUNT(sc.id) as cnt, ROUND(SUM(sc.numeric_score), 2) as total
                FROM students s LEFT JOIN classes c ON s.class_id = c.id
                LEFT JOIN scores sc ON sc.student_id = s.id AND sc.numeric_score IS NOT NULL
                WHERE 1=1{scope_sql}
                GROUP BY s.id HAVING cnt > 0 ORDER BY avg {{}}
            '''.format('DESC' if order == 'desc' else 'ASC')
            rows = db.execute(sql, scope_params).fetchall()
            results = {'title': 'sorted by average score', 'rows': rows, 'type': 'average'}
    db.close()
    return render_template('sort.html', subjects=subjects, results=results, sort_by=sort_by, order=order)

@app.route('/statistics')
@login_required()
def statistics():
    db = get_db()
    role = session.get('role', 'admin')
    scope = session.get('scope', '*')
    scope_sql, scope_params = get_scope_filter_sql(role, scope, 's')
    report = request.args.get('report', '1')
    class_id = request.args.get('class_id', type=int)

    # 老师只能看到管辖班级的下拉选项
    if role == 'teacher':
        class_names = [c.strip() for c in scope.split(',')]
        placeholders = ','.join(['?'] * len(class_names))
        classes = db.execute(f'SELECT id, name FROM classes WHERE name IN ({placeholders}) ORDER BY name', class_names).fetchall()
    else:
        classes = db.execute('SELECT id, name FROM classes ORDER BY name').fetchall()

    result = None
    report_title = ''

    # scope 过滤在学⽣表 s 上的通用子句
    # 对统计来说，用 s.id 做 IN 子查询过滤
    scope_student_filter = scope_sql  # e.g. " AND s.id IN (SELECT id FROM students WHERE ...)"

    if report == '1':
        report_title = '各科成绩分布'
        params = scope_params.copy()
        if class_id:
            scope_student_filter += ' AND s.class_id = ?'
            params.append(class_id)
        result = db.execute(f'''
            SELECT sub.name,
                   SUM(CASE WHEN sc.numeric_score >= 90 THEN 1 ELSE 0 END) as excellent,
                   SUM(CASE WHEN sc.numeric_score >= 80 AND sc.numeric_score < 90 THEN 1 ELSE 0 END) as good,
                   SUM(CASE WHEN sc.numeric_score >= 70 AND sc.numeric_score < 80 THEN 1 ELSE 0 END) as medium,
                   SUM(CASE WHEN sc.numeric_score >= 60 AND sc.numeric_score < 70 THEN 1 ELSE 0 END) as pass,
                   SUM(CASE WHEN sc.numeric_score < 60 THEN 1 ELSE 0 END) as fail
            FROM subjects sub
            LEFT JOIN scores sc ON sc.subject_id = sub.id
            LEFT JOIN students s ON sc.student_id = s.id
            WHERE 1=1{scope_student_filter}
            GROUP BY sub.id ORDER BY sub.id
        ''', params).fetchall()
    elif report == '2':
        report_title = '各科平均/最高/最低'
        params = scope_params.copy()
        if class_id:
            scope_student_filter += ' AND s.class_id = ?'
            params.append(class_id)
        result = db.execute(f'''
            SELECT sub.name, ROUND(AVG(sc.numeric_score), 2) as avg_score,
                   MAX(sc.numeric_score) as max_score, MIN(sc.numeric_score) as min_score, COUNT(sc.id) as count
            FROM subjects sub
            LEFT JOIN scores sc ON sc.subject_id = sub.id AND sc.numeric_score IS NOT NULL
            LEFT JOIN students s ON sc.student_id = s.id
            WHERE 1=1{scope_student_filter}
            GROUP BY sub.id ORDER BY sub.id
        ''', params).fetchall()
    elif report == '3':
        report_title = '班级统计'
        params = scope_params.copy()
        if class_id:
            scope_student_filter += ' AND s.class_id = ?'
            params.append(class_id)
        result = db.execute(f'''
            SELECT c.name, c.college, c.department, COUNT(DISTINCT s.id) as student_count,
                   ROUND(AVG(sc.numeric_score), 2) as avg_score,
                   ROUND(SUM(CASE WHEN sc.numeric_score >= 60 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(sc.id), 0), 1) as pass_rate
            FROM classes c
            LEFT JOIN students s ON s.class_id = c.id
            LEFT JOIN scores sc ON sc.student_id = s.id AND sc.numeric_score IS NOT NULL
            WHERE 1=1{scope_student_filter}
            GROUP BY c.id ORDER BY c.name
        ''', params).fetchall()
    elif report == '4':
        report_title = '学院/系汇总'
        params = scope_params.copy()
        college_result = db.execute(f'''
            SELECT c.college, COUNT(DISTINCT c.id) as class_count, COUNT(DISTINCT s.id) as student_count,
                   ROUND(AVG(sc.numeric_score), 2) as avg_score
            FROM classes c
            LEFT JOIN students s ON s.class_id = c.id
            LEFT JOIN scores sc ON sc.student_id = s.id AND sc.numeric_score IS NOT NULL
            WHERE c.college IS NOT NULL{scope_student_filter}
            GROUP BY c.college
        ''', params).fetchall()
        dept_result = db.execute(f'''
            SELECT c.department, COUNT(DISTINCT s.id) as student_count, ROUND(AVG(sc.numeric_score), 2) as avg_score
            FROM classes c
            LEFT JOIN students s ON s.class_id = c.id
            LEFT JOIN scores sc ON sc.student_id = s.id AND sc.numeric_score IS NOT NULL
            WHERE c.department IS NOT NULL{scope_student_filter}
            GROUP BY c.department
        ''', params).fetchall()
        result = {'college': college_result, 'dept': dept_result}
    elif report == '5':
        report_title = '加权GPA排名'
        params = scope_params.copy()
        if class_id:
            scope_student_filter += ' AND s.class_id = ?'
            params.append(class_id)
        result = db.execute(f'''
            SELECT s.id, s.name, c.name as class_name,
                   ROUND(SUM(sc.numeric_score * sub.credit) / NULLIF(SUM(sub.credit), 0), 2) as gpa,
                   ROUND(SUM(sub.credit), 1) as total_credit
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.id
            LEFT JOIN scores sc ON sc.student_id = s.id AND sc.numeric_score IS NOT NULL
            LEFT JOIN subjects sub ON sc.subject_id = sub.id AND sub.credit > 0
            WHERE 1=1{scope_student_filter}
            GROUP BY s.id HAVING total_credit > 0 ORDER BY gpa DESC
        ''', params).fetchall()
    elif report == '6':
        report_title = '挂科名单'
        params = scope_params.copy()
        if class_id:
            scope_student_filter += ' AND s.class_id = ?'
            params.append(class_id)
        result = db.execute(f'''
            SELECT s.id, s.name, c.name as class_name, sub.name as subject_name, sc.raw_score, sc.numeric_score
            FROM scores sc
            JOIN students s ON sc.student_id = s.id
            LEFT JOIN classes c ON s.class_id = c.id
            JOIN subjects sub ON sc.subject_id = sub.id
            WHERE sc.numeric_score < 60 AND sc.numeric_score IS NOT NULL{scope_student_filter}
            ORDER BY s.id, sub.id
        ''', params).fetchall()
    db.close()
    return render_template('statistics.html', report=report, report_title=report_title, result=result, classes=classes, class_id=class_id)

# ========== 新增：批量录入某科成绩 ==========
@app.route('/scores/batch', methods=['GET', 'POST'])
@login_required(roles=['admin', 'teacher'])
def batch_scores():
    db = get_db()
    subjects = db.execute('SELECT id, name, credit FROM subjects ORDER BY id').fetchall()
    result = None
    subject_name = ''
    preview = None
    subject_id = None

    if request.method == 'POST':
        subject_id = request.form.get('subject_id', type=int)
        raw_lines = request.form.get('lines', '').strip()
        action = request.form.get('action', 'preview')

        if not subject_id or not raw_lines:
            flash('请选择科目并输入成绩数据！', 'error')
            db.close()
            return render_template('batch_scores.html', subjects=subjects, result=result, subject_name=subject_name, preview=preview)

        subj = db.execute('SELECT name FROM subjects WHERE id = ?', (subject_id,)).fetchone()
        if not subj:
            flash('无效科目！', 'error')
            db.close()
            return render_template('batch_scores.html', subjects=subjects, result=result, subject_name=subject_name, preview=preview)
        subject_name = subj['name']

        role = session.get('role', 'admin')
        scope = session.get('scope', '*')
        scope_sql, scope_params = get_scope_filter_sql(role, scope, 's')

        # 解析输入：每行"学号 成绩"
        entries = []
        errors = []
        for line in raw_lines.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            parts = line.split(None, 1)  # 按空格分割，最多2部分
            if len(parts) != 2:
                errors.append(f'格式错误: {line}')
                continue
            sid, score = parts[0].strip(), parts[1].strip()
            # 短学号补全
            if len(sid) < 10:
                sid = '20181828' + sid
            # 验证学号存在且在权限范围内
            check = db.execute(f'SELECT id, name FROM students WHERE id = ?{scope_sql}', [sid] + scope_params).fetchone()
            if not check:
                errors.append(f'学号 {sid} 不存在或无权限')
                continue
            # 获取当前值
            cur = db.execute('SELECT raw_score FROM scores WHERE student_id = ? AND subject_id = ?', (sid, subject_id)).fetchone()
            cur_val = cur[0] if cur else ''
            entries.append({'sid': sid, 'name': check['name'], 'score': score, 'current': cur_val})

        if action == 'confirm':
            # 真正写入
            success = 0
            fail = 0
            for e in entries:
                numeric = grade_to_numeric(e['score'])
                try:
                    db.execute(
                        'INSERT OR REPLACE INTO scores (student_id, subject_id, raw_score, numeric_score) VALUES (?, ?, ?, ?)',
                        (e['sid'], subject_id, e['score'], numeric)
                    )
                    db.commit()
                    success += 1
                except Exception:
                    fail += 1
            flash(f'批量录入完成！成功 {success} 条{", 失败 " + str(fail) if fail else ""}', 'success')
            result = {'success': success, 'fail': fail, 'subject': subject_name}
            db.close()
            return render_template('batch_scores.html', subjects=subjects, result=result, subject_name=subject_name, preview=None, selected_subject=subject_id)
        else:
            # 预览模式
            preview = {'entries': entries, 'errors': errors, 'subject': subject_name, 'total': len(entries)}

    db.close()
    return render_template('batch_scores.html', subjects=subjects, result=result, subject_name=subject_name, preview=preview, selected_subject=subject_id)


@app.route('/users')
@login_required(roles=['admin'])
def user_list():
    db = get_db()
    users = db.execute('SELECT id, username, role, scope FROM users ORDER BY id').fetchall()
    db.close()
    return render_template('users.html', users=users)

@app.route('/users/add', methods=['POST'])
@login_required(roles=['admin'])
def user_add():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    role = request.form.get('role', 'student').strip()
    scope = request.form.get('scope', '').strip()
    if not username or not password:
        flash('用户名和密码不能为空！', 'error')
        return redirect(url_for('user_list'))
    if role not in ('admin', 'teacher', 'student'):
        flash('无效角色！', 'error')
        return redirect(url_for('user_list'))
    if role == 'admin':
        scope = '*'
    elif not scope:
        flash(f'请为{role}角色设置数据范围！', 'error')
        return redirect(url_for('user_list'))
    db = get_db()
    try:
        db.execute('INSERT INTO users (username, password, role, scope) VALUES (?, ?, ?, ?)',
                   (username, password, role, scope))
        db.commit()
        flash(f'用户 {username} 已创建！', 'success')
    except Exception as e:
        flash(f'创建失败：{e}', 'error')
    db.close()
    return redirect(url_for('user_list'))

@app.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required(roles=['admin'])
def user_delete(user_id):
    db = get_db()
    user = db.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        flash('用户不存在！', 'error')
        db.close()
        return redirect(url_for('user_list'))
    if user['username'] == 'admin':
        flash('不能删除超级管理员！', 'error')
        db.close()
        return redirect(url_for('user_list'))
    db.execute('DELETE FROM users WHERE id = ?', (user_id,))
    db.commit()
    flash(f'用户 {user["username"]} 已删除！', 'success')
    db.close()
    return redirect(url_for('user_list'))

if __name__ == '__main__':
    if not os.path.exists(os.path.join(os.path.dirname(__file__), 'data', 'scores.db')):
        print('[init] creating database...')
        from init_db import init_database
        if init_database():
            print('[init] done')
        else:
            print('[init] failed!')
            sys.exit(1)
    port = int(os.environ.get('PORT', 5000))
    print(f'[start] score management system')
    print(f'[url] http://127.0.0.1:{port}')
    app.run(debug=True, host='0.0.0.0', port=port)
