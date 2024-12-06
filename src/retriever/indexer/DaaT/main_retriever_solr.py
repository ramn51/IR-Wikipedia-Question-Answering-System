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
from nltk.tokenize import WhitespaceTokenizer
nltk.download('stopwords')
from tqdm import tqdm
import threading

nltk.download()
nltk.download('stopwords')

# Query Preprocessing
class Preprocessor:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.ps = PorterStemmer()

    def get_doc_id(self, doc):
        """ Splits each line of the document, into doc_id & text.
            Already implemented"""
        arr = doc.split("\t")
        return int(arr[0]), arr[1]
    
    @staticmethod
    def get_token_freq(token, tokens):
        token_counter = collections.Counter(tokens)
        return token_counter[token]

    def tokenizer(self, text):
        """ Implement logic to pre-process & tokenize document text.
            Write the code in such a way that it can be re-used for processing the user's query.
            To be implemented."""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)

        # White Space tokenization
        text = text.strip()
        tokens = text.split()

        invalid_token_status = False

        # Count white space between words
        if any(word == '' or word == ' ' for word in tokens):
            invalid_token_status = True
            raise ValueError("Invalid token found (space or a blank token)")
        
        # Do not include stop words
        tokens = [word for word in tokens if word not in self.stop_words]

        # Performing Porters stemming
        stemmer = PorterStemmer()
        tokens = [stemmer.stem(word) for word in tokens]

        return tokens
    
    def read_file_content(self, file_path):
        try:
            with open(file_path, 'r') as file:
                data = file.read()
            return data
        except FileNotFoundError:
            print(f"File not found: {file_path}")
        except Exception as e:
            print(f"An error occurred: {e}")

    
    def preprocess_query(self, file_path=None, query=None):
        if file_path and query:
            raise ValueError("Provide either file_path or query, not both")
    
        if file_path:
            content = self.read_file_content(file_path=file_path)
        elif query:
            content = '\n'.join(query)
        
        queries = []
        original_queries = []
        if content:
            split_content = content.split("\n")
            
            for index, line in enumerate(split_content):
                if line.strip():
                    queries.append(self.tokenizer(line))
                    original_queries.append(line)
                
        return queries, original_queries

    def preprocess_2(self, file_path):
        preprocessed_data = []

        try:
            with open(file_path, 'r') as fp:
                total_lines = sum(1 for _ in fp)

            def process_line(line):
                doc_id, text = self.get_doc_id(line)
                tokens = self.tokenizer(text)
                return doc_id, tokens
            
            with open(file_path, 'r') as fp:
                with ThreadPoolExecutor(max_workers=4) as executor:
                    futures = [executor.submit(process_line, line) for line in fp]
                    for future in tqdm(as_completed(futures), total=total_lines, desc="Preprocessing", colour='green'):
                        preprocessed_data.append(future.result())

            # Sequential processing code
            # with open(file_path, 'r') as fp:
            #     for line in tqdm(fp, total=total_lines, desc="Preprocessing", colour='green'):
            #         doc_id, text = self.get_doc_id(line)
            #         tokens = self.tokenizer(text)
            #         preprocessed_data.append((doc_id, tokens))
        except FileNotFoundError:
            print(f"File not found: {file_path}")
        except Exception as e:
            print(f"An error occurred: {e}")

        return preprocessed_data
    

def query_normalizer(queries, preprocessor):
    original_queries = queries
    queries = [[element] for element in queries]
    
    print("Original queries::", queries)
    query_terms = []
    for query in queries:
        normalized_query, original_query = preprocessor.preprocess_query(query=query)
        print(normalized_query, original_query)
        query_terms.append((normalized_query, original_query))

    normalized_queries, original_queries = zip(*query_terms)

    # Add the parts of the query to the list of queries (eg: [[], ['novel'], ['coronavirus']]) => [['novel coronavirus']]
    normalized_queries = [sum(sublist, []) for sublist in normalized_queries]

    print('Queries stuff::', normalized_queries, original_queries)

    return normalized_queries, original_queries

preprocessor = Preprocessor()
query_normalizer(["what is coronavirus"], preprocessor)

def retrieve_docs(topics, query_string, k):
    all_res = []
    for topic in topics:
        all_res.append(retrieve_docs_single_topic(topic, query_string, k))

    # Flatten the all_res into one single list (it is multi-dim initially)
    return sum(all_res, [])

def retrieve_docs_single_topic(topic, query_string, k):
    solr_url_ = f'http://{VM_IP}:8983/solr/'
    connection_ = pysolr.Solr(solr_url_ + CORE_NAME, always_commit=True, timeout=5000000)

    query = {
        'q': query_string,
        'fq': f'topic:{topic}',  # Topic filter
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

topic = "Travel"
query_string  = "What is cryptocurrency"
preprocessor = Preprocessor()
norm_query, orig_query = query_normalizer([query_string], preprocessor)

res_list = retrieve_docs("Politics", norm_query[0][0], 5)
print(res_list)