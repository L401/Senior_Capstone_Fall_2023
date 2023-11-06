from bert_serving.client import BertClient
from elasticsearch import Elasticsearch, helpers

from flask import Flask

app = Flask(__name__)

import json
import hashlib


# Initialize BERT client
try:
    bc = BertClient(check_length=False)
    print("BERT client initialized successfully.")
except Exception as e:
    print("Error initializing BERT client:", str(e))

# Initialize Elasticsearch client
try:
    es = Elasticsearch(hosts=["http://localhost:9200"])
    print("Elasticsearch client initialized successfully.")
except Exception as e:
    print("Error initializing Elasticsearch client:", str(e))

INDEX_NAME = "semantic_search"

# Ensure the index exists
try:
    if not es.indices.exists(index=INDEX_NAME):
        es.indices.create(index=INDEX_NAME, body={
            "mappings": {
                "properties": {
                    "embedding": {
                        "type": "dense_vector",
                        "dims": 768  # Assuming BERT base model
                    }
                }
            }
        })
    print("Index created/exists successfully.")
except Exception as e:
    print("Error creating index:", str(e))

def load_data(filepath):
    with open(filepath, 'r') as file:
        data = json.load(file)
        return [item["subheader"] for item in data if item["subheader"].strip()]

def index_data(data):
    try:
        actions = []
        for text in data:
            # Create a hash of the text content
            doc_id = hashlib.sha256(text.encode()).hexdigest()

@app.route('/api/elastic_search')
def semantic_search(query, size=5):
    try:
        embedding = bc.encode([query])[0].tolist()
        script_query = {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                    "params": {"query_vector": embedding}
                }
            }
        }
        response = es.search(index=INDEX_NAME, body={
            "size": size,
            "query": script_query,
            "_source": {"includes": ["text"]}
        })
        print("Search executed successfully.")
        return [hit["_source"]["text"] for hit in response["hits"]["hits"]]
    except Exception as e:
        print("Error executing search:", str(e))
        return []

# Load data from file
data = load_data('../data/extracted_data.json')

# Index data
index_data(data)

# Sample search
query = "What is TODPG?"
results = semantic_search(query)
print("Search results:", results)
