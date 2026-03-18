from flask import Flask, request, redirect, session, render_template_string, send_from_directory, jsonify 
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
app.secret_key = os.getenv('SECRET_KEY', 'study2026-default-key')

# Fixed GLOBAL_ALARM_JS - completed audio URLs and syntax
GLOBAL_ALARM_JS = """
<script>

// ✅ Prevent multiple runs
if(window.alarmRunning){
    console.log("Alarm already running");
} else {
    window.alarmRunning = true;

    let firedAlarms = new Set();

    console.log("🎵 GLOBAL ALARM ACTIVE");

    // ⏰ Check every 2 sec
    setInterval(() => {
        fetch("/api/user-alarms")
        .then(r => r.json())
        .then(data => {
            const now = new Date();

            data.forEach(alarm => {
                if(new Date(alarm.deadline) <= now && !firedAlarms.has(alarm.id)) {
                    firedAlarms.add(alarm.id);
                    console.log("🚨 TRIGGER:", alarm.title);

                    playAlarmSound(alarm.id, alarm.title);
                }
            });
        })
        .catch(err => console.log("Alarm fetch error:", err));

    }, 2000);


    // 🚨 Alarm function
    function playAlarmSound(id, title) {

        // 🔥 Delete from DB
        fetch("/mark-triggered/" + id, {method: "POST"});

        // 🔊 Main sound
        const audio = new Audio("https://freesound.org/data/previews/316/316847_4939433-lq.mp3");
        audio.volume = 1.0;
        audio.play().catch(e => console.log("Audio blocked:", e));

        // 🔊 Backup beep
        playBeepSound();

        // 🔴 Red alert screen
        document.body.innerHTML += `
            <div style="
                position:fixed;top:0;left:0;width:100vw;height:100vh;
                background:rgba(255,0,0,0.8);z-index:99999;
                display:flex;align-items:center;justify-content:center;
                font-size:50px;font-weight:bold;color:white;
                text-shadow:0 0 20px #fff;
                animation: pulse 1s infinite;" 
                onclick="this.remove()">
                🚨 ${title.toUpperCase()} 🚨
            </div>
        `;

        // 📳 Shake effect
        document.body.classList.add('shake');
        setTimeout(() => document.body.classList.remove('shake'), 2000);
    }


    // 🔊 Beep sound
    function playBeepSound() {
        for(let i=0; i<3; i++) {
            setTimeout(() => {
                try {
                    const ctx = new (window.AudioContext || window.webkitAudioContext)();
                    const o = ctx.createOscillator(), g = ctx.createGain();
                    o.connect(g); g.connect(ctx.destination);
                    o.frequency.value = 800 + i*200;
                    o.type = "sine";
                    g.gain.setValueAtTime(0.3, ctx.currentTime);
                    g.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.5);
                    o.start(ctx.currentTime);
                    o.stop(ctx.currentTime + 0.5);
                } catch(e) {}
            }, i*600);
        }
    }

}
</script>

<style>
@keyframes pulse {
    0%,100% { transform: scale(1); }
    50% { transform: scale(1.1); }
}
@keyframes shake {
    0%,100% { transform: translateX(0); }
    25% { transform: translateX(-10px); }
    75% { transform: translateX(10px); }
}
body.shake { animation: shake 0.2s infinite; }
</style>
"""

GMAIL_USER = os.getenv("GMAIL_USER", "your-email@gmail.com")
GMAIL_PASS = os.getenv("GMAIL_PASS", "")
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
                  email TEXT, 
                  title TEXT, 
                  deadline TEXT,
                  triggered INTEGER DEFAULT 0)''')
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

@app.route('/', methods=['GET', 'POST'])
def home():
    session.clear()
    # ✅ AUTOMATIC REDIRECT MAGIC
    if session.get('logged_in') and session.get('email'):
        print(f"🚀 Auto-redirecting {session['email']} to dashboard")
        return redirect('/dashboard')
    
    if request.method == 'POST':
        try:
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
                    print(f"✅ LOGIN SUCCESS: {email}")
                    return redirect('/dashboard')  # Auto dashboard!
                else:
                    return render_login_page("❌ Wrong email or password!")
                    
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
    
    email = session['email']
    conn = get_db_connection()
    reminders = conn.execute("SELECT * FROM reminders WHERE email=? ORDER BY deadline ASC", (email,)).fetchall()
    conn.close()
    
    notifications = ""
    for r in reminders[:5]:  # Show top 5
        notifications += f'''
        <div class="notification" style="background:rgba(231,76,60,0.95);padding:25px;border-radius:20px;margin:20px auto;max-width:600px;box-shadow:0 15px 40px rgba(231,76,60,0.5);cursor:pointer">
            <div style="font-size:28px">⏰ {r["title"]}</div>
            <div style="font-size:20px;color:#ffd700">{r["deadline"]}</div>
        </div>
        '''
    
    return f'''
<!DOCTYPE html>
<html><head><title>Dashboard</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:'Segoe UI';background:linear-gradient(135deg,#667eea,#764ba2);color:white;min-height:100vh;padding:30px}}.container{{max-width:900px;margin:0 auto;text-align:center}}.btn{{display:inline-block;padding:22px 40px;margin:10px;background:linear-gradient(135deg,#f093fb,#f5576c);color:white;text-decoration:none;border-radius:20px;font-size:20px;font-weight:600;box-shadow:0 12px 30px rgba(0,0,0,0.3);transition:all 0.3s}}.btn:hover{{transform:translateY(-5px);box-shadow:0 20px 40px rgba(0,0,0,0.4)}}</style></head>
<body>
<div class="container">
    <h1 style="font-size:42px;margin-bottom:20px">🎓 Welcome {session.get("name", "User")}!</h1>
    <h2 style="font-size:24px;margin-bottom:30px">Study Planner Dashboard</h2>
    {notifications}
    <div style="margin:40px 0">
        <a href="/study" class="btn">📚 Study Dashboard</a>
        <a href="/goals" class="btn">🎯 Set Goals</a>
        <a href="/view-goals" class="btn">📊 View Goals</a>
        <a href="/reminders" class="btn">⏰ Reminders</a>
        <a href="/logout" class="btn" style="background:linear-gradient(135deg,#e74c3c,#c0392b)">🚪 Logout</a>
    </div>
</div>
{GLOBAL_ALARM_JS}
</body></html>
'''

@app.route('/api/user-alarms')
def user_alarms():
    if not session.get('logged_in'):
        return jsonify([])
    conn = get_db_connection()
    alarms = conn.execute("""
    SELECT id, title, deadline 
    FROM reminders 
    WHERE email=? AND triggered=0
""", (session['email'],)).fetchall()
    conn.close()
    return jsonify([{'id': a['id'], 'title': a['title'], 'deadline': a['deadline']} for a in alarms])

@app.route('/mark-triggered/<int:alarm_id>', methods=['POST'])
def mark_triggered(alarm_id):
    if not session.get('logged_in'):
        return "Unauthorized", 401
    
    conn = get_db_connection()
    conn.execute("""
        DELETE FROM reminders
        WHERE id=? AND email=?
    """, (alarm_id, session['email']))
    conn.commit()
    conn.close()
    
    return "OK"

@app.route('/reminders', methods=['GET', 'POST'])
def reminders():
    if not session.get('logged_in'): return redirect('/')
    
    if request.method == 'POST':
        conn = get_db_connection()
        conn.execute("INSERT INTO reminders (email, title, deadline) VALUES (?, ?, ?)",
                    (session['email'], request.form['title'], request.form['deadline']))
        conn.commit()
        conn.close()
        return redirect('/reminders')
    
    conn = get_db_connection()
    my_reminders = conn.execute("SELECT * FROM reminders WHERE email=? ORDER BY deadline ASC", 
                               (session['email'],)).fetchall()
    conn.close()
    
    reminders_html = ""
    for r in my_reminders:
        reminders_html += f'''
        <div style="background:rgba(255,255,255,0.2);padding:20px;margin:15px;border-radius:15px">
            <strong>{r['title']}</strong> - {r['deadline']}
            <a href="/delete-reminder/{r['id']}" onclick="return confirm('Delete?')" 
               style="float:right;color:#ff6b6b;font-weight:bold">🗑️</a>
        </div>
        '''
    
    return f'''
<!DOCTYPE html>
<html><head><title>Reminders</title>
<style>body{{font-family:'Segoe UI';background:linear-gradient(135deg,#667eea,#764ba2);color:white;min-height:100vh;padding:50px}}.form-box{{background:rgba(255,255,255,0.15);padding:40px;border-radius:25px;max-width:600px;margin:0 auto}}.input-group input{{width:100%;padding:15px;margin:10px 0;border-radius:12px;border:none;font-size:16px}}</style></head>
<body>
<div class="form-box">
    <h1 style="text-align:center;font-size:36px;margin-bottom:30px">⏰ Set Reminder</h1>
    <form method="POST">
        <div class="input-group">
            <input name="title" placeholder="Reminder Title (ex: Math Exam)" required>
            <input name="deadline" type="datetime-local" required>
            <button style="width:100%;padding:18px;background:#50c878;color:white;border:none;border-radius:15px;font-size:20px;font-weight:600;cursor:pointer">✅ Add Reminder</button>
        </div>
    </form>
    <h2 style="margin-top:40px">Your Reminders:</h2>
    {reminders_html or '<p style="text-align:center;color:#f1c40f">No reminders set</p>'}
    <a href="/dashboard" style="display:block;margin-top:30px;padding:15px;background:#f39c12;color:white;text-decoration:none;border-radius:12px;text-align:center;font-weight:600">← Dashboard</a>
</div>
{GLOBAL_ALARM_JS}
</body></html>
'''
    
@app.route('/delete-reminder/<int:reminder_id>')
def delete_reminder(reminder_id):
    if not session.get('logged_in'): return redirect('/')
    conn = get_db_connection()
    conn.execute("DELETE FROM reminders WHERE id=? AND email=?", (reminder_id, session['email']))
    conn.commit()
    conn.close()
    return redirect('/reminders')
    
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
    return f'''
    <!DOCTYPE html>
    <html><head><title>Study Dashboard</title>
    <style>
    *{{margin:0;padding:0;box-sizing:border-box}}
    body{{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:50px;text-align:center}}
    .container{{max-width:800px;width:100%}}
    h1{{font-size:48px;margin-bottom:80px;text-shadow:0 3px 15px rgba(0,0,0,0.3);animation:fadeInUp 1s ease}}
    .year-btn{{display:block;width:100%;max-width:500px;margin:30px auto;padding:30px;background:linear-gradient(135deg,#50c878,#27ae60);color:white;text-decoration:none;border-radius:25px;font-size:28px;font-weight:600;box-shadow:0 20px 40px rgba(80,200,120,0.4);transition:all 0.4s ease;transform:translateY(0)}}
    .year-btn:hover{{transform:translateY(-10px);box-shadow:0 30px 60px rgba(80,200,120,0.6)}}
    .back-btn{{position:fixed;top:25px;left:25px;padding:18px 30px;background:#f39c12;color:white;text-decoration:none;border-radius:18px;font-size:20px;font-weight:600;z-index:1000;animation:fadeInLeft 0.8s ease}}
    @keyframes fadeInUp{{from{{opacity:0;transform:translateY(30px)}}to{{opacity:1;transform:translateY(0)}}
    @keyframes fadeInLeft{{from{{opacity:0;transform:translateX(-30px)}}to{{opacity:1;transform:translateX(0)}}
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
    {GLOBAL_ALARM_JS}
    </body>
    </html>
    '''

# ===== 1st YEAR =====
@app.route('/year1')
def year1():
    if not session.get('logged_in'): return redirect('/')
    return f'''
    <!DOCTYPE html><html><head><title>1st Year</title><style>body{{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}}
    .btn{{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}}h1{{font-size:32px;margin-bottom:40px}}</style></head>
    <body><h1>📚 1st Year</h1><a href="/sem1" class="btn">Semester 1</a><a href="/sem2" class="btn">Semester 2</a>
    <br><a href="/study" class="btn" style="background:#f39c12">← Back</a>{GLOBAL_ALARM_JS}</body></html>
    '''

@app.route('/sem1')
def sem1():
    if not session.get('logged_in'): return redirect('/')
    return f'''
    <!DOCTYPE html><html><head><title>Semester 1</title><style>body{{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}}
    .btn{{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}}h1{{font-size:32px;margin-bottom:40px}}</style></head>
    <body><h1>📖 Semester 1</h1>
    <a href="/subject/maths" class="btn">Mathematics-1</a>
    <a href="/subject/python" class="btn">Python</a>
    <a href="/subject/tamil-1" class="btn">Tamil-1</a>
    <a href="/subject/english-1" class="btn">English-1</a>
    <br><a href="/year1" class="btn" style="background:#f39c12">← Back</a>{GLOBAL_ALARM_JS}</body></html>
    '''

@app.route('/sem2')
def sem2():
    if not session.get('logged_in'): return redirect('/')
    return f'''
    <!DOCTYPE html><html><head><title>Semester 2</title><style>body{{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}}
    .btn{{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}}h1{{font-size:32px;margin-bottom:40px}}</style></head>
    <body><h1>📖 Semester 2</h1>
    <a href="/subject/maths2" class="btn">Maths-2</a>
    <a href="/subject/physics" class="btn">Physics-2</a>
    <a href="/subject/tamil-2" class="btn">Tamil-2</a>
    <a href="/subject/english-2" class="btn">english-2</a>
    <br><a href="/year1" class="btn" style="background:#f39c12">← Back</a>{GLOBAL_ALARM_JS}</body></html>
    '''

# ===== 2nd YEAR =====
@app.route('/year2')
def year2():
    if not session.get('logged_in'): return redirect('/')
    return f'''
    <!DOCTYPE html><html><head><title>2nd Year</title><style>body{{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}}
    .btn{{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}}h1{{font-size:32px;margin-bottom:40px}}</style></head>
    <body><h1>📚 2nd Year</h1><a href="/sem3" class="btn">Semester 3</a><a href="/sem4" class="btn">Semester 4</a>
    <br><a href="/study" class="btn" style="background:#f39c12">← Back</a>{GLOBAL_ALARM_JS}</body></html>
    '''

@app.route('/sem3')
def sem3():
    if not session.get('logged_in'): return redirect('/')
    return f'''
    <!DOCTYPE html><html><head><title>Semester 3</title><style>body{{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}}
    .btn{{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}}h1{{font-size:32px;margin-bottom:40px}}</style></head>
    <body><h1>📖 Semester 3</h1>
    <a href="/subject/java_programming" class="btn">Java Programming</a>
    <a href="/subject/statistics-1" class="btn">Statistics-1</a>
    <a href="/subject/tamil-3" class="btn">Tamil-3</a>
    <a href="/subject/english-3" class="btn">English-3</a>
    <br><a href="/year2" class="btn" style="background:#f39c12">← Back</a>{GLOBAL_ALARM_JS}</body></html>
    '''

@app.route('/sem4')
def sem4():
    if not session.get('logged_in'): return redirect('/')
    return f'''
    <!DOCTYPE html><html><head><title>Semester 4</title><style>body{{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}}
    .btn{{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}}h1{{font-size:32px;margin-bottom:40px}}</style></head>
    <body><h1>📖 Semester 4</h1>
    <a href="/subject/data_structures" class="btn">Data structures</a>
    <a href="/subject/statistics" class="btn">Statistics-2</a>
    <a href="/subject/tamil-4" class="btn">Tamil-4</a>
    <a href="/subject/english-4" class="btn">English-4</a>
    <br><a href="/year2" class="btn" style="background:#f39c12">← Back</a>{GLOBAL_ALARM_JS}</body></html>
    '''

# ===== 3rd YEAR =====
@app.route('/year3')
def year3():
    if not session.get('logged_in'): return redirect('/')
    return f'''
    <!DOCTYPE html><html><head><title>3rd Year</title><style>body{{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}}
    .btn{{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}}h1{{font-size:32px;margin-bottom:40px}}</style></head>
    <body><h1>📚 3rd Year</h1><a href="/sem5" class="btn">Semester 5</a><a href="/sem6" class="btn">Semester 6</a>
    <br><a href="/study" class="btn" style="background:#f39c12">← Back</a>{GLOBAL_ALARM_JS}</body></html>
    '''

@app.route('/sem5')
def sem5():
    if not session.get('logged_in'): return redirect('/')
    return f'''
    <!DOCTYPE html><html><head><title>Semester 5</title><style>body{{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}}
    .btn{{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}}h1{{font-size:32px;margin-bottom:40px}}</style></head>
    <body><h1>📖 Semester 5</h1>
    <a href="/subject/0perating_System" class="btn">Operating System</a>
    <a href="/subject/RDBMS" class="btn">Relational database management system</a>
    <a href="/subject/Software_Engineering" class="btn">Software engineering</a>
    <a href="/subject/DMW" class="btn">Data mining and warehousing</a>
    <br><a href="/year3" class="btn" style="background:#f39c12">← Back</a>{GLOBAL_ALARM_JS}</body></html>
    '''

@app.route('/sem6')
def sem6():
    if not session.get('logged_in'): return redirect('/')
    return f'''
    <!DOCTYPE html><html><head><title>Semester 6</title><style>body{{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}}
    .btn{{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}}h1{{font-size:32px;margin-bottom:40px}}</style></head>
    <body><h1>📖 Semester 6</h1>
    <a href="/subject/ASP.net" class="btn">Programming in ASP.net</a>
    <a href="/subject/Data_Science" class="btn">Data science</a>
    <a href="/subject/Cloud_Computing" class="btn">Cloud computing</a>
    <br><a href="/year3" class="btn" style="background:#f39c12">← Back</a>{GLOBAL_ALARM_JS}</body></html>
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
    {GLOBAL_ALARM_JS}
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
    {GLOBAL_ALARM_JS}
    </body></html>
    '''
    
@app.route('/view-pdf/<subject>/<filename>')
def view_pdf(subject, filename):
    if not session.get('logged_in'): 
        return redirect('/')
    
    return f'''
    <html>
    <body>

    <!-- 📄 PDF -->
    <iframe src="/static/uploads/{subject}/{filename}" 
            style="width:100%; height:100vh;"></iframe>

    <!-- 🔥 இத தான் IMPORTANT -->
    {GLOBAL_ALARM_JS}

    </body>
    </html>
    '''
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
    {GLOBAL_ALARM_JS}
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
    {GLOBAL_ALARM_JS}
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
    
    subject = goal['subject'].strip().lower()
    if subject in ['maths', 'math', 'mathematics']:
         subject = 'mathematics'
    elif subject in ['tamil', 'tamil-1', 'tamil1']:
         subject = 'tamil-1'
    elif subject in ['english', 'english-1', 'eng1']:
         subject = 'english-1'

# 2nd sem
    elif subject in ['maths-2', 'math-2', 'mathematics-2']:
         subject = 'mathematics-2'
    elif subject in ['tamil-2']:
         subject = 'tamil-2'
    elif subject in ['english-2']:
         subject = 'english-2'

# 3rd sem
    elif subject in ['java', 'java programming', 'java-programming']:
         subject = 'java-programming'
    elif subject in ['statistics-1', 'stats1']:
         subject = 'statistics-1'
    elif subject in ['tamil-3']:
         subject = 'tamil-3'
    elif subject in ['english-3']:
         subject = 'english-3'
 
# 4th sem
    elif subject in ['data structure', 'data-structure']:
         subject = 'data-structure'
    elif subject in ['statistics-2', 'stats2']:
         subject = 'statistics-2'
    elif subject in ['tamil-4']:
         subject = 'tamil-4'
    elif subject in ['english-4']:
         subject = 'english-4'

# 5th sem
    elif subject in ['operating system', 'os']:
         subject = 'operating-system'
    elif subject in ['rdbms']:
         subject = 'rdbms'
    elif subject in ['software engineering', 'se']:
         subject = 'software-engineering'
    elif subject in ['data mining', 'data-warehousing', 'dm', 'dw']:
         subject = 'data-mining-warehousing'

# 6th sem
    elif subject in ['asp.net', 'programming in asp.net']:
         subject = 'asp-net'
    elif subject in ['data science']:
         subject = 'data-science'
    elif subject in ['cloud computing', 'cloud']:
         subject = 'cloud-computing'
    
    all_questions = {
        'mathematics': [
    {"q": "What is |−10| ?", "options": ["-10", "10", "0", "1"], "answer": "10"},
    {"q": "If A = {1,2,3} and B = {2,3,4}, what is A ∩ B?", "options": ["{1,2}", "{2,3}", "{3,4}", "{1,4}"], "answer": "{2,3}"},
    {"q": "Derivative of x³ is?", "options": ["3x²", "x²", "x³", "3x"], "answer": "3x²"},
    {"q": "∫ x dx = ?", "options": ["x²/2", "x", "1", "x³"], "answer": "x²/2"},
    {"q": "Value of sin(90°)?", "options": ["0", "1", "-1", "undefined"], "answer": "1"},
    {"q": "Matrix multiplication is possible when?", "options": ["Columns of first = Rows of second", "Same order","Square matrix only", "None"], "answer": "Columns of first = Rows of second"},
    {"q": "Limit of x → 0 of sinx/x = ?", "options": ["0", "1", "∞", "undefined"], "answer": "1"},
    {"q": "If f(x) = x², find f(2)", "options": ["2", "4", "8", "16"], "answer": "4"},
    {"q": "Determinant of matrix [[a,b],[c,d]] is?", "options": ["ad - bc", "a+b+c+d", "ab+cd", "a-b"], "answer": "ad - bc"},
    {"q": "Value of cos(0°)?", "options": ["0", "1", "-1", "undefined"], "answer": "1"}
],
        'python': [
    {"q": "Python is a ?", "options": ["Programming Language", "Game", "Browser", "OS"], "answer": "Programming Language"},
    {"q": "Which keyword is used to define a function?", "options": ["def", "fun", "function", "define"], "answer": "def"},
    {"q": "Which symbol is used for comments?", "options": ["//", "#", "/* */", "--"], "answer": "#"},
    {"q": "Output of print(2+3)?", "options": ["23", "5", "6", "Error"], "answer": "5"},
    {"q": "Which data type is used for text?", "options": ["int", "str", "float", "bool"], "answer": "str"},
    {"q": "Which is a loop?", "options": ["if", "for", "def", "print"], "answer": "for"},
    {"q": "len('abc') = ?", "options": ["2", "3", "4", "1"], "answer": "3"},
    {"q": "Which is a list?", "options": ["{}", "()", "[]", "<>"], "answer": "[]"},
    {"q": "Which operator is for power?", "options": ["^", "**", "*", "//"], "answer": "**"},
    {"q": "Which keyword is used for condition?", "options": ["loop", "if", "case", "switch"], "answer": "if"}
],
        'tamil-1': [
    {"q": "தமிழ் மொழி எது?", "options": ["வடமொழி", "தென்மொழி", "ஆங்கிலம்", "ஹிந்தி"], "answer": "தென்மொழி"},
    {"q": "உயிரெழுத்துகள் எத்தனை?", "options": ["10", "12", "18", "5"], "answer": "12"},
    {"q": "மெய்யெழுத்துகள் எத்தனை?", "options": ["12", "18", "10", "5"], "answer": "18"},
    {"q": "'அம்மா' என்பது எந்த வகை சொல்?", "options": ["பெயர்ச்சொல்", "வினைச்சொல்", "உரிச்சொல்", "வினையெச்சம்"], "answer": "பெயர்ச்சொல்"},
    {"q": "தமிழ் எழுத்துக்கள் மொத்தம்?", "options": ["247", "200", "300", "150"], "answer": "247"},
    {"q": "திருக்குறள் எழுதியவர் யார்?", "options": ["பாரதியார்", "திருவள்ளுவர்", "கம்பன்", "அவ்வையார்"], "answer": "திருவள்ளுவர்"},
    {"q": "வினைச்சொல் என்றால்?", "options": ["செயலைக் குறிக்கும் சொல்", "பெயரைச் சொல்", "உரிச்சொல்", "எண்"], "answer": "செயலைக் குறிக்கும் சொல்"},
    {"q": "'நான் பள்ளிக்குச் சென்றேன்' இதில் வினைச்சொல்?", "options": ["நான்", "பள்ளி", "சென்றேன்", "க்கு"], "answer": "சென்றேன்"},
    {"q": "உயிர்மெய்யெழுத்து உதாரணம்?", "options": ["அ", "க்", "க", "ம்"], "answer": "க"},
    {"q": "தமிழின் பழமையான நூல்?", "options": ["திருக்குறள்", "சிலப்பதிகாரம்", "தொல்காப்பியம்", "ராமாயணம்"], "answer": "தொல்காப்பியம்"}
],
         'english-1': [
    {"q": "What is a noun?", "options": ["Action", "Name", "Quality", "None"], "answer": "Name"},
    {"q": "Verb means?", "options": ["Action", "Place", "Thing", "Person"], "answer": "Action"},
    {"q": "He ___ going to school.", "options": ["is", "are", "am", "be"], "answer": "is"},
    {"q": "Plural of 'child'?", "options": ["childs", "children", "childes", "child"], "answer": "children"},
    {"q": "Opposite of 'good'?", "options": ["bad", "better", "best", "nice"], "answer": "bad"},
    {"q": "Past tense of 'go'?", "options": ["goed", "gone", "went", "goes"], "answer": "went"},
    {"q": "Which is a pronoun?", "options": ["he", "run", "book", "big"], "answer": "he"},
    {"q": "Which is an adjective?", "options": ["run", "big", "he", "play"], "answer": "big"},
    {"q": "Fill: She ___ a song.", "options": ["sing", "sings", "sang", "singing"], "answer": "sings"},
    {"q": "Article for 'apple'?", "options": ["a", "an", "the", "none"], "answer": "an"}
],
         'maths2': [
    {"q": "What is the rank of a matrix?", "options": ["No. of rows", "No. of columns", "Max no. of independent rows/columns", "Determinant"], "answer": "Max no. of independent rows/columns"},
    {"q": "Eigenvalues are found using?", "options": ["|A|", "|A - λI| = 0", "A+B", "A²"], "answer": "|A - λI| = 0"},
    {"q": "Derivative of sinx is?", "options": ["cosx", "-cosx", "tanx", "secx"], "answer": "cosx"},
    {"q": "∫ cosx dx = ?", "options": ["sinx", "-sinx", "cosx", "tanx"], "answer": "sinx"},
    {"q": "Value of e⁰ ?", "options": ["0", "1", "e", "-1"], "answer": "1"},
    {"q": "What is a vector?", "options": ["Scalar only", "Magnitude only", "Magnitude & direction", "Number"], "answer": "Magnitude & direction"},
    {"q": "Dot product result is?", "options": ["Vector", "Scalar", "Matrix", "None"], "answer": "Scalar"},
    {"q": "Cross product result is?", "options": ["Scalar", "Vector", "Number", "Matrix"], "answer": "Vector"},
    {"q": "∂/∂x (x² + y²) = ?", "options": ["2x", "2y", "x+y", "0"], "answer": "2x"},
    {"q": "L'Hospital rule is used for?", "options": ["Integration", "Indeterminate forms", "Matrix", "Trigonometry"], "answer": "Indeterminate forms"}
],
         'tamil-2': [
    {"q": "இலக்கியம் என்றால்?", "options": ["விளையாட்டு", "எழுத்து படைப்புகள்", "கணக்கு", "அறிவு"], "answer": "எழுத்து படைப்புகள்"},
    {"q": "சங்க இலக்கியம் எத்தனை காலம்?", "options": ["மூன்று", "இரண்டு", "நான்கு", "ஐந்து"], "answer": "மூன்று"},
    {"q": "புறநானூறு என்ன வகை நூல்?", "options": ["அகநூல்", "புறநூல்", "இலக்கணம்", "கவிதை இல்லை"], "answer": "புறநூல்"},
    {"q": "திருக்குறள் எத்தனை அதிகாரங்கள்?", "options": ["100", "133", "200", "150"], "answer": "133"},
    {"q": "கம்பராமாயணம் எழுதியவர்?", "options": ["வள்ளுவர்", "கம்பர்", "பாரதி", "அவ்வையார்"], "answer": "கம்பர்"},
    {"q": "உரைநடை என்றால்?", "options": ["கவிதை", "பாடல்", "சாதாரண மொழி", "இசை"], "answer": "சாதாரண மொழி"},
    {"q": "உவமை என்றால்?", "options": ["ஒப்பிடுதல்", "எண்ணிக்கை", "செயல்", "பெயர்"], "answer": "ஒப்பிடுதல்"},
    {"q": "அகநானூறு என்ன கூறுகிறது?", "options": ["போர்", "காதல்", "அரசு", "வரலாறு"], "answer": "காதல்"},
    {"q": "பாரதியார் யார்?", "options": ["கவிஞர்", "அரசர்", "விஞ்ஞானி", "ஆசிரியர்"], "answer": "கவிஞர்"},
    {"q": "தமிழ் இலக்கண நூல்?", "options": ["திருக்குறள்", "தொல்காப்பியம்", "ராமாயணம்", "மகாபாரதம்"], "answer": "தொல்காப்பியம்"}
],
          'english-2': [
    {"q": "What is a sentence?", "options": ["Group of words", "Complete meaning", "Letters", "None"], "answer": "Complete meaning"},
    {"q": "Types of sentences?", "options": ["4", "2", "3", "5"], "answer": "4"},
    {"q": "What is an adverb?", "options": ["Describes noun", "Describes verb", "Name", "Action"], "answer": "Describes verb"},
    {"q": "He is ___ honest man.", "options": ["a", "an", "the", "no article"], "answer": "an"},
    {"q": "Synonym of 'big'?", "options": ["small", "large", "tiny", "short"], "answer": "large"},
    {"q": "Antonym of 'happy'?", "options": ["sad", "joy", "fun", "good"], "answer": "sad"},
    {"q": "Present continuous tense?", "options": ["I eat", "I am eating", "I ate", "I will eat"], "answer": "I am eating"},
    {"q": "Plural of 'mouse'?", "options": ["mouses", "mice", "mouse", "meese"], "answer": "mice"},
    {"q": "Which is a preposition?", "options": ["in", "run", "big", "he"], "answer": "in"},
    {"q": "She ___ playing.", "options": ["is", "are", "am", "be"], "answer": "is"}
],
          'java': [
    {"q": "Java is a ?", "options": ["Programming Language", "OS", "Browser", "Database"], "answer": "Programming Language"},
    {"q": "Which keyword is used to create class?", "options": ["class", "define", "struct", "new"], "answer": "class"},
    {"q": "Main method syntax?", "options": ["public static void main(String[] args)","main()","void main()","static main()"], "answer": "public static void main(String[] args)"},
    {"q": "Which is not a data type?", "options": ["int", "float", "string", "boolean"], "answer": "string"},
    {"q": "Object is created using?", "options": ["new", "create", "make", "init"], "answer": "new"},
    {"q": "Inheritance means?", "options": ["Copy data", "Reuse properties", "Delete class", "Create loop"], "answer": "Reuse properties"},
    {"q": "Which symbol for single line comment?", "options": ["//", "#", "/* */", "--"], "answer": "//"},
    {"q": "Which is loop?", "options": ["if", "for", "class", "int"], "answer": "for"},
    {"q": "JVM stands for?", "options": ["Java Virtual Machine", "Java Variable Method", "Joint Virtual Machine", "Java Verified Machine"], "answer": "Java Virtual Machine"},
    {"q": "Java is platform ?", "options": ["dependent", "independent", "semi", "none"], "answer": "independent"}
],
         'statistics-1': [
    {"q": "Statistics is the study of?", "options": ["Data", "Numbers only", "Words", "None"], "answer": "Data"},
    {"q": "Mean formula?", "options": ["Σx/n", "Σx", "n/x", "x²"], "answer": "Σx/n"},
    {"q": "Median is?", "options": ["Middle value", "Average", "Highest", "Lowest"], "answer": "Middle value"},
    {"q": "Mode is?", "options": ["Most frequent value", "Least value", "Average", "Sum"], "answer": "Most frequent value"},
    {"q": "Range = ?", "options": ["Max - Min", "Min - Max", "Sum", "Mean"], "answer": "Max - Min"},
    {"q": "Variance measures?", "options": ["Spread", "Center", "Sum", "Count"], "answer": "Spread"},
    {"q": "Standard deviation is?", "options": ["√variance", "variance²", "mean", "range"], "answer": "√variance"},
    {"q": "Frequency means?", "options": ["Count", "Sum", "Average", "Range"], "answer": "Count"},
    {"q": "Graph used in statistics?", "options": ["Bar chart", "Circle", "Line", "All"], "answer": "All"},
    {"q": "Population means?", "options": ["Whole data", "Sample", "Part", "None"], "answer": "Whole data"}
],
         'tamil-3': [
    {"q": "சங்க காலம் எதை குறிக்கிறது?", "options": ["பழமையான தமிழ் இலக்கியம்", "இசை", "கணக்கு", "விளையாட்டு"], "answer": "பழமையான தமிழ் இலக்கியம்"},
    {"q": "புறநானூறு எந்த வகை?", "options": ["புறநூல்", "அகநூல்", "இலக்கணம்", "கவிதை இல்லை"], "answer": "புறநூல்"},
    {"q": "அகநானூறு எதைச் சொல்கிறது?", "options": ["காதல்", "போர்", "அரசு", "வரலாறு"], "answer": "காதல்"},
    {"q": "சிலப்பதிகாரம் எழுதியவர்?", "options": ["இளங்கோ அடிகள்", "வள்ளுவர்", "கம்பர்", "பாரதி"], "answer": "இளங்கோ அடிகள்"},
    {"q": "மணிமேகலை என்ன?", "options": ["காப்பியம்", "கவிதை", "கதை", "நாடகம்"], "answer": "காப்பியம்"},
    {"q": "பாரதியார் யார்?", "options": ["கவிஞர்", "அரசர்", "ஆசிரியர்", "விஞ்ஞானி"], "answer": "கவிஞர்"},
    {"q": "உவமை என்றால்?", "options": ["ஒப்பிடுதல்", "எண்ணிக்கை", "செயல்", "பெயர்"], "answer": "ஒப்பிடுதல்"},
    {"q": "திருக்குறள் எத்தனை அதிகாரம்?", "options": ["133", "100", "200", "150"], "answer": "133"},
    {"q": "தமிழ் இலக்கண நூல்?", "options": ["தொல்காப்பியம்", "திருக்குறள்", "ராமாயணம்", "மகாபாரதம்"], "answer": "தொல்காப்பியம்"},
    {"q": "உரைநடை என்றால்?", "options": ["சாதாரண மொழி", "கவிதை", "பாடல்", "இசை"], "answer": "சாதாரண மொழி"}
],
         'english-3': [
    {"q": "What is a paragraph?", "options": ["Group of sentences", "Word", "Letter", "None"], "answer": "Group of sentences"},
    {"q": "What is a synonym?", "options": ["Same meaning", "Opposite", "Action", "Name"], "answer": "Same meaning"},
    {"q": "Opposite of 'fast'?", "options": ["slow", "quick", "speed", "run"], "answer": "slow"},
    {"q": "He ___ finished work.", "options": ["has", "have", "had", "is"], "answer": "has"},
    {"q": "Past tense of 'write'?", "options": ["writed", "wrote", "written", "write"], "answer": "wrote"},
    {"q": "Which is a conjunction?", "options": ["and", "run", "big", "he"], "answer": "and"},
    {"q": "Future tense example?", "options": ["I go", "I went", "I will go", "I going"], "answer": "I will go"},
    {"q": "What is an adjective?", "options": ["Describes noun", "Action", "Name", "None"], "answer": "Describes noun"},
    {"q": "Plural of 'man'?", "options": ["mans", "men", "man", "mens"], "answer": "men"},
    {"q": "She ___ reading.", "options": ["is", "are", "am", "be"], "answer": "is"}
],
          'data_structures': [
    {"q": "Data structure is?", "options": ["Way of storing data", "Program", "Language", "OS"], "answer": "Way of storing data"},
    {"q": "Which is linear data structure?", "options": ["Tree", "Graph", "Array", "Heap"], "answer": "Array"},
    {"q": "Stack follows?", "options": ["FIFO", "LIFO", "Random", "None"], "answer": "LIFO"},
    {"q": "Queue follows?", "options": ["LIFO", "FIFO", "Random", "None"], "answer": "FIFO"},
    {"q": "Top element in stack is called?", "options": ["Front", "Top", "Rear", "End"], "answer": "Top"},
    {"q": "Insertion in queue is at?", "options": ["Front", "Rear", "Top", "Middle"], "answer": "Rear"},
    {"q": "Deletion in queue is at?", "options": ["Front", "Rear", "Top", "Middle"], "answer": "Front"},
    {"q": "Which is non-linear structure?", "options": ["Array", "Stack", "Tree", "Queue"], "answer": "Tree"},
    {"q": "Binary tree max children?", "options": ["1", "2", "3", "4"], "answer": "2"},
    {"q": "Linked list uses?", "options": ["Contiguous memory", "Pointers", "Index only", "None"], "answer": "Pointers"}
],
          'statistics-2': [
    {"q": "Probability value range?", "options": ["0 to 1", "-1 to 1", "0 to 10", "1 to 100"], "answer": "0 to 1"},
    {"q": "P(A) + P(A') = ?", "options": ["1", "0", "2", "A"], "answer": "1"},
    {"q": "Independent events mean?", "options": ["No effect on each other", "Same event", "Dependent", "None"], "answer": "No effect on each other"},
    {"q": "Binomial distribution is used for?", "options": ["Two outcomes", "Many outcomes", "Continuous data", "None"], "answer": "Two outcomes"},
    {"q": "Mean of binomial?", "options": ["np", "n+p", "p/n", "n²"], "answer": "np"},
    {"q": "Variance of binomial?", "options": ["npq", "np", "n²", "pq"], "answer": "npq"},
    {"q": "Normal distribution shape?", "options": ["Bell", "Square", "Triangle", "Line"], "answer": "Bell"},
    {"q": "Correlation measures?", "options": ["Relationship", "Sum", "Count", "Range"], "answer": "Relationship"},
    {"q": "Correlation coefficient range?", "options": ["-1 to 1", "0 to 1", "0 to 10", "-10 to 10"], "answer": "-1 to 1"},
    {"q": "Regression is used for?", "options": ["Prediction", "Counting", "Sorting", "None"], "answer": "Prediction"}
],
          'tamil-4': [
    {"q": "நவீன தமிழ் இலக்கியம் என்றால்?", "options": ["புதிய படைப்புகள்", "பழைய நூல்கள்", "இசை", "கணக்கு"], "answer": "புதிய படைப்புகள்"},
    {"q": "பாரதியார் என்ன புகழ்?", "options": ["தேசியக் கவிஞர்", "அரசர்", "விஞ்ஞானி", "ஆசிரியர்"], "answer": "தேசியக் கவிஞர்"},
    {"q": "புதுக்கவிதை என்றால்?", "options": ["புதிய வடிவ கவிதை", "பழைய கவிதை", "பாடல்", "இசை"], "answer": "புதிய வடிவ கவிதை"},
    {"q": "கட்டுரை என்றால்?", "options": ["விவரிப்பு", "கவிதை", "பாடல்", "இசை"], "answer": "விவரிப்பு"},
    {"q": "உரைநடை பயன்பாடு?", "options": ["எளிய மொழி", "கவிதை", "இசை", "கணக்கு"], "answer": "எளிய மொழி"},
    {"q": "படைப்பில் உவமை பயன்பாடு?", "options": ["அழகு சேர்க்க", "கணக்கு", "செயல்", "பெயர்"], "answer": "அழகு சேர்க்க"},
    {"q": "தமிழ் நாவல் என்றால்?", "options": ["நீண்ட கதை", "சிறுகதை", "கவிதை", "பாடல்"], "answer": "நீண்ட கதை"},
    {"q": "சிறுகதை என்றால்?", "options": ["குறுகிய கதை", "நீண்ட கதை", "கவிதை", "இசை"], "answer": "குறுகிய கதை"},
    {"q": "இலக்கியத்தின் நோக்கம்?", "options": ["அறிவு & மகிழ்ச்சி", "கணக்கு", "விளையாட்டு", "None"], "answer": "அறிவு & மகிழ்ச்சி"},
    {"q": "தமிழ் வளர்ச்சி எதனால்?", "options": ["இலக்கியம்", "கணக்கு", "விளையாட்டு", "None"], "answer": "இலக்கியம்"}
],
          'english-4': [
    {"q": "What is an essay?", "options": ["Short writing", "Long writing", "Word", "Letter"], "answer": "Long writing"},
    {"q": "What is a letter?", "options": ["Communication", "Story", "Poem", "None"], "answer": "Communication"},
    {"q": "Formal letter is used for?", "options": ["Official purpose", "Friends", "Story", "None"], "answer": "Official purpose"},
    {"q": "Informal letter is used for?", "options": ["Friends", "Office", "Government", "None"], "answer": "Friends"},
    {"q": "What is comprehension?", "options": ["Understanding", "Writing", "Reading only", "None"], "answer": "Understanding"},
    {"q": "Synonym of 'easy'?", "options": ["simple", "hard", "tough", "difficult"], "answer": "simple"},
    {"q": "Antonym of 'strong'?", "options": ["weak", "powerful", "big", "fast"], "answer": "weak"},
    {"q": "He ___ a letter.", "options": ["writes", "write", "writing", "wrote"], "answer": "writes"},
    {"q": "Past tense of 'eat'?", "options": ["eated", "ate", "eat", "eaten"], "answer": "ate"},
    {"q": "She ___ going to college.", "options": ["is", "are", "am", "be"], "answer": "is"}
],
          'operating_system': [
    {"q": "Operating System is?", "options": ["Interface between user & hardware", "Application", "Compiler", "Language"], "answer": "Interface between user & hardware"},
    {"q": "Which is not an OS?", "options": ["Windows", "Linux", "Oracle", "Android"], "answer": "Oracle"},
    {"q": "Process is?", "options": ["Program in execution", "Program", "File", "Memory"], "answer": "Program in execution"},
    {"q": "CPU scheduling is?", "options": ["Process management", "Memory", "File", "None"], "answer": "Process management"},
    {"q": "Deadlock means?", "options": ["No progress", "Fast process", "Execution", "None"], "answer": "No progress"},
    {"q": "Which is scheduling algorithm?", "options": ["FCFS", "SQL", "HTML", "Python"], "answer": "FCFS"},
    {"q": "Memory unit?", "options": ["Byte", "Meter", "Second", "Liter"], "answer": "Byte"},
    {"q": "Virtual memory is?", "options": ["Extension of RAM", "Disk only", "CPU", "None"], "answer": "Extension of RAM"},
    {"q": "File system manages?", "options": ["Files", "CPU", "Memory", "Network"], "answer": "Files"},
    {"q": "Kernel is?", "options": ["Core of OS", "Application", "File", "None"], "answer": "Core of OS"}
],
          'rdbms': [
    {"q": "RDBMS stands for?", "options": ["Relational Database Management System", "Random Data System", "Real DB System", "None"], "answer": "Relational Database Management System"},
    {"q": "Table is also called?", "options": ["Relation", "Row", "Column", "Key"], "answer": "Relation"},
    {"q": "Primary key is?", "options": ["Unique identifier", "Duplicate", "Null", "None"], "answer": "Unique identifier"},
    {"q": "Foreign key is?", "options": ["Link between tables", "Primary", "Null", "None"], "answer": "Link between tables"},
    {"q": "SQL is used for?", "options": ["Database", "Design", "Hardware", "Network"], "answer": "Database"},
    {"q": "SELECT is?", "options": ["DML", "DDL", "DCL", "TCL"], "answer": "DML"},
    {"q": "CREATE is?", "options": ["DDL", "DML", "DCL", "TCL"], "answer": "DDL"},
    {"q": "DELETE removes?", "options": ["Rows", "Table", "Column", "Database"], "answer": "Rows"},
    {"q": "Normalization is?", "options": ["Reduce redundancy", "Increase data", "Delete data", "None"], "answer": "Reduce redundancy"},
    {"q": "JOIN is used for?", "options": ["Combine tables", "Delete", "Update", "Insert"], "answer": "Combine tables"}
],
          'software_engineering': [
    {"q": "Software Engineering is?", "options": ["Systematic development", "Random coding", "Hardware", "None"], "answer": "Systematic development"},
    {"q": "SDLC stands for?", "options": ["Software Development Life Cycle", "System Design Logic Cycle", "Software Data Life Cycle", "None"], "answer": "Software Development Life Cycle"},
    {"q": "First phase of SDLC?", "options": ["Requirement", "Testing", "Coding", "Maintenance"], "answer": "Requirement"},
    {"q": "Waterfall model is?", "options": ["Sequential", "Random", "Circular", "None"], "answer": "Sequential"},
    {"q": "Testing ensures?", "options": ["Quality", "Speed", "Design", "None"], "answer": "Quality"},
    {"q": "Bug is?", "options": ["Error", "Feature", "Design", "None"], "answer": "Error"},
    {"q": "Maintenance phase?", "options": ["After delivery", "Before coding", "Design", "None"], "answer": "After delivery"},
    {"q": "Agile model is?", "options": ["Iterative", "Sequential", "Static", "None"], "answer": "Iterative"},
    {"q": "UML is used for?", "options": ["Design", "Coding", "Testing", "None"], "answer": "Design"},
    {"q": "Version control?", "options": ["Track changes", "Delete code", "Run program", "None"], "answer": "Track changes"}
],
          'DMW': [
    {"q": "Data mining is?", "options": ["Extract knowledge", "Delete data", "Store data", "None"], "answer": "Extract knowledge"},
    {"q": "Data warehouse is?", "options": ["Central storage", "Temporary data", "File", "None"], "answer": "Central storage"},
    {"q": "OLAP stands for?", "options": ["Online Analytical Processing","Online Application Program","Offline Data","None"], "answer": "Online Analytical Processing"},
    {"q": "OLTP is used for?", "options": ["Transactions", "Analysis", "Storage", "None"], "answer": "Transactions"},
    {"q": "ETL means?", "options": ["Extract Transform Load", "Edit Transfer Load", "Enter Transfer Load", "None"], "answer": "Extract Transform Load"},
    {"q": "Clustering is?", "options": ["Grouping data", "Sorting", "Deleting", "None"], "answer": "Grouping data"},
    {"q": "Classification is?", "options": ["Assign class", "Delete", "Sort", "None"], "answer": "Assign class"},
    {"q": "Data cleaning?", "options": ["Remove errors", "Add data", "Delete all", "None"], "answer": "Remove errors"},
    {"q": "Warehouse stores?", "options": ["Historical data", "Current only", "None", "Temporary"], "answer": "Historical data"},
    {"q": "Data mart is?", "options": ["Subset of warehouse", "Full DB", "File", "None"], "answer": "Subset of warehouse"}
],
           'asp': [
    {"q": "ASP.NET is?", "options": ["Web framework", "OS", "Database", "Language"], "answer": "Web framework"},
    {"q": "ASP stands for?", "options": ["Active Server Pages","Advanced Server Program","Application Server Page","None"], "answer": "Active Server Pages"},
    {"q": ".NET is developed by?", "options": ["Microsoft", "Google", "Apple", "IBM"], "answer": "Microsoft"},
    {"q": "Code behind file extension?", "options": [".cs", ".html", ".js", ".py"], "answer": ".cs"},
    {"q": "ASP.NET uses?", "options": ["C#", "Java", "Python", "C++"], "answer": "C#"},
    {"q": "Which is web control?", "options": ["TextBox", "Scanner", "Printer", "CPU"], "answer": "TextBox"},
    {"q": "ViewState is used for?", "options": ["Store page data", "Delete data", "Run code", "None"], "answer": "Store page data"},
    {"q": "Postback means?", "options": ["Reload page", "Close page", "Open file", "None"], "answer": "Reload page"},
    {"q": "MVC stands for?", "options": ["Model View Controller", "Main View Control", "Model Version Control", "None"], "answer": "Model View Controller"},
    {"q": "Web.config file is used for?", "options": ["Configuration", "Coding", "Design", "None"], "answer": "Configuration"}
],
          'data_science': [
    {"q": "Data Science is?", "options": ["Study of data", "Hardware", "Network", "None"], "answer": "Study of data"},
    {"q": "Which language is popular in Data Science?", "options": ["Python", "HTML", "CSS", "XML"], "answer": "Python"},
    {"q": "Data analysis means?", "options": ["Process data", "Delete data", "Store data", "None"], "answer": "Process data"},
    {"q": "Machine learning is?", "options": ["Learning from data", "Manual coding", "Hardware", "None"], "answer": "Learning from data"},
    {"q": "Supervised learning uses?", "options": ["Labeled data", "No data", "Random", "None"], "answer": "Labeled data"},
    {"q": "Unsupervised learning?", "options": ["No labels", "Labels", "Manual", "None"], "answer": "No labels"},
    {"q": "Dataset is?", "options": ["Collection of data", "Single value", "Code", "None"], "answer": "Collection of data"},
    {"q": "Visualization means?", "options": ["Graphs", "Code", "Text", "None"], "answer": "Graphs"},
    {"q": "Algorithm is?", "options": ["Step by step process", "Random", "None", "Data"], "answer": "Step by step process"},
    {"q": "AI stands for?", "options": ["Artificial Intelligence", "Automatic Input", "Advanced Internet", "None"], "answer": "Artificial Intelligence"}
],  
          'cloud_computing': [
    {"q": "Cloud computing is?", "options": ["Internet-based computing", "Local system", "Hardware", "None"], "answer": "Internet-based computing"},
    {"q": "Cloud provides?", "options": ["Services", "Only storage", "Only CPU", "None"], "answer": "Services"},
    {"q": "IaaS stands for?", "options": ["Infrastructure as a Service", "Internet as Service", "Internal Service", "None"], "answer": "Infrastructure as a Service"},
    {"q": "PaaS stands for?", "options": ["Platform as a Service", "Program as Service", "Public Service", "None"], "answer": "Platform as a Service"},
    {"q": "SaaS stands for?", "options": ["Software as a Service", "System as Service", "Server as Service", "None"], "answer": "Software as a Service"},
    {"q": "Example of cloud?", "options": ["Google Drive", "Pen Drive", "Hard Disk", "CPU"], "answer": "Google Drive"},
    {"q": "Cloud storage is?", "options": ["Online storage", "Offline", "Local", "None"], "answer": "Online storage"},
    {"q": "Public cloud is?", "options": ["Open to all", "Private", "Local", "None"], "answer": "Open to all"},
    {"q": "Private cloud is?", "options": ["Single organization", "Public", "Internet", "None"], "answer": "Single organization"},
    {"q": "Hybrid cloud is?", "options": ["Mix of public & private", "Only public", "Only private", "None"], "answer": "Mix of public & private"}
]
    }
    
    quiz_questions = questions.get(subject, [])
    
    if not quiz_questions:
        # ✅ function உள்ஆக return பண்ணணும்
        return render_template_string("<h3>No questions found for this subject.</h3>")
        # render quiz template (example)
        return render_template('quiz.html', questions=quiz_questions, subject=subject)
    
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
        {GLOBAL_ALARM_JS}
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
    {GLOBAL_ALARM_JS}
    </body></html>
    '''
    
@app.route('/view-goals')
def view_goals():
    if not session.get('logged_in'): return redirect('/')
    conn = get_db_connection()
    goals = conn.execute("SELECT * FROM goals WHERE email=? ORDER BY progress DESC", 
                        (session['email'],)).fetchall()
    conn.close()
    
    goals_html = ""
    for goal in goals:
        progress_bar = f'<div style="background:#ddd;height:25px;border-radius:12px;overflow:hidden"><div style="background:linear-gradient(90deg,#50c878,#27ae60);width:{goal["progress"]}% height:100%;transition:width 0.5s"></div></div>'
        goals_html += f'''
        <div style="background:rgba(255,255,255,0.2);padding:30px;margin:20px;border-radius:20px">
            <h3>{goal["subject"]} - {goal["goal"]}</h3>
            <p>Target: {goal["target_score"]}% | Progress: {goal["progress"]}% | Best: {goal["max_score"]}/10</p>
            {progress_bar}
            <a href="/quiz/{goal['id']}" style="padding:12px 25px;background:#3498db;color:white;text-decoration:none;border-radius:10px;margin-top:15px;display:inline-block">📝 Take Quiz</a>
        </div>
        '''
    
    return f'''
<!DOCTYPE html>
<html><head><title>My Goals</title>
<style>body{{font-family:'Segoe UI';background:linear-gradient(135deg,#667eea,#764ba2);color:white;min-height:100vh;padding:30px}}.container{{max-width:900px;margin:0 auto}}</style></head>
<body>
<a href="/dashboard" style="position:fixed;top:20px;left:20px;padding:15px 25px;background:#f39c12;color:white;text-decoration:none;border-radius:15px;font-weight:600">← Dashboard</a>
<div class="container">
    <h1 style="text-align:center;font-size:42px;margin:80px 0 40px">🎯 My Study Goals</h1>
    {goals_html or '<p style="text-align:center;font-size:28px;color:#f1c40f">No goals set yet! <a href="/goals" style="color:#50c878">Create one →</a></p>'}
</div>
{GLOBAL_ALARM_JS}
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

# 🔥 RENDER.COM PORT FIX 🔥
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
