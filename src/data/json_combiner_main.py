from doc_combiner import combine_json_files, modify_certain_json, seperate_json, batch_results_to_json
from validator_script import analyze_json_file
import json

file1 = './seperated_out_files/Food_Tech_docs.json'
file2 = './seperated_out_files/Travel_Economy_docs.json'
file3 = './docs/checkpoint_Sports_results.json'
file4='./docs/Environment_Politics_Education_docs.json'
file5='./docs/checkpoint_Health_results.json'
file6='./docs/Entertainment_docs.json'


save_file1 = 'Food_Tech_regular_format.json'
save_file2 = 'Travel_Economy_regular_format.json'

modify_certain_json(file1)
modify_certain_json(file2)
modify_certain_json(file6)
# modify_certain_json(file5)

# batch_results_to_json(save_file1, file1)
# batch_results_to_json(save_file2, file2)

def combine_docs(json_files, output_file):
    # Create a list of all the JSON files that you want to combine.

    # Create an empty list to store the Python objects.
    python_objects = []

    # Load each JSON file into a Python object.
    for json_file in json_files:
        with open(json_file, "r") as f:
            python_objects.append(json.load(f))

    # Dump all the Python objects into a single JSON file.
    with open(output_file, "w") as f:
        json.dump(python_objects, f, indent=4)

    # # Dump all the Python objects into a single JSON file.
    # with open("combined.json", "w") as f:
        


# json_files = [file1, file2, file3, file4, file5, file6]
# combine_docs(json_files, 'All_topics_combined_final_testing.json')


# combine_json_files(save_file1, save_file2, 'Food_Tech_Travel_Economy_combined.json')
file = 'All_topics_combined_final_testing.json'
# analyze_json_file(file)
is_valid, topic_stats2 = analyze_json_file(file)
    # print(f"\nIs the JSON file valid? {topic_stats}")
for c, t in topic_stats2.items():
    print(f"{c} : {t['count']}")