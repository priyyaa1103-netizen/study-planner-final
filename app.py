from flask import Flask, request, redirect, session, render_template_string, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
from datetime import datetime, timedelta
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = 'study2026-super-secure-key-change-this-in-production'

# Create necessary folders
os.makedirs('static/uploads', exist_ok=True)

# Initialize SQLite Database
def init_db():
    conn = sqlite3.connect('/tmp/users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (email TEXT PRIMARY KEY, password TEXT, name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS goals 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  email TEXT, subject TEXT, goal TEXT, 
                  target_score INTEGER, study_hours INTEGER, 
                  progress INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reminders 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT, title TEXT, deadline TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Email Configuration - UPDATE THESE WITH YOUR GMAIL
GMAIL_USER = "your-gmail@gmail.com"  # Change this
GMAIL_PASS = "your-16-digit-app-password"  # Gmail App Password

def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASS)
        server.send_message(msg)
        server.quit()
        return True
    except:
        return False

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

def load_reminders_file():
    try:
        with open('static/reminders.json', 'r') as f:
            return json.load(f)
    except:
        return {}

def save_reminders_file(reminders):
    with open('static/reminders.json', 'w') as f:
        json.dump(reminders, f)

@app.route('/', methods=['GET', 'POST'])
def login():
    error = ""
    if request.method == 'POST':
        action = request.form.get('action', 'login')
        email = request.form['email'].lower()
        password = request.form['password']
        
        conn = get_db_connection()
        c = conn.cursor()
        
        if action == 'register':
            c.execute("SELECT email FROM users WHERE email=?", (email,))
            if c.fetchone():
                error = "❌ Email already registered!"
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
                error = "❌ Wrong email or password!"
    
    return render_login_page(error)
    
def render_login_page(error=""):
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Study Planner & Reminder App</title>
        <style>
            *{{margin:0;padding:0;box-sizing:border-box}}
            body{{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}}
            .login-box{{background:white;color:#333;padding:50px;border-radius:20px;box-shadow:0 20px 40px rgba(0,0,0,0.2);width:100%;max-width:420px}}
            .tabs{{display:flex;background:#f8f9fa;border-radius:12px;overflow:hidden;margin:30px 0}}
            .tab{{flex:1;padding:18px 10px;text-align:center;cursor:pointer;font-weight:600;transition:all 0.3s;font-size:16px}}
            .tab.active{{background:#667eea;color:white}}
            input{{width:100%;padding:15px;margin:10px 0;font-size:16px;border:2px solid #e1e5e9;border-radius:12px;box-sizing:border-box;transition:all 0.3s}}
            input:focus{{border-color:#667eea;outline:none;box-shadow:0 0 0 3px rgba(102,126,234,0.1)}}
            button{{width:100%;padding:16px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:12px;font-size:18px;font-weight:600;cursor:pointer;transition:all 0.3s;margin:5px 0}}
            button:hover{{transform:translateY(-2px);box-shadow:0 10px 25px rgba(102,126,234,0.4)}}
            .error{{background:#fee;color:#c53030;padding:12px;border-radius:8px;margin:15px 0;font-weight:500}}
            .demo{{text-align:center;margin-top:25px;font-size:14px;color:#666;padding:15px;background:#f8f9fa;border-radius:8px}}
            h1{{text-align:center;margin-bottom:30px;font-size:32px;color:#333}}
            .tabs-container{{margin:25px 0}}
        </style>
    </head>
    <body>
        <div class="login-box">
            <h1>🎓 Study Planner</h1>
            {f'<div class="error">{error}</div>' if error else ''}
            
            <!-- TABS KEELA VARUM -->
            <div class="tabs-container">
                <div class="tabs">
                    <div class="tab active" onclick="showTab('login')">🔐 Login</div>
                    <div class="tab" onclick="showTab('register')">➕ Register</div>
                </div>
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
            
            <div class="demo">
                Demo: test@test.com / 123456
            </div>
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
    </html>
    '''

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'): 
        return redirect('/')
    
    # Check notifications
    notifications = check_notifications()
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard - Study Planner</title>
        <style>
            *{{margin:0;padding:0;box-sizing:border-box}}
            body{{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:30px}}
            .container{{max-width:1000px;margin:0 auto;text-align:center}}
            h1{{font-size:42px;margin-bottom:10px;text-shadow:0 2px 10px rgba(0,0,0,0.3)}}
            h2{{font-size:24px;margin-bottom:40px;opacity:0.9}}
            .btn{{display:inline-block;padding:22px 45px;margin:15px;background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);color:white;text-decoration:none;border-radius:20px;font-size:22px;font-weight:600;box-shadow:0 12px 30px rgba(0,0,0,0.3);transition:all 0.3s;position:relative;overflow:hidden}}
            .btn:hover{{transform:translateY(-5px);box-shadow:0 20px 40px rgba(0,0,0,0.4)}}
            .btn.logout{{background:linear-gradient(135deg,#e74c3c,#c0392b)}}
            .notification{{background:rgba(231,76,60,0.9);padding:20px;border-radius:15px;margin:20px auto;font-size:20px;max-width:600px;box-shadow:0 10px 30px rgba(231,76,60,0.4)}}
            .welcome-card{{background:rgba(255,255,255,0.15);padding:40px;border-radius:25px;margin-bottom:40px;backdrop-filter:blur(15px);box-shadow:0 20px 40px rgba(0,0,0,0.2)}}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="welcome-card">
                <h1>Welcome {session['name']}! 🎓</h1>
                <h2>Study Planner & Reminder App</h2>
                {notifications}
            </div>
            <a href="/study" class="btn">📚 Study Dashboard</a>
            <a href="/goals" class="btn">🎯 Set Goal</a>
            <a href="/view-goals" class="btn">📊 View Goals</a>
            <a href="/reminders" class="btn">⏰ Reminders</a>
            <a href="/logout" class="btn logout">🚪 Logout</a>
        </div>
    </body>
    </html>
    '''

def check_notifications():
    conn = get_db_connection()
    c = conn.cursor()
    email = session.get('email', '')
    now = datetime.now()
    
    c.execute("SELECT * FROM reminders WHERE email=? AND datetime(deadline) <= datetime(?)", 
              (email, now.isoformat()))
    overdue = c.fetchall()
    
    notifications = ""
    for reminder in overdue:
        send_email(email, "🚨 Study Reminder - OVERDUE", 
                  f"Your reminder '{reminder['title']}' was due at {reminder['deadline']}!")
        notifications += f'<div class="notification">🚨 <strong>{reminder["title"]}</strong> - Deadline Passed!</div>'
    
    conn.close()
    return notifications

@app.route('/study')
def study():
    if not session.get('logged_in'): return redirect('/')
    return f'''
    <!DOCTYPE html>
    <html><head><title>Study Dashboard</title>
    <style>body{{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}}
    .btn{{padding:20px 40px;margin:15px;background:#50c878;color:white;text-decoration:none;border-radius:15px;font-size:20px;display:inline-block;box-shadow:0 10px 25px rgba(80,200,120,0.4);transition:all 0.3s}}
    .btn:hover{{transform:translateY(-3px);box-shadow:0 15px 35px rgba(80,200,120,0.6)}}
    h1{{font-size:38px;margin-bottom:50px;text-shadow:0 2px 10px rgba(0,0,0,0.3)}}</style></head>
    <body>
    <h1>📚 Study Dashboard</h1>
    <a href="/year1" class="btn">🎓 1st Year</a>
    <a href="/year2" class="btn">🎓 2nd Year</a>
    <a href="/year3" class="btn">🎓 3rd Year</a>
    <br><a href="/dashboard" class="btn" style="background:#f39c12;margin-top:30px">← Back to Dashboard</a>
    </body></html>
    '''

# ===== 1st YEAR =====
@app.route('/year1')
def year1():
    if not session.get('logged_in'): return redirect('/')
    return '''
    <!DOCTYPE html><html><head><title>1st Year</title><style>body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}
    .btn{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}h1{font-size:32px;margin-bottom:40px}</style></head>
    <body><h1>📚 1st Year</h1><a href="/sem1" class="btn">Semester 1</a><a href="/sem2" class="btn">Semester 2</a>
    <br><a href="/study" class="btn" style="background:#f39c12">← Back</a></body></html>
    '''

@app.route('/sem1')
def sem1():
    if not session.get('logged_in'): return redirect('/')
    return '''
    <!DOCTYPE html><html><head><title>Semester 1</title><style>body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}
    .btn{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}h1{font-size:32px;margin-bottom:40px}</style></head>
    <body><h1>📖 Semester 1</h1>
    <a href="/subject/maths" class="btn">Mathematics</a>
    <a href="/subject/python" class="btn">Python</a>
    <a href="/subject/tamil" class="btn">Tamil</a>
    <a href="/subject/english" class="btn">English</a>
    <br><a href="/year1" class="btn" style="background:#f39c12">← Back</a></body></html>
    '''

@app.route('/sem2')
def sem2():
    if not session.get('logged_in'): return redirect('/')
    return '''
    <!DOCTYPE html><html><head><title>Semester 2</title><style>body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}
    .btn{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}h1{font-size:32px;margin-bottom:40px}</style></head>
    <body><h1>📖 Semester 2</h1>
    <a href="/subject/maths2" class="btn">Maths-II</a>
    <a href="/subject/physics" class="btn">Physics-II</a>
    <a href="/subject/tamil" class="btn">Tamil</a>
    <a href="/subject/english" class="btn">english</a>
    <br><a href="/year1" class="btn" style="background:#f39c12">← Back</a></body></html>
    '''

# ===== 2nd YEAR =====
@app.route('/year2')
def year2():
    if not session.get('logged_in'): return redirect('/')
    return '''
    <!DOCTYPE html><html><head><title>2nd Year</title><style>body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}
    .btn{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}h1{font-size:32px;margin-bottom:40px}</style></head>
    <body><h1>📚 2nd Year</h1><a href="/sem3" class="btn">Semester 3</a><a href="/sem4" class="btn">Semester 4</a>
    <br><a href="/study" class="btn" style="background:#f39c12">← Back</a></body></html>
    '''

@app.route('/sem3')
def sem3():
    if not session.get('logged_in'): return redirect('/')
    return '''
    <!DOCTYPE html><html><head><title>Semester 3</title><style>body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}
    .btn{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}h1{font-size:32px;margin-bottom:40px}</style></head>
    <body><h1>📖 Semester 3</h1>
    <a href="/subject/java programming" class="btn">Java Programming</a>
    <a href="/subject/statistics-1" class="btn">Statistics-1</a>
    <a href="/subject/tamil" class="btn">Tamil</a>
    <a href="/subject/english" class="btn">English</a>
    <br><a href="/year2" class="btn" style="background:#f39c12">← Back</a></body></html>
    '''

@app.route('/sem4')
def sem4():
    if not session.get('logged_in'): return redirect('/')
    return '''
    <!DOCTYPE html><html><head><title>Semester 4</title><style>body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}
    .btn{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}h1{font-size:32px;margin-bottom:40px}</style></head>
    <body><h1>📖 Semester 4</h1>
    <a href="/subject/data structures" class="btn">Data structures</a>
    <a href="/subject/statistics" class="btn">Statistics</a>
    <a href="/subject/tamil" class="btn">Tamil</a>
    <a href="/subject/english" class="btn">English</a>
    <br><a href="/year2" class="btn" style="background:#f39c12">← Back</a></body></html>
    '''

# ===== 3rd YEAR =====
@app.route('/year3')
def year3():
    if not session.get('logged_in'): return redirect('/')
    return '''
    <!DOCTYPE html><html><head><title>3rd Year</title><style>body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}
    .btn{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}h1{font-size:32px;margin-bottom:40px}</style></head>
    <body><h1>📚 3rd Year</h1><a href="/sem5" class="btn">Semester 5</a><a href="/sem6" class="btn">Semester 6</a>
    <br><a href="/study" class="btn" style="background:#f39c12">← Back</a></body></html>
    '''

@app.route('/sem5')
def sem5():
    if not session.get('logged_in'): return redirect('/')
    return '''
    <!DOCTYPE html><html><head><title>Semester 5</title><style>body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}
    .btn{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}h1{font-size:32px;margin-bottom:40px}</style></head>
    <body><h1>📖 Semester 5</h1>
    <a href="/subject/os" class="btn">Operating System</a>
    <a href="/subject/RDBMS" class="btn">Relational database management system</a>
    <a href="/subject/SE" class="btn">Software engineering</a>
    <a href="/subject/DMW" class="btn">Data mining and warehousing</a>
    <br><a href="/year3" class="btn" style="background:#f39c12">← Back</a></body></html>
    '''

@app.route('/sem6')
def sem6():
    if not session.get('logged_in'): return redirect('/')
    return '''
    <!DOCTYPE html><html><head><title>Semester 6</title><style>body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}
    .btn{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}h1{font-size:32px;margin-bottom:40px}</style></head>
    <body><h1>📖 Semester 6</h1>
    <a href="/subject/ASP.net" class="btn">Programming in ASP.net</a>
    <a href="/subject/DS" class="btn">Data science</a>
    <a href="/subject/CC" class="btn">Cloud computing</a>
    <br><a href="/year3" class="btn" style="background:#f39c12">← Back</a></body></html>
    '''

@app.route('/subject/<subject_name>')
def subject_notes(subject_name):
    if not session.get('logged_in'): return redirect('/')
    
    units_html = ''
    subject_folder = f"static/uploads/{subject_name}"
    os.makedirs(subject_folder, exist_ok=True)
    
    for i in range(1, 11):
        unit_file = f"{subject_folder}/unit{i}.pdf"
        upload_link = f"/upload/{subject_name}/unit{i}"
        has_file = os.path.exists(unit_file)
        
        units_html += f'''
        <div style="display:inline-block;margin:15px;background:rgba(255,255,255,0.15);padding:25px;border-radius:20px;width:220px;box-shadow:0 10px 30px rgba(0,0,0,0.2);backdrop-filter:blur(10px)">
            <h3 style="margin-bottom:15px">📚 Unit {i}</h3>
            <a href="{upload_link}" style="display:block;padding:12px;background:#3498db;color:white;text-decoration:none;border-radius:10px;margin:8px 0;font-weight:500">📤 Upload</a>
            {f'''
            <a href="/download/{subject_name}/unit{i}.pdf" target="_blank"
            style="display:block;padding:12px;background:#27ae60;color:white;text-decoration:none;border-radius:10px;margin:8px 0;font-weight:500">📥 Download</a>

            <a href="/delete/{subject_name}/unit{i}.pdf"
            style="display:block;padding:12px;background:#e74c3c;color:white;text-decoration:none;border-radius:10px;margin:8px 0;font-weight:500">🗑 Delete</a>
            ''' if has_file else '<p style="color:#f39c12;font-weight:500">No file uploaded</p>'}
    
    return f'''
    <!DOCTYPE html>
    <html><head><title>{subject_name.replace("-"," ").title()} Notes</title>
    <style>body{{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:30px}}
    .back-btn{{position:fixed;top:25px;left:25px;padding:15px 25px;background:#f39c12;color:white;text-decoration:none;border-radius:15px;font-size:18px;font-weight:600;box-shadow:0 5px 15px rgba(243,156,18,0.4);z-index:1000}}
    h1{{font-size:40px;margin:60px 0 40px 0;text-align:center;text-shadow:0 2px 10px rgba(0,0,0,0.3)}} .container{{max-width:1400px;margin:0 auto}}</style></head>
    <body>
    <a href="/dashboard" class="back-btn">← Dashboard</a>
    <h1>📚 {subject_name.replace("-"," ").title()}</h1>
    <div class="container">{units_html}</div>
    </body></html>
    '''

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
                return f'''
                <div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;display:flex;align-items:center;justify-content:center;flex-direction:column;padding:50px;text-align:center">
                <h1 style="font-size:50px;color:#2ecc71">✅ Success!</h1>
                <p style="font-size:24px;margin:30px 0">{subject_name.title()} Unit {unit_num} uploaded!</p>
                <a href="/subject/{subject_name}" style="padding:20px 50px;background:#27ae60;color:white;text-decoration:none;border-radius:15px;font-size:22px;font-weight:600">← Back to {subject_name.title()}</a>
                </div>
                '''
        return '<h1 style="color:red;text-align:center">No file selected!</h1>'
    
    return f'''
    <!DOCTYPE html>
    <html><head><title>Upload {subject_name.title()} Unit {unit_num}</title>
    <style>body{{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}}
    input[type=file]{{width:500px;padding:20px;margin:30px;border-radius:15px;border:none;background:rgba(255,255,255,0.95);font-size:18px}}
    button{{padding:25px 60px;margin:30px;background:#50c878;color:white;border:none;border-radius:20px;font-size:24px;cursor:pointer;font-weight:600;box-shadow:0 10px 30px rgba(80,200,120,0.4)}}
    h1{{font-size:42px;margin-bottom:40px}}</style></head>
    <body>
    <h1>📤 Upload Unit {unit_num}</h1>
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="file" accept=".pdf" required>
        <br><button type="submit">✅ Upload PDF</button>
    </form>
    <a href="/subject/{subject_name}" style="color:#3498db;font-size:22px;font-weight:600">← Back to {subject_name.title()}</a>
    </body></html>
    '''

@app.route('/download/<subject_name>/<filename>')
def download_file(subject_name, filename):
    return send_from_directory(f'static/uploads/{subject_name}', filename)
    
@app.route('/delete/<subject_name>/<filename>')
def delete_file(subject_name, filename):
    if not session.get('logged_in'):
        return redirect('/')

    file_path = f'static/uploads/{subject_name}/{filename}'

    if os.path.exists(file_path):
        os.remove(file_path)

    return redirect(f'/subject/{subject_name}')

@app.route('/goals', methods=['GET', 'POST'])
def goals():
    if not session.get('logged_in'): return redirect('/')
    
    if request.method == 'POST':
        conn = get_db_connection()
        conn.execute('''INSERT INTO goals (email, subject, goal, target_score, study_hours) 
                       VALUES (?, ?, ?, ?, ?)''', 
                    (session['email'], request.form['subject'], 
                     request.form['goal'], request.form['target_score'], 
                     request.form['study_hours']))
        conn.commit()
        conn.close()
        return redirect('/view-goals')
    
    return f'''
    <!DOCTYPE html>
    <html><head><title>Set Goals</title>
    <style>body{{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}}
    .form-box{{background:rgba(255,255,255,0.15);padding:50px;border-radius:25px;margin:50px auto;max-width:600px;box-shadow:0 20px 40px rgba(0,0,0,0.2);backdrop-filter:blur(15px)}}
    input{{width:100%;padding:18px;margin:15px 0;font-size:18px;border-radius:12px;border:none;box-shadow:0 5px 15px rgba(0,0,0,0.1)}}
    button{{width:100%;padding:20px;background:#50c878;color:white;border:none;border-radius:15px;font-size:22px;font-weight:600;cursor:pointer;margin-top:20px;box-shadow:0 10px 30px rgba(80,200,120,0.4)}}
    h1{{font-size:42px;margin-bottom:30px}}</style></head>
    <body>
    <div class="form-box">
        <h1>🎯 Set Study Goals</h1>
        <form method="POST">
            <input name="subject" placeholder="Subject (ex: Mathematics)" required>
            <input name="goal" placeholder="Goal Description" required>
            <input name="target_score" type="number" placeholder="Target Score (ex: 90)" required>
            <input name="study_hours" type="number" placeholder="Study Hours Target" required>
            <button type="submit">✅ Save Goal</button>
        </form>
    </div>
    <a href="/dashboard" style="position:fixed;top:30px;left:30px;color:white;font-size:20px;font-weight:600;text-decoration:none">← Dashboard</a>
    </body></html>
    '''

@app.route('/view-goals')
def view_goals():
    if not session.get('logged_in'): return redirect('/')
    
    conn = get_db_connection()
    goals = conn.execute('SELECT * FROM goals WHERE email=?', (session['email'],)).fetchall()
    conn.close()
    
    goals_html = ''
    for goal in goals:
        progress_width = min(goal['progress'] * 5, 100)
        goals_html += f'''
        <div style="background:rgba(255,255,255,0.15);padding:30px;margin:20px;border-radius:20px;box-shadow:0 15px 35px rgba(0,0,0,0.2);backdrop-filter:blur(10px)">
            <h3 style="margin-bottom:15px">📚 {goal['subject']}</h3>
            <p><strong>Goal:</strong> {goal['goal']}</p>
            <p><strong>Target:</strong> {goal['target_score']}% | <strong>Hours:</strong> {goal['study_hours']}h</p>
            <div style="background:#e1e8ed;height:25px;border-radius:15px;overflow:hidden;margin:20px 0">
                <div style="background:#2ecc71;width:{progress_width}%;height:100%;transition:all 0.3s"></div>
            </div>
            <p style="font-size:20px;font-weight:600">Progress: {goal['progress']}%</p>
            <a href="/delete-goal/{goal['id']}"
            style="display:inline-block;padding:10px 20px;background:#e74c3c;color:white;text-decoration:none;border-radius:10px;margin-top:10px">
            🗑 Delete Goal
            </a>
        </div>
        '''
    
    return f'''
    <!DOCTYPE html>
    <html><head><title>Your Goals</title>
    <style>body{{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px}}
    .container{{max-width:900px;margin:0 auto}}</style></head>
    <body>
    <div class="container">
        <h1 style="font-size:42px;text-align:center;margin-bottom:50px">📊 Your Goals</h1>
        {goals_html or '<div style="text-align:center;font-size:28px;padding:80px;background:rgba(255,255,255,0.1);border-radius:25px"><p>No goals set yet!</p><a href="/goals" style="color:#f1c40f;font-size:32px;font-weight:600">🎯 Set goals now!</a></div>'}
        <div style="text-align:center;margin-top:50px">
            <a href="/dashboard" style="padding:20px 50px;background:#f39c12;color:white;text-decoration:none;border-radius:20px;font-size:22px;font-weight:600;display:inline-block">← Back to Dashboard</a>
        </div>
    </div>
    </body></html>
    '''
@app.route('/delete-goal/<int:goal_id>')
def delete_goal(goal_id):
    if not session.get('logged_in'):
        return redirect('/')

    conn = get_db_connection()
    conn.execute("DELETE FROM goals WHERE id=? AND email=?", 
                 (goal_id, session['email']))
    conn.commit()
    conn.close()

    return redirect('/view-goals')

@app.route('/reminders', methods=['GET', 'POST'])
def reminders():
    if not session.get('logged_in'): return redirect('/')
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        deadline = datetime.now() + timedelta(hours=int(request.form['hours']))
        conn.execute('INSERT INTO reminders (email, title, deadline) VALUES (?, ?, ?)',
                    (session['email'], request.form['title'], deadline.isoformat()))
        conn.commit()
        return redirect('/reminders')
    
    reminders_list = conn.execute('SELECT * FROM reminders WHERE email=? ORDER BY deadline', 
                                 (session['email'],)).fetchall()
    conn.close()
    
    reminders_html = ''
    now = datetime.now()
    
    for r in reminders_list:
        deadline = datetime.fromisoformat(r['deadline'])
        time_left = deadline - now
        if time_left.total_seconds() > 0:
            status = f"⏰ Due in {int(time_left.total_seconds()//3600)}h"
            status_color = "orange"
        else:
            status = "🚨 OVERDUE"
            status_color = "#e74c3c"
        reminders_html += f'''
        <div style="background:{status_color};padding:25px;margin:20px;border-radius:20px;text-align:left;box-shadow:0 10px 30px rgba(0,0,0,0.3)">
        <h3 style="margin-bottom:10px">{status}</h3>
        <p><strong>{r['title']}</strong></p>
        <p style="opacity:0.9">Deadline: {deadline.strftime('%Y-%m-%d %H:%M')}</p>
        <a href="/delete-reminder/{r['id']}"
        style="display:inline-block;padding:8px 15px;background:#c0392b;color:white;text-decoration:none;border-radius:8px;margin-top:10px">
        🗑 Delete
        </a>
        </div>
        '''
       
    return f'''
    <!DOCTYPE html>
    <html><head><title>Reminders</title>
    <style>body{{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}}
    .form-box{{background:rgba(255,255,255,0.15);padding:40px;border-radius:25px;margin:0 auto 50px;max-width:500px;box-shadow:0 20px 40px rgba(0,0,0,0.2);backdrop-filter:blur(15px)}}
    input,select{{width:100%;padding:15px;margin:12px 0;border-radius:12px;border:none;font-size:16px}}
    button{{width:100%;padding:18px;background:#50c878;color:white;border:none;border-radius:15px;font-size:20px;font-weight:600;cursor:pointer;margin-top:15px}}</style></head>
    <body>
    <h1 style="font-size:42px;margin-bottom:30px">⏰ Your Reminders</h1>
    
    <div class="form-box">
        <h3 style="margin-bottom:25px;font-size:24px">➕ Add New Reminder</h3>
        <form method="POST">
            <input name="title" placeholder="Reminder title (ex: Exam tomorrow)" required>
            <select name="hours">
                <option value="1">1 hour</option>
                <option value="6">6 hours</option>
                <option value="24">1 day</option>
                <option value="48">2 days</option>
                <option value="168">1 week</option>
            </select>
            <button type="submit">✅ Set Reminder</button>
        </form>
    </div>
    
    {reminders_html or '<p style="font-size:28px">No reminders set. Add one above! 🎯</p>'}
    
    <a href="/dashboard" style="padding:25px 60px;background:#f39c12;color:white;text-decoration:none;border-radius:20px;font-size:24px;font-weight:600;display:inline-block">← Dashboard</a>
    </body></html>
    '''

@app.route('/delete-reminder/<int:reminder_id>')
def delete_reminder(reminder_id):
    if not session.get('logged_in'):
        return redirect('/')

    conn = get_db_connection()
    conn.execute("DELETE FROM reminders WHERE id=? AND email=?", 
                 (reminder_id, session['email']))
    conn.commit()
    conn.close()

    return redirect('/reminders')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)




