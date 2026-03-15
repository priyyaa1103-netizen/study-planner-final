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

# ✅ NO dotenv - Direct env vars
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'study2026-default-key')  # Default for testing

GMAIL_USER = os.getenv("GMAIL_USER", "your-email@gmail.com")
GMAIL_PASS = os.getenv("GMAIL_PASS", "")
os.makedirs('static/uploads', exist_ok=True)

# Initialize SQLite Database
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
def login_register():
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').lower().strip()
            password = request.form.get('password', '')
            name = request.form.get('name', '').strip()
            action = request.form.get('action', 'login')
            
            print(f"🔍 DEBUG: action={action}, email={email}, password_len={len(password) if password else 0}")
            
            conn = get_db_connection()
            
            if action == 'register':
                # Check if user exists
                user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
                print(f"🔍 User exists? {user is not None}")
                
                if user:
                    conn.close()
                    return render_login_page("❌ Email already registered!")
                
                # Create new user
                hashed_pw = generate_password_hash(password)
                print(f"🔐 Hash created: {hashed_pw[:20]}...")
                conn.execute("INSERT INTO users (email, password, name) VALUES (?, ?, ?)", 
                            (email, hashed_pw, name))
                conn.commit()
                conn.close()
                print(f"✅ User CREATED: {email}")
                return render_login_page("✅ Account created! Please login.")
                
            else:  # login
                user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
                print(f"🔍 User found: {user['email'] if user else 'None'}")
                
                if user:
                    print(f"🔍 Password check: {check_password_hash(user['password'], password)}")
                    print(f"🔍 Stored hash: {user['password'][:20]}...")
                    print(f"🔍 Input password len: {len(password)}")
                
                conn.close()
                
                if user and check_password_hash(user['password'], password):
                    session['logged_in'] = True
                    session['email'] = email
                    session['name'] = user['name']
                    print(f"✅ LOGIN SUCCESS: {email}")
                    return redirect('/dashboard')
                else:
                    print(f"❌ LOGIN FAILED: {email}")
                    return render_login_page("❌ Wrong email or password! Check console logs.")
                    
        except Exception as e:
            print(f"💥 ERROR: {e}")
            return render_login_page(f"❌ Error: {str(e)}")
    
    return render_login_page()
    
def render_login_page(error=""):
    error_html = f'<div class="error">{error}</div>' if error else ''
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Study Planner</title>
        <style>
            *{{margin:0;padding:0;box-sizing:border-box}}
            body{{font-family:'Segoe UI';background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}}
            .login-box{{background:#fff;padding:50px;border-radius:25px;box-shadow:0 25px 50px rgba(0,0,0,0.3);width:90%;max-width:450px;text-align:center}}
            .tabs{{display:flex;margin:20px 0;border-radius:15px;overflow:hidden;box-shadow:0 5px 15px rgba(0,0,0,0.2)}}
            .tab{{flex:1;padding:18px;background:#f8fafc;cursor:pointer;border:none;font-weight:600;font-size:16px;transition:all 0.3s}}
            .tab.active{{background:#667eea;color:white}}
            input{{width:100%;padding:18px;margin:15px 0;border:2px solid #e1e5e9;border-radius:15px;font-size:17px;box-sizing:border-box}}
            input:focus{{border-color:#667eea;outline:none}}
            button{{width:100%;padding:20px;background:linear-gradient(135deg,#667eea,#764ba2);color:white;border:none;border-radius:15px;font-size:20px;font-weight:600;cursor:pointer;margin:10px 0;transition:all 0.3s}}
            button:hover{{transform:translateY(-2px);box-shadow:0 10px 25px rgba(102,126,234,0.4)}}
            .error{{background:#fee2e2;color:#dc2626;padding:15px;border-radius:10px;margin:20px 0;font-weight:500}}
        </style>
    </head>
    <body>
        <div class="login-box">
            <h1 style="font-size:40px;margin-bottom:20px;color:#333">🎓 Study Planner</h1>
            {error_html}
            
            <div class="tabs">
                <button class="tab active" onclick="showTab('login')">Login</button>
                <button class="tab" onclick="showTab('register')">Register</button>
            </div>
            
            <!-- LOGIN FORM -->
            <form method="POST" id="loginForm">
                <input type="hidden" name="action" value="login">
                <input type="email" name="email" placeholder="your-email@gmail.com" required>
                <input type="password" name="password" placeholder="Enter password" required>
                <button type="submit">🚀 Login</button>
            </form>
            
            <!-- REGISTER FORM -->
            <form method="POST" id="registerForm" style="display:none">
                <input type="hidden" name="action" value="register">
                <input type="text" name="name" placeholder="Your Full Name" required>
                <input type="email" name="email" placeholder="your-email@gmail.com" required>
                <input type="password" name="password" placeholder="Create Password (6+ chars)" required>
                <button type="submit">✅ Create Account</button>
            </form>
        </div>
        
        <script>
        function showTab(tabName) {{
            const loginForm = document.getElementById('loginForm');
            const registerForm = document.getElementById('registerForm');
            const tabs = document.querySelectorAll('.tab');
            
            if (tabName === 'login') {{
                loginForm.style.display = 'block';
                registerForm.style.display = 'none';
            }} else {{
                loginForm.style.display = 'none';
                registerForm.style.display = 'block';
            }}
            
            tabs.forEach(tab => tab.classList.remove('active'));
            event.target.classList.add('active');
        }}
        </script>
    </body>
    </html>
    '''
    
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'): 
        return redirect('/')
    
    notifications = ""
    email = session.get('email', '')
    name = session.get('name', 'User')
    
    # Simple notification check
    try:
        conn = get_db_connection()
        c = conn.cursor()
        now = datetime.now()
        c.execute("SELECT * FROM reminders WHERE email=?", (email,))
        reminders = c.fetchall()
        
        for reminder in reminders:
            deadline = datetime.fromisoformat(reminder['deadline'].replace('Z', '+00:00'))
            time_left = deadline - now
            hours_left = int(time_left.total_seconds() / 3600)
            
            notifications += f'''
            <div class="notification">
                <div style="font-size:24px">⏰ {reminder['title']}</div>
                <div style="font-size:20px;color:#ffd700">
                    {"Due Now!" if hours_left <= 0 else f"Due in {hours_left}h"}
                </div>
            </div>
            '''
        conn.close()
    except:
        pass
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard - Study Planner</title>
        <style>
            *{{margin:0;padding:0;box-sizing:border-box}}
            body{{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);color:white;min-height:100vh;padding:30px}}
            .container{{max-width:900px;margin:0 auto;text-align:center}}
            h1{{font-size:42px;margin-bottom:10px}}
            h2{{font-size:24px;margin-bottom:40px}}
            .btn{{display:inline-block;padding:22px 40px;margin:10px;background:linear-gradient(135deg,#f093fb,#f5576c);color:white;text-decoration:none;border-radius:20px;font-size:20px;font-weight:600;box-shadow:0 12px 30px rgba(0,0,0,0.3);transition:all 0.3s}}
            .btn:hover{{transform:translateY(-5px)}}
            .btn.logout{{background:linear-gradient(135deg,#e74c3c,#c0392b)}}
            .notification{{background:rgba(231,76,60,0.9);padding:20px;border-radius:20px;margin:20px auto;max-width:600px;box-shadow:0 15px 40px rgba(231,76,60,0.5);border:2px solid #ff6b6b}}
            .welcome-card{{background:rgba(255,255,255,0.15);padding:40px;border-radius:25px;margin-bottom:40px}}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="welcome-card">
                <h1>🎓 Welcome {name}!</h1>
                <h2>Your Study Hub</h2>
            </div>
            
            {notifications}
            
            <a href="/study" class="btn">📚 Study Dashboard</a>
            <a href="/goals" class="btn">🎯 Set Goals</a>
            <a href="/view-goals" class="btn">📊 View Goals</a>
            <a href="/reminders" class="btn">⏰ Reminders</a>
            <a href="/myfiles" class="btn">📁 My Files</a>
            <a href="/logout" class="btn logout">🚪 Logout</a>
        </div>
    </body>
    </html>
    '''
    
@app.route('/check-notifications')
def check_notifications_api():
    if not session.get('logged_in'):
        return ""
    conn = get_db_connection()
    c = conn.cursor()
    email = session.get('email', '')
    now = datetime.now()
    c.execute("SELECT COUNT(*) FROM reminders WHERE email=? AND datetime(deadline) <= datetime(?)", 
              (email, now.isoformat()))
    count = c.fetchone()[0]
    conn.close()
    if count > 0:
        return "🚨"
    return ""

@app.route('/study')
def study():
    if not session.get('logged_in'): return redirect('/')
    return '''
    <!DOCTYPE html>
    <html><head><title>Study Dashboard</title>
    <style>
    *{margin:0;padding:0;box-sizing:border-box}
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
    <a href="/subject/maths" class="btn">Mathematics-1</a>
    <a href="/subject/python" class="btn">Python</a>
    <a href="/subject/tamil-1" class="btn">Tamil-1</a>
    <a href="/subject/english-1" class="btn">English-1</a>
    <br><a href="/year1" class="btn" style="background:#f39c12">← Back</a></body></html>
    '''

@app.route('/sem2')
def sem2():
    if not session.get('logged_in'): return redirect('/')
    return '''
    <!DOCTYPE html><html><head><title>Semester 2</title><style>body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}
    .btn{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}h1{font-size:32px;margin-bottom:40px}</style></head>
    <body><h1>📖 Semester 2</h1>
    <a href="/subject/maths2" class="btn">Maths-2</a>
    <a href="/subject/physics" class="btn">Physics-2</a>
    <a href="/subject/tamil-2" class="btn">Tamil-2</a>
    <a href="/subject/english-2" class="btn">english-2</a>
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
    <a href="/subject/java_programming" class="btn">Java Programming</a>
    <a href="/subject/statistics-1" class="btn">Statistics-1</a>
    <a href="/subject/tamil-3" class="btn">Tamil-3</a>
    <a href="/subject/english-3" class="btn">English-3</a>
    <br><a href="/year2" class="btn" style="background:#f39c12">← Back</a></body></html>
    '''

@app.route('/sem4')
def sem4():
    if not session.get('logged_in'): return redirect('/')
    return '''
    <!DOCTYPE html><html><head><title>Semester 4</title><style>body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}
    .btn{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}h1{font-size:32px;margin-bottom:40px}</style></head>
    <body><h1>📖 Semester 4</h1>
    <a href="/subject/data_structures" class="btn">Data structures</a>
    <a href="/subject/statistics" class="btn">Statistics-2</a>
    <a href="/subject/tamil-4" class="btn">Tamil-4</a>
    <a href="/subject/english-4" class="btn">English-4</a>
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
    <a href="/subject/0perating_System" class="btn">Operating System</a>
    <a href="/subject/RDBMS" class="btn">Relational database management system</a>
    <a href="/subject/Software_Engineering" class="btn">Software engineering</a>
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
    <a href="/subject/Data_Science" class="btn">Data science</a>
    <a href="/subject/Cloud_Computing" class="btn">Cloud computing</a>
    <br><a href="/year3" class="btn" style="background:#f39c12">← Back</a></body></html>
    '''

@app.route('/subject/<subject>', methods=['GET'])
def subject(subject):
    if not session.get('logged_in'): return redirect('/')
    
    # Check uploaded files
    files = []
    subject_path = f'static/uploads/{subject}'
    if os.path.exists(subject_path):
        files = [f for f in os.listdir(subject_path) if f.endswith('.pdf')]
    
    # Units 1-10 HTML
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
            </div>
            '''
        else:
            units_html += f'''
            <div style="background:#fff3cd;color:#856404;padding:15px;margin:10px;border-radius:10px">
                📚 Unit {i} 📤 
                <a href="/upload/{subject}/{i}" style="color:#856404;font-weight:bold">[UPLOAD]</a>
            </div>
            '''
    
    return f'''
    <!DOCTYPE html>
    <html><head><title>{subject.replace('-', ' ').title()}</title>
    <style>
    body{{background:linear-gradient(135deg,#667eea,#764ba2);color:white;min-height:100vh;padding:30px;font-family:'Segoe UI'}}
    .container{{max-width:800px;margin:0 auto}}
    .back{{position:fixed;top:20px;left:20px;padding:15px;background:#f39c12;color:white;text-decoration:none;border-radius:15px}}
    h1{{text-align:center;font-size:36px;margin:60px 0 40px}}
    </style></head>
    <body>
    <a href="/study" class="back">← Study</a>
    <div class="container">
        <h1>{subject.replace('-', ' ').title()}</h1>
        {units_html}
    </div>
    </body></html>
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
            file.save(f'static/uploads/{subject}/{filename}')
            return f'<h1 style="text-align:center;font-size:50px;color:#28a745;margin-top:100px">✅ Unit {unit} Uploaded!</h1><script>setTimeout(()=>location.href="/subject/{subject}", 1500)</script>'
    
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
        <a href="/subject/{subject}" style="display:inline-block;margin-top:20px;color:#f1c40f">← Back to {subject.replace('-', ' ').title()}</a>
    </div>
    </body></html>
    '''
    
@app.route('/view-pdf/<subject>/<filename>')
def view_pdf(subject, filename):
    if not session.get('logged_in'): return redirect('/')
    return send_from_directory(f'static/uploads/{subject}', filename, mimetype='application/pdf')

# ===== MY FILES PAGE (COMPLETE VERSION) =====
@app.route('/myfiles')
def myfiles_page():  # Function name change pannirukken
    if not session.get('logged_in'): 
        return redirect('/')
    
    files_html = ''
    upload_base = 'static/uploads'
    
    if os.path.exists(upload_base):
        for subject in os.listdir(upload_base):
            subject_path = os.path.join(upload_base, subject)
            if os.path.isdir(subject_path):
                for filename in os.listdir(subject_path):
                    if filename.endswith('.pdf'):
                        files_html += f'''
                        <div style="background:rgba(255,255,255,0.2);padding:25px;margin:20px;border-radius:20px">
                            <h3>{subject.replace('-',' ').title()} → {filename}</h3>
                            <div>
                                <a href="/view-pdf/{subject}/{filename}" target="_blank" style="padding:10px 20px;background:#27ae60;color:white;text-decoration:none;border-radius:10px;margin-right:10px">👀 View</a>
                                <a href="/download/{subject}/{filename}" style="padding:10px 20px;background:#3498db;color:white;text-decoration:none;border-radius:10px;margin-right:10px">📥 Download</a>
                                <a href="/delete/{subject}/{filename}" onclick="return confirm('Delete {filename}?')" style="padding:10px 20px;background:#e74c3c;color:white;text-decoration:none;border-radius:10px">🗑️ Delete</a>
                            </div>
                        </div>
                        '''
    
    return f'''
    <!DOCTYPE html>
    <html><head><title>My Files</title>
    <style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:Arial;background:linear-gradient(135deg,#667eea,#764ba2);color:white;min-height:100vh;padding:30px}}.container{{max-width:1000px;margin:0 auto}}.back-btn{{position:fixed;top:20px;left:20px;padding:15px 25px;background:#f39c12;color:white;text-decoration:none;border-radius:15px;font-weight:600}}</style></head>
    <body>
    <a href="/dashboard" class="back-btn">← Dashboard</a>
    <div class="container">
        <h1 style="text-align:center;font-size:42px;margin:80px 0 40px">📁 My Files</h1>
        {files_html or "<p style='text-align:center;font-size:28px;color:#f1c40f'>No files uploaded yet!</p>"}
    </div>
    </body></html>
    '''
    
@app.route('/delete/<subject>/<filename>')
def delete(subject, filename):
    if not session.get('logged_in'): return redirect('/')
    file_path = f"static/uploads/{subject}/{filename}"
    if os.path.exists(file_path): os.remove(file_path)
    return redirect('/myfiles')

@app.route('/download/<subject>/<filename>')
def download(subject, filename):
    if not session.get('logged_in'): return redirect('/')
    return send_from_directory(f'static/uploads/{subject}', filename, as_attachment=True)


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
                     request.form['target_score']))
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
            <button type="submit">✅ Save Goal</button>
        </form>
        <p style="font-size:16px;margin-top:20px;color:#f1c40f">📝 Complete 10-question quiz to earn progress!</p>
    </div>
    <a href="/dashboard" style="position:fixed;top:30px;left:30px;color:white;font-size:20px;font-weight:600;text-decoration:none">← Dashboard</a>
    </body></html>
    '''

@app.route('/quiz/<int:goal_id>', methods=['GET', 'POST'])
def quiz(goal_id):
    if not session.get('logged_in'): 
        return redirect('/')
    
    conn = get_db_connection()
    goal = conn.execute('SELECT * FROM goals WHERE id=? AND email=?', 
                       (goal_id, session['email'])).fetchone()
    conn.close()
    
    if not goal:
        return redirect('/view-goals')
    
    # Subject-specific questions
    subject = goal['subject'].lower()
    questions = {
        'mathematics': [
            {"q": "What is 15 × 4?", "options": ["50", "60", "70", "45"], "ans": "60"},
            {"q": "Derivative of x²?", "options": ["2x", "x", "2", "x³"], "ans": "2x"},
            {"q": "sin(90°) =", "options": ["0", "1", "0.5", "-1"], "ans": "1"},
            {"q": "What is 25% of 80?", "options": ["20", "15", "25", "30"], "ans": "20"},
            {"q": "log₁₀(100) =", "options": ["10", "2", "1", "0"], "ans": "2"},
            {"q": "Area of circle = ?", "options": ["πr", "πr²", "2πr", "4πr"], "ans": "πr²"},
            {"q": "1+1 =", "options": ["2", "1", "0", "11"], "ans": "2"},
            {"q": "Pythagoras theorem?", "options": ["a²+b²=c²", "a+b=c", "a×b=c", "a-b=c"], "ans": "a²+b²=c²"},
            {"q": "Factorial 5! =", "options": ["120", "25", "10", "50"], "ans": "120"},
            {"q": "√16 =", "options": ["2", "4", "8", "16"], "ans": "4"}
        ],
        'python': [
            {"q": "print('Hello') output?", "options": ["Hello", "Hello ", "'Hello'", "Error"], "ans": "Hello"},
            {"q": "len('abc') =", "options": ["3", "2", "abc", "Error"], "ans": "3"},
            {"q": "[1,2,3][1] =", "options": ["1", "2", "3", "Error"], "ans": "2"},
            {"q": "'hello'.upper() =", "options": ["HELLO", "hello", "Hello", "Error"], "ans": "HELLO"},
            {"q": "range(3) length?", "options": ["3", "2", "0", "4"], "ans": "3"},
            {"q": "True == 1 ?", "options": ["True", "False", "Error", "1"], "ans": "True"},
            {"q": "for i in range(5): print(i) last?", "options": ["4", "5", "0", "3"], "ans": "4"},
            {"q": "list[0] access?", "options": ["First item", "Last item", "Middle", "Error"], "ans": "First item"},
            {"q": "if True: print('hi')?", "options": ["Prints hi", "No print", "Error", "Infinite"], "ans": "Prints hi"},
            {"q": "def func(): pass?", "options": ["Function", "Class", "Variable", "Error"], "ans": "Function"}
        ]
    }
    
    # Default questions for other subjects (FIXED - no comprehension)
    default_questions = [
        {"q": "Basic concept of this subject?", "options": ["A", "B", "C", "D"], "ans": "A"},
        {"q": "Main topic #1?", "options": ["Option1", "Option2", "Option3", "Option4"], "ans": "Option1"},
        {"q": "Main topic #2?", "options": ["Option1", "Option2", "Option3", "Option4"], "ans": "Option1"},
        {"q": "Key principle?", "options": ["Option1", "Option2", "Option3", "Option4"], "ans": "Option1"},
        {"q": "Basic definition?", "options": ["Option1", "Option2", "Option3", "Option4"], "ans": "Option1"},
        {"q": "Core concept?", "options": ["Option1", "Option2", "Option3", "Option4"], "ans": "Option1"},
        {"q": "Fundamental idea?", "options": ["Option1", "Option2", "Option3", "Option4"], "ans": "Option1"},
        {"q": "Main principle?", "options": ["Option1", "Option2", "Option3", "Option4"], "ans": "Option1"},
        {"q": "Key topic?", "options": ["Option1", "Option2", "Option3", "Option4"], "ans": "Option1"},
        {"q": "Basic question?", "options": ["Option1", "Option2", "Option3", "Option4"], "ans": "Option1"}
    ]
    
    quiz_questions = questions.get(subject, default_questions)
    
    if request.method == 'POST':
        score = 0
        for i in range(10):
            if request.form.get(f'q{i}') == quiz_questions[i]['ans']:
                score += 1
        
        # Update progress
        progress_increase = score * 10
        new_progress = min(goal['progress'] + progress_increase, 100)
        new_max_score = max(goal['max_score'], score)
        
        conn = get_db_connection()
        conn.execute('UPDATE goals SET progress=?, max_score=? WHERE id=? AND email=?',
                    (new_progress, new_max_score, goal_id, session['email']))
        conn.commit()
        conn.close()
        
        return f'''
        <!DOCTYPE html>
        <html><head><title>Quiz Result</title>
        <style>body{{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}}
        .result-box{{background:rgba(255,255,255,0.15);padding:60px;border-radius:25px;margin:50px auto;max-width:600px;box-shadow:0 20px 40px rgba(0,0,0,0.2);backdrop-filter:blur(15px)}}
        .score{{font-size:48px;margin:30px 0;color:#2ecc71;font-weight:700}}</style></head>
        <body>
        <div class="result-box">
            <h1>🎉 Quiz Complete!</h1>
            <div class="score">Score: {score}/10</div>
            <p style="font-size:24px">Progress increased by {progress_increase}%!</p>
            <p style="font-size:20px">Total Progress: {new_progress}%</p>
            <a href="/view-goals" style="padding:20px 50px;background:#50c878;color:white;text-decoration:none;border-radius:20px;font-size:24px;font-weight:600;display:inline-block;margin-top:30px">📊 View Goals</a>
        </div>
        </body></html>
        '''
    
    # Quiz form
    questions_html = ''
    for i, q in enumerate(quiz_questions):
        options_html = ''.join([f'<label><input type="radio" name="q{i}" value="{opt}" required> {opt}</label><br>' 
                               for opt in q['options']])
        questions_html += f'''
        <div style="background:rgba(255,255,255,0.1);padding:20px;margin:20px 0;border-radius:15px">
            <p style="font-size:20px;margin-bottom:15px"><strong>Q{i+1}:</strong> {q["q"]}</p>
            {options_html}
        </div>
        '''
    
    return f'''
    <!DOCTYPE html>
    <html><head><title>{goal["subject"]} Quiz</title>
    <style>body{{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px}}
    .quiz-container{{max-width:800px;margin:0 auto;background:rgba(255,255,255,0.1);padding:40px;border-radius:25px;box-shadow:0 20px 40px rgba(0,0,0,0.2);backdrop-filter:blur(15px)}}
    input[type=radio]{{margin-right:10px;transform:scale(1.2)}} label{{display:block;margin:10px 0;font-size:18px;cursor:pointer}}</style></head>
    <body>
    <div class="quiz-container">
        <h1 style="text-align:center;font-size:42px;margin-bottom:30px">🧠 {goal["subject"]} Quiz</h1>
        <p style="text-align:center;font-size:20px;margin-bottom:40px">Complete 10 questions (1 point each = 10% progress)</p>
        <form method="POST">
            {questions_html}
            <button type="submit" style="width:100%;padding:20px;background:#50c878;color:white;border:none;border-radius:20px;font-size:24px;font-weight:600;cursor:pointer;margin-top:30px;box-shadow:0 10px 30px rgba(80,200,120,0.4)">✅ Submit Quiz</button>
        </form>
        <a href="/view-goals" style="display:block;text-align:center;margin-top:20px;color:#f1c40f;font-size:20px;font-weight:600">← Back to Goals</a>
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
    conn.close()  # ← This was missing!
    
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
    <style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);color:white;min-height:100vh;padding:30px}}.container{{max-width:900px;margin:0 auto}}.back-btn{{position:fixed;top:20px;left:20px;padding:15px 25px;background:#f39c12;color:white;text-decoration:none;border-radius:15px;font-weight:600;z-index:100}}</style></head>
    <body>
    <a href="/dashboard" class="back-btn">← Dashboard</a>
    <div class="container">
        <h1 style="text-align:center;font-size:42px;margin:80px 0 40px">🎯 My Study Goals</h1>
        {goals_html or '<p style="text-align:center;font-size:28px;color:#f1c40f;margin-top:50px">No goals set yet! <a href="/goals" style="color:#50c878">Set goals →</a></p>'}
    </div>
    </body></html>
    '''
    
@app.route('/reminders', methods=['GET', 'POST'])
def reminders():
    if not session.get('logged_in'): 
        return redirect('/')
    
    email = session.get('email', '')
    
    if request.method == 'POST':
        conn = get_db_connection()
        deadline_input = request.form['deadline']  # "2026-03-15T20:20"
        
        # ✅ Fix: Date + Time combine
        now_date = datetime.now().strftime('%Y-%m-%d')
        fixed_datetime = f"{now_date} {deadline_input.split('T')[1]}:00"
        deadline = datetime.strptime(fixed_datetime, '%Y-%m-%d %H:%M:%S')
        
        conn.execute("INSERT INTO reminders (email, title, deadline) VALUES (?, ?, ?)",
                    (email, request.form['title'], deadline.isoformat()))
        conn.commit()
        conn.close()
        return redirect('/reminders')
    
    # ✅ Perfect time display
    conn = get_db_connection()
    reminders_data = conn.execute("SELECT * FROM reminders WHERE email=? ORDER BY deadline", (email,)).fetchall()
    conn.close()
    
    now = datetime.now()
    reminders_html = ''
    
    for r in reminders_data:
        try:
            deadline = datetime.fromisoformat(r['deadline'])
            time_diff = deadline - now
            
            # ✅ Real calculation
            total_minutes = max(0, int(time_diff.total_seconds() / 60))
            
            if total_minutes == 0:
                status = "🚨 RIGHT NOW!"
                color = "#ff4757"
            elif total_minutes < 60:
                status = f"⏳ {total_minutes} mins"
                color = "#ff6b7a"
            elif total_minutes < 1440:  # 24 hours
                hours = total_minutes // 60
                mins = total_minutes % 60
                status = f"⏰ {hours}h {mins}m"
                color = "#f1c40f"
            else:
                days = total_minutes // 1440
                status = f"📅 {days} days"
                color = "#2ed573"
            
            display_time = deadline.strftime('%I:%M %p')
            
            reminders_html += f'''
            <div style="background:rgba(255,255,255,0.1);padding:25px;margin:15px 0;border-radius:20px;border-left:6px solid {color}">
                <div style="font-size:26px;font-weight:600">{r['title']}</div>
                <div style="font-size:20px;color:#f1c40f">🕐 {display_time}</div>
                <div style="font-size:22px;color:{color};font-weight:600">{status}</div>
            </div>
            '''
        except:
            reminders_html += f'<div style="padding:20px;margin:15px;background:rgba(255,255,255,0.1);border-radius:15px">{r["title"]}</div>'
    
    return f'''
    <!DOCTYPE html>
    <html><head><title>⏰ Reminders</title>
    <style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:'Segoe UI';background:linear-gradient(135deg,#667eea,#764ba2);color:white;min-height:100vh;padding:30px}}.container{{max-width:650px;margin:0 auto;text-align:center}}.form-box{{background:rgba(255,255,255,0.15);padding:45px;border-radius:25px;margin:40px 0;backdrop-filter:blur(15px)}}input{{width:100%;padding:18px;margin:12px 0;border-radius:12px;border:none;font-size:18px;box-shadow:0 5px 20px rgba(0,0,0,0.1)}}button{{width:100%;padding:20px;background:#50c878;color:white;border:none;border-radius:15px;font-size:20px;font-weight:600;cursor:pointer;margin-top:10px}}h1{{font-size:42px;margin-bottom:30px;text-shadow:0 5px 20px rgba(0,0,0,0.3)}}.back-btn{{position:fixed;top:25px;left:25px;padding:15px 25px;background:#f39c12;color:white;text-decoration:none;border-radius:15px;font-weight:600;font-size:18px}}</style></head>
    <body>
        <a href="/dashboard" class="back-btn">← Dashboard</a>
        <div class="container">
            <h1>⏰ Reminders</h1>
            <div class="form-box">
                <form method="POST">
                    <input name="title" placeholder="Study Task" required>
                    <input name="deadline" type="time" required>  <!-- ✅ TIME ONLY -->
                    <button>✅ Add Reminder</button>
                </form>
                <small style="color:#f1c40f">Today’s date + your time = Perfect reminder!</small>
            </div>
            {reminders_html or '<p style="font-size:28px;padding:40px;background:rgba(255,255,255,0.1);border-radius:20px">No reminders set</p>'}
        </div>
    </body></html>
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
    
@app.route('/delete_reminder/<int:id>')
def delete_reminder(id):
    if not session.get('logged_in'): return redirect('/')
    conn = sqlite3.connect('users.db')
    conn.execute('DELETE FROM reminders WHERE id=? AND email=?', (id, session['email']))
    conn.commit()
    conn.close()
    return redirect('/reminders')

@app.route('/delete_goal/<int:id>')
def delete_goal(id):
    if not session.get('logged_in'): return redirect('/')
    conn = sqlite3.connect('users.db')
    conn.execute('DELETE FROM goals WHERE id=? AND email=?', (id, session['email']))
    conn.commit()
    conn.close()
    return redirect('/view-goals')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
