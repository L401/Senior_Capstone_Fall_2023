from bert_serving.client import BertClient
from elasticsearch import Elasticsearch, helpers
from flask import Flask

app = Flask(__name__)

# Initialize BERT client
bc = BertClient()

# Initialize Elasticsearch client
es = Elasticsearch(hosts=["http://localhost:9200"])

INDEX_NAME = "semantic_search"

# Ensure the index exists
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

def index_data(data):
    """
    Index data into Elasticsearch.
    :param data: List of texts to be indexed.
    """
    actions = []
    for text in data:
        embedding = bc.encode([text])[0].tolist()
        action = {
            "_index": INDEX_NAME,
            "_source": {
                "text": text,
                "embedding": embedding
            }
        }
        actions.append(action)
    helpers.bulk(es, actions)

@app.route('/api/elastic_search')
def semantic_search(query, size=4):
    """
    Perform semantic search.
    :param query: Search query.
    :param size: Number of results to return.
    :return: List of search results.
    """
    embedding = bc.encode([query])[0].tolist()
    script_query = {
    "script_score": {
        "query": {"match_all": {}},
        "script": {
            "source": "return 1.0;",
        }
    }
    }
    try:
        response = es.search(index=INDEX_NAME, body={
            "size": size,
            "query": script_query,
            "_source": {"includes": ["text"]}
        })
    except Exception as e:
        print(str(e))  # Print detailed error information
        raise e
    return [hit["_source"]["text"] for hit in response["hits"]["hits"]]

# Sample data to index
data = ["2.5.1.4 Notify the TOMA of any TOs which require post-publication command reviews.", "2.8.4.1 Request TO numbering and indexing, typically outside of ETIMS", "what even is this", "totally wrong answer"]
index_data(data)

# Sample search
query = "when should I notify the TOMA"
results = semantic_search(query)
print(results)
