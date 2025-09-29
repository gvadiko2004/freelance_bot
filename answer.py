import asyncio
import re
from telethon import TelegramClient, events, Button
from telegram import Bot

# ===== Настройки =====
api_id = 21882740
api_hash = "c80a68894509d01a93f5acfeabfdd922"
SESSION_NAME = "session"

BOT_TOKEN = "6566504110:AAFK9hA4jxZ0eA7KZGhVvPe8mL2HZj2tQmE"
ALERT_CHAT_ID = 1168962519  # твой Telegram ID

TARGET_USERNAME = "achie_81"  # пользователь, чьи сообщения слушаем

KEYWORDS = [
    "#html_и_css_верстка",
    "#веб_программирование",
    "#cms",
    "#интернет_магазины_и_электронная_коммерция",
    "#создание_сайта_под_ключ",
    "#дизайн_сайтов"
]
KEYWORDS = [kw.lower() for kw in KEYWORDS]

# ===== Инициализация =====
alert_bot = Bot(token=BOT_TOKEN)
client = TelegramClient(SESSION_NAME, api_id, api_hash)

# ===== Функции =====
async def send_alert(text):
    try:
        await alert_bot.send_message(chat_id=ALERT_CHAT_ID, text=text)
        print(f"[INFO] Сообщение отправлено:\n{text}")
    except Exception as e:
        print(f"[ERROR] Не удалось отправить сообщение: {e}")

def extract_links(text):
    return re.findall(r'https?://[^\s]+', text)

async def process_buttons(event):
    """Обрабатываем кнопки в сообщении и извлекаем ссылки из ответов"""
    buttons = event.message.buttons or []
    for row in buttons:
        for button in row:
            if isinstance(button, Button):
                try:
                    # Нажимаем кнопку
                    response = await event.click(button)
                    if response and response.text:
                        links = extract_links(response.text)
                        if links:
                            for link in links:
                                await send_alert(f"🔗 Ссылка с кнопки:\n{link}")
                except Exception as e:
                    print(f"[ERROR] Не удалось нажать кнопку: {e}")

# ===== Обработчик новых сообщений =====
@client.on(events.NewMessage(chats=TARGET_USERNAME))
async def handler(event):
    text = (event.message.text or "").lower()

    # Проверяем ключевые слова
    if any(k in text for k in KEYWORDS):
        await send_alert(f"🔔 Новое сообщение с ключевым словом:\n{event.message.text}")

        # Если есть кнопки — обрабатываем их
        await process_buttons(event)

# ===== Запуск =====
async def main():
    print("✅ Бот запущен. Ожидание новых сообщений...")
    await client.start()
    await send_alert("✅ Бот успешно запущен и готов к работе!")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
