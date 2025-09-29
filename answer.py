from telethon import TelegramClient, events
import asyncio

# ===== НАСТРОЙКИ =====
api_id = 21882740
api_hash = "c80a68894509d01a93f5acfeabfdd922"
PHONE_NUMBER = "+380634646075"  # Авторизация как пользователь

BOT_TOKEN = "6566504110:AAFK9hA4jxZ0eA7KZGhVvPe8mL2HZj2tQmE"
ALERT_CHAT_ID = 1168962519  # Твой личный Telegram ID

SOURCE_CHAT = "FreelancehuntProjects"  # Канал, который слушаем

KEYWORDS = [
    "#html_и_css_верстка",
    "#веб_программирование",
    "#cms",
    "#интернет_магазины_и_электронная_коммерция",
    "#создание_сайта_под_ключ",
    "#дизайн_сайтов"
]
KEYWORDS = [k.lower() for k in KEYWORDS]

# ===== Клиенты =====
user_client = TelegramClient("user_session", api_id, api_hash)
bot_client = TelegramClient("bot_session", api_id, api_hash)

# ===== Проверка сообщения и пересылка =====
async def check_and_forward(message):
    text = (message.text or "").lower()
    if any(k in text for k in KEYWORDS):
        try:
            await bot_client.forward_messages(ALERT_CHAT_ID, message)
            print(f"[FORWARDED] {text[:50]}...")
        except Exception as e:
            print(f"[ERROR FORWARDING] {e}")

# ===== Реальный мониторинг канала =====
@user_client.on(events.NewMessage(chats=SOURCE_CHAT))
async def handler(event):
    await check_and_forward(event.message)

# ===== Основная функция =====
async def main():
    await user_client.start(phone=PHONE_NUMBER)
    await bot_client.start(bot_token=BOT_TOKEN)
    print("✅ USER и BOT авторизованы")

    print("🔍 Тест — беру последние 3 сообщения...")
    async for msg in user_client.get_messages(SOURCE_CHAT, limit=3):
        await check_and_forward(msg)

    print("👁 Теперь слушаю новые сообщения...")
    await user_client.run_until_disconnected()

# ===== ЗАПУСК =====
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
