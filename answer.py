#!/usr/bin/env python3
# coding: utf-8

import time
from telethon import TelegramClient, events

# ---------------- CONFIG ----------------
API_ID = 21882740
API_HASH = "c80a68894509d01a93f5acfeabfdd922"

YOUR_USERNAME = "iliarchie_bot"  # Кому бот будет отправлять уведомления
CONTEXT_MESSAGES = 3              # Количество сообщений для контекста
KEYWORDS = [k.lower() for k in [
    "#html_и_css_верстка",
    "#веб_программирование",
    "#cms",
    "#интернет_магазины_и_электронная_коммерция",
    "#создание_сайта_под_ключ",
    "#дизайн_сайтов"
]]

# ---------------- INIT ----------------
client = TelegramClient("session", API_ID, API_HASH)
processed_messages = set()  # чтобы не дублировать уведомления

# ---------------- HELPERS ----------------
def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

async def send_alert(text):
    try:
        entity = await client.get_input_entity(YOUR_USERNAME)
        # Разбиваем длинные сообщения на куски ≤ 4000 символов
        for i in range(0, len(text), 4000):
            await client.send_message(entity, text[i:i+4000])
        log("Уведомление отправлено")
    except Exception as e:
        log(f"Ошибка отправки уведомления: {e}")

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

# ---------------- EVENTS ----------------
@client.on(events.NewMessage)
async def handle_new_message(event):
    if event.id in processed_messages:
        return
    processed_messages.add(event.id)

    text = (event.message.text or "").lower()
    if any(k in text for k in KEYWORDS):
        sender = await event.get_sender()
        sender_name = getattr(sender, 'username', None) or getattr(sender, 'first_name', 'Unknown')
        log(f"Найдено ключевое слово в сообщении от {sender_name}")

        context = await get_context(event, CONTEXT_MESSAGES)
        full_text = f"⚡ Найден проект по ключевому слову в чате '{sender_name}':\n\n{context}"
        await send_alert(full_text)

# ---------------- START ----------------
async def main():
    log("Запуск Telegram клиента...")
    await client.start()
    log("Клиент запущен, ожидаем новые сообщения...")

    # Отправляем тестовое уведомление
    await send_alert("✅ Бот успешно запущен и готов к работе!")

    await client.run_until_disconnected()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
