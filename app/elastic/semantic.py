import json
import hashlib
import sys
from bert_serving.client import BertClient
from elasticsearch import Elasticsearch, helpers
from flask import Blueprint, request, jsonify
from time import sleep

semantic = Blueprint("semantic", __name__)

max_retries = 5
wait_seconds = 5

#retry initializing bert client because it doesnt auto retry and will hang
for attempt in range(max_retries):
    try:
        # Attempt to connect to the BERT server
        bc = BertClient(check_length=False, ip="bert", timeout=2000, port=5555, port_out=5556)
        print("Connected to BERT server.")
        break
    except Exception as e:
        print(f"Connection attempt {attempt + 1}/{max_retries} failed: {e}")
        if attempt < max_retries - 1:
            print(f"Retrying in {wait_seconds} seconds...")
            sleep(wait_seconds)
        else:
            print("Could not connect to the BERT server after several retries.")
            sys.exit(1)

# Initialize Elasticsearch client
try:
    es = Elasticsearch(hosts=["http://elasticsearch:9200"])
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
        texts = []
        #funky custom data scraper from json to pull all dictionary elements listed under "subheader"
        for item in data:
            subheaders = item.get("subheader", {})
            for subheader_title, subheader_content in subheaders.items():
                if isinstance(subheader_content, str) and subheader_content.strip():
                    texts.append(subheader_content)
        return texts

def index_data(data):
    try:
        actions = []
        for text in data:
            # Create a hash of the text content to recognize if it was previously indexed
            doc_id = hashlib.sha256(text.encode()).hexdigest()
            # Check if the document already exists by cross referencing with hash
            if not es.exists(index=INDEX_NAME, id=doc_id):
                # Generate embedding only if the document does not exist
                embedding = bc.encode([text])[0].tolist()
                action = {
                    "_index": INDEX_NAME,
                    "_id": doc_id,  # Set the document ID
                    "_source": {
                        "text": text,
                        "embedding": embedding
                    }
                }
                actions.append(action)
        if actions:
            #helps to bulk process actions that are stored in the actions "queue"
            helpers.bulk(es, actions)
            es.indices.refresh(index=INDEX_NAME)
            print("Data indexed/updated successfully.")
        else:
            print("No data to index or data already indexed.")
    except Exception as e:
        print("Error indexing data:", str(e))

@semantic.route('/api/elastic_search', methods=["POST"])
def semantic_search():
    try:
        #assigns the user_data post request as the query
        data = request.get_json()
        query = data.get("user_input")
        size = data.get("size", 5)
        #creates embedd for the query
        embedding = bc.encode([query])[0].tolist()
        script_query = {
            "script_score": {
                "query": {"match_all": {}}, #matches the query against all indexed strings
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0", #assigns and normalizes score between -1 and 1
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
        #finds the source document and the text stored along with it and returns the "hit" at each of the hit keys
        return [hit["_source"]["text"] for hit in response["hits"]["hits"]] #returns all the answers
    except Exception as e:
        print("Error executing search:", str(e))
        return jsonify({"error": str(e)})

# Load data from file
data = load_data('./data/extracted_data.json')

# Index data
index_data(data)