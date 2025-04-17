import sys
import os
import json
import logging
import math
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from database.models import get_or_create_user, update_score, get_leaderboard

# Ініціалізація логера
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Ініціалізація сесій користувачів
USER_SESSION = {}

def load_questions():
    """Динамічно завантажує файл питань."""
    file_path = "bot/questions.json"
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл {file_path} не знайдено!")
    with open(file_path, "r") as f:
        data = json.load(f)
        return data

def haversine(lat1, lon1, lat2, lon2):
    """Обчислює відстань між двома точками (GPS) у метрах."""
    R = 6371000  # Радіус Землі в метрах
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

    questions_data = load_questions()
    quest_name = questions_data.get("quest_name", "Квест")

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
    """Обробляє запит на отримання питання."""
    user_id = update.effective_user.id

    # Перевіряємо, чи є активна сесія для користувача
    if user_id not in USER_SESSION:
        USER_SESSION[user_id] = {"current_question": 0, "score": 0}

    # Завантажуємо питання
    questions = load_questions()
    question_index = USER_SESSION[user_id]["current_question"]

    # Перевіряємо, чи є ще питання
    if question_index >= len(questions):
        await update.message.reply_text(
            "Всі питання завершені. Щоб почати знову, натисніть /start."
        )
        return

    # Створюємо клавіатуру для запиту геолокації
    location_keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("Надіслати геолокацію", request_location=True)]],
        resize_keyboard=True,  # Робить клавіатуру компактнішою
        one_time_keyboard=True  # Клавіатура зникне після вибору
    )

    # Надсилаємо запит на геолокацію
    await update.message.reply_text(
        "Будь ласка, надішліть вашу геолокацію.",
        reply_markup=location_keyboard
    )

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє геолокацію, яку надсилає користувач."""
    user_location = update.message.location
    user_id = update.effective_user.id

    if not user_location:
        await update.message.reply_text("❌ Ви не надали геолокацію. Спробуйте ще раз.")
        return

    # Перевіряємо, чи є активна сесія для користувача
    if user_id not in USER_SESSION:
        USER_SESSION[user_id] = {"current_question": 0, "score": 0}

    # Завантажуємо питання
    questions = load_questions()
    question_index = USER_SESSION[user_id]["current_question"]

    # Перевіряємо, чи є ще питання
    if question_index >= len(questions):
        await update.message.reply_text(
            "Всі питання завершені. Щоб почати знову, натисніть /start."
        )
        return

    # Перевіряємо координати
    target_question = questions[question_index]
    target_lat = target_question.get("latitude")
    target_lon = target_question.get("longitude")

    if not target_lat or not target_lon:
        await update.message.reply_text("❌ Для цього питання не задано координат.")
        return

    distance = haversine(user_location.latitude, user_location.longitude, target_lat, target_lon)
    if distance <= 10:
        # Надсилаємо питання
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

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє команду /leaderboard."""
    leaderboard_data = get_leaderboard()
    leaderboard_text = "🏆 Дошка переможців 🏆\n\n"
    for idx, (name, score) in enumerate(leaderboard_data, start=1):
        leaderboard_text += f"{idx}. {name}: {score} балів\n"
    await update.message.reply_text(leaderboard_text)

async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє команду /leaderboard."""
    leaderboard_data = get_leaderboard()
    leaderboard_text = "🏆 Дошка переможців 🏆\n\n"
    for idx, (name, score) in enumerate(leaderboard_data, start=1):
        leaderboard_text += f"{idx}. {name}: {score} балів\n"
    await update.message.reply_text(leaderboard_text)

async def ask_question(update, context, new_session=False):
    """Відправляє наступне питання користувачу."""
    user_id = update.effective_user.id
    if new_session or user_id not in USER_SESSION:
        USER_SESSION[user_id] = {"current_question": 0, "score": 0}

    # Динамічно завантажуємо питання
    questions = load_questions()
    question_index = USER_SESSION[user_id]["current_question"]

    # Перевіряємо, чи є ще питання
    if question_index >= len(questions):
        await update.message.reply_text(
            f"Гра завершена! Твій підсумковий результат: {USER_SESSION[user_id]['score']} балів.\n"
            "Натисни 'Отримати питання', щоб почати знову."
        )
        update_score(user_id, USER_SESSION[user_id]["score"])
        del USER_SESSION[user_id]
        return

    question = questions[question_index]
    options = question["options"]

    # Створюємо клавіатуру для відповідей
    keyboard = [
        [InlineKeyboardButton(option, callback_data=str(idx))]
        for idx, option in enumerate(options)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Відправляємо питання користувачу
    await update.message.reply_text(question["question"], reply_markup=reply_markup)

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє відповідь користувача."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    # Переконайтеся, що сесія користувача існує
    if user_id not in USER_SESSION:
        await query.edit_message_text(text="❌ Помилка: Сесія не знайдена.")
        return

    # Динамічно завантажуємо питання
    questions = load_questions()
    question_index = USER_SESSION[user_id]["current_question"]
    question = questions[question_index]

    # Перевіряємо відповідь
    if int(query.data) == question["correct"]:
        USER_SESSION[user_id]["score"] += 1
        response = "✅ Правильно!"
    else:
        response = "❌ Неправильно!"

    # Оновлюємо текст повідомлення
    await query.edit_message_text(text=response)

    # Переходимо до наступного питання
    USER_SESSION[user_id]["current_question"] += 1
    await update.callback_query.message.reply_text("Перейдіть до наступної локації.")
