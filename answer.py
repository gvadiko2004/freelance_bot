#!/usr/bin/env python3
# coding: utf-8

import time
from telethon import TelegramClient, events

# ---------------- CONFIG ----------------
API_ID = 21882740
API_HASH = "c80a68894509d01a93f5acfeabfdd922"

YOUR_USER_ID = 1168962519  # <-- твой Telegram ID
KEYWORDS = [k.lower() for k in [
    "html", "верстка", "сайт", "wordpress", "лендинг",
    "магазин", "веб", "cms", "дизайн", "разработка"
]]

# ---------------- INIT ----------------
client = TelegramClient("session", API_ID, API_HASH)

def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

# ---------------- MAIN HANDLER ----------------
@client.on(events.NewMessage)
async def handler(event):
    text = (event.message.text or "").lower()

    if any(k in text for k in KEYWORDS):
        try:
            sender = await event.get_sender()
            chat = await event.get_chat()
            sender_name = getattr(sender, 'username', None) or getattr(sender, 'first_name', 'Unknown')
            chat_name = getattr(chat, 'title', 'Личный чат')

            log(f"⚡ Найдено ключевое слово в '{chat_name}' от {sender_name}. Пересылаю...")

            await client.forward_messages(YOUR_USER_ID, event.message)

        except Exception as e:
            log(f"Ошибка при пересылке: {e}")

# ---------------- START ----------------
async def main():
    log("Запуск Telegram клиента...")
    await client.start()
    await client.send_message(YOUR_USER_ID, "✅ Бот запущен и мониторит все твои чаты!")
    log("Бот запущен, ждёт новые сообщения...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
