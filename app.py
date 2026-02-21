from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import sqlite3
import os
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.secret_key = 'studyplanner2026'

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT, name TEXT)''')
    # Subjects table
    c.execute('''CREATE TABLE IF NOT EXISTS subjects 
                 (id INTEGER PRIMARY KEY, year TEXT, semester TEXT, name TEXT)''')
    # Notes table
    c.execute('''CREATE TABLE IF NOT EXISTS notes 
                 (id INTEGER PRIMARY KEY, subject_id INTEGER, filename TEXT, upload_date TEXT)''')
    # Goals table
    c.execute('''CREATE TABLE IF NOT EXISTS goals 
                 (user_id INTEGER, subject_id INTEGER, description TEXT, target_score INTEGER, hours INTEGER, progress INTEGER)''')
    
    # Test user
    c.execute("INSERT OR IGNORE INTO users VALUES (1, 'test@test.com', '123456', 'Student')")
    # Sample subjects
    c.execute("INSERT OR IGNORE INTO subjects (year, semester, name) VALUES ('1st Year', 'Sem 1', 'Maths')")
    c.execute("INSERT OR IGNORE INTO subjects (year, semester, name) VALUES ('1st Year', 'Sem 1', 'Physics')")
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['name'] = user[3]
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Wrong credentials! Use: test@test.com / 123456")
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', name=session['name'])

@app.route('/study')
def study():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT year FROM subjects ORDER BY year")
    years = c.fetchall()
    conn.close()
    return render_template('study.html', years=years)

@app.route('/study/<year>')
def semester(year):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT semester FROM subjects WHERE year=? ORDER BY semester", (year,))
    semesters = c.fetchall()
    conn.close()
    return render_template('semester.html', year=year, semesters=semesters)

@app.route('/study/<year>/<sem>')
def subjects(year, sem):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM subjects WHERE year=? AND semester=? AND name NOT LIKE '%Sample%'", (year, sem))
    subjects_list = c.fetchall()
    conn.close()
    return render_template('subjects.html', year=year, sem=sem, subjects=subjects_list)

@app.route('/goals')
def goals():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('goals.html')

@app.route('/view-goals')
def view_goals():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('view_goals.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
