import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))


from flask import Flask, render_template
from database.models import get_leaderboard
from database.models import SessionLocal, User

app = Flask(__name__)

@app.route("/test_db")
def test_db_connection():
    session = SessionLocal()
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

@app.route("/")
def home():
    leaderboard_data = get_leaderboard()
    print("Leaderboard data:", leaderboard_data)  # Додайте цей рядок
    return render_template("index.html", bot_name="ZapytunBot", leaderboard=leaderboard_data)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
