from flask import Flask, request, redirect, session
import os

app = Flask(__name__)
app.secret_key = 'study2026'

# Create uploads folder
os.makedirs('static/uploads', exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['email'] == 'test@test.com' and request.form['password'] == '123456':
            session['logged_in'] = True
            session['name'] = 'Student'
            return redirect('/dashboard')
        else:
            return '''
            <!DOCTYPE html>
            <html><head><title>Login Failed</title>
            <style>body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;display:flex;align-items:center;justify-content:center}
            .login-box{background:white;color:#333;padding:40px;border-radius:15px;box-shadow:0 15px 35px rgba(0,0,0,0.1);width:350px}</style></head>
            <body><div class="login-box">
            <h1>❌ Wrong Credentials!</h1>
            <form method="POST">
            <input type="email" name="email" placeholder="Email" style="width:100%;padding:15px;margin:10px 0;border-radius:8px">
            <input type="password" name="password" placeholder="Password" style="width:100%;padding:15px;margin:10px 0;border-radius:8px">
            <button type="submit" style="width:100%;padding:15px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:8px;font-size:18px">Login</button>
            </form><p>test@test.com / 123456</p></div></body></html>
            '''
    return '''
    <!DOCTYPE html>
    <html><head><title>Study Planner Login</title>
    <style>body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;display:flex;align-items:center;justify-content:center}
    .login-box{background:white;color:#333;padding:40px;border-radius:15px;box-shadow:0 15px 35px rgba(0,0,0,0.1);width:350px}
    input{width:100%;padding:15px;margin:10px 0;font-size:16px;border:2px solid #ddd;border-radius:8px;box-sizing:border-box}
    button{width:100%;padding:15px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:8px;font-size:18px;cursor:pointer;font-weight:bold}</style></head>
    <body><div class="login-box">
    <h1>🎓 Study Planner</h1>
    <form method="POST">
    <input type="email" name="email" placeholder="Email" required>
    <input type="password" name="password" placeholder="Password" required>
    <button type="submit">Login</button>
    </form><p>Demo: test@test.com / 123456</p></div></body></html>
    '''

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'): return redirect('/')
    return '''
    <!DOCTYPE html>
    <html><head><title>Dashboard</title>
    <style>body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}
    .btn{display:inline-block;padding:20px 40px;margin:15px;background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);color:white;text-decoration:none;border-radius:15px;font-size:20px;font-weight:bold}
    .btn:hover{transform:translateY(-3px)}h1{font-size:36px;margin-bottom:20px}</style></head>
    <body><h1>Welcome Student! 🎓</h1><h2>Study Planner App</h2>
    <a href="/study" class="btn">📚 Study Dashboard</a>
    <a href="/goals" class="btn">🎯 Set Goal</a>
    <a href="/view-goals" class="btn">📊 View Goals</a>
    <a href="/reminders" class="btn">⏰ Reminders</a>
    <a href="/logout" class="btn" style="background:linear-gradient(135deg,#e74c3c,#c0392b)">🚪 Logout</a>
    </body></html>
    '''

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

# ===== 1st YEAR =====
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

# ===== 2nd YEAR =====
@app.route('/year2')
def year2():
    if not session.get('logged_in'): return redirect('/')
    return '''
    <!DOCTYPE html><html><head><title>2nd Year</title><style>body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}
    .btn{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}h1{font-size:32px;margin-bottom:40px}</style></head>
    <body><h1>📚 2nd Year</h1><a href="/sem3" class="btn">Semester 3</a><a href="/sem4" class="btn">Semester 4</a>
    <br><a href="/study" class="btn" style="background:#f39c12">← Back</a></body></html>
    '''

@app.route('/sem3')
def sem3():
    if not session.get('logged_in'): return redirect('/')
    return '''
    <!DOCTYPE html><html><head><title>Semester 3</title><style>body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}
    .btn{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}h1{font-size:32px;margin-bottom:40px}</style></head>
    <body><h1>📖 Semester 3</h1>
    <a href="/subject/ds" class="btn">Data Structures</a>
    <a href="/subject/algo" class="btn">Algorithms</a>
    <a href="/subject/dbms" class="btn">DBMS</a>
    <br><a href="/year2" class="btn" style="background:#f39c12">← Back</a></body></html>
    '''

@app.route('/sem4')
def sem4():
    if not session.get('logged_in'): return redirect('/')
    return '''
    <!DOCTYPE html><html><head><title>Semester 4</title><style>body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}
    .btn{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}h1{font-size:32px;margin-bottom:40px}</style></head>
    <body><h1>📖 Semester 4</h1>
    <a href="/subject/oop" class="btn">OOP</a>
    <a href="/subject/networks" class="btn">Networks</a>
    <a href="/subject/os" class="btn">OS</a>
    <br><a href="/year2" class="btn" style="background:#f39c12">← Back</a></body></html>
    '''

# ===== 3rd YEAR =====
@app.route('/year3')
def year3():
    if not session.get('logged_in'): return redirect('/')
    return '''
    <!DOCTYPE html><html><head><title>3rd Year</title><style>body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}
    .btn{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}h1{font-size:32px;margin-bottom:40px}</style></head>
    <body><h1>📚 3rd Year</h1><a href="/sem5" class="btn">Semester 5</a><a href="/sem6" class="btn">Semester 6</a>
    <br><a href="/study" class="btn" style="background:#f39c12">← Back</a></body></html>
    '''

@app.route('/sem5')
def sem5():
    if not session.get('logged_in'): return redirect('/')
    return '''
    <!DOCTYPE html><html><head><title>Semester 5</title><style>body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}
    .btn{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}h1{font-size:32px;margin-bottom:40px}</style></head>
    <body><h1>📖 Semester 5</h1>
    <a href="/subject/ml" class="btn">Machine Learning</a>
    <a href="/subject/ai" class="btn">AI</a>
    <a href="/subject/cloud" class="btn">Cloud Computing</a>
    <br><a href="/year3" class="btn" style="background:#f39c12">← Back</a></body></html>
    '''

@app.route('/sem6')
def sem6():
    if not session.get('logged_in'): return redirect('/')
    return '''
    <!DOCTYPE html><html><head><title>Semester 6</title><style>body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}
    .btn{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}h1{font-size:32px;margin-bottom:40px}</style></head>
    <body><h1>📖 Semester 6</h1>
    <a href="/subject/project" class="btn">Project</a>
    <a href="/subject/internship" class="btn">Internship</a>
    <a href="/subject/electives" class="btn">Electives</a>
    <br><a href="/year3" class="btn" style="background:#f39c12">← Back</a></body></html>
    '''

# ===== SUBJECT NOTES PAGES =====
@app.route('/subject/<subject_name>')
def subject_notes(subject_name):
    if not session.get('logged_in'): return redirect('/')
    return f'''
    <!DOCTYPE html><html><head><title>{subject_name} Notes</title><style>body{{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}}
    .btn{{padding:20px 40px;margin:20px;background:#e74c3c;color:white;text-decoration:none;border-radius:15px;font-size:20px;display:inline-block}}.download-btn{{background:#27ae60}}h1{{font-size:36px;margin-bottom:40px}}</style></head>
    <body><h1>📚 {subject_name.replace("-"," ").title()} Notes</h1>
    <a href="/upload/{subject_name}" class="btn">📤 Upload PDF Notes</a>
    <a href="/static/uploads/{subject_name}.pdf" class="download-btn btn" target="_blank">📥 Download PDF</a>
    <a href="/dashboard" class="btn" style="background:#f39c12">← Dashboard</a></body></html>
    '''

@app.route('/upload/<subject_name>', methods=['GET', 'POST'])
def upload_notes(subject_name):
    if not session.get('logged_in'): return redirect('/')
    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                os.makedirs('static/uploads', exist_ok=True)
                file.save(f'static/uploads/{subject_name}.pdf')
                return f'<h1 style="text-align:center;color:green">✅ {subject_name} PDF Uploaded!</h1><a href="/subject/{subject_name}">← Back</a>'
    return f'''
    <!DOCTYPE html><html><head><title>Upload {subject_name}</title><style>body{{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}}
    input[type=file]{{width:400px;padding:15px;margin:20px;border-radius:10px;border:none;background:rgba(255,255,255,0.9)}}button{{padding:20px 40px;margin:20px;background:#50c878;color:white;border:none;border-radius:15px;font-size:20px;cursor:pointer}}h1{{font-size:36px;margin-bottom:40px}}</style></head>
    <body><h1>📤 Upload {subject_name} Notes</h1>
    <form method="POST" enctype="multipart/form-data">
    <input type="file" name="file" accept=".pdf" required><br>
    <button type="submit">✅ Upload PDF</button>
    </form><a href="/subject/{subject_name}" style="color:#3498db;font-size:20px">← Back to {subject_name}</a></body></html>
    '''

@app.route('/goals', methods=['GET', 'POST'])
def goals():
    if not session.get('logged_in'): return redirect('/')
    if request.method == 'POST':
        session['goals'] = session.get('goals', []) + [request.form['subject']]
        return redirect('/view-goals')
    return '''
    <!DOCTYPE html><html><head><title>Set Goals</title><style>body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}
    input{{width:300px;padding:15px;margin:10px;font-size:16px;border-radius:10px;border:none}}button{{padding:20px 40px;margin:20px;background:#50c878;color:white;border:none;border-radius:15px;font-size:20px;cursor:pointer}}h1{{font-size:36px;margin-bottom:40px}}</style></head>
    <body><h1>🎯 Set Study Goals</h1>
    <form method="POST">
    Subject: <input name="subject" required><br>
    Goal: <input name="goal" required><br>
    Target Score: <input name="target_score" type="number"><br>
    Study Hours: <input name="study_hours" type="number"><br>
    <button type="submit">✅ Save Goal</button></form>
    <a href="/dashboard" style="color:white;font-size:20px">← Dashboard</a></body></html>
    '''

@app.route('/view-goals')
def view_goals():
    if not session.get('logged_in'): return redirect('/')
    goals = session.get('goals', [])
    goals_html = ''.join([f'<div style="background:rgba(255,255,255,0.1);padding:20px;margin:20px;border-radius:15px"><h3>📚 {g}</h3><div style="background:#2ecc71;width:60%;height:20px;border-radius:10px;margin:10px auto"></div><p>Progress: 60% ✅</p></div>' for g in goals])
    if not goals:
        goals_html = '<p>No goals set yet. <a href="/goals" style="color:#f1c40f">Set goals now!</a></p>'
    return f'''
    <!DOCTYPE html><html><head><title>View Goals</title><style>body{{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}}h1{{font-size:36px;margin-bottom:40px}}</style></head>
    <body><h1>📊 Your Goals</h1>{goals_html}<a href="/dashboard" style="color:white;font-size:20px">← Dashboard</a></body></html>
    '''
    
@app.route('/reminders')
def reminders():
    if not session.get('logged_in'): return redirect('/')
    return '''
    <!DOCTYPE html><html><head><title>Reminders</title><style>body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}
    .card{background:linear-gradient(135deg,orange,#f39c12);padding:25px;margin:20px;border-radius:20px;display:inline-block;box-shadow:0 10px 30px rgba(0,0,0,0.3)}
    .btn{padding:20px 40px;margin:20px;background:#50c878;color:white;text-decoration:none;border-radius:15px;font-size:20px}h1{font-size:36px}</style></head>
    <body><h1>⏰ Study Reminders</h1>
    <div class="card">📚 <b>Maths Test</b><br>Tomorrow 10AM</div>
    <div class="card">🎯 <b>Physics Ch3</b><br>Friday Deadline</div>
    <a href="/dashboard" class="btn">← Dashboard</a></body></html>
    '''
    
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

