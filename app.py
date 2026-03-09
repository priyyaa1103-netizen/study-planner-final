from flask import Flask, request, redirect, session, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta
import sqlite3

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'study2026-super-secure-key')

# Create folders
os.makedirs('static/uploads', exist_ok=True)

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (email TEXT PRIMARY KEY, password TEXT, name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS goals 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  email TEXT, subject TEXT, goal TEXT, 
                  target_score INTEGER, study_hours TEXT, 
                  progress INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reminders 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT, title TEXT, deadline TEXT)''')
    conn.commit()
    conn.close()

if not os.path.exists('users.db'):
    init_db()

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

def render_login_page(error=""):
    return f'''
<!DOCTYPE html>
<html>
<head>
    <title>Study Planner</title>
    <style>
        *{{margin:0;padding:0;box-sizing:border-box}}
        body{{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}}
        .login-box{{background:white;color:#333;padding:50px;border-radius:20px;box-shadow:0 20px 40px rgba(0,0,0,0.2);width:100%;max-width:420px}}
        .tabs{{display:flex;background:#f8f9fa;border-radius:12px;overflow:hidden;margin:30px 0}}
        .tab{{flex:1;padding:18px 10px;text-align:center;cursor:pointer;font-weight:600;transition:all 0.3s;font-size:16px}}
        .tab.active{{background:#667eea;color:white}}
        input{{width:100%;padding:15px;margin:10px 0;font-size:16px;border:2px solid #e1e5e9;border-radius:12px;transition:all 0.3s}}
        input:focus{{border-color:#667eea;outline:none;box-shadow:0 0 0 3px rgba(102,126,234,0.1)}}
        button{{width:100%;padding:16px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:12px;font-size:18px;font-weight:600;cursor:pointer;transition:all 0.3s;margin:5px 0}}
        button:hover{{transform:translateY(-2px);box-shadow:0 10px 25px rgba(102,126,234,0.4)}}
        .error{{background:#fee;color:#c53030;padding:12px;border-radius:8px;margin:15px 0;font-weight:500}}
        .demo{{text-align:center;margin-top:25px;font-size:14px;color:#666;padding:15px;background:#f8f9fa;border-radius:8px}}
        h1{{text-align:center;margin-bottom:30px;font-size:32px;color:#333}}
    </style>
</head>
<body>
    <div class="login-box">
        <h1>🎓 Study Planner</h1>
        {f'<div class="error">{error}</div>' if error else ''}
        
        <div class="tabs">
            <div class="tab active" onclick="showTab('login')">🔐 Login</div>
            <div class="tab" onclick="showTab('register')">➕ Register</div>
        </div>
        
        <form method="POST" id="login-form">
            <input type="hidden" name="action" value="login">
            <input type="email" name="email" placeholder="your-email@gmail.com" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        
        <form method="POST" id="register-form" style="display:none">
            <input type="hidden" name="action" value="register">
            <input type="email" name="email" placeholder="your-email@gmail.com" required>
            <input type="password" name="password" placeholder="Create Password" required>
            <button type="submit">Create Account</button>
        </form>
        
        <div class="demo">Demo: test@test.com / 123456</div>
    </div>
    <script>
    function showTab(tab) {{
        document.getElementById('login-form').style.display = tab === 'login' ? 'block' : 'none';
        document.getElementById('register-form').style.display = tab === 'register' ? 'block' : 'none';
        document.querySelectorAll('.tab')[0].classList.toggle('active', tab === 'login');
        document.querySelectorAll('.tab')[1].classList.toggle('active', tab === 'register');
    }}
    </script>
</body>
</html>'''

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        action = request.form.get('action', 'login')
        email = request.form['email'].lower().strip()
        password = request.form['password']
        
        conn = get_db_connection()
        c = conn.cursor()
        
        if action == 'register':
            c.execute("SELECT email FROM users WHERE email=?", (email,))
            if c.fetchone():
                conn.close()
                return render_login_page("❌ Email already registered!")
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
            if email == 'test@test.com' and password == '123456':
                session['logged_in'] = True
                session['email'] = email
                session['name'] = 'Demo User'
                return redirect('/dashboard')
            
            c.execute("SELECT * FROM users WHERE email=?", (email,))
            user = c.fetchone()
            conn.close()
            
            if user and check_password_hash(user['password'], password):
                session['logged_in'] = True
                session['email'] = email
                session['name'] = user['name']
                return redirect('/dashboard')
            else:
                return render_login_page("❌ Wrong email or password!")
    
    return render_login_page()

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'): 
        return redirect('/')
    return f'''
<!DOCTYPE html>
<html><head><title>Dashboard</title>
<style>body{{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center;font-family:'Segoe UI',sans-serif}}
.btn{{display:inline-block;padding:20px 40px;margin:15px;background:#50c878;color:white;text-decoration:none;border-radius:15px;font-size:20px;box-shadow:0 10px 25px rgba(80,200,120,0.4);transition:all 0.3s}}
.btn:hover{{transform:translateY(-3px)}}
h1{{font-size:42px;margin-bottom:20px}}</style></head>
<body>
<h1>Welcome {session.get("name", "User")}! 🎓</h1>
<a href="/study" class="btn">📚 Study Dashboard</a>
<a href="/goals" class="btn">🎯 Set Goal</a>
<a href="/view-goals" class="btn">📊 View Goals</a>
<a href="/reminders" class="btn">⏰ Reminders</a>
<a href="/logout" class="btn" style="background:#e74c3c">🚪 Logout</a>
</body></html>'''

@app.route('/study')
def study():
    if not session.get('logged_in'): return redirect('/')
    return f'''
<!DOCTYPE html>
<html><head><title>Study</title>
<style>body{{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center;font-family:'Segoe UI'}}
.btn{{padding:20px 40px;margin:15px;background:#50c878;color:white;text-decoration:none;border-radius:15px;font-size:20px;display:inline-block;box-shadow:0 10px 25px rgba(80,200,120,0.4)}}
h1{{font-size:38px;margin-bottom:50px}}</style></head>
<body>
<h1>📚 Study Dashboard</h1>
<a href="/year1" class="btn">🎓 1st Year</a>
<a href="/year2" class="btn">🎓 2nd Year</a>
<a href="/year3" class="btn">🎓 3rd Year</a>
<a href="/dashboard" class="btn" style="background:#f39c12">← Back</a>
</body></html>'''

@app.route('/year1')
def year1():
    if not session.get('logged_in'): return redirect('/')
    return f'''
<!DOCTYPE html><html><head><title>1st Year</title><style>body{{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center;font-family:'Segoe UI'}}
.btn{{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}}h1{{font-size:32px;margin-bottom:40px}}</style></head>
<body><h1>📚 1st Year</h1><a href="/sem1" class="btn">Semester 1</a><a href="/sem2" class="btn">Semester 2</a>
<a href="/study" class="btn" style="background:#f39c12">← Back</a></body></html>'''

@app.route('/sem1')
def sem1():
    if not session.get('logged_in'): return redirect('/')
    return f'''
<!DOCTYPE html><html><head><title>Sem 1</title><style>body{{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center;font-family:'Segoe UI'}}
.btn{{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}}h1{{font-size:32px;margin-bottom:40px}}</style></head>
<body><h1>📖 Semester 1</h1>
<a href="/subject/maths" class="btn">Mathematics</a>
<a href="/subject/python" class="btn">Python</a>
<a href="/subject/tamil" class="btn">Tamil</a>
<a href="/subject/english" class="btn">English</a>
<a href="/year1" class="btn" style="background:#f39c12">← Back</a></body></html>'''

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/subject/<subject_name>')
def subject_notes(subject_name):
    if not session.get('logged_in'): return redirect('/')
    units_html = ''
    subject_folder = f"static/uploads/{subject_name}"
    os.makedirs(subject_folder, exist_ok=True)
    
    for i in range(1, 6):
        unit_file = f"{subject_folder}/unit{i}.pdf"
        has_file = os.path.exists(unit_file)
        units_html += f'''
        <div style="display:inline-block;margin:15px;background:rgba(255,255,255,0.15);padding:25px;border-radius:20px;width:200px">
            <h3>📚 Unit {i}</h3>
            <a href="/upload/{subject_name}/unit{i}" style="display:block;padding:12px;background:#3498db;color:white;text-decoration:none;border-radius:10px;margin:8px 0">📤 Upload</a>
            {f'<a href="/download/{subject_name}/unit{i}.pdf" target="_blank" style="display:block;padding:12px;background:#27ae60;color:white;text-decoration:none;border-radius:10px;margin:8px 0">📥 Download</a>' if has_file else '<p style="color:#f39c12">No file</p>'}
        </div>'''
    
    return f'''
<!DOCTYPE html>
<html><head><title>{subject_name.title()}</title>
<style>body{{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:30px;font-family:'Segoe UI'}}
.back-btn{{position:fixed;top:25px;left:25px;padding:15px 25px;background:#f39c12;color:white;text-decoration:none;border-radius:15px;font-size:18px;z-index:1000}}
h1{{font-size:40px;margin:80px 0 40px 0;text-align:center}}.container{{max-width:1400px;margin:0 auto}}</style></head>
<body>
<a href="/dashboard" class="back-btn">← Dashboard</a>
<h1>📚 {subject_name.replace("-"," ").title()}</h1>
<div class="container">{units_html}</div>
</body></html>'''

@app.route('/upload/<subject_name>/<unit_num>', methods=['GET', 'POST'])
def upload_unit(subject_name, unit_num):
    if not session.get('logged_in'): return redirect('/')
    
    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                os.makedirs(f'static/uploads/{subject_name}', exist_ok=True)
                filename = secure_filename(f"unit{unit_num}.pdf")
                file.save(f'static/uploads/{subject_name}/{filename}')
                return f'<div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;display:flex;align-items:center;justify-content:center;flex-direction:column;padding:50px;text-align:center"><h1 style="font-size:50px;color:#2ecc71">✅ Success!</h1><p style="font-size:24px">Unit {unit_num} uploaded!</p><a href="/subject/{subject_name}" style="padding:20px 50px;background:#27ae60;color:white;text-decoration:none;border-radius:15px;font-size:22px">← Back</a></div>'
        return '<h1 style="color:red;text-align:center">No file selected!</h1>'
    
    return f'''
<!DOCTYPE html>
<html><head><title>Upload</title>
<style>body{{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center;font-family:'Segoe UI'}}
input[type=file]{{width:500px;padding:20px;margin:30px;border-radius:15px;border:none;background:rgba(255,255,255,0.95);font-size:18px}}
button{{padding:25px 60px;margin:30px;background:#50c878;color:white;border:none;border-radius:20px;font-size:24px;cursor:pointer;font-weight:600}}</style></head>
<body>
<h1>📤 Upload Unit {unit_num}</h1>
<form method="POST" enctype="multipart/form-data">
    <input type="file" name="file" accept=".pdf" required>
    <br><button type="submit">✅ Upload PDF</button>
</form>
<a href="/subject/{subject_name}" style="color:#3498db;font-size:22px">← Back</a>
</body></html>'''

@app.route('/download/<subject_name>/<filename>')
def download_file(subject_name, filename):
    return send_from_directory(f'static/uploads/{subject_name}', filename)

@app.route('/goals', methods=['GET', 'POST'])
def goals():
    if not session.get('logged_in'): return redirect('/')
    
    if request.method == 'POST':
        conn = get_db_connection()
        study_time = f"{request.form['hour']}:{request.form['minute']} {request.form['ampm']}"
        conn.execute('''INSERT INTO goals (email, subject, goal, target_score, study_hours) 
                       VALUES (?, ?, ?, ?, ?)''', 
                    (session['email'], request.form['subject'], 
                     request.form['goal'], request.form['target_score'], study_time))
        conn.commit()
        conn.close()
        return redirect('/view-goals')
    
    return f'''
<!DOCTYPE html>
<html><head><title>Goals</title>
<style>body{{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center;font-family:'Segoe UI'}}
.form-box{{background:rgba(255,255,255,0.15);padding:50px;border-radius:25px;margin:50px auto;max-width:600px;box-shadow:0 20px 40px rgba(0,0,0,0.2)}}
input,select{{width:100%;padding:18px;margin:15px 0;font-size:18px;border-radius:12px;border:none}}
button{{width:100%;padding:20px;background:#50c878;color:white;border:none;border-radius:15px;font-size:22px;font-weight:600;cursor:pointer;margin-top:20px}}</style></head>
<body>
<div class="form-box">
<h1>🎯 Set Study Goals</h1>
<form method="POST">
    <input name="subject" placeholder="Subject" required>
    <input name="goal" placeholder="Goal Description" required>
    <input name="target_score" type="number" placeholder="Target Score" required>
    <label>⏰ Study Hours:</label>
    <div style="display:flex;gap:10px">
        <select name="hour">{''.join([f'<option value="{i}">{i}</option>' for i in range(1,13)])}</select>
        <select name="minute">{''.join([f'<option value="{i:02d}">{i:02d}</option>' for i in range(0,60,5)])}</select>
        <select name="ampm"><option value="AM">AM</option><option value="PM">PM</option></select>
    </div>
    <button type="submit">✅ Save Goal</button>
</form>
<a href="/dashboard" style="position:fixed;top:30px;left:30px;color:white;font-size:20px">← Dashboard</a>
</div></body></html>'''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
