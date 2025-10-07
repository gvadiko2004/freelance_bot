import asyncio
import re
import requests
from bs4 import BeautifulSoup
from telethon import TelegramClient, events, Button
from telethon.errors import SessionPasswordNeededError

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

# ===== Обработка сообщений канала =====
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
        import os, sys
        os.execv(sys.executable, ['python'] + sys.argv)

# ===== Функция авторизации =====
async def authorize():
    await user_client.connect()
    if await user_client.is_user_authorized():
        send_to_bot("✅ Клиент уже авторизован!")
        asyncio.create_task(start_monitoring())
        return

    # Отправляем запрос кода
    await user_client.send_code_request(PHONE_NUMBER)
    send_to_bot("📩 Запрос кода отправлен Telegram. Ждём код...")

    # Ждём автоматически код от Telegram
    code_event = asyncio.Event()
    code_value = {"code": None}

    @user_client.on(events.NewMessage(from_users="Telegram"))
    async def code_listener(event):
        text = event.message.message or ""
        match = re.search(r'Код для входа в Telegram:\s*(\d+)', text)
        if match:
            code_value["code"] = match.group(1)
            code_event.set()
            await bot_client.send_message(ALERT_CHAT_ID, f"🔑 Код автоматически получен: {code_value['code']}")

    await code_event.wait()
    try:
        await user_client.sign_in(PHONE_NUMBER, code_value["code"])
    except SessionPasswordNeededError:
        await user_client.sign_in(password=PASSWORD_2FA)
    send_to_bot("✅ Авторизация выполнена!")

    asyncio.create_task(start_monitoring())

# ===== Мониторинг канала =====
async def start_monitoring():
    @user_client.on(events.NewMessage(chats=SOURCE_CHAT))
    async def channel_handler(event):
        await check_and_forward(event.message)

    send_to_bot("🚀 Мониторинг канала запущен!")
    await user_client.run_until_disconnected()

# ===== Команда /start api =====
@bot_client.on(events.NewMessage(pattern="/start api"))
async def start_command(event):
    await event.respond("🚀 Запуск бота и автоматическая авторизация...")
    asyncio.create_task(authorize())

# ===== Запуск бота =====
if __name__ == "__main__":
    print("Бот запущен, ждём /start api...")
    bot_client.run_until_disconnected()
