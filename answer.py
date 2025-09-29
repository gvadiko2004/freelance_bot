from telethon import TelegramClient, events
import asyncio
import requests

# ===== НАСТРОЙКИ =====
api_id = 21882740
api_hash = "c80a68894509d01a93f5acfeabfdd922"
PHONE_NUMBER = "+380634646075"

BOT_TOKEN = "6566504110:AAFK9hA4jxZ0eA7KZGhVvPe8mL2HZj2tQmE"
ALERT_CHAT_ID = 1168962519  # ID, куда пересылать (твой Telegram)

SOURCE_CHAT = "FreelancehuntProjects"

KEYWORDS = [
    "#html_и_css_верстка",
    "#веб_программирование",
    "#cms",
    "#интернет_магазины_и_электронная_коммерция",
    "#создание_сайта_под_ключ",
    "#дизайн_сайтов"
]
KEYWORDS = [k.lower() for k in KEYWORDS]

# ===== Клиент User =====
user_client = TelegramClient("user_session", api_id, api_hash)

# ===== Функция отправки через Bot API =====
def send_to_bot(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": ALERT_CHAT_ID, "text": text}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"[ERROR BOT SEND] {e}")

# ===== Проверка и пересылка =====
async def check_and_forward(message):
    text = message.text or ""
    lower_text = text.lower()
    if any(k in lower_text for k in KEYWORDS):
        send_to_bot(f"🔔 Новое сообщение:\n{text}")
        print(f"[SENT TO BOT] {text[:50]}...")

# ===== Обработчик новых сообщений =====
@user_client.on(events.NewMessage(chats=SOURCE_CHAT))
async def handler(event):
    await check_and_forward(event.message)

# ===== Основная функция =====
async def main():
    await user_client.start(phone=PHONE_NUMBER)
    print("✅ USER авторизован")

    # Тест: последние 10 сообщений
    print("🔍 Тест — беру последние 10 сообщений...")
    messages = await user_client.get_messages(SOURCE_CHAT, limit=10)
    for msg in messages:
        await check_and_forward(msg)

    print("👁 Теперь слушаю новые сообщения...")
    await user_client.run_until_disconnected()

# ===== Запуск =====
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
