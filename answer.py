from telethon import TelegramClient, events
import asyncio

# ===== НАСТРОЙКИ =====
api_id = 21882740
api_hash = "c80a68894509d01a93f5acfeabfdd922"
PHONE_NUMBER = "+380634646075"

ALERT_CHAT_ID = 1168962519  # Твой Telegram ID
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

# ===== Проверка и пересылка =====
async def check_and_forward(message):
    text = message.text or ""
    lower_text = text.lower()
    if any(k in lower_text for k in KEYWORDS):
        try:
            # Пересылаем именно как пересланное сообщение
            await user_client.forward_messages(ALERT_CHAT_ID, message)
            print(f"[FORWARDED] {text[:50]}...")
        except Exception as e:
            print(f"[ERROR FORWARDING] {e}")

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
