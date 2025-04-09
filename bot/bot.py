import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# from config import TELEGRAM_BOT_TOKEN
from bot.handlers import start, leaderboard, handle_answer

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Create the bot application
app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

# Add command handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("leaderboard", leaderboard))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))

if __name__ == "__main__":
    logger.info("Starting bot...")
    app.run_polling()
