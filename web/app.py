import sys
import os
import json

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from config import DATABASE_URL
from flask import Flask, render_template
from database.models import get_leaderboard_for_quest
from database.models import Session, User

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_PATH = os.path.join(BASE_DIR, "..", "bot", "questions.json")

def get_quest_id():
    with open(QUESTIONS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["quest_id"]

app = Flask(__name__)

@app.route("/")
def home():
    quest_id = get_quest_id()
    leaderboard_data = [
        (name, score, format_duration(duration))
        for name, score, duration in get_leaderboard_for_quest(quest_id)
    ]
    return render_template("index.html", bot_name="ZapytunBot", leaderboard=leaderboard_data)

def format_duration(seconds):
    if seconds is None:
        return "-"
    minutes = int(seconds) // 60
    seconds = int(seconds) % 60
    return f"{minutes} хв {seconds} сек"

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
