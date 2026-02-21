from flask import Flask, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'study2026'

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT)''')
    c.execute("INSERT OR IGNORE INTO users VALUES ('test@test.com', '123456')")
    conn.commit()
    conn.close()

init_db()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['logged_in'] = True
            session['email'] = email
            return redirect('/dashboard')
    return '''
    <!DOCTYPE html><html><head><title>Login</title><style>body{{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;display:flex;align-items:center;justify-content:center}}.box{{background:white;color:#333;padding:40px;border-radius:15px;box-shadow:0 15px 35px rgba(0,0,0,0.1);width:350px}}</style></head>
    <body><div class="box"><h1>🎓 Study Planner</h1><form method="POST">
    <input type="email" name="email" placeholder="Email" required style="width:100%;padding:15px;margin:10px 0;border-radius:8px">
    <input type="password" name="password" placeholder="Password" required style="width:100%;padding:15px;margin:10px 0;border-radius:8px">
    <button type="submit" style="width:100%;padding:15px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:8px;font-size:18px">Login</button></form>
    <p><b>Test:</b> test@test.com / 123456</p></div></body></html>'''

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'): return redirect('/')
    return '''
    <!DOCTYPE html><html><head><title>Dashboard</title><style>body{{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}}.btn{{display:inline-block;padding:20px 40px;margin:15px;background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);color:white;text-decoration:none;border-radius:15px;font-size:20px;font-weight:bold}}h1{{font-size:36px}}</style></head>
    <body><h1>Welcome! 🎓</h1><a href="/study" class="btn">📚 Study</a><a href="/set-reminder" class="btn">⏰ Reminder</a><a href="/logout" class="btn" style="background:red">Logout</a></body></html>'''

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
