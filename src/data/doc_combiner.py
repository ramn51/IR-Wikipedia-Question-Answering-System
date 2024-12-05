import json
import os
# Restructure the output dict into the one we need in the json
def batch_results_to_json(save_file_name, file_name):
    try:
        with open(file_name, 'r') as file:
            data = json.load(file)

        restruct_dict = {}
        if isinstance(data, dict):
            topic = data.get("topic", "Unknown")
            documents = data.get("documents", [])

            # Add the topic and associated documents to the restructured dictionary
            restruct_dict[topic] = documents
        
        with open(save_file_name, 'w') as f:
            json.dump(restruct_dict, f)

    except json.JSONDecodeError:
        print("Invalid JSON file")
        return False
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False
    
    return restruct_dict


def combine_json_files(file1_path, file2_path, output_path, same_topic=False):
    # Read the first JSON file
    with open(file1_path, 'r') as f1:
        data1 = json.load(f1)

    # Read the second JSON file
    with open(file2_path, 'r') as f2:
        data2 = json.load(f2)

    if same_topic:
        combined_data = data1.copy()
        for key, value in data2.items():
            if key in combined_data:
                combined_data[key].extend(value)
            else:
                combined_data[key] = value
    else:
        combined_data = {**data1, **data2}

    # Write the combined data to a new JSON file
    with open(output_path, 'w') as outfile:
        json.dump(combined_data, outfile, indent=4)

    print(f"Combined JSON saved to {output_path}")


def modify_certain_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    for topic, docs in data.items():
        for doc in docs:
            doc['topic'] = topic
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

    return data

def seperate_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    for topic, docs in data.items():
        for doc in docs:
            doc['topic'] = topic
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

    return data

def separate_json_keys_to_files(input_file, output_directory):
    """
    Splits a JSON file into multiple files, one for each key.

    :param input_file: Path to the input JSON file
    :param output_directory: Directory where the separate files will be saved
    """
    try:
        with open(input_file, 'r') as infile:
            data = json.load(infile)

        if not isinstance(data, dict):
            raise ValueError("The input JSON file must contain a dictionary at the top level.")

        os.makedirs(output_directory, exist_ok=True)

        # Save each key-value pair to a separate JSON file
        for key, value in data.items():
            output_file = os.path.join(output_directory, f"{key}_seperated.json")
            with open(output_file, 'w') as outfile:
                json.dump({key: value}, outfile, indent=4)
            print(f"Saved {key} to {output_file}")

    except json.JSONDecodeError:
        print("Error: Input file is not a valid JSON file.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    file_name0 = 'checkpoint_until_Food_4_topics_results.json'
    # Usage

    # Convert the Sports and health JSON files to the required format
    save_file_name = 'Sports_regular_format.json'
    file_name = './docs/checkpoint_Sports_results.json'
    save_file_name2 = 'Health_regular_format.json'
    file_name2 = './docs/checkpoint_Health_results.json'
    save_file_name3 = 'Technology_regular_format.json'
    file_name3 = './docs/checkpoint_Technology_results.json'


    # Combine the Sports and Health JSON files
    file1_path = 'Sports_regular_format.json'
    file2_path = 'Health_regular_format.json'
    output_path = 'Health_Sports_combined.json'

    # Combine Sports Health and Technology JSON files
    output_path2 = 'Health_Sports_Technology_combined.json'

    # Combine the Health, Sports, Travel and Entertainment JSON files
    file3_path = 'Health_Sports_combined.json'
    file4_path = 'Travel_and_Entertainment_docs.json'
    output_path3 = 'Health_Sports_Travel_Entertainment_Technology_combined.json'

    modify_certain_json(file4_path)

    # Make the JSON files in the required format
    batch_results_to_json(save_file_name, file_name)
    batch_results_to_json(save_file_name2, file_name2)
    batch_results_to_json(save_file_name3, file_name3)

    # Combine files
    combine_json_files(file1_path, file2_path, output_path)
    combine_json_files(output_path, save_file_name3, output_path2)
    combine_json_files(output_path2, file4_path, output_path3)

    # Seperate out some files which needs combining later on
    separate_json_keys_to_files("Food_Economy_Travel_docs.json", "seperated_out_files")
    # separate_json_keys_to_files(file_name0, "seperated_out_files")

    modify_certain_json("seperated_out_files/Food_seperated.json")
    modify_certain_json("seperated_out_files/Economy_seperated.json")

    batch_results_to_json('Economy_regular_format.json','./docs/checkpoint_Economy_results.json')

    # Combine economy results of two different files
    economy_file_path1 = 'Economy_regular_format.json'
    economy_file_path2 = 'seperated_out_files/Economy_seperated.json'
    economy_output_path = 'Economy_combined.json'

    combine_json_files(economy_file_path1, economy_file_path2, economy_output_path, same_topic=True)

    # Combine the Economy and Food JSON files
    economy_file_path = 'Economy_combined.json'
    food_file_path = 'seperated_out_files/Food_seperated.json'
    output_file_path = 'Economy_Food_combined.json'
    combine_json_files(economy_file_path, food_file_path, output_file_path)

    # Combine the Economy_Food_combined.json and Health_Sports_Travel_Entertainment_Technology_combined.json
    file1_path = 'Economy_Food_combined.json'
    file2_path = 'Health_Sports_Travel_Entertainment_Technology_combined.json'
    output_path = 'All_topics_combined.json'

    combine_json_files(file1_path, file2_path, output_path)
    combine_json_files(output_path, file_name0, 'All_topics_combined_final.json')



# print(final_results.keys())