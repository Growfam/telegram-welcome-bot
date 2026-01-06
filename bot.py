import os
import asyncio
from flask import Flask, request
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ChatJoinRequestHandler, CallbackQueryHandler, CommandHandler, ContextTypes

# Flask app
app = Flask(__name__)

# Налаштування
BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', '')
PORT = int(os.environ.get('PORT', 8080))

# Канали для підписки (змінюй на свої!)
CHANNELS = {
    'channel1': {
        'name': 'Workers Crypto',
        'url': 'https://t.me/+8i5494TSePE1MTgy',
        'id': -1001234567890  # ID каналу (отримаєш коли додаси бота)
    },
    'channel2': {
        'name': 'Alex Trade',
        'url': 'https://t.me/+l8YjXgFg07lmMTky',
        'id': -1001234567891
    },
    'channel3': {
        'name': 'Маша | Trade 🌸',
        'url': 'https://t.me/+wtYfuXMyCzg3ZmE6',
        'id': -1001234567892
    }
}

# Створюємо bot application
application = Application.builder().token(BOT_TOKEN).build()

# ============================================
# ОБРОБНИКИ ПОДІЙ
# ============================================

async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка заявки на вступ в канал"""
    user = update.chat_join_request.from_user
    chat = update.chat_join_request.chat
    
    print(f"✅ Нова заявка від {user.first_name} (@{user.username}) в {chat.title}")
    
    # Вітальне повідомлення
    text = f"""
👋 <b>Привіт, {user.first_name}!</b>

✅ <b>ВАМ ПОДАРУНОК - 890 USDT!</b>

Щоб отримати доступ до каналу "<i>{chat.title}</i>", потрібно:

📌 <b>Підписатися на ТРИ канали:</b>

1️⃣ {CHANNELS['channel1']['name']}
2️⃣ {CHANNELS['channel2']['name']}
3️⃣ {CHANNELS['channel3']['name']}

⚡️ <b>Завтра вхід буде платним (890$)</b>
Заходь прямо зараз <b>БЕЗКОШТОВНО!</b>

👇 <b>Натисни кнопку нижче після підписки:</b>
"""
    
    # Кнопки
    keyboard = [
        [InlineKeyboardButton("1-Й КАНАЛ →", url=CHANNELS['channel1']['url'])],
        [InlineKeyboardButton("2-Й КАНАЛ →", url=CHANNELS['channel2']['url'])],
        [InlineKeyboardButton("3-Й КАНАЛ →", url=CHANNELS['channel3']['url'])],
        [InlineKeyboardButton("✅ Я НЕ РОБОТ", callback_data=f"verify_{user.id}_{chat.id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Відправляємо повідомлення
    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        print(f"📨 Відправлено вітальне повідомлення користувачу {user.id}")
    except Exception as e:
        print(f"❌ Помилка відправки: {e}")


async def handle_verify_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка натискання кнопки 'Я не робот'"""
    query = update.callback_query
    await query.answer()
    
    # Парсимо дані
    data_parts = query.data.split("_")
    if data_parts[0] != "verify":
        return
        
    user_id = int(data_parts[1])
    chat_id = int(data_parts[2])
    
    print(f"🔘 Користувач {user_id} натиснув 'Я не робот'")
    
    # Тут можна додати перевірку підписок на канали
    # subscribed = await check_subscriptions(user_id, context)
    # if not subscribed:
    #     await query.edit_message_text("❌ Спочатку підпишись на всі 3 канали!")
    #     return
    
    # Одобрюємо заявку
    try:
        await context.bot.approve_chat_join_request(
            chat_id=chat_id,
            user_id=user_id
        )
        
        # Змінюємо повідомлення
        await query.edit_message_text(
            text="✅ <b>Вітаю! Твою заявку одобрено!</b>\n\n"
                 "🎉 Тепер ти маєш доступ до каналу!\n"
                 "💰 Твій бонус чекає на тебе всередині!",
            parse_mode='HTML'
        )
        print(f"✅ Заявку одобрено для користувача {user_id}")
        
    except Exception as e:
        print(f"❌ Помилка одобрення: {e}")
        await query.edit_message_text(
            text=f"❌ <b>Помилка при одобренні заявки</b>\n\n"
                 f"Спробуй ще раз або напиши адміністратору.\n\n"
                 f"<i>Помилка: {str(e)}</i>",
            parse_mode='HTML'
        )


async def check_subscriptions(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Перевірка підписок на всі канали (опціонально)"""
    for channel_key, channel_info in CHANNELS.items():
        try:
            member = await context.bot.get_chat_member(
                chat_id=channel_info['id'],
                user_id=user_id
            )
            # Якщо не підписаний - повертаємо False
            if member.status not in ['member', 'administrator', 'creator']:
                print(f"❌ Користувач {user_id} не підписаний на {channel_info['name']}")
                return False
        except Exception as e:
            print(f"⚠️ Не вдалося перевірити підписку на {channel_info['name']}: {e}")
            # Можна або пропустити, або вважати що не підписаний
            continue
    
    return True


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    await update.message.reply_text(
        "👋 <b>Привіт! Я Welcome Bot!</b>\n\n"
        "Мене потрібно додати адміністратором в канал з увімкненим 'Approve New Members'.\n\n"
        "Коли хтось подає заявку на вступ - я автоматично надішлю йому вітальне повідомлення!",
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
    return "🤖 Welcome Bot is running!"


@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint для Telegram"""
    try:
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, application.bot)
        
        # Обробляємо update асинхронно
        asyncio.run(application.process_update(update))
        
        return {"ok": True}
    except Exception as e:
        print(f"❌ Помилка в webhook: {e}")
        return {"ok": False, "error": str(e)}


@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    """Встановлення webhook (для ручного виклику)"""
    try:
        webhook_url = f"{WEBHOOK_URL}/webhook"
        asyncio.run(application.bot.set_webhook(url=webhook_url))
        return f"✅ Webhook встановлено: {webhook_url}"
    except Exception as e:
        return f"❌ Помилка: {e}"


# ============================================
# ЗАПУСК БОТА
# ============================================

if __name__ == '__main__':
    print("🚀 Запуск Welcome Bot...")
    print(f"📍 Webhook URL: {WEBHOOK_URL}")
    print(f"🔌 Port: {PORT}")
    
    # Встановлюємо webhook при старті
    if WEBHOOK_URL:
        try:
            webhook_url = f"{WEBHOOK_URL}/webhook"
            asyncio.run(application.bot.set_webhook(url=webhook_url))
            print(f"✅ Webhook встановлено: {webhook_url}")
        except Exception as e:
            print(f"⚠️ Не вдалося встановити webhook: {e}")
    
    # Запускаємо Flask
    app.run(host='0.0.0.0', port=PORT)
