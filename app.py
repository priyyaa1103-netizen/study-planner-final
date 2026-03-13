from flask import Flask, request, redirect, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'study2026-super-secure-key-change-in-prod'

# Folders create pannunga
os.makedirs('static/uploads', exist_ok=True)

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (email TEXT PRIMARY KEY, password TEXT, name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS goals 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  email TEXT, subject TEXT, goal TEXT, 
                  target_score INTEGER, progress INTEGER DEFAULT 0,
                  max_score INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS files 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT, subject TEXT, filename TEXT, 
                  upload_date TEXT)''')
    conn.commit()
    conn.close()
init_db()

def get_db():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

# ============= LOGIN/REGISTER =============
@app.route('/', methods=['GET', 'POST'])
def login():
    error = ""
    if request.method == 'POST':
        action = request.form.get('action', 'login')
        email = request.form['email'].lower()
        password = request.form['password']
        
        conn = get_db()
        c = conn.cursor()
        
        if action == 'register':
            c.execute("SELECT email FROM users WHERE email=?", (email,))
            if c.fetchone():
                error = "❌ Email already exists!"
            else:
                name = email.split('@')[0].title()
                hashed_pw = generate_password_hash(password)
                c.execute("INSERT INTO users (email, password, name) VALUES (?, ?, ?)", 
                         (email, hashed_pw, name))
                conn.commit()
                session['logged_in'] = True
                session['email'] = email
                session['name'] = name
                conn.close()
                return redirect('/dashboard')
        
        elif action == 'login':
            c.execute("SELECT * FROM users WHERE email=?", (email,))
            user = c.fetchone()
            conn.close()
            if user and check_password_hash(user['password'], password):
                session['logged_in'] = True
                session['email'] = email
                session['name'] = user['name']
                return redirect('/dashboard')
            else:
                error = "❌ Wrong email/password!"
    
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>Study Planner</title>
    <style>
    *{margin:0;padding:0;box-sizing:border-box}
    body{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;display:flex;align-items:center;justify-content:center}
    .box{background:white;padding:50px;border-radius:20px;box-shadow:0 20px 40px rgba(0,0,0,0.3);max-width:400px;width:100%}
    .tabs{display:flex;background:#f8f9fa;border-radius:12px;overflow:hidden;margin-bottom:30px}
    .tab{padding:18px 10px;text-align:center;cursor:pointer;font-weight:600;transition:all 0.3s;flex:1}
    .tab.active{background:#667eea;color:white}
    input{width:100%;padding:15px;margin:10px 0;border:2px solid #e1e5e9;border-radius:12px;font-size:16px;box-sizing:border-box}
    input:focus{border-color:#667eea;outline:none;box-shadow:0 0 0 3px rgba(102,126,234,0.1)}
    button{width:100%;padding:16px;background:linear-gradient(135deg,#667eea,#764ba2);color:white;border:none;border-radius:12px;font-size:18px;font-weight:600;cursor:pointer;transition:all 0.3s}
    button:hover{transform:translateY(-2px);box-shadow:0 10px 25px rgba(102,126,234,0.4)}
    .error{background:#fee;color:#c53030;padding:12px;border-radius:8px;margin:15px 0;font-weight:500}
    h1{text-align:center;margin-bottom:30px;font-size:32px;color:#333}
    .demo{text-align:center;margin-top:25px;font-size:14px;color:#666;padding:15px;background:#f8f9fa;border-radius:8px}
    </style>
    </head>
    <body>
        <div class="box">
            <h1>🎓 Study Planner</h1>
            ''' + (f'<div class="error">{error}</div>' if error else '') + '''
            <div class="tabs">
                <div class="tab active" onclick="showTab('login')">🔐 Login</div>
                <div class="tab" onclick="showTab('register')">➕ Register</div>
            </div>
            <form method="POST" id="login-form">
                <input type="hidden" name="action" value="login">
                <input type="email" name="email" placeholder="your-email@gmail.com" required>
                <input type="password" name="password" placeholder="Password" required>
                <button>Login</button>
            </form>
            <form method="POST" id="register-form" style="display:none">
                <input type="hidden" name="action" value="register">
                <input type="email" name="email" placeholder="your-email@gmail.com" required>
                <input type="password" name="password" placeholder="Create Password" required>
                <button>Create Account</button>
            </form>
            <div class="demo">Demo: test@test.com / 123456</div>
        </div>
        <script>
        function showTab(tab) {
            document.getElementById('login-form').style.display = tab === 'login' ? 'block' : 'none';
            document.getElementById('register-form').style.display = tab === 'register' ? 'block' : 'none';
            document.querySelectorAll('.tab')[0].classList.toggle('active', tab === 'login');
            document.querySelectorAll('.tab')[1].classList.toggle('active', tab === 'register');
        }
        </script>
    </body></html>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ============= DASHBOARD =============
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'): return redirect('/')
    return '''
    <!DOCTYPE html>
    <html><head><title>Dashboard</title>
    <style>
    *{margin:0;padding:0;box-sizing:border-box}
    body{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:30px}
    .container{max-width:1000px;margin:0 auto;text-align:center}
    h1{font-size:42px;margin-bottom:10px}
    h2{font-size:24px;margin-bottom:40px}
    .btn{display:inline-block;padding:22px 45px;margin:15px;background:linear-gradient(135deg,#f093fb,#f5576c);color:white;text-decoration:none;border-radius:20px;font-size:22px;font-weight:600;box-shadow:0 12px 30px rgba(0,0,0,0.3);transition:all 0.3s}
    .btn:hover{transform:translateY(-5px)}
    .btn.logout{background:linear-gradient(135deg,#e74c3c,#c0392b)}
    .welcome{background:rgba(255,255,255,0.15);padding:40px;border-radius:25px;margin-bottom:40px}
    </style></head>
    <body>
    <div class="container">
        <div class="welcome">
            <h1>Welcome ''' + session['name'] + '''! 🎓</h1>
            <h2>Study Planner App</h2>
        </div>
        <a href="/study" class="btn">📚 Study</a>
        <a href="/goals" class="btn">🎯 Goals</a>
        <a href="/view-goals" class="btn">📊 Progress</a>
        <a href="/myfiles" class="btn">📁 Files</a>
        <a href="/logout" class="btn logout">🚪 Logout</a>
    </div></body></html>
    '''

# ============= STUDY NAVIGATION =============
@app.route('/study')
def study():
    if not session.get('logged_in'): return redirect('/')
    return '''
    <!DOCTYPE html><html><head><title>Study</title>
    <style>body{font-family:'Segoe UI';background:linear-gradient(135deg,#667eea,#764ba2);color:white;min-height:100vh;padding:50px;text-align:center}
    .container{max-width:800px;margin:0 auto}
    h1{font-size:48px;margin-bottom:60px}
    .btn{display:inline-block;padding:25px 50px;margin:20px;background:#50c878;color:white;text-decoration:none;border-radius:20px;font-size:24px;font-weight:600;box-shadow:0 15px 35px rgba(80,200,120,0.4);transition:all 0.3s}
    .btn:hover{transform:translateY(-5px);box-shadow:0 20px 45px rgba(80,200,120,0.6)}
    .back{position:fixed;top:25px;left:25px;padding:18px 30px;background:#f39c12;color:white;text-decoration:none;border-radius:18px;font-size:20px;font-weight:600}</style>
    </head><body>
    <a href="/dashboard" class="back">← Dashboard</a>
    <div class="container">
        <h1>📚 Study Dashboard</h1>
        <a href="/year1" class="btn">1st Year 🎓</a>
        <a href="/year2" class="btn">2nd Year 🎓</a>
        <a href="/year3" class="btn">3rd Year 🎓</a>
    </div></body></html>
    '''

# Year 1,2,3 + Semesters (shortened for space - add similar routes)
@app.route('/year1')
def year1(): return year_page("1st Year", "/sem1", "/sem2")
@app.route('/year2')
def year2(): return year_page("2nd Year", "/sem3", "/sem4") 
@app.route('/year3')
def year3(): return year_page("3rd Year", "/sem5", "/sem6")

def year_page(title, sem1, sem2):
    if not session.get('logged_in'): return redirect('/')
    return f'''
    <!DOCTYPE html><html><head><title>{title}</title>
    <style>body{{font-family:'Segoe UI';background:linear-gradient(135deg,#667eea,#764ba2);color:white;min-height:100vh;padding:50px;text-align:center}}
    .btn{{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}}h1{{font-size:32px;margin-bottom:40px}}</style></head>
    <body><h1>📚 {title}</h1>
    <a href="{sem1}" class="btn">Semester 1</a><a href="{sem2}" class="btn">Semester 2</a>
    <br><a href="/study" class="btn" style="background:#f39c12">← Back</a></body></html>
    '''

@app.route('/sem1')
def sem1():
    if not session.get('logged_in'): return redirect('/')
    return subjects_page("Semester 1", 
        [('maths-1', 'Mathematics-1'), ('python', 'Python'), 
         ('tamil-1', 'Tamil-1'), ('english-1', 'English-1')])

# Add sem2, sem3, sem4, sem5, sem6 similarly...

def subjects_page(title, subjects):
    if not session.get('logged_in'): return redirect('/')
    btns = ''.join([f'<a href="/subject/{slug}" class="btn">{name}</a>' for slug, name in subjects])
    return f'''
    <!DOCTYPE html><html><head><title>{title}</title>
    <style>body{{font-family:'Segoe UI';background:linear-gradient(135deg,#667eea,#764ba2);color:white;min-height:100vh;padding:50px;text-align:center}}
    .btn{{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}}h1{{font-size:32px;margin-bottom:40px}}</style></head>
    <body><h1>📖 {title}</h1>{btns}
    <br><a href="/year1" class="btn" style="background:#f39c12">← Back</a></body></html>
    '''

@app.route('/subject/<subject>')
def subject(subject):
    if not session.get('logged_in'): return redirect('/')
    conn = get_db()
    files = conn.execute('SELECT filename FROM files WHERE subject=? AND email=?', 
                        (subject, session['email'])).fetchall()
    conn.close()
    
    uploaded = [row['filename'] for row in files]
    units = ''
    
    for i in range(1, 11):
        filename = f"unit{i}.pdf"
        if filename in uploaded:
            units += f'<div style="background:rgba(0,255,0,0.2);padding:20px;margin:10px;border-radius:15px">📚 Unit {i} ✅ <a href="/view-pdf/{subject}/{filename}" target="_blank" style="color:white">View</a></div>'
        else:
            units += f'<div style="background:rgba(255,255,0,0.2);padding:20px;margin:10px;border-radius:15px">📚 Unit {i} <a href="/upload/{subject}/{i}" style="color:black;font-weight:bold">Upload PDF</a></div>'
    
    return f'''
    <!DOCTYPE html><html><head><title>{subject.replace("-", " ").title()}</title>
    <style>body{{background:linear-gradient(135deg,#667eea,#764ba2);color:white;min-height:100vh;padding:30px;font-family:'Segoe UI'}}.container{{max-width:800px;margin:0 auto}}.back{{position:fixed;top:20px;left:20px;padding:15px;background:#f39c12;color:white;text-decoration:none;border-radius:15px}}</style></head>
    <body><a href="/study" class="back">← Back</a>
    <div class="container"><h1 style="text-align:center;font-size:40px;margin:60px 0 40px">{subject.replace("-", " ").title()}</h1>
    {units}</div></body></html>
    '''

# ============= FILE UPLOAD =============
@app.route('/upload/<subject>/<unit>', methods=['GET', 'POST'])
def upload(subject, unit):
    if not session.get('logged_in'): return redirect('/')
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = f"unit{unit}.pdf"
            os.makedirs(f'static/uploads/{subject}', exist_ok=True)
            filepath = f'static/uploads/{subject}/{filename}'
            file.save(filepath)
            
            conn = get_db()
            conn.execute('INSERT OR REPLACE INTO files (email, subject, filename, upload_date) VALUES (?, ?, ?, ?)',
                        (session['email'], subject, filename, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            return '<h1 style="text-align:center;font-size:50px;margin-top:100px;color:#2ecc71">✅ Uploaded Successfully!</h1><script>setTimeout(() => location.href=`/subject/${subject}`, 2000)</script>'
    
    return '''
    <!DOCTYPE html><html><head><title>Upload</title>
    <style>body{background:linear-gradient(135deg,#667eea,#764ba2);color:white;min-height:100vh;display:flex;align-items:center;justify-content:center;font-family:'Segoe UI'}
    .form{background:rgba(255,255,255,0.1);padding:50px;border-radius:25px;text-align:center;box-shadow:0 20px 40px rgba(0,0,0,0.3)}
    input[type=file]{width:100%;padding:15px;margin:20px 0;border-radius:12px;background:#fff}
    button{width:100%;padding:20px;background:#50c878;color:white;border:none;border-radius:15px;font-size:20px;font-weight:600;cursor:pointer}</style></head>
    <body>
    <div class="form">
        <h1 style="font-size:40px;margin-bottom:30px">📤 Upload Unit PDF</h1>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="file" accept=".pdf" required>
            <button>Upload PDF</button>
        </form>
    </div></body></html>
    '''

@app.route('/view-pdf/<subject>/<filename>')
def view_pdf(subject, filename):
    if not session.get('logged_in'): return redirect('/')
    return send_from_directory(f'static/uploads/{subject}', filename, mimetype='application/pdf')

# ============= GOALS & QUIZ =============
@app.route('/goals', methods=['GET', 'POST'])
def goals():
    if not session.get('logged_in'): return redirect('/')
    if request.method == 'POST':
        conn = get_db()
        conn.execute('INSERT INTO goals (email, subject, goal, target_score) VALUES (?, ?, ?, ?)',
                    (session['email'], request.form['subject'], 
                     request.form['goal'], request.form['target_score']))
        conn.commit()
        conn.close()
        return redirect('/view-goals')
    
    return '''
    <!DOCTYPE html><html><head><title>Goals</title>
    <style>body{background:linear-gradient(135deg,#667eea,#764ba2);color:white;min-height:100vh;padding:50px;font-family:'Segoe UI';text-align:center}
    .form{background:rgba(255,255,255,0.15);padding:50px;border-radius:25px;margin:0 auto;max-width:600px;box-shadow:0 20px 40px rgba(0,0,0,0.2)}
    input{width:100%;padding:18px;margin:15px 0;font-size:18px;border-radius:12px;border:none;box-shadow:0 5px 15px rgba(0,0,0,0.1)}
    button{width:100%;padding:20px;background:#50c878;color:white;border:none;border-radius:15px;font-size:22px;font-weight:600;cursor:pointer;margin-top:20px}</style></head>
    <body>
    <div class="form">
        <h1 style="font-size:42px;margin-bottom:30px">🎯 Set Study Goals</h1>
        <form method="POST">
            <input name="subject" placeholder="Subject (ex: Mathematics)" required>
            <input name="goal" placeholder="Goal Description" required>
            <input name="target_score" type="number" placeholder="Target Score (90)" required>
            <button>✅ Save Goal</button>
        </form>
    </div>
    <a href="/dashboard" style="position:fixed;top:30px;left:30px;color:white;font-size:20px;font-weight:600;text-decoration:none">← Dashboard</a>
    </body></html>
    '''

@app.route('/view-goals')
def view_goals():
    if not session.get('logged_in'): return redirect('/')
    conn = get_db()
    goals = conn.execute('SELECT * FROM goals WHERE email=?', (session['email'],)).fetchall()
    conn.close()
    
    goals_html = ''
    for goal in goals:
        quiz_btn = f'<a href="/quiz/{goal["id"]}" style="padding:12px 25px;background:#e74c3c;color:white;text-decoration:none;border-radius:10px;font-weight:600">🧠 Take Quiz</a>'
        goals_html += f'''
        <div style="background:rgba(255,255,255,0.15);padding:30px;margin:20px;border-radius:20px">
            <h3 style="font-size:28px;margin-bottom:10px">{goal["subject"]}</h3>
            <p style="font-size:18px;margin-bottom:15px">{goal["goal"]}</p>
            <div style="font-size:24px;margin-bottom:20px">
                Progress: <span style="color:#2ecc71;font-size:28px;font-weight:700">{goal["progress"]}%</span>
                | Target: {goal["target_score"]}
            </div>
            {quiz_btn}
        </div>
        '''
    
    return f'''
    <!DOCTYPE html><html><head><title>Goals</title>
    <style>body{{background:linear-gradient(135deg,#667eea,#764ba2);color:white;min-height:100vh;padding:30px;font-family:'Segoe UI'}}
    .container{{max-width:900px;margin:0 auto}}.back{{position:fixed;top:20px;left:20px;padding:15px;background:#f39c12;color:white;text-decoration:none;border-radius:15px;font-weight:600}}</style></head>
    <body>
    <a href="/dashboard" class="back">← Dashboard</a>
    <div class="container">
        <h1 style="text-align:center;font-size:42px;margin:80px 0 50px">📊 Your Study Goals</h1>
        {goals_html or '<p style="text-align:center;font-size:28px;color:#f1c40f;padding:80px;background:rgba(255,255,255,0.1);border-radius:25px">No goals set! <a href="/goals" style="color:#fff;font-weight:600">Set goals →</a></p>'}
    </div></body></html>
    '''

@app.route('/quiz/<int:goal_id>', methods=['GET', 'POST'])
def quiz(goal_id):
    if not session.get('logged_in'): return redirect('/')
    
    conn = get_db()
    goal = conn.execute('SELECT * FROM goals WHERE id=? AND email=?', 
                       (goal_id, session['email'])).fetchone()
    conn.close()
    
    if not goal: return redirect('/view-goals')
    
    # Simple quiz questions
    questions = [
        {"q": "Basic concept?", "options": ["A", "B", "C", "D"], "ans": "A"},
        {"q": "Main topic?", "options": ["Opt1", "Opt2", "Opt3", "Opt4"], "ans": "Opt1"},
        {"q": "Key principle?", "options": ["A", "B", "C", "D"], "ans": "A"},
        {"q": "Definition?", "options": ["Opt1", "Opt2", "Opt3", "Opt4"], "ans": "Opt1"},
        {"q": "Core idea?", "options": ["A", "B", "C", "D"], "ans": "A"},
        {"q": "Main principle?", "options": ["Opt1", "Opt2", "Opt3", "Opt4"], "ans": "Opt1"},
        {"q": "Key topic?", "options": ["A", "B", "C", "D"], "ans": "A"},
        {"q": "Basic Q?", "options": ["Opt1", "Opt2", "Opt3", "Opt4"], "ans": "Opt1"},
        {"q": "Core concept?", "options": ["A", "B", "C", "D"], "ans": "A"},
        {"q": "Final Q?", "options": ["Opt1", "Opt2", "Opt3", "Opt4"], "ans": "Opt1"}
    ]
    
    if request.method == 'POST':
        score = sum(1 for i in range(10) if request.form.get(f'q{i}') == questions[i]['ans'])
        progress_increase = score * 10
        new_progress = min(goal['progress'] + progress_increase, 100)
        conn = get_db()
        conn.execute('UPDATE goals SET progress=?, max_score=? WHERE id=? AND email=?',
                    (new_progress, score, goal_id, session['email']))
        conn.commit()
        conn.close()
        
        return f'''
        <!DOCTYPE html><html><head><title>Result</title>
        <style>body{{background:linear-gradient(135deg,#667eea,#764ba2);color:white;min-height:100vh;padding:50px;text-align:center;font-family:'Segoe UI'}}
        .result{{background:rgba(255,255,255,0.15);padding:60px;border-radius:25px;margin:50px auto;max-width:600px;box-shadow:0 20px 40px rgba(0,0,0,0.2)}}
        .score{{font-size:48px;margin:30px 0;color:#2ecc71;font-weight:700}}</style></head>
        <body><div class="result">
        <h1>🎉 Quiz Complete!</h1>
        <div class="score">Score: {score}/10</div>
        <p style="font-size:24px">Progress +{progress_increase}%!</p>
        <p style="font-size:20px">Total: {new_progress}%</p>
        <a href="/view-goals" style="padding:20px 50px;background:#50c878;color:white;text-decoration:none;border-radius:20px;font-size:24px;font-weight:600;display:inline-block">📊 View Goals</a>
        </div></body></html>
        '''
    
    # Quiz form
    qhtml = ''
    for i, q in enumerate(questions):
        opts = ''.join(f'<label style="display:block;margin:8px 0"><input type="radio" name="q{i}" value="{opt}" required> {opt}</label>' for opt in q['options'])
        qhtml += f'<div style="background:rgba(255,255,255,0.1);padding:20px;margin:20px 0;border-radius:15px"><p style="font-size:20px;margin-bottom:15px"><strong>Q{i+1}:</strong> {q["q"]}</p>{opts}</div>'
    
    return f'''
    <!DOCTYPE html><html><head><title>{goal["subject"]} Quiz</title>
    <style>body{{background:linear-gradient(135deg,#667eea,#764ba2);color:white;min-height:100vh;padding:50px;font-family:'Segoe UI'}}
    .quiz{{max-width:800px;margin:0 auto;background:rgba(255,255,255,0.1);padding:40px;border-radius:25px;box-shadow:0 20px 40px rgba(0,0,0,0.2)}}
    input[type=radio]{{margin-right:10px;transform:scale(1.2)}}</style></head>
    <body>
    <div class="quiz">
        <h1 style="text-align:center;font-size:42px;margin-bottom:30px">🧠 {goal["subject"]} Quiz</h1>
        <p style="text-align:center;font-size:20px;margin-bottom:40px">10 questions = 10% progress each</p>
        <form method="POST">{qhtml}
        <button style="width:100%;padding:20px;background:#50c878;color:white;border:none;border-radius:20px;font-size:24px;font-weight:600;margin-top:30px;cursor:pointer">✅ Submit Quiz</button>
        </form>
    </div></body></html>
    '''

@app.route('/myfiles')
def myfiles():
    if not session.get('logged_in'): return redirect('/')
    # List all uploaded files (implementation similar to above)
    return '''
    <!DOCTYPE html><html><head><title>My Files</title>
    <style>body{background:linear-gradient(135deg,#667eea,#764ba2);color:white;min-height:100vh;padding:30px;font-family:'Segoe UI'}
    .container{max-width:1000px;margin:0 auto}</style></head>
    <body><div class="container">
    <h1 style="text-align:center;font-size:42px;margin:80px 0 40px">📁 My Files</h1>
    <p style="text-align:center;font-size:24px">File upload working! Check subjects to upload.</p>
    <a href="/dashboard" style="display:block;text-align:center;margin:50px 0;padding:20px 50px;background:#f39c12;color:white;text-decoration:none;border-radius:20px;font-size:24px;width:300px;margin:50px auto">← Dashboard</a>
    </div></body></html>
    '''

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
