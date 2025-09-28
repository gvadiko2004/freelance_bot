import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

BOT_TOKEN = "6566504110:AAFK9hA4jxZ0eA7KZGhVvPe8mL2HZj2tQmE"

KEYWORDS = [
    "#html_и_css_верстка",
    "#веб_программирование",
    "#cms",
    "#интернет_магазины_и_электронная_коммерция",
    "#создание_сайта_под_ключ",
    "#дизайн_сайтов",
    "Создание сайта на Wordpress"
]

TARGET_CHAT_ID = 1168962519  # твой chat_id

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    text = msg.text or msg.caption
    if not text:
        return

    if any(keyword.lower() in text.lower() for keyword in KEYWORDS):
        try:
            await context.bot.forward_message(
                chat_id=TARGET_CHAT_ID,
                from_chat_id=msg.chat_id,
                message_id=msg.message_id
            )
            print(f"✅ Переслано сообщение: {text[:50]}...")
        except Exception as e:
            print(f"[ERROR] Не удалось переслать сообщение: {e}")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    print("✅ Бот запущен. Ожидание сообщений...")

    # В этом режиме run_polling не закрывает loop, просто запускаем polling
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()  # чтобы бот работал постоянно

if __name__ == "__main__":
    # Запускаем в существующем loop, если он есть
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(main())
        print("🔹 Запуск через существующий цикл событий")
        loop.run_forever()
    except RuntimeError:
        # Если loop нет, создаём новый
        asyncio.run(main())
