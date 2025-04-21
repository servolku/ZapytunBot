import sys
import os
import json
import glob
import logging
import math
import random
from datetime import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import ContextTypes
from database.models import (
    get_or_create_user,
    start_quest_for_user,
    finish_quest_for_user,
    get_leaderboard_for_quest
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

USER_SESSION = {}

QUESTS_DIR = os.path.join("bot", "quests")

def get_open_quests():
    open_quests = []
    for quest_path in glob.glob(os.path.join(QUESTS_DIR, "*/questions.json")):
        with open(quest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if data.get("is_open"):
                open_quests.append({
                    "quest_id": data["quest_id"],
                    "quest_name": data.get("quest_name", data["quest_id"]),
                    "description": data.get("description", ""),
                    "path": quest_path
                })
    return open_quests

def load_questions_for_user(user_id):
    user = USER_SESSION.get(user_id, {})
    questions_path = user.get("questions_path")
    if not questions_path or not os.path.exists(questions_path):
        raise FileNotFoundError(f"Файл {questions_path} не знайдено!")
    with open(questions_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received /start command from user: {update.effective_user.id}")
    user = update.effective_user
    get_or_create_user(user.id, user.first_name)
    USER_SESSION[user.id] = {}

    open_quests = get_open_quests()
    if not open_quests:
        await update.message.reply_text("Немає відкритих квестів для проходження наразі.")
        return

    # Зберігаємо список квестів у context.user_data
    context.user_data["open_quests"] = open_quests

    # Формуємо кнопки зі списком квестів
    keyboard = [
        [quest["quest_name"]] for quest in open_quests
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    quest_list_text = "Оберіть квест для проходження:\n\n"
    for quest in open_quests:
        quest_list_text += f"• <b>{quest['quest_name']}</b>\n{quest['description']}\n\n"
    await update.message.reply_text(
        quest_list_text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    USER_SESSION[user.id]["state"] = "CHOOSE_QUEST"

async def handle_choose_quest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
	
    quest_name = update.message.text
    # Знайти квест за ім’ям у context.user_data["open_quests"]
    quest = next((q for q in context.user_data["open_quests"] if q["quest_name"] == quest_name), None)
    if not quest:
        await update.message.reply_text("Квест не знайдено.")
        return

    # Завантажити питання цього квесту (шлях до questions.json)
    with open(quest["file_path"], "r", encoding="utf-8") as f:
        data = json.load(f)
    questions = data["questions"]
    random_order = data.get("random_order", False)

    if random_order:
        indices = list(range(len(questions)))
        random.shuffle(indices)
    else:
        indices = list(range(len(questions)))

    USER_SESSION[user_id]["current_question"] = 0
    USER_SESSION[user_id]["score"] = 0
    USER_SESSION[user_id]["order"] = indices
    USER_SESSION[user_id]["questions"] = questions
    USER_SESSION[user_id]["quest_id"] = data["quest_id"]
    USER_SESSION[user_id]["state"] = "IN_QUEST"

    # Старт для бд
    start_quest_for_user(user_id, data["quest_id"], update.effective_user.first_name)
    main_keyboard = ReplyKeyboardMarkup(
        [["Отримати питання"]],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    await update.message.reply_text(
        f"Ви обрали квест: «{quest_name}»\nНатисніть 'Отримати питання', щоб почати.",
        reply_markup=main_keyboard
    )

async def handle_get_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in USER_SESSION or USER_SESSION[user_id].get("state") != "IN_QUEST":
        await update.message.reply_text("Спочатку оберіть квест через /start.")
        return

    data = load_questions_for_user(user_id)
    questions = data["questions"]
    question_index = USER_SESSION[user_id]["current_question"]
    order = USER_SESSION[user_id].get("order", list(range(len(questions))))  # <--- дістаємо порядок

    if question_index >= len(questions):
        await update.message.reply_text("Всі питання завершені. Щоб почати знову, натисніть /start.")
        return

    real_question_idx = order[question_index]  # <--- тут!
    question = questions[real_question_idx]

    location_keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("Надіслати геолокацію", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await update.message.reply_text(
        "Будь ласка, надішліть вашу геолокацію.",
        reply_markup=location_keyboard
    )

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_location = update.message.location
    user_id = update.effective_user.id

    if not user_location:
        await update.message.reply_text("❌ Ви не надали геолокацію. Спробуйте ще раз.")
        return

    if user_id not in USER_SESSION or USER_SESSION[user_id].get("state") != "IN_QUEST":
        await update.message.reply_text("Спочатку оберіть квест через /start.")
        return

    data = load_questions_for_user(user_id)
    questions = data["questions"]
    question_index = USER_SESSION[user_id]["current_question"]
    order = USER_SESSION[user_id].get("order", list(range(len(questions))))
    real_question_idx = order[question_index]
    target_question = questions[real_question_idx]

    target_lat = target_question.get("latitude")
    target_lon = target_question.get("longitude")

    if not target_lat or not target_lon:
        await update.message.reply_text("❌ Для цього питання не задано координат.")
        return

    distance = haversine(user_location.latitude, user_location.longitude, target_lat, target_lon)
    if distance <= 20000:
        options = target_question["options"]
        keyboard = [
            [InlineKeyboardButton(option, callback_data=str(idx))]
            for idx, option in enumerate(options)
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Надсилаємо зображення питання, якщо є
        quest_dir = os.path.dirname(USER_SESSION[user_id]["questions_path"])
        question_image = target_question.get("question_image")
        if question_image:
            image_path = os.path.join(quest_dir, question_image)
            if os.path.exists(image_path):
                with open(image_path, "rb") as photo:
                    await update.message.reply_photo(photo=photo, caption=target_question["question"], reply_markup=reply_markup)
                return  # питання вже відправлено з картинкою

        await update.message.reply_text(target_question["question"], reply_markup=reply_markup)
    else:
        await update.message.reply_text(
            f"❌ Ви не знаходитеся в потрібній локації. Ваша відстань до цілі: {int(distance)} м. Спробуйте ще раз."
        )

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if user_id not in USER_SESSION or USER_SESSION[user_id].get("state") != "IN_QUEST":
        await query.edit_message_text(text="❌ Помилка: Сесія не знайдена або ви не обрали квест.")
        return

    data = load_questions_for_user(user_id)
    questions = data["questions"]
    quest_id = data.get("quest_id", "default-quest")
    question_index = USER_SESSION[user_id]["current_question"]
    order = USER_SESSION[user_id].get("order", list(range(len(questions))))
    real_question_idx = order[question_index]
    question = questions[real_question_idx]

    if int(query.data) == question["correct"]:
        USER_SESSION[user_id]["score"] += 1
        response = "✅ Правильно!"
    else:
        response = "❌ Неправильно!"

    if hasattr(query.message, "photo") and query.message.photo:
        await query.edit_message_caption(caption=response)
    else:
        await query.edit_message_text(text=response)

    # Показуємо зображення місцевості для наступної точки (якщо є)
    after_answer_image = question.get("after_answer_image")
    quest_dir = os.path.dirname(USER_SESSION[user_id]["questions_path"])
    if after_answer_image:
        image_path = os.path.join(quest_dir, after_answer_image)
        if os.path.exists(image_path):
            with open(image_path, "rb") as photo:
                await query.message.reply_photo(photo=photo, caption="Ось місце наступної точки!")

    USER_SESSION[user_id]["current_question"] += 1

    if USER_SESSION[user_id]["current_question"] >= len(questions):
        # Фінішуємо квест для користувача
        finish_quest_for_user(
            user_id,
            quest_id,
            USER_SESSION[user_id]["score"]
        )
        await query.message.reply_text(
            f"Квест завершено! Твій підсумковий результат: {USER_SESSION[user_id]['score']} балів.\n"
            "Щоб пройти ще раз — натисни /start."
        )
        del USER_SESSION[user_id]
    else:
        await query.message.reply_text("Перейдіть до наступної локації та натисніть \"Надіслати геолокацію\".")

async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in USER_SESSION or "questions_path" not in USER_SESSION[user_id]:
        await update.message.reply_text("Спочатку оберіть квест через /start.")
        return
    data = load_questions_for_user(user_id)
    quest_id = data.get("quest_id", "default-quest")
    quest_name = data.get("quest_name", "Квест")
    leaderboard_data = get_leaderboard_for_quest(quest_id)
    leaderboard_text = f"🏆 Дошка переможців для «{quest_name}» 🏆\n\n"
    if not leaderboard_data:
        leaderboard_text += "Немає учасників."
    else:
        for idx, (name, score, duration) in enumerate(leaderboard_data, start=1):
            mins = int(duration) // 60
            secs = int(duration) % 60
            time_str = f"{mins} хв {secs} сек"
            leaderboard_text += f"{idx}. {name}: {score} балів, час: {time_str}\n"
    await update.message.reply_text(leaderboard_text)

# --- ДОДАЙТЕ у bot/bot.py ---
# app.add_handler(MessageHandler(filters.TEXT, handle_choose_quest))
# Цей хендлер має бути доданий ПЕРЕД обробником "Отримати питання", щоб вибір квесту спрацьовував правильно!
