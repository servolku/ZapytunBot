import os
import logging
import asyncio
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/../"))

# Імпортуємо обробники
from handlers import start, show_leaderboard, handle_answer, handle_location, handle_get_question
from handlers import leaderboard

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Ініціалізація бота
bot = Bot(token=TELEGRAM_BOT_TOKEN)

from database.models import create_tables
create_tables()

# Асинхронне видалення вебхука
async def remove_webhook():
    webhook_deleted = await bot.delete_webhook(drop_pending_updates=True)
    if webhook_deleted:
        logging.info("Webhook successfully deleted.")
    else:
        logging.warning("Webhook was not active or could not be deleted.")

# Налаштування логування
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Створення додатка
app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

# Додаємо обробники команд
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("leaderboard", show_leaderboard))

# Додаємо обробник для кнопки "ОТРИМАТИ ПИТАННЯ"
#app.add_handler(CommandHandler("get_question", handle_get_question))
app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Отримати питання$"), handle_get_question))

# Додаємо обробник для геолокації
app.add_handler(MessageHandler(filters.LOCATION, handle_location))

# Додаємо обробник для відповідей через callback_query
app.add_handler(CallbackQueryHandler(handle_answer))

# Головна функція для запуску бота
def main():
    logger.info("Starting bot...")

    # Створення нового циклу подій для уникнення DeprecationWarning
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Видалення вебхука перед запуском
    loop.run_until_complete(remove_webhook())

    # Запуск polling
    app.run_polling()

if __name__ == "__main__":
    main()
