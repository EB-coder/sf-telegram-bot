import telebot
import random
import json
import os
from flask import Flask, request

# Получаем токен из переменных окружения
TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    print("❌ ОШИБКА: Переменная окружения BOT_TOKEN не установлена!")
    print("📝 Установите переменную BOT_TOKEN в настройках Render")
    exit(1)

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Загружаем вопросы из JSON
with open("quiz_questions.json", "r", encoding="utf-8") as f:
    questions = json.load(f)

# Состояние пользователей
user_data = {}

@bot.message_handler(commands=["start"])
def start_bot(message):
    chat_id = message.chat.id
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("📚 Подготовка", "🎯 Экзамен")
    bot.send_message(
        chat_id,
        "🤖 Добро пожаловать в бот-викторину!\n\n"
        "Выберите режим:\n"
        "• 📚 **Подготовка** - все вопросы подряд\n"
        "• 🎯 **Экзамен** - 60 случайных вопросов",
        reply_markup=markup
    )

@bot.message_handler(func=lambda msg: msg.text in ["📚 Подготовка", "🎯 Экзамен"])
def select_mode(message):
    chat_id = message.chat.id
    mode = message.text
    
    if mode == "📚 Подготовка":
        # Все вопросы
        questions_to_use = questions.copy()
        random.shuffle(questions_to_use)
        user_data[chat_id] = {
            "remaining": questions_to_use,
            "correct": 0,
            "wrong": 0,
            "current": None,
            "mode": "preparation"
        }
        bot.send_message(chat_id, "📚 Режим: Подготовка\nВсего вопросов: " + str(len(questions)))
        
    elif mode == "🎯 Экзамен":
        # 60 случайных вопросов
        if len(questions) >= 60:
            questions_to_use = random.sample(questions, 60)
        else:
            questions_to_use = questions.copy()
        random.shuffle(questions_to_use)
        user_data[chat_id] = {
            "remaining": questions_to_use,
            "correct": 0,
            "wrong": 0,
            "current": None,
            "mode": "exam"
        }
        bot.send_message(chat_id, "🎯 Режим: Экзамен\nКоличество вопросов: 60")
    
    # Убираем клавиатуру после выбора
    markup = telebot.types.ReplyKeyboardRemove()
    bot.send_message(chat_id, "Начинаем викторину! 🚀", reply_markup=markup)
    send_new_question(chat_id)

def send_new_question(chat_id):
    user = user_data.get(chat_id)
    if not user or not user["remaining"]:
        if user:
            total = user["correct"] + user["wrong"]
            mode_text = "📚 Подготовка" if user["mode"] == "preparation" else "🎯 Экзамен"
            
            bot.send_message(
                chat_id,
                f"🏁 Викторина окончена!\n"
                f"Режим: {mode_text}\n\n"
                f"✅ Правильных: {user['correct']}\n"
                f"❌ Неправильных: {user['wrong']}\n"
                f"📊 Всего вопросов: {total}\n"
                f"📈 Процент правильных: {user['correct']/total*100:.1f}%" if total > 0 else "📊 Всего вопросов: 0"
            )
            
            # Предлагаем начать заново
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add("📚 Подготовка", "🎯 Экзамен")
            bot.send_message(chat_id, "Хотите пройти ещё раз?", reply_markup=markup)
            del user_data[chat_id]
        return

    q = user["remaining"].pop()
    user["current"] = q

    # Добавляем прогресс
    total_questions = len(user["remaining"]) + 1
    progress = f"({total_questions - len(user['remaining'])}/{total_questions})"
    
    text = f"❓ {q['question']} {progress}\n\n"
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

# Вебхук обработчики для Render
@app.route('/')
def index():
    return "Бот запущен и работает! 🤖"

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        return 'Bad request', 400

if __name__ == '__main__':
    # На Render используем порт из переменной окружения
    port = int(os.environ.get('PORT', 5000))
    
    # Удаляем вебхук если был установлен ранее
    bot.remove_webhook()
    
    # Устанавливаем вебхук
    webhook_url = os.environ.get('WEBHOOK_URL', '') + '/webhook'
    if webhook_url:
        bot.set_webhook(url=webhook_url)
        print(f"✅ Вебхук установлен: {webhook_url}")
    else:
        print("⚠️  WEBHOOK_URL не установлен, бот будет работать в polling режиме")
    
    # Запускаем Flask приложение
    app.run(host='0.0.0.0', port=port)
