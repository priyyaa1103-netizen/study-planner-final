from flask import Flask, request, redirect, session
app = Flask(__name__)
app.secret_key = 'study2026'

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['email']=='test@test.com' and request.form['password']=='123456':
            session['logged_in'] = True
            return redirect('/dashboard')
    return '''
<center><h1 style="color:#4a90e2;font-size:36px">🎓 Study Planner Login</h1>
<div style="background:rgba(255,255,255,0.1);padding:30px;border-radius:15px;max-width:400px;margin:50px auto">
<form method="POST">
<input style="padding:15px;margin:10px;width:90%;border-radius:8px;border:none;font-size:16px" name="email" placeholder="Email" required>
<input style="padding:15px;margin:10px;width:90%;border-radius:8px;border:none;font-size:16px" name="password" type="password" placeholder="Password" required>
<button style="padding:15px 40px;background:#50c878;color:white;border:none;border-radius:8px;font-size:18px;cursor:pointer;width:100%">Login</button>
</form>
<p style="color:#ffd700;margin-top:20px">Demo: test@test.com / 123456</p>
</div>
    '''

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect('/')
    return '''
<center><h1 style="color:#4a90e2;font-size:40px;margin:30px">Welcome Student! 🎓</h1>
<h2 style="color:white;font-size:28px">Study Planner & Reminder App</h2>
<div style="margin:40px">
<a href="/study"><button style="padding:25px 50px;font-size:22px;margin:15px;background:#50c878;color:white;border:none;border-radius:15px;cursor:pointer;box-shadow:0 8px 20px rgba(80,200,120,0.3)">📚 Study Dashboard</button></a><br>
<a href="/goals"><button style="padding:25px 50px;font-size:22px;margin:15px;background:#f39c12;color:white;border:none;border-radius:15px;cursor:pointer;box-shadow:0 8px 20px rgba(243,156,18,0.3)">🎯 Set Goal</button></a><br>
<a href="/view-goals"><button style="padding:25px 50px;font-size:22px;margin:15px;background:#3498db;color:white;border:none;border-radius:15px;cursor:pointer;box-shadow:0 8px 20px rgba(52,152,219,0.3)">📊 View Goals</button></a><br>
<a href="/reminders"><button style="padding:25px 50px;font-size:22px;margin:15px;background:#e74c3c;color:white;border:none;border-radius:15px;cursor:pointer;box-shadow:0 8px 20px rgba(231,76,60,0.3)">⏰ Reminders</button></a><br>
<a href="/logout"><button style="padding:25px 50px;font-size:22px;margin:15px;background:#95a5a6;color:white;border:none;border-radius:15px;cursor:pointer;box-shadow:0 8px 20px rgba(149,165,166,0.3)">Logout</button></a>
</div>
    '''

@app.route('/study')
def study():
    if not session.get('logged_in'):
        return redirect('/')
    return '''
<center><h1 style="color:#4a90e2;font-size:36px;margin:30px">📚 Study Dashboard</h1>
<div style="margin:40px">
<a href="/year1"><button style="padding:25px 50px;font-size:22px;margin:15px;background:#50c878;color:white;border:none;border-radius:15px;cursor:pointer">1st Year</button></a><br>
<a href="/year2"><button style="padding:25px 50px;font-size:22px;margin:15px;background:#50c878;color:white;border:none;border-radius:15px;cursor:pointer">2nd Year</button></a><br>
<a href="/year3"><button style="padding:25px 50px;font-size:22px;margin:15px;background:#50c878;color:white;border:none;border-radius:15px;cursor:pointer">3rd Year</button></a>
</div>
<a href="/dashboard"><button style="padding:25px 50px;font-size:22px;background:orange;color:white;border:none;border-radius:15px;cursor:pointer">← Back to Dashboard</button></a>
    '''

@app.route('/year1')
def year1():
    return '''
<center><h1 style="color:#4a90e2;font-size:36px;margin:30px">📚 1st Year</h1>
<div style="margin:40px">
<a href="/sem1"><button style="padding:25px 50px;font-size:22px;margin:15px;background:#3498db;color:white;border:none;border-radius:15px;cursor:pointer">Semester 1</button></a><br>
<a href="/sem2"><button style="padding:25px 50px;font-size:22px;margin:15px;background:#3498db;color:white;border:none;border-radius:15px;cursor:pointer">Semester 2</button></a>
</div>
<a href="/study"><button style="padding:25px 50px;font-size:22px;background:orange;color:white;border:none;border-radius:15px;cursor:pointer">← Back</button></a>
    '''

@app.route('/year2')
def year2():
    return '''
<center><h1 style="color:#4a90e2;font-size:36px;margin:30px">📚 2nd Year</h1>
<div style="margin:40px">
<a href="/sem3"><button style="padding:25px 50px;font-size:22px;margin:15px;background:#3498db;color:white;border:none;border-radius:15px;cursor:pointer">Semester 3</button></a><br>
<a href="/sem4"><button style="padding:25px 50px;font-size:22px;margin:15px;background:#3498db;color:white;border:none;border-radius:15px;cursor:pointer">Semester 4</button></a>
</div>
<a href="/study"><button style="padding:25px 50px;font-size:22px;background:orange;color:white;border:none;border-radius:15px;cursor:pointer">← Back</button></a>
    '''

@app.route('/year3')
def year3():
    return '''
<center><h1 style="color:#4a90e2;font-size:36px;margin:30px">📚 3rd Year</h1>
<div style="margin:40px">
<a href="/sem5"><button style="padding:25px 50px;font-size:22px;margin:15px;background:#3498db;color:white;border:none;border-radius:15px;cursor:pointer">Semester 5</button></a><br>
<a href="/sem6"><button style="padding:25px 50px;font-size:22px;margin:15px;background:#3498db;color:white;border:none;border-radius:15px;cursor:pointer">Semester 6</button></a>
</div>
<a href="/study"><button style="padding:25px 50px;font-size:22px;background:orange;color:white;border:none;border-radius:15px;cursor:pointer">← Back</button></a>
    '''

@app.route('/sem1')
def sem1():
    return '''
<center><h1 style="color:#4a90e2;font-size:36px;margin:30px">📖 Semester 1</h1>
<div style="margin:40px">
<a href="/maths"><button style="padding:25px 50px;font-size:22px;margin:15px;background:#50c878;color:white;border:none;border-radius:15px;cursor:pointer">📖 Maths</button></a><br>
<a href="/physics"><button style="padding:25px 50px;font-size:22px;margin:15px;background:#50c878;color:white;border:none;border-radius:15px;cursor:pointer">⚛️ Physics</button></a><br>
<a href="/chem"><button style="padding:25px 50px;font-size:22px;margin:15px;background:#50c878;color:white;border:none;border-radius:15px;cursor:pointer">🧪 Chemistry</button></a>
</div>
<a href="/year1"><button style="padding:25px 50px;font-size:22px;background:orange;color:white;border:none;border-radius:15px;cursor:pointer">← Back</button></a>
    '''

@app.route('/sem2')
def sem2():
    return '''
<center><h1 style="color:#4a90e2;font-size:36px;margin:30px">📖 Semester 2</h1>
<div style="margin:40px">
<a href="/maths2"><button style="padding:25px 50px;font-size:22px;margin:15px;background:#50c878;color:white;border:none;border-radius:15px;cursor:pointer">📖 Advanced Maths</button></a><br>
<a href="/physics2"><button style="padding:25px 50px;font-size:22px;margin:15px;background:#50c878;color:white;border:none;border-radius:15px;cursor:pointer">⚛️ Physics-II</button></a><br>
<a href="/bio"><button style="padding:25px 50px;font-size:22px;margin:15px;background:#50c878;color:white;border:none;border-radius:15px;cursor:pointer">🧬 Biology</button></a>
</div>
<a href="/year1"><button style="padding:25px 50px;font-size:22px;background:orange;color:white;border:none;border-radius:15px;cursor:pointer">← Back</button></a>
    '''

@app.route('/sem3')
def sem3():
    return '''
<center><h1 style="color:#4a90e2;font-size:36px;margin:30px">📖 Semester 3</h1>
<div style="margin:40px">
<a href="/ds"><button style="padding:25px 50px;font-size:22px;margin:15px;background:#50c878;color:white;border:none;border-radius:15px;cursor:pointer">📚 Data Structures</button></a><br>
<a href="/algo"><button style="padding:25px 50px;font-size:22px;margin:15px;background:#50c878;color:white;border:none;border-radius:15px;cursor:pointer">⚙️ Algorithms</button></a><br>
<a href="/dbms"><button style="padding:25px 50px;font-size:22px;margin:15px;background
