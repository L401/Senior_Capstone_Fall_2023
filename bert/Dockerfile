FROM tensorflow/tensorflow:1.12.0-py3

RUN pip install --no-cache-dir bert-serving-server

COPY . /bert

WORKDIR /bert

RUN chmod +x bert_start.sh

ENTRYPOINT ["./bert_start.sh"]