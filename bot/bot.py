import os
import logging
import asyncio
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/../"))

# 1. СТВОРІТЬ ТАБЛИЦІ ДО ІМПОРТУ HANDLERS!
from database.models import create_tables
create_tables()

from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from quest_admin import create_quest_start, create_quest_message_handler

# Тепер імпортуйте обробники
from handlers import start, show_leaderboard, handle_answer, handle_location, handle_get_question, handle_choose_quest

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

# Додаємо обробник для вибору квесту
from telegram.ext import MessageHandler, filters

def choose_quest_filter(message):
    # Дозволяємо вибирати квест, якщо в context.user_data["open_quests"] є такий квест
    context = message.application.context_types.context  # Отримуємо context
    user_data = context.user_data
    open_quests = user_data.get("open_quests", []) if user_data else []
    return bool(open_quests) and any(q["quest_name"] == message.text for q in open_quests)

choose_quest_filter = filters.TEXT & filters.Create(choose_quest_filter)

# Додаємо обробник для кнопки "ОТРИМАТИ ПИТАННЯ"
app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Отримати питання$"), handle_get_question))

app.add_handler(MessageHandler(choose_quest_filter, handle_choose_quest))


# Додаємо обробники команд
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("leaderboard", show_leaderboard))
app.add_handler(CommandHandler("create_quest", create_quest_start))

# Додаємо обробники для створення квестів
app.add_handler(MessageHandler(filters.TEXT, create_quest_message_handler))



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
