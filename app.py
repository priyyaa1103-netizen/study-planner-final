from flask import Flask, request, redirect, session
app = Flask(__name__)
app.secret_key = 'key123'

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
    <center><h1>Welcome to Study Planner! 🎓</h1>
    <a href="/study"><button style="padding:20px;font-size:20px">📚 Study Dashboard</button></a><br><br>
    <a href="/logout"><button style="padding:20px;font-size:20px;background:red;color:white">Logout</button></a>
    '''

@app.route('/study')
def study():
    return '''
    <center><h1>📚 Study Dashboard</h1>
    <button style="padding:20px;font-size:20px">1st Year</button><br><br>
    <a href="/dashboard"><button style="padding:20px;font-size:20px">← Back</button></a>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    from os import environ
    port = int(environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
