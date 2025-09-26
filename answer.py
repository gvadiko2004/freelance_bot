# answer.py
import asyncio
import re
import json
import time
import logging
from pathlib import Path
from dotenv import load_dotenv
import os
import aiohttp

# Telethon (async)
from telethon import TelegramClient, events

# Playwright async
from playwright.async_api import async_playwright

# ---------- CONFIG ----------
# Для безопасности можно вынести в .env, пример .env:
# API_ID=21882740
# API_HASH=c80a68894509d01a93f5acfeabfdd922
# ALERT_BOT_TOKEN=6566504110:AAFK9hA4jxZ0eA7KZGhVvPe8mL2HZj2tQmE
# ALERT_CHAT_ID=1168962519
# FH_LOGIN=Vlari
# FH_PASSWORD=Gvadiko_2004
# CAPTCHA_API_KEY=898059857fb8c709ca5c9613d44ffae4

load_dotenv()

API_ID = int(os.getenv("API_ID", "21882740"))
API_HASH = os.getenv("API_HASH", "c80a68894509d01a93f5acfeabfdd922")
ALERT_BOT_TOKEN = os.getenv("ALERT_BOT_TOKEN", "6566504110:AAFK9hA4jxZ0eA7KZGhVvPe8mL2HZj2tQmE")
ALERT_CHAT_ID = os.getenv("ALERT_CHAT_ID", "1168962519")
FH_LOGIN = os.getenv("FH_LOGIN", "Vlari")
FH_PASSWORD = os.getenv("FH_PASSWORD", "Gvadiko_2004")
CAPTCHA_API_KEY = os.getenv("CAPTCHA_API_KEY", "898059857fb8c709ca5c9613d44ffae4")

# keywords (lowercase)
KEYWORDS = [
    "#html_и_css_верстка",
    "#веб_программирование",
    "#cms",
    "#интернет_магазины_и_электронная_коммерция",
    "#создание_сайта_под_ключ",
    "#дизайн_сайтов",
]

PROCESSED_FILE = Path("processed_links.json")
BROWSER_STATE_DIR = Path("playwright_state")  # where cookies / storage will be stored
BROWSER_STATE_DIR.mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("freelance_bot")

# Load processed links
if PROCESSED_FILE.exists():
    processed = set(json.loads(PROCESSED_FILE.read_text()))
else:
    processed = set()

# Regex to find freelancehunt links
FH_LINK_RE = re.compile(r"https://freelancehunt\.com[^\s)]+", re.IGNORECASE)

# Template for comment (you requested)
COMMENT_TEMPLATE = (
    "Доброго дня! Готовий виконати роботу якісно.\n"
    "Портфоліо робіт у моєму профілі.\n"
    "Заздалегідь дякую!"
)

# ---------------- utilities ----------------
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

# Optional: 2captcha solver (very basic flow). You must adapt to the specific widget (sitekey + pageurl).
async def solve_captcha_2captcha(session: aiohttp.ClientSession, site_key: str, page_url: str) -> str:
    # This is a simple 2captcha flow: send request, poll for result
    api_key = CAPTCHA_API_KEY
    create_url = "http://2captcha.com/in.php"
    get_url = "http://2captcha.com/res.php"
    params = {
        "key": api_key,
        "method": "userrecaptcha",
        "googlekey": site_key,
        "pageurl": page_url,
        "json": 1
    }
    async with session.post(create_url, data=params) as resp:
        j = await resp.json()
    if j.get("status") != 1:
        raise RuntimeError("2captcha create error: " + str(j))
    request_id = j["request"]
    # poll
    for _ in range(30):
        await asyncio.sleep(5)
        async with session.get(get_url, params={"key": api_key, "action":"get", "id":request_id, "json":1}) as r:
            res = await r.json()
        if res.get("status") == 1:
            return res["request"]
    raise RuntimeError("Captcha solve timeout")

# ---------------- core: process link with Playwright ----------------
async def process_fh_link(link: str):
    logger.info("Processing link: %s", link)
    await send_alert(f"Начинаю обработку ссылки: {link}")
    # Use playwright async and persistent context to keep cookies
    storage_path = str(BROWSER_STATE_DIR / "playwright_storage.json")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # headless=False для визуального дебага; можно True
        # create persistent context using storage state file to persist cookies/localStorage
        context = await browser.new_context(storage_state=storage_path if Path(storage_path).exists() else None)
        page = await context.new_page()

        try:
            # Open the link
            await page.goto(link, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(1)

            # If on a page that shows register button (first-time opening), find the register link and click
            # selector from your HTML snippet:
            reg_sel = 'a.with-tooltip.btn.btn-primary.btn-md.bottom-margin[href^="https://freelancehunt.com/ua/register/freelancer"]'
            if await page.query_selector(reg_sel):
                logger.info("Register button found -> clicking")
                await send_alert("Найдена кнопка регистрации — кликаю и буду логиниться.")
                # click via JS to be safe
                await page.eval_on_selector(reg_sel, "el => el.click()")
                # Wait for redirect to login page (they said login page is https://freelancehunt.com/ua/profile/login)
                await page.wait_for_url("https://freelancehunt.com/ua/profile/login", timeout=20000)
                await asyncio.sleep(1)

            # If we are on login page and not logged in, perform login
            if "profile/login" in page.url:
                logger.info("On login page, performing login")
                # Type login and password like a human
                # Fill login
                await page.focus('input[name="login"]')
                # clear & type
                await page.fill('input[name="login"]', '')
                for ch in FH_LOGIN:
                    await page.keyboard.type(ch, delay=120)  # delay ms per char
                await asyncio.sleep(0.3)
                await page.focus('input[name="password"]')
                await page.fill('input[name="password"]', '')
                for ch in FH_PASSWORD:
                    await page.keyboard.type(ch, delay=120)
                await asyncio.sleep(0.5)
                # Submit form
                # click submit button
                await page.click('button[type="submit"]')
                # Wait for navigation back to original project link or another page
                try:
                    await page.wait_for_load_state('networkidle', timeout=15000)
                except Exception:
                    pass
                await asyncio.sleep(1)

            # After login, ensure we are on the project page — if not, navigate to it
            if page.url != link:
                logger.info("Navigating to original project link after login")
                await page.goto(link, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(1)

            # Now look for "Сделать ставку" button and click
            add_bid_selector = 'a#add-bid, a.with-tooltip.btn.btn-primary.btn-lg.bottom-margin'
            add_btn = await page.query_selector(add_bid_selector)
            if add_btn:
                logger.info("Found 'Сделать ставку' -> clicking")
                await add_btn.click()
                await asyncio.sleep(0.7)
            else:
                logger.warning("Не найден элемент 'Сделать ставку' — пытаюсь открыть add-bid-form")
                # try to open collapse by JS
                await page.evaluate("""
                    () => {
                        const el = document.querySelector('#add-bid');
                        if(el) el.click();
                    }
                """)
                await asyncio.sleep(0.7)

            # Wait for form to appear
            # Fill comment
            comment_sel = 'textarea[name="comment"], textarea#comment-0'
            if await page.query_selector(comment_sel):
                # ensure minimal length (they requested 60 minlength)
                comment = COMMENT_TEMPLATE + "\nСрок выполнения: 1 день\n"
                # cost default
                amount_val = 1111
                # Try to detect numeric budget on page: element like span.text-green.bold.pull-right.price ... or price in USD
                budget_match = await page.eval_on_selector_all("span", "els => els.map(e=>e.innerText)")
                # parse for "USD" or "UAH" near numbers
                detected_amount = None
                if budget_match:
                    for st in budget_match:
                        if st and ("USD" in st or "UAH" in st or "$" in st):
                            m = re.search(r"([\d\s,.]+)", st.replace('\xa0',' '))
                            if m:
                                num = m.group(1).replace(" ", "").replace(",", "").replace(".", "")
                                try:
                                    detected_amount = int(num)
                                    break
                                except:
                                    pass
                if detected_amount:
                    amount_val = detected_amount
                # fill comment
                await page.fill(comment_sel, comment)
                # fill days
                days_sel = 'input[name="days_to_deliver"], input#days_to_deliver-0'
                if await page.query_selector(days_sel):
                    await page.fill(days_sel, "1")
                # fill amount
                amount_sel = 'input[name="amount"], input#amount-0'
                if await page.query_selector(amount_sel):
                    await page.fill(amount_sel, str(amount_val))
                await asyncio.sleep(0.4)
                # submit
                submit_sel = 'button#add-0, button[name="add"], button[type="submit"].ladda-button'
                if await page.query_selector(submit_sel):
                    # final submit
                    logger.info("Submitting bid...")
                    await page.click(submit_sel)
                    await asyncio.sleep(1.5)
                    await send_alert(f"Отклик отправлен на {link}. Цена: {amount_val}, Срок: 1 день")
                else:
                    logger.warning("Не найден submit button для добавления ставки.")
                    await send_alert(f"Не удалось найти кнопку отправки ставки на {link}")
            else:
                logger.warning("Форма комментария не найдена.")
                await send_alert(f"Форма для ставки не найдена на {link}")

            # Save storage state (cookies/localStorage)
            await context.storage_state(path=storage_path)
            logger.info("Состояние браузера сохранено в %s", storage_path)

        except Exception as e:
            logger.exception("Ошибка при обработке ссылки: %s", e)
            await send_alert(f"Ошибка при обработке {link}: {e}")
        finally:
            await context.close()
            await browser.close()

# ---------------- Telegram monitoring ----------------
async def main():
    global processed
    # Telethon client
    session_name = "freelance_telethon_session"
    client = TelegramClient(session_name, API_ID, API_HASH)
    await client.start()
    logger.info("Telegram client started.")

    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        text = event.raw_text or ""
        lower = text.lower()
        # check keywords
        if any(k.lower() in lower for k in KEYWORDS):
            # extract freelancehunt links
            links = FH_LINK_RE.findall(text)
            if not links:
                logger.info("Ключи найдены, но ссылок freelancehunt нет.")
                return
            for link in links:
                # normalize link trimming punctuation
                link = link.rstrip('.,)')
                if link in processed:
                    logger.info("Ссылка уже обработана: %s", link)
                    continue
                # mark processed early to avoid duplicates
                processed.add(link)
                save_processed()
                # spawn background task to process link
                asyncio.create_task(process_fh_link(link))
                logger.info("Создана задача для %s", link)
                await send_alert(f"Найдена ссылка с ключевыми словами: {link}")

    # Run client until cancelled
    logger.info("Запуск мониторинга входящих сообщений...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Остановлено пользователем.")
