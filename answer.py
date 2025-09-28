#!/usr/bin/env python3
# coding: utf-8
"""
Телеграм-бот на Telethon: ищет ключевые слова в новых сообщениях и пересылает полный диалог.
После запуска отправляет тестовое сообщение о готовности.
"""

import time
from telethon import TelegramClient, events

# ---------------- CONFIG ----------------
API_ID = 21882740
API_HASH = "c80a68894509d01a93f5acfeabfdd922"

# Можно использовать username или числовой ID
ALERT_USER = "achie_81"  # username
# ALERT_USER = 1168962519  # либо ID

# Ключевые слова для поиска
KEYWORDS = [k.lower() for k in [
    "#html_и_css_верстка",
    "#веб_программирование",
    "#cms",
    "#интернет_магазины_и_электронная_коммерция",
    "#создание_сайта_под_ключ",
    "#дизайн_сайтов"
]]

# ---------------- INIT ----------------
tg_client = TelegramClient("session", API_ID, API_HASH)

# ---------------- HELPERS ----------------
def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

async def send_alert_text(text):
    try:
        entity = await tg_client.get_input_entity(ALERT_USER)
        await tg_client.send_message(entity, text)
        log("Сообщение отправлено")
    except Exception as e:
        log(f"Ошибка при отправке сообщения: {e}")

# ---------------- TELEGRAM ----------------
@tg_client.on(events.NewMessage)
async def on_new_message(event):
    text = (event.message.text or "").lower()
    sender = await event.get_sender()
    sender_name = getattr(sender, 'username', None) or getattr(sender, 'first_name', 'Unknown')

    # Проверка ключевых слов
    if any(k in text for k in KEYWORDS):
        log(f"Найдено ключевое слово в сообщении от {sender_name}")

        # Получаем последние 50 сообщений в диалоге
        try:
            dialog_messages = []
            async for msg in tg_client.iter_messages(event.chat_id, limit=50):
                sender_msg = getattr(msg.sender, 'username', None) or getattr(msg.sender, 'first_name', 'Unknown')
                dialog_messages.append(f"{sender_msg}: {msg.text or ''}")
            full_dialog = "\n".join(reversed(dialog_messages))
        except Exception as e:
            full_dialog = f"Не удалось получить полный диалог: {e}"

        # Отправляем полный диалог себе
        await send_alert_text(f"⚡ Найден проект по ключевому слову в чате '{sender_name}':\n\n{full_dialog}")

# ---------------- START ----------------
async def main():
    log("Запуск Telegram клиента...")
    await tg_client.start()
    log("Клиент запущен, ожидаем новые сообщения...")

    # Отправляем тестовое сообщение о готовности
    await send_alert_text("✅ Бот успешно запущен и готов к работе!")

    # Ожидание новых сообщений
    await tg_client.run_until_disconnected()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
