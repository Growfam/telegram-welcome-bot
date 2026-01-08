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

    # Вітальне повідомлення від Mark
    text = f"""Привіт, {user.first_name}!

Це Mark.

6 років тому я почав з $500. Зараз трейдинг — моє основне джерело доходу.

Секрет? Немає секрету. Є стратегія, дисципліна і бажання заробляти.

У каналі ділюся всім що працює. Без води і теорії з підручників.

Підтверджуй що ти жива людина — і входь."""

    # Кнопка
    keyboard = [[InlineKeyboardButton("🚀 Підтверджую!", callback_data=f"verify_{user.id}_{chat.id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Відправляємо повідомлення з банером і текстом в одному повідомленні
    try:
        # Відправляємо банер з текстом і кнопкою
        if os.path.exists("welcome_banner.png"):
            with open("welcome_banner.png", 'rb') as banner:
                await context.bot.send_photo(
                    chat_id=user.id,
                    photo=banner,
                    caption=text,
                    reply_markup=reply_markup
                )
        else:
            # Якщо банера немає - просто текст
            await context.bot.send_message(
                chat_id=user.id,
                text=text,
                reply_markup=reply_markup
            )

        print(f"📨 Відправлено вітальне повідомлення користувачу {user.id}")
    except Exception as e:
        print(f"❌ Помилка відправки: {e}")


async def handle_verify_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка натискання кнопки 'Підтверджую'"""
    query = update.callback_query
    await query.answer()

    # Парсимо дані
    data_parts = query.data.split("_")
    if data_parts[0] != "verify":
        return

    user_id = int(data_parts[1])
    chat_id = int(data_parts[2])
    user_name = query.from_user.first_name

    print(f"🔘 Користувач {user_id} натиснув 'Підтверджую'")

    # Одобрюємо заявку
    try:
        await context.bot.approve_chat_join_request(
            chat_id=chat_id,
            user_id=user_id
        )
        print(f"✅ Заявку одобрено для користувача {user_id}")

        # Видаляємо кнопку з попереднього повідомлення (фото)
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except:
            pass

        # Відправляємо нове повідомлення
        await context.bot.send_message(
            chat_id=user_id,
            text="✅ Готово! Ти всередині."
        )

        # НАДСИЛАЄМО БАНЕР З ПОДАРУНКОМ + ТЕКСТ В ОДНОМУ ПОВІДОМЛЕННІ
        gift_text = """🎁 Подарунок на старті від мене:
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
                    await context.bot.send_photo(
                        chat_id=user_id,
                        photo=banner,
                        caption=gift_text
                    )
                print(f"🎁 Банер з подарунком надіслано користувачу {user_id}")
            else:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=gift_text
                )
        except Exception as banner_error:
            print(f"⚠️ Помилка відправки банера: {banner_error}")

        # АВТОМАТИЧНО НАДСИЛАЄМО PDF КНИГУ
        try:
            # Перевіряємо чи існує файл
            if os.path.exists(PDF_PATH):
                with open(PDF_PATH, 'rb') as pdf_file:
                    await context.bot.send_document(
                        chat_id=user_id,
                        document=pdf_file,
                        filename="Дві_сторони_трейдингу_Mark_Inside.pdf",
                        caption="📚 Твій подарунок від Mark Inside!\n\nЧитай, вчись, заробляй 💰"
                    )
                print(f"📚 PDF книгу надіслано користувачу {user_id}")
            else:
                print(f"⚠️ Файл {PDF_PATH} не знайдено!")
                await context.bot.send_message(
                    chat_id=user_id,
                    text="⚠️ Технічна помилка при відправці книги. Зверніться до адміністратора."
                )
        except Exception as pdf_error:
            print(f"❌ Помилка відправки PDF: {pdf_error}")
            await context.bot.send_message(
                chat_id=user_id,
                text="⚠️ Не вдалося надіслати книгу. Спробуйте звернутися до адміністратора."
            )

    except Exception as e:
        print(f"❌ Помилка одобрення: {e}")
        await query.edit_message_text(
            text=f"❌ <b>Помилка при одобренні заявки</b>\n\n"
                 f"Спробуй ще раз або напиши адміністратору.\n\n"
                 f"<i>Помилка: {str(e)}</i>",
            parse_mode='HTML'
        )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    await update.message.reply_text(
        "👋 <b>Привіт! Я Mark Inside Bot!</b>\n\n"
        "Мене потрібно додати адміністратором в канал з увімкненим 'Approve New Members'.\n\n"
        "Коли хтось подає заявку на вступ - я автоматично надішлю йому вітальне повідомлення від Mark!",
        parse_mode='HTML'
    )


# Додаємо обробники
application.add_handler(CommandHandler("start", start_command))
application.add_handler(ChatJoinRequestHandler(handle_join_request))
application.add_handler(CallbackQueryHandler(handle_verify_button))


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