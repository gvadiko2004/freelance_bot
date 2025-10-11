


import asyncio
import re
import requests
import os
import sys
from bs4 import BeautifulSoup
from telethon import TelegramClient, events, Button

# ===== НАСТРОЙКИ =====
API_ID = 21882740
API_HASH = "c80a68894509d01a93f5acfeabfdd922"
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

TERMINAL_SECRET = "run_server_code"  # код для запуска команд на VPS

# ===== Клиент =====
user_client = TelegramClient("freelance_user", API_ID, API_HASH)

# ===== Отправка сообщений в бота =====
def send_to_bot(text: str):
    """Отправка уведомления в Telegram бота"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": ALERT_CHAT_ID, "text": text, "disable_web_page_preview": False}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"[ERROR BOT SEND] {e}")

# ===== Извлечение ссылок =====
def extract_links(text: str):
    """Возвращает все ссылки из текста"""
    return re.findall(r'https?://[^\s]+', text or "")

# ===== Получение Title страницы =====
def get_page_title(url: str) -> str:
    """Возвращает title страницы по ссылке"""
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.title.string.strip() if soup.title else "Без заголовка"
    except Exception as e:
        return f"[Ошибка title: {e}]"

# ===== Выполнение команды на VPS =====
def execute_command(cmd: str) -> str:
    """Выполняет команду на сервере и возвращает вывод"""
    try:
        output = os.popen(cmd).read()
        return output if output else "Команда выполнена, но вывода нет."
    except Exception as e:
        return f"[Ошибка выполнения команды: {e}]"

# ===== Обработка сообщений =====
async def check_and_forward(message):
    text = message.text or ""
    lower_text = text.lower()

    # Проверка ключевых слов
    if any(k in lower_text for k in KEYWORDS):
        send_to_bot(f"🔔 Новое сообщение:\n{text}")

        for link in extract_links(text):
            send_to_bot(f"🔗 Ссылка:\n{link}")
            send_to_bot(f"📝 Title:\n{get_page_title(link)}")

        # Проверка кнопок с URL
        if message.buttons:
            for row in message.buttons:
                for button in row:
                    if isinstance(button, Button) and getattr(button, "url", None):
                        send_to_bot(f"🔘 Кнопка:\n{button.url}")
                        send_to_bot(f"📝 Title:\n{get_page_title(button.url)}")

    # Проверка команды на выполнение терминала
    if lower_text.startswith(TERMINAL_SECRET):
        cmd_to_run = text[len(TERMINAL_SECRET):].strip()
        if cmd_to_run:
            send_to_bot(f"💻 Выполняется команда: `{cmd_to_run}`")
            result = execute_command(cmd_to_run)
            send_to_bot(f"📤 Результат:\n{result}")
        else:
            send_to_bot("❌ Команда не указана после секрета.")

# ===== Обработчик новых сообщений =====
@user_client.on(events.NewMessage(chats=SOURCE_CHAT))
async def handler(event):
    await check_and_forward(event.message)

# ===== Основной запуск бота =====
async def main():
    await user_client.start(phone=PHONE_NUMBER)
    send_to_bot("✅ Бот запущен и работает!")

    # Обработка последних сообщений
    messages = await user_client.get_messages(SOURCE_CHAT, limit=10)
    for msg in messages:
        await check_and_forward(msg)

    await user_client.run_until_disconnected()

# ===== Запуск =====
if __name__ == "__main__":
    asyncio.run(main())
