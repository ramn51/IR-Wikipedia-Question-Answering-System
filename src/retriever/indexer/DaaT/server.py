import flask
import time
from flask import Flask, request
import hashlib
import json
from boolean_retrieval_runner import BooleanRetrievalRunner


app = Flask(__name__)
# output_location = 'output.json'
username = 'anantha2'

@app.route("/execute_query", methods=['POST'])
def execute_query():
    """ This function handles the POST request to your endpoint.
        Do NOT change it."""
    start_time = time.time()

    queries = request.json["queries"]

    original_queries = queries
    queries = [[element] for element in queries]
    
    print("Original queries::", queries)
    query_terms = []
    for query in queries:
        normalized_query, original_query = boolean_retrieval_runner.preprocessor.preprocess_query(query=query)
        print(normalized_query, original_query)
        query_terms.append((normalized_query, original_query))

    normalized_queries, original_queries = zip(*query_terms)

    # Add the parts of the query to the list of queries (eg: [[], ['novel'], ['coronavirus']]) => [['novel coronavirus']]
    normalized_queries = [sum(sublist, []) for sublist in normalized_queries]

    print('Queries stuff::', normalized_queries, original_queries)


    output_location = 'output_flask.json'

    """ Running the queries against the pre-loaded index. """
    output_dict = boolean_retrieval_runner.run_queries(normalized_queries, original_queries)

   
    username_hash = hashlib.md5(username.encode()).hexdigest()

    response = {
        "Response": output_dict,
        "time_taken": str(time.time() - start_time),
        "username_hash": username_hash
    }

    """ Dumping the results to a JSON file. """
    with open(output_location, 'w') as fp:
        json.dump(response, fp, sort_keys=True, indent=4)

    return flask.jsonify(response)

if __name__ == "__main__":
    boolean_retrieval_runner = BooleanRetrievalRunner()

    corpus_path = 'input_corpus.txt'
    boolean_retrieval_runner.run_indexer(corpus_path)

    app.run(port=9999)