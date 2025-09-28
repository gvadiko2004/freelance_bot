#!/usr/bin/env python3
# coding: utf-8

import asyncio, re
from telethon import TelegramClient, events
from telegram import Bot

# --- CONFIG ---
API_ID = 21882740
API_HASH = "c80a68894509d01a93f5acfeabfdd922"
BOT_TOKEN = "6566504110:AAFK9hA4jxZ0eA7KZGhVvPe8mL2HZj2tQmE"
OWNER_ID = 1168962519  # твой Telegram ID

# ключевые слова (поиск ведется без регистра)
KEYWORDS = [k.lower() for k in [
    "#html_и_css_верстка",
    "#веб_программирование",
    "#cms",
    "#интернет_магазины_и_электронная_коммерция",
    "#создание_сайта_под_ключ",
    "#дизайн_сайтов"
]]

# --- INIT ---
tg_client = TelegramClient("session", API_ID, API_HASH)
alert_bot = Bot(token=BOT_TOKEN)

# --- HELPERS ---
def extract_links(msg):
    """Ищет ссылки в тексте и в кнопках"""
    text = msg.message or ""
    links = []

    # ссылки из текста
    urls = re.findall(r"https?://[^\s)]+", text)
    links.extend(urls)

    # ссылки из inline кнопок
    try:
        for row in getattr(msg, "buttons", []) or []:
            for btn in row:
                url = getattr(btn, "url", None)
                if url:
                    links.append(url)
    except:
        pass

    # убираем дубликаты и **звёздочки**
    clean = []
    for link in links:
        link = link.replace("*", "").strip()
        if link not in clean:
            clean.append(link)

    return clean

# --- MAIN HANDLER ---
@tg_client.on(events.NewMessage)
async def handle_message(event):
    text = (event.message.text or "").lower()
    if not any(k in text for k in KEYWORDS):
        return  # если нет ключевых слов — выходим

    links = extract_links(event.message)
    msg_text = event.message.text or ""

    report = f"🔍 Найдено сообщение по ключевому слову!\n\n"
    report += f"👤 От: {event.chat.title if event.chat else 'личка'}\n\n"
    report += f"📄 Текст:\n{msg_text}\n\n"

    if links:
        report += "🔗 Ссылки:\n" + "\n".join(links)
    else:
        report += "❌ Ссылок не найдено"

    try:
        await alert_bot.send_message(chat_id=OWNER_ID, text=report)
        print(f"[INFO] Переслано сообщение: {event.id}")
    except Exception as e:
        print(f"[ERROR] Не удалось отправить сообщение: {e}")

# --- MAIN LOOP ---
async def main():
    await tg_client.start()
    print("✅ Мониторинг Telegram запущен...")
    await tg_client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Остановка бота")
