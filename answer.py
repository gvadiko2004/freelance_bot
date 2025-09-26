# answer_playwright.py
import asyncio
import re
import json
import logging
import random
import time
from pathlib import Path
import os
from dotenv import load_dotenv
import aiohttp
from telethon import TelegramClient, events
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

FH_LINK_RE = re.compile(r"https://freelancehunt\.com[^\s)]+", re.IGNORECASE)

COMMENT_TEXT = (
    "Доброго дня! Готовий виконати роботу якісно.\n"
    "Портфоліо робіт у моєму профілі.\n"
    "Заздалегідь дякую!"
)

# Load processed links
if PROCESSED_FILE.exists():
    processed = set(json.loads(PROCESSED_FILE.read_text()))
else:
    processed = set()

# ---------------- Utilities ----------------
async def send_alert(msg: str):
    url = f"https://api.telegram.org/bot{ALERT_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": ALERT_CHAT_ID, "text": msg}
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
    create_url = "http://2captcha.com/in.php"
    get_url = "http://2captcha.com/res.php"
    params = {"key": CAPTCHA_API_KEY, "method": "userrecaptcha", "googlekey": site_key, "pageurl": page_url, "json": 1}
    async with session.post(create_url, data=params) as resp:
        j = await resp.json()
    if j.get("status") != 1:
        raise RuntimeError("2captcha create error: " + str(j))
    request_id = j["request"]
    logger.info("reCAPTCHA отправлена на решение, ожидаем результат...")
    for _ in range(30):
        await asyncio.sleep(5)
        async with session.get(get_url, params={"key": CAPTCHA_API_KEY, "action":"get", "id":request_id, "json":1}) as r:
            res = await r.json()
        if res.get("status") == 1:
            logger.info("reCAPTCHA решена!")
            return res["request"]
    raise RuntimeError("Captcha solve timeout")

# ---------------- Core ----------------
async def human_scroll_and_move(page):
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight*0.3);")
    await asyncio.sleep(random.uniform(0.15,0.4))
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight*0.6);")
    await page.mouse.move(random.randint(1,50), random.randint(1,50))

async def attempt_bid_on_url(page, url: str):
    logger.info(f"Открываю: {url}")
    await page.goto(url, wait_until="networkidle")
    await asyncio.sleep(1)
    
    # reCAPTCHA
    frames = page.frames
    for f in frames:
        if "https://www.google.com/recaptcha/api2/anchor" in f.url:
            site_key = await f.get_attribute("#recaptcha-anchor", "data-sitekey")
            async with aiohttp.ClientSession() as session:
                token = await solve_captcha_2captcha(session, site_key, page.url)
            await page.evaluate(f'document.getElementById("g-recaptcha-response").innerHTML="{token}";')
            logger.info("reCAPTCHA токен введен")

    # Click "Сделать ставку"
    clicked=False
    try:
        btn = await page.wait_for_selector("#add-bid, a.btn-primary", timeout=5000)
        await btn.click()
        clicked=True
    except:
        for c in await page.query_selector_all("a.btn, button.btn"):
            txt = (await c.inner_text()).lower()
            if "ставк" in txt or "сделать" in txt:
                await c.click()
                clicked=True
                break
    if not clicked:
        logger.warning("Кнопка 'Сделать ставку' не найдена")
        return False

    await human_scroll_and_move(page)

    try:
        await page.fill("#amount-0, input[name='amount']", "1111")
    except: pass
    try:
        await page.fill("#days_to_deliver-0, input[name='days_to_deliver']", "3")
    except: pass
    try:
        await page.fill("#comment-0, textarea[name='comment']", COMMENT_TEXT)
    except: pass

    submitted=False
    try:
        submit_btn = await page.query_selector("#btn-submit-0, button.btn-primary")
        await submit_btn.click()
        submitted=True
    except:
        pass

    if submitted:
        logger.info(f"Ставка отправлена: {url}")
        await send_alert(f"✅ Ставка отправлена: {url}")
        return True
    else:
        logger.warning("Не удалось нажать кнопку 'Добавить'")
        return False

def extract_links(message):
    found=[]
    txt = getattr(message, "text", "") or getattr(message, "message", "")
    if txt: found+=FH_LINK_RE.findall(txt)
    buttons = getattr(message, "buttons", None)
    if buttons:
        for row in buttons:
            for btn in row:
                url=getattr(btn,"url",None)
                if url: found.append(url)
                else: btn_txt = getattr(btn,"text","") or ""; found+=FH_LINK_RE.findall(btn_txt)
    uniq=[]
    for u in found:
        if u not in uniq: uniq.append(u)
    return uniq

# ---------------- Telegram monitoring ----------------
async def main():
    global processed
    tg_client = TelegramClient("freelance_telethon_session", API_ID, API_HASH)
    await tg_client.start()
    logger.info("Telegram client started")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        @tg_client.on(events.NewMessage(incoming=True))
        async def handler(event):
            try:
                text = (event.message.text or "").lower()
                if any(k in text for k in KEYWORDS):
                    links = extract_links(event.message)
                    if not links:
                        logger.info("Ключевое слово найдено, но ссылки не обнаружены.")
                        await send_alert("⚠️ Ключевое слово найдено, но ссылки не обнаружены.")
                        return
                    for url in links:
                        if url in processed: continue
                        processed.add(url)
                        save_processed()
                        await attempt_bid_on_url(page, url)
            except Exception as e:
                logger.exception(f"handler_newmsg error: {e}")

        logger.info("Запуск мониторинга сообщений...")
        await tg_client.run_until_disconnected()
        await context.close()
        await browser.close()

if __name__=="__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Завершение работы")
