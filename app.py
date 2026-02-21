from flask import Flask,request,redirect,session
app=Flask(__name__)
app.secret_key='study2026'

@app.route('/',methods=['GET','POST'])
def login():
 if request.method=='POST':
  if request.form['email']=='test@test.com' and request.form['password']=='123456':
   session['logged_in']=True;return redirect('/dashboard')
 return'<center><h1>🎓 Study Planner</h1><form method="POST"><input name="email" placeholder="test@test.com"><br><input name="password" type="password" placeholder="123456"><br><button>Login</button></form></center>'

@app.route('/dashboard')
def dashboard():
 if not session.get('logged_in'):return redirect('/')
 return'<center><h1>Welcome! 🎓</h1><a href="/study"><button>📚 Study</button></a><a href="/goals"><button>🎯 Goals</button></a><a href="/view-goals"><button>📊 Progress</button></a><a href="/logout"><button style="background:red;color:white">Logout</button></a></center>'

@app.route('/study')
def study():
 if not session.get('logged_in'):return redirect('/')
 return'<center><h1>📚 Study Dashboard</h1><a href="/year1"><button>1st Year</button></a><a href="/year2"><button>2nd Year</button></a><a href="/year3"><button>3rd Year</button></a><br><a href="/dashboard"><button>← Back</button></a></center>'

@app.route('/year1')
def year1():return'<center><h1>1st Year</h1><a href="/sem1"><button>Sem 1</button></a><a href="/sem2"><button>Sem 2</button></a><br><a href="/study"><button>← Back</button></a></center>'

@app.route('/year2')
def year2():return'<center><h1>2nd Year</h1><a href="/sem3"><button>Sem 3</button></a><a href="/sem4"><button>Sem 4</button></a><br><a href="/study"><button>← Back</button></a></center>'

@app.route('/year3')
def year3():return'<center><h1>3rd Year</h1><a href="/sem5"><button>Sem 5</button></a><a href="/sem6"><button>Sem 6</button></a><br><a href="/study"><button>← Back</button></a></center>'

@app.route('/sem1')
def sem1():return'<center><h1>Sem 1</h1><a href="/maths"><button>Maths</button></a><a href="/physics"><button>Physics</button></a><a href="/chem"><button>Chemistry</button></a><br><a href="/year1"><button>← Back</button></a></center>'

@app.route('/sem2')
def sem2():return'<center><h1>Sem 2</h1><a href="/maths2"><button>Adv Maths</button></a><a href="/physics2"><button>Physics-II</button></a><a href="/bio"><button>Biology</button></a><br><a href="/year1"><button>← Back</button></a></center>'

@app.route('/sem3')
def sem3():return'<center><h1>Sem 3</h1><a href="/ds"><button>Data Structures</button></a><a href="/algo"><button>Algorithms</button></a><a href="/dbms"><button>DBMS</button></a><br><a href="/year2"><button>← Back</button></a></center>'

@app.route('/sem4')
def sem4():return'<center><h1>Sem 4</h1><a href="/oops"><button>OOPS</button></a><a href="/network"><button>Networks</button></a><a href="/os"><button>OS</button></a><br><a href="/year2"><button>← Back</button></a></center>'

@app.route('/sem5')
def sem5():return'<center><h1>Sem 5</h1><a href="/ai"><button>AI</button></a><a href="/ml"><button>ML</button></a><a href="/web"><button>Web Dev</button></a><br><a href="/year3"><button>← Back</button></a></center>'

@app.route('/sem6')
def sem6():return'<center><h1>Sem 6</h1><a href="/cloud"><button>Cloud</button></a><a href="/security"><button>Security</button></a><a href="/project"><button>Project</button></a><br><a href="/year3"><button>← Back</button></a></center>'

@app.route('/maths')
def maths():return'<center><h1>📖 Maths</h1><h2>Notes</h2><form>Upload PDF:<input type="file" accept=".pdf"></form><button style="background:green;color:white">📥 Download</button><br><a href="/sem1"><button>← Back</button></a></center>'

@app.route('/physics')
def physics():return'<center><h1>⚛️ Physics</h1><h2>Notes</h2><form>Upload PDF:<input type="file" accept=".pdf"></form><button style="background:green;color:white">📥 Download</button><br><a href="/sem1"><button>← Back</button></a></center>'

@app.route('/chem')
def chem():return'<center><h1>🧪 Chemistry</h1><h2>Notes</h2><form>Upload PDF:<input type="file" accept=".pdf"></form><button style="background:green;color:white">📥 Download</button><br><a href="/sem1"><button>← Back</button></a></center>'

@app.route('/goals')
def goals():return'<center><h1>🎯 Set Goals</h1><form method="POST">Subject:<input name="sub"><br>Hours:<input name="hours"><button>Add Goal</button></form><br><a href="/dashboard"><button>← Back</button></a></center>'

@app.route('/view-goals')
def view_goals():return'<center><h1>📊 Progress: 80%</h1><div style="width:300px;height:30px;background:grey;margin:20px auto"><div style="width:80%;height:30px;background:green"></div></div><a href="/dashboard"><button>← Back</button></a></center>'

@app.route('/reminders')
def reminders():return'<center><h1>⏰ Reminders</h1><p>Maths exam - 2 days left!</p><a href="/dashboard"><button>← Back</button></a></center>'

@app.route('/logout')
def logout():
 session.clear()
 return redirect('/')

if __name__=='__main__':
 from os import environ
 port=int(environ.get('PORT',5000))
 app.run(host='0.0.0.0',port=port)
