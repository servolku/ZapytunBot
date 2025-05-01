import os
import logging
import asyncio
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/../"))

from database.models import create_tables
create_tables()

from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from quest_admin import create_quest_start, create_quest_message_handler
from handlers import (
    start, show_leaderboard, handle_answer, handle_location,
    handle_get_question, handle_choose_quest, USER_SESSION
)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def remove_webhook():
    webhook_deleted = await bot.delete_webhook(drop_pending_updates=True)
    if (webhook_deleted):
        logging.info("Webhook successfully deleted.")
    else:
        logging.warning("Webhook was not active or could not be deleted.")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

# Команди
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("leaderboard", show_leaderboard))
app.add_handler(CommandHandler("create_quest", create_quest_start))

# "Отримати питання" — окремий!
app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Отримати питання$"), handle_get_question))

# ОДИН роутер для всіх інших текстових повідомлень!
async def text_router(update, context):
    user_id = update.effective_user.id

    # 1. Якщо користувач у процесі створення квесту
    if context.user_data.get("quest_create_state") is not None:
        await create_quest_message_handler(update, context)
        return

    # 2. Якщо користувач у стані вибору квесту
    if USER_SESSION.get(user_id, {}).get("state") == "CHOOSE_QUEST":
        await handle_choose_quest(update, context)
        return

    # 3. Якщо нічого з вище — дай підказку
    await update.message.reply_text("Надішліть команду /start або виберіть квест зі списку.")

app.add_handler(MessageHandler(filters.TEXT & (~filters.Regex("^Отримати питання$")), text_router))

# Геолокація
app.add_handler(MessageHandler(filters.LOCATION, handle_location))

# Callback answer
app.add_handler(CallbackQueryHandler(handle_answer))

def main():
    logger.info("Starting bot...")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(remove_webhook())
    app.run_polling()

if __name__ == "__main__":
    main()
