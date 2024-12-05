import json
import os

class CorpusCreator:
    def __init__(self, json_input_file, json_input_folder):
        self.corpus = []
        self.file_name = json_input_file.split('/')[-1].split('.')[0] + '.txt' if json_input_file else 'corpus_main.txt'
        self.folder_path = '../indexer/corpus'
        self.input_file = json_input_file
        self.input_folder = json_input_folder
        self.process_folder = True if self.input_folder else False
        
        os.makedirs(self.folder_path, exist_ok=True)
        self.file_save_path = os.path.join(self.folder_path, self.file_name)
        
    def read_json(self, file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data
    
    def process_docs(self, data):
        # data = self.read_json(self.input_file)
        for doc_id, doc in enumerate(data["documents"]):
            # print("Topic name", item["topic"])
            # # documents = item["documents"]
            # print(item['summary'])
            self.corpus.append((doc_id, doc["summary"]))

        return self.corpus
    

    def convert_to_corpus(self):
        res_file_name = 'corpus_main.txt' if self.process_folder else None
        if self.process_folder:
            self.read_folder_files()
            self.save_to_file(res_file_name)
        
        else:
            data = self.read_json(self.input_file)
            self.process_docs(data)
            self.save_to_file(res_file_name)

    def read_folder_files(self):
        for file in os.listdir(self.input_folder):
            if file.endswith('.json'):
                print(file)
                data = self.read_json(os.path.join(self.input_folder, file))
                self.corpus.extend(self.process_docs(data))
        return self.corpus
    
    def save_to_file(self, file_name_to_save=None):
        file_name = file_name_to_save if 'corpus_main.txt' else self.file_name
        if file_name_to_save:
            with open(self.file_save_path, 'w') as f:
                for doc in self.corpus:
                    f.write(f'{doc[0]} \t {doc[1]}\n')



if __name__ == '__main__':
    # json_file_path = 'retriever\\docs\\checkpoint_Environment_results.json'
    # folder_path = 'retriever\\docs'
    # Single file corpus maker
    json_file_path = '../retriever/docs/checkpoint_Environment_results.json'
    print("Single file corpus maker")
    corpus_creator = CorpusCreator(json_file_path, None)
    corpus_creator.convert_to_corpus()
    # Folder corpus maker
    folder_path = '../retriever/docs'
    print("Folder corpus maker")
    corpus_creator2 = CorpusCreator(None, folder_path)

    corpus_creator2.convert_to_corpus()



