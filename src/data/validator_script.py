import json
from collections import Counter
import json
import time
import threading
from tqdm import tqdm

def analyze_json_file(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        
        topic_stats = {}
        total_docs = 0
        
        for topic, documents in data.items():
            doc_count = len(documents)
            titles = [doc['title'] for doc in documents]
            topic_stats[topic] = {
                'count': doc_count,
                'titles': titles
            }
            total_docs += doc_count
        
        print(f"Total number of documents: {total_docs}")
        print("\nDocuments per topic:")
        # for topic, stats in topic_stats.items():
        #     print(f"\n{topic}: {stats['count']} documents")
        #     print("Titles:")
        #     for title in stats['titles']:
        #         print(f"- {title}")
        
        return True, topic_stats
    except json.JSONDecodeError:
        print("Invalid JSON file")
        return False, None
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False, None




def batch_results_to_json(save_file_name, file_path):
    restruct_dict = {}
    try:
        with open(file_path, 'r') as file:
            batch_results = json.load(file)
        
        topic_stats = {}
        total_docs = 0
        
        for index, batch_item in enumerate(batch_results):
            title = batch_item['topic']
            docs = batch_item['documents']
            restruct_dict[title] = docs

        with open(save_file_name, 'w') as f:
            json.dump(restruct_dict, f)
    
        return restruct_dict
    except json.JSONDecodeError:
        print("Invalid JSON file")
        return False, None
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False, None
    

# Stop words removal amnd processing 

stopwords = [
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours",
    "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers",
    "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves",
    "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are",
    "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does",
    "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until",
    "while", "of", "at", "by", "for", "with", "about", "against", "between", "into",
    "through", "during", "before", "after", "above", "below", "to", "from", "up", "down",
    "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here",
    "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so",
    "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now"
]

def process_documents(documents, threads_count=30):
    n_threads = min(threads_count, len(documents))
    batch_sz = max(1, len(documents) // n_threads)
    threads = []
    filtered_docs = []

    with tqdm(total=len(documents), desc="Processing documents", leave=False) as pbar:
        for i in range(n_threads):
            batch_start = i * batch_sz
            batch_end = batch_start + batch_sz if i < n_threads - 1 else len(documents)

            thread = threading.Thread(target=stopword_filter, args=(documents[batch_start:batch_end], filtered_docs, pbar))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    return filtered_docs

def stopword_filter(docs, filtered_docs, pbar):
    for doc in docs:
        word_list = doc['summary'].split()
        filtered_words = [w for w in word_list if w.lower() not in stopwords]
        filtered_content = " ".join(filtered_words)

        filtered_doc = doc.copy()
        filtered_doc['summary'] = filtered_content
        filtered_docs.append(filtered_doc)
        pbar.update(1)

def process_each_topic(all_docs_temp):
    s_time = time.time()
    total_docs = sum(len(docs) for docs in all_docs_temp.values())
    
    with tqdm(total=total_docs, desc="Processing topics") as pbar:
        for topic, docs in all_docs_temp.items():
            filtered_docs = process_documents(docs)
            all_docs_temp[topic] = filtered_docs
            pbar.update(len(docs))
    
    e_time = time.time()
    return all_docs_temp, (e_time - s_time)


if __name__ == '__main__':

    file_path = 'Food_Economy_Travel_docs.json'

    is_valid, topic_stats = analyze_json_file(file_path)
    # print(f"\nIs the JSON file valid? {topic_stats}")
    for c, t in topic_stats.items():
        print(f"{c} : {t['count']}")
        
    # Check through docs on Economy and Food to get titles that are present in my set but not on the new ones

    economy_docs = topic_stats['Economy']['titles']
    food_docs = topic_stats['Food']['titles']

    economy_set = set(economy_docs)
    food_set = set(food_docs)


    final_results = batch_results_to_json('save_file_4_topics_docs.json','checkpoint_until_Food_4_topics_results.json')
    # print("FINAL RESULTS OF MERGED ITEMS", final_results)

    file_path2 = 'save_file_4_topics_docs.json'
    is_valid, topic_stats2 = analyze_json_file(file_path2)
    # print(f"\nIs the JSON file valid? {topic_stats}")
    for c, t in topic_stats2.items():
        print(f"{c} : {t['count']}")
        
    # Check through docs on Economy and Food to get titles that are present in my set but not on the new ones

    # economy_docs = topic_stats['Economy']['titles']
    # economy_docs_2 = topic_stats2['Economy']['titles']

    # # economy_set = set(economy_docs)
    # economy_set_2 = set(economy_docs_2)

    # print('Items in A not in B set',food_set_2.difference(food_set))

    file_path3 = 'Travel_and_Entertainment_docs.json'
    is_valid, topic_stats3 = analyze_json_file(file_path3)
    # print(f"\nIs the JSON file valid? {topic_stats}")
    for c, t in topic_stats3.items():
        print(f"{c} : {t['count']}")
        
    # Check through docs on Economy and Food to get titles that are present in my set but not on the new ones

    economy_docs = topic_stats3['Travel']['titles']
    food_docs = topic_stats3['Entertainment']['titles']

    economy_set = set(economy_docs)
    food_set = set(food_docs)

    file_path = 'All_topics_combined_final.json'
    is_valid, topic_stats = analyze_json_file(file_path)
    # print(f"\nIs the JSON file valid? {topic_stats}")
    for c, t in topic_stats.items():
        print(f"{c} : {t['count']}")


    final_file = 'All_topics_combined_final.json'

    # Load the JSON file
    with open(final_file, 'r') as file:
        all_docs_temp = json.load(file)

    # Process the documents
    processed_docs, processing_time = process_each_topic(all_docs_temp)

    # Save the processed documents
    with open('processed_documents_final.json', 'w') as file:
        json.dump(processed_docs, file, indent=4)

    print(f"Processing completed in {processing_time:.2f} seconds")