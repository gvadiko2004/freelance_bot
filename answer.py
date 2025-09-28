from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import asyncio

# Токен твоего бота
BOT_TOKEN = "6566504110:AAFK9hA4jxZ0eA7KZGhVvPe8mL2HZj2tQmE"

# Список ключевых слов для фильтрации
KEYWORDS = [
    "#html_и_css_верстка",
    "#веб_программирование",
    "#cms",
    "#интернет_магазины_и_электронная_коммерция",
    "#создание_сайта_под_ключ",
    "#дизайн_сайтов",
    "Создание сайта на Wordpress"
]

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.message.chat_id

    # Проверяем наличие любого ключевого слова в сообщении
    if any(keyword in text for keyword in KEYWORDS):
        try:
            await context.bot.send_message(chat_id=chat_id, text="✅ Сообщение с ключевым словом найдено!")
        except Exception as e:
            print(f"[ERROR] Не удалось отправить сообщение: {e}")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Обработчик всех текстовых сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Бот запущен. Ожидание сообщений...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
