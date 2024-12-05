import wikipedia
import re
import random
import time
from tqdm import tqdm
import json

NUM_DOCS = 5100
MIN_SUMMARY_LEN = 300

class WikiRetriever:
    def __init__(self, topic, relevant_terms, total_docs=520, wiki_search_size=500):
        self.visited = set()
        self.search_size = wiki_search_size
        self.relevant_terms = [i.lower() for i in relevant_terms]
        self.total_docs = total_docs
        self.document_topic = topic
        self.search_terms = self.relevant_terms
        self.progress_bar = None

    def reset(self):
        self.visited.clear()

    def checkpoint(self, file_name, results):
        with open(file_name, 'w') as f:
            json.dump(results, f)

    @staticmethod
    def is_relevant(page, key_words, summary):
        words_re = re.compile("|".join(key_words))
        normalized_summary = WikiRetriever.filter_for_alnum(summary)
        return bool(words_re.findall(normalized_summary) and (len(normalized_summary) > MIN_SUMMARY_LEN))

    @staticmethod
    def filter_for_alnum(summary):
        return re.sub(r'[^a-zA-Z0-9]', ' ', summary.lower())

    def make_result_dict(self, content):
        if content is not None:
            return {
                'summary': self.filter_for_alnum(content.summary),
                'url': content.url,
                'title': content.title,
                'revision_id': content.revision_id,
                'topic': self.document_topic
            }
        return {}

    def get_page_content(self, title):
        if title in self.visited:
            return None, []
        try:
            content = wikipedia.page(title, auto_suggest=False)
            if self.is_relevant(content, self.relevant_terms, content.summary):
                self.visited.add(content.title)
                return content, [self.make_result_dict(content)]
            return content, []
        except wikipedia.exceptions.PageError:
            print(f"Page not found for {title}")
            return None, []
        except wikipedia.exceptions.DisambiguationError as e:
            random_title = random.choice(e.options)
            return self.get_page_content(random_title)

    def search_thru_links(self, page, max_links=20):
        if not page:
            return []
        links = page.links[:max_links]
        link_results = []
        for link in links:
            if link not in self.visited:
                page, res = self.get_page_content(link)
                if res:
                    link_results.extend(res)
                    if len(link_results) >= self.total_docs:
                        break
        return link_results

    def wiki_doc_retriever(self):
        results = []
        print(f"Starting retrieval for {self.document_topic}")
        self.progress_bar = tqdm(total=self.total_docs, desc=f"Retrieving docs for {self.document_topic}", leave=True)

        all_search_results = []
        for search_term in self.search_terms:
            all_search_results.extend(wikipedia.search(search_term, results=self.search_size))
        all_search_results = list(set(all_search_results))

        print(all_search_results)

        for title in all_search_results:
            page, page_res = self.get_page_content(title)
            if page_res:
                # print(page_res)
                results.extend(page_res)
                self.progress_bar.update(len(page_res))
            if len(results) >= self.total_docs:
                break

        if len(results) < self.total_docs:
            print(f"Found only {len(results)} docs, going through the links further")
            for title in all_search_results:
                page, _ = self.get_page_content(title)
                if page:
                    link_results = self.search_thru_links(page)
                    results.extend(link_results)
                    self.progress_bar.update(len(link_results))
                if len(results) >= self.total_docs:
                    break

        self.progress_bar.close()
        return results, {'title': self.document_topic, 'documents': len(results)}, self.visited

def main_runner(topics_terms_batch):
    all_results = []
    visited_pages_list = []
    for topic, terms in topics_terms_batch:
        wiki_ret = WikiRetriever(topic, terms, total_docs=NUM_DOCS)
        res, docs_dict, visited_pages = wiki_ret.wiki_doc_retriever()

        wiki_ret.checkpoint(f'checkpoint_{topic}_results.json', res)

        all_results.append({'topic': docs_dict['title'], 'documents': res})
        visited_pages_list.append({'topic': docs_dict['title'], 'visited_page_set': list(visited_pages)})
        print(f"Retrieved {len(res)} documents for {topic}")
    return all_results, visited_pages_list

# Usage
topics_and_terms = [
        ("Travel", [
        "Top tourist destinations", "Airline industry data", "Travel trends", 
        "Sustainable tourism", "Adventure tourism", "Business travel", 
        "Travel restrictions", "Ecotourism", "Digital nomadism", "Luxury travel", 
        "Budget travel", "Solo travel", "Family vacations", "Travel safety", 
        "Cultural tourism", "Space tourism"
    ]),
     ("Food", [
        "Crop yield statistics", "Global hunger", "Food security", 
        "Sustainable agriculture", "Nutrition trends", "Food Industry", "Cuisines",
        "Food supply chains", "Organic farming", "Food waste management", 
        "Food Safety", "Genetically modified organisms", "Urban farming", "Plant-based diets"
    ])
]

results, visited_pages = main_runner(topics_and_terms)