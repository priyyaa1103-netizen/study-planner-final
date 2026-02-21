from flask import Flask, request, redirect, session, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
from datetime import datetime, timedelta
import sqlite3

app = Flask(__name__)
app.secret_key = 'study2026-super-secure-key'

os.makedirs('static/uploads', exist_ok=True)

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (email TEXT PRIMARY KEY, password TEXT, name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS goals 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  email TEXT, subject TEXT, goal TEXT, 
                  target_score INTEGER, study_hours INTEGER, 
                  progress INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reminders 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT, title TEXT, deadline TEXT)''')
    conn.commit()
    conn.close()
init_db()

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=['GET', 'POST'])
def login():
    error = ""
    if request.method == 'POST':
        action = request.form.get('action', 'login')
        email = request.form['email'].lower()
        password = request.form['password']
        
        conn = get_db_connection()
        c = conn.cursor()
        
        if action == 'register':
            c.execute("SELECT email FROM users WHERE email=?", (email,))
            if c.fetchone():
                error = "Email already registered!"
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
            c.execute("SELECT * FROM users WHERE email=?", (email,))
            user = c.fetchone()
            conn.close()
            if user and check_password_hash(user['password'], password):
                session['logged_in'] = True
                session['email'] = email
                session['name'] = user['name']
                return redirect('/dashboard')
            else:
                error = "Wrong email or password!"
    
    return f'''
    <!DOCTYPE html>
    <html><head><title>Study Planner</title>
    <style>body{{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}}
    .login-box{{background:white;color:#333;padding:50px;border-radius:20px;box-shadow:0 20px 40px rgba(0,0,0,0.2);width:100%;max-width:420px}}
    .tabs{{display:flex;background:#f8f9fa;border-radius:12px;overflow:hidden;margin:30px 0}}
    .tab{{flex:1;padding:18px 10px;text-align:center;cursor:pointer;font-weight:600;transition:all 0.3s}}
    .tab.active{{background:#667eea;color:white}}
    input{{width:100%;padding:15px;margin:10px 0;font-size:16px;border:2px solid #e1e5e9;border-radius:12px}}
    button{{width:100%;padding:16px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:12px;font-size:18px;font-weight:600;cursor:pointer}}</style></head>
    <body>
    <div class="login-box">
        <h1 style="text-align:center;margin-bottom:30px;font-size:32px">🎓 Study Planner</h1>
        {f'<div style="background:#fee;color:#c53030;padding:12px;border-radius:8px;margin:15px 0">{error}</div>' if error else ''}
        <div class="tabs">
            <div class="tab active" onclick="showTab('login')">🔐 Login</div>
            <div class="tab" onclick="showTab('register')">➕ Register</div>
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
        <div style="text-align:center;margin-top:25px;font-size:14px;color:#666;padding:15px;background:#f8f9fa;border-radius:8px">
            Demo: test@test.com / 123456
        </div>
    </div>
    <script>
    function showTab(tab) {{
        document.getElementById('login-form').style.display = tab === 'login' ? 'block' : 'none';
        document.getElementById('register-form').style.display = tab === 'register' ? 'block' : 'none';
        document.querySelectorAll('.tab')[0].classList.toggle('active', tab === 'login');
        document.querySelectorAll('.tab')[1].classList.toggle('active', tab === 'register');
    }}
    </script>
    </body></html>
    '''

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'): return redirect('/')
    return f'''
    <!DOCTYPE html>
    <html><head><title>Dashboard</title>
    <style>body{{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:30px;text-align:center}}
    .btn{{display:inline-block;padding:22px 45px;margin:15px;background:linear-gradient(135deg,#f093fb 0%,#f5576c
