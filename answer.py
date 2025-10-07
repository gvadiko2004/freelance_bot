import asyncio
import re
import requests
import os
import sys
from bs4 import BeautifulSoup
from telethon import TelegramClient, events, Button

# ===== НАСТРОЙКИ =====
api_id = 21882740
api_hash = "c80a68894509d01a93f5acfeabfdd922"
PHONE_NUMBER = "+380634646075"
PASSWORD_2FA = "gvadiko2004"

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

SESSION_FILE = "user_session.session"
RESTART_INTERVAL = 20 * 60  # 20 минут

# ===== Клиенты =====
user_client = TelegramClient(SESSION_FILE, api_id, api_hash)
bot_client = TelegramClient("bot_session", api_id, api_hash).start(bot_token=BOT_TOKEN)

# ===== Отправка сообщений =====
def send_to_bot(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": ALERT_CHAT_ID, "text": text, "disable_web_page_preview": False}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"[ERROR BOT SEND] {e}")

# ===== Извлечение ссылок =====
def extract_links(text):
    return re.findall(r'https?://[^\s]+', text or "")

# ===== Title страницы =====
def get_page_title(url):
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.string.strip() if soup.title else "Без заголовка"
        return title
    except Exception as e:
        return f"[Ошибка title: {e}]"

# ===== Обработка сообщений =====
async def check_and_forward(message):
    text = message.text or ""
    lower_text = text.lower()

    if any(k in lower_text for k in KEYWORDS):
        send_to_bot(f"🔔 Новое сообщение:\n{text}")

        for link in extract_links(text):
            send_to_bot(f"🔗 Ссылка:\n{link}")
            send_to_bot(f"📝 Title:\n{get_page_title(link)}")

        if message.buttons:
            for row in message.buttons:
                for button in row:
                    if isinstance(button, Button) and getattr(button, "url", None):
                        send_to_bot(f"🔘 Кнопка:\n{button.url}")
                        send_to_bot(f"📝 Title:\n{get_page_title(button.url)}")

# ===== Авто-перезапуск =====
async def auto_restart():
    while True:
        await asyncio.sleep(RESTART_INTERVAL)
        send_to_bot("♻️ Перезапуск бота через 20 минут!")
        await user_client.disconnect()
        os.execv(sys.executable, ['python'] + sys.argv)

# ===== Основной мониторинг =====
async def start_monitoring(phone_code=None):
    async def code_callback():
        # Ждём пока пользователь через бот отправит код
        while not start_monitoring.code_value:
            await asyncio.sleep(1)
        return start_monitoring.code_value

    start_monitoring.code_value = phone_code

    await user_client.start(
        phone=PHONE_NUMBER,
        password=lambda: PASSWORD_2FA,
        phone_code_callback=code_callback
    )

    send_to_bot("✅ Бот запущен и работает!")

    asyncio.create_task(auto_restart())

    messages = await user_client.get_messages(SOURCE_CHAT, limit=10)
    for msg in messages:
        await check_and_forward(msg)

    await user_client.run_until_disconnected()

# ===== Переменная для хранения кода =====
start_monitoring.code_value = None

# ===== Команда /start api =====
@bot_client.on(events.NewMessage(pattern="/start api"))
async def start_command(event):
    await event.respond("🚀 Запуск бота! Пожалуйста, отправьте код, который пришёл в Telegram в формате /code 12345")

# ===== Команда /code 12345 =====
@bot_client.on(events.NewMessage(pattern=r"/code (\d+)"))
async def code_command(event):
    code = event.pattern_match.group(1)
    start_monitoring.code_value = code
    await event.respond(f"✅ Код получен: {code}. Продолжаем авторизацию...")
    asyncio.create_task(start_monitoring(phone_code=code))

# ===== Запуск бота =====
if __name__ == "__main__":
    print("Бот запущен, ждём команду /start api и код подтверждения...")
    bot_client.run_until_disconnected()
