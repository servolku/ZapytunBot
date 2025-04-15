import sys
import os
import json
import logging
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
        questions = json.load(f)
        return questions

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє команду /start."""
    logger.info(f"Received /start command from user: {update.effective_user.id}")
    user = update.effective_user
    get_or_create_user(user.id, user.first_name)

    # Додаємо постійну кнопку "Отримати питання"
    main_keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("Отримати питання")]],
        resize_keyboard=True,
        one_time_keyboard=False
    )

    await update.message.reply_text(
        f"Привіт, {user.first_name}! Готовий розпочати квест?\n"
        "Натисни 'Отримати питання', щоб почати.",
        reply_markup=main_keyboard
    )

async def handle_get_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє запит на отримання питання."""
    # Створюємо клавіатуру для запиту геолокації
    location_keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("Надіслати геолокацію", request_location=True)]],
        resize_keyboard=True,  # Робить клавіатуру компактнішою
        one_time_keyboard=True  # Клавіатура зникне після вибору
    )

    # Надсилаємо повідомлення з клавіатурою для геолокації
    await update.message.reply_text(
        "Будь ласка, надішліть вашу геолокацію, щоб отримати питання.",
        reply_markup=location_keyboard
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

    # Перевірка успішності
    await update.message.reply_text("✅ Ваші координати отримано! Продовжуйте.")
