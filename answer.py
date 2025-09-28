import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import time

# Токен вашего бота
BOT_TOKEN = "6566504110:AAFK9hA4jxZ0eA7KZGhVvPe8mL2HZj2tQmE"

# Ключевые слова
KEYWORDS = [
    "#html_и_css_верстка",
    "#веб_программирование",
    "#cms",
    "#интернет_магазины_и_электронная_коммерция",
    "#создание_сайта_под_ключ",
    "#дизайн_сайтов",
    "Создание сайта на Wordpress"
]

# Чтобы не слать alert повторно для одного и того же сообщения
sent_alerts = set()

# Минимальный интервал между сообщениями (защита от flood)
FLOOD_INTERVAL = 2  # секунд
last_sent_time = 0

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_sent_time
    text = update.message.text
    chat_id = update.message.chat_id
    message_id = update.message.message_id

    # Проверяем ключевые слова
    if any(keyword in text for keyword in KEYWORDS):
        # Проверка, что сообщение ещё не обрабатывалось
        if message_id in sent_alerts:
            return

        # Проверяем ограничение по времени (flood)
        now = time.time()
        if now - last_sent_time < FLOOD_INTERVAL:
            return

        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"✅ Найдено сообщение с ключевым словом:\n{text}"
            )
            sent_alerts.add(message_id)
            last_sent_time = now
        except Exception as e:
            print(f"[ERROR] Не удалось отправить сообщение: {e}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Бот запущен. Ожидание сообщений...")
    app.run_polling()  # без asyncio.run()

if __name__ == "__main__":
    main()
