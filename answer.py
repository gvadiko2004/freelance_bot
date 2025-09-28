#!/usr/bin/env python3
# coding: utf-8

import time
import requests
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
    # Игнорируем свои сообщения
    sender = await event.get_sender()
    if sender.is_self:
        return

    # Проверяем, чтобы уведомление отправлялось один раз
    if event.id in processed_messages:
        return
    processed_messages.add(event.id)

    text = (event.message.text or "").lower()

    if any(k in text for k in KEYWORDS):
        chat = await event.get_chat()

        sender_name = getattr(sender, 'username', None) or getattr(sender, 'first_name', 'Unknown')
        chat_name = getattr(chat, 'title', 'Личный чат')

        log(f"⚡ Найдено ключевое слово в '{chat_name}' от {sender_name}")

        alert_text = f"⚡ Найдено сообщение:\nЧат: {chat_name}\nОт: {sender_name}\n\n{text}"
        send_bot_alert(alert_text)

# ---------------- START ----------------
async def main():
    log("Запуск Telegram клиента...")
    await client.start()
    send_bot_alert("✅ Бот успешно запущен и мониторит чаты!")
    log("Бот запущен, ждёт события...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
