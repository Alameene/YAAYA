# YAAYA AI — Flask Chatbot

This project is a lightweight Flask-based chatbot using the `transformers` library (DistilGPT2 by default) for generation. It includes a responsive, techy UI with browser-based voice input and text-to-speech output.

## Quick notes
- Default model: `distilgpt2` (good balance between quality and memory). Change model with env var `YAAYA_MODEL`.
- The model will be downloaded on first run on the host (Render or local). Do **not** include model files in the repo — letting the host download them keeps the repo small.
- If you get memory issues on Render, switch to `distilgpt2` (already default) or set `YAAYA_MODEL=distilgpt2` in Render environment settings.

## Local run
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
# then visit http://localhost:5000
```

## Deploying to Render
1. Push this repo to GitHub.
2. Create a new Web Service on Render, connect your GitHub repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Optionally set environment variable `YAAYA_MODEL` to select a different HF model.

## Creator response
The bot uses pattern detection so that any phrasing of creator/sponsor questions (\"who made you\", \"who's behind you\", \"who sponsored you\") will return: **\"I was created by YAAYA, sponsored by UNI ABUJA.\"**

## Troubleshooting
- First model download can be large and may take a few minutes.
- If Render's deployment fails due to memory, try using a smaller model or reduce generation length in `app.py`.
