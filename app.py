from flask import Flask, request, redirect, session, render_template_string, send_from_directory, jsonify, url_for 
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import json
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import threading
import time
import os

app = Flask(__name__)
db = SQLAlchemy()

# Config
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///reminders.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'

db.init_app(app)

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(100), nullable=False)
    seconds = db.Column(db.Integer, nullable=False)
    trigger_time = db.Column(db.DateTime)
    is_triggered = db.Column(db.Boolean, default=False)
    is_dismissed = db.Column(db.Boolean, default=False)

# Background thread
check_thread = None

def check_reminders():
    global check_thread
    def loop():
        while True:
            try:
                now = datetime.utcnow()
                due = Reminder.query.filter(
                    Reminder.trigger_time <= now,
                    Reminder.is_triggered == False
                ).all()
                for r in due:
                    print(f"🔔 {r.task}")
                    r.is_triggered = True
                    db.session.commit()
                time.sleep(3)
            except:
                time.sleep(5)
    
    if check_thread is None or not check_thread.is_alive():
        check_thread = threading.Thread(target=loop, daemon=True)
        check_thread.start()

# Fixed GLOBAL_ALARM_JS - completed audio URLs and syntax
GLOBAL_ALARM_JS = '''
<script>
let firedAlarms = new Set();

document.addEventListener("DOMContentLoaded", function() {
    console.log("🎵 SOUND ALARM LOADED");
    
    setInterval(() => {
        fetch("/api/user-alarms")
        .then(r => r.json())
        .then(data => {
            const now = new Date();
            data.forEach(alarm => {
                if(new Date(alarm.deadline) <= now && !firedAlarms.has(alarm.id)) {
                    firedAlarms.add(alarm.id);
                    console.log("🚨 TRIGGER ALARM:", alarm.title);
                    playAlarmSound(alarm.title);
                }
            });
        });
    }, 2000);
});

function playAlarmSound(title) {
    // Fixed audio URLs
    const audio = new Audio("https://freesound.org/data/previews/316/316847_4939433-lq.mp3");
    audio.volume = 1.0;
    audio.play().catch(e => console.log("Audio play failed:", e));
    
    // Backup beep sound
    playBeepSound();
    
    // VISUAL EXPLOSION
    document.body.innerHTML += `
        <div style="
            position:fixed;top:0;left:0;width:100vw;height:100vh;
            background:rgba(255,0,0,0.8);z-index:9999;display:flex;align-items:center;
            justify-content:center;font-size:50px;font-weight:bold;text-shadow:0 0 20px #fff;
            animation: pulse 1s infinite;" 
            onclick="this.remove()">
            🚨 ${title.toUpperCase()} 🚨
        </div>
    `;
    
    // Screen shake
    document.body.classList.add('shake');
    setTimeout(() => document.body.classList.remove('shake'), 2000);
}

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
                o.start(ctx.currentTime); o.stop(ctx.currentTime + 0.5);
            } catch(e) {}
        }, i*600);
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
'''

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
                  email TEXT, title TEXT, deadline TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS files 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT, subject TEXT, filename TEXT, 
                  upload_date TEXT)''')
    conn.commit()
    conn.close()

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

@app.route('/set-reminder', methods=['POST'])
def set_reminder():
    task = request.form['task']
    seconds = int(request.form['seconds'])
    
    reminder = Reminder(
        task=task,
        seconds=seconds,
        trigger_time=datetime.utcnow() + timedelta(seconds=seconds)
    )
    db.session.add(reminder)
    db.session.commit()
    
    check_reminders()
    return redirect(url_for('dashboard'))

@app.route('/dismiss/<int:id>')
def dismiss(id):
    reminder = Reminder.query.get(id)
    if reminder:
        reminder.is_dismissed = True
        db.session.commit()
    return redirect(url_for('dashboard'))

# CREATE TABLES & START CHECKER
with app.app_context():
    db.create_all()
    check_reminders()

@app.route('/')
def home():
    recent = Reminder.query.order_by(Reminder.id.desc()).limit(5).all()
    return f'''
    <h1>📚 Study Reminder</h1>
    <form action="/set-reminder" method="post">
        Task: <input name="task" required>
        Seconds: <input name="seconds" value="30" required>
        <button>Set</button>
    </form>
    <h3>Recent: {len(recent)}</h3>
    <a href="/dashboard">Dashboard</a>
    '''
    
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'): 
        return redirect('/')
    
    # SQLAlchemy reminders
    now = datetime.utcnow()
    reminders_sql = Reminder.query.filter(
        Reminder.trigger_time <= now,
        Reminder.is_triggered == True,
        Reminder.is_dismissed == False
    ).all()
    
    # SQLite reminders  
    conn = get_db_connection()
    reminders_sqlite = conn.execute("SELECT * FROM reminders WHERE email=?", 
                                   (session.get('email',''),)).fetchall()
    conn.close()
    
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
        <a href="/myfiles" class="btn">📁 My Files</a>
        <a href="/logout" class="btn" style="background:linear-gradient(135deg,#e74c3c,#c0392b)">🚪 Logout</a>
<button onclick="localStorage.removeItem('firedAlarms');location.reload();" 
        style="background:orange;color:white;padding:20px;border-radius:15px;font-size:18px">
    🗑️ Clear All Alarms (Test Use)
</button>
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
    alarms = conn.execute("SELECT id, title, deadline FROM reminders WHERE email=?", 
                         (session['email'],)).fetchall()
    conn.close()
    return jsonify([{'id': a['id'], 'title': a['title'], 'deadline': a['deadline']} for a in alarms])

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
    {GLOBAL_ALARM_JS}
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
