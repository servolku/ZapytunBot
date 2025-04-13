async def ask_question(update, context, new_session=False, query=None):
    """Send a question to the user."""
    user_id = update.effective_user.id
    if new_session or user_id not in USER_SESSION:
        USER_SESSION[user_id] = {"current_question": 0, "score": 0}

    question_index = USER_SESSION[user_id]["current_question"]

    # Check if there are more questions
    if question_index >= len(QUESTIONS):
        end_message = (
            f"Гра завершена! Твій підсумковий результат: {USER_SESSION[user_id]['score']} балів."
        )
        if query:
            await query.edit_message_text(text=end_message)
        else:
            await update.message.reply_text(text=end_message)
        update_score(user_id, USER_SESSION[user_id]["score"])
        del USER_SESSION[user_id]
        return

    question = QUESTIONS[question_index]
    options = question["options"]

    # Create inline keyboard for options
    keyboard = [
        [InlineKeyboardButton(option, callback_data=str(idx))]
        for idx, option in enumerate(options)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:  # If called from handle_answer
        await query.edit_message_text(text=question["question"], reply_markup=reply_markup)
    else:  # If called from start command
        await update.message.reply_text(text=question["question"], reply_markup=reply_markup)

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user's answer."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    # Переконайтеся, що сесія користувача існує
    if user_id not in USER_SESSION:
        await query.edit_message_text(text="❌ Помилка: Сесія не знайдена.")
        return

    question_index = USER_SESSION[user_id]["current_question"]
    question = QUESTIONS[question_index]

    # Перевірка відповіді
    if int(query.data) == question["correct"]:
        USER_SESSION[user_id]["score"] += 1
        response = "✅ Правильно!"
    else:
        response = "❌ Неправильно!"

    # Оновлення тексту повідомлення
    await query.edit_message_text(text=response)

    # Перехід до наступного питання
    USER_SESSION[user_id]["current_question"] += 1
    await ask_question(update, context, query=query)
