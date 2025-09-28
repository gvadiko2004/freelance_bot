import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import time

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

sent_alerts = set()
FLOOD_INTERVAL = 2
last_sent_time = 0

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_sent_time
    msg = update.message
    if not msg:
        return

    # Берём текст сообщения или подпись медиа
    text = msg.text or msg.caption
    if not text:
        return

    chat_id = msg.chat_id
    message_id = msg.message_id

    if any(keyword in text for keyword in KEYWORDS):
        if message_id in sent_alerts:
            return

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
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    print("✅ Бот запущен. Ожидание сообщений...")
    app.run_polling()

if __name__ == "__main__":
    main()
