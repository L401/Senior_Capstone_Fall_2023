from flask import Flask, render_template
from elasticsearch import Elasticsearch
#from elastic.semantic import semantic_search

SEARCH_SIZE = 5

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/elastic_search')
def call_elastic_search():
    #result = semantic_search
    return 0

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)