from flask import Flask, render_template
from waitress import serve
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('pindex.html')

if __name__ == '__main__':
    # Serve the app on http://127.0.0.1:8000
    serve(app, host="0.0.0.0", port=8000)
