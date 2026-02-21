from flask import Flask, request, redirect, session, render_template_string
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
import json

app = Flask(__name__)
app.secret_key = 'study2026-super-secure-key-2026'

# Create necessary folders
os.makedirs('static/uploads', exist_ok=True)

# User database (simple dict - in production use proper database)
users = {
    'test@test.com': {'password': '123456', 'name': 'Student'},
    # Add more users here or use registration
}

# Simple reminder storage
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

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        if email in users and users[email]['password'] == password:
            session['logged_in'] = True
            session['email'] = email
            session['name'] = users[email]['name']
            return redirect('/dashboard')
        else:
            return render_login("❌ Wrong Credentials! Invalid email or password.")
    
    return render_login("Demo: test@test.com / 123456")

def render_login(message):
    return f'''
    <!DOCTYPE html>
    <html><head><title>Study Planner Login</title>
    <style>body{{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;display:flex;align-items:center;justify-content:center}}
    .login-box{{background:white;color:#333;padding:40px;border-radius:15px;box-shadow:0 15px 35px rgba(0,0,0,0.1);width:350px}}
    input{{width:100%;padding:15px;margin:10px 0;font-size:16px;border:2px solid #ddd;border-radius:8px;box-sizing:border-box}}
    button{{width:100%;padding:15px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:8px;font-size:18px;cursor:pointer;font-weight:bold}}</style></head>
    <body><div class="login-box">
    <h1>🎓 Study Planner</h1>
    <p style="color:#e74c3c">{message}</p>
    <form method="POST">
    <input type="email" name="email" placeholder="Email" required>
    <input type="password" name="password" placeholder="Password" required>
    <button type="submit">Login</button>
    </form><p>Demo: test@test.com / 123456</p></div></body></html>
    '''

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'): 
        return redirect('/')
    
    # Check for notifications
    notifications = check_notifications()
    
    return f'''
    <!DOCTYPE html>
    <html><head><title>Dashboard</title>
    <style>body{{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}}
    .btn{{display:inline-block;padding:20px 40px;margin:15px;background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);color:white;text-decoration:none;border-radius:15px;font-size:20px;font-weight:bold}}
    .btn:hover{{transform:translateY(-3px)}}
    .notification{{background:#e74c3c;padding:15px;border-radius:10px;margin:20px;font-size:18px}}
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
                notifications.append(f'<div class="notification">🚨 <b>{reminder["title"]}</b> - Deadline Passed!</div>')
    
    return ''.join(notifications)

@app.route('/study')
def study():
    if not session.get('logged_in'): return redirect('/')
    return '''
    <!DOCTYPE html><html><head><title>Study Dashboard</title><style>body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}
    .btn{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}h1{font-size:32px;margin-bottom:40px}</style></head>
    <body><h1>📚 Study Dashboard</h1>
    <a href="/year1" class="btn">1st Year</a><a href="/year2" class="btn">2nd Year</a><a href="/year3" class="btn">3rd Year</a>
    <br><a href="/dashboard" class="btn" style="background:#f39c12">← Back</a></body></html>
    '''

# 1st Year Routes
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
    <a href="/subject/physics" class="btn">Physics</a>
    <a href="/subject/chemistry" class="btn">Chemistry</a>
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
    <a href="/subject/physics2" class="btn">Physics-II</a>
    <a href="/subject/biology" class="btn">Biology</a>
    <br><a href="/year1" class="btn" style="background:#f39c12">← Back</a></body></html>
    '''

# Subject with Units (Updated)
@app.route('/subject/<subject_name>')
def subject_notes(subject_name):
    if not session.get('logged_in'): return redirect('/')
    
    units_html = ''
    for i in range(1, 11):  # Units 1 to 10
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

# Unit file upload
@app.route('/upload/<subject_name>/<unit_num>', methods=['GET', 'POST'])
def upload_unit(subject_name, unit_num):
    if not session.get('logged_in'): return redirect('/')
    
    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                os.makedirs(f'static/uploads/{subject_name}', exist_ok=True)
                filename = secure_filename(f"{unit_num}.pdf")
                file.save(f'static/uploads/{subject_name}/{filename}')
                return f'''
                <div style="text-align:center;padding:50px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;display:flex;align-items:center;justify-content:center;flex-direction:column">
                <h1 style="color:#2ecc71;font-size:48px">✅ Uploaded!</h1>
                <p>{subject_name.title()} Unit {unit_num} PDF uploaded successfully!</p>
                <a href="/subject/{subject_name}" style="padding:15px 30px;background:#27ae60;color:white;text-decoration:none;border-radius:10px;font-size:20px">← Back to Subject</a>
                </div>
                '''
        return '<h1 style="text-align:center;color:red">No file selected!</h1><a href="/subject/' + subject_name + '">← Back</a>'
    
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

# Download route
@app.route('/download/<subject_name>/<filename>')
def download_file(subject_name, filename):
    return send_from_directory(f'static/uploads/{subject_name}', filename)

from flask import send_from_directory

# Add other year/semester routes (keeping same structure)
@app.route('/year2')
@app.route('/year3')
@app.route('/sem3')
@app.route('/sem4')
@app.route('/sem5')
@app.route('/sem6')
def placeholder_routes():
    if not session.get('logged_in'): return redirect('/')
    return '''
    <!DOCTYPE html><html><head><title>Coming Soon</title><style>body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;display:flex;align-items:center;justify-content:center}
    .box{background:white;color:#333;padding:60px;border-radius:20px;text-align:center;box-shadow:0 20px 40px rgba(0,0,0,0.2);width:400px}</style></head>
    <body><div class="box">
    <h1>🚧 Coming Soon</h1>
    <p>This section is under development</p>
    <a href="/dashboard" style="padding:15px 30px;background:#3498db;color:white;text-decoration:none;border-radius:10px;display:inline-block">← Dashboard</a>
    </div></body></html>
    '''

# Enhanced Reminders with deadlines
@app.route('/reminders', methods=['GET', 'POST'])
def reminders():
    if not session.get('logged_in'): return redirect('/')
    
    reminders = load_reminders()
    email = session.get('email', '')
    user_reminders = [r for r in reminders.values() if r.get('email') == email]
    
    if request.method == 'POST':
        reminder = {
            'title': request.form['title'],
            'deadline': (datetime.now() + timedelta(hours=int(request.form['hours']))).isoformat(),
            'email': email,
            'created': datetime.now().isoformat()
        }
        reminders[str(len(reminders))] = reminder
        save_reminders(reminders)
        return redirect('/reminders')
    
    reminders_html = ''
    for r in user_reminders:
        deadline = datetime.fromisoformat(r['deadline'])
        time_left = deadline - datetime.now()
        status = "⏰ Due Soon" if time_left.total_seconds() > 0 else "🚨 OVERDUE"
        reminders_html += f'''
        <div style="background:linear-gradient(135deg,orange,#f39c12);padding:20px;margin:20px;border-radius:15px;text-align:left">
        <h3>{status} {r['title']}</h3>
        <p>Deadline: {deadline.strftime('%Y-%m-%d %H:%M')}</p>
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
    <input name="title" placeholder="Reminder title" required><br>
    <select name="hours">
    <option value="1">1 hour</option><option value="6">6 hours</option><option value="24">1 day</option>
    <option value="48">2 days</option><option value="168">1 week</option>
    </select><br>
    <button type="submit">✅ Set Reminder</button>
    </form>
    </div>
    
    {reminders_html or '<p>No reminders set. Add one above! 🎯</p>'}
    
    <a href="/dashboard" style="display:inline-block;padding:20px 40px;margin:20px;background:#f39c12;color:white;text-decoration:none;border-radius:15px;font-size:20px">← Dashboard</a>
    </body></html>
    '''

@app.route('/goals', methods=['GET', 'POST'])
def goals():
    if not session.get('logged_in'): return redirect('/')
    if request.method == 'POST':
        goals = session.get('goals', [])
        goal_data = {
            'subject': request.form['subject'],
            'goal': request.form['goal'],
            'target_score': request.form['target_score'],
            'study_hours': request.form['study_hours'],
            'progress': 0,
            'email': session['email']
        }
        goals.append(goal_data)
        session['goals'] = goals
        session.modified = True
        return redirect('/view-goals')
    
    return '''
    <!DOCTYPE html>
    <html><head><title>Set Goals</title>
    <style>body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}
    input{width:300px;padding:15px;margin:10px;font-size:16px;border-radius:10px;border:none}
    button{padding:20px 40px;margin:20px;background:#50c878;color:white;border:none;border-radius:15px;font-size:20px;cursor:pointer}
    h1{font-size:36px;margin-bottom:40px}</style></head>
    <body>
    <h1>🎯 Set Study Goals</h1>
    <form method="POST">
    Subject: <input name="subject" required><br>
    Goal: <input name="goal" required><br>
    Target Score: <input name="target_score" type="number"><br>
    Study Hours: <input name="study_hours" type="number"><br>
    <button type="submit">✅ Save Goal</button>
    </form><a href="/dashboard" style="color:white;font-size:20px">← Dashboard</a>
    </body></html>
    '''

@app.route('/view-goals')
def view_goals():
    if not session.get('logged_in'): return redirect('/')
    goals = session.get('goals', [])
    email = session.get('email', '')
    user_goals = [g for g in goals if g.get('email') == email]
    
    goals_html = ''
    for goal in user_goals:
        progress = f'<div style="background:#2ecc71;width:{goal["progress"]*5}%;height:20px;border-radius:10px;margin:10px auto"></div>'
        goals_html += f'''
        <div style="background:rgba(255,255,255,0.1);padding:25px;margin:20px;border-radius:15px">
        <h3>📚 {goal["subject"]}</h3>
        <p><b>Goal:</b> {goal["goal"]}</p>
        <p><b>Target:</b> {goal["target_score"]}% | <b>Hours:</b> {goal["study_hours"]}h</p>
        {progress}<p>Progress: {goal["progress"]}%</p>
        </div>
        '''
    
    if not user_goals:
        goals_html = '<p style="font-size:24px">No goals set yet. <a href="/goals" style="color:#f1c40f;font-size:28px">Set goals now! 🎯</a></p>'
    
    return f'''
    <!DOCTYPE html>
    <html><head><title>View Goals</title>
    <style>body{{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}}h1{{font-size:36px;margin-bottom:40px}}</style></head>
    <body><h1>📊 Your Goals</h1>{goals_html}<a href="/dashboard" style="color:white;font-size:20px">← Dashboard</a></body></html>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
