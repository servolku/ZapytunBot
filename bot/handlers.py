import math
import sys
import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.models import get_or_create_user, update_score, get_leaderboard

# Ініціалізація сесій користувачів
USER_SESSION = {}

def calculate_distance(lat1, lon1, lat2, lon2):
    """Обчислює відстань між двома точками (в метрах) за допомогою формули Гаверсина."""
    R = 6371000  # Радіус Землі в метрах
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє геолокацію, яку надсилає користувач."""
    user_location = update.message.location
    if not user_location:
        await update.message.reply_text("❌ Ви не надали геолокацію. Спробуйте ще раз.")
        return

    user_lat = user_location.latitude
    user_lon = user_location.longitude

    # Завантажуємо питання
    questions = load_questions()
    user_id = update.effective_user.id

    # Переконайтеся, що сесія користувача існує
    if user_id not in USER_SESSION:
        await update.message.reply_text("❌ Помилка: Сесія не знайдена.")
        return

    question_index = USER_SESSION[user_id]["current_question"]
    if question_index >= len(questions):
        await update.message.reply_text("❌ Завдання завершені. Почніть нову гру.")
        return

    # Отримуємо координати з питання
    target_question = questions[question_index]
    target_lat = target_question.get("latitude")
    target_lon = target_question.get("longitude")

    if target_lat is None or target_lon is None:
        await update.message.reply_text("❌ Для цього питання не задано координат.")
        return

    # Перевіряємо відстань
    distance = calculate_distance(user_lat, user_lon, target_lat, target_lon)
    if distance <= 20:
        await update.message.reply_text("✅ Ви знаходитесь у правильному місці! Отримуєте питання...")
        await ask_question(update, context)
    else:
        await update.message.reply_text(f"❌ Ви занадто далеко від місця. Будь ласка, підійдіть ближче. Відстань: {distance:.2f} метрів.")

def load_questions():
    """Динамічно завантажує файл питань."""
    file_path = "bot/questions.json"
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл {file_path} не знайдено!")
    with open(file_path, "r") as f:
        questions = json.load(f)
        print(f"Питання завантажені: {questions}")  # Додайте це для перевірки
        return questions

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
     """Обробляє команду /start."""
     from telegram import KeyboardButton, ReplyKeyboardMarkup
     
     user = update.effective_user
     get_or_create_user(user.id, user.first_name)
     
     # Додаємо кнопку для запиту геолокації
     keyboard = [
         [KeyboardButton("Отримати питання", request_location=True)]
     ]
     reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
     
     await update.message.reply_text(
         f"Привіт, {user.first_name}! Готовий розпочати квест?\n"
         "Натисни 'Отримати питання', щоб продовжити.",
         reply_markup=reply_markup
     )

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        if update.message:
            await update.message.reply_text(
                f"Гра завершена! Твій підсумковий результат: {USER_SESSION[user_id]['score']} балів."
            )
        elif update.callback_query:
            await update.callback_query.message.reply_text(
                f"Гра завершена! Твій підсумковий результат: {USER_SESSION[user_id]['score']} балів."
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
    if update.message:
        await update.message.reply_text(question["question"], reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(question["question"], reply_markup=reply_markup)

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
    await ask_question(update, context)
