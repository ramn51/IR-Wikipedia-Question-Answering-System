from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

app = Flask(__name__)
CORS(app)

# Load the DialoGPT model and tokenizer
model_name = "microsoft/DialoGPT-medium"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Initialize conversation history
chat_history_ids = None

@app.route('/chat', methods=['POST'])
def chat():
    global chat_history_ids
    user_input = request.json.get("message", "")
    if not user_input:
        return jsonify({"response": "No input provided!"}), 400

    # Encode input and generate response
    new_input_ids = tokenizer.encode(user_input + tokenizer.eos_token, return_tensors="pt")
    attention_mask = torch.ones(new_input_ids.shape, dtype=torch.long)

    if chat_history_ids is not None:
        bot_input_ids = torch.cat([chat_history_ids, new_input_ids], dim=-1)
        attention_mask = torch.cat([torch.ones(chat_history_ids.shape, dtype=torch.long), attention_mask], dim=-1)
    else:
        bot_input_ids = new_input_ids

    chat_history_ids = model.generate(
        bot_input_ids,
        attention_mask=attention_mask,
        max_length=1000,
        pad_token_id=tokenizer.eos_token_id,
        top_k=50,
        top_p=0.95,
        temperature=0.7,
        do_sample=True,
    )

    bot_response = tokenizer.decode(chat_history_ids[:, bot_input_ids.shape[-1]:][0], skip_special_tokens=True)
    return jsonify({"response": bot_response})

if __name__ == '__main__':
    app.run(debug=True)
