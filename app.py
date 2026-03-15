from flask import Flask, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3

app = Flask(__name__)
app.secret_key = 'study2026-secure-key'

def init_db():
    conn = sqlite3.connect('users.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                    (email TEXT PRIMARY KEY, password TEXT, name TEXT)''')
    conn.commit()
    conn.close()
init_db()

def get_db():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        email = request.form['email'].lower().strip()
        password = request.form['password']
        name = request.form.get('name', email.split('@')[0].title())
        is_register = 'register' in request.form
        
        conn = get_db()
        
        if is_register:
            # Register new user
            user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
            if user:
                conn.close()
                return simple_login_page("❌ Email already registered!")
            
            conn.execute("INSERT INTO users VALUES (?, ?, ?)", 
                        (email, generate_password_hash(password), name))
            conn.commit()
            conn.close()
            return simple_login_page("✅ Registered! Now login with same details.")
        
        # Login
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user'] = {'email': email, 'name': user['name']}
            return dashboard()
        else:
            return simple_login_page("❌ Wrong email/password!")
    
    return simple_login_page()

def simple_login_page(msg=""):
    return f'''
    <!DOCTYPE html>
    <html>
    <head><title>Study Planner</title>
    <style>
    *{{margin:0;padding:0;box-sizing:border-box}}
    body{{background:linear-gradient(135deg,#667eea,#764ba2);font-family:'Segoe UI',sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}}
    .box{{background:white;padding:50px;border-radius:25px;box-shadow:0 25px 50px rgba(0,0,0,0.3);width:100%;max-width:400px;text-align:center}}
    input{{width:100%;padding:18px;margin:15px 0;border:2px solid #ddd;border-radius:12px;font-size:16px;box-sizing:border-box}}
    input:focus{{border-color:#667eea;outline:none}}
    button{{width:100%;padding:20px;background:linear-gradient(135deg,#667eea,#764ba2);color:white;border:none;border-radius:15px;font-size:18px;font-weight:600;cursor:pointer;margin:10px 0}}
    button:hover{{transform:translateY(-2px)}}
    .msg{{padding:15px;margin:20px 0;border-radius:10px}}
    .success{{background:#d4edda;color:#155724;border:1px solid #c3e6cb}}
    .error{{background:#f8d7da;color:#721c24;border:1px solid #f5c6cb}}
    h1{{font-size:36px;color:#333;margin-bottom:30px}}
    .toggle-btn{{background:#6c757d;color:white;padding:12px 25px;border:none;border-radius:10px;cursor:pointer;margin:10px;font-size:16px}}
    </style>
    </head>
    <body>
    <div class="box">
        <h1>🎓 Study Planner</h1>
        {f'<div class="msg {'success' if "✅" in msg else 'error'}">{msg}</div>' if msg else ''}
        
        <form method="POST">
            <input type="email" name="email" placeholder="your@gmail.com" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
            <input type="hidden" name="register" value="1">
            <button type="submit" class="toggle-btn" name="register" value="1">New? Register</button>
        </form>
    </div>
    </body>
    </html>
    '''

def dashboard():
    user = session.get('user', {{}})
    return f'''
    <!DOCTYPE html>
    <html><head><title>Dashboard</title>
    <style>body{{background:linear-gradient(135deg,#667eea,#764ba2);color:white;font-family:'Segoe UI';min-height:100vh;padding:50px;text-align:center}}
    .btn{{display:inline-block;padding:20px 40px;margin:20px;background:#50c878;color:white;text-decoration:none;border-radius:20px;font-size:20px;font-weight:600;box-shadow:0 10px 30px rgba(80,200,120,0.4);transition:all 0.3s}}
    .btn:hover{{transform:translateY(-5px);box-shadow:0 20px 40px rgba(80,200,120,0.6)}}
    h1{{font-size:42px;margin-bottom:40px}} .user-info{{background:rgba(255,255,255,0.2);padding:30px;border-radius:25px;margin-bottom:40px}}</style></head>
    <body>
        <div class="user-info">
            <h1>🎉 Welcome {user["name"]}! </h1>
            <p style="font-size:24px">Email: {user["email"]}</p>
        </div>
        <a href="/study" class="btn">📚 Study Materials</a>
        <a href="/files" class="btn">📁 My Files</a>
        <a href="/goals" class="btn">🎯 Goals</a>
        <a href="/logout" class="btn" style="background:#e74c3c">🚪 Logout</a>
    </body></html>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/study')
@app.route('/files')
@app.route('/goals')
def placeholder():
    if not session.get('user'):
        return redirect('/')
    return '<h1 style="color:white;font-size:50px;text-align:center;margin-top:100px;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;padding-top:200px">Coming Soon! 🚀</h1>'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
