import sys
import os
import json
import glob

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from config import DATABASE_URL
from flask import Flask, render_template
from database.models import get_leaderboard_for_quest

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTS_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "bot", "quests"))

def get_open_quests():
    open_quests = []
    for quest_path in glob.glob(os.path.join(QUESTS_DIR, "*/questions.json")):
        with open(quest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if data.get("is_open"):
                open_quests.append({
                    "quest_id": data["quest_id"],
                    "quest_name": data.get("quest_name", data["quest_id"]),
                    "description": data.get("description", ""),
                })
    return open_quests

def format_duration(seconds):
    if seconds is None:
        return "-"
    minutes = int(seconds) // 60
    seconds = int(seconds) % 60
    return f"{minutes} хв {seconds} сек"

app = Flask(__name__)

@app.route("/")
def home():
    quests = get_open_quests()
    all_leaderboards = []
    for quest in quests:
        quest_id = quest["quest_id"]
        leaderboard = [
            (name, score, format_duration(duration))
            for name, score, duration in get_leaderboard_for_quest(quest_id)
        ]
        all_leaderboards.append({
            "quest_name": quest["quest_name"],
            "description": quest["description"],
            "leaderboard": leaderboard
        })
    return render_template(
        "index.html",
        bot_name="ZapytunBot",
        all_leaderboards=all_leaderboards
    )

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
