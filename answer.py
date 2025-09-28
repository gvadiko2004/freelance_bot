#!/usr/bin/env python3
# coding: utf-8
"""
Телеграм-бот, который отслеживает новые сообщения в Telegram, ищет ключевые слова
и пересылает полный диалог на ваш бот (через Bot API).
"""

import re
import time
from telethon import TelegramClient, events
from telegram import Bot

# ---------------- CONFIG ----------------
API_ID = 21882740
API_HASH = "c80a68894509d01a93f5acfeabfdd922"

ALERT_BOT_TOKEN = "6566504110:AAFK9hA4jxZ0eA7KZGhVvPe8mL2HZj2tQmE"  # твой бот
ALERT_CHAT_ID   = 123456789  # <-- сюда вставь свой chat_id, куда бот отправляет

# ключевые слова для поиска
KEYWORDS = [k.lower() for k in [
    "#html_и_css_верстка",
    "#веб_программирование",
    "#cms",
    "#интернет_магазины_и_электронная_коммерция",
    "#создание_сайта_под_ключ",
    "#дизайн_сайтов"
]]

# ---------------- INIT ----------------
alert_bot = Bot(token=ALERT_BOT_TOKEN)
tg_client = TelegramClient("session", API_ID, API_HASH)

# ---------------- HELPERS ----------------
def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

def send_alert_text(text):
    try:
        alert_bot.send_message(chat_id=ALERT_CHAT_ID, text=text)
        log("Отправлено сообщение через бота")
    except Exception as e:
        log(f"Ошибка при отправке сообщения: {e}")

# ---------------- TELEGRAM ----------------
@tg_client.on(events.NewMessage)
async def on_new_message(event):
    text = (event.message.text or "").lower()
    sender = await event.get_sender()
    sender_name = getattr(sender, 'username', None) or getattr(sender, 'first_name', 'Unknown')

    # Проверяем ключевые слова
    if any(k in text for k in KEYWORDS):
        log(f"Найдено ключевое слово в сообщении от {sender_name}")

        # Получаем полный диалог (последние 50 сообщений)
        try:
            dialog_messages = []
            async for msg in tg_client.iter_messages(event.chat_id, limit=50):
                sender_msg = getattr(msg.sender, 'username', None) or getattr(msg.sender, 'first_name', 'Unknown')
                dialog_messages.append(f"{sender_msg}: {msg.text or ''}")
            full_dialog = "\n".join(reversed(dialog_messages))  # от старых к новым
        except Exception as e:
            full_dialog = f"Не удалось получить полный диалог: {e}"

        # Отправляем полный диалог через бота
        send_alert_text(f"⚡ Найден проект по ключевому слову в чате '{sender_name}':\n\n{full_dialog}")

# ---------------- START ----------------
def main():
    log("Запуск Telegram клиента...")
    tg_client.start()
    log("Клиент запущен, ожидаем новые сообщения...")
    tg_client.run_until_disconnected()

if __name__ == "__main__":
    main()
