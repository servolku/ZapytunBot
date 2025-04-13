import sys
import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.models import get_or_create_user, update_score, get_leaderboard

# Initialize user session
USER_SESSION = {}

def load_questions():
    """Load questions dynamically from the JSON file."""
    with open("bot/questions.json", "r") as f:
        return json.load(f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    user = update.effective_user
    get_or_create_user(user.id, user.first_name)
    await update.message.reply_text(
        f"Привіт, {user.first_name}! Готовий розпочати квест?\n"
        "Відповідай на запитання, щоб заробити бали!"
    )
    # Ask the first question
    await ask_question(update, context, new_session=True)

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /leaderboard command."""
    leaderboard_data = get_leaderboard()
    leaderboard_text = "🏆 Дошка переможців 🏆\n\n"
    for idx, (name, score) in enumerate(leaderboard_data, start=1):
        leaderboard_text += f"{idx}. {name}: {score} балів\n"
    await update.message.reply_text(leaderboard_text)

async def ask_question(update, context, new_session=False):
    """Send a question to the user."""
    user_id = update.effective_user.id
    if new_session or user_id not in USER_SESSION:
        USER_SESSION[user_id] = {"current_question": 0, "score": 0}

    # Load questions dynamically
    questions = load_questions()
    question_index = USER_SESSION[user_id]["current_question"]

    # Check if there are more questions
    if question_index >= len(questions):
        await update.message.reply_text(
            f"Гра завершена! Твій підсумковий результат: {USER_SESSION[user_id]['score']} балів."
        )
        update_score(user_id, USER_SESSION[user_id]["score"])
        del USER_SESSION[user_id]
        return

    question = questions[question_index]
    options = question["options"]

    # Create inline keyboard for options
    keyboard = [
        [InlineKeyboardButton(option, callback_data=str(idx))]
        for idx, option in enumerate(options)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(question["question"], reply_markup=reply_markup)

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user's answer."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    # Ensure the user's session exists
    if user_id not in USER_SESSION:
        await query.edit_message_text(text="❌ Помилка: Сесія не знайдена.")
        return

    # Load questions dynamically
    questions = load_questions()
    question_index = USER_SESSION[user_id]["current_question"]
    question = questions[question_index]

    # Check the answer
    if int(query.data) == question["correct"]:
        USER_SESSION[user_id]["score"] += 1
        response = "✅ Правильно!"
    else:
        response = "❌ Неправильно!"

    # Update the message with the response
    await query.edit_message_text(text=response)

    # Move to the next question
    USER_SESSION[user_id]["current_question"] += 1
    await ask_question(update, context)
