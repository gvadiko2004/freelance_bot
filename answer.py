import re
import asyncio
from telethon import TelegramClient, events

# ===== Настройки Telegram =====
api_id = 21882740
api_hash = "c80a68894509d01a93f5acfeabfdd922"
ALERT_CHAT_ID = 1168962519  # твой Telegram ID

# ===== Ключевые слова =====
KEYWORDS = [
    "#html_и_css_верстка",
    "#веб_программирование",
    "#cms",
    "#интернет_магазины_и_электронная_коммерция",
    "#создание_сайта_под_ключ",
    "#дизайн_сайтов"
]
KEYWORDS = [kw.lower() for kw in KEYWORDS]

# ---------------- Функции ----------------
def extract_links(text: str):
    """Извлекает ссылки Freelancehunt из текста"""
    return [link for link in re.findall(r"https?://[^\s]+", text)
            if link.startswith("https://freelancehunt.com/")]

# ---------------- Telegram ----------------
client = TelegramClient("session", api_id, api_hash)

@client.on(events.NewMessage)
async def handler(event):
    """Обрабатывает новые сообщения и пересылает их если есть ключевые слова"""
    text = (event.message.text or "").lower()
    links = extract_links(text)

    # Проверка ключевых слов и наличия ссылок
    if any(k in text for k in KEYWORDS) and links:
        link = links[0]
        print(f"[INFO] Найден подходящий проект: {link}")
        try:
            # Пересылаем в свой Telegram
            await client.send_message(ALERT_CHAT_ID, f"🔔 Новый проект:\n{link}\n\nСообщение:\n{event.message.text}")
            print("[SUCCESS] Сообщение переслано")
        except Exception as e:
            print(f"[ERROR] Не удалось переслать сообщение: {e}")

# ---------------- Запуск ----------------
async def main():
    print("✅ Бот запущен. Ожидание новых сообщений...")
    await client.start()
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
