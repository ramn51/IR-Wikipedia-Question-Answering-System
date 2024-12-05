#!/usr/bin/env python
# coding: utf-8
import pysolr
import json

VM_IP = '34.130.33.83'
CORE_NAME = "IRF24P3"


# Import NLTK
import collections
import nltk
from nltk.stem import PorterStemmer
import re
from nltk.corpus import stopwords
from nltk.data import find
from nltk.tokenize import WhitespaceTokenizer

from tqdm import tqdm
import threading
from preprocessor import Preprocessor

def download_nltk_resource(resource):
    try:
        # check if resource already downloaded else go for downloading
        find(f'corpora/{resource}')
    except LookupError:
        print(f'Downloading {resource}...')
        nltk.download(resource)
        print(f'{resource} downloaded successfully')
    else:
        print(f'{resource} already downloaded')


download_nltk_resource('stopwords')

class Retriever():
    def __init__(self):
        self.preprocessor = Preprocessor()
        self.solr_url_ = f'http://{VM_IP}:8983/solr/'
    
    def query_normalizer(self, queries):
        original_queries = queries
        queries = [[element] for element in queries]
        
        print("Original queries::", queries)
        query_terms = []
        for query in queries:
            normalized_query, original_query = self.preprocessor.preprocess_query(query=query)
            print(normalized_query, original_query)
            query_terms.append((normalized_query, original_query))
    
        normalized_queries, original_queries = zip(*query_terms)
    
        # Add the parts of the query to the list of queries (eg: [[], ['novel'], ['coronavirus']]) => [['novel coronavirus']]
        normalized_queries = [sum(sublist, []) for sublist in normalized_queries]
    
        print('Queries stuff::', normalized_queries, original_queries)
    
        return normalized_queries, original_queries

    def retrieve_docs(self, topics, query_string, k):
        all_res = []
        for topic in topics:
            all_res.append(self.retrieve_docs_single_topic(topic, query_string, k))
    
        # Flatten the all_res into one single list (it is multi-dim initially)
        final_res = sum(all_res, [])
        response_dict = {"results": final_res, "total_results": len(final_res) }
        return response_dict
    
    def retrieve_docs_single_topic(self, topic, query_string, k):
        connection_ = pysolr.Solr(self.solr_url_ + CORE_NAME, always_commit=True, timeout=5000000)

        print('QUERY STRING inside Retrieve_docs_single_topic',query_string)
        # if multiple terms then we need to OR them and give it (AND will be very strict search)
        if isinstance(query_string, list):
            query_string = ' OR '.join(query_string)
    
        print(query_string)
    
        query = {
            'q': query_string,
            'fq': f'topic:{topic}',
            'df': 'summary',
            'rows': k,
            'fl': '*,score'
        }
        
        results = connection_.search(**query)
        print(f"Total documents matching query: {len(results)}")
        
        res_list = []
        res_title = set()
        for result in results:
            res_dict = {
                "title": result.get("title"),
                "summary": result.get("summary"),
                "topic": result.get("topic"),
                "score": result.get("score")
            }
            if res_dict["title"] not in res_title:
                res_title.add(res_dict["title"])
                res_list.append(res_dict)
    
        return res_list


if __name__ == '__main__':
    retriever = Retriever()
    

    topic = "Travel"
    query_string  = "What is cryptocurrency coronavirus"
    norm_query, orig_query = retriever.query_normalizer([query_string])

    # Make the query into one single list and flatten since it is 2-D.
    norm_query = sum(norm_query, [])
    res_list = retriever.retrieve_docs_single_topic("Politics", norm_query, 5)
    len(res_list)
    print(res_list)

    query_string  = "the novel coronavirus"
    preprocessor = Preprocessor()
    norm_query, orig_query = retriever.query_normalizer([query_string])
    
    # Make the query into one single list and flatten since it is 2-D.
    norm_query = sum(norm_query, [])
    
    res_list = retriever.retrieve_docs(["Politics", "Health"], norm_query, 5)
    print(res_list)

