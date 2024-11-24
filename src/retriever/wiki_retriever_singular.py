import wikipedia
import re
import random
import time
from tqdm import tqdm
from collections import Counter
import concurrent.futures
from requests.exceptions import RequestException
from json.decoder import JSONDecodeError
import json

topics_and_terms = [
    ("Health", ["Heart disease", "Cancer", "Diabetes", "COVID-19", "Depression", "Anxiety disorders", 
                "Obesity", "Alzheimer's disease", "Autoimmune disorders", "Infectious diseases", 
                "Maternal health", "Mental health stigma"]),
     ("Sports", [
        "Major sporting events", "Sports analytics", "Player statistics", 
        "Team performance", "Sports technology", "Cricket", "Sports medicine", 
        "Esports", "Football", "Olympic Games", "Athlete mental health", 
        "Sports betting", "Women in sports", "Youth sports development"
    ])
]

# Backup Terms for the topic that failed to fetch min of 520 docs
topic_terms_backup = [
    ("Health", [
        "Telemedicine", "Preventive care", "Healthcare technology",
        "Wellness programs", "Public health initiatives", "Chronic disease management",
        "Health equity", "Personalized medicine", "Digital health solutions", "Global health challenges"
    ])
]

MAX_DOCS = 5100
MAX_WORKERS = 10
TOPICS_BATCH_SIZE = 2 # Dont change this
MIN_SUMMARY_LEN = 300

class WikiRetriever:
    def __init__(self, topic, relevant_terms, total_docs=520, wiki_search_size=500, max_workers=10, visited_pages=None):
        # We use this when we want to do a rerun on a particular set of docs to ensure there is no similarity
        self.visited = visited_pages if visited_pages is not None else set()
        self.search_size = wiki_search_size
        self.relevant_terms= [i.lower() for i in relevant_terms]
        self.total_docs = total_docs
        self.retrieved_docs = 0
        self.document_topic = topic
        self.search_terms = self.relevant_terms
        self.progress_bar = None
        self.max_workers = max_workers

    
    def reset(self):
        self.visited.clear()

    @staticmethod
    def is_relevant(page, key_words, summary):
        words_re = re.compile("|".join(key_words))
        word_matched = False
        match_count = 0
        normalized_summary = WikiRetriever.filter_for_alnum(summary)
        if words_re.findall(normalized_summary) and (len(normalized_summary) > 200):
            return True
            # word_matched = True
            # match_count = len(words_re.findall(summary))
            # if (match_count >= 2 or word_matched):
            #     return True
        else:
            return False

    @staticmethod
    def filter_for_alnum(summary):
        return re.sub(r'[^a-zA-Z0-9]', ' ', summary.lower())
        # return ''.join(char.lower() for char in text if char.isalnum() or char.isspace())
        

    def handle_disambiguous(self, search_options, depth=0):
        max_depth = 3
        if depth >= max_depth:
            return None
        else:
            random_title = random.choice(search_options)
            try:
                random_page = wikipedia.page(random_title, auto_suggest=False)
                return random_page
            except wikipedia.DisambiguationError as e:
                return self.handle_disambiguous(e.options, depth+1)
            except wikipedia.PageError:
                return None

    
    # Get the results for each of the searches, handle ambiguous searches
    def make_result_dict(self, content):
        if content is not None:
            content_dict = {'summary': '', 'url': '', 'title': '', 'revision_id': 0 }
            content_dict['summary'] = self.filter_for_alnum(content.summary)
            content_dict['url'] = content.url
            content_dict['title'] = content.title
            content_dict['revision_id'] = content.revision_id
            content_dict['topic'] = self.document_topic
    
            return content_dict
        return {}

    def get_page_content(self, title, search_from_link=False):
        res = []
        check_thru_link = False

        if title in self.visited:
            return None, [], False
        
        try:
            content = wikipedia.page(title, auto_suggest=False)
            if self.is_relevant(content, self.relevant_terms, content.summary):
                # print('Relevant content present in:', content.title)
                res.append(self.make_result_dict(content))
                self.visited.add(content.title)
                return content, res, check_thru_link
            else:
                check_thru_link = True
                return content, res, check_thru_link
        except wikipedia.DisambiguationError as e:
            random_page = self.handle_disambiguous(e.options)
            res = self.make_result_dict(random_page)
        except wikipedia.exceptions.PageError:
            # Handle page not found
            print(f"Page not found for {title}")
    
        return None, [], check_thru_link


    def search_thru_links(self, page, max_links=20, remaining_docs=None):
        if not page:
            return []
            
        links = page.links
        if self.document_topic == 'Travel':
            max_links = 500
            links = links[:max_links]
        else:
            links = links[:max_links]
        link_results = []

        # print(links)
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_link = {executor.submit(self.process_link_with_retry, link): link for link in links}
            for future in concurrent.futures.as_completed(future_to_link):
                link = future_to_link[future]
                try:
                    link_result = future.result()
                    if link_result:
                        link_results.append(link_result)
                        if remaining_docs is not None:
                            remaining_docs -= 1
                            if remaining_docs <= 0:
                                # Cancel all pending futures
                                for f in future_to_link:
                                    f.cancel()
                                break
                except Exception as exc:
                    print(f"{link} generated an exception: {exc}")

        return link_results

    def process_link(self, link):
        if link in self.visited:
            return None
        try:
            page = wikipedia.page(link, auto_suggest=False)
            self.visited.add(link)
            if self.is_relevant(page, self.relevant_terms, page.summary):
                return self.make_result_dict(page)
        except (wikipedia.DisambiguationError, wikipedia.PageError, wikipedia.exceptions.HTTPTimeoutError):
            pass
        
        return None    

    def process_link_with_retry(self, link, max_retries=3, initial_delay=1):
        if link in self.visited:
            return None
    
        for attempt in range(max_retries):
            try:
                page = wikipedia.page(link, auto_suggest=False)
                self.visited.add(link)
                if self.is_relevant(page, self.relevant_terms, page.summary):
                    return self.make_result_dict(page)
                return None
            except (wikipedia.DisambiguationError, wikipedia.PageError):
                return None
            except (wikipedia.exceptions.HTTPTimeoutError, RequestException, JSONDecodeError) as e:
                print('Rate limited')
                if attempt == max_retries - 1:
                    print(f"Failed to process link {link} after {max_retries} attempts: {str(e)}")
                    return None
                wait_time = initial_delay * (2 ** attempt)
                print(f"Attempt {attempt + 1} failed for {link}: {str(e)}. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
    
        return None
        
    
    def get_page_details(self, search_title, total_docs = 100 , search_thru_link = False ):
        # print(search_title, 'GT_PAGE_DETAILS')
        link_res = []
        doc_count = 0
        page, res, check_link = self.get_page_content(search_title, self.relevant_terms)
        # if check_link:
        #     link_res = retrieve_res_thru_links(page, relevant_terms, link_count = 5)
    
        return page, res

    # To handle rate limiting when we run more worker threads
    def get_page_details_with_retry(self, title, max_retries=3, initial_delay=1):
        for attempt in range(max_retries):
            try:
                return self.get_page_details(title)
            except (RequestException, JSONDecodeError) as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(initial_delay * (2 ** attempt))

    
    def wiki_doc_retriever(self):
        results = []
        docs_dict = {'title': '', 'documents': 0}
    
        print(f"Starting retrieval for {self.document_topic}")
        self.progress_bar = tqdm(total=self.total_docs, desc=f"Retrieving docs for {self.document_topic}", leave=True)
        
        all_search_results = []
        for search_term in self.search_terms:
            search_results = wikipedia.search(search_term, results=self.search_size)
            all_search_results.extend(search_results)
            # if len(all_search_results) >= self.total_docs * 3:
                # break

        print(self.search_terms)
        print('All searches len: ',len(all_search_results))
        all_search_results = list(set(all_search_results))
        print('All searches len after set: ',len(all_search_results))

        processed_count = 0                
        while len(results) < self.total_docs and processed_count < len(all_search_results):
            batch = all_search_results[processed_count:processed_count + self.max_workers * 2]
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_title = {executor.submit(self.get_page_details_with_retry, title): title for title in batch}
                for future in concurrent.futures.as_completed(future_to_title):
                    title = future_to_title[future]
                    try:
                        page, page_res = future.result()
                        if page_res:  # Only add if the result is not empty
                            results.extend(page_res)
                            self.progress_bar.update(len(page_res))
                            if len(results) >= self.total_docs:
                                break
                    except Exception as exc:
                        print(f"{title} generated an exception: {exc}")
            
            processed_count += len(batch)
            time.sleep(1) # sleep between the batches for 1 second
            if len(results) >= self.total_docs:
                break

        # Search for additional docs if we cant retrieve min no.of docs through links of each search result
        if len(results) < self.total_docs:
            print(f"Found only {len(results)} docs, going through the links further")
            remaining_docs = (self.total_docs - len(results))
            reduced_workers = max(1, self.max_workers // 2)
            # First executor: Get pages
            with concurrent.futures.ThreadPoolExecutor(max_workers=reduced_workers) as page_executor:
                future_to_title = {page_executor.submit(self.get_page_details_with_retry, title): title 
                                  for title in all_search_results[:remaining_docs]}
                
                pages_to_search = []
                for future in concurrent.futures.as_completed(future_to_title):
                    title = future_to_title[future]
                    try:
                        page, page_res = future.result()
                        if page:
                            pages_to_search.append(page)
                    except Exception as exc:
                        print(f"{title} generated an exception: {exc}")
            
            # Second executor: Search through links
            for page in pages_to_search:
                try:
                    link_results = self.search_thru_links(page, remaining_docs)
                    results.extend(link_results)
                    self.progress_bar.update(len(link_results))
                    if len(results) >= self.total_docs:
                        break
                    time.sleep(1)
                except Exception as exc:
                    print(f"{page} generated an exception: {exc}")
                    

        docs_dict['title'] = self.document_topic
        docs_dict['documents'] = len(results)
        print("DOC RETRIEVER: VISITED PAGES LENGTH", len(self.visited))
        self.progress_bar.close()
        return results, docs_dict, self.visited


def checkpoint_results(all_results, visited_pages_list, checkpoint_file_name):
    with open(checkpoint_file_name, 'w') as f:
        json.dump(all_results, f)

    with open(f'visited_pages_{checkpoint_file_name}', 'w') as f:
        json.dump(visited_pages_list, f)

def main_runner(topics_terms_batch, run_specific_topic=False, **kwargs):
    print('TOPICS TERMS', topics_terms_batch)
    all_results = []
    start_time = time.time()

    if not run_specific_topic:
        overall_pbar = tqdm(total=len(topics_terms_batch), desc="Overall progress", position=0, leave=True)
    else:
        remaining_docs = kwargs['rem_docs']
        overall_pbar = tqdm(total=remaining_docs, desc="Remaining Docs Fetch Overall progress", position=0, leave=True)
    
    gap_seconds = 60
    batch_sz = TOPICS_BATCH_SIZE

    # Maintaining visited sets for reruns for particular topics
    visited_pages_list = []
   
    # if there is no specific topic to be run, then do the batch processing
    # else, take the remaining docs to be processed, visited set from the batch, changed relevant terms
    if not run_specific_topic:
        for i in range(0, len(topics_terms_batch) - 1, batch_sz):
            batch = topics_terms_batch[i: i + batch_sz]
            for topic, terms in batch:
                wiki_ret = WikiRetriever(topic, terms, max_workers=MAX_WORKERS, total_docs=MAX_DOCS)
                res, docs_dict, visited_pages = wiki_ret.wiki_doc_retriever()

                res_dict = {
                    'topic': docs_dict['title'],
                    'documents': res
                }

                visited_pages_dict = {
                    'topic': docs_dict['title'], 
                    'visited_page_set': list(visited_pages)
                }

                checkpoint_results(res_dict, visited_pages_list, f'checkpoint_{topic}_results.json')
                all_results.append(res_dict)
                visited_pages_list.append(visited_pages_dict)

                print('VISITED_PAGES_LIST::::LEN::', len(visited_pages_list))
                print('LAST_ENTRY::::LEN::', len(visited_pages_list[-1]['visited_page_set']))
                
                # Reset the visited pages for the next iteration to start fresh
                wiki_ret.reset()
                overall_pbar.update(1)
                print(docs_dict)
        
            # check if the batch and iteration sum is less than the batch size taken
            # then, add a gap between the batches.
            if i + batch_sz < len(topics_and_terms) - 1:
                print(f'Wait for some time {gap_seconds} seconds')
                time.sleep(gap_seconds)
                
        overall_pbar.close()
    
        end_time = time.time()
        
    else:
        topic_name = kwargs['topic_name']
        remaining_docs = kwargs['rem_docs']
        print(f"Retrieving for the specific topic: {topic_name} for these many docs {remaining_docs}")
        
        visited_pages = kwargs['visited_pages']
        # The backup relevant terms that are not the previous ones given for the search
        topic_terms = kwargs['topic_terms']

        topic, terms = topic_terms
        print(topic_terms)
        
        # Retrieve docs for the remaining count for the topic
        wiki_ret = WikiRetriever(topic=topic_name, relevant_terms=terms, total_docs=remaining_docs, max_workers=20, visited_pages=visited_pages)
        res, docs_dict, visited_pages_info = wiki_ret.wiki_doc_retriever()

        res_dict = { 'topic': docs_dict['title'], 'documents': res }
        visited_pages_dict = {'topic': docs_dict['title'], 'visited_page_set': list(visited_pages_info)}

        checkpoint_results(res_dict, visited_pages_list, f'checkpoint_{topic}_results.json')
        
        # Return the single result
        all_results.append(res_dict)
        visited_pages_list.append(visited_pages_dict)
        
        # Reset the visited pages for the next iteration to start fresh
        wiki_ret.reset()
        overall_pbar.update(1)
        print(docs_dict)

        overall_pbar.close()
        end_time = time.time()
        


    print("Synchy total trime", end_time - start_time)
    print('Done Retrieving', len(all_results)) 
    
    return all_results, visited_pages_list, (end_time - start_time)


# Get results for first 6 topics
batch_sz = TOPICS_BATCH_SIZE
topics_terms_batch_1 = topics_and_terms[:batch_sz]
# topics_terms_batch_2 = topics_and_terms[batch_sz:]

batch_1_results, visited_pages_dict_list ,running_time = main_runner(topics_terms_batch_1)

def validate_docs_results(batch_results, visited_pages_dict_list):
    insuff_docs = []
    min_docs = MAX_DOCS
    for i in batch_results:
        print(i['topic'], len(i['documents']))
        if len(i['documents']) < MAX_DOCS:
            #  , 'visited_pages': visited_pages_dict_list[]
            visited_pages_dict = [visited_item['visited_page_set'] for visited_item in visited_pages_dict_list if visited_item['topic'] == i['topic'] ]
            insuff_docs.append({'topic': i['topic'], 'docs_count': len(i['documents']), 'visited_pages': visited_pages_dict})
   
    return insuff_docs if insuff_docs else None

rem_docs_b1 = validate_docs_results(batch_1_results, visited_pages_dict_list)
if not rem_docs_b1:
    print("No pending docs to retrieve, its all fine for Batch 1")
else:
    print('Fetched this much docs remaining', len(rem_docs_b1))

def retrieve_rem_docs(batch_results, visited_pages_dict_list, topic_terms_backup):
    docs_retrieve_rem = validate_docs_results(batch_results, visited_pages_dict_list)
    all_results_rem_docs = []
    max_docs = MAX_DOCS
    if docs_retrieve_rem:                                   
        for i in docs_retrieve_rem:
            # Get the visited pages for the docs
            # Get the total retrived docs and calculate the remaining_docs
            # Pass the backup topcs
            topic_name = i['topic']
            retrieved_docs = i['docs_count']
            visited_pages = set(i['visited_pages'][0])
            remaining_docs = max_docs - retrieved_docs
            remaining_docs_results, visited_pages_dict_list_rem, total_time = main_runner(topics_terms_batch_1, run_specific_topic=True, 
                                                                                        topic_name=topic_name, rem_docs=remaining_docs, visited_pages=visited_pages, 
                                                                                        topic_terms=topic_terms_backup)
            all_results_rem_docs.append(remaining_docs_results)
        return all_results_rem_docs
    else:
        return []
    
# Retrieve the remaining docs for the topics
rem_doc_results = retrieve_rem_docs(batch_1_results, visited_pages_dict_list, topic_terms_backup)

for i in batch_1_results:
    print(i['topic'], len(i['documents']))

batch_1_cp = batch_1_results.copy()

# validate if we have all the topics with 520 documents or more than 500
all_docs = []
# all_docs.extend(batch_1_results)

# Merge the arrays with remaining docs and the rest of the docs
# This needs to be done else for same topic two different arrays will be maintained
# Finally there needs to be 10 topics len(all_docs) should be 10
def merge_all_results(batch_results, rem_doc_results):
    merged = batch_results.copy()
    for rem_doc in rem_doc_results:
        for item in rem_doc:
            existing = next((i for i in merged if i['topic'] == item['topic']), None)
            if existing:
                existing_titles = {doc['title'] for doc in existing['documents']}
                for doc in item['documents']:
                    if doc['title'] not in existing_titles:
                        existing['documents'].append(doc)
                        existing_titles.add(doc['title'])
            else:
                merged.append(item)
    return merged

# print(rem_doc_results)

# There is no remaining docs for batch1 we add to the all_docs list
all_docs.extend(batch_1_results)


batch_1_all_results = merge_all_results(batch_1_results, rem_doc_results)

# Extend all_docs with the merged results
all_docs.extend(batch_1_all_results)

print(len(all_docs))

for i in all_docs:
    print(i['topic'], len(i['documents']))

# Check if each of the topics are having atleast 5000 docs
is_min_5000 = all(len(i['documents']) > MAX_DOCS for i in all_docs)

# Validate if all 5000 documents under each topic is unique
# We check if the duplicate count is not exceeding 40 (20 will be discarded) and it will still be within 500 docs
# Else we need to do retrieval using new topics and redo for the specific topic.
def find_and_replace_non_unique_docs(all_docs):
    for topic in all_docs:
        topic_name = topic['topic']
        topic_docs = topic['documents']
        titles = [doc['title'] for doc in topic_docs]
        
        title_counts = Counter(titles)

        duplicate_titles = [title for title, count in title_counts.items() if count > 1]
        
        if duplicate_titles:
            print(f"\nTopic: {topic_name}")
            print("Duplicate titles:")
            for title in duplicate_titles:
                print(f"  - '{title}' appears {title_counts[title]} times")
            
            print("Removing the duplicate documents")
            visited_titles = set()
            unique_docs = []
            for doc in topic_docs:
                if doc['title'] not in visited_titles:
                    unique_docs.append(doc)
                    visited_titles.add(doc['title'])
            topic['documents'] = unique_docs
            print(f"  Removed {len(topic_docs) - len(unique_docs)} duplicate(s)")
        else:
            print(f"\nTopic: {topic_name} - All titles are unique")


find_and_replace_non_unique_docs(all_docs)

is_topic_docs_unique = False
unique_docs_bool = []
for topic in all_docs:
    topic_docs = topic['documents']
    titles = [doc['title'] for doc in topic_docs]
    unique_docs_bool.append(len(titles) == len(list(set(titles))))

is_topic_docs_unique = all(is_unique for is_unique in unique_docs_bool)

def validate_doc_len(all_docs):
    unique_docs_bool = []
    for topic in all_docs:
        topic_docs = topic['documents']
        summary_lengths = [len(doc['summary']) for doc in topic_docs]
        unique_docs_bool.append(all(summ_len >= 200 for summ_len in summary_lengths))

    return all(is_unique for is_unique in unique_docs_bool)

is_min_doc_len_valid = validate_doc_len(all_docs)

print("Is each topic having 500 documents :", is_min_5000)
print("Is each topic having unique Titles:", is_topic_docs_unique)
print("Is each topic having summary length at least with 200 characters:", is_topic_docs_unique)

if not is_topic_docs_unique:
    print("There are duplicate documents, please re-run the retrieval process")

# ## Preprocessing to remove Stop words across all docs

# %%
import threading
# Data Preprocessing with removal of stop words
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


def stopword_filter(docs, filtered_docs):
    for doc in docs:
        word_list = doc['summary'].split()
        filtered_words = [w for w in word_list if w not in stopwords]
        filtered_content = " ".join(filtered_words)

        filtered_doc = doc.copy()
        filtered_doc['summary'] = filtered_content
        filtered_docs.append(filtered_doc)

def process_documents(documents, threads_count=10):
    n_threads = min(threads_count, len(documents))
    batch_sz = max(1, len(documents) // n_threads)
    threads = []
    filtered_docs = []

    for i in range(n_threads):
        batch_start = i * batch_sz
        if i < n_threads - 1: 
            batch_end = batch_start + batch_sz
        else:
            batch_end = len(documents)

        thread = threading.Thread(target=stopword_filter, args=(documents[batch_start : batch_end], filtered_docs))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return filtered_docs

def process_each_topic(all_docs_temp):
    s_time = time.time()
    for topic_doc in all_docs_temp:
        topic_name = topic_doc['topic']
        docs = topic_doc['documents']
        filtered_docs = process_documents(docs)
    
        # Replace the exisitng docs fro the topic with the nw filtered ones
        topic_doc['documents'] = filtered_docs
    e_time = time.time()
    return all_docs_temp, (e_time - s_time)

# print(len(all_docs[0]['documents']))

all_docs_temp  = all_docs.copy()
print((all_docs[0]['documents'][0]['summary']))

print('Removal of stop words processing started')
all_docs_final, total_time = process_each_topic(all_docs)

print(all_docs_final[0]['documents'][0], total_time)
print('All docs temp processing tiem:', total_time)

# ## Convert Results into Json file
import json
# Restructure the output dict into the one we need in the json
def batch_results_to_json(batch_results, save_file_name):
    restruct_dict = {}
    for index, batch_item in enumerate(batch_results):
        # print(batch_item[1])
        title = batch_item['topic']
        docs = batch_item['documents']
        restruct_dict[title] = docs


    with open(save_file_name, 'w') as f:
        json.dump(restruct_dict, f)
    
    return restruct_dict

final_results = batch_results_to_json(all_docs_final, f'topic_{topics_and_terms[0][0]}_final.json')
len(final_results)
print(f"Saved the final results in the topic_{topics_and_terms[0][0]}_final.json file")