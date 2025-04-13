import os
import logging
from telegram import Update
from telegram import Bot

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# from config import TELEGRAM_BOT_TOKEN
# from bot.handlers import start, leaderboard, handle_answer
from handlers import start, leaderboard, handle_answer  # Якщо запускаєте з папки `bot/`

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# додав код  для видалення вебхуків
bot = Bot(token=TELEGRAM_BOT_TOKEN)
# Видалення вебхука
# bot.delete_webhook(drop_pending_updates=True)


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Видаляємо вебхук, якщо він активний
try:
    bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook deleted successfully.")
except Exception as e:
    logger.error(f"Failed to delete webhook: {e}")

# Create the bot application
app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

# Add command handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("leaderboard", leaderboard))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))

if __name__ == "__main__":
    logger.info("Starting bot...")
    app.run_polling()
