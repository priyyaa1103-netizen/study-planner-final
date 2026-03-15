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

# ===== உங்க Google credentials =====
GOOGLE_CLIENT_ID = "443460939889-qm93e4877opr63d9kktm9lssta81h7md.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"
GOOGLE_REDIRECT_URI = "https://your-render-app.onrender.com/google-callback"  # உங்க Render URL

app = Flask(__name__)
app.secret_key = 'study2026-super-secure-key-change-this-in-production'

# Create necessary folders
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

# ===== USER CREATION - இங்க add ஆகும் =====
def ensure_test_user():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE email='student@gmail.com'")
    if c.fetchone()[0] == 0:
        hashed_pw = generate_password_hash('123456')
        c.execute("INSERT INTO users VALUES (?, ?, ?)", 
                 ('student@gmail.com', hashed_pw, 'Student'))
        conn.commit()
        print("✅ Test user created!")
    conn.close()

ensure_test_user()
# ========================================

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
        email = request.form['email'].lower().strip()
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['logged_in'] = True
            session['email'] = email
            session['name'] = user['name']
            return redirect('/dashboard')
        else:
            error = "❌ Email or Password is incorrect!"
    
    return render_login_page(error)

def render_login_page(error=""):
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Study Planner</title>
        <style>
            *{{margin:0;padding:0;box-sizing:border-box}}
            body{{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}}
            .login-box{{background:#fff;color:#333;padding:60px;border-radius:25px;box-shadow:0 25px 50px rgba(0,0,0,0.3);width:100%;max-width:450px;text-align:center}}
            .input-group{{position:relative;margin:20px 0}}
            .input-group i{{position:absolute;left:20px;top:50%;transform:translateY(-50%);color:#9ca3af;font-size:20px;z-index:1}}
            input{{width:100%;padding:18px 18px 18px 55px;font-size:17px;border:2px solid #e1e5e9;border-radius:15px;box-sizing:border-box;transition:all 0.3s}}
            input:focus{{border-color:#667eea;outline:none;box-shadow:0 0 0 4px rgba(102,126,234,0.1)}}
            .password-toggle{{position:absolute;right:20px;top:50%;transform:translateY(-50%);cursor:pointer;font-size:20px;color:#9ca3af;transition:all 0.3s}}
            .password-toggle:hover{{color:#667eea}}
            button{{width:100%;padding:20px;background:linear-gradient(135deg,#667eea,#764ba2);color:white;border:none;border-radius:15px;font-size:20px;font-weight:600;cursor:pointer;transition:all 0.3s;margin:10px 0}}
            button:hover{{transform:translateY(-3px);box-shadow:0 15px 35px rgba(102,126,234,0.5)}}
            .error{{background:#fee2e2;color:#dc2626;padding:15px;border-radius:10px;margin:20px 0;font-weight:500;border:1px solid #fecaca}}
            h1{{font-size:38px;margin-bottom:40px;color:#1f2937}}
        </style>
    </head>
    <body>
        <div class="login-box">
            <h1>🎓 Study Planner</h1>
            {f'<div class="error">{error}</div>' if error else ''}
            
            <form method="POST">
                <div class="input-group">
                    <i>👤</i>
                    <input type="text" name="name" placeholder="Enter your name" required>
                </div>
                <div class="input-group" style="position:relative;">
                    <i>📧</i>
                    <input type="email" name="email" placeholder="your-email@gmail.com" required>
                </div>
                <div class="input-group">
                    <i>🔒</i>
                    <input type="password" name="password" id="password" placeholder="Enter your password" required>
                    <span class="password-toggle" onclick="togglePassword()">👁️</span>
                </div>
                <button type="submit">🚀 Login</button>
            </form>
        </div>
        
        <script>
        function togglePassword() {{
            const password = document.getElementById('password');
            const toggle = event.target;
            if (password.type === 'password') {{
                password.type = 'text';
                toggle.textContent = '🙈';
            }} else {{
                password.type = 'password';
                toggle.textContent = '👁️';
            }}
        }}
        </script>
    </body>
    </html>
    '''

@app.route('/google-login')
def google_login():
    google_url = "https://accounts.google.com/o/oauth2/auth"
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': GOOGLE_REDIRECT_URI,
        'scope': 'openid email profile',
        'response_type': 'code',
        'access_type': 'offline'
    }
    url = f"{google_url}?{urlencode(params)}"
    return redirect(url)

@app.route('/google-callback')
def google_callback():
    code = request.args.get('code')
    if not code:
        return "Google login failed!", 400
    
    # Token exchange
    token_data = {
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': GOOGLE_REDIRECT_URI
    }
    token_response = requests.post('https://oauth2.googleapis.com/token', data=token_data)
    token = token_response.json()
    
    # User info
    headers = {'Authorization': f'Bearer {token["access_token"]}'}
    user_info = requests.get('https://www.googleapis.com/oauth2/v2/userinfo', headers=headers).json()
    
    # Login
    session['logged_in'] = True
    session['email'] = user_info['email']
    session['name'] = user_info['name']
    
    return redirect('/dashboard')
    
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'): 
        return redirect('/')
    
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
            h1{{font-size:42px;margin-bottom:10px}}
            h2{{font-size:24px;margin-bottom:40px}}
            .btn{{display:inline-block;padding:22px 45px;margin:15px;background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);color:white;text-decoration:none;border-radius:20px;font-size:22px;font-weight:600;box-shadow:0 12px 30px rgba(0,0,0,0.3);transition:all 0.3s}}
            .btn:hover{{transform:translateY(-5px)}}
            .btn.logout{{background:linear-gradient(135deg,#e74c3c,#c0392b)}}
            .notification{{background:rgba(231,76,60,0.95);padding:25px;border-radius:20px;margin:20px auto;font-size:22px;max-width:650px;box-shadow:0 15px 40px rgba(231,76,60,0.5);cursor:pointer;animation:pulse 2s infinite}}
            @keyframes pulse{{0%{{transform:scale(1);}}50%{{transform:scale(1.05);}}100%{{transform:scale(1);}}}}
            .welcome-card{{background:rgba(255,255,255,0.15);padding:40px;border-radius:25px;margin-bottom:40px}}
        </style>
        <script>
        function playAlarm() {{
            try {{
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                oscillator.frequency.value = 800;
                oscillator.type = 'sine';
                gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 1);
                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + 1);
            }} catch(e) {{}}
        }}
        </script>
    </head>
    <body>
        <div class="container">
            <div class="welcome-card">
                <h1>Welcome {session['name']}! 🎓</h1>
                <h2>Study Planner & Reminder App</h2>
            </div>
            {notifications}
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
                  f"Your reminder '{reminder['title']}' was due at {reminder['deadline']}")
        
        notifications += f'''
        <div style="background:linear-gradient(135deg,#e74c3c,#c0392b);padding:30px;margin:30px auto;border-radius:25px;max-width:600px;text-align:center;box-shadow:0 20px 40px rgba(231,76,60,0.4);cursor:pointer;animation:pulse 2s infinite;border:4px solid #ff6b6b" onclick="playAlarm()">
            <div style="font-size:28px;margin-bottom:15px">🚨 REMINDER</div>
            <div style="font-size:24px;font-weight:600;color:#ffd700">{reminder['title']}</div>
            <div style="font-size:20px;margin-top:10px;color:#fff">Deadline Passed! 🔊</div>
        </div>
        <style>
        @keyframes pulse {{
            0% {{ transform: scale(1); box-shadow: 0 0 0 0 rgba(231, 76, 60, 0.7); }}
            70% {{ transform: scale(1.02); box-shadow: 0 0 0 20px rgba(231, 76, 60, 0); }}
            100% {{ transform: scale(1); box-shadow: 0 0 0 0 rgba(231, 76, 60, 0); }}
        }}
        </style>
        '''
    
    conn.close()
    return notifications

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
    if not session.get('logged_in'): return redirect('/')
    
    conn = get_db_connection()
    goals = conn.execute('SELECT * FROM goals WHERE email=? ORDER BY id DESC', 
                        (session['email'],)).fetchall()
    conn.close()
    
    goals_html = ''
    for goal in goals:
        progress_width = goal['progress']
        progress_color = '#2ecc71' if progress_width >= 80 else '#f39c12' if progress_width >= 50 else '#e67e22'
        
        goals_html += f'''
        <div style="background:rgba(255,255,255,0.15);padding:30px;margin:20px;border-radius:25px;box-shadow:0 15px 35px rgba(0,0,0,0.2);backdrop-filter:blur(15px);text-align:left">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:15px">
                <h3 style="font-size:26px;margin:0">{goal['subject']}</h3>
                <a href="/delete_goal/{goal['id']}" style="color:#e74c3c;font-size:24px;text-decoration:none" onclick="return confirm('Delete Goal?')">🗑️</a>
            </div>
            <p style="font-size:18px;margin-bottom:20px;color:#f1c40f"><strong>Goal:</strong> {goal['goal']}</p>
            <p style="font-size:18px;margin-bottom:25px"><strong>Target Score:</strong> {goal['target_score']}</p>
            
            <div style="margin-bottom:20px">
                <div style="background:#34495e;border-radius:25px;padding:3px;margin-bottom:10px">
                    <div style="background:{progress_color};height:25px;border-radius:20px;width:{progress_width}%;transition:all 0.5s;box-shadow:0 5px 15px rgba(0,0,0,0.3)"></div>
                </div>
                <p style="text-align:center;font-size:20px;font-weight:600">
                    Progress: {goal['progress']}% 
                    ({goal['max_score']}/10 quizzes completed)
                </p>
            </div>
            
            <div style="text-align:center">
                <a href="/quiz/{goal['id']}" style="padding:15px 35px;background:#9b59b6;color:white;text-decoration:none;border-radius:20px;font-size:20px;font-weight:600;display:inline-block;box-shadow:0 8px 25px rgba(155,89,182,0.4);margin:5px">🧠 Take Quiz</a>
            </div>
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
    
@app.route('/reminders', methods=['GET', 'POST'])
def reminders():
    if not session.get('logged_in'): return redirect('/')
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        subject = request.form['subject']
        
        # Time parser (hour:minute AM/PM)
        hour = int(request.form['hour'])
        minute = int(request.form['minute'])
        ampm = request.form['ampm']
        
        # Convert 12-hour to 24-hour
        if ampm == 'PM' and hour != 12:
            hour += 12
        elif ampm == 'AM' and hour == 12:
            hour = 0
            
        deadline = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
        if deadline < datetime.now():
            deadline += timedelta(days=1)
            
        # Subject மட்டும் save ஆகும்
        conn.execute('INSERT INTO reminders (email, title, deadline) VALUES (?, ?, ?)',
                    (session['email'], subject, deadline.isoformat()))
        conn.commit()
        return redirect('/reminders')
    
    reminders_list = conn.execute('SELECT * FROM reminders WHERE email=? ORDER BY deadline', 
                                 (session['email'],)).fetchall()
    conn.close()
    
    subjects = ['Mathematics', 'Python', 'Tamil-1', 'english-1', 'Maths-2', 'Physics', 'Tamil-2', 'English-2', 'Java Programming', 'statistics-1', 'Tamil--3', 'english-3',
                'Data Structures', 'statistics-2', 'Tamil-4', 'english-4', 'Operating System', 'RDBMS', 'software_engineering', 'DMW', 'ASP.net', 'Data science', 'Cloud computing']
    
    reminders_html = ''
    now = datetime.now()
    for r in reminders_list:
        deadline = datetime.fromisoformat(r['deadline'])
        time_left = deadline - now
        if time_left.total_seconds() > 0:
            status = f"⏰ Due in {int(time_left.total_seconds()//3600)}h"
            status_color = "#f39c12"
        else:
            status = "🚨 OVERDUE"
            status_color = "#e74c3c"
        
        deadline_time = deadline.strftime('%I:%M %p')
        reminders_html += f'''
        <div style="background:linear-gradient(135deg,{status_color},#333);padding:25px;margin:20px;border-radius:20px">
            <h3 style="margin:0 0 10px 0">{r['title']}</h3>
            <p style="color:#ffd700;font-size:18px;margin:0">{status} | {deadline_time}</p>
            <a href="/delete_reminder/{r['id']}" style="float:right;color:#ff4444;font-size:24px" onclick="return confirm('Delete?')">🗑️</a>
        </div>
        '''
    
    return f'''
    <!DOCTYPE html>
    <html><head><title>Reminders</title>
    <style>
    body{{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}}
    .form-box{{background:rgba(255,255,255,0.15);padding:40px;border-radius:25px;margin:0 auto 50px;max-width:500px;box-shadow:0 20px 40px rgba(0,0,0,0.2);backdrop-filter:blur(15px)}}
    input,select{{width:100%;padding:15px;margin:12px 0;border-radius:12px;border:none;font-size:16px;background:rgba(255,255,255,0.9)}}
    button{{width:100%;padding:18px;background:#50c878;color:white;border:none;border-radius:15px;font-size:20px;font-weight:600;cursor:pointer;margin-top:15px}}
    .time-row{{display:flex;gap:10px;align-items:center}}
    .time-row select{{flex:1}}
    </style>
    </head>
    <body>
        <h1 style="font-size:42px;margin-bottom:30px">⏰ Your Reminders</h1>
        
        <!-- SUBJECT + TIME ONLY (NO TITLE FIELD) -->
        <div class="form-box">
            <h3 style="margin-bottom:25px;font-size:24px">➕ Add New Reminder</h3>
            <form method="POST">
                <select name="subject" required>
                    <option value="">📚 Select Subject</option>
                    {''.join([f'<option value="{sub}">{sub}</option>' for sub in subjects])}
                </select>
                
                <!-- TIME SELECTOR -->
                <div class="time-row">
                    <select name="hour" required>
                        {''.join([f'<option value="{i}">{i}</option>' for i in range(0,13)])}
                    </select>
                    <select name="minute" required>
                        {''.join([f'<option value="{i:02d}">{i:02d}</option>' for i in range(0,60,5)])}
                    </select>
                    <select name="ampm" required>
                        <option value="AM">AM</option>
                        <option value="PM">PM</option>
                    </select>
                </div>
                <button type="submit">✅ Set Reminder</button>
            </form>
        </div>
        
        <!-- SUBJECT NAMES LIST -->
        {reminders_html or '<p style="font-size:28px;color:#f1c40f">No reminders set! 🎯</p>'}
        
        <a href="/dashboard" style="padding:25px 60px;background:#f39c12;color:white;text-decoration:none;border-radius:20px;font-size:24px;font-weight:600;display:inline-block;margin-top:50px">← Dashboard</a>
    </body>
    </html>
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
