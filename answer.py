import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Ваш токен бота
BOT_TOKEN = "6566504110:AAFK9hA4jxZ0eA7KZGhVvPe8mL2HZj2tQmE"

# Список ключевых слов
KEYWORDS = [
    "#html_и_css_верстка",
    "#веб_программирование",
    "#cms",
    "#интернет_магазины_и_электронная_коммерция",
    "#создание_сайта_под_ключ",
    "#дизайн_сайтов",
    "Создание сайта на Wordpress"
]

# Ваш chat_id, куда бот будет пересылать найденные сообщения
TARGET_CHAT_ID = 1168962519  # замените на свой ID

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    # Получаем текст или подпись медиа
    text = msg.text or msg.caption
    if not text:
        return

    # Проверяем ключевые слова
    if any(keyword.lower() in text.lower() for keyword in KEYWORDS):
        try:
            # Пересылаем сообщение целиком
            await context.bot.forward_message(
                chat_id=TARGET_CHAT_ID,
                from_chat_id=msg.chat_id,
                message_id=msg.message_id
            )
            print(f"✅ Переслано сообщение: {text[:50]}...")  # для логов
        except Exception as e:
            print(f"[ERROR] Не удалось переслать сообщение: {e}")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Ловим любые сообщения кроме команд
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    print("✅ Бот запущен. Ожидание сообщений...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
