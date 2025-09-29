import asyncio
from telethon import TelegramClient, events
from telegram import Bot

# ===== Настройки =====
api_id = 21882740
api_hash = "c80a68894509d01a93f5acfeabfdd922"
SESSION_NAME = "session"  # для Telethon

BOT_TOKEN = "6566504110:AAFK9hA4jxZ0eA7KZGhVvPe8mL2HZj2tQmE"
ALERT_CHAT_ID = 1168962519  # твой Telegram ID

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

# ===== Telethon клиент =====
client = TelegramClient(SESSION_NAME, api_id, api_hash)

# ===== Функция отправки уведомлений =====
async def send_alert(text):
    try:
        await alert_bot.send_message(chat_id=ALERT_CHAT_ID, text=text)
        print("[INFO] Сообщение отправлено через бот")
    except Exception as e:
        print(f"[ERROR] Не удалось отправить сообщение: {e}")

# ===== Обработка новых сообщений =====
@client.on(events.NewMessage)
async def handler(event):
    text = (event.message.text or "").lower()
    if any(k in text for k in KEYWORDS):
        msg = f"🔔 Новое сообщение с ключевым словом:\n{text}"
        await send_alert(msg)

# ===== Запуск =====
async def main():
    print("✅ Бот запущен. Ожидание новых сообщений...")
    await send_alert("✅ Бот успешно запущен и готов к работе!")
    await client.start()
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
