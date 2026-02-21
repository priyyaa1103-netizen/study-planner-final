@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Dashboard</title>
    <style>body{font-family:Arial;background:#4a90e2;color:white;padding:50px;text-align:center}
    button{padding:20px 40px;margin:20px;background:#50c878;color:white;border:none;border-radius:10px;font-size:20px;cursor:pointer}
    h1{font-size:32px;margin-bottom:50px}</style></head>
    <body>
    <h1>Welcome {{name}}! 🎓</h1>
    <h2>Study Planner & Reminder App</h2>
    <a href='/study'><button>📚 Study Dashboard</button></a>
    <a href='/goals'><button>🎯 Set Goal</button></a>
    <a href='/view-goals'><button>📊 View Goals</button></a>
    <a href='/reminders'><button>⏰ Reminders</button></a>
    </body>
    </html>
    """.replace('{{name}}', session['name'])v
