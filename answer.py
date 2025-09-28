#!/usr/bin/env python3
# coding: utf-8

import time
from telethon import TelegramClient, events

# ---------------- CONFIG ----------------
API_ID = 21882740
API_HASH = "c80a68894509d01a93f5acfeabfdd922"

YOUR_USER_ID = 1168962519  # <-- Укажи СВОЙ числовой user_id, не username!
CONTEXT_MESSAGES = 5        # Сколько последних сообщений показывать
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
processed_messages = set()

def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

async def send_alert(text):
    try:
        for i in range(0, len(text), 4000):
            await client.send_message(YOUR_USER_ID, text[i:i+4000])
        log("Уведомление отправлено")
    except Exception as e:
        log(f"Ошибка отправки уведомления: {e}")

async def get_context(event, limit=CONTEXT_MESSAGES):
        msgs = []
        try:
            async for msg in client.iter_messages(event.chat_id, limit=limit, reverse=True):
                sender_name = getattr(msg.sender, 'username', None) or getattr(msg.sender, 'first_name', 'Unknown')
                msgs.append(f"{sender_name}: {msg.text or ''}")
        except Exception as e:
            msgs.append(f"[Не удалось получить контекст: {e}]")
        return "\n".join(msgs)

@client.on(events.NewMessage)
async def handle_new_message(event):
    if event.id in processed_messages:
        return
    processed_messages.add(event.id)

    text = (event.message.text or "").lower()

    if any(k in text for k in KEYWORDS):
        sender = await event.get_sender()
        sender_name = getattr(sender, 'username', None) or getattr(sender, 'first_name', 'Unknown')
        chat = await event.get_chat()
        chat_title = getattr(chat, 'title', 'Личный чат')

        log(f"Найдено ключевое слово в '{chat_title}' от {sender_name}")

        context = await get_context(event, CONTEXT_MESSAGES)
        full_text = f"⚡ Найдено ключевое слово в чате '{chat_title}':\n\n{context}"

        await send_alert(full_text)

async def main():
    log("Запуск Telegram клиента...")
    await client.start()
    log("Клиент запущен, ожидаем новые сообщения...")

    await send_alert("✅ Бот успешно запущен и готов к работе!")
    await client.run_until_disconnected()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
