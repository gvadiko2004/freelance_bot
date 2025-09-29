import asyncio
from telethon import TelegramClient, events
from telegram import Bot

# ===== Настройки =====
api_id = 21882740
api_hash = "c80a68894509d01a93f5acfeabfdd922"
SESSION_NAME = "session"

BOT_TOKEN = "6566504110:AAFK9hA4jxZ0eA7KZGhVvPe8mL2HZj2tQmE"
ALERT_CHAT_ID = 1168962519  # твой Telegram ID

TARGET_USERNAME = "achie_81"  # пользователь/чат, откуда берём сообщения

KEYWORDS = [
    "#html_и_css_верстка",
    "#веб_программирование",
    "#cms",
    "#интернет_магазины_и_электронная_коммерция",
    "#создание_сайта_под_ключ",
    "#дизайн_сайтов"
]
KEYWORDS = [kw.lower() for kw in KEYWORDS]

# ===== Инициализация бота =====
alert_bot = Bot(token=BOT_TOKEN)
client = TelegramClient(SESSION_NAME, api_id, api_hash)

# ===== Функция пересылки =====
async def send_alert(text):
    try:
        await alert_bot.send_message(chat_id=ALERT_CHAT_ID, text=text)
        print("[INFO] Сообщение переслано через бот")
    except Exception as e:
        print(f"[ERROR] Не удалось переслать сообщение: {e}")

# ===== Обработка новых сообщений =====
@client.on(events.NewMessage(chats=TARGET_USERNAME))
async def handler(event):
    message = event.message
    text = message.text or ""
    
    # Проверка ключевых слов
    if any(k in text.lower() for k in KEYWORDS):
        # Собираем текст сообщения
        output_text = f"🔔 Новое сообщение:\n\n{text}"
        # Добавляем ссылку на сообщение в Telegram
        output_text += f"\n\nСсылка на сообщение: https://t.me/{TARGET_USERNAME}/{message.id}"
        
        # Отправляем через бот
        await send_alert(output_text)

# ===== Запуск =====
async def main():
    print("✅ Бот запущен. Ожидание новых сообщений...")
    await send_alert("✅ Бот успешно запущен и готов к работе!")
    await client.start()
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
