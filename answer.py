#!/usr/bin/env python3
# coding: utf-8

import time
import requests
import asyncio
from telethon import TelegramClient, events

# ---------------- CONFIG ----------------
API_ID = 21882740
API_HASH = "c80a68894509d01a93f5acfeabfdd922"

BOT_TOKEN = "6566504110:AAFK9hA4jxZ0eA7KZGhVvPe8mL2HZj2tQmE"
ALERT_USER_ID = 1168962519  # Куда слать уведомления

KEYWORDS = [k.lower() for k in [
    "html", "верстка", "сайт", "wordpress", "лендинг",
    "магазин", "веб", "cms", "дизайн", "разработка"
]]

# ---------------- INIT ----------------
client = TelegramClient("session", API_ID, API_HASH)
processed_messages = set()  # Чтобы не слать дубликаты

# ---------------- HELPERS ----------------
def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

def send_bot_alert(text):
    """Отправка уведомления через Telegram Bot API"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": ALERT_USER_ID, "text": text}
    try:
        requests.post(url, data=data)
        log("Уведомление отправлено ботом")
    except Exception as e:
        log(f"Ошибка отправки через бота: {e}")

# ---------------- MAIN HANDLER ----------------
@client.on(events.NewMessage)
async def handler(event):
    sender = await event.get_sender()
    if sender.is_self:
        return

    # Уникальный ключ для предотвращения дубликатов
    message_key = (event.chat_id, event.id)
    if message_key in processed_messages:
        return
    processed_messages.add(message_key)

    text = (event.message.text or "").lower()
    if any(k in text for k in KEYWORDS):
        chat = await event.get_chat()
        chat_name = getattr(chat, 'title', 'Личный чат')
        sender_name = getattr(sender, 'username', None) or getattr(sender, 'first_name', 'Unknown')

        alert_text = f"⚡ Новое сообщение с ключевым словом:\nЧат: {chat_name}\nОт: {sender_name}\n\nСообщение:\n{text}"

        log(f"⚡ Найдено ключевое слово в '{chat_name}' от {sender_name}")
        send_bot_alert(alert_text)

# ---------------- HEARTBEAT ----------------
async def heartbeat():
    while True:
        log("Бот жив и работает...")
        await asyncio.sleep(10)

# ---------------- START ----------------
async def main():
    log("Запуск Telegram клиента...")
    await client.start()
    send_bot_alert("✅ Бот успешно запущен и мониторит чаты!")

    asyncio.create_task(heartbeat())

    log("Бот запущен, ждёт новых сообщений...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
