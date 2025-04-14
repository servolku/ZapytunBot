# config.py

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = "8121382718:AAFYlfyE9jprJ1tw7Ppb0dPP5AAxxv4oNdQ"

# Database Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Абсолютний шлях до кореневої папки проекту
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'quest_bot.db')}"

# Web Application URL
WEB_APP_URL = "http://localhost:8000"
