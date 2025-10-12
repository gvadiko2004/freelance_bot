import asyncio
import re
import requests
import os
import subprocess
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

BOT_PATH = "/root/freelance_bot"  # путь к текущей папке
VENV_PATH = f"{BOT_PATH}/venv/bin/activate"

# ===== Клиент =====
user_client = TelegramClient("freelance_user", API_ID, API_HASH)
watchdog_client = TelegramClient("watchdog", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# ===== Отправка сообщений =====
def send_to_bot(text, buttons=None):
    try:
        watchdog_client.loop.create_task(
            watchdog_client.send_message(ALERT_CHAT_ID, text, buttons=buttons)
        )
    except Exception as e:
        print(f"[ERROR BOT SEND] {e}")

# ===== Извлечение ссылок =====
def extract_links(text: str):
    return re.findall(r'https?://[^\s]+', text or "")

# ===== Получение Title =====
def get_page_title(url: str) -> str:
    try:
        r = requests.get(url, timeout=5)
        soup = BeautifulSoup(r.text, "html.parser")
        return soup.title.string.strip() if soup.title else "Без заголовка"
    except Exception as e:
        return f"[Ошибка title: {e}]"

# ===== Выполнение команды =====
def execute_command(cmd: str):
    try:
        output = os.popen(cmd).read()
        return output if output else "Команда выполнена, но вывода нет."
    except Exception as e:
        return f"[Ошибка выполнения команды: {e}]"

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
                    if getattr(button, "url", None):
                        send_to_bot(f"🔘 Кнопка:\n{button.url}")
                        send_to_bot(f"📝 Title:\n{get_page_title(button.url)}")

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

# ===== Обработчик кнопки Start =====
@watchdog_client.on(events.CallbackQuery)
async def callback_handler(event):
    if event.data == b"start_bot":
        cmd = f"cd {BOT_PATH} && source {VENV_PATH} && python answer.py &"
        os.system(cmd)
        await event.answer("Команда отправлена в терминал ✅")

# ===== Watchdog =====
def is_bot_running():
    result = subprocess.run(["pgrep", "-f", "answer.py"], stdout=subprocess.PIPE)
    return bool(result.stdout.strip())

async def monitor():
    while True:
        if not is_bot_running():
            # Уведомление в Telegram
            send_to_bot(
                "⚠️ Бот упал! Перезапуск автоматически запускается.",
                buttons=[[Button.inline("🚀 Start", b"start_bot")]]
            )
            # Автоперезапуск
            cmd = f"cd {BOT_PATH} && source {VENV_PATH} && python answer.py &"
            os.system(cmd)
        await asyncio.sleep(60)  # проверка каждые 60 секунд

# ===== Основной запуск =====
async def main():
    await user_client.start(phone=PHONE_NUMBER)
    send_to_bot("✅ Бот запущен и работает!")

    messages = await user_client.get_messages(SOURCE_CHAT, limit=10)
    for msg in messages:
        await check_and_forward(msg)

    # Запуск watchdog в фоне
    asyncio.create_task(monitor())

    await user_client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
