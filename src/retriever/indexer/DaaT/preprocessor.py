'''
@author: Sougata Saha
Institute: University at Buffalo
'''

import collections
import nltk
from nltk.stem import PorterStemmer
import re
from nltk.corpus import stopwords
from nltk.tokenize import WhitespaceTokenizer
nltk.download('stopwords')
from tqdm import tqdm
import threading

from concurrent.futures import ThreadPoolExecutor, as_completed

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


if __name__ == "__main__":
    preprocessor = Preprocessor()
    # using file path for query
    queries, non_normalized_queries = preprocessor.preprocess_query(file_path='../project2/data/queries.txt')
    print(queries, non_normalized_queries)

    # using file path for corpus
    postings_dict, total_docs = preprocessor.preprocess(file_path='../project2/data/input_corpus.txt')
    print(postings_dict['plea'], total_docs)

    # Not using file path
    queries, non_normalized_queries = preprocessor.preprocess_query(query=["plea bargaining", "plea agreement"])
    # print(queries)

    # print()

    print(preprocessor.preprocess_query(query=['the novel coronavirus']))


    



