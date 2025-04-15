import sys
import os
import json
import logging
from geopy.distance import geodesic  # Для перевірки дистанції
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.models import get_or_create_user, update_score, get_leaderboard

# Налаштування логування
logger = logging.getLogger(__name__)

# Ініціалізація сесій користувачів
USER_SESSION = {}

def load_questions():
    """Динамічно завантажує файл питань."""
    file_path = "bot/questions.json"
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл {file_path} не знайдено!")
    with open(file_path, "r") as f:
        questions = json.load(f)
        return questions

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє команду /start."""
    logger.info(f"Received /start command from user: {update.effective_user.id}")
    user = update.effective_user
    get_or_create_user(user.id, user.first_name)
    await update.message.reply_text(
        f"Привіт, {user.first_name}! Готовий розпочати квест?\n"
        "Натисни кнопку нижче, щоб отримати питання.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("ОТРИМАТИ ПИТАННЯ", callback_data="get_question")]
        ])
    )

async def handle_get_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє натискання кнопки 'ОТРИМАТИ ПИТАННЯ'."""
    query = update.callback_query
    await query.answer()

    # Надіслати запит на геолокацію
    await query.message.reply_text(
        "Будь ласка, надішліть вашу геолокацію, щоб отримати питання.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Надіслати геолокацію", request_location=True)]
        ])
    )

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє геолокацію, яку надсилає користувач."""
    user_location = update.message.location
    if not user_location:
        await update.message.reply_text("❌ Ви не надали геолокацію. Спробуйте ще раз.")
        return

    user_id = update.effective_user.id

    # Ініціалізація сесії, якщо її немає
    if user_id not in USER_SESSION:
        USER_SESSION[user_id] = {"current_question": 0, "score": 0}

    # Завантажуємо питання
    questions = load_questions()
    question_index = USER_SESSION[user_id]["current_question"]

    # Перевіряємо, чи є ще питання
    if question_index >= len(questions):
        await update.message.reply_text(
            "Завдання завершені. Почніть нову гру."
        )
        return

    # Обробляємо координати
    target_question = questions[question_index]
    target_lat = target_question.get("latitude")
    target_lon = target_question.get("longitude")

    if target_lat is None or target_lon is None:
        await update.message.reply_text("❌ Для цього питання не задано координат.")
        return

    # Перевіряємо відстань до цільової точки
    user_coords = (user_location.latitude, user_location.longitude)
    target_coords = (target_lat, target_lon)

    distance = geodesic(user_coords, target_coords).meters
    if distance > 20:
        await update.message.reply_text(
            f"❌ Ви занадто далеко від цільової точки. Відстань: {distance:.2f} метрів. Підходьте ближче!"
        )
        return

    # Якщо користувач в межах 20 метрів, надсилаємо питання
    options = target_question["options"]
    keyboard = [
        [InlineKeyboardButton(option, callback_data=str(idx))]
        for idx, option in enumerate(options)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"✅ Ви на правильному місці! Ось ваше питання:\n\n{target_question['question']}",
        reply_markup=reply_markup
    )
