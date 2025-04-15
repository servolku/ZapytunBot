import os
import logging
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import asyncio
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/../"))

# Імпортуємо обробники
from handlers import start, leaderboard, handle_answer, handle_location, handle_button_click

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Ініціалізація бота
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set! Перевірте змінні середовища.")
bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def remove_webhook():
    try:
        webhook_deleted = await bot.delete_webhook(drop_pending_updates=True)
        if webhook_deleted:
            logging.info("Webhook successfully deleted.")
        else:
            logging.warning("Webhook was not active or could not be deleted.")
    except Exception as e:
        logging.error(f"Error while removing webhook: {e}")

# Налаштування логування
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Створення додатка
app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

# Додаємо обробники команд
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("leaderboard", leaderboard))
app.add_handler(CallbackQueryHandler(handle_button_click, pattern="get_question"))
app.add_handler(CallbackQueryHandler(handle_answer))
app.add_handler(MessageHandler(filters.LOCATION, handle_location))

# Головна функція для запуску бота
def main():
    logger.info("Starting bot...")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(remove_webhook())
    except Exception as e:
        logger.error(f"Error while removing webhook: {e}")

    try:
        app.run_polling()
    except Exception as e:
        logger.error(f"Error while running polling: {e}")

if __name__ == "__main__":
    main()
