from flask import Flask, request, redirect, session, render_template_string
app = Flask(__name__)
app.secret_key = 'study2026'

users = {'test@test.com': '123456'}

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['email']=='test@test.com' and request.form['password']=='123456':
            session['logged_in'] = True
            session['name'] = 'Student'
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
    <center><h1>Welcome {{name}}! 🎓</h1>
    <h2>Study Planner & Reminder App</h2>
    <a href="/study"><button style="padding:20px 40px;font-size:20px;margin:10px">📚 Study Dashboard</button></a><br>
    <a href="/goals"><button style="padding:20px 40px;font-size:20px;margin:10px">🎯 Set Goal</button></a><br>
    <a href="/view-goals"><button style="padding:20px 40px;font-size:20px;margin:10px">📊 View Goals</button></a><br>
    <a href="/logout"><button style="padding:20px 40px;font-size:20px;margin:10px;background:red;color:white">Logout</button></a>
    '''.replace('{{name}}', session['name'])

@app.route('/study')
def study():
    if not session.get('logged_in'):
        return redirect('/')
    return '''
    <center><h1>📚 Study Dashboard</h1>
    <a href="/study/1st-year"><button style="padding:20px 40px;font-size:20px;margin:10px">1st Year</button></a><br>
    <a href="/study/2nd-year"><button style="padding:20px 40px;font-size:20px;margin:10px">2nd Year</button></a><br>
    <a href="/study/3rd-year"><button style="padding:20px 40px;font-size:20px;margin:10px">3rd Year</button></a><br><br>
    <a href="/dashboard"><button style="padding:20px 40px;font-size:20px;background:orange">← Back</button></a>
    '''

@app.route('/study/<year>')
def semester(year):
    if not session.get('logged_in'):
        return redirect('/')
    sems = {'1st-year': ['Sem 1', 'Sem 2'], '2nd-year': ['Sem 3', 'Sem 4'], '3rd-year': ['Sem 5', 'Sem 6']}
    return '''
    <center><h1>📚 ''' + year.replace('-', ' ').title() + '''</h1>
    {% for sem in semesters %}
    <a href="/subjects/''' + year + '''/{{sem|lower}}"><button style="padding:20px 40px;font-size:20px;margin:10px">''' + year.replace('-', ' ') + ''' {{sem}}</button></a><br>
    {% endfor %}
    <br><a href="/study"><button style="padding:20px 40px;font-size:20px;background:orange">← Back</button></a>
    '''.replace('{% for sem in semesters %}', '
'.join([f'<a href="/subjects/{year}/{s.lower()}"><button style="padding:20px 40px;font-size:20px;margin:10px">{year.replace("-", " ")} {s}</button></a><br>' for s in sems.get(year, [])])).replace('{% endfor %}', '')

@app.route('/subjects/<year>/<sem>')
def subjects(year, sem):
    if not session.get('logged_in'):
        return redirect('/')
    subjects_list = {
        '1st-year/sem-1': ['Maths', 'Physics', 'Chemistry'],
        '1st-year/sem-2': ['Maths-II', 'Physics-II', 'Biology'],
        '2nd-year/sem-3': ['Data Structures', 'Algorithms', 'DBMS'],
        '2nd-year/sem-4': ['OOPS', 'Networks', 'OS'],
        '3rd-year/sem-5': ['AI', 'ML', 'Web Dev'],
        '3rd-year/sem-6': ['Cloud', 'Security', 'Project']
    }
    subs = subjects_list.get(f'{year}/{sem}', [])
    buttons = ''.join([f'<a href="/notes/{year}/{sem}/{sub.lower().replace(" ", "-")}"><button style="padding:15px 30px;font-size:18px;margin:10px">{sub}</button></a><br>' for sub in subs])
    return f'''
    <center><h1>📖 {year.replace("-", " ").title()} {sem.replace("sem-", "Sem ").title()}</h1>
    <h2>Select Subject:</h2>
    {buttons}
    <br><a href="/study/{year}"><button style="padding:20px 40px;font-size:20px;background:orange">← Back</button></a>
    '''

@app.route('/notes/<year>/<sem>/<subject>')
def notes(year, sem, subject):
    if not session.get('logged_in'):
        return redirect('/')
    return f'''
    <center><h1>📚 {subject.replace("-", " ").title()}</h1>
    <h2>Notes Section</h2>
    <p><b>Upload Notes:</b> <input type="file" accept=".pdf"></p>
    <p><button style="padding:15px 30px;background:green;color:white">📥 Download Notes</button></p>
    <br><a href="/subjects/{year}/{sem}"><button style="padding:20px 40px;font-size:20px;background:orange">← Back</button></a>
    '''

@app.route('/goals', methods=['GET', 'POST'])
def goals():
    if not session.get('logged_in'):
        return redirect('/')
    if request.method == 'POST':
        session['goals'] = session.get('goals', []) + [request.form.to_dict()]
    goals_list = session.get('goals', [])
    return '''
    <center><h1>🎯 Set Goals</h1>
    <form method="POST">
    Subject: <input name="subject"><br>
    Description: <input name="desc"><br>
    Target Score: <input name="score"><br>
    Study Hours: <input name="hours"><br><br>
    <button style="padding:15px 30px;font-size:18px">Set Goal</button>
    </form>
    <h3>Your Goals:</h3>
    ''' + ''.join([f'<p>📚 {g.get("subject", "N/A")} - {g.get("desc", "N/A")} (Score: {g.get("score", 0)})</p>' for g in goals_list]) + '''
    <br><a href="/dashboard"><button style="padding:20px 40px;font-size:20px;background:orange">← Back</button></a>
    '''

@app.route('/view-goals')
def view_goals():
    if not session.get('logged_in'):
        return redirect('/')
    goals_list = session.get('goals', [])
    progress = min(80, len(goals_list) * 20) if goals_list else 0
    return f'''
    <center><h1>📊 View Goals</h1>
    <h2>Progress: {progress}%</h2>
    <div style="background:grey;width:300px;height:30px;border-radius:15px;margin:20px auto">
    <div style="background:green;width:{progress}%;height:30px;border-radius:15px"></div>
    </div>
    <h3>Goals:</h3>
    ''' + ''.join([f'<p>✅ {g.get("subject", "N/A")} - {g.get("desc", "N/A")}</p>' for g in goals_list]) + '''
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
