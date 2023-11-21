from flask import Flask, render_template
from elasticsearch import Elasticsearch
from elastic.semantic import semantic
from elastic.semantic import semantic_search
import traceback

SEARCH_SIZE = 5

app = Flask(__name__)
app.register_blueprint(semantic)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chatbox/<int:chatbox_id>')
def chatbox(chatbox_id):
    return render_template('chatbox.html', chatbox_id = chatbox_id)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/upload')
def upload():
    return render_template('upload.html')

if __name__ == "__main__":
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()