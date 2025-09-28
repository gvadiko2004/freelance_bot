#!/usr/bin/env python3
# coding: utf-8
"""
Telegram bot — отслеживает новые сообщения, ищет ключевые слова и пересылает полный диалог.
"""

import re
import time
from telethon import TelegramClient, events
from telegram import Bot  # для пересылки в TG (опционально)

# ---------------- CONFIG ----------------
API_ID = 21882740
API_HASH = "c80a68894509d01a93f5acfeabfdd922"

ALERT_BOT_TOKEN = ""      # <-- Впиши сюда токен бота Telegram (куда пересылать)
ALERT_CHAT_ID   = 0       # <-- Впиши chat_id

KEYWORDS = [k.lower() for k in [
    "#html_и_css_верстка","#веб_программирование","#cms",
    "#интернет_магазины_и_электронная_коммерция","#создание_сайта_под_ключ","#дизайн_сайтов"
]]

# ---------------- INIT ----------------
alert_bot = Bot(token=ALERT_BOT_TOKEN) if ALERT_BOT_TOKEN else None
tg_client = TelegramClient("session", API_ID, API_HASH)

# ---------------- HELPERS ----------------
def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

def send_alert_text(text):
    log(f"ALERT: {text}")
    if alert_bot and ALERT_CHAT_ID:
        try:
            alert_bot.send_message(chat_id=ALERT_CHAT_ID, text=text)
        except Exception as e:
            log(f"Failed to send TG alert: {e}")

# ---------------- TELEGRAM ----------------
@tg_client.on(events.NewMessage)
async def on_msg(event):
    text = (event.message.text or "").lower()
    sender = await event.get_sender()
    sender_name = getattr(sender, 'username', None) or getattr(sender, 'first_name', 'Unknown')

    # Проверяем ключевые слова
    if any(k in text for k in KEYWORDS):
        log(f"Найдено ключевое слово в сообщении от {sender_name}")

        # Получаем полный диалог
        try:
            dialog_messages = []
            async for msg in tg_client.iter_messages(event.chat_id, limit=50):
                sender_msg = getattr(msg.sender, 'username', None) or getattr(msg.sender, 'first_name', 'Unknown')
                dialog_messages.append(f"{sender_msg}: {msg.text or ''}")
            full_dialog = "\n".join(reversed(dialog_messages))  # от старых к новым
        except Exception as e:
            full_dialog = f"Не удалось получить полный диалог: {e}"

        # Отправляем полный диалог себе
        send_alert_text(f"⚡ Найден проект по ключевому слову в чате '{sender_name}':\n\n{full_dialog}")

# ---------------- START ----------------
def main():
    log("Запуск Telegram клиента...")
    tg_client.start()
    log("Клиент запущен, ожидаем сообщения...")
    tg_client.run_until_disconnected()

if __name__ == "__main__":
    main()
