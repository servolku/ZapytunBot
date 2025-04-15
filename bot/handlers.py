import sys
import os
import json
import logging
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
        logger.error(f"Файл {file_path} не знайдено!")
        raise FileNotFoundError(f"Файл {file_path} не знайдено!")
    try:
        with open(file_path, "r") as f:
            questions = json.load(f)
            return questions
    except Exception as e:
        logger.error(f"Error while loading questions: {e}")
        raise

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        logger.info(f"Received /start command from user: {update.effective_user.id}")
        user = update.effective_user
        get_or_create_user(user.id, user.first_name)
        await update.message.reply_text(
            f"Привіт, {user.first_name}! Готовий розпочати квест?\n"
            "Відповідай на запитання, щоб заробити бали!"
        )
        await ask_question(update, context, new_session=True)
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await update.message.reply_text("❌ Виникла помилка. Спробуйте ще раз.")

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє команду /leaderboard."""
    try:
        leaderboard_data = get_leaderboard()
        leaderboard_text = "🏆 Дошка переможців 🏆\n\n"
        for idx, (name, score) in enumerate(leaderboard_data, start=1):
            leaderboard_text += f"{idx}. {name}: {score} балів\n"
        await update.message.reply_text(leaderboard_text)
    except Exception as e:
        logger.error(f"Error in leaderboard command: {e}")
        await update.message.reply_text("❌ Виникла помилка при завантаженні дошки переможців.")

async def ask_question(update, context, new_session=False):
    """Відправляє наступне питання користувачу."""
    try:
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
    except Exception as e:
        logger.error(f"Error in ask_question function: {e}")
        await update.message.reply_text("❌ Виникла помилка при завантаженні питання.")

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє відповідь користувача."""
    try:
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
    except Exception as e:
        logger.error(f"Error in handle_answer function: {e}")
        await update.message.reply_text("❌ Виникла помилка при обробці вашої відповіді.")
