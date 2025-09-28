import asyncio
import re
from telethon import TelegramClient, events
from telegram import Bot
from collections import deque

# -------- CONFIG --------
API_ID = 21882740
API_HASH = "c80a68894509d01a93f5acfeabfdd922"
BOT_TOKEN = "6566504110:AAFK9hA4jxZ0eA7KZGhVvPe8mL2HZj2tQmE"
ALERT_CHAT_ID = 1168962519

KEYWORDS = ["#cms", "#html_и_css_верстка", "#веб_программирование"]
MIN_TEXT_LENGTH = 15
IGNORE_LINKS = True

# -------- INIT --------
tg_client = TelegramClient("session", API_ID, API_HASH)
alert_bot = Bot(token=BOT_TOKEN)

# очередь сообщений для отправки (чтобы избежать flood)
message_queue = deque()
sent_messages = set()

# -------- HELPERS --------
def contains_keywords(text: str) -> bool:
    return any(k.lower() in text.lower() for k in KEYWORDS)

def is_valid_message(text: str) -> bool:
    if len(text.strip()) < MIN_TEXT_LENGTH:
        return False
    if IGNORE_LINKS and re.search(r"https?://", text):
        return False
    return True

async def process_queue():
    while True:
        if message_queue:
            msg = message_queue.popleft()
            try:
                await alert_bot.send_message(chat_id=ALERT_CHAT_ID, text=msg)
                print(f"[ALERT] {msg}")
                # небольшой тайм-аут между сообщениями, чтобы Telegram не ругался
                await asyncio.sleep(3)
            except Exception as e:
                print(f"[ERROR] Не удалось отправить сообщение: {e}")
        else:
            await asyncio.sleep(1)

# -------- EVENTS --------
@tg_client.on(events.NewMessage)
async def new_message_handler(event):
    if not hasattr(event.message, "message") or not event.message.message:
        return
    text = event.message.message.strip()
    if text in sent_messages:
        return
    if not is_valid_message(text):
        return
    if contains_keywords(text):
        sent_messages.add(text)
        message_queue.append(f"Найдено сообщение с ключевым словом:\n{text}")

# -------- MAIN --------
async def main():
    await tg_client.start()
    print("✅ Telegram клиент запущен. Ожидание сообщений...")
    asyncio.create_task(process_queue())  # запуск очереди на отправку
    await tg_client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
