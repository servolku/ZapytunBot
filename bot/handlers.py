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

    # Переходимо до наступного питання
    USER_SESSION[user_id]["current_question"] += 1

    # Викликаємо наступне питання
    # Створюємо "фейковий" Update для функції ask_question
    fake_update = Update(
        update.update_id,
        message=query.message
    )
    await ask_question(fake_update, context)
