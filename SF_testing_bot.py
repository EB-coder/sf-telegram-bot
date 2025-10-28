import telebot
import random
import json
import os
from flask import Flask, request

# Получаем токен из переменных окружения
TOKEN = os.environ.get('BOT_TOKEN')

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

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

# Webhook обработчик для Render
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        return 'Invalid content type', 403

@app.route('/')
def index():
    return '🤖 Бот запущен и работает!'

# Установка webhook при запуске (исправленная версия)
def set_webhook():
    webhook_url = f"https://{os.environ.get('RENDER_SERVICE_NAME', 'your-app-name')}.onrender.com/webhook"
    try:
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
        print(f"Webhook установлен: {webhook_url}")
    except Exception as e:
        print(f"Ошибка установки webhook: {e}")

# Устанавливаем webhook при старте приложения
set_webhook()

if __name__ == '__main__':
    # На Render используем Flask
    app.run(host='0.0.0.0', port=5000, debug=False)
