import json
import os
import pysolr
import requests
import pandas as pd

CORE_NAME = "IRF24P3"
VM_IP = "34.130.33.83"
CORPUS_FILE='All_topics_combined_final.json'


def delete_core(core=CORE_NAME):
    print(os.system('sudo su - solr -c "/opt/solr/bin/solr delete -c {core}"'.format(core=core)))


def create_core(core=CORE_NAME):
    print(os.system(
        'sudo su - solr -c "/opt/solr/bin/solr create -c {core} -n data_driven_schema_configs"'.format(
            core=core)))

class Indexer:
    def __init__(self):
        self.solr_url = f'http://{VM_IP}:8983/solr/'
        self.connection = pysolr.Solr(self.solr_url + CORE_NAME, always_commit=True, timeout=5000000)

    def do_initial_setup(self):
        delete_core()
        create_core()

    def create_documents(self, docs):
        print(self.connection.add(docs))

    def add_fields(self):
        data = {
            "add-field": [
                {
                    "name": "title",
                    "type": "string",
                    "indexed": True,
                    "multiValued": False
                },
                {
                    "name": "revision_id",
                    "type": "string",
                    "multiValued": False
                },
                {
                    "name": "url",
                    "type": "string",
                    "multiValued": False
                },
                {
                    "name": "summary",
                    "type": "text_en",
                    "indexed": True,
                    "multiValued": False
                },
                {
                    "name": "topic",
                    "type": "string",
                    "indexed": True,
                    "multiValued": False
                },
            ]
        }

        print(requests.post(self.solr_url + CORE_NAME + "/schema", json=data).json())

# Load the data from the json file
file_name = CORPUS_FILE 
with open(file_name) as f:
    data = json.load(f)

# Pad the data in the one that doesnt have 520 documents
def pad_docs(docs, total_len, topic):
    if len(docs) >= total_len:
        return docs[:total_len]
    else:
        pad_data = [{'summary': '', 'revision_id': '', 'title': '', 'revision_id': '', topic: topic}] * (total_len - len(docs))
        return docs + pad_data

padded_data_final = {}
total_length = 5000 
for topic, docs in data.items():
    padded_data_final[str(topic)] = pad_docs(docs, total_length, topic)

df = pd.DataFrame(padded_data_final)

i = Indexer()
i.do_initial_setup()
i.add_fields()

collection = df.to_dict('records')
i.create_documents(collection)

solr_url_ = f'http://{VM_IP}:8983/solr/'
connection_ = pysolr.Solr(solr_url_ + CORE_NAME, always_commit=True, timeout=5000000)

# Query all documents
res = connection_.search('*:*', )
print(f"Total number of documents indexed: {len(res)}")
for i in res:
    print(i)
