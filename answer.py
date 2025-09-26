# answer.py
import asyncio
import re
import json
import logging
from pathlib import Path
import os
from dotenv import load_dotenv
import aiohttp

from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaWebPage, MessageEntityUrl, KeyboardButtonUrl
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# ---------- CONFIG ----------
load_dotenv()

API_ID = int(os.getenv("API_ID", "21882740"))
API_HASH = os.getenv("API_HASH", "c80a68894509d01a93f5acfeabfdd922")
ALERT_BOT_TOKEN = os.getenv("ALERT_BOT_TOKEN", "")
ALERT_CHAT_ID = os.getenv("ALERT_CHAT_ID", "")
FH_LOGIN = os.getenv("FH_LOGIN", "")
FH_PASSWORD = os.getenv("FH_PASSWORD", "")
CAPTCHA_API_KEY = os.getenv("CAPTCHA_API_KEY", "")

KEYWORDS = [
    "#html_и_css_верстка",
    "#веб_программирование",
    "#cms",
    "#интернет_магазины_и_электронная_коммерция",
    "#создание_сайта_под_ключ",
    "#дизайн_сайтов",
]

PROCESSED_FILE = Path("processed_links.json")
BROWSER_STATE_DIR = Path("playwright_state")
BROWSER_STATE_DIR.mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("freelance_bot")

# Load processed links
if PROCESSED_FILE.exists():
    processed = set(json.loads(PROCESSED_FILE.read_text()))
else:
    processed = set()

FH_LINK_RE = re.compile(r"https://freelancehunt\.com[^\s)]+", re.IGNORECASE)

COMMENT_TEMPLATE = (
    "Доброго дня! Готовий виконати роботу якісно.\n"
    "Портфоліо робіт у моєму профілі.\n"
    "Заздалегідь дякую!"
)

# ---------------- Utilities ----------------
async def send_alert(text: str):
    url = f"https://api.telegram.org/bot{ALERT_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": ALERT_CHAT_ID, "text": text}
    async with aiohttp.ClientSession() as sess:
        try:
            async with sess.post(url, json=payload, timeout=10) as r:
                if r.status != 200:
                    logger.warning("Telegram alert failed: %s", await r.text())
        except Exception as e:
            logger.exception("send_alert failed: %s", e)

def save_processed():
    PROCESSED_FILE.write_text(json.dumps(list(processed), ensure_ascii=False, indent=2))

async def solve_captcha_2captcha(session: aiohttp.ClientSession, site_key: str, page_url: str) -> str:
    logger.info("Инициализация reCAPTCHA...")
    api_key = CAPTCHA_API_KEY
    create_url = "http://2captcha.com/in.php"
    get_url = "http://2captcha.com/res.php"
    params = {"key": api_key, "method": "userrecaptcha", "googlekey": site_key, "pageurl": page_url, "json": 1}
    async with session.post(create_url, data=params) as resp:
        j = await resp.json()
    if j.get("status") != 1:
        raise RuntimeError("2captcha create error: " + str(j))
    request_id = j["request"]
    logger.info("reCAPTCHA отправлена на решение, ожидаем результат...")
    for _ in range(30):
        await asyncio.sleep(5)
        async with session.get(get_url, params={"key": api_key, "action":"get", "id":request_id, "json":1}) as r:
            res = await r.json()
        if res.get("status") == 1:
            logger.info("reCAPTCHA решена!")
            return res["request"]
    raise RuntimeError("Captcha solve timeout")

# ---------------- Core ----------------
async def process_fh_link(link: str):
    logger.info("Processing link: %s", link)
    await send_alert(f"Начинаю обработку ссылки: {link}")
    storage_path = str(BROWSER_STATE_DIR / "playwright_storage.json")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state=storage_path if Path(storage_path).exists() else None)
        page = await context.new_page()

        try:
            # Navigate to project page and wait until fully loaded
            await page.goto(link, wait_until="networkidle", timeout=30000)
            logger.info("Страница полностью загружена.")

            # Check for register/login page
            reg_selector = 'a.with-tooltip.btn.btn-primary.btn-md.bottom-margin[href^="https://freelancehunt.com/ua/register/freelancer"]'
            if await page.query_selector(reg_selector):
                logger.info("Register button found -> clicking")
                await page.eval_on_selector(reg_selector, "el => el.click()")
                await page.wait_for_url("https://freelancehunt.com/ua/profile/login", timeout=20000)

            # Login if required
            if "profile/login" in page.url:
                logger.info("На странице логина, выполняю вход")
                await page.fill('input[name="login"]', FH_LOGIN)
                await page.fill('input[name="password"]', FH_PASSWORD)
                await page.click('button[type="submit"]')
                await page.wait_for_load_state('networkidle', timeout=15000)

            # Ensure we are on project page
            if page.url != link:
                await page.goto(link, wait_until="networkidle", timeout=30000)

            # Detect and solve reCAPTCHA if present
            recaptcha_frame = None
            for f in page.frames:
                if "https://www.google.com/recaptcha/api2/anchor" in f.url:
                    recaptcha_frame = f
                    break
            if recaptcha_frame:
                logger.info("reCAPTCHA инициализирована, решаем...")
                site_key = await recaptcha_frame.get_attribute('#recaptcha-anchor', 'data-sitekey')
                async with aiohttp.ClientSession() as session:
                    token = await solve_captcha_2captcha(session, site_key, page.url)
                await page.evaluate(f'document.getElementById("g-recaptcha-response").innerHTML="{token}";')
                logger.info("reCAPTCHA токен введен.")

            # Click "Сделать ставку"
            add_bid_selector = 'a#add-bid, a.with-tooltip.btn.btn-primary.btn-lg.bottom-margin'
            add_btn = await page.query_selector(add_bid_selector)
            if add_btn:
                await add_btn.click()
                await asyncio.sleep(0.7)

            # Fill bid form
            comment_sel = 'textarea[name="comment"], textarea#comment-0'
            if await page.query_selector(comment_sel):
                await page.fill(comment_sel, COMMENT_TEMPLATE + "\nСрок выполнения: 1 день")
                days_sel = 'input[name="days_to_deliver"], input#days_to_deliver-0'
                if await page.query_selector(days_sel):
                    await page.fill(days_sel, "1")
                amount_sel = 'input[name="amount"], input#amount-0'
                if await page.query_selector(amount_sel):
                    await page.fill(amount_sel, "1111")
                submit_sel = 'button#add-0, button[name="add"], button[type="submit"].ladda-button'
                if await page.query_selector(submit_sel):
                    await page.click(submit_sel)
                    logger.info("Ставка отправлена!")
                    await send_alert(f"Отклик отправлен на {link}.")
                else:
                    logger.warning("Не найден submit button.")
            else:
                logger.warning("Форма комментария не найдена.")

            await context.storage_state(path=storage_path)
            logger.info("Состояние браузера сохранено.")

        except PlaywrightTimeoutError:
            logger.error("Таймаут при загрузке страницы или ожидании элемента.")
        except Exception as e:
            logger.exception("Ошибка при обработке ссылки: %s", e)
            await send_alert(f"Ошибка при обработке {link}: {e}")
        finally:
            await context.close()
            await browser.close()

# ---------------- Telegram monitoring ----------------
async def main():
    global processed
    client = TelegramClient("freelance_telethon_session", API_ID, API_HASH)
    await client.start()
    logger.info("Telegram client started.")

    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        # Собираем все ссылки: текст + кнопки
        links = set()
        text = event.raw_text or ""
        lower = text.lower()

        if any(k.lower() in lower for k in KEYWORDS):
            # Ссылки из текста
            links.update(FH_LINK_RE.findall(text))

            # Inline кнопки (urls)
            if event.message.reply_markup:
                for row in event.message.reply_markup.rows:
                    for button in row.buttons:
                        if isinstance(button, KeyboardButtonUrl):
                            links.update(FH_LINK_RE.findall(button.url))

            # entities urls
            if event.message.entities:
                for ent in event.message.entities:
                    if isinstance(ent, MessageEntityUrl):
                        url = text[ent.offset:ent.offset+ent.length]
                        links.update(FH_LINK_RE.findall(url))

            # media webpage (preview link)
            if isinstance(event.message.media, MessageMediaWebPage):
                page_url = event.message.media.webpage.url
                links.update(FH_LINK_RE.findall(page_url))

            if not links:
                logger.info("Ключи найдены, но ссылок freelancehunt нет.")
                return

            for link in links:
                link = link.rstrip('.,)')
                if link in processed:
                    logger.info("Ссылка уже обработана: %s", link)
                    continue
                processed.add(link)
                save_processed()
                asyncio.create_task(process_fh_link(link))
                await send_alert(f"Найдена ссылка с ключевыми словами: {link}")

    logger.info("Запуск мониторинга входящих сообщений...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Остановлено пользователем.")
