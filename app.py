from flask import Flask, request, redirect, session, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'super-secret-key-2026')

# Create folders
os.makedirs('static/uploads', exist_ok=True)

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (email TEXT PRIMARY KEY, password TEXT, name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS goals 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, subject TEXT, 
                  goal TEXT, target_score INTEGER, study_hours TEXT, progress INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reminders 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, title TEXT, deadline TEXT)''')
    conn.commit()
    conn.close()

# Init DB
try:
    init_db()
except:
    pass

def get_db():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

def render_login_page(error=""):
    html = '''
<!DOCTYPE html>
<html>
<head>
    <title>Study Planner</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
        .login-box{background:white;color:#333;padding:50px;border-radius:20px;box-shadow:0 20px 40px rgba(0,0,0,0.2);width:100%;max-width:420px}
        .tabs{display:flex;background:#f8f9fa;border-radius:12px;overflow:hidden;margin:30px 0}
        .tab{flex:1;padding:18px 10px;text-align:center;cursor:pointer;font-weight:600;transition:all 0.3s;font-size:16px}
        .tab.active{background:#667eea;color:white}
        input{width:100%;padding:15px;margin:10px 0;font-size:16px;border:2px solid #e1e5e9;border-radius:12px;box-sizing:border-box;transition:all 0.3s}
        input:focus{border-color:#667eea;outline:none;box-shadow:0 0 0 3px rgba(102,126,234,0.1)}
        button{width:100%;padding:16px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:12px;font-size:18px;font-weight:600;cursor:pointer;transition:all 0.3s;margin:5px 0}
        button:hover{transform:translateY(-2px);box-shadow:0 10px 25px rgba(102,126,234,0.4)}
        .error{background:#fee;color:#c53030;padding:12px;border-radius:8px;margin:15px 0;font-weight:500}
        .demo{text-align:center;margin-top:25px;font-size:14px;color:#666;padding:15px;background:#f8f9fa;border-radius:8px}
        h1{text-align:center;margin-bottom:30px;font-size:32px;color:#333}
    </style>
</head>
<body>
    <div class="login-box">
        <h1>🎓 Study Planner</h1>
    '''
    
    if error:
        html += f'<div class="error">{error}</div>'
    
    html += '''
        <div class="tabs">
            <div class="tab active" onclick="showTab(0)">🔐 Login</div>
            <div class="tab" onclick="showTab(1)">➕ Register</div>
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
        
        <div class="demo">Demo: test@test.com / 123456</div>
    </div>
    
    <script>
    function showTab(n) {
        document.getElementById('login-form').style.display = n===0?'block':'none';
        document.getElementById('register-form').style.display = n===1?'block':'none';
        document.querySelectorAll('.tab')[0].classList.toggle('active', n===0);
        document.querySelectorAll('.tab')[1].classList.toggle('active', n===1);
    }
    </script>
</body>
</html>'''
    return html

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            action = request.form.get('action', 'login')
            email = request.form['email'].lower().strip()
            password = request.form['password']
            
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            
            if action == 'register':
                c.execute("SELECT email FROM users WHERE email=?", (email,))
                if c.fetchone():
                    conn.close()
                    return render_login_page("❌ Email already registered!")
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
                # Demo user
                if email == 'test@test.com' and password == '123456':
                    session['logged_in'] = True
                    session['email'] = email
                    session['name'] = 'Demo User'
                    return redirect('/dashboard')
                
                # Real user
                c.execute("SELECT * FROM users WHERE email=?", (email,))
                user = c.fetchone()
                conn.close()
                
                if user and check_password_hash(user['password'], password):
                    session['logged_in'] = True
                    session['email'] = email
                    session['name'] = user['name']
                    return redirect('/dashboard')
                else:
                    return render_login_page("❌ Wrong email or password!")
        
        except Exception as e:
            return render_login_page("❌ Server error! Try again.")
    
    return render_login_page()

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'): return redirect('/')
    return f'''
<!DOCTYPE html><html><head><title>Dashboard</title>
<style>body{{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center;font-family:Arial}}
.btn{{display:inline-block;padding:20px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:15px;font-size:18px;box-shadow:0 10px 20px rgba(0,0,0,0.3)}}
h1{{font-size:40px;margin-bottom:40px}}</style></head>
<body>
<h1>Welcome {session.get("name", "User")}! 🎓</h1>
<a href="/study" class="btn">📚 Study</a>
<a href="/goals" class="btn">🎯 Goals</a>
<a href="/logout" class="btn" style="background:#e74c3c">🚪 Logout</a>
</body></html>'''

@app.route('/study')
def study():
    if not session.get('logged_in'): return redirect('/')
    return f'''
<!DOCTYPE html><html><head><title>Study</title>
<style>body{{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center;font-family:Arial}}
.btn{{padding:15px 25px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:16px;display:inline-block}}h1{{font-size:35px;margin-bottom:40px}}</style></head>
<body>
<h1>📚 Study Dashboard</h1>
<a href="/subject/maths" class="btn">Mathematics</a>
<a href="/subject/python" class="btn">Python</a>
<a href="/subject/java" class="btn">Java</a>
<a href="/dashboard" class="btn" style="background:#f39c12">← Back</a>
</body></html>'''

@app.route('/subject/<subject>')
def subject(subject):
    if not session.get('logged_in'): return redirect('/')
    return f'''
<!DOCTYPE html><html><head><title>{subject.title()}</title>
<style>body{{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:30px;font-family:Arial;text-align:center}}
.unit{{display:inline-block;margin:15px;padding:20px;background:rgba(255,255,255,0.1);border-radius:15px;width:200px}}h1{{font-size:35px;margin:50px 0 30px 0}}</style></head>
<body>
<h1>📚 {subject.replace("-"," ").title()}</h1>
<div class="unit"><h3>Unit 1</h3><a href="/upload/{subject}/1" style="display:block;padding:10px;background:#3498db;color:white;text-decoration:none;border-radius:8px">Upload PDF</a></div>
<div class="unit"><h3>Unit 2</h3><a href="/upload/{subject}/2" style="display:block;padding:10px;background:#3498db;color:white;text-decoration:none;border-radius:8px">Upload PDF</a></div>
<a href="/dashboard" style="position:fixed;top:20px;left:20px;padding:15px;background:#f39c12;color:white;text-decoration:none;border-radius:10px">← Back</a>
</body></html>'''

@app.route('/upload/<subject>/<unit>', methods=['GET', 'POST'])
def upload(subject, unit):
    if not session.get('logged_in'): return redirect('/')
    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            if file.filename:
                os.makedirs(f'static/uploads/{subject}', exist_ok=True)
                file.save(f'static/uploads/{subject}/unit{unit}.pdf')
                return f'<h1 style="text-align:center;color:green;margin-top:100px">✅ Uploaded Successfully!</h1><a href="/subject/{subject}" style="display:block;margin:20px auto;width:200px;text-align:center;padding:15px;background:#50c878;color:white;text-decoration:none;border-radius:10px">← Back</a>'
        return '<h1 style="color:red;text-align:center">No file selected!</h1>'
    return f'''
<!DOCTYPE html><html><head><title>Upload</title>
<style>body{{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center;font-family:Arial}}
input[type=file]{{width:400px;padding:15px;margin:20px;border-radius:10px;border:none}}button{{padding:15px 40px;background:#50c878;color:white;border:none;border-radius:10px;font-size:18px;cursor:pointer}}</style></head>
<body>
<h1>📤 Upload Unit {unit}</h1>
<form method="POST" enctype="multipart/form-data">
<input type="file" name="file" accept=".pdf" required>
<button>Upload PDF</button>
</form>
<a href="/subject/{subject}" style="color:#3498db;font-size:20px">← Back</a>
</body></html>'''

@app.route('/download/<subject>/<filename>')
def download(subject, filename):
    return send_from_directory(f'static/uploads/{subject}', filename)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
