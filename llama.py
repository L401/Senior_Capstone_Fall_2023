import chromadb
import os

chroma_client = chromadb.Client()
collection = chroma_client.create_collection(name="data")


def read_files(folder_path):
    file_data = []

    for file_name in os.listdir(folder_path):
        if file_name.endswith(".txt"):
            with open(os.path.join(folder_path, file_name), 'r') as file:
                content = file.read()
                file_data.append({"file_name": file_name, "content": content})

    return file_data

folder_path = 'db'
file_data = read_files(folder_path)

documents = []
metadatas = []
ids = []

for index, data in enumerate(file_data):
    documents.append(data['content'])
    metadatas.append({'source': data['file_name']})
    ids.append(str(index+1))

collection.add(
    documents=documents,
    metadatas=metadatas,
    ids=ids
)

results = collection.query(
    query_texts=["what does b recondition?"],
    n_results=1
)

print(results)