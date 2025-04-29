import os
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

# Завантаження списку адміністраторів
def load_admins():
    with open("bot/quest_admins.json", "r") as f:
        return json.load(f)["admins"]

ADMINS = load_admins()

QUESTS_DIR = os.path.join("bot", "quests")

# Початок створення квесту
async def create_quest_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        await update.message.reply_text("У вас немає прав для створення квесту.")
        return

    context.user_data["quest_create_state"] = "ASK_NAME"
    context.user_data["new_quest"] = {}
    await update.message.reply_text("Введіть назву для нового квесту:")

# FSM для створення квесту
async def create_quest_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("quest_create_state")

    if state == "ASK_NAME":
        context.user_data["new_quest"]["name"] = update.message.text
        context.user_data["quest_create_state"] = "ASK_DESCRIPTION"
        await update.message.reply_text("Введіть опис квесту:")

    elif state == "ASK_DESCRIPTION":
        context.user_data["new_quest"]["description"] = update.message.text
        context.user_data["quest_create_state"] = "ASK_QUESTIONS"
        await update.message.reply_text("Скільки питань буде в квесті? Введіть число:")

    elif state == "ASK_QUESTIONS":
        try:
            num_questions = int(update.message.text)
            context.user_data["new_quest"]["questions"] = []
            context.user_data["new_quest"]["num_questions"] = num_questions
            context.user_data["quest_create_state"] = "ADD_QUESTION"
            await update.message.reply_text("Введіть текст першого питання:")
        except ValueError:
            await update.message.reply_text("Будь ласка, введіть число.")

    elif state == "ADD_QUESTION":
        current_questions = context.user_data["new_quest"]["questions"]
        current_questions.append({"text": update.message.text})
        context.user_data["quest_create_state"] = "ASK_COORDINATES"
        await update.message.reply_text("Введіть координати питання у форматі: широта, довгота")

    elif state == "ASK_COORDINATES":
        try:
            lat, lon = map(float, update.message.text.split(","))
            context.user_data["new_quest"]["questions"][-1]["coordinates"] = {"lat": lat, "lon": lon}
            if len(context.user_data["new_quest"]["questions"]) < context.user_data["new_quest"]["num_questions"]:
                context.user_data["quest_create_state"] = "ADD_QUESTION"
                await update.message.reply_text(f"Введіть текст наступного питання ({len(context.user_data['new_quest']['questions']) + 1}):")
            else:
                context.user_data["quest_create_state"] = "FINISH"
                await update.message.reply_text("Квест створено! Зберігаємо...")
                await save_quest(update, context)
        except ValueError:
            await update.message.reply_text("Невірний формат координат. Введіть ще раз: широта, довгота")

# Збереження квесту
async def save_quest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quest = context.user_data["new_quest"]
    quest_id = quest["name"].replace(" ", "_").lower()
    quest_dir = os.path.join(QUESTS_DIR, quest_id)
    os.makedirs(quest_dir, exist_ok=True)

    with open(os.path.join(quest_dir, "questions.json"), "w", encoding="utf-8") as f:
        json.dump(quest, f, ensure_ascii=False, indent=4)

    await update.message.reply_text(f"Квест «{quest['name']}» успішно створено!")
    context.user_data.clear()
