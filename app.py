from flask import Flask, request, redirect, url_for, session, render_template_string
app = Flask(__name__)
app.secret_key = 'study2026'

users = {'test@test.com': '123456', 'Student': True}

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email in users and users[email] == password:
            session['user'] = email
            return redirect(url_for('dashboard'))
        return login_html.format(error="Wrong email/password!")
    
    return login_html.format(error="")

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return dashboard_html.format(name=session['user'])

@app.route('/study')
def study():
    return study_html

@app.route('/goals')
def goals():
    return goals_html

@app.route('/view-goals')
def view_goals():
    return view_goals_html

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

login_html = """
<!DOCTYPE html><html><head><title>Login</title>
<style>body{font-family:Arial;background:#4a90e2;color:white;padding:100px;text-align:center}
input{padding:15px;margin:10px;font-size:18px;border:none;border-radius:5px;width:300px}
button{padding:15px 30px;background:#50c878;color:white;border:none;border-radius:5px;font-size:18px}
.login-box{max-width:400px;margin:auto;background:rgba(255,255,255,0.1);padding:40px;border-radius:15px}</style>
</head><body>
<div class="login-box">
<h1>🎓 Study Planner</h1>
<form method="POST">
<input type="email" name="email" placeholder="Email" required>
<input type="password" name="password" placeholder="Password" required>
<button>Login</button>
</form>
{{error}}
<p>Use: test@test.com / 123456</p>
</div></body></html>
"""

dashboard_html = """
<!DOCTYPE html><html><head><title>Dashboard</title>
<style>body{font-family:Arial;background:#4a90e2;color:white;padding:50px;text-align:center}
.btn{padding:20px 40px;margin:20px;display:inline-block;background:#50c878;color:white;text-decoration:none;border-radius:15px;font-size:20px;font-weight:bold}
h1{font-size:36px;margin-bottom:20px}</style></head>
<body>
<h1>Welcome {{name}}! 🎓</h1>
<h2>Study Planner App</h2>
<a href="/study" class="btn">📚 Study Dashboard</a>
<a href="/goals" class="btn">🎯 Set Goal</a>
<a href="/view-goals" class="btn">📊 View Goals</a>
<a href="/logout" class="btn" style="background:#e74c3c">Logout</a>
</body></html>
"""

study_html = """
<!DOCTYPE html><html><head><title>Study</title>
<style>body{font-family:Arial;background:#4a90e2;color:white;padding:50px;text-align:center}
.btn{padding:20px 40px;margin:20px;display:inline-block;background:#50c878;color:white;text-decoration:none;border-radius:15px;font-size:20px}</style>
</head><body>
<h1>📚 Study Dashboard</h1>
<a href="#" class="btn">1st Year</a>
<a href="#" class="btn">2nd Year</a>
<a href="#" class="btn">3rd Year</a>
<a href="/dashboard" class="btn" style="background:#f39c12">← Back</a>
</body></html>
"""

goals_html = """
<!DOCTYPE html><html><head><title>Goals</title>
<style>body{font-family:Arial;background:#4a90e2;color:white;padding:50px;text-align:center}</style>
</head><body>
<h1>🎯 Set Goals - Coming Soon!</h1>
<a href="/dashboard" style="color:white;font-size:20px">← Back</a>
</body></html>
"""

view_goals_html = """
<!DOCTYPE html><html><head><title>View Goals</title>
<style>body{font-family:Arial;background:#4a90e2;color:white;padding:50px;text-align:center}</style>
</head><body>
<h1>📊 View Goals - Coming Soon!</h1>
<a href="/dashboard" style="color:white;font-size:20px">← Back</a>
</body></html>
"""

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
