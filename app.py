@app.route('/maths')
def maths():
    return '''
<center><h1>📖 Maths</h1>
<h2>Notes Section</h2>
<form>Upload PDF: <input type="file" accept=".pdf"></form>
<button style="padding:15px 30px;background:green;color:white">📥 Download Notes</button>
<br><br><a href="/sem1"><button style="padding:20px 40px;font-size:20px;background:orange">← Back</button></a>
    '''
