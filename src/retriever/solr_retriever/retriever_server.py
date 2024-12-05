import flask
import time
from flask import Flask, request
import hashlib
import json
from retriever import Retriever

app = Flask(__name__)

backup_res_output_file = 'retriever_results.json'

@app.route("/retriever_docs", methods=['POST'])
def execute_query():
    start_time = time.time()
    K=5

    query = request.json["query"]
    topics = request.json["topics"]

    query_terms = []
    
    normalized_query, original_query = retriever.query_normalizer([query])
    print("FROM SERVER, PRINTING normalzied query")
    print(normalized_query, original_query)

    normalized_query = [term for sublist in normalized_query for term in sublist]
    
    """ Running the queries against the pre-loaded index. """
    output_dict = retriever.retrieve_docs(topics, normalized_query, 5)

    response = {
        "Response": output_dict,
        "time_taken": str(time.time() - start_time),
    }

    """ Dumping the results to a JSON file. """
    with open(backup_res_output_file, 'w') as fp:
        json.dump(response, fp, sort_keys=True, indent=4)

    return flask.jsonify(response)

if __name__ == "__main__":
    retriever = Retriever()
    app.run(port=9999, host='0.0.0.0')