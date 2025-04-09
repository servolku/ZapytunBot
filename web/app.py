from flask import Flask, render_template
from database.models import get_leaderboard

app = Flask(__name__)

@app.route("/")
def leaderboard():
    """Render the leaderboard page."""
    leaderboard_data = get_leaderboard()
    return render_template("leaderboard.html", leaderboard=leaderboard_data)

if __name__ == "__main__":
    app.run(debug=True)