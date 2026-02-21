from flask import Flask, request, redirect, session, render_template
import os

app = Flask(__name__)
app.secret_key = 'study2026'

# Create uploads folder if not exists
os.makedirs('static/uploads', exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['email'] == 'test@test.com' and request.form['password'] == '123456':
            session['logged_in'] = True
            session['name'] = 'Student'
            return redirect('/dashboard')
        return render_template('login.html', error="❌ Wrong credentials!")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect('/')
    return render_template('dashboard.html', name=session.get('name', 'Student'))

@app.route('/study')
def study():
    if not session.get('logged_in'):
        return redirect('/')
    years = [('1st Year',), ('2nd Year',), ('3rd Year',)]
    return render_template('study.html', years=years)

@app.route('/year1')
def year1():
    if not session.get('logged_in'):
        return redirect('/')
    semesters = [('Semester 1',), ('Semester 2',)]
    return render_template('semester.html', year='1st Year', semesters=semesters)

@app.route('/year2')
def year2():
    if not session.get('logged_in'):
        return redirect('/')
    semesters = [('Semester 3',), ('Semester 4',)]
    return render_template('semester.html', year='2nd Year', semesters=semesters)

@app.route('/year3')
def year3():
    if not session.get('logged_in'):
        return redirect('/')
    semesters = [('Semester 5',), ('Semester 6',)]
    return render_template('semester.html', year='3rd Year', semesters=semesters)

@app.route('/sem1')
def sem1():
    if not session.get('logged_in'):
        return redirect('/')
    subjects = [('Maths',), ('Physics',), ('Chemistry',)]
    return render_template('subjects.html', year='1st Year', sem='Semester 1', subjects=subjects)

@app.route('/sem2')
def sem2():
    if not session.get('logged_in'):
        return redirect('/')
    subjects = [('Maths-II',), ('Physics-II',), ('Biology',)]
    return render_template('subjects.html', year='1st Year', sem='Semester 2', subjects=subjects)

@app.route('/sem3')
def sem3():
    if not session.get('logged_in'):
        return redirect('/')
    subjects = [('Data Structures',), ('Algorithms',), ('DBMS',)]
    return render_template('subjects.html', year='2nd Year', sem='Semester 3', subjects=subjects)

@app.route('/sem4')
def sem4():
    if not session.get('logged_in'):
        return redirect('/')
    subjects = [('OOP',), ('Networks',), ('OS',)]
    return render_template('subjects.html', year='2nd Year', sem='Semester 4', subjects=subjects)

@app.route('/sem5')
def sem5():
    if not session.get('logged_in'):
        return redirect('/')
    subjects = [('ML',), ('AI',), ('Cloud',)]
    return render_template('subjects.html', year='3rd Year', sem='Semester 5', subjects=subjects)

@app.route('/sem6')
def sem6():
    if not session.get('logged_in'):
        return redirect('/')
    subjects = [('Project',), ('Internship',), ('Electives',)]
    return render_template('subjects.html', year='3rd Year', sem='Semester 6', subjects=subjects)

# NEW: SUBJECT NOTES PAGES
@app.route('/subject/<subject_name>')
def subject_notes(subject_name):
    if not session.get('logged_in'): 
        return redirect('/')
    return render_template('subject_notes.html', subject=subject_name)

@app.route('/upload/<subject_name>', methods=['GET', 'POST'])
def upload_notes(subject_name):
    if not session.get('logged_in'): 
        return redirect('/')
    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                file.save(f'static/uploads/{subject_name}.pdf')
                return render_template('subject_notes.html', subject=subject_name, message="✅ PDF Uploaded Successfully!")
    return render_template('upload_notes.html', subject=subject_name)

@app.route('/goals', methods=['GET', 'POST'])
def goals():
    if not session.get('logged_in'):
        return redirect('/')
    if request.method == 'POST':
        goal_data = {
            'subject': request.form['subject'],
            'description': request.form['goal'],
            'target_score': request.form.get('target_score', 0),
            'study_hours': request.form.get('study_hours', 0),
            'progress': 0
        }
        goals = session.get('goals', [])
        goals.append(goal_data)
        session['goals'] = goals
        return redirect('/view-goals')
    return render_template('goals.html')

@app.route('/view-goals')
def view_goals():
    if not session.get('logged_in'):
        return redirect('/')
    goals_list = session.get('goals', [])
    return render_template('view_goals.html', goals=goals_list)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
