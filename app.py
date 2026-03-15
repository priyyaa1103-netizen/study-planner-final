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
import requests
from urllib.parse import urlencode

# ===== FIXED: Proper env vars =====
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = "https://study-planner-final-6k41.onrender.com/google-callback"
GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_PASS = os.getenv('GMAIL_PASS')

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'study2026-super-secure-key-change-this')

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
                  target_score INTEGER, progress INTEGER DEFAULT 0,
                  max_score INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reminders 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT, title TEXT, deadline TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS files 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT, subject TEXT, filename TEXT, 
                  upload_date TEXT)''')
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=['GET', 'POST'])
def login_register():
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        name = request.form.get('name', '').strip()
        action = request.form.get('action', 'login')
        
        conn = get_db_connection()
        
        if action == 'register':
            user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
            if user:
                conn.close()
                return render_login_page("❌ Email already registered!")
            
            hashed_pw = generate_password_hash(password)
            conn.execute("INSERT INTO users (email, password, name) VALUES (?, ?, ?)", 
                        (email, hashed_pw, name))
            conn.commit()
            conn.close()
            return render_login_page("✅ Account created! Please login.")
            
        else:  # login
            user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
            conn.close()
            
            if user and check_password_hash(user['password'], password):
                session['logged_in'] = True
                session['email'] = email
                session['name'] = user['name']
                return redirect('/dashboard')
            else:
                return render_login_page("❌ Wrong email or password!")
    
    return render_login_page()

def render_login_page(error=""):
    error_html = f'<div class="error">{error}</div>' if error else ''
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Study Planner</title>
        <style>
            *{margin:0;padding:0;box-sizing:border-box}
            body{font-family:'Segoe UI';background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
            .login-box{background:#fff;padding:50px;border-radius:25px;box-shadow:0 25px 50px rgba(0,0,0,0.3);width:90%;max-width:450px;text-align:center}
            .tabs{display:flex;margin:20px 0;border-radius:15px;overflow:hidden;box-shadow:0 5px 15px rgba(0,0,0,0.2)}
            .tab{flex:1;padding:18px;background:#f8fafc;cursor:pointer;border:none;font-weight:600;font-size:16px;transition:all 0.3s}
            .tab.active{background:#667eea;color:white}
            input{width:100%;padding:18px;margin:15px 0;border:2px solid #e1e5e9;border-radius:15px;font-size:17px;box-sizing:border-box}
            input:focus{border-color:#667eea;outline:none}
            button{width:100%;padding:20px;background:linear-gradient(135deg,#667eea,#764ba2);color:white;border:none;border-radius:15px;font-size:20px;font-weight:600;cursor:pointer;margin:10px 0;transition:all 0.3s}
            button:hover{transform:translateY(-2px);box-shadow:0 10px 25px rgba(102,126,234,0.4)}
            .error{background:#fee2e2;color:#dc2626;padding:15px;border-radius:10px;margin:20px 0;font-weight:500}
        </style>
    </head>
    <body>
        <div class="login-box">
            <h1 style="font-size:40px;margin-bottom:20px;color:#333">🎓 Study Planner</h1>
            {{ error_html|safe }}
            
            <div class="tabs">
                <button class="tab active" onclick="showTab('login')">Login</button>
                <button class="tab" onclick="showTab('register')">Register</button>
            </div>
            
            <form method="POST" id="loginForm">
                <input type="hidden" name="action" value="login">
                <input type="email" name="email" placeholder="your-email@gmail.com" required>
                <input type="password" name="password" placeholder="Enter password" required>
                <button type="submit">🚀 Login</button>
            </form>
            
            <form method="POST" id="registerForm" style="display:none">
                <input type="hidden" name="action" value="register">
                <input type="text" name="name" placeholder="Your Full Name" required>
                <input type="email" name="email" placeholder="your-email@gmail.com" required>
                <input type="password" name="password" placeholder="Create Password (6+ chars)" required>
                <button type="submit">✅ Create Account</button>
            </form>
        </div>
        
        <script>
        function showTab(tabName) {
            const loginForm = document.getElementById('loginForm');
            const registerForm = document.getElementById('registerForm');
            const tabs = document.querySelectorAll('.tab');
            
            if (tabName === 'login') {
                loginForm.style.display = 'block';
                registerForm.style.display = 'none';
            } else {
                loginForm.style.display = 'none';
                registerForm.style.display = 'block';
            }
            
            tabs.forEach(tab => tab.classList.remove('active'));
            event.target.classList.add('active');
        }
        </script>
    </body>
    </html>
    ''', error_html=error_html)

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'): 
        return redirect('/')
    
    notifications = check_notifications()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard - Study Planner</title>
        <style>
            *{margin:0;padding:0;box-sizing:border-box}
            body{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:30px}
            .container{max-width:1000px;margin:0 auto;text-align:center}
            h1{font-size:42px;margin-bottom:10px}
            h2{font-size:24px;margin-bottom:40px}
            .btn{display:inline-block;padding:22px 45px;margin:15px;background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);color:white;text-decoration:none;border-radius:20px;font-size:22px;font-weight:600;box-shadow:0 12px 30px rgba(0,0,0,0.3);transition:all 0.3s}
            .btn:hover{transform:translateY(-5px)}
            .btn.logout{background:linear-gradient(135deg,#e74c3c,#c0392b)}
            .notification{background:rgba(231,76,60,0.95);padding:25px;border-radius:20px;margin:20px auto;font-size:22px;max-width:650px;box-shadow:0 15px 40px rgba(231,76,60,0.5);cursor:pointer;animation:pulse 2s infinite}
            @keyframes pulse{0%{transform:scale(1);}50%{transform:scale(1.05);}100%{transform:scale(1);}}
            .welcome-card{background:rgba(255,255,255,0.15);padding:40px;border-radius:25px;margin-bottom:40px}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="welcome-card">
                <h1>Welcome {{ session.name }}! 🎓</h1>
                <h2>Study Planner & Reminder App</h2>
            </div>
            {{ notifications|safe }}
            <a href="/study" class="btn">📚 Study Dashboard</a>
            <a href="/goals" class="btn">🎯 Set Goal</a>
            <a href="/view-goals" class="btn">📊 View Goals</a>
            <a href="/reminders" class="btn">⏰ Reminders</a>
            <a href="/myfiles" class="btn">📁 My Files</a>
            <a href="/logout" class="btn logout">🚪 Logout</a>
        </div>
    </body>
    </html>
    ''', session=session, notifications=notifications)

def check_notifications():
    conn = get_db_connection()
    email = session.get('email', '')
    now = datetime.now()
    
    overdue = conn.execute("SELECT * FROM reminders WHERE email=? AND datetime(deadline) <= datetime(?)", 
                          (email, now.isoformat())).fetchall()
    
    notifications = ""
    for reminder in overdue:
        notifications += f'''
        <div class="notification" onclick="playAlarm()">
            <div style="font-size:28px;margin-bottom:15px">🚨 REMINDER</div>
            <div style="font-size:24px;font-weight:600;color:#ffd700">{reminder['title']}</div>
            <div style="font-size:20px;margin-top:10px;color:#fff">Deadline Passed!</div>
        </div>
        '''
    conn.close()
    return notifications

# ===== FIXED COMPLETE STUDY NAVIGATION =====
@app.route('/study')
def study():
    if not session.get('logged_in'): return redirect('/')
    return '''
    <!DOCTYPE html>
    <html><head><title>Study Dashboard</title>
    <style>*{margin:0;padding:0;box-sizing:border-box}
    body{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:50px;text-align:center}
    .container{max-width:800px;width:100%}
    h1{font-size:48px;margin-bottom:80px;text-shadow:0 3px 15px rgba(0,0,0,0.3);animation:fadeInUp 1s ease}
    .year-btn{display:block;width:100%;max-width:500px;margin:30px auto;padding:30px;background:linear-gradient(135deg,#50c878,#27ae60);color:white;text-decoration:none;border-radius:25px;font-size:28px;font-weight:600;box-shadow:0 20px 40px rgba(80,200,120,0.4);transition:all 0.4s ease;transform:translateY(0)}
    .year-btn:hover{transform:translateY(-10px);box-shadow:0 30px 60px rgba(80,200,120,0.6)}
    .back-btn{position:fixed;top:25px;left:25px;padding:18px 30px;background:#f39c12;color:white;text-decoration:none;border-radius:18px;font-size:20px;font-weight:600;z-index:1000;animation:fadeInLeft 0.8s ease}
    @keyframes fadeInUp{from{opacity:0;transform:translateY(30px)}to{opacity:1;transform:translateY(0)}}
    @keyframes fadeInLeft{from{opacity:0;transform:translateX(-30px)}to{opacity:1;transform:translateX(0)}}
    </style>
    </head>
    <body>
    <a href="/dashboard" class="back-btn">← Dashboard</a>
    <div class="container">
        <h1>📚 Study Dashboard</h1>
        <a href="/year1" class="year-btn">🎓 1st Year</a>
        <a href="/year2" class="year-btn">🎓 2nd Year</a>
        <a href="/year3" class="year-btn">🎓 3rd Year</a>
    </div>
    </body>
    </html>
    '''

# ===== FIXED ROUTE STRUCTURE =====
@app.route('/year1')
def year1():
    if not session.get('logged_in'): return redirect('/')
    return year_page("1st Year", "/sem1", "/sem2")

@app.route('/year2') 
def year2():
    if not session.get('logged_in'): return redirect('/')
    return year_page("2nd Year", "/sem3", "/sem4")

@app.route('/year3')
def year3():
    if not session.get('logged_in'): return redirect('/')
    return year_page("3rd Year", "/sem5", "/sem6")

def year_page(title, sem1, sem2):
    return f'''
    <!DOCTYPE html><html><head><title>{title}</title>
    <style>body{{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}}
    .btn{{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}}h1{{font-size:32px;margin-bottom:40px}}</style>
    </head><body><h1>📚 {title}</h1>
    <a href="{sem1}" class="btn">Semester 1</a><a href="{sem2}" class="btn">Semester 2</a>
    <br><a href="/study" class="btn" style="background:#f39c12">← Back</a></body></html>
    '''

@app.route('/sem1')
def sem1(): return semester_page("Semester 1", "/year1", ["maths", "python", "tamil-1", "english-1"])

@app.route('/sem2')
def sem2(): return semester_page("Semester 2", "/year1", ["maths2", "physics", "tamil-2", "english-2"])

@app.route('/sem3')
def sem3(): return semester_page("Semester 3", "/year2", ["data-structures", "algorithms", "web-tech", "dbms"])

@app.route('/sem4')
def sem4(): return semester_page("Semester 4", "/year2", ["os", "networks", "java", "software-eng"])

def semester_page(title, back_link, subjects):
    btns = ''.join([f'<a href="/subject/{sub}" class="btn">{sub.replace("-", " ").title()}</a>' for sub in subjects])
    return f'''
    <!DOCTYPE html><html><head><title>{title}</title>
    <style>body{{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}}
    .btn{{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}}h1{{font-size:32px;margin-bottom:40px}}</style>
    </head><body><h1>📖 {title}</h1>{btns}
    <br><a href="{back_link}" class="btn" style="background:#f39c12">← Back</a></body></html>
    '''

@app.route('/subject/<subject>')
def subject(subject):
    if not session.get('logged_in'): return redirect('/')
    
    files = []
    subject_path = f'static/uploads/{subject}'
    if os.path.exists(subject_path):
        files = [f for f in os.listdir(subject_path) if f.endswith('.pdf')]
    
    units_html = ''
    for i in range(1, 6):
        filename = f"unit{i}.pdf"
        if filename in files:
            units_html += f'''
            <div style="background:#d4edda;color:#155724;padding:15px;margin:10px;border-radius:10px">
                📚 Unit {i} ✅ 
                <a href="/view-pdf/{subject}/{filename}" target="_blank" style="color:#28a745">[View]</a>
                <a href="/download/{subject}/{filename}" style="color:#007bff">[Download]</a>
                <a href="/delete/{subject}/{filename}" onclick="return confirm('Delete Unit {i}?')" style="color:#dc3545">[Delete]</a>
            </div>'''
        else:
            units_html += f'''
            <div style="background:#fff3cd;color:#856404;padding:15px;margin:10px;border-radius:10px">
                📚 Unit {i} 📤 
                <a href="/upload/{subject}/{i}" style="color:#856404;font-weight:bold">[UPLOAD]</a>
            </div>'''
    
    return f'''
    <!DOCTYPE html>
    <html><head><title>{subject.replace('-', ' ').title()}</title>
    <style>body{{background:linear-gradient(135deg,#667eea,#764ba2);color:white;min-height:100vh;padding:30px;font-family:'Segoe UI'}}
    .container{{max-width:800px;margin:0 auto}}
    .back{{position:fixed;top:20px;left:20px;padding:15px;background:#f39c12;color:white;text-decoration:none;border-radius:15px}}
    h1{{text-align:center;font-size:36px;margin:60px 0 40px}}</style></head>
    <body>
    <a href="/study" class="back">← Study</a>
    <div class="container">
        <h1>{subject.replace('-', ' ').title()}</h1>
        {units_html}
    </div>
    </body></html>
    '''

# File operations (upload, view, download, delete) - SAME AS ORIGINAL but fixed
@app.route('/upload/<subject>/<unit>', methods=['GET', 'POST'])
def upload(subject, unit):
    if not session.get('logged_in'): return redirect('/')
    
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.pdf'):
            filename = f"unit{unit}.pdf"
            os.makedirs(f'static/uploads/{subject}', exist_ok=True)
            file.save(f'static/uploads/{subject}/{filename}')
            return redirect(f'/subject/{subject}')
    
    return f'''
    <!DOCTYPE html>
    <html><head><title>Upload Unit {unit}</title>
    <style>body{{background:linear-gradient(135deg,#667eea,#764ba2);color:white;min-height:100vh;display:flex;align-items:center;justify-content:center;font-family:'Segoe UI'}}
    .form{{background:rgba(255,255,255,0.1);padding:50px;border-radius:25px;text-align:center;box-shadow:0 20px 40px rgba(0,0,0,0.3)}}
    input[type=file]{{width:100%;padding:15px;margin:20px 0;border-radius:12px;background:#fff}}
    button{{width:100%;padding:20px;background:#28a745;color:white;border:none;border-radius:15px;font-size:20px;font-weight:600;cursor:pointer}}</style></head>
    <body>
    <div class="form">
        <h1 style="font-size:40px;margin-bottom:30px">📤 Upload Unit {unit}</h1>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="file" accept=".pdf" required>
            <button>Upload PDF</button>
        </form>
        <a href="/subject/{subject}" style="display:inline-block;margin-top:20px;color:#f1c40f">← Back</a>
    </div>
    </body></html>
    '''

@app.route('/view-pdf/<subject>/<filename>')
@app.route('/download/<subject>/<filename>')
def static_file(subject, filename):
    if not session.get('logged_in'): return redirect('/')
    if '/download/' in request.path:
        return send_from_directory(f'static/uploads/{subject}', filename, as_attachment=True)
    return send_from_directory(f'static/uploads/{subject}', filename)

@app.route('/delete/<subject>/<filename>')
def delete(subject, filename):
    if not session.get('logged_in'): return redirect('/')
    file_path = f"static/uploads/{subject}/{filename}"
    if os.path.exists(file_path): 
        os.remove(file_path)
    return redirect('/subject/' + subject)

@app.route('/myfiles')
def myfiles():
    if not session.get('logged_in'): 
        return redirect('/')
    
    files_html = ''
    upload_base = 'static/uploads'
    
    # Create uploads directory if not exists
    os.makedirs(upload_base, exist_ok=True)
    
    if os.path.exists(upload_base):
        subjects = [d for d in os.listdir(upload_base) if os.path.isdir(os.path.join(upload_base, d))]
        subjects.sort()
        
        for subject in subjects:
            subject_path = os.path.join(upload_base, subject)
            pdf_files = [f for f in os.listdir(subject_path) if f.endswith('.pdf')]
            pdf_files.sort()
            
            if pdf_files:  # Only show subjects with PDF files
                files_html += f'''
                <div style="background:linear-gradient(135deg, rgba(255,255,255,0.2), rgba(255,255,255,0.1)); 
                           padding:30px;margin:20px 0;border-radius:25px;box-shadow:0 15px 35px rgba(0,0,0,0.2); 
                           border:1px solid rgba(255,255,255,0.2); backdrop-filter:blur(10px)">
                    <h3 style="margin:0 0 20px 0; font-size:24px; color:#f1c40f; text-align:center">
                        📚 {subject.replace('-', ' ').title()}
                    </h3>
                '''
                
                for filename in pdf_files:
                    file_size = os.path.getsize(os.path.join(subject_path, filename)) / (1024*1024)  # MB
                    upload_date = datetime.fromtimestamp(os.path.getmtime(os.path.join(subject_path, filename))).strftime('%d/%m/%Y')
                    
                    files_html += f'''
                    <div style="background:rgba(255,255,255,0.1);padding:20px;margin:15px 0;border-radius:20px;
                               border-left:4px solid #50c878; box-shadow:0 8px 20px rgba(0,0,0,0.1)">
                        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap">
                            <div>
                                <strong style="font-size:18px;color:white">{filename}</strong><br>
                                <small style="color:#f1c40f">📏 {file_size:.1f} MB | 📅 {upload_date}</small>
                            </div>
                            <div style="display:flex;gap:10px;flex-wrap:wrap">
                                <a href="/view-pdf/{subject}/{filename}" target="_blank" 
                                   style="padding:12px 20px;background:#27ae60;color:white;text-decoration:none;
                                          border-radius:12px;font-weight:600;font-size:14px;transition:all 0.3s;
                                          box-shadow:0 4px 15px rgba(39,174,96,0.4)">
                                   👀 View
                                </a>
                                <a href="/download/{subject}/{filename}" 
                                   style="padding:12px 20px;background:#3498db;color:white;text-decoration:none;
                                          border-radius:12px;font-weight:600;font-size:14px;transition:all 0.3s;
                                          box-shadow:0 4px 15px rgba(52,152,219,0.4)">
                                   📥 Download
                                </a>
                                <a href="/delete/{subject}/{filename}" 
                                   onclick="return confirm('Delete {filename}? This cannot be undone!')"
                                   style="padding:12px 20px;background:#e74c3c;color:white;text-decoration:none;
                                          border-radius:12px;font-weight:600;font-size:14px;transition:all 0.3s;
                                          box-shadow:0 4px 15px rgba(231,76,60,0.4)">
                                   🗑️ Delete
                                </a>
                            </div>
                        </div>
                    </div>
                    '''
                files_html += '</div>'
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>📁 My Files - Study Planner</title>
        <style>
            *{{margin:0;padding:0;box-sizing:border-box}}
            body{{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:30px;overflow-x:hidden}}
            .container{{max-width:1200px;margin:0 auto}}
            .header{{text-align:center;margin-bottom:40px}}
            .back-btn{{position:fixed;top:20px;left:20px;padding:15px 25px;background:#f39c12;color:white;text-decoration:none;border-radius:15px;font-weight:600;font-size:18px;box-shadow:0 8px 20px rgba(243,156,18,0.4);z-index:1000;transition:all 0.3s}}
            .back-btn:hover{{transform:translateY(-2px);box-shadow:0 12px 25px rgba(243,156,18,0.6)}}
            h1{{font-size:48px;margin-bottom:10px;text-shadow:0 4px 20px rgba(0,0,0,0.3)}}
            .stats{{display:flex;justify-content:center;gap:30px;flex-wrap:wrap;margin-bottom:30px}}
            .stat-card{{background:rgba(255,255,255,0.15);padding:20px 30px;border-radius:20px;backdrop-filter:blur(10px);box-shadow:0 10px 30px rgba(0,0,0,0.2)}}
            .upload-section{{text-align:center;margin:40px 0}}
            .upload-btn{{display:inline-block;padding:20px 50px;background:linear-gradient(135deg,#50c878,#27ae60);color:white;text-decoration:none;border-radius:20px;font-size:24px;font-weight:600;box-shadow:0 15px 35px rgba(80,200,120,0.4);transition:all 0.3s;margin:20px}}
            .upload-btn:hover{{transform:translateY(-5px);box-shadow:0 25px 45px rgba(80,200,120,0.6)}}
            .no-files{{text-align:center;padding:80px 20px;background:rgba(255,255,255,0.1);border-radius:25px;margin:40px 0;max-width:600px;margin-left:auto;margin-right:auto;backdrop-filter:blur(15px)}}
            .no-files h2{{font-size:36px;margin-bottom:20px;color:#f1c40f}}
            @media (max-width:768px) {{ .stats{{flex-direction:column;align-items:center}} .stat-card{{text-align:center}} }}
        </style>
    </head>
    <body>
        <a href="/dashboard" class="back-btn">← Dashboard</a>
        <div class="container">
            <div class="header">
                <h1>📁 My Files</h1>
                <div class="stats">
                    <div class="stat-card">
                        <div style="font-size:36px;color:#50c878">📚 {len([d for d in os.listdir(upload_base) if os.path.isdir(os.path.join(upload_base,d)) if any(f.endswith('.pdf') for f in os.listdir(os.path.join(upload_base,d)))])}</div>
                        <div style="font-size:18px">Subjects</div>
                    </div>
                    <div class="stat-card">
                        <div style="font-size:36px;color:#3498db">{sum(len([f for f in os.listdir(os.path.join(upload_base,d)) if f.endswith('.pdf')]) for d in os.listdir(upload_base) if os.path.isdir(os.path.join(upload_base,d)))}</div>
                        <div style="font-size:18px">Total Files</div>
                    </div>
                    <div class="stat-card">
                        <div style="font-size:36px;color:#f39c12">{sum(os.path.getsize(os.path.join(upload_base,d,f))/(1024*1024) for d in os.listdir(upload_base) if os.path.isdir(os.path.join(upload_base,d)) for f in os.listdir(os.path.join(upload_base,d)) if f.endswith('.pdf')):.1f} MB</div>
                        <div style="font-size:18px">Storage Used</div>
                    </div>
                </div>
            </div>
            
            <div class="upload-section">
                <a href="/study" class="upload-btn">📚 Go to Study</a>
                <a href="/upload-new" class="upload-btn">➕ Upload New File</a>
            </div>
            
            {files_html or '''
            <div class="no-files">
                <h2>📂 No files uploaded yet!</h2>
                <p style="font-size:20px;color:#bdc3c7;margin-bottom:30px">Upload your study materials to get started</p>
                <a href="/study" style="padding:18px 40px;background:#50c878;color:white;text-decoration:none;border-radius:15px;font-size:20px;font-weight:600;box-shadow:0 10px 25px rgba(80,200,120,0.4)">🚀 Start Uploading</a>
            </div>
            '''}
        </div>
        
        <script>
        // Add hover effects
        document.querySelectorAll('a[href*="/view-pdf/"], a[href*="/download/"], a[href*="/delete/"]').forEach(btn => {{
            btn.addEventListener('mouseenter', function() {{
                this.style.transform = 'translateY(-2px)';
            }});
            btn.addEventListener('mouseleave', function() {{
                this.style.transform = 'translateY(0)';
            }});
        }});
        </script>
    </body>
    </html>
    '''

# Supporting file routes (add these if not already present)
@app.route('/upload-new', methods=['GET', 'POST'])
def upload_new():
    if not session.get('logged_in'): return redirect('/')
    if request.method == 'POST':
        subject = request.form.get('subject', 'general').lower().replace(' ', '-')
        file = request.files['file']
        if file and file.filename.endswith('.pdf'):
            filename = secure_filename(file.filename)
            os.makedirs(f'static/uploads/{subject}', exist_ok=True)
            file.save(f'static/uploads/{subject}/{filename}')
            return redirect('/myfiles')
        return '<script>alert("Only PDF files allowed!"); history.back();</script>'
    
    return '''
    <h1 style="text-align:center">Upload New File</h1>
    <form method="POST" enctype="multipart/form-data" style="max-width:500px;margin:50px auto">
        <input name="subject" placeholder="Subject name" required>
        <input type="file" name="file" accept=".pdf" required>
        <button type="submit">Upload</button>
    </form>
    <a href="/myfiles">← Back</a>
    '''

@app.route('/goals', methods=['GET', 'POST'])
def goals():
    if not session.get('logged_in'): 
        return redirect('/')
    
    if request.method == 'POST':
        conn = get_db_connection()
        conn.execute('''INSERT INTO goals (email, subject, goal, target_score) 
                       VALUES (?, ?, ?, ?)''', 
                    (session['email'], 
                     request.form['subject'], 
                     request.form['goal'], 
                     int(request.form['target_score'])))
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
    <a href="/dashboard" style="position:fixed;top:30px;left:30px;color:white;font-size:20px;font-weight:600;text-decoration:none">← Dashboard</a>
    <div class="form-box">
        <h1>🎯 Set Study Goals</h1>
        <form method="POST">
            <input name="subject" placeholder="Subject (ex: Mathematics)" required>
            <input name="goal" placeholder="Goal Description" required>
            <input name="target_score" type="number" placeholder="Target Score (ex: 90)" min="0" max="100" required>
            <button type="submit">✅ Save Goal</button>
        </form>
        <p style="font-size:16px;margin-top:20px;color:#f1c40f">📝 Complete 10-question quiz to earn progress!</p>
    </div>
    </body></html>
    '''

@app.route('/view-goals')
def view_goals():
    if not session.get('logged_in'): 
        return redirect('/')
    
    conn = get_db_connection()
    goals = conn.execute('SELECT * FROM goals WHERE email=? ORDER BY id DESC', 
                        (session['email'],)).fetchall()
    conn.close()
    
    goals_html = ''
    for goal in goals:
        progress_bar = f'''
        <div style="background:linear-gradient(90deg, #50c878 {goal['progress']}%, #e0e0e0 {goal['progress']}%); 
                    height:25px;border-radius:15px;overflow:hidden;margin:15px 0">
            <span style="padding:8px 15px;background:rgba(255,255,255,0.2);border-radius:15px;font-weight:600">
                {goal['progress']}% - Max: {goal['max_score']}/10
            </span>
        </div>
        '''
        goals_html += f'''
        <div style="background:rgba(255,255,255,0.15);padding:30px;margin:20px;border-radius:20px">
            <h3>📚 {goal['subject']}</h3>
            <p><strong>Goal:</strong> {goal['goal']}</p>
            <p><strong>Target:</strong> {goal['target_score']}</p>
            {progress_bar}
            <a href="/quiz/{goal['id']}" style="padding:12px 25px;background:#50c878;color:white;text-decoration:none;border-radius:15px;font-weight:600">🧠 Take Quiz</a>
        </div>
        '''
    
    return f'''
    <!DOCTYPE html>
    <html><head><title>My Goals</title>
    <style>*{{margin:0;padding:0;box-sizing:border-box}}
    body{{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:30px}}
    .container{{max-width:1000px;margin:0 auto}}
    .back-btn{{position:fixed;top:20px;left:20px;padding:15px 25px;background:#f39c12;color:white;text-decoration:none;border-radius:15px;font-weight:600}}</style></head>
    <body>
    <a href="/dashboard" class="back-btn">← Dashboard</a>
    <div class="container">
        <h1 style="text-align:center;font-size:42px;margin:80px 0 40px">📊 My Goals</h1>
        {goals_html or '<p style="text-align:center;font-size:28px;color:#f1c40f;margin-top:50px">No goals set yet! <a href="/goals" style="color:#50c878">Set goals →</a></p>'}
    </div>
    </body></html>
    '''

@app.route('/quiz/<int:goal_id>', methods=['GET', 'POST'])
def quiz(goal_id):
    if not session.get('logged_in'): return redirect('/')
    
    conn = get_db_connection()
    goal = conn.execute('SELECT * FROM goals WHERE id=? AND email=?', 
                       (goal_id, session['email'])).fetchone()
    conn.close()
    
    if not goal: return redirect('/view-goals')
    
    # Subject-specific questions
    subject = goal['subject'].lower()
    questions = {
        'mathematics': [
            {"q": "What is 15 × 4?", "options": ["50", "60", "70", "45"], "ans": "60"},
            {"q": "Derivative of x²?", "options": ["2x", "x", "2", "x³"], "ans": "2x"},
        ],
        'python': [
            {"q": "print('Hello') output?", "options": ["Hello", "Hello ", "'Hello'", "Error"], "ans": "Hello"},
            {"q": "len('abc') =", "options": ["3", "2", "abc", "Error"], "ans": "3"},
        ]
    }
    
    quiz_questions = questions.get(subject, [{"q": "Basic concept?", "options": ["A", "B", "C", "D"], "ans": "A"}])
    
    if request.method == 'POST':
        score = sum(1 for i in range(min(10, len(quiz_questions))) 
                   if request.form.get(f'q{i}') == quiz_questions[i]['ans'])
        
        progress_increase = score * 10
        new_progress = min(goal['progress'] + progress_increase, 100)
        
        conn = get_db_connection()
        conn.execute('UPDATE goals SET progress=?, max_score=? WHERE id=? AND email=?',
                    (new_progress, max(goal['max_score'], score), goal_id, session['email']))
        conn.commit()
        conn.close()
        
        return f'''
        <h1 style="text-align:center;font-size:50px;color:#28a745;margin-top:100px">🎉 Score: {score}/10</h1>
        <p style="text-align:center;font-size:24px">Progress: +{progress_increase}%</p>
        <script>setTimeout(()=>location.href="/view-goals", 2000)</script>
        '''
    
    # Quiz form (first 10 questions)
    questions_html = ''
    for i, q in enumerate(quiz_questions[:10]):
        options_html = ''.join([f'<label><input type="radio" name="q{i}" value="{opt}" required> {opt}</label><br>' 
                               for opt in q['options']])
        questions_html += f'<div style="background:rgba(255,255,255,0.1);padding:20px;margin:20px 0;border-radius:15px"><p style="font-size:20px"><strong>Q{i+1}:</strong> {q["q"]}</p>{options_html}</div>'
    
    return f'''
    <!DOCTYPE html>
    <html><head><title>{goal["subject"]} Quiz</title>
    <style>body{{background:linear-gradient(135deg,#667eea,#764ba2);color:white;min-height:100vh;padding:50px;font-family:'Segoe UI'}}
    .quiz-container{{max-width:800px;margin:0 auto;background:rgba(255,255,255,0.1);padding:40px;border-radius:25px;box-shadow:0 20px 40px rgba(0,0,0,0.2)}}
    input[type=radio]{{margin-right:10px;transform:scale(1.2)}} label{{display:block;margin:10px 0;font-size:18px;cursor:pointer}}</style></head>
    <body>
    <div class="quiz-container">
        <h1 style="text-align:center;font-size:42px;margin-bottom:30px">🧠 {goal["subject"]} Quiz</h1>
        <form method="POST">{questions_html}
        <button type="submit" style="width:100%;padding:20px;background:#50c878;color:white;border:none;border-radius:20px;font-size:24px;font-weight:600;margin-top:30px">✅ Submit Quiz</button>
        </form>
    </div>
    </body></html>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/reminders', methods=['GET', 'POST'])
def reminders():
    if not session.get('logged_in'): return redirect('/')
    # Simple placeholder
    return '<h1>⏰ Reminders (Coming Soon)</h1><a href="/dashboard">← Back</a>'

if __name__ == '__main__':
    app.run(debug=True)
