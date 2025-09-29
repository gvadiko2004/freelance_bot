import asyncio
from telethon import TelegramClient, events

# ===== ТВОИ ДАННЫЕ =====
api_id = 21882740
api_hash = "c80a68894509d01a93f5acfeabfdd922"
PHONE_NUMBER = "+380634646075"  # авторизация как пользователь

BOT_TOKEN = "6566504110:AAFK9hA4jxZ0eA7KZGhVvPe8mL2HZj2tQmE"
ALERT_CHAT_ID = 1168962519  # твой Telegram ID

SOURCE_CHAT = "FreelancehuntProjects"  # канал, который слушаем

KEYWORDS = [
    "wordpress", "верстка", "лендинг", "сайт", 
    "figma", "html", "css", "shopify"
]
KEYWORDS = [k.lower() for k in KEYWORDS]

# ===== Telethon User Client =====
user_client = TelegramClient("user_session", api_id, api_hash)
bot_client = TelegramClient("bot_session", api_id, api_hash).start(bot_token=BOT_TOKEN)

# ===== Функция проверки и пересылки =====
async def check_and_forward(message):
    text = (message.text or "").lower()
    if any(k in text for k in KEYWORDS):
        try:
            await bot_client.forward_messages(ALERT_CHAT_ID, message)
            print(f"[TEST-FORWARD] Переслано: {text[:50]}...")
        except Exception as e:
            print(f"[ERROR] Не удалось переслать: {e}")

# ===== LIVE Обработчик =====
@user_client.on(events.NewMessage(chats=SOURCE_CHAT))
async def handler(event):
    await check_and_forward(event.message)

# ===== Тестовый запуск =====
async def test_run():
    print("🔍 Тест — беру последние 3 сообщения из канала...")
    async for msg in user_client.get_messages(SOURCE_CHAT, limit=3):
        await check_and_forward(msg)

# ===== Запуск =====
async def main():
    print("✅ Запуск...")
    await user_client.start(phone=PHONE_NUMBER)
    print("👤 USER авторизован")
    print("🤖 BOT авторизован")

    # Тестовый режим
    await test_run()
    print("⏳ Теперь бот слушает новые сообщения...")

    await user_client.run_until_disconnected()

asyncio.run(main())
