from flask import Flask, request, redirect, session, send_from_directory, render_template_string
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
import json
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'study2026-super-secure-key-2026')

# Create necessary folders
os.makedirs('static/uploads', exist_ok=True)
os.makedirs('static/reminders', exist_ok=True)

# User database - Add your own users here
users = {
    'test@test.com': {'password': '123456', 'name': 'Student'},
    # Add more users like this:
    # 'student1@gmail.com': {'password': 'pass123', 'name': 'Ravi'},
    # 'student2@yahoo.com': {'password': 'mypassword', 'name': 'Priya'},
}

# Email configuration - Set these in your hosting platform's environment variables
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USER = os.environ.get('SMTP_USER', 'your-email@gmail.com')
SMTP_PASS = os.environ.get('SMTP_PASS', 'your-app-password')

reminders_file = 'static/reminders.json'

def load_reminders():
    try:
        with open(reminders_file, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_reminders(reminders):
    with open(reminders_file, 'w') as f:
        json.dump(reminders, f)

def send_email(to_email, subject, body):
    try:
        msg = MimeMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MimeText(body, 'html'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        text = msg.as_string()
        server.sendmail(SMTP_USER, to_email, text)
        server.quit()
        return True
    except:
        return False

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password']
        
        if email in users and users[email]['password'] == password:
            session['logged_in'] = True
            session['email'] = email
            session['name'] = users[email]['name']
            
            # Check for overdue reminders on login
            check_and_notify_reminders(email)
            
            return redirect('/dashboard')
        else:
            return render_login("❌ Wrong Credentials!")
    
    return render_login("Create your account in users dict above!")

def render_login(message):
    return f'''
    <!DOCTYPE html>
    <html><head><title>Study Planner Login</title>
    <style>
    body{{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;display:flex;align-items:center;justify-content:center}}
    .login-box{{background:white;color:#333;padding:40px;border-radius:15px;box-shadow:0 15px 35px rgba(0,0,0,0.1);width:350px}}
    input{{width:100%;padding:15px;margin:10px 0;font-size:16px;border:2px solid #ddd;border-radius:8px;box-sizing:border-box}}
    button{{width:100%;padding:15px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:8px;font-size:18px;cursor:pointer;font-weight:bold}}
    </style></head>
    <body><div class="login-box">
    <h1>🎓 Study Planner</h1>
    <p style="color:#e74c3c">{message}</p>
    <form method="POST">
    <input type="email" name="email" placeholder="Email" required>
    <input type="password" name="password" placeholder="Password" required>
    <button type="submit">Login</button>
    </form>
    <p><b>Demo:</b> test@test.com / 123456</p>
    <p><small>Add users in <code>users</code> dict above!</small></p>
    </div></body></html>
    '''

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'): 
        return redirect('/')
    
    notifications = check_notifications()
    return f'''
    <!DOCTYPE html>
    <html><head><title>Dashboard</title>
    <style>body{{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}}
    .btn{{display:inline-block;padding:20px 40px;margin:15px;background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);color:white;text-decoration:none;border-radius:15px;font-size:20px;font-weight:bold}}
    .btn:hover{{transform:translateY(-3px)}}
    .notification{{background:#e74c3c;padding:15px;border-radius:10px;margin:20px;font-size:18px;box-shadow:0 5px 15px rgba(0,0,0,0.3)}}
    h1{{font-size:36px;margin-bottom:20px}}</style></head>
    <body>
    <h1>Welcome {session['name']}! 🎓</h1><h2>Study Planner App</h2>
    {notifications}
    <a href="/study" class="btn">📚 Study Dashboard</a>
    <a href="/goals" class="btn">🎯 Set Goals</a>
    <a href="/view-goals" class="btn">📊 View Goals</a>
    <a href="/reminders" class="btn">⏰ Reminders</a>
    <a href="/logout" class="btn" style="background:linear-gradient(135deg,#e74c3c,#c0392b)">🚪 Logout</a>
    </body></html>
    '''

def check_notifications():
    reminders = load_reminders()
    email = session.get('email', '')
    now = datetime.now()
    
    notifications = []
    for reminder_id, reminder in reminders.items():
        if reminder.get('email') == email:
            deadline = datetime.fromisoformat(reminder['deadline'])
            if deadline <= now:
                notifications.append(f'''
                <div class="notification">
                🚨 <b>{reminder["title"]}</b><br>
                Deadline Passed! 📅 {deadline.strftime('%Y-%m-%d %H:%M')}
                </div>''')
    
    return ''.join(notifications)

def check_and_notify_reminders(email):
    """Check reminders and send email notifications"""
    reminders = load_reminders()
    now = datetime.now()
    
    for reminder_id, reminder in reminders.items():
        if reminder.get('email') == email and not reminder.get('notified', False):
            deadline = datetime.fromisoformat(reminder['deadline'])
            if deadline <= now:
                # Send email notification
                subject = f"🚨 Study Reminder: {reminder['title']} - OVERDUE!"
                body = f"""
                <h2>🚨 Study Reminder Overdue!</h2>
                <p><b>{reminder['title']}</b></p>
                <p><b>Deadline:</b> {deadline.strftime('%Y-%m-%d %H:%M')}</p>
                <p>Login to your Study Planner to mark as complete!</p>
                """
                if send_email(email, subject, body):
                    reminder['notified'] = True
                    save_reminders(reminders)

# Subject pages with 10 units (keeping same as before)
@app.route('/subject/<subject_name>')
def subject_notes(subject_name):
    if not session.get('logged_in'): return redirect('/')
    
    units_html = ''
    for i in range(1, 11):
        unit_file = f"static/uploads/{subject_name}/unit{i}.pdf"
        download_link = f"/download/{subject_name}/unit{i}.pdf"
        upload_link = f"/upload/{subject_name}/unit{i}"
        has_file = os.path.exists(unit_file)
        
        units_html += f'''
        <div style="display:inline-block;margin:10px;background:rgba(255,255,255,0.1);padding:20px;border-radius:15px;width:200px">
            <h3>📚 Unit {i}</h3>
            <a href="{upload_link}" style="display:block;padding:10px;background:#3498db;color:white;text-decoration:none;border-radius:8px;margin:5px 0">📤 Upload</a>
            {f'<a href="{download_link}" target="_blank" style="display:block;padding:10px;background:#27ae60;color:white;text-decoration:none;border-radius:8px;margin:5px 0">📥 Download</a>' if has_file else '<p style="color:#f39c12">No file</p>'}
        </div>
        '''
    
    return f'''
    <!DOCTYPE html>
    <html><head><title>{subject_name.title()} Notes</title>
    <style>body{{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:30px;text-align:center}}
    h1{{font-size:36px;margin-bottom:30px}} .back-btn{{position:fixed;top:20px;left:20px;padding:15px 25px;background:#f39c12;color:white;text-decoration:none;border-radius:10px;font-size:18px}}</style></head>
    <body>
    <a href="/dashboard" class="back-btn">← Dashboard</a>
    <h1>📚 {subject_name.replace("-"," ").title()}</h1>
    <div style="max-width:1200px;margin:0 auto">{units_html}</div>
    </body></html>
    '''

# Unit upload/download routes (same as before)
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
                <div style="text-align:center;padding:50px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;display:flex;align-items:center;justify-content:center;flex-direction:column">
                <h1 style="color:#2ecc71;font-size:48px">✅ Uploaded!</h1>
                <p>{subject_name.title()} Unit {unit_num} PDF uploaded successfully!</p>
                <a href="/subject/{subject_name}" style="padding:15px 30px;background:#27ae60;color:white;text-decoration:none;border-radius:10px;font-size:20px">← Back to Subject</a>
                </div>
                '''
    
    return f'''
    <!DOCTYPE html>
    <html><head><title>Upload Unit {unit_num}</title>
    <style>body{{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}}
    input[type=file]{{width:400px;padding:15px;margin:20px;border-radius:10px;border:none;background:rgba(255,255,255,0.9)}}
    button{{padding:20px 40px;margin:20px;background:#50c878;color:white;border:none;border-radius:15px;font-size:20px;cursor:pointer}}</style></head>
    <body>
    <h1>📤 Upload {subject_name.title()} Unit {unit_num}</h1>
    <form method="POST" enctype="multipart/form-data">
    <input type="file" name="file" accept=".pdf" required><br>
    <button type="submit">✅ Upload PDF</button>
    </form>
    <a href="/subject/{subject_name}" style="color:#3498db;font-size:20px">← Back to {subject_name.title()}</a>
    </body></html>
    '''

@app.route('/download/<subject_name>/<filename>')
def download_file(subject_name, filename):
    return send_from_directory(f'static/uploads/{subject_name}', filename)

# Enhanced Reminders with email notifications
@app.route('/reminders', methods=['GET', 'POST'])
def reminders():
    if not session.get('logged_in'): return redirect('/')
    
    reminders = load_reminders()
    email = session['email']
    user_reminders = {k: v for k, v in reminders.items() if v.get('email') == email}
    
    if request.method == 'POST':
        reminder = {
            'title': request.form['title'],
            'deadline': (datetime.now() + timedelta(hours=float(request.form['hours']))).isoformat(),
            'email': email,
            'created': datetime.now().isoformat(),
            'notified': False
        }
        reminder_id = str(len(reminders))
        reminders[reminder_id] = reminder
        save_reminders(reminders)
        return redirect('/reminders')
    
    reminders_html = ''
    now = datetime.now()
    for rid, r in user_reminders.items():
        deadline = datetime.fromisoformat(r['deadline'])
        time_left = deadline - now
        status = "⏰ Due Soon" if time_left.total_seconds() > 0 else "🚨 OVERDUE"
        status_color = "#f39c12" if time_left.total_seconds() > 0 else "#e74c3c"
        
        reminders_html += f'''
        <div style="background:linear-gradient(135deg,{status_color},darken({status_color},10%));padding:20px;margin:20px;border-radius:15px;text-align:left">
        <h3>{status} - {r['title']}</h3>
        <p>📅 {deadline.strftime('%Y-%m-%d %H:%M')}</p>
        <p>⏱️ {int(time_left.total_seconds()/3600)} hours left</p>
        </div>
        '''
    
    return f'''
    <!DOCTYPE html>
    <html><head><title>Reminders</title>
    <style>body{{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}}
    .form-box{{background:rgba(255,255,255,0.1);padding:30px;border-radius:20px;margin:20px;display:inline-block}}
    input,select{{padding:12px;margin:10px;border-radius:8px;border:none;width:250px}}button{{padding:15px 30px;background:#50c878;color:white;border:none;border-radius:10px;font-size:18px;cursor:pointer}}</style></head>
    <body>
    <h1 style="font-size:36px;margin-bottom:30px">⏰ Your Reminders</h1>
    
    <div class="form-box">
    <h3>➕ Add New Reminder</h3>
    <form method="POST">
    <input name="title" placeholder="Reminder title (Ex: Maths Ch5)" required><br>
    <select name="hours">
    <option value="1">1 hour</option><option value="6">6 hours</option><option value="24">1 day</option>
    <option value="48">2 days</option><option value="168">1 week</option>
    </select><br>
    <button type="submit">✅ Set Reminder</button>
    </form>
    </div>
    
    {reminders_html or '<p style="font-size:24px">No reminders set. Add one above! 🎯</p>'}
    
    <a href="/dashboard" style="display:inline-block;padding:20px 40px;margin:20px;background:#f39c12;color:white;text-decoration:none;border-radius:15px;font-size:20px">← Dashboard</a>
    </body></html>
    '''

# Add other navigation routes (study, years, semesters)
@app.route('/study')
@app.route('/year1')
@app.route('/year2')
@app.route('/year3')
@app.route('/sem1')
@app.route('/sem2')
@app.route('/sem3')
@app.route('/sem4')
@app.route('/sem5')
@app.route('/sem6')
def navigation():
    if not session.get('logged_in'): return redirect('/')
    return '''
    <!DOCTYPE html>
    <html><head><title>Study Dashboard</title>
    <style>body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}
    .btn{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}
    h1{font-size:32px;margin-bottom:40px}</style></head>
    <body>
    <h1>📚 Study Dashboard</h1>
    <a href="/year1" class="btn">1st Year</a><a href="/year2" class="btn">2nd Year</a><a href="/year3" class="btn">3rd Year</a>
    <a href="/dashboard" class="btn" style="background:#f39c12">← Dashboard</a>
    </body></html>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

# Create requirements.txt
with open('requirements.txt', 'w') as f:
    f.write('Flask==2.3.3
werkzeug==2.3.7
')

print("✅ Complete Study Planner App Ready!")
print("👥 Add users in 'users' dict above")
print("📧 Set SMTP env vars for email notifications")
