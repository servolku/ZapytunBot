from flask import Flask, render_template
from database.models import get_leaderboard

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello, this is the Zapytun web app!"

def leaderboard():
    """Render the leaderboard page."""
    leaderboard_data = get_leaderboard()
    return render_template("leaderboard.html", leaderboard=leaderboard_data)

if __name__ == "__main__":
    # Використовуйте порт, який Render надає через змінну середовища PORT
    import os
    port = int(os.environ.get("PORT", 5000))  # За замовчуванням 5000
    app.run(host="0.0.0.0", port=port)
    app.run(debug=True)
