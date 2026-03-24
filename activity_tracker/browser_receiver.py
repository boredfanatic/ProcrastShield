from flask import Flask, request
import json
import os
from datetime import datetime

app = Flask(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data_storage")
DATA_DIR = os.path.abspath(DATA_DIR)
os.makedirs(DATA_DIR, exist_ok=True)

ACTIVITY_FILE = os.path.join(DATA_DIR, "activity_log.json")

last_domain = None

def is_valid_domain(domain):
    if not domain:
        return False
    domain = domain.lower()
    invalid_keywords = ["extensions", "startpageshared", "newtab", "localhost"]
    if any(k in domain for k in invalid_keywords):
        return False
    if "." not in domain:
        return False
    return True

@app.route("/tab", methods=["POST"])
def receive_tab():
    global last_domain
    data = request.json
    domain = data.get("domain")
    if not is_valid_domain(domain):
        return {"status": "ignored"}
    if domain == last_domain:
        return {"status": "duplicate"}
    last_domain = domain
    entry = {"type": "web", "name": domain, "timestamp": str(datetime.now())}
    with open(ACTIVITY_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"Browser: {domain}")
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(port=5000)  # localhost only