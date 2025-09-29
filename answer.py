import asyncio
from telethon import TelegramClient, events

# ===== ТВОИ ДАННЫЕ =====
api_id = 21882740
api_hash = "c80a68894509d01a93f5acfeabfdd922"
PHONE_NUMBER = "+380634646075"  # авторизация как пользователь

BOT_TOKEN = "6566504110:AAFK9hA4jxZ0eA7KZGhVvPe8mL2HZj2tQmE"
ALERT_CHAT_ID = 1168962519  # твой Telegram ID

SOURCE_CHAT = "FreelancehuntProjects"  # можно также "https://t.me/FreelancehuntProjects"

KEYWORDS = [
    "wordpress", "верстка", "лендинг", "сайт", 
    "figma", "html", "css", "shopify"
]
KEYWORDS = [k.lower() for k in KEYWORDS]

# ===== Telethon User Client =====
user_client = TelegramClient("user_session", api_id, api_hash)

# ===== Bot Client (для отправки сообщений) =====
bot_client = TelegramClient("bot_session", api_id, api_hash).start(bot_token=BOT_TOKEN)

# ===== Основная логика =====
@user_client.on(events.NewMessage(chats=SOURCE_CHAT))
async def handler(event):
    text = (event.message.text or "").lower()

    if any(k in text for k in KEYWORDS):
        print(f"[MATCH] Найдено ключевое слово -> {text[:50]}...")

        # Пересылаем тебе от имени бота
        try:
            await bot_client.forward_messages(ALERT_CHAT_ID, event.message)
            print("[OK] Сообщение переслано!")
        except Exception as e:
            print(f"[ERROR] Не удалось переслать: {e}")

async def main():
    print("✅ Запуск...")
    await user_client.start(phone=PHONE_NUMBER)
    print("👤 USER авторизован")
    print("🤖 BOT авторизован")
    print("👁 Слежу за FreelancehuntProjects...")

    await user_client.run_until_disconnected()

asyncio.run(main())
