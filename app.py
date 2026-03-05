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
import secrets

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(24)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

# Create necessary folders
os.makedirs('static/uploads', exist_ok=True)

# Initialize SQLite Database - FIXED
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
                  email TEXT, title TEXT, deadline TEXT, 
                  notified INTEGER DEFAULT 0)''')  # notified column added
    conn.commit()
    conn.close()

init_db()

# Email Configuration
GMAIL_USER = os.environ.get('GMAIL_USER', "your-gmail@gmail.com")
GMAIL_PASS = os.environ.get('GMAIL_PASS', "your-16-digit-app-password")

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

# FIXED check_notifications - NO SPAM EMAILS
def check_notifications():
    conn = get_db_connection()
    email = session.get('email', '')
    now = datetime.now()
    
    overdue = conn.execute("""
        SELECT * FROM reminders 
        WHERE email=? AND datetime(deadline) <= ? AND notified=0
    """, (email, now.isoformat())).fetchall()
    
    notifications = ""
    for reminder in overdue:
        send_email(email, "🚨 Study Reminder - OVERDUE", 
                  f"Your reminder '{reminder['title']}' was due at {reminder['deadline']}!")
        conn.execute("UPDATE reminders SET notified=1 WHERE id=?", (reminder['id'],))
        notifications += f'<div class="notification">🚨 <strong>{reminder["title"]}</strong> - Deadline Passed!</div>'
    
    conn.commit()
    conn.close()
    return notifications

# File upload security
ALLOWED_EXTENSIONS = {'pdf'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes remain SAME as your original code until view_goals...
# ... (all your study routes same until line 650)

@app.route('/view-goals')  # FIXED SYNTAX ERROR HERE
def view_goals():
    if not session.get('logged_in'): 
        return redirect('/')
    
    conn = get_db_connection()
    goals = conn.execute('SELECT * FROM goals WHERE email=?', (session['email'],)).fetchall()
    conn.close()
    
    goals_html = ''
    for goal in goals:
        progress_width = min(goal['progress'] * 5, 100)
        goals_html += f'''
<div style="background:rgba(255,255,255,0.15);padding:30px;margin:20px auto;border-radius:20px;max-width:600px;text-align:left;box-shadow:0 10px 30px rgba(0,0,0,0.2);">
    <h3 style="margin:0 0 15px 0;color:#fff;">{goal["subject"]} 
        <a href="/delete_goal/{goal["id"]}" style="float:right;color:#ff4444;font-size:24px;text-decoration:none;font-weight:bold;" 
           onclick="return confirm('Delete this goal?')">🗑️</a>
    </h3>
    <p style="margin:10px 0;"><strong>🎯 Goal:</strong> {goal["goal"]}</p>
    <p style="margin:10px 0;"><strong>Target Score:</strong> {goal["target_score"]} | <strong>Study Hours:</strong> {goal["study_hours"]}</p>
    <div style="background:#333;height:25px;border-radius:12px;overflow:hidden;margin:15px 0;">
        <div style="width:{progress_width}%;background:linear-gradient(90deg,#50c878,#27ae60);height:100%;transition:width 0.5s;border-radius:12px;"></div>
    </div>
    <p style="margin:5px 0;font-weight:600;color:#f1c40f;">Progress: {goal["progress"] * 5}%</p>
</div>
'''
    
    return f'''
<!DOCTYPE html>
<html><head><title>Your Goals</title>
<style>
body{{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px}}
.container{{max-width:900px;margin:0 auto;text-align:center}}
.notification{{background:rgba(231,76,60,0.9);padding:20px;border-radius:15px;margin:20px auto;font-size:20px;max-width:600px;box-shadow:0 10px 30px rgba(231,76,60,0.4)}}
</style></head>
<body>
<div class="container">
    <h1 style="font-size:42px;margin-bottom:50px;text-shadow:0 2px 10px rgba(0,0,0,0.3);">📊 Your Goals</h1>
    {goals_html or '<div style="text-align:center;font-size:28px;padding:80px;background:rgba(255,255,255,0.1);border-radius:25px;box-shadow:0 10px 30px rgba(0,0,0,0.2)"><p>🎯 No goals set yet!</p><a href="/goals" style="color:#f1c40f;font-size:32px;font-weight:600;text-decoration:none;">Set goals now!</a></div>'}
    <div style="margin-top:50px">
        <a href="/dashboard" style="padding:20px 50px;background:linear-gradient(135deg,#f39c12,#e67e22);color:white;text-decoration:none;border-radius:20px;font-size:22px;font-weight:600;display:inline-block;box-shadow:0 10px 30px rgba(243,156,18,0.4)">← Back to Dashboard</a>
    </div>
</div>
</body></html>
'''

# FIXED upload route with security
@app.route('/upload/<subject_name>/<unit_num>', methods=['GET', 'POST'])
def upload_unit(subject_name, unit_num):
    if not session.get('logged_in'): return redirect('/')
    
    if request.method == 'POST':
        if 'file' not in request.files:
            return '<h1 style="color:red;text-align:center;padding:50px;">No file selected!</h1>'
        file = request.files['file']
        if file.filename == '':
            return '<h1 style="color:red;text-align:center;padding:50px;">No file selected!</h1>'
        
        # SECURITY CHECKS
        if file and allowed_file(file.filename) and file.mimetype == 'application/pdf':
            os.makedirs(f'static/uploads/{subject_name}', exist_ok=True)
            filename = secure_filename(f"unit{unit_num}.pdf")
            file.save(f'static/uploads/{subject_name}/{filename}')
            return f'''
            <div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;display:flex;align-items:center;justify-content:center;flex-direction:column;padding:50px;text-align:center">
            <h1 style="font-size:50px;color:#2ecc71">✅ Success!</h1>
            <p style="font-size:24px;margin:30px 0">{subject_name.replace("-"," ").title()} Unit {unit_num} uploaded!</p>
            <a href="/subject/{subject_name}" style="padding:20px 50px;background:#27ae60;color:white;text-decoration:none;border-radius:15px;font-size:22px;font-weight:600;box-shadow:0 10px 30px rgba(39,174,96,0.4)">← Back to {subject_name.replace("-"," ").title()}</a>
            </div>
            '''
        else:
            return f'''
            <div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;display:flex;align-items:center;justify-content:center;flex-direction:column;padding:50px;text-align:center">
            <h1 style="font-size:50px;color:#e74c3c">❌ Invalid File!</h1>
            <p style="font-size:24px;margin:30px 0">Only PDF files allowed (≤16MB)</p>
            <a href="/upload/{subject_name}/{unit_num}" style="padding:20px 50px;background:#3498db;color:white;text-decoration:none;border-radius:15px;font-size:22px;font-weight:600">← Try Again</a>
            </div>
            '''
    
    # GET HTML same as original
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
    <a href="/subject/{subject_name}" style="color:#3498db;font-size:22px;font-weight:600">← Back to {subject_name.replace("-"," ").title()}</a>
    </body></html>
    '''

# Keep all your other original routes (login, dashboard, study, etc.) exactly same...

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
