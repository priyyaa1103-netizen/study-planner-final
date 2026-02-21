@app.route('/maths')
def maths():
    return '''
<center><h1>📖 Maths</h1>
<h2>Notes Section</h2>
<form>Upload PDF: <input type="file" accept=".pdf"><button>Upload</button></form><br>
<button style="padding:15px 30px;background:green;color:white">📥 Download Notes</button><br>
<p>📄 Available: Maths-Notes-1.pdf, Formula-Sheet.pdf</p>
<br><a href="/sem1"><button style="padding:20px 40px;font-size:20px;background:orange">← Back</button></a>
    '''

@app.route('/physics')
def physics():
    return '''
<center><h1>⚛️ Physics</h1>
<h2>Notes Section</h2>
<form>Upload PDF: <input type="file" accept=".pdf"><button>Upload</button></form><br>
<button style="padding:15px 30px;background:green;color:white">📥 Download Notes</button><br>
<p>📄 Available: Physics-Notes.pdf, Mechanics.pdf</p>
<br><a href="/sem1"><button style="padding:20px 40px;font-size:20px;background:orange">← Back</button></a>
    '''

@app.route('/chem')
def chem():
    return '''
<center><h1>🧪 Chemistry</h1>
<h2>Notes Section</h2>
<form>Upload PDF: <input type="file" accept=".pdf"><button>Upload</button></form><br>
<button style="padding:15px 30px;background:green;color:white">📥 Download Notes</button><br>
<p>📄 Available: Chemistry-Notes.pdf, Organic.pdf</p>
<br><a href="/sem1"><button style="padding:20px 40px;font-size:20px;background:orange">← Back</button></a>
    '''
