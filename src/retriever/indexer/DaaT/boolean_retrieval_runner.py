from indexer import Indexer
from preprocessor import Preprocessor
from linkedlist import LinkedList, Node

from tqdm import tqdm
import heapq
import sys
import random
import json

class BooleanRetrievalRunner:
    def __init__(self):
        self.preprocessor = Preprocessor()
        self.indexer = Indexer() 

    def _merge(self, results=None, daats=True, key_name=None):
        """ Implement the merge algorithm to merge 2 postings list at a time.
            Use appropriate parameters & return types.
            While merging 2 postings list, preserve the maximum tf-idf value of a document.
            To be implemented."""
        merged = {}

        # print("RESULTS", results)

        if not daats:
            key = key_name
        else:
            key = 'daatAnd'
            
        for results in results:
            merged.update(results[key])
        
        return merged
    
    def _daat_and_skip(self, retrieved_postings_list, original_query, use_tf_idf=False):
        """ Implement the DAAT AND algorithm, which merges the postings list of N query terms.
            Use appropriate parameters & return types.
            To be implemented."""
        postings_list_key = 'postingsListSkip'

        postings_lists = retrieved_postings_list[postings_list_key]

        postings_list = dict(sorted(postings_lists.items(), key=lambda item: len(item[1])))

        heads = {term: retrieved_postings_list['head'][term] for term in postings_list}

        terms = list(postings_list.keys())

        # Ensure original_query is a string
        if isinstance(original_query, list):
            query_terms_key = ' '.join(original_query)
        else:
            query_terms_key = original_query

        res_key = 'daatAndSkip'
        res = {res_key: {query_terms_key: {'results': [], 'num_comparisons': 0, 'num_docs': 0}}}
        

        if use_tf_idf:
            min_heap = [(postings_lists[term][0][0], postings_lists[term][0][1], term, heads[term]) for term in terms]
            heapq.heapify(min_heap)
        else:
            min_heap = [(postings_lists[term][0], term, heads[term]) for term in terms]
            heapq.heapify(min_heap)

        print("MIN HEAP INITAIL", min_heap)

        log_file = open('daat_log_file.txt', 'w')
        sys.stdout = log_file

        while min_heap:
            if use_tf_idf:
                min_doc_id, min_tf_idf, min_term, min_head = heapq.heappop(min_heap)
            else:
                min_doc_id, min_term, min_head = heapq.heappop(min_heap)

            docs_matched = True

            res[res_key][query_terms_key]['num_comparisons'] += 1
            print("MIN DOC ID", min_doc_id)
            print("heap after pop", min_heap)
            terms_to_remove = []

            for term in terms:
                if heads[term] is None:
                    terms_to_remove.append(term)

            terms = [i for i in terms if i not in terms_to_remove]

            # If there's only one term left or any term has reached the end, break out of the loop
            if len(terms) <= 1 or len(terms_to_remove) > 0:
                break
            
            for term in terms:
                current_node = heads[term]
                doc_id = current_node.value[0]

                # Checking doc_id value of the current node against the min_doc_id
                if min_doc_id != doc_id:
                    if current_node.skip is not None and current_node.skip.value[0] <= min_doc_id:
                        # Use skip pointer to jump to next node skip
                        heads[term] = current_node.skip
                    else:
                        # Move to next node (normal traversal)
                        if current_node.next is not None:
                            heads[term] = current_node.next
                    docs_matched = False
                    # continue

                else:
                    if current_node.next is not None:
                        heads[term] = current_node.next
                

                if heads[term] is not None:
                    if use_tf_idf:
                        next_doc_id = heads[term].value[0]
                        next_tf_idf = heads[term].value[2]
                        heapq.heappush(min_heap, (next_doc_id, next_tf_idf, term, heads[term]))
                    else:
                        next_doc_id = heads[term].value[0]
                        print("NEXT DOC ID", next_doc_id, term, heads[term])
                        heapq.heappush(min_heap, (next_doc_id, term, heads[term]))

            if docs_matched:
                print("DOCS MATCHED", min_doc_id, min_term, "\n")
                if use_tf_idf:
                    res[res_key][query_terms_key]['results'].append((min_doc_id, min_tf_idf))
                else:
                    res[res_key][query_terms_key]['results'].append(min_doc_id)
                res[res_key][query_terms_key]['num_docs'] += 1

                # Clear out all occurrences of `min_doc_id` from the heap
                while min_heap and (min_doc_id == min_heap[0][0]):
                    if use_tf_idf:
                        min_doc_id, min_tf_idf, min_term, _ = heapq.heappop(min_heap)
                    else:
                        min_doc_id, min_term, _ = heapq.heappop(min_heap)

        return res


    def _merge_intersection_skip(self, head_posting1, head_posting2, use_tf_idf=False):
        if not head_posting1 or not head_posting2:
            return []

        head1 = head_posting1
        head2 = head_posting2

        result = []
        num_comparisons = 0

        while head1 and head2:
            num_comparisons += 1
            if head1.value[0] == head2.value[0]:
                if use_tf_idf:
                    result.append((head1.value[0], head1.value[3]))
                else:
                    result.append(head1.value[0])
                head1 = head1.next
                head2 = head2.next
            elif head1.value[0] < head2.value[0]:
                if head1.skip and head1.skip.value[0] <= head2.value[0]:
                    head1 = head1.skip
                else:
                    head1 = head1.next
            else:
                if head2.skip and head2.skip.value[0] <= head1.value[0]:
                    head2 = head2.skip
                else:
                    head2 = head2.next

        if use_tf_idf:
            result.sort(key=lambda x: x[1], reverse=True)
        return result, num_comparisons
    
    
    def _daat_and_skip_intersect(self, retrieved_postings_list, original_query_term, query_terms, use_tf_idf=False):
        postings_list_key = 'postingsListSkip'
        postings_lists = retrieved_postings_list[postings_list_key]

        # print(postings_lists, 'Inside DAAT AND SKIP INTERSECT')

        postings_lists = dict(sorted(postings_lists.items(), key=lambda item: len(item[1])))
        

        # if not postings_lists or len(postings_lists) < len(query_terms):
        #     return [], 0

        num_comparisons = 0
        
        res = postings_lists[query_terms[0]]

        postings_list_heads = [ retrieved_postings_list['head'][term] for term in postings_lists ]

        num_comparisons = {term: 0 for term in postings_lists}

        query_terms_key = ' '.join(original_query_term)

        # result_key = 'daatAndSkip' if not use_tf_idf else 'daatAndSkipTfIdf'
        result_key = 'daatAnd'

        result = {result_key: {query_terms_key: {'results': [], 'num_comparisons': 0, 'num_docs': 0}}}

        for i in range(len(postings_list_heads) - 1):
            res_array, num_compares = self._merge_intersection_skip(postings_list_heads[i], postings_list_heads[i + 1], use_tf_idf)
            result[result_key][query_terms_key]['results'] = res_array
            result[result_key][query_terms_key]['num_comparisons']  = num_compares
            result[result_key][query_terms_key]['num_docs'] = len(res_array)
            num_comparisons[query_terms[i]] = num_compares
            if not res:
                break
            # num_comparisons += 1
        if use_tf_idf:
            result[result_key][query_terms_key]['results'] = [doc_id for doc_id, _ in result[result_key][query_terms_key]['results']]
        return result

 

    def _daat_and(self, retrieved_postings_list, original_query ,use_skip=False ,use_tf_idf=False):
        """ Implement the DAAT AND algorithm, which merges the postings list of N query terms.
            Use appropriate parameters & return types.
            To be implemented."""
         # log_file = open('daat_log_file.txt', 'w')
        # sys.stdout = log_file
        posting_list_key = 'postingsList' if not use_skip else 'postingsListSkip'


        starting_ptrs = {term: 0 for term in retrieved_postings_list[posting_list_key]}
        
        ending_ptrs = {term: len(retrieved_postings_list[posting_list_key][term])  for term in retrieved_postings_list[posting_list_key]}

        postings_lists = retrieved_postings_list[posting_list_key]

        if use_skip:
            print('Retrieved Postings List', postings_lists)

        # For Merge order optimization
        postings_lists = dict(sorted(postings_lists.items(), key=lambda item: len(item[1])))
        terms = list(postings_lists.keys())

        # Ensure original_query is a string
        if isinstance(original_query, list):
            query_terms_key = ' '.join(original_query)
        else:
            query_terms_key = original_query

        res = {'daatAnd': {query_terms_key: {'results': [], 'num_comparisons': 0, 'num_docs': 0}}}


        # Add the first element of each postings list to the min heap
        # If its tf-idf ordering then add the doc_id still but the tuple needs to destructured
        if use_tf_idf:
            min_heap = [(postings_lists[term][0][0], postings_lists[term][0][1], term) for term in terms]
        else:
            min_heap = [(postings_lists[term][0], term) for term in terms]
        
        heapq.heapify(min_heap)

        while min_heap:
            if use_tf_idf:
                min_doc_id, min_tf_idf, min_term = heapq.heappop(min_heap)
            else:
                min_doc_id, min_term = heapq.heappop(min_heap)

            docs_matched = True

            res['daatAnd'][query_terms_key]['num_comparisons'] += 1
            # print("MIN DOC ID", min_doc_id)
            # print("heap after pop", min_heap)

            # Take out the term which dont need to iterated as its length is traversed
            terms_to_remove = []

            for term, start_ptr in starting_ptrs.items():
                for term_, end_ptr in ending_ptrs.items():
                    if term == term_ and start_ptr == end_ptr:
                        terms_to_remove.append(term)

            # print("TERMS TO REMOVE", terms_to_remove)
            
            terms = [i for i in terms if i not in terms_to_remove]
            
            # print('TERMS UPDATED', terms)

            # If there is only one term then dont have to continue since it will not result in an AND match
            if len(terms) == 1:
                break

            # If there is even one term which has reached the end of its postings list then break
            if len(terms_to_remove) > 0:
                break

            for term in terms:
                term_pointer = starting_ptrs[term]
                term_postings_list = postings_lists[term]

                # print("TERM POINTER", term, term_pointer)
                # print("TERM POSTINGS LIST", term, term_postings_list)
                # print("ENDING PTRS", ending_ptrs)
                
                doc_id = term_postings_list[term_pointer][0] if use_tf_idf else term_postings_list[term_pointer]

                if term_pointer < ending_ptrs[term] and doc_id == min_doc_id:
                    # print("INSIDE THE IF of exact match", term_postings_list[term_pointer], min_doc_id)
                    # res['daatAnd'][query_terms_key]['num_comparisons'] += 1
                    term_pointer += 1
                    starting_ptrs[term] = term_pointer
                    # print(starting_ptrs)
                    if term_pointer < ending_ptrs[term]:
                        if use_tf_idf:
                            doc_id, tf_idf = term_postings_list[term_pointer]
                            heapq.heappush(min_heap, (doc_id, tf_idf, term))
                        else:
                            doc_id = term_postings_list[term_pointer]
                            heapq.heappush(min_heap, (doc_id, term))
                        # print("MIN HEAP AFTER INSERTION", min_heap)
                    else:
                        docs_matched = False
                    continue
                

                elif term_pointer < ending_ptrs[term] and doc_id > min_doc_id:
                    # res['daatAnd'][query_terms_key]['num_comparisons'] += 1
                    # print("INSIDE THE ELIF of not exact match", term_postings_list[term_pointer], min_doc_id)
                    docs_matched = False

                elif term_pointer >= ending_ptrs[term]:
                    # print('ENDING TERM PTR REACHED FOGR TERM', term)
                    continue


            # print("STARTING PTRS", starting_ptrs, "DOC MATCHED", docs_matched)
            if docs_matched:
                if use_tf_idf:
                    res['daatAnd'][query_terms_key]['results'].append((min_doc_id, min_tf_idf))
                else:
                    res['daatAnd'][query_terms_key]['results'].append(min_doc_id)
                res['daatAnd'][query_terms_key]['num_docs'] += 1
                # for term in terms:
                #     starting_ptrs[term] += 1
                # print('MIN DOC ID BEFORE THE CLEARING LOOP', min_doc_id, min_heap, starting_ptrs)
                while min_heap and (min_doc_id == min_heap[0][0] if use_tf_idf else min_doc_id == min_heap[0]):
                    if use_tf_idf:
                        min_doc_id, min_tf_idf, min_term = heapq.heappop(min_heap)
                    else:
                        min_doc_id, min_term = heapq.heappop(min_heap)
                    # print('Poping from heap', min_doc_id, min_heap)

                # print('MIN DOC ID AFTER THE CLEARING LOOP', min_doc_id, min_heap, starting_ptrs)

            # print("RES AFTER THE LOOP", res)
        if use_tf_idf:
            res['daatAnd'][query_terms_key]['results'].sort(key=lambda x: x[1], reverse=True)
            # Remove the tf-idf values from the results
            res['daatAnd'][query_terms_key]['results'] = [doc_id for doc_id, _ in res['daatAnd'][query_terms_key]['results']]

        # print(res)

        return res
       

    def get_postings(self, query, use_skip=False, get_tf_idf=False):
        """ Function to get the postings list of a term from the index.
            Use appropriate parameters & return types.
            To be implemented."""
        inverted_index_key = 'postingsList' if not use_skip else 'postingsListSkip'
        res = {inverted_index_key: {}, 'head': {}}
        inverted_index = self.indexer.get_index()
        for term in query:
            if term not in inverted_index:
                res[inverted_index_key][term] = []
                res['head'][term] = None
            else:
                if not use_skip:
                    term_docs, list_head = inverted_index[term].traverse_list()
                    res['head'][term] = list_head
                else:
                    term_docs, list_head = inverted_index[term].traverse_list()
                    term_docs = inverted_index[term].traverse_skips()
                    res['head'][term] = list_head
                
                res[inverted_index_key][term] = [(doc_id, tf_idf) if get_tf_idf else doc_id for doc_id, term_freq, total_doc_tokens, tf_idf in term_docs]
                
        return res

    def _output_formatter(self, op):
        """ This formats the result in the required format.
            Do NOT change."""
        if op is None or len(op) == 0:
            return [], 0
        op_no_score = [int(i) for i in op]
        results_cnt = len(op_no_score)
        return op_no_score, results_cnt

    def run_indexer(self, corpus_path):
        """ This function reads & indexes the corpus. After creating the inverted index,
            it sorts the index by the terms, add skip pointers, and calculates the tf-idf scores.
            Already implemented, but you can modify the orchestration, as you seem fit."""
        # with open(corpus, 'r') as fp:
        #     for line in tqdm(fp.readlines()):
        #         doc_id, document = self.preprocessor.get_doc_id(line)
        #         tokenized_document = self.preprocessor.tokenizer(document)
        preprocessed_data = self.preprocessor.preprocess_2(corpus_path)
        inverted_index, total_docs = self.indexer.create_index(preprocessed_data)
        self.indexer.sort_terms()
        self.indexer.add_skip_connections()
        self.indexer.calculate_tf_idf(total_docs)

    def sanity_checker(self, command):
        """ DO NOT MODIFY THIS. THIS IS USED BY THE GRADER. """

        index = self.indexer.get_index()
        kw = random.choice(list(index.keys()))
        return {"index_type": str(type(index)),
                "indexer_type": str(type(self.indexer)),
                "post_mem": str(index[kw]),
                "post_type": str(type(index[kw])),
                "node_mem": str(index[kw].start_node),
                "node_type": str(type(index[kw].start_node)),
                "node_value": str(index[kw].start_node.value),
                "command_result": eval(command) if "." in command else ""}

    def run_queries(self, query_list, original_query_list):
        # print(query_list)
        """ DO NOT CHANGE THE output_dict definition"""
        output_dict = {'postingsList': {},
                       'postingsListSkip': {},
                       'daatAnd': {},
                       'daatAndSkip': {},
                       'daatAndTfIdf': {},
                       'daatAndSkipTfIdf': {},
                       }
        
        daat_results = []
        daat_results_skip = []
        daat_results_tf_idf = []
        daat_results_tf_idf_skip = []

        query_list_tuple = [(query, original_query) for query, original_query in zip(query_list, original_query_list)] 

        # print(query_list_tuple)

        # log_file = open('daat_log_file.txt', 'w')
        # sys.stdout = log_file


        postings_lists_set = []
        postings_lists_skip_set = []
        postings_lists_tf_idf_set = []
        postings_lists_tf_idf_skip_set = []

        # print('Query TUPLE', query_list_tuple)

        for query, original_query in tqdm(query_list_tuple, desc="Processing Queries to do DAAT"):
            """ Run each query against the index. You should do the following for each query:
                1. Pre-process & tokenize the query.
                2. For each query token, get the postings list & postings list with skip pointers.
                3. Get the DAAT AND query results & number of comparisons with & without skip pointers.
                4. Get the DAAT AND query results & number of comparisons with & without skip pointers, 
                    along with sorting by tf-idf scores."""
            query_str = " ".join(query)
            postings_list = self.get_postings(query, use_skip=False, get_tf_idf=False)
            postings_list_skip = self.get_postings(query, use_skip=True, get_tf_idf=False)
            postings_list_tf_idf = self.get_postings(query, use_skip=False, get_tf_idf=True)
            postings_list_tf_idf_skip = self.get_postings(query, use_skip=True, get_tf_idf=True)

            postings_lists_set.append(postings_list)
            postings_lists_skip_set.append(postings_list_skip)
            postings_lists_tf_idf_set.append(postings_list_tf_idf)
            postings_lists_tf_idf_skip_set.append(postings_list_tf_idf_skip)

            # print(postings_list_tf_idf_skip, "POSTINGS LIST TF IDF SKIP")
            # print("QUERY", query_str, "POSTINGS LIST", postings_list)
            # print("POstings List Skip", postings_list_skip)
            daat_result_normal = self._daat_and(postings_list, original_query)
            daat_result_skip = self._daat_and_skip_intersect(postings_list_skip, original_query, query)
            daat_result_tf_idf = self._daat_and(postings_list_tf_idf, original_query, use_tf_idf=True)
            daat_result_tf_idf_skip = self._daat_and_skip_intersect(postings_list_tf_idf_skip, original_query, query, use_tf_idf=True)

            daat_results.append(daat_result_normal)
            daat_results_skip.append(daat_result_skip)
            daat_results_tf_idf.append(daat_result_tf_idf)
            daat_results_tf_idf_skip.append(daat_result_tf_idf_skip)

        
        # print("RESULT of SKIP DAAT AND TFIDF", daat_results_tf_idf)
        output_dict['daatAnd'] = self._merge(daat_results, daats=True)
        output_dict['daatAndSkip'] = self._merge(daat_results_skip, daats=True)
        output_dict['daatAndTfIdf'] = self._merge(daat_results_tf_idf, daats=True)
        output_dict['daatAndSkipTfIdf'] = self._merge(daat_results_tf_idf_skip, daats=True)
 
        output_dict['postingsList'] = self._merge(postings_lists_set, daats=False, key_name='postingsList')
        output_dict['postingsListSkip'] = self._merge(postings_lists_skip_set, daats=False, key_name='postingsListSkip')

        return output_dict
    


if __name__ == "__main__":
    """ Driver code for the project, which defines the global variables.
        Do NOT change it."""

    output_location = "project2_output.json"


    """ Initialize the project runner"""
    runner = BooleanRetrievalRunner()

    """ Index the documents from beforehand. When the API endpoint is hit, queries are run against 
        this pre-loaded in memory index. """
    corpus_path = 'input_corpus.txt'
    runner.run_indexer(corpus_path)

    queries, original_queries = runner.preprocessor.preprocess_query(file_path='queries.txt')

    print(queries)

    # postings_list = runner.get_postings(queries[0], use_skip=True, get_tf_idf=False)
    # print(postings_list)

    # # print(runner._daat_and_skip(postings_list, queries[2], use_tf_idf=False))

    # print(runner._daat_and_skip_intersect(queries[0], postings_list))


    # Print or return the combined result
    # print(combined_results)

    
    output_dict = runner.run_queries(queries, original_queries)

    print(output_dict)
    # print(output_dict)
    # with open(output_location, 'w') as fp:
    #     json.dump(output_dict, fp)

    with open(output_location, 'w') as fp:
        json.dump(output_dict, fp, sort_keys=True, indent=4)
    



        