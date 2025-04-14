import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))


from flask import Flask, render_template
from database.models import get_leaderboard

app = Flask(__name__)

@app.route("/")
def home():
    leaderboard_data = get_leaderboard()
    return render_template("index.html", bot_name="ZapytunBot", leaderboard=leaderboard_data)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
