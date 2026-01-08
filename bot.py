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

# Bot username (заповнюється при ініціалізації)
bot_username = "Mark_Inside_bot"

# ============================================
# ОБРОБНИКИ ПОДІЙ
# ============================================

async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка заявки на вступ в канал"""
    user = update.chat_join_request.from_user
    chat = update.chat_join_request.chat
    
    print(f"✅ Нова заявка від {user.first_name} (@{user.username}) в {chat.title}")
    
    # Зберігаємо chat_id для пізнішого одобрення
    context.bot_data[f'pending_{user.id}'] = chat.id
    
    # Вітальне повідомлення від Mark
    text = f"""Привіт, {user.first_name}!

Це Mark.

6 років тому я почав з $500. Зараз трейдинг — моє основне джерело доходу.

Секрет? Немає секрету. Є стратегія, дисципліна і бажання заробляти.

У каналі ділюся всім що працює. Без води і теорії з підручників.

Натискай кнопку нижче щоб підтвердити заявку та отримати подарунок! 👇"""
    
    # Кнопка з URL що відкриває приват з ботом
    keyboard = [[InlineKeyboardButton(
        "🚀 Підтверджую та отримую подарунок!",
        url=f"https://t.me/{bot_username}?start=welcome_{user.id}"
    )]]
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
        
    except Exception as e:
        print(f"❌ Помилка відправки вітального повідомлення: {e}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start - обробляє підтвердження і надсилає подарунки"""
    user_id = update.effective_user.id
    
    # Перевіряємо чи є параметр welcome
    if context.args and context.args[0].startswith('welcome_'):
        # Витягуємо user_id з параметра
        param_user_id = int(context.args[0].split('_')[1])
        
        # Перевіряємо що користувач підтверджує свою власну заявку
        if param_user_id != user_id:
            await update.message.reply_text("❌ Помилка: невірний параметр")
            return
        
        # Отримуємо chat_id з bot_data
        chat_id = context.bot_data.get(f'pending_{user_id}')
        
        if not chat_id:
            await update.message.reply_text("❌ Не знайдено активної заявки. Спробуйте подати заявку знову.")
            return
        
        print(f"🔘 Користувач {user_id} підтвердив через /start")
        
        # Одобрюємо заявку
        try:
            await context.bot.approve_chat_join_request(
                chat_id=chat_id,
                user_id=user_id
            )
            print(f"✅ Заявку одобрено для користувача {user_id}")
            
            # Видаляємо з pending
            del context.bot_data[f'pending_{user_id}']
            
        except Exception as e:
            print(f"❌ Помилка одобрення: {e}")
            await update.message.reply_text(f"❌ Помилка одобрення заявки: {e}")
            return
        
        # НАДСИЛАЄМО БАНЕР З ПОДАРУНКОМ
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
                    await update.message.reply_photo(
                        photo=banner,
                        caption=gift_text
                    )
                print(f"🎁 Банер з подарунком надіслано користувачу {user_id}")
            else:
                await update.message.reply_text(gift_text)
        except Exception as banner_error:
            print(f"⚠️ Помилка відправки банера: {banner_error}")
        
        # АВТОМАТИЧНО НАДСИЛАЄМО PDF КНИГУ
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
                    "⚠️ Технічна помилка при відправці книги. Зверніться до адміністратора."
                )
        except Exception as pdf_error:
            print(f"❌ Помилка відправки PDF: {pdf_error}")
            await update.message.reply_text(
                "⚠️ Не вдалося надіслати книгу. Спробуйте звернутися до адміністратора."
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

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обробка webhook від Telegram"""
    try:
        json_data = request.get_json()
        update = Update.de_json(json_data, application.bot)
        
        # Виконуємо обробку в event loop
        asyncio.run_coroutine_threadsafe(
            application.process_update(update),
            loop
        )
        
        return '', 200
    except Exception as e:
        print(f"Webhook error: {e}")
        return '', 500

@app.route('/')
def index():
    return 'Bot is running!', 200

# ============================================
# ІНІЦІАЛІЗАЦІЯ
# ============================================

async def setup_webhook():
    """Налаштування webhook"""
    webhook_url = f"{WEBHOOK_URL}/webhook"
    
    print(f"🚀 Запуск Mark Inside Bot...")
    print(f"📍 Webhook URL: {WEBHOOK_URL}")
    print(f"🔌 Port: {PORT}")
    
    # Встановлюємо webhook
    await application.bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook встановлено: {webhook_url}")
    
    # Ініціалізуємо bot application
    await application.initialize()
    await application.start()
    print(f"✅ Бот ініціалізовано успішно!")

def run_bot():
    """Запуск бота"""
    global loop
    
    # Створюємо новий event loop для цього потоку
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Налаштовуємо webhook
    loop.run_until_complete(setup_webhook())
    
    # Запускаємо Flask
    app.run(host='0.0.0.0', port=PORT)

if __name__ == '__main__':
    # Запускаємо в окремому потоці
    bot_thread = Thread(target=run_bot)
    bot_thread.start()
    bot_thread.join()
