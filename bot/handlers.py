import sys
import os
import json
import logging
import math
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
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

def load_questions():
    file_path = "bot/questions.json"
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл {file_path} не знайдено!")
    with open(file_path, "r") as f:
        data = json.load(f)
        return data

def get_current_quest_id():
    data = load_questions()
    return data.get("quest_id", "default-quest")

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
    USER_SESSION[user.id] = {"current_question": 0, "score": 0}

    questions_data = load_questions()
    quest_id = questions_data.get("quest_id", "default-quest")
    quest_name = questions_data.get("quest_name", "Квест")

    # Зберігаємо старт квесту
    start_quest_for_user(user.id, quest_id, user.first_name)

    main_keyboard = ReplyKeyboardMarkup(
        [["Отримати питання"]],
        resize_keyboard=True,
        one_time_keyboard=False
    )

    await update.message.reply_text(
        f"Привіт, {user.first_name}! Готовий розпочати «{quest_name}»?\n"
        "Натисни 'Отримати питання', щоб почати.",
        reply_markup=main_keyboard
    )

async def handle_get_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in USER_SESSION:
        USER_SESSION[user_id] = {"current_question": 0, "score": 0}

    questions_data = load_questions()
    questions = questions_data["questions"]
    question_index = USER_SESSION[user_id]["current_question"]

    if question_index >= len(questions):
        await update.message.reply_text("Всі питання завершені. Щоб почати знову, натисніть /start.")
        return

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

    if user_id not in USER_SESSION:
        USER_SESSION[user_id] = {"current_question": 0, "score": 0}

    questions_data = load_questions()
    questions = questions_data["questions"]
    question_index = USER_SESSION[user_id]["current_question"]

    if question_index >= len(questions):
        await update.message.reply_text("Всі питання завершені. Щоб почати знову, натисніть /start.")
        return

    target_question = questions[question_index]
    target_lat = target_question.get("latitude")
    target_lon = target_question.get("longitude")

    if not target_lat or not target_lon:
        await update.message.reply_text("❌ Для цього питання не задано координат.")
        return

    distance = haversine(user_location.latitude, user_location.longitude, target_lat, target_lon)
    if distance <= 10:
        options = target_question["options"]
        keyboard = [
            [InlineKeyboardButton(option, callback_data=str(idx))]
            for idx, option in enumerate(options)
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(target_question["question"], reply_markup=reply_markup)
    else:
        await update.message.reply_text(
            f"❌ Ви не знаходитеся в потрібній локації. Ваша відстань до цілі: {int(distance)} м. Спробуйте ще раз."
        )

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if user_id not in USER_SESSION:
        await query.edit_message_text(text="❌ Помилка: Сесія не знайдена.")
        return

    questions_data = load_questions()
    questions = questions_data["questions"]
    quest_id = questions_data.get("quest_id", "default-quest")
    question_index = USER_SESSION[user_id]["current_question"]
    question = questions[question_index]

    if int(query.data) == question["correct"]:
        USER_SESSION[user_id]["score"] += 1
        response = "✅ Правильно!"
    else:
        response = "❌ Неправильно!"

    await query.edit_message_text(text=response)

    USER_SESSION[user_id]["current_question"] += 1

    if USER_SESSION[user_id]["current_question"] >= len(questions):
        # Фінішуємо квест для користувача
        finish_quest_for_user(
            user_id,
            quest_id,
            USER_SESSION[user_id]["score"]
        )
        await update.callback_query.message.reply_text(
            f"Квест завершено! Твій підсумковий результат: {USER_SESSION[user_id]['score']} балів.\n"
            "Щоб пройти ще раз — натисни /start."
        )
        del USER_SESSION[user_id]
    else:
        await update.callback_query.message.reply_text("Перейдіть до наступної локації.")

async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    questions_data = load_questions()
    quest_id = questions_data.get("quest_id", "default-quest")
    quest_name = questions_data.get("quest_name", "Квест")
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
