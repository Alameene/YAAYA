from flask import Flask, render_template, request, jsonify
from transformers import pipeline
import os

app = Flask(__name__)

# Conversation memory store
chat_history = []

# =========================
#  TRY TO LOAD MODEL
# =========================
try:
    MODEL_NAME = os.environ.get("YAAYA_MODEL", "distilgpt2")
    generator = pipeline("text-generation", model=MODEL_NAME, device=-1)
    MODEL_READY = True
    print(f"✅ Model '{MODEL_NAME}' loaded successfully.")
except Exception as e:
    print("⚠️ Could not load model, switching to rule-based mode:", e)
    generator = None
    MODEL_READY = False


# =========================
#  RULE-BASED FALLBACK LOGIC
# =========================
def rule_based_reply(message):
    msg = message.lower()

    if any(word in msg for word in ["who made you", "who built you", "who created you", "who is your maker", "your creator", "who developed you"]):
        return "I was created by YAAYA, sponsored by UNI ABUJA."
    elif "your name" in msg:
        return "My name is YAAYA AI — your digital assistant, sponsored by UNI ABUJA."
    elif any(greet in msg for greet in ["hi", "hello", "hey"]):
        return "Hello there! I’m YAAYA AI — how may I assist you today?"
    elif "how are you" in msg:
        return "I’m doing great and fully operational! Thanks for asking 🙂"
    elif "thank" in msg:
        return "You’re always welcome 💫"
    else:
        return "I’m running in lightweight mode right now — but I can still chat with you smoothly 🙂."


# =========================
#  CHAT ENDPOINT
# =========================
@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "").strip()
    if not user_message:
        return jsonify({"response": "Please say something first 😊"})

    # Append user message to memory
    chat_history.append({"role": "user", "content": user_message})

    # --- Rule-based mode ---
    if not MODEL_READY:
        response_text = rule_based_reply(user_message)
    else:
        # Build conversation context
        context = "\n".join([f"User: {msg['content']}" for msg in chat_history[-5:]])
        prompt = f"{context}\nYAAYA:"

        try:
            result = generator(prompt, max_length=100, num_return_sequences=1, do_sample=True, temperature=0.8)
            response_text = result[0]['generated_text'].split("YAAYA:")[-1].strip()
        except Exception as e:
            print("⚠️ Model generation error:", e)
            response_text = rule_based_reply(user_message)

    # Save bot response
    chat_history.append({"role": "assistant", "content": response_text})

    return jsonify({"response": response_text})


# =========================
#  FRONTEND
# =========================
@app.route("/")
def index():
    return render_template("index.html")


# =========================
#  MAIN ENTRY
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
