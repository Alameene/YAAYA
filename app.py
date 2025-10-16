from flask import Flask, render_template, request, jsonify, make_response
from transformers import pipeline
import re, uuid, os

# --- Simple in-memory session store (not persistent across restarts) ---
SESSIONS = {}
MAX_HISTORY = 8  # how many past messages to keep for context

# --- Creator intent patterns (broad) ---
CREATOR_PATTERNS = re.compile(r"((who|who's|who is|whom).*(create|made|built|developed|author|authored|program|sponsor|sponsored|behind|owner|founder|origin))|((created|made|built|developed).*(you|the bot|this bot))|(who (created|made|built) (you|this))", re.I)

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.secret_key = os.environ.get("FLASK_SECRET", "change_this_secret_for_prod")

# --- Load lightweight model (distilgpt2 by default for easier deployment) ---
# If you want a stronger model, change model name to 'gpt2' or another Hugging Face model.
MODEL_NAME = os.environ.get("YAAYA_MODEL", "distilgpt2")
generator = pipeline("text-generation", model=MODEL_NAME, device=-1)

def detect_creator_intent(text):
    return bool(CREATOR_PATTERNS.search(text))

def generate_reply(prompt, max_new_tokens=80):
    # Simple generation wrapper. We keep responses brief to save resources.
    out = generator(prompt, max_new_tokens=max_new_tokens, do_sample=True, top_k=50, top_p=0.95, num_return_sequences=1)
    # The pipeline returns a list with 'generated_text'
    gen_text = out[0]['generated_text']
    # If model repeats prompt, try to strip prompt from result (best effort)
    if gen_text.startswith(prompt):
        reply = gen_text[len(prompt):].strip()
    else:
        reply = gen_text.strip()
    # Fallback
    if not reply:
        reply = "I'm here, but I didn't find an answer. Could you ask another way?"
    return reply

@app.route("/")
def index():
    resp = make_response(render_template("index.html"))
    # Ensure client has a session id cookie so we can track session memory server-side
    sid = request.cookies.get("yaaya_sid")
    if not sid:
        sid = str(uuid.uuid4())
        resp.set_cookie("yaaya_sid", sid, httponly=True, samesite='Lax')
        SESSIONS[sid] = {"history": []}
    else:
        if sid not in SESSIONS:
            SESSIONS[sid] = {"history": []}
    return resp

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    text = data.get("message", "").strip()
    if not text:
        return jsonify({"error": "No message provided."}), 400

    sid = request.cookies.get("yaaya_sid")
    if not sid:
        sid = str(uuid.uuid4())
        SESSIONS[sid] = {"history": []}

    # Creator intent handling (robust to phrasing)
    if detect_creator_intent(text):
        reply = "I was created by YAAYA, sponsored by UNI ABUJA."
        # store into history
        SESSIONS.setdefault(sid, {"history": []})["history"].append({"role": "user", "text": text})
        SESSIONS[sid]["history"].append({"role": "assistant", "text": reply})
        # cap history
        SESSIONS[sid]["history"] = SESSIONS[sid]["history"][-MAX_HISTORY*2:]
        return jsonify({"reply": reply})

    # Build a short context prompt using the last few messages
    history = SESSIONS.setdefault(sid, {"history": []})["history"]
    prompt = ""
    if history:
        for item in history[-MAX_HISTORY*2:]:
            role = item.get("role")
            t = item.get("text")
            if role == "user":
                prompt += f"User: {t}\n"
            else:
                prompt += f"Assistant: {t}\n"
    prompt += f"User: {text}\nAssistant:"

    # Generate reply
    try:
        reply = generate_reply(prompt, max_new_tokens=80)
    except Exception as e:
        # Fallback short answer
        reply = "Sorry, I'm having trouble thinking right now. Try again in a moment."

    # Save history
    history.append({"role": "user", "text": text})
    history.append({"role": "assistant", "text": reply})
    SESSIONS[sid]["history"] = history[-MAX_HISTORY*2:]

    return jsonify({"reply": reply})

if __name__ == "__main__":
    # local debug
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
