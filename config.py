# config.py
import os

# Telegram Bot Token
# Рекомендується зберігати токен у змінній оточення та отримувати його за допомогою os.getenv
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не встановлено. Будь ласка, додайте токен до змінних оточення.")

# Database Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Абсолютний шлях до кореневої папки проекту
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'quest_bot.db')}"

# Web Application URL
WEB_APP_URL = "http://localhost:8000"
