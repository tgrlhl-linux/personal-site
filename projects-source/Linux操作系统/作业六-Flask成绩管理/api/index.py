#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vercel Serverless — Flask 成绩管理系统（自包含单文件版）
冷启动时自动用种子数据初始化 SQLite。
"""
import os, sys, sqlite3, random, re, functools
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify

HERE = os.path.dirname(os.path.abspath(__file__))
# Vercel Serverless: /tmp 是可写目录
DB_PATH = os.path.join('/tmp', 'flask-score', 'scores.db')

app = Flask(__name__)
app.secret_key = 'linux_zuoye6_secret_key_2026'
app.template_folder = os.path.join(HERE, 'templates')
app.static_folder = os.path.join(HERE, 'static')

# ── Database helpers ──
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def grade_to_numeric(raw):
    if raw is None: return None
    raw = str(raw).strip()
    if not raw: return None
    mapping = {'优秀':95,'优':95,'良好':85,'良':85,'中等':75,'中':75,'及格':65,'及':65,'不及格':55}
    if raw in mapping: return mapping[raw]
    m = re.search(r'(\d+(?:\.\d+)?)', raw)
    return float(m.group(1)) if m else None

def get_scope_filter_sql(role, scope, table_alias='s'):
    if role == 'admin' or not scope: return '', []
    if role == 'teacher':
        classes = [c.strip() for c in scope.split(',')]
        ph = ','.join(['?'] * len(classes))
        return f' AND {table_alias}.id IN (SELECT id FROM students WHERE class_id IN (SELECT id FROM classes WHERE name IN ({ph})))', classes
    if role == 'student': return f' AND {table_alias}.id = ?', [scope]
    return ' AND 1=0', []

def get_student_stats(db, sid):
    r = db.execute('SELECT COUNT(*),SUM(s.numeric_score),AVG(s.numeric_score) FROM scores s WHERE s.student_id=? AND s.numeric_score IS NOT NULL', (sid,)).fetchone()
    return round(r[1] or 0, 2), round(r[2] or 0, 2), r[0] or 0

def get_gpa(db, sid):
    r = db.execute('SELECT SUM(s.numeric_score*sub.credit),SUM(sub.credit) FROM scores s JOIN subjects sub ON s.subject_id=sub.id WHERE s.student_id=? AND s.numeric_score IS NOT NULL AND sub.credit>0', (sid,)).fetchone()
    return (round(r[0]/r[1],2) if r[1] else 0), round(r[1] or 0, 1)

def get_all_students(db, page=1, per_page=20, search='', class_id=None, role='admin', scope='*'):
    conds, params = [], []
    if search:
        conds.append('(s.id LIKE ? OR s.name LIKE ?)')
        params.extend([f'%{search}%', f'%{search}%'])
    if class_id: conds.append('s.class_id=?'); params.append(class_id)
    scope_sql, scope_params = get_scope_filter_sql(role, scope, 's')
    if scope_sql: conds.append(scope_sql[4:]); params.extend(scope_params)
    where = 'WHERE '+' AND '.join(conds) if conds else ''
    total = db.execute(f'SELECT COUNT(*) FROM students s {where}', params).fetchone()[0]
    offset = (page-1)*per_page
    students = db.execute(f'SELECT s.id,s.name,c.name as class_name FROM students s LEFT JOIN classes c ON s.class_id=c.id {where} ORDER BY s.id LIMIT ? OFFSET ?', params+[per_page,offset]).fetchall()
    return students, total, page, (total+per_page-1)//per_page

# ── DB seed ──
def seed_demo_data():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.executescript('''CREATE TABLE IF NOT EXISTS classes(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE NOT NULL,college TEXT,department TEXT);
        CREATE TABLE IF NOT EXISTS students(id TEXT PRIMARY KEY,name TEXT NOT NULL,class_id INTEGER REFERENCES classes(id));
        CREATE TABLE IF NOT EXISTS subjects(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE NOT NULL,credit REAL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS scores(id INTEGER PRIMARY KEY AUTOINCREMENT,student_id TEXT REFERENCES students(id),subject_id INTEGER REFERENCES subjects(id),raw_score TEXT,numeric_score REAL,UNIQUE(student_id,subject_id));
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT UNIQUE NOT NULL,password TEXT NOT NULL,role TEXT NOT NULL CHECK(role IN('admin','teacher','student')),scope TEXT DEFAULT '*');''')
    cid={}
    for n,co,dep in [('计科1801','信息科学与工程学院','计算机科学系'),('计科1802','信息科学与工程学院','计算机科学系'),('软件1801','信息科学与工程学院','软件工程系'),('软件1802','信息科学与工程学院','软件工程系')]:
        c.execute('INSERT OR IGNORE INTO classes(name,college,department) VALUES(?,?,?)',(n,co,dep))
    for r in c.execute('SELECT id,name FROM classes'): cid[r[1]]=r[0]
    sid_map={}
    for n,cr in [('高等数学[5]',5),('线性代数[3]',3),('C语言程序设计[4]',4),('数据结构[4]',4),('操作系统[3]',3),('数据库原理[3]',3)]:
        c.execute('INSERT OR IGNORE INTO subjects(name,credit) VALUES(?,?)',(n,cr))
    for r in c.execute('SELECT id,name FROM subjects'): sid_map[r[1]]=r[0]
    random.seed(42)
    for sn,nm,cl in [('2018182801','张三','计科1801'),('2018182802','李四','计科1801'),('2018182803','王五','计科1802'),('2018182804','赵六','软件1801'),('2018182805','钱七','软件1802')]:
        c.execute('INSERT OR IGNORE INTO students(id,name,class_id) VALUES(?,?,?)',(sn,nm,cid.get(cl)))
        for subj_id in sid_map.values():
            score = round(random.uniform(55,100),1)
            c.execute('INSERT OR IGNORE INTO scores(student_id,subject_id,raw_score,numeric_score) VALUES(?,?,?,?)',(sn,subj_id,str(score),score))
    for u,p,r,s in [('admin','admin123','admin','*'),('zhanglao','123456','teacher','计科1801,计科1802'),('wanglao','123456','teacher','软件1801,软件1802'),('2018182801','123456','student','2018182801')]:
        c.execute('INSERT OR IGNORE INTO users(username,password,role,scope) VALUES(?,?,?,?)',(u,p,r,s))
    conn.commit(); conn.close()

if not os.path.exists(DB_PATH):
    seed_demo_data()

# ── Auth decorator ──
def login_required(roles=None):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*a,**kw):
            if 'user_id' not in session:
                flash('请先登录！','error'); return redirect(url_for('login'))
            if roles and session.get('role') not in roles:
                flash('权限不足！','error'); return redirect(url_for('dashboard'))
            return f(*a,**kw)
        return wrapper
    return decorator

# ── Routes ──
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','').strip()
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username=? AND password=?', (username,password)).fetchone()
        db.close()
        if user:
            session['user_id']=user['id']; session['username']=user['username']
            session['role']=user['role']; session['scope']=user['scope'] or '*'
            flash(f'登录成功！欢迎 {username}','success'); return redirect(url_for('dashboard'))
        flash('用户名或密码错误！','error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear(); flash('已退出登录','info'); return redirect(url_for('login'))

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required()
def dashboard():
    db = get_db(); role=session.get('role'); scope=session.get('scope')
    total_students = db.execute('SELECT COUNT(*) as c FROM students').fetchone()['c']
    total_scores = db.execute('SELECT COUNT(*) as c FROM scores').fetchone()['c']
    avg_all = db.execute('SELECT ROUND(AVG(numeric_score),1) as a FROM scores WHERE numeric_score IS NOT NULL').fetchone()['a'] or 0
    pass_rate = db.execute("SELECT ROUND(SUM(CASE WHEN numeric_score>=60 THEN 1 ELSE 0 END)*100.0/COUNT(*),1) as p FROM scores WHERE numeric_score IS NOT NULL").fetchone()['p'] or 0
    db.close()
    return render_template('dashboard.html', total_students=total_students, total_scores=total_scores, avg_all=avg_all, pass_rate=pass_rate)

@app.route('/students')
@login_required()
def list_students():
    db=get_db(); role=session.get('role'); scope=session.get('scope')
    page=int(request.args.get('page',1)); search=request.args.get('q',''); class_id=request.args.get('class_id','')
    students, total, p, pages = get_all_students(db, page, 20, search, class_id, role, scope)
    classes = db.execute('SELECT id,name FROM classes ORDER BY id').fetchall()
    db.close()
    return render_template('students.html', students=students, total=total, page=p, pages=pages, search=search, class_id=class_id, classes=classes)

@app.route('/student/<sid>')
@login_required()
def student_detail(sid):
    db=get_db()
    student = db.execute('SELECT s.id,s.name,c.name as class_name,c.college,c.department FROM students s LEFT JOIN classes c ON s.class_id=c.id WHERE s.id=?',(sid,)).fetchone()
    if not student: db.close(); flash('学生不存在','error'); return redirect(url_for('list_students'))
    scores = db.execute('SELECT sub.id,sub.name,sub.credit,sc.raw_score,sc.numeric_score FROM subjects sub LEFT JOIN scores sc ON sc.subject_id=sub.id AND sc.student_id=? ORDER BY sub.id',(sid,)).fetchall()
    total_score, avg_score, count = get_student_stats(db, sid)
    gpa, total_credit = get_gpa(db, sid)
    db.close()
    return render_template('student_detail.html', student=student, scores=scores, total_score=total_score, avg_score=avg_score, count=count, gpa=gpa, total_credit=total_credit)

@app.route('/query', methods=['GET','POST'])
@login_required()
def query():
    if request.method=='POST':
        student_id=request.form.get('student_id','').strip()
        return redirect(url_for('student_detail',sid=student_id))
    return render_template('query.html')

@app.route('/grade/add', methods=['POST'])
@login_required(roles=['admin','teacher'])
def add_grade():
    db=get_db()
    db.execute('INSERT INTO scores(student_id,subject_id,raw_score,numeric_score) VALUES(?,?,?,?)',
               (request.form['student_id'],request.form['subject_id'],request.form['raw_score'],grade_to_numeric(request.form['raw_score'])))
    db.commit(); db.close()
    flash('成绩已添加','success'); return redirect(url_for('student_detail',sid=request.form['student_id']))

@app.route('/statistics')
@login_required()
def statistics():
    db=get_db()
    class_stats = db.execute('''SELECT c.name as class_name,COUNT(DISTINCT s.id) as stu_count,
        ROUND(AVG(sc.numeric_score),1) as avg_score,
        ROUND(SUM(CASE WHEN sc.numeric_score>=60 THEN 1 ELSE 0 END)*100.0/COUNT(*),1) as pass_rate
        FROM classes c JOIN students s ON s.class_id=c.id JOIN scores sc ON sc.student_id=s.id
        WHERE sc.numeric_score IS NOT NULL GROUP BY c.id ORDER BY c.id''').fetchall()
    subj_stats = db.execute('''SELECT sub.name,COUNT(*) as count,ROUND(AVG(sc.numeric_score),1) as avg,
        ROUND(SUM(CASE WHEN sc.numeric_score>=60 THEN 1 ELSE 0 END)*100.0/COUNT(*),1) as pass_rate
        FROM subjects sub JOIN scores sc ON sc.subject_id=sub.id
        WHERE sc.numeric_score IS NOT NULL GROUP BY sub.id ORDER BY sub.id''').fetchall()
    db.close()
    return render_template('statistics.html', class_stats=class_stats, subj_stats=subj_stats)

@app.route('/sort')
@login_required()
def sort_scores():
    by=request.args.get('by','score'); order=request.args.get('order','desc')
    db=get_db()
    students = db.execute(f'''SELECT s.id,s.name,COUNT(sc.id) as sub_count,ROUND(AVG(sc.numeric_score),1) as avg_score,
        ROUND(SUM(CASE WHEN sc.numeric_score>=60 THEN 1 ELSE 0 END)*100.0/COUNT(*),1) as pass_rate
        FROM students s JOIN scores sc ON sc.student_id=s.id
        WHERE sc.numeric_score IS NOT NULL GROUP BY s.id
        ORDER BY {'avg_score' if by=='score' else 's.id'} {'DESC' if order=='desc' else 'ASC'}''').fetchall()
    db.close()
    return render_template('sort.html', students=students, by=by, order=order)

@app.route('/batch', methods=['GET','POST'])
@login_required(roles=['admin','teacher'])
def batch_scores():
    db=get_db(); subjects=db.execute('SELECT id,name,credit FROM subjects ORDER BY id').fetchall()
    if request.method=='POST':
        subject_id=request.form.get('subject_id')
        lines=request.form.get('data','').strip().split('\n')
        results=[]
        for line in lines:
            parts=line.strip().split()
            if len(parts)>=2:
                sid,raw=parts[0],' '.join(parts[1:])
                student=db.execute('SELECT id,name FROM students WHERE id=?',(sid,)).fetchone()
                if student:
                    existing=db.execute('SELECT id,raw_score,numeric_score FROM scores WHERE student_id=? AND subject_id=?',(sid,subject_id)).fetchone()
                    numeric=grade_to_numeric(raw)
                    results.append({'student':student,'raw':raw,'numeric':numeric,'existing':existing})
        db.close()
        return render_template('batch_scores.html', subjects=subjects, subject_id=subject_id, results=results, preview=True)
    db.close()
    return render_template('batch_scores.html', subjects=subjects, preview=False)

@app.route('/batch/confirm', methods=['POST'])
@login_required(roles=['admin','teacher'])
def batch_confirm():
    db=get_db()
    subject_id=request.form.get('subject_id')
    sids=request.form.getlist('student_id[]')
    raws=request.form.getlist('raw_score[]')
    for sid,raw in zip(sids,raws):
        numeric=grade_to_numeric(raw)
        existing=db.execute('SELECT id FROM scores WHERE student_id=? AND subject_id=?',(sid,subject_id)).fetchone()
        if existing:
            db.execute('UPDATE scores SET raw_score=?,numeric_score=? WHERE id=?',(raw,numeric,existing['id']))
        else:
            db.execute('INSERT INTO scores(student_id,subject_id,raw_score,numeric_score) VALUES(?,?,?,?)',(sid,subject_id,raw,numeric))
    db.commit(); db.close()
    flash('批量录入完成！','success'); return redirect(url_for('list_students'))

@app.route('/users')
@login_required(roles=['admin'])
def user_management():
    db=get_db(); users=db.execute('SELECT id,username,role,scope FROM users ORDER BY id').fetchall(); db.close()
    return render_template('users.html', users=users)

@app.route('/user/add', methods=['POST'])
@login_required(roles=['admin'])
def add_user():
    db=get_db()
    db.execute('INSERT INTO users(username,password,role,scope) VALUES(?,?,?,?)',
               (request.form['username'],request.form['password'],request.form['role'],request.form.get('scope','')))
    db.commit(); db.close()
    flash('用户已添加','success'); return redirect(url_for('user_management'))

@app.route('/user/delete/<int:uid>')
@login_required(roles=['admin'])
def delete_user(uid):
    db=get_db(); db.execute('DELETE FROM users WHERE id=?',(uid,)); db.commit(); db.close()
    flash('用户已删除','success'); return redirect(url_for('user_management'))

# For Vercel Python Runtime - WSGI handler
app = app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
