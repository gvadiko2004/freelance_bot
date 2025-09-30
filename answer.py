import asyncio
import re
import requests
from bs4 import BeautifulSoup
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession

# ===== НАСТРОЙКИ =====
api_id = 21882740
api_hash = "c80a68894509d01a93f5acfeabfdd922"
PHONE_NUMBER = "+380634646075"

BOT_TOKEN = "6566504110:AAFK9hA4jxZ0eA7KZGhVvPe8mL2HZj2tQmE"
ALERT_CHAT_ID = 1168962519

SOURCE_CHAT = "FreelancehuntProjects"

KEYWORDS = [
    "#html_и_css_верстка",
    "#веб_программирование",
    "#cms",
    "#интернет_магазины_и_электронная_коммерция",
    "#создание_сайта_под_ключ",
    "#дизайн_сайтов"
]
KEYWORDS = [k.lower() for k in KEYWORDS]

# ===== Клиент User =====
user_client = TelegramClient(StringSession(), api_id, api_hash)

# ===== Отправка сообщений в бота =====
def send_to_bot(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": ALERT_CHAT_ID, "text": text, "disable_web_page_preview": False}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"[ERROR BOT SEND] {e}")

# ===== Извлечение ссылок из текста =====
def extract_links(text):
    return re.findall(r'https?://[^\s]+', text or "")

# ===== Получение title страницы =====
def get_page_title(url):
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.string.strip() if soup.title else "Без заголовка"
        return title
    except Exception as e:
        return f"[Ошибка при получении title: {e}]"

# ===== Обработка сообщения =====
async def check_and_forward(message):
    text = message.text or ""
    lower_text = text.lower()

    if any(k in lower_text for k in KEYWORDS):
        send_to_bot(f"🔔 Новое сообщение:\n{text}")

        for link in extract_links(text):
            send_to_bot(f"🔗 Ссылка из текста:\n{link}")
            page_title = get_page_title(link)
            send_to_bot(f"📝 Title страницы:\n{page_title}")

        buttons = message.buttons or []
        for row in buttons:
            for button in row:
                if isinstance(button, Button) and hasattr(button, "url") and button.url:
                    send_to_bot(f"🔘 Ссылка с кнопки:\n{button.url}")
                    page_title = get_page_title(button.url)
                    send_to_bot(f"📝 Title страницы:\n{page_title}")

        print(f"[SENT TO BOT] {text[:50]}...")

# ===== Обработчик новых сообщений =====
@user_client.on(events.NewMessage(chats=SOURCE_CHAT))
async def handler(event):
    await check_and_forward(event.message)

# ===== Основной запуск с уведомлением =====
async def main():
    await user_client.start(phone=PHONE_NUMBER)
    print("✅ USER авторизован")
    send_to_bot("✅ Бот запущен и слушает канал!")

    try:
        print("🔍 Загружаю последние 10 сообщений...")
        messages = await user_client.get_messages(SOURCE_CHAT, limit=10)
        for msg in messages:
            await check_and_forward(msg)

        print("👁 Ожидание новых сообщений...")
        await user_client.run_until_disconnected()

    except Exception as e:
        send_to_bot(f"❌ Бот упал с ошибкой:\n{e}")

    finally:
        send_to_bot("⚠️ Бот остановлен или отключён!")
        print("🔒 Отключение клиента...")
        await user_client.disconnect()

# ===== Запуск =====
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except Exception as e:
        send_to_bot(f"🔥 Критическая ошибка запуска:\n{e}")
