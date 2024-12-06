from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS
# from transformers import AutoModelForCausalLM, AutoTokenizer
# import torch, os, json
import os, json

app = Flask(__name__)
CORS(app)

# # Load the DialoGPT model and tokenizer
# model_name = "microsoft/DialoGPT-medium"
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# model = AutoModelForCausalLM.from_pretrained(model_name)

# # Initialize conversation history
# chat_history_ids = None

# @app.route('/chat', methods=['POST'])
# def chat():
#     global chat_history_ids
#     user_input = request.json.get("message", "")
#     if not user_input:
#         return jsonify({"response": "No input provided!"}), 400

#     # Encode input and generate response
#     new_input_ids = tokenizer.encode(user_input + tokenizer.eos_token, return_tensors="pt")
#     attention_mask = torch.ones(new_input_ids.shape, dtype=torch.long)

#     if chat_history_ids is not None:
#         bot_input_ids = torch.cat([chat_history_ids, new_input_ids], dim=-1)
#         attention_mask = torch.cat([torch.ones(chat_history_ids.shape, dtype=torch.long), attention_mask], dim=-1)
#     else:
#         bot_input_ids = new_input_ids

#     chat_history_ids = model.generate(
#         bot_input_ids,
#         attention_mask=attention_mask,
#         max_length=1000,
#         pad_token_id=tokenizer.eos_token_id,
#         top_k=50,
#         top_p=0.95,
#         temperature=0.7,
#         do_sample=True,
#     )

#     bot_response = tokenizer.decode(chat_history_ids[:, bot_input_ids.shape[-1]:][0], skip_special_tokens=True)
#     return jsonify({"response": bot_response})



# Endpoint to save the response data
@app.route('/saveLog', methods=['POST'])
def save_log():
    log_file_path = os.path.join(os.getcwd(), "analytics_logs", "responses.json")

    # Ensure the "logs" folder exists
    if not os.path.exists(os.path.dirname(log_file_path)):
        os.makedirs(os.path.dirname(log_file_path))
    try:
        # Extract the JSON data from the request
        log_data = request.get_json()

        # Open the file in append mode to add new log data
        with open(log_file_path, 'a') as log_file:
            # Append the log data as a JSON object with a newline
            json.dump(log_data, log_file)
            log_file.write('\n')  # Ensure each log is on a new line

        return jsonify({"message": "Log data saved successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/getLog', methods=['GET'])
def get_log():
    log_file_path = './chatbot-ui/src/analytics_data/analytics_data.json'  # Update this with your actual log file path
    
    # Check if the file exists
    if not os.path.exists(log_file_path):
        abort(404, description="Log file not found")

    try:
        # Open and read the log file
        with open(log_file_path, 'r') as file:
            log_data = file.read()

        # If your log file is in JSON format, you can return it as a JSON response
        return jsonify(log_data)

    except Exception as e:
        # Handle any errors during file reading
        abort(500, description=f"Error reading log file: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)
