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
<center><h1>🎓 Study Planner Login</h1>
<form method="POST">
Email: <input name="email"><br>
Password: <input name="password" type="password"><br><br>
<button>Login</button>
</form>
<p>test@test.com / 123456</p>
    '''

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect('/')
    return '''
<center><h1>Welcome Student! 🎓</h1>
<h2>Study Planner App</h2>
<a href="/study"><button style="padding:20px 40px;font-size:20px;margin:10px">📚 Study Dashboard</button></a><br>
<a href="/goals"><button style="padding:20px 40px;font-size:20px;margin:10px">🎯 Set Goal</button></a><br>
<a href="/view-goals"><button style="padding:20px 40px;font-size:20px;margin:10px">📊 View Goals</button></a><br>
<a href="/logout"><button style="padding:20px 40px;font-size:20px;margin:10px;background:red;color:white">Logout</button></a>
    '''

@app.route('/study')
def study():
    if not session.get('logged_in'):
        return redirect('/')
    return '''
<center><h1>📚 Study Dashboard</h1>
<a href="/year1"><button style="padding:20px 40px;font-size:20px;margin:10px">1st Year</button></a><br>
<a href="/year2"><button style="padding:20px 40px;font-size:20px;margin:10px">2nd Year</button></a><br>
<a href="/year3"><button style="padding:20px 40px;font-size:20px;margin:10px">3rd Year</button></a><br><br>
<a href="/dashboard"><button style="padding:20px 40px;font-size:20px;background:orange">← Back</button></a>
    '''

@app.route('/year1')
def year1():
    return '''
<center><h1>📚 1st Year</h1>
<a href="/sem1"><button style="padding:20px 40px;font-size:20px;margin:10px">Semester 1</button></a><br>
<a href="/sem2"><button style="padding:20px 40px;font-size:20px;margin:10px">Semester 2</button></a><br><br>
<a href="/study"><button style="padding:20px 40px;font-size:20px;background:orange">← Back</button></a>
    '''

@app.route('/year2')
def year2():
    return '''
<center><h1>📚 2nd Year</h1>
<a href="/sem3"><button style="padding:20px 40px;font-size:20px;margin:10px">Semester 3</button></a><br>
<a href="/sem4"><button style="padding:20px 40px;font-size:20px;margin:10px">Semester 4</button></a><br><br>
<a href="/study"><button style="padding:20px 40px;font-size:20px;background:orange">← Back</button></a>
    '''

@app.route('/year3')
def year3():
    return '''
<center><h1>📚 3rd Year</h1>
<a href="/sem5"><button style="padding:20px 40px;font-size:20px;margin:10px">Semester 5</button></a><br>
<a href="/sem6"><button style="padding:20px 40px;font-size:20px;margin:10px">Semester 6</button></a><br><br>
<a href="/study"><button style="padding:20px 40px;font-size:20px;background:orange">← Back</button></a>
    '''

@app.route('/sem1')
def sem1():
    return '''
<center><h1>📖 Semester 1</h1>
<a href="/maths"><button style="padding:20px 40px;font-size:20px;margin:10px">Maths</button></a><br>
<a href="/physics"><button style="padding:20px 40px;font-size:20px;margin:10px">Physics</button></a><br>
<a href="/chem"><button style="padding:20px 40px;font-size:20px;margin:10px">Chemistry</button></a><br><br>
<a href="/year1"><button style="padding:20px 40px;font-size:20px;background:orange">← Back</button></a>
    '''

@app.route('/goals')
def goals():
    return '''
<center><h1>🎯 Set Goals</h1>
<form method="POST">
Subject: <input name="subject"><br>
Description: <input name="goal"><br><br>
<button style="padding:15px 30px;font-size:18px">Add Goal</button>
</form>
<br><a href="/dashboard"><button style="padding:20px 40px;font-size:20px;background:orange">← Back</button></a>
    '''

@app.route('/view-goals')
def view_goals():
    return '''
<center><h1>📊 View Goals - 75% Complete!</h1>
<div style="background:grey;width:300px;height:30px;border-radius:15px;margin:20px auto">
<div style="background:green;width:75%;height:30px;border-radius:15px"></div>
</div>
<br><a href="/dashboard"><button style="padding:20px 40px;font-size:20px;background:orange">← Back</button></a>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    from os import environ
    port = int(environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
