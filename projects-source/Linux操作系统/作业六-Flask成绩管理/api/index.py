#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vercel Serverless — Flask 成绩管理系统（完整版）
冷启动时自动用种子数据初始化 SQLite。
"""
import os, sys, sqlite3, random, re, functools
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join('/tmp', 'flask-score', 'scores.db')

app = Flask(__name__)
app.secret_key = 'linux_zuoye6_secret_key_2026'
app.template_folder = os.path.join(HERE, 'templates')
app.static_folder = os.path.join(HERE, 'static')

# ── 全局错误处理 ──
@app.errorhandler(500)
def handle_500(e):
    import traceback
    return f"<pre>{traceback.format_exc()}</pre>", 500

@app.errorhandler(404)
def handle_404(e):
    return render_template('login.html' if 'user_id' not in session else 'dashboard.html'), 404

# ── Database helpers (from models.py) ──
def get_db():
    ensure_db()
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

def get_student_detail(db, sid):
    student = db.execute('SELECT s.id,s.name,c.name as class_name,c.college,c.department FROM students s LEFT JOIN classes c ON s.class_id=c.id WHERE s.id=?',(sid,)).fetchone()
    if not student: return None, None
    scores = db.execute('SELECT sub.id,sub.name,sub.credit,sc.raw_score,sc.numeric_score FROM subjects sub LEFT JOIN scores sc ON sc.subject_id=sub.id AND sc.student_id=? ORDER BY sub.id',(sid,)).fetchall()
    return student, scores

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

def ensure_db():
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

# ═══════════════════════════════════════════
# 路由：认证
# ═══════════════════════════════════════════

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

# ═══════════════════════════════════════════
# 路由：仪表盘
# ═══════════════════════════════════════════

@app.route('/dashboard')
@login_required()
def dashboard():
    db = get_db(); role=session.get('role'); scope=session.get('scope')
    scope_sql, scope_params = get_scope_filter_sql(role, scope, 's')
    total_students = db.execute(f'SELECT COUNT(*) FROM students s WHERE 1=1{scope_sql}', scope_params).fetchone()[0]
    total_subjects = db.execute('SELECT COUNT(*) FROM subjects').fetchone()[0]
    total_classes = db.execute('SELECT COUNT(*) FROM classes').fetchone()[0]
    total_scores = db.execute(f'SELECT COUNT(*) FROM scores WHERE student_id IN (SELECT id FROM students s WHERE 1=1{scope_sql})', scope_params).fetchone()[0]
    class_stats = db.execute(f'SELECT c.name,COUNT(s.id) as cnt FROM classes c LEFT JOIN students s ON s.class_id=c.id WHERE 1=1{scope_sql} GROUP BY c.id ORDER BY c.name', scope_params).fetchall()
    avg_all = db.execute('SELECT ROUND(AVG(numeric_score),1) FROM scores WHERE numeric_score IS NOT NULL').fetchone()[0] or 0
    pass_rate = db.execute("SELECT ROUND(SUM(CASE WHEN numeric_score>=60 THEN 1 ELSE 0 END)*100.0/COUNT(*),1) FROM scores WHERE numeric_score IS NOT NULL").fetchone()[0] or 0
    db.close()
    return render_template('dashboard.html', total_students=total_students, total_subjects=total_subjects,
                           total_classes=total_classes, total_scores=total_scores,
                           class_stats=class_stats, avg_all=avg_all, pass_rate=pass_rate)

# ═══════════════════════════════════════════
# 路由：学生管理
# ═══════════════════════════════════════════

@app.route('/students')
@login_required()
def student_list():
    db=get_db(); role=session.get('role'); scope=session.get('scope')
    page=request.args.get('page',1,type=int); search=request.args.get('search',''); class_id=request.args.get('class_id',type=int)
    students, total, p, pages = get_all_students(db, page, 20, search, class_id, role, scope)
    scope_sql,scope_params=get_scope_filter_sql(role,scope,'s')
    classes = db.execute(f'SELECT DISTINCT c.id,c.name FROM classes c JOIN students s ON s.class_id=c.id WHERE 1=1{scope_sql} ORDER BY c.name', scope_params).fetchall()
    db.close()
    return render_template('students.html', students=students, total=total, page=p, total_pages=pages, search=search, class_id=class_id, classes=classes)

@app.route('/student/<student_id>')
@login_required()
def student_detail(student_id):
    db=get_db(); role=session.get('role'); scope=session.get('scope')
    scope_sql,scope_params=get_scope_filter_sql(role,scope)
    if scope_sql:
        check=db.execute(f'SELECT s.id FROM students s WHERE s.id=?{scope_sql}',[student_id]+scope_params).fetchone()
        if not check: flash('权限不足！','error'); db.close(); return redirect(url_for('student_list'))
    student,scores = get_student_detail(db, student_id)
    if not student: flash('学生不存在','error'); db.close(); return redirect(url_for('student_list'))
    total_score, avg_score, count = get_student_stats(db, student_id)
    gpa, total_credit = get_gpa(db, student_id)
    db.close()
    return render_template('student_detail.html', student=student, scores=scores, total=total_score, avg=avg_score, count=count, gpa=gpa, total_credit=total_credit)

@app.route('/students/add', methods=['GET','POST'])
@login_required(roles=['admin','teacher'])
def add_student():
    db=get_db(); role=session.get('role'); scope=session.get('scope')
    subjects = db.execute('SELECT id,name,credit FROM subjects ORDER BY id').fetchall()
    if role == 'teacher':
        class_names=[c.strip() for c in scope.split(',')]
        ph=','.join(['?']*len(class_names))
        classes=db.execute(f'SELECT id,name FROM classes WHERE name IN ({ph}) ORDER BY name',class_names).fetchall()
    else:
        classes=db.execute('SELECT id,name FROM classes ORDER BY name').fetchall()
    if request.method=='POST':
        sid=request.form.get('sid','').strip(); name=request.form.get('name','').strip()
        class_id=request.form.get('class_id',type=int)
        if not sid or not name: flash('学号和姓名不能为空！','error'); db.close(); return render_template('student_form.html',subjects=subjects,classes=classes,mode='add')
        if db.execute('SELECT id FROM students WHERE id=?',(sid,)).fetchone(): flash(f'学号 {sid} 已存在！','error'); db.close(); return render_template('student_form.html',subjects=subjects,classes=classes,mode='add')
        if role=='teacher':
            allowed_ids=[c['id'] for c in classes]
            if class_id not in allowed_ids: flash('权限不足！','error'); db.close(); return render_template('student_form.html',subjects=subjects,classes=classes,mode='add')
        db.execute('INSERT INTO students(id,name,class_id) VALUES(?,?,?)',(sid,name,class_id))
        for sub in subjects:
            raw=request.form.get(f'score_{sub["id"]}','').strip()
            if raw: db.execute('INSERT OR REPLACE INTO scores(student_id,subject_id,raw_score,numeric_score) VALUES(?,?,?,?)',(sid,sub['id'],raw,grade_to_numeric(raw)))
        db.commit(); db.close()
        flash(f'学生 {name} ({sid}) 已添加！','success'); return redirect(url_for('student_list'))
    db.close()
    return render_template('student_form.html',subjects=subjects,classes=classes,mode='add')

@app.route('/student/<student_id>/edit', methods=['GET','POST'])
@login_required(roles=['admin','teacher'])
def edit_student(student_id):
    db=get_db(); role=session.get('role'); scope=session.get('scope')
    scope_sql,scope_params=get_scope_filter_sql(role,scope)
    student=db.execute('SELECT * FROM students WHERE id=?',(student_id,)).fetchone()
    if not student: flash('学生不存在！','error'); db.close(); return redirect(url_for('student_list'))
    if scope_sql:
        check=db.execute(f'SELECT s.id FROM students s WHERE s.id=?{scope_sql}',[student_id]+scope_params).fetchone()
        if not check: flash('权限不足！','error'); db.close(); return redirect(url_for('student_list'))
    subjects=db.execute('SELECT id,name,credit FROM subjects ORDER BY id').fetchall()
    if role=='teacher':
        class_names=[c.strip() for c in scope.split(',')]
        ph=','.join(['?']*len(class_names))
        classes=db.execute(f'SELECT id,name FROM classes WHERE name IN ({ph}) ORDER BY name',class_names).fetchall()
    else:
        classes=db.execute('SELECT id,name FROM classes ORDER BY name').fetchall()
    scores_data={}
    for sc in db.execute('SELECT subject_id,raw_score FROM scores WHERE student_id=?',(student_id,)).fetchall():
        scores_data[sc['subject_id']]=sc['raw_score'] or ''
    if request.method=='POST':
        name=request.form.get('name','').strip(); class_id=request.form.get('class_id',type=int)
        if not name: flash('姓名不能为空！','error'); db.close(); return render_template('student_form.html',student=student,subjects=subjects,classes=classes,scores_data=scores_data,mode='edit')
        db.execute('UPDATE students SET name=?,class_id=? WHERE id=?',(name,class_id,student_id))
        for sub in subjects:
            raw=request.form.get(f'score_{sub["id"]}','').strip()
            if raw: db.execute('INSERT OR REPLACE INTO scores(student_id,subject_id,raw_score,numeric_score) VALUES(?,?,?,?)',(student_id,sub['id'],raw,grade_to_numeric(raw)))
            else: db.execute('DELETE FROM scores WHERE student_id=? AND subject_id=?',(student_id,sub['id']))
        db.commit(); db.close()
        flash('修改成功！','success'); return redirect(url_for('student_detail',student_id=student_id))
    db.close()
    return render_template('student_form.html',student=student,subjects=subjects,classes=classes,scores_data=scores_data,mode='edit')

@app.route('/student/<student_id>/delete', methods=['POST'])
@login_required(roles=['admin','teacher'])
def delete_student(student_id):
    db=get_db(); role=session.get('role'); scope=session.get('scope')
    scope_sql,scope_params=get_scope_filter_sql(role,scope)
    if scope_sql:
        check=db.execute(f'SELECT s.id FROM students s WHERE s.id=?{scope_sql}',[student_id]+scope_params).fetchone()
        if not check: flash('权限不足！','error'); db.close(); return redirect(url_for('student_list'))
    student=db.execute('SELECT name FROM students WHERE id=?',(student_id,)).fetchone()
    if not student: flash('学生不存在！','error'); db.close(); return redirect(url_for('student_list'))
    db.execute('DELETE FROM scores WHERE student_id=?',(student_id,))
    db.execute('DELETE FROM students WHERE id=?',(student_id,))
    db.commit(); db.close()
    flash(f'已删除 {student["name"]} ({student_id})','success'); return redirect(url_for('student_list'))

# ═══════════════════════════════════════════
# 路由：查询（4 种模式） ⭐ 修复点
# ═══════════════════════════════════════════

@app.route('/query', methods=['GET','POST'])
@login_required()
def query_page():
    db=get_db(); role=session.get('role'); scope=session.get('scope')
    scope_sql,scope_params=get_scope_filter_sql(role,scope,'s')
    subjects=db.execute('SELECT id,name FROM subjects ORDER BY id').fetchall()
    results=None; query_type=None
    if request.method=='POST':
        query_type=request.form.get('query_type','1')
        if query_type=='1':
            sid=request.form.get('sid','').strip()
            if sid:
                student,scores=get_student_detail(db,sid)
                if student:
                    total,avg,count=get_student_stats(db,sid)
                    gpa,tc=get_gpa(db,sid)
                    results={'student':student,'scores':scores,'total':total,'avg':avg,'count':count,'gpa':gpa,'total_credit':tc}
                else:
                    flash(f'学号 {sid} 不存在','error')
        elif query_type=='2':
            keyword=request.form.get('keyword','').strip()
            if keyword:
                rows=db.execute(f'SELECT s.id,s.name,c.name as class_name FROM students s LEFT JOIN classes c ON s.class_id=c.id WHERE s.name LIKE ?{scope_sql} ORDER BY s.id',[f'%{keyword}%']+scope_params).fetchall()
                if rows:
                    results=[]
                    for r in rows:
                        t,a,c=get_student_stats(db,r['id'])
                        results.append({**dict(r),'total':t,'avg':a,'count':c})
        elif query_type=='3':
            subject_id=request.form.get('subject_id',type=int); min_score=request.form.get('min_score',type=float); max_score=request.form.get('max_score',type=float)
            if subject_id:
                subj=db.execute('SELECT name FROM subjects WHERE id=?',(subject_id,)).fetchone()
                if subj:
                    sql=f'SELECT s.id,s.name,c.name as class_name,sc.raw_score,sc.numeric_score FROM scores sc JOIN students s ON sc.student_id=s.id LEFT JOIN classes c ON s.class_id=c.id WHERE sc.subject_id=? AND sc.numeric_score IS NOT NULL{scope_sql}'
                    params=[subject_id]+scope_params
                    if min_score is not None: sql+=' AND sc.numeric_score >= ?'; params.append(min_score)
                    if max_score is not None: sql+=' AND sc.numeric_score <= ?'; params.append(max_score)
                    sql+=' ORDER BY sc.numeric_score DESC'
                    rows=db.execute(sql,params).fetchall()
                    if rows: results={'subject_name':subj['name'],'rows':rows}
        elif query_type=='4':
            name_kw=request.form.get('name_kw','').strip(); subj_id=request.form.get('subj_id',type=int)
            min_s=request.form.get('min_s',type=float); max_s=request.form.get('max_s',type=float)
            sql=f'SELECT DISTINCT s.id,s.name,c.name as class_name FROM students s LEFT JOIN classes c ON s.class_id=c.id WHERE 1=1{scope_sql}'
            params=scope_params.copy()
            if name_kw: sql+=' AND s.name LIKE ?'; params.append(f'%{name_kw}%')
            if subj_id:
                sql+=' AND s.id IN (SELECT student_id FROM scores WHERE subject_id=? AND numeric_score IS NOT NULL)'; params.append(subj_id)
                if min_s is not None: sql+=f' AND s.id IN (SELECT student_id FROM scores WHERE subject_id=? AND numeric_score >= ?)'; params.extend([subj_id,min_s])
                if max_s is not None: sql+=f' AND s.id IN (SELECT student_id FROM scores WHERE subject_id=? AND numeric_score <= ?)'; params.extend([subj_id,max_s])
            sql+=' ORDER BY s.id'
            rows=db.execute(sql,params).fetchall()
            if rows:
                results=[]
                for r in rows:
                    t,a,c=get_student_stats(db,r['id'])
                    results.append({**dict(r),'total':t,'avg':a,'count':c})
    db.close()
    return render_template('query.html',subjects=subjects,results=results,query_type=query_type)

# ═══════════════════════════════════════════
# 路由：排序（总分/平均分/指定科目） ⭐ 修复点
# ═══════════════════════════════════════════

@app.route('/sort', methods=['GET','POST'])
@login_required()
def sort_page():
    db=get_db(); role=session.get('role'); scope=session.get('scope')
    scope_sql,scope_params=get_scope_filter_sql(role,scope,'s')
    subjects=db.execute('SELECT id,name FROM subjects ORDER BY id').fetchall()
    results=None; sort_by=None; order='desc'
    if request.method=='POST':
        sort_by=request.form.get('sort_by','total'); order=request.form.get('order','desc')
        subject_id=request.form.get('subject_id',type=int)
        if sort_by=='subject' and subject_id:
            subj=db.execute('SELECT name FROM subjects WHERE id=?',(subject_id,)).fetchone()
            if subj:
                sql=f'SELECT s.id,s.name,c.name as class_name,sc.raw_score,sc.numeric_score FROM scores sc JOIN students s ON sc.student_id=s.id LEFT JOIN classes c ON s.class_id=c.id WHERE sc.subject_id=? AND sc.numeric_score IS NOT NULL{scope_sql} ORDER BY sc.numeric_score {"DESC" if order=="desc" else "ASC"}'
                rows=db.execute(sql,[subject_id]+scope_params).fetchall()
                results={'title':f'《{subj["name"]}》成绩排序','rows':rows,'type':'subject'}
        elif sort_by=='total':
            sql=f'SELECT s.id,s.name,c.name as class_name,ROUND(SUM(sc.numeric_score),2) as total,COUNT(sc.id) as cnt,ROUND(AVG(sc.numeric_score),2) as avg FROM students s LEFT JOIN classes c ON s.class_id=c.id LEFT JOIN scores sc ON sc.student_id=s.id AND sc.numeric_score IS NOT NULL WHERE 1=1{scope_sql} GROUP BY s.id ORDER BY total {"DESC" if order=="desc" else "ASC"}'
            rows=db.execute(sql,scope_params).fetchall()
            results={'title':'总分排序','rows':rows,'type':'total'}
        elif sort_by=='average':
            sql=f'SELECT s.id,s.name,c.name as class_name,ROUND(AVG(sc.numeric_score),2) as avg,COUNT(sc.id) as cnt,ROUND(SUM(sc.numeric_score),2) as total FROM students s LEFT JOIN classes c ON s.class_id=c.id LEFT JOIN scores sc ON sc.student_id=s.id AND sc.numeric_score IS NOT NULL WHERE 1=1{scope_sql} GROUP BY s.id HAVING cnt>0 ORDER BY avg {"DESC" if order=="desc" else "ASC"}'
            rows=db.execute(sql,scope_params).fetchall()
            results={'title':'平均分排序','rows':rows,'type':'average'}
    db.close()
    return render_template('sort.html',subjects=subjects,results=results,sort_by=sort_by,order=order)

# ═══════════════════════════════════════════
# 路由：单条成绩录入（兼容旧版）
# ═══════════════════════════════════════════

@app.route('/grade/add', methods=['POST'])
@login_required(roles=['admin','teacher'])
def add_grade():
    db=get_db()
    db.execute('INSERT INTO scores(student_id,subject_id,raw_score,numeric_score) VALUES(?,?,?,?)',
               (request.form['student_id'],request.form['subject_id'],request.form['raw_score'],grade_to_numeric(request.form['raw_score'])))
    db.commit(); db.close()
    flash('成绩已添加','success'); return redirect(url_for('student_detail',student_id=request.form['student_id']))

# ═══════════════════════════════════════════
# 路由：统计报表（6 种报表 + 班级筛选） ⭐ 修复点
# ═══════════════════════════════════════════

@app.route('/statistics')
@login_required()
def statistics():
    db=get_db(); role=session.get('role'); scope=session.get('scope')
    scope_sql,scope_params=get_scope_filter_sql(role,scope,'s')
    report=request.args.get('report','1'); class_id=request.args.get('class_id',type=int)
    if role=='teacher':
        class_names=[c.strip() for c in scope.split(',')]
        ph=','.join(['?']*len(class_names))
        classes=db.execute(f'SELECT id,name FROM classes WHERE name IN ({ph}) ORDER BY name',class_names).fetchall()
    else:
        classes=db.execute('SELECT id,name FROM classes ORDER BY name').fetchall()
    result=None; report_title=''
    params=scope_params.copy()
    if class_id:
        scope_sql+=' AND s.class_id=?'; params.append(class_id)
    if report=='1':
        report_title='各科成绩分布'
        result=db.execute(f'''SELECT sub.name,
            SUM(CASE WHEN sc.numeric_score>=90 THEN 1 ELSE 0 END) as excellent,
            SUM(CASE WHEN sc.numeric_score>=80 AND sc.numeric_score<90 THEN 1 ELSE 0 END) as good,
            SUM(CASE WHEN sc.numeric_score>=70 AND sc.numeric_score<80 THEN 1 ELSE 0 END) as medium,
            SUM(CASE WHEN sc.numeric_score>=60 AND sc.numeric_score<70 THEN 1 ELSE 0 END) as pass,
            SUM(CASE WHEN sc.numeric_score<60 THEN 1 ELSE 0 END) as fail
            FROM subjects sub LEFT JOIN scores sc ON sc.subject_id=sub.id LEFT JOIN students s ON sc.student_id=s.id WHERE 1=1{scope_sql} GROUP BY sub.id ORDER BY sub.id''',params).fetchall()
    elif report=='2':
        report_title='各科平均/最高/最低'
        result=db.execute(f'''SELECT sub.name,ROUND(AVG(sc.numeric_score),2) as avg_score,MAX(sc.numeric_score) as max_score,MIN(sc.numeric_score) as min_score,COUNT(sc.id) as count
            FROM subjects sub LEFT JOIN scores sc ON sc.subject_id=sub.id AND sc.numeric_score IS NOT NULL LEFT JOIN students s ON sc.student_id=s.id WHERE 1=1{scope_sql} GROUP BY sub.id ORDER BY sub.id''',params).fetchall()
    elif report=='3':
        report_title='班级统计'
        result=db.execute(f'''SELECT c.name,c.college,c.department,COUNT(DISTINCT s.id) as student_count,ROUND(AVG(sc.numeric_score),2) as avg_score,
            ROUND(SUM(CASE WHEN sc.numeric_score>=60 THEN 1 ELSE 0 END)*100.0/NULLIF(COUNT(sc.id),0),1) as pass_rate
            FROM classes c LEFT JOIN students s ON s.class_id=c.id LEFT JOIN scores sc ON sc.student_id=s.id AND sc.numeric_score IS NOT NULL WHERE 1=1{scope_sql} GROUP BY c.id ORDER BY c.name''',params).fetchall()
    elif report=='4':
        report_title='学院/系汇总'
        college=db.execute(f'''SELECT c.college,COUNT(DISTINCT c.id) as class_count,COUNT(DISTINCT s.id) as student_count,ROUND(AVG(sc.numeric_score),2) as avg_score
            FROM classes c LEFT JOIN students s ON s.class_id=c.id LEFT JOIN scores sc ON sc.student_id=s.id AND sc.numeric_score IS NOT NULL WHERE c.college IS NOT NULL{scope_sql} GROUP BY c.college''',params).fetchall()
        dept=db.execute(f'''SELECT c.department,COUNT(DISTINCT s.id) as student_count,ROUND(AVG(sc.numeric_score),2) as avg_score
            FROM classes c LEFT JOIN students s ON s.class_id=c.id LEFT JOIN scores sc ON sc.student_id=s.id AND sc.numeric_score IS NOT NULL WHERE c.department IS NOT NULL{scope_sql} GROUP BY c.department''',params).fetchall()
        result={'college':college,'dept':dept}
    elif report=='5':
        report_title='加权 GPA 排名'
        result=db.execute(f'''SELECT s.id,s.name,c.name as class_name,ROUND(SUM(sc.numeric_score*sub.credit)/NULLIF(SUM(sub.credit),0),2) as gpa,ROUND(SUM(sub.credit),1) as total_credit
            FROM students s LEFT JOIN classes c ON s.class_id=c.id LEFT JOIN scores sc ON sc.student_id=s.id AND sc.numeric_score IS NOT NULL LEFT JOIN subjects sub ON sc.subject_id=sub.id AND sub.credit>0 WHERE 1=1{scope_sql} GROUP BY s.id HAVING total_credit>0 ORDER BY gpa DESC''',params).fetchall()
    elif report=='6':
        report_title='挂科名单'
        result=db.execute(f'''SELECT s.id,s.name,c.name as class_name,sub.name as subject_name,sc.raw_score,sc.numeric_score
            FROM scores sc JOIN students s ON sc.student_id=s.id LEFT JOIN classes c ON s.class_id=c.id JOIN subjects sub ON sc.subject_id=sub.id
            WHERE sc.numeric_score<60 AND sc.numeric_score IS NOT NULL{scope_sql} ORDER BY s.id,sub.id''',params).fetchall()
    db.close()
    return render_template('statistics.html',report=report,report_title=report_title,result=result,classes=classes,class_id=class_id)

# ═══════════════════════════════════════════
# 路由：批量录入（预览+确认）
# ═══════════════════════════════════════════

@app.route('/batch', methods=['GET','POST'])
@login_required(roles=['admin','teacher'])
def batch_scores():
    db=get_db(); subjects=db.execute('SELECT id,name,credit FROM subjects ORDER BY id').fetchall()
    result=None; subject_name=''; preview=None; selected_subject=None
    if request.method=='POST':
        subject_id=request.form.get('subject_id',type=int); raw_lines=request.form.get('lines','').strip()
        action=request.form.get('action','preview')
        if not subject_id or not raw_lines: flash('请选择科目并输入成绩数据！','error'); db.close(); return render_template('batch_scores.html',subjects=subjects,result=result,subject_name=subject_name,preview=preview,selected_subject=selected_subject)
        subj=db.execute('SELECT name FROM subjects WHERE id=?',(subject_id,)).fetchone()
        if not subj: flash('无效科目！','error'); db.close(); return render_template('batch_scores.html',subjects=subjects,result=result,subject_name=subject_name,preview=preview,selected_subject=selected_subject)
        subject_name=subj['name']; selected_subject=subject_id; role=session.get('role'); scope=session.get('scope')
        scope_sql,scope_params=get_scope_filter_sql(role,scope,'s')
        entries=[]; errors=[]
        for line in raw_lines.strip().split('\n'):
            line=line.strip()
            if not line: continue
            parts=line.split(None,1)
            if len(parts)!=2: errors.append(f'格式错误: {line}'); continue
            sid,score=parts[0].strip(),parts[1].strip()
            if len(sid)<10: sid='20181828'+sid
            check=db.execute(f'SELECT id,name FROM students WHERE id=?{scope_sql}',[sid]+scope_params).fetchone()
            if not check: errors.append(f'学号 {sid} 不存在或无权限'); continue
            cur=db.execute('SELECT raw_score FROM scores WHERE student_id=? AND subject_id=?',(sid,subject_id)).fetchone()
            cur_val=cur[0] if cur else ''
            entries.append({'sid':sid,'name':check['name'],'score':score,'current':cur_val})
        if action=='confirm':
            success=0; fail=0
            for e in entries:
                numeric=grade_to_numeric(e['score'])
                try:
                    db.execute('INSERT OR REPLACE INTO scores(student_id,subject_id,raw_score,numeric_score) VALUES(?,?,?,?)',(e['sid'],subject_id,e['score'],numeric))
                    db.commit(); success+=1
                except: fail+=1
            flash(f'批量录入完成！成功 {success} 条{", 失败 "+str(fail) if fail else ""}','success')
            result={'success':success,'fail':fail,'subject':subject_name}
            db.close(); return render_template('batch_scores.html',subjects=subjects,result=result,subject_name=subject_name,preview=None,selected_subject=selected_subject)
        else:
            preview={'entries':entries,'errors':errors,'subject':subject_name,'total':len(entries)}
    db.close()
    return render_template('batch_scores.html',subjects=subjects,result=result,subject_name=subject_name,preview=preview,selected_subject=selected_subject)

@app.route('/batch/confirm', methods=['POST'])
@login_required(roles=['admin','teacher'])
def batch_confirm():
    """兼容旧版 /batch/confirm 直接提交（无预览）"""
    db=get_db(); subject_id=request.form.get('subject_id')
    sids=request.form.getlist('student_id[]'); raws=request.form.getlist('raw_score[]')
    for sid,raw in zip(sids,raws):
        numeric=grade_to_numeric(raw)
        existing=db.execute('SELECT id FROM scores WHERE student_id=? AND subject_id=?',(sid,subject_id)).fetchone()
        if existing: db.execute('UPDATE scores SET raw_score=?,numeric_score=? WHERE id=?',(raw,numeric,existing['id']))
        else: db.execute('INSERT INTO scores(student_id,subject_id,raw_score,numeric_score) VALUES(?,?,?,?)',(sid,subject_id,raw,numeric))
    db.commit(); db.close()
    flash('批量录入完成！','success'); return redirect(url_for('student_list'))

# ═══════════════════════════════════════════
# 路由：用户管理
# ═══════════════════════════════════════════

@app.route('/users')
@login_required(roles=['admin'])
def user_list():
    db=get_db(); users=db.execute('SELECT id,username,role,scope FROM users ORDER BY id').fetchall(); db.close()
    return render_template('users.html',users=users)

@app.route('/user/add', methods=['POST'])
@login_required(roles=['admin'])
def user_add():
    db=get_db()
    db.execute('INSERT INTO users(username,password,role,scope) VALUES(?,?,?,?)',
               (request.form['username'],request.form['password'],request.form['role'],request.form.get('scope','')))
    db.commit(); db.close()
    flash('用户已添加','success'); return redirect(url_for('user_list'))

@app.route('/user/delete/<int:user_id>')
@login_required(roles=['admin'])
def user_delete(user_id):
    db=get_db(); user=db.execute('SELECT username FROM users WHERE id=?',(user_id,)).fetchone()
    if not user: flash('用户不存在！','error'); db.close(); return redirect(url_for('user_list'))
    if user['username']=='admin': flash('不能删除超级管理员！','error'); db.close(); return redirect(url_for('user_list'))
    db.execute('DELETE FROM users WHERE id=?',(user_id,)); db.commit(); db.close()
    flash('用户已删除','success'); return redirect(url_for('user_list'))

# For Vercel Python Runtime - WSGI handler
app = app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
