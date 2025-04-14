import os
import logging
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters

import asyncio  # Додано для явної роботи з asyncio

import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/../"))

# Імпортуємо обробники
from handlers import start, leaderboard, handle_answer, handle_location

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Ініціалізація бота
bot = Bot(token=TELEGRAM_BOT_TOKEN)

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
app.add_handler(CommandHandler("leaderboard", leaderboard))

# Додаємо обробник для обробки відповідей користувача через callback_query
app.add_handler(CallbackQueryHandler(handle_answer))

# Додаємо обробник для обробки геолокації
app.add_handler(MessageHandler(filters.LOCATION, handle_location))

# Головна асинхронна функція
async def main():
    logger.info("Starting bot...")
    await remove_webhook()  # Видалення вебхука перед запуском
    await app.run_polling()  # Запуск polling

if __name__ == "__main__":
    asyncio.run(main())  # Запуск головної асинхронної функції
