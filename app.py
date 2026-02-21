from flask import Flask, request, redirect, session
import os

app = Flask(__name__, template_folder='templates')
app.secret_key = 'study2026'

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
            <input type="email" name="email" placeholder="Email" style="width:100%;padding:15px;margin:10px 0;border-radius:8px"><br>
            <input type="password" name="password" placeholder="Password" style="width:100%;padding:15px;margin:10px 0;border-radius:8px"><br>
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
    if not session.get('logged_in'):
        return redirect('/')
    return '''
    <!DOCTYPE html>
    <html><head><title>Dashboard</title>
    <style>body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}
    .btn{display:inline-block;padding:20px 40px;margin:15px;background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);color:white;text-decoration:none;border-radius:15px;font-size:20px;font-weight:bold}
    .btn:hover{transform:translateY(-3px)}
    h1{font-size:36px;margin-bottom:20px}</style></head>
    <body>
    <h1>Welcome Student! 🎓</h1>
    <h2>Study Planner & Reminder App</h2>
    <a href="/study" class="btn">📚 Study Dashboard</a>
    <a href="/goals" class="btn">🎯 Set Goal</a>
    <a href="/view-goals" class="btn">📊 View Goals</a>
    <a href="/logout" class="btn" style="background:linear-gradient(135deg,#e74c3c,#c0392b)">🚪 Logout</a>
    </body></html>
    '''

# ADD ALL OTHER ROUTES HERE (same as before but inline HTML)
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

@app.route('/year1')
def year1():
    if not session.get('logged_in'): return redirect('/')
    return '''
    <!DOCTYPE html><html><head><title>1st Year</title><style>body{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;min-height:100vh;padding:50px;text-align:center}
    .btn{padding:15px 30px;margin:10px;background:#50c878;color:white;text-decoration:none;border-radius:10px;font-size:18px;display:inline-block}h1{font-size:32px;margin-bottom:40px}</style></head>
    <body><h1>📚 1st Year</h1><a href="/sem1" class="btn">Semester 1</a><a href="/sem2" class="btn">Semester 2</a>
    <br><a href="/study" class="btn" style="background:#f39c12">← Back</a></body></html>
    '''

# Add year2, year3, sem1, sem2... routes same way
# ... (copy your old working routes)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
