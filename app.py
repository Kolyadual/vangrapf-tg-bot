from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "ok", "service": "Video Downloader Bot", "author": "Kolyadual"})

@app.route('/health')
def health():
    return jsonify({"ok": True})
