import telebot
import random
import json
import os

# Получаем токен из переменных окружения

bot = telebot.TeleBot(TOKEN)

# Загружаем вопросы из JSON
with open("quiz_questions.json", "r", encoding="utf-8") as f:
    questions = json.load(f)

# Состояние пользователей
user_data = {}

@bot.message_handler(commands=["start"])
def start_quiz(message):
    chat_id = message.chat.id
    random.shuffle(questions)
    user_data[chat_id] = {
        "remaining": questions.copy(),
        "correct": 0,
        "wrong": 0,
        "current": None
    }
    bot.send_message(chat_id, "Привет! 🤖 Начинаем викторину!")
    send_new_question(chat_id)

def send_new_question(chat_id):
    user = user_data[chat_id]
    if not user["remaining"]:
        total = user["correct"] + user["wrong"]
        bot.send_message(
            chat_id,
            f"🏁 Викторина окончена!\n\n✅ Правильных: {user['correct']}\n❌ Неправильных: {user['wrong']}\n📊 Всего вопросов: {total}"
        )
        del user_data[chat_id]
        return

    q = user["remaining"].pop()
    user["current"] = q

    text = f"❓ {q['question']}\n\n"
    for letter, option in q["options"].items():
        text += f"{letter}. {option}\n"
    text += "\nОтправь букву(-ы) правильных ответов (например A или A,C):"

    bot.send_message(chat_id, text)

@bot.message_handler(func=lambda msg: True)
def handle_answer(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        bot.send_message(chat_id, "Чтобы начать викторину, напиши /start")
        return

    user = user_data[chat_id]
    q = user["current"]

    if not q:
        bot.send_message(chat_id, "Ошибка — вопрос не найден. Напиши /start чтобы начать заново.")
        return

    user_input = [x.strip().upper() for x in message.text.split(",") if x.strip()]
    correct_answers = q["answers"]

    if set(user_input) == set(correct_answers):
        user["correct"] += 1
        bot.send_message(chat_id, "✅ Правильно!")
    else:
        user["wrong"] += 1
        correct_text = ", ".join(correct_answers)
        bot.send_message(chat_id, f"❌ Неправильно. Правильный ответ: {correct_text}")

    user["current"] = None
    send_new_question(chat_id)

print("🤖 Бот запущен...")
bot.infinity_polling()
