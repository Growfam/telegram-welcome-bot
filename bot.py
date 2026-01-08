import os
import asyncio
from threading import Thread
from flask import Flask, request
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ChatJoinRequestHandler, CallbackQueryHandler, CommandHandler, ContextTypes

# Flask app
app = Flask(__name__)

# Налаштування
BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', '')
PORT = int(os.environ.get('PORT', 8080))

# Шлях до PDF книги
PDF_PATH = "book.pdf"

# Створюємо bot application
application = Application.builder().token(BOT_TOKEN).build()

# Глобальний event loop для асинхронних операцій
loop = None


# ============================================
# ОБРОБНИКИ ПОДІЙ
# ============================================

async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка заявки на вступ в канал"""
    user = update.chat_join_request.from_user
    chat = update.chat_join_request.chat

    print(f"✅ Нова заявка від {user.first_name} (@{user.username}) в {chat.title}")

    # Отримуємо username бота
    bot_username = (await context.bot.get_me()).username

    # 🔥 Створюємо deep link URL - користувач натисне і автоматично відкриє бота
    deep_link = f"https://t.me/{bot_username}?start=verify_{user.id}_{chat.id}"

    # Вітальне повідомлення від Mark
    text = f"""Привіт, {user.first_name}!

Це Mark.

6 років тому я почав з $500. Зараз трейдинг — моє основне джерело доходу.

Секрет? Немає секрету. Є стратегія, дисципліна і бажання заробляти.

У каналі ділюся всім що працює. Без води і теорії з підручників.

Підтверджуй що ти жива людина — і входь."""

    # 🔥 URL кнопка замість callback - це дає дозвіл боту писати!
    keyboard = [[InlineKeyboardButton("🚀 Підтверджую!", url=deep_link)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Відправляємо повідомлення з банером і текстом
    try:
        if os.path.exists("welcome_banner.png"):
            with open("welcome_banner.png", 'rb') as banner:
                await context.bot.send_photo(
                    chat_id=user.id,
                    photo=banner,
                    caption=text,
                    reply_markup=reply_markup
                )
        else:
            await context.bot.send_message(
                chat_id=user.id,
                text=text,
                reply_markup=reply_markup
            )

        print(f"📨 Відправлено вітальне повідомлення користувачу {user.id}")
        print(f"🔗 Deep link: {deep_link}")
    except Exception as e:
        print(f"❌ Помилка відправки: {e}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start - обробляє deep link параметри"""
    user = update.effective_user

    # Перевіряємо чи є start параметр (з deep link кнопки)
    if context.args and len(context.args) > 0:
        param = context.args[0]

        # Якщо це verify параметр (користувач натиснув кнопку "Підтверджую")
        if param.startswith("verify_"):
            try:
                # Парсимо параметр: verify_USER_ID_CHAT_ID
                parts = param.split("_")
                user_id = int(parts[1])
                chat_id = int(parts[2])

                print(f"🔘 Користувач {user_id} натиснув deep link кнопку")

                # Перевіряємо чи це той самий користувач
                if user.id != user_id:
                    await update.message.reply_text("❌ Помилка: невідповідність користувача")
                    return

                # 🎯 ОДОБРЮЄМО ЗАЯВКУ
                await context.bot.approve_chat_join_request(
                    chat_id=chat_id,
                    user_id=user_id
                )
                print(f"✅ Заявку одобрено для користувача {user_id}")

                # 🎁 НАДСИЛАЄМО БАНЕР З ПОДАРУНКОМ
                gift_text = """Готово! Ти всередині.

🎁 Подарунок на старті від мене:
📚 Книга «Дві сторони трейдингу»

Моя автобіографічна історія: від -$18,400 втрат і боргів до +$18,000/місяць. Без прикрас. Тільки правда про помилки, падіння і шлях до профіту.

📖 Книга вже у тебе в чаті 👇

💡 Порада від Mark:
Коли я втратив все, у мене було два шляхи: здатися або вчитися. Я обрав другий. Проаналізував кожну помилку. Змінив підхід. Зараз трейдинг — мій основний дохід. Твій вибір — що обереш ти?

Let's make money 💵

— Mark"""

                try:
                    if os.path.exists("gift_banner.png"):
                        with open("gift_banner.png", 'rb') as banner:
                            await update.message.reply_photo(
                                photo=banner,
                                caption=gift_text
                            )
                        print(f"🎁 Банер з подарунком надіслано користувачу {user_id}")
                    else:
                        await update.message.reply_text(text=gift_text)
                except Exception as banner_error:
                    print(f"⚠️ Помилка відправки банера: {banner_error}")

                # 📚 АВТОМАТИЧНО НАДСИЛАЄМО PDF КНИГУ
                try:
                    if os.path.exists(PDF_PATH):
                        with open(PDF_PATH, 'rb') as pdf_file:
                            await update.message.reply_document(
                                document=pdf_file,
                                filename="Дві_сторони_трейдингу_Mark_Inside.pdf",
                                caption="📚 Твій подарунок від Mark Inside!\n\nЧитай, вчись, заробляй 💰"
                            )
                        print(f"📚 PDF книгу надіслано користувачу {user_id}")
                    else:
                        print(f"⚠️ Файл {PDF_PATH} не знайдено!")
                        await update.message.reply_text(
                            text="⚠️ Технічна помилка при відправці книги. Зверніться до адміністратора."
                        )
                except Exception as pdf_error:
                    print(f"❌ Помилка відправки PDF: {pdf_error}")

            except Exception as e:
                print(f"❌ Помилка обробки verify параметра: {e}")
                await update.message.reply_text(
                    "❌ Помилка обробки заявки. Спробуйте ще раз або зверніться до адміністратора."
                )
    else:
        # Звичайний /start без параметрів
        await update.message.reply_text(
            "👋 <b>Привіт! Я Mark Inside Bot!</b>\n\n"
            "Мене потрібно додати адміністратором в канал з увімкненим 'Approve New Members'.\n\n"
            "Коли хтось подає заявку на вступ - я автоматично надішлю йому вітальне повідомлення від Mark!",
            parse_mode='HTML'
        )


# Додаємо обробники
application.add_handler(CommandHandler("start", start_command))
application.add_handler(ChatJoinRequestHandler(handle_join_request))


# ============================================
# FLASK WEBHOOK
# ============================================

@app.route('/')
def index():
    """Головна сторінка"""
    return "🤖 Mark Inside Bot is running!"


@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint для Telegram"""
    try:
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, application.bot)

        # ВАЖЛИВО: Обробляємо update в окремому event loop
        asyncio.run_coroutine_threadsafe(
            application.process_update(update),
            loop
        )

        return {"ok": True}
    except Exception as e:
        print(f"❌ Помилка в webhook: {e}")
        return {"ok": False, "error": str(e)}


@app.route('/setwebhook', methods=['GET'])
def set_webhook_route():
    """Встановлення webhook (для ручного виклику)"""
    try:
        webhook_url = f"{WEBHOOK_URL}/webhook"
        future = asyncio.run_coroutine_threadsafe(
            application.bot.set_webhook(url=webhook_url),
            loop
        )
        future.result(timeout=10)
        return f"✅ Webhook встановлено: {webhook_url}"
    except Exception as e:
        return f"❌ Помилка: {e}"


# ============================================
# ЗАПУСК БОТА
# ============================================

def run_asyncio_loop(loop):
    """Запуск event loop в окремому потоці"""
    asyncio.set_event_loop(loop)
    loop.run_forever()


async def setup_bot():
    """Ініціалізація бота"""
    await application.initialize()
    await application.start()

    # Встановлюємо webhook
    if WEBHOOK_URL:
        webhook_url = f"{WEBHOOK_URL}/webhook"
        await application.bot.set_webhook(url=webhook_url)
        print(f"✅ Webhook встановлено: {webhook_url}")


if __name__ == '__main__':
    print("🚀 Запуск Mark Inside Bot...")
    print(f"📍 Webhook URL: {WEBHOOK_URL}")
    print(f"🔌 Port: {PORT}")

    # Створюємо новий event loop
    loop = asyncio.new_event_loop()

    # Запускаємо event loop в окремому потоці
    thread = Thread(target=run_asyncio_loop, args=(loop,), daemon=True)
    thread.start()

    # Ініціалізуємо бота в цьому event loop
    future = asyncio.run_coroutine_threadsafe(setup_bot(), loop)
    try:
        future.result(timeout=30)
        print("✅ Бот ініціалізовано успішно!")
    except Exception as e:
        print(f"❌ Помилка ініціалізації: {e}")

    # Запускаємо Flask (він працює синхронно в основному потоці)
    app.run(host='0.0.0.0', port=PORT)