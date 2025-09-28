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

CONTEXT_MESSAGES = 2  # Количество предыдущих сообщений для контекста

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

async def get_context(event, limit=CONTEXT_MESSAGES):
    """Возвращает последние N сообщений перед текущим для контекста"""
    msgs = []
    try:
        async for msg in client.iter_messages(event.chat_id, limit=limit, reverse=True):
            sender_name = getattr(msg.sender, 'username', None) or getattr(msg.sender, 'first_name', 'Unknown')
            msgs.append(f"{sender_name}: {msg.text or ''}")
    except Exception as e:
        msgs.append(f"[Не удалось получить контекст: {e}]")
    return "\n".join(msgs)

# ---------------- MAIN HANDLER ----------------
@client.on(events.NewMessage)
async def handler(event):
    sender = await event.get_sender()
    # Игнорируем свои сообщения
    if sender.is_self:
        return

    # Уникальный идентификатор: chat_id + message_id
    message_key = (event.chat_id, event.id)
    if message_key in processed_messages:
        return
    processed_messages.add(message_key)

    text = (event.message.text or "").lower()

    if any(k in text for k in KEYWORDS):
        chat = await event.get_chat()
        sender_name = getattr(sender, 'username', None) or getattr(sender, 'first_name', 'Unknown')
        chat_name = getattr(chat, 'title', 'Личный чат')

        context_text = await get_context(event, CONTEXT_MESSAGES)
        alert_text = f"⚡ Найдено сообщение:\nЧат: {chat_name}\nОт: {sender_name}\n\nКонтекст:\n{context_text}\n\nСообщение:\n{text}"

        log(f"⚡ Найдено ключевое слово в '{chat_name}' от {sender_name}")
        send_bot_alert(alert_text)

# ---------------- HEARTBEAT ----------------
import asyncio
async def heartbeat():
    while True:
        log("Бот жив и работает...")
        await asyncio.sleep(10)

# ---------------- START ----------------
async def main():
    log("Запуск Telegram клиента...")
    await client.start()
    send_bot_alert("✅ Бот успешно запущен и мониторит чаты!")

    # Запускаем heartbeat параллельно
    asyncio.create_task(heartbeat())

    log("Бот запущен, ждёт события...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
