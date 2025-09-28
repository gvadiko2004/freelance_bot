#!/usr/bin/env python3
# coding: utf-8

import asyncio
from telethon import TelegramClient, events
from telegram import Bot

# -------- CONFIG --------
API_ID = 21882740
API_HASH = "c80a68894509d01a93f5acfeabfdd922"
BOT_TOKEN = "6566504110:AAFK9hA4jxZ0eA7KZGhVvPe8mL2HZj2tQmE"
ALERT_CHAT_ID = 1168962519

KEYWORDS = [
    "#html_и_css_верстка", "#веб_программирование", "#cms",
    "#интернет_магазины_и_электронная_коммерция",
    "#создание_сайта_под_ключ", "#дизайн_сайтов"
]

# -------- INIT --------
tg_client = TelegramClient("session", API_ID, API_HASH)
alert_bot = Bot(token=BOT_TOKEN)

# -------- HELPERS --------
async def send_alert(msg):
    try:
        await alert_bot.send_message(chat_id=ALERT_CHAT_ID, text=msg)
        print(f"[ALERT] {msg}")
    except Exception as e:
        print(f"[ERROR] Не удалось отправить сообщение: {e}")

def contains_keywords(text):
    text_lower = text.lower()
    return any(k.lower() in text_lower for k in KEYWORDS)

# -------- EVENTS --------
@tg_client.on(events.NewMessage)
async def handler(event):
    text = event.message.message if hasattr(event.message, "message") else str(event.message)
    if contains_keywords(text):
        await send_alert(f"Найдено сообщение с ключевым словом:\n{text}")

# -------- MAIN --------
async def main():
    await tg_client.start()
    print("Telegram клиент запущен. Ожидание сообщений...")
    await tg_client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
