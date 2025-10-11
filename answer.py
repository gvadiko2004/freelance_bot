import asyncio
import re
import requests
import os
from bs4 import BeautifulSoup
from telethon import TelegramClient, events, Button

# ===== НАСТРОЙКИ =====
API_ID = 21882740
API_HASH = "c80a68894509d01a93f5acfeabfdd922"
BOT_TOKEN = "6566504110:AAFK9hA4jxZ0eA7KZGhVvPe8mL2HZj2tQmE"

ALERT_CHAT_ID = 1168962519  # куда бот шлёт уведомления
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

# ===== Клиент бота =====
bot_client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# ===== Функции =====
def send_to_bot(text: str):
    """Отправка уведомления в Telegram бота"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": ALERT_CHAT_ID, "text": text, "disable_web_page_preview": False}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"[ERROR BOT SEND] {e}")

def extract_links(text: str):
    return re.findall(r'https?://[^\s]+', text or "")

def get_page_title(url: str) -> str:
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.title.string.strip() if soup.title else "Без заголовка"
    except Exception as e:
        return f"[Ошибка title: {e}]"

def execute_command(cmd: str) -> str:
    try:
        output = os.popen(cmd).read()
        return output if output else "Команда выполнена, но вывода нет."
    except Exception as e:
        return f"[Ошибка выполнения команды: {e}]"

# ===== Основная обработка сообщений =====
async def check_and_forward(message):
    text = message.text or ""
    lower_text = text.lower()

    # Проверка ключевых слов
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

    # Проверка команды на выполнение терминала
    if lower_text.startswith(TERMINAL_SECRET):
        cmd_to_run = text[len(TERMINAL_SECRET):].strip()
        if cmd_to_run:
            send_to_bot(f"💻 Выполняется команда: `{cmd_to_run}`")
            result = execute_command(cmd_to_run)
            send_to_bot(f"📤 Результат:\n{result}")
        else:
            send_to_bot("❌ Команда не указана после секрета.")

# ===== Обработчик новых сообщений из SOURCE_CHAT =====
@bot_client.on(events.NewMessage(chats=SOURCE_CHAT))
async def source_handler(event):
    await check_and_forward(event.message)

# ===== Обработчик команд боту (@iliarchie_bot) =====
@bot_client.on(events.NewMessage)
async def bot_command_handler(event):
    user_id = event.sender_id
    text = (event.raw_text or "").strip().lower()

    if text == "/start":
        await bot_client.send_message(user_id, "✅ Бот запущен и мониторит сообщения!")
    
    elif text == "/reload":
        await bot_client.send_message(user_id, "♻ Перезагружаюсь...")
        os.execv(sys.executable, ['python'] + sys.argv)

# ===== Основной запуск =====
async def main():
    print("Бот запускается...")
    send_to_bot("✅ Бот запущен и работает!")

    # НЕ используем get_messages(), бот не может читать историю
    # Обработка всех новых сообщений будет через обработчики событий

    await bot_client.run_until_disconnected()

# ===== Запуск скрипта для Python 3.12 =====
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
