import time
from flask import Flask, request, jsonify
import hashlib
import json
from retriever import Retriever
from flask_cors import CORS

app = Flask(__name__)

CORS(app,  supports_credentials=True)

retriever = Retriever()
backup_res_output_file = 'retriever_results.json'

@app.route("/retriever_docs", methods=['POST', 'OPTIONS'])
def execute_query():
    if request.method == 'OPTIONS':
        # Return a 204 No Content response with the necessary CORS headers
        response = app.make_response('')
        #response = Flask.make_response()
        response.headers['Access-Control-Allow-Origin'] = 'http://34.68.123.1:3000'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response, 204
    start_time = time.time()
    K=5

    print(request.json)
    query = request.json.get("query")
    topics = request.json.get("topics", [])

    if not query or not topics:
        return jsonify({"error": "Missing query or topics"}), 400

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
    #retriever = Retriever()
    app.run(port=9999, host='0.0.0.0')