from flask import Flask, request, redirect, session, jsonify, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = 'study-planner-2026-secret-key-change-this'

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                    (email TEXT PRIMARY KEY, password TEXT, name TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS reminders 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                     email TEXT, title TEXT, deadline TEXT)''')
    conn.commit()
    conn.close()

init_db()

def get_alarm_js():
    return '''
<script>
let firedAlarms = new Set();
document.addEventListener("DOMContentLoaded", function() {
    setInterval(() => {
        fetch("/api/user-alarms").then(r=>r.json()).then(data => {
            const now = new Date();
            data.forEach(alarm => {
                if(new Date(alarm.deadline) <= now && !firedAlarms.has(alarm.id)) {
                    firedAlarms.add(alarm.id);
                    const audio = new Audio();
                    audio.src = "data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAo";
                    audio.play();
                    const div = document.createElement("div");
                    div.style.cssText = "position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(255,0,0,0.9);z-index:99999;font-size:50px;display:flex;align-items:center;justify-content:center;color:white;text-shadow:0 0 20px #fff;";
                    div.innerHTML = `🚨 ${alarm.title.toUpperCase()} 🚨<br><button onclick="this.parentElement.remove();document.querySelectorAll('audio').forEach(a=>a.pause());" style="padding:15px 30px;font-size:20px;background:#fff;color:#f00;border:none;border-radius:10px;margin-top:20px;cursor:pointer;">STOP ALARM</button>`;
                    document.body.appendChild(div);
                }
            });
        });
    }, 2000);
});
</script>
'''

@app.route('/', methods=['GET', 'POST'])
def home():
    if session.get('logged_in'):
        return redirect('/dashboard')
    
    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']
        action = request.form.get('action', 'login')
        
        conn = get_db_connection()
        if action == 'register':
            if not conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone():
                conn.execute("INSERT INTO users VALUES (?, ?, ?)", 
                           (email, generate_password_hash(password), request.form['name']))
                conn.commit()
                return redirect('/dashboard')
        else:
            user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
            if user and check_password_hash(user['password'], password):
                session['logged_in'] = True
                session['email'] = email
                session['name'] = user['name']
                conn.close()
                return redirect('/dashboard')
        conn.close()
    
    return '''
<!DOCTYPE html>
<html><head><title>Study Planner</title>
<style>body{background:linear-gradient(135deg,#667eea,#764ba2);display:flex;align-items:center;justify-content:center;min-height:100vh;font-family:'Segoe UI';margin:0;}
form{background:#fff;padding:50px;border-radius:20px;box-shadow:0 20px 40px rgba(0,0,0,0.3);width:90%;max-width:400px;}
input{width:100%;padding:15px;margin:10px 0;border-radius:10px;border:1px solid #ddd;box-sizing:border-box;}
button{width:100%;padding:15px;background:#667eea;color:white;border:none;border-radius:10px;font-size:18px;cursor:pointer;margin-top:10px;}
</style></head>
<body>
<form method="POST">
<h1 style="text-align:center;margin-bottom:30px;">🎓 Study Planner</h1>
<input name="email" placeholder="Email" required>
<input type="password" name="password" placeholder="Password" required>
<input type="text" name="name" placeholder="Full Name (for register)">
<button type="submit">Login</button>
<button type="submit" name="action" value="register">Register New</button>
</form>
</body></html>'''

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect('/')
    name = session.get('name', 'User')
    return f'''
<!DOCTYPE html>
<html><head><title>Dashboard</title>
<style>body{{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:20px;text-align:center;margin:0;}}
.container{{max-width:800px;margin:0 auto;}}
h1{{font-size:36px;margin-bottom:20px;text-shadow:0 2px 10px rgba(0,0,0,0.3);}}
h2{{font-size:24px;margin-bottom:40px;}}
.btn{{display:inline-block;padding:20px 40px;margin:15px;background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);color:white;text-decoration:none;border-radius:15px;font-size:20px;font-weight:bold;box-shadow:0 10px 30px rgba(0,0,0,0.2);transition:all 0.3s;}}
.btn:hover{{transform:translateY(-5px);box-shadow:0 15px 40px rgba(0,0,0,0.3);}}
.welcome{{background:rgba(255,255,255,0.1);padding:30px;border-radius:20px;margin-bottom:40px;backdrop-filter:blur(10px);}}
</style></head>
<body>
<div class="container">
<div class="welcome">
<h1>Welcome {name}! 🎓</h1>
<h2>Study Planner & Reminder App</h2>
</div>
<a href="/study" class="btn">📚 Study Dashboard</a>
<a href="/goals" class="btn">🎯 Set Goal</a>
<a href="/view-goals" class="btn">📊 View Goals</a>
<a href="/reminders" class="btn">⏰ Reminders</a>
<a href="/myfiles" class="btn">📁 My Files</a>
<a href="/logout" class="btn" style="background:linear-gradient(135deg,#e74c3c,#c0392b)">🚪 Logout</a>
</div>
{get_alarm_js()}
</body></html>'''

@app.route('/reminders')
def reminders():
    if not session.get('logged_in'):
        return redirect('/')
    
    conn = get_db_connection()
    reminders_list = conn.execute("SELECT * FROM reminders WHERE email=? ORDER BY deadline ASC", (session['email'],)).fetchall()
    conn.close()
    
    r_html = ''
    for r in reminders_list:
        r_html += f'''
        <div style="background:rgba(255,255,255,0.15);padding:30px;margin:20px;border-radius:20px;box-shadow:0 10px 30px rgba(0,0,0,0.2);">
            <div style="font-size:28px;margin-bottom:10px;">⏰ {r['title']}</div>
            <div style="font-size:22px;color:#ffd700;margin-bottom:15px;">📅 {r['deadline']}</div>
            <a href="/delete-reminder/{r['id']}" onclick="return confirm('Delete {r['title']}?')" 
               style="background:#e74c3c;padding:12px 25px;border-radius:12px;color:white;text-decoration:none;font-weight:600;">🗑️ Delete</a>
        </div>'''
    
    return f'''
<!DOCTYPE html>
<html><head><title>Reminders</title>
<style>body{{font-family:'Segoe UI';background:linear-gradient(135deg,#667eea,#764ba2);color:white;min-height:100vh;padding:20px;margin:0;}}.container{{max-width:900px;margin:0 auto;text-align:center;}}.btn{{display:inline-block;padding:22px 40px;margin:10px;background:linear-gradient(135deg,#f093fb,#f5576c);color:white;text-decoration:none;border-radius:20px;font-size:20px;font-weight:600;}}</style>
</head><body>
<div class="container">
<a href="/dashboard" style="position:absolute;top:20px;left:20px;padding:15px 25px;background:#f39c12;color:white;text-decoration:none;border-radius:15px;font-weight:600;">← Dashboard</a>
<h1 style="font-size:42px;margin:80px 0 40px;">⏰ My Reminders</h1>

<div style="background:rgba(255,255,255,0.1);padding:40px;border-radius:25px;margin:40px 0;max-width:600px;margin-left:auto;margin-right:auto;box-shadow:0 20px 40px rgba(0,0,0,0.2);">
<h2 style="font-size:28px;margin-bottom:30px;">➕ Add New Reminder</h2>
<form method="POST" action="/set-reminder">
<input name="title" placeholder="🎯 Reminder Title (Maths Ch1, Exam Prep)" style="width:100%;padding:20px;margin:15px 0;border-radius:15px;border:none;font-size:18px;box-shadow:0 5px 15px rgba(0,0,0,0.2);background:rgba(255,255,255,0.9);" required>
<input name="deadline" type="datetime-local" style="width:100%;padding:20px;margin:15px 0;border-radius:15px;border:none;font-size:18px;box-shadow:0 5px 15px rgba(0,0,0,0.2);background:rgba(255,255,255,0.9);" required>
<button type="submit" class="btn" style="width:100%;background:linear-gradient(135deg,#50c878,#27ae60);font-size:22px;">✅ Set Reminder</button>
</form>
</div>

{r_html or '<div style="background:rgba(255,255,255,0.1);padding:60px;border-radius:25px;margin:60px 0;"><h2 style="font-size:32px;">😊 No Reminders Set</h2><p style="font-size:22px;color:#f1c40f;">Set your first study reminder above!</p></div>'}
</div>
{get_alarm_js()}
</body></html>'''

@app.route('/set-reminder', methods=['POST'])
def set_reminder():
    if not session.get('logged_in'):
        return redirect('/')
    conn = get_db_connection()
    conn.execute("INSERT INTO reminders (email, title, deadline) VALUES (?, ?, ?)", 
                (session['email'], request.form['title'], request.form['deadline']))
    conn.commit()
    conn.close()
    return redirect('/reminders')

@app.route('/delete-reminder/<int:rem_id>')
def delete_reminder(rem_id):
    if not session.get('logged_in'):
        return redirect('/')
    conn = get_db_connection()
    conn.execute("DELETE FROM reminders WHERE id=? AND email=?", (rem_id, session['email']))
    conn.commit()
    conn.close()
    return redirect('/reminders')

@app.route('/api/user-alarms')
def user_alarms():
    if not session.get('logged_in'):
        return jsonify([])
    conn = get_db_connection()
    alarms = conn.execute("SELECT id, title, deadline FROM reminders WHERE email=?", (session['email'],)).fetchall()
    conn.close()
    return jsonify([{'id':a['id'],'title':a['title'],'deadline':a['deadline']} for a in alarms])

@app.route('/study')
def study():
    if not session.get('logged_in'):
        return redirect('/')
    return f'''
<!DOCTYPE html>
<html><head><title>Study Dashboard</title>
<style>body{{background:linear-gradient(135deg,#667eea,#764ba2);color:white;font-family:'Segoe UI';text-align:center;padding:50px;margin:0;}}.btn{{padding:25px 50px;margin:20px;background:#50c878;color:white;text-decoration:none;border-radius:20px;font-size:24px;font-weight:bold;display:inline-block;box-shadow:0 10px 30px rgba(0,0,0,0.3);}}</style>
</head><body>
<h1 style="font-size:48px;margin-bottom:60px;">📚 Study Dashboard</h1>
<a href="/year1" class="btn">🎓 1st Year</a>
<a href="/year2" class="btn">🎓 2nd Year</a>
<a href="/year3" class="btn">🎓 3rd Year</a>
<a href="/dashboard" style="position:absolute;top:20px;left:20px;padding:15px 25px;background:#f39c12;color:white;text-decoration:none;border-radius:15px;font-weight:600;">← Dashboard</a>
{get_alarm_js()}
</body></html>'''

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
