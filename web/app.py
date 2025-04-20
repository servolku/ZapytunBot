import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from config import DATABASE_URL
from flask import Flask, render_template
from database.models import get_leaderboard_for_quest
from database.models import Session, User

app = Flask(__name__)

@app.route("/test_db")
def test_db_connection():
    session = Session()
    try:
        # Перевіряємо, чи є користувачі в базі даних
        users = session.query(User).all()
        print("Users in database:", users)
        return f"Users in database: {users}"
    except Exception as e:
        print("Database connection error:", e)
        return f"Database connection error: {e}"
    finally:
        session.close()

@app.route("/add_test_user")
def add_test_user():
    from database.models import get_or_create_user
    user = get_or_create_user(1, "Test User")
    return f"Added user: {user.name} with ID: {user.id}"

@app.route("/")
def home():
    quest_id = "quest1"
    leaderboard_data = [
        (name, score, format_duration(duration))
        for name, score, duration in get_leaderboard_for_quest(quest_id)
    ]
    print("DEBUG leaderboard_data:", leaderboard_data)
    with open("/tmp/flask_leaderboard.log", "a") as f:
        f.write(f"DEBUG leaderboard_data: {leaderboard_data}\n")
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
