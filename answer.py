#!/usr/bin/env python3
# coding: utf-8

import os, time, random, pickle, asyncio, re
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from telethon import TelegramClient, events
from telegram import Bot

# ---------------- CONFIG ----------------
API_ID, API_HASH = 21882740, "c80a68894509d01a93f5acfeabfdd922"
ALERT_BOT_TOKEN, ALERT_CHAT_ID = "6566504110:AAFK9hA4jxZ0eA7KZGhVvPe8mL2HZj2tQmE", 1168962519
HEADLESS = False
LOGIN_URL = "https://freelancehunt.com/ua/profile/login"
LOGIN_DATA = {"login": "Vlari", "password": "Gvadiko_2004"}
COOKIES_FILE = "fh_cookies.pkl"
COMMENT_TEXT = "Доброго дня! Готовий виконати роботу якісно.\nПортфоліо робіт у моєму профілі.\nЗаздалегідь дякую!"
KEYWORDS = [k.lower() for k in [
    "#html_и_css_верстка","#веб_программирование","#cms",
    "#интернет_магазины_и_электронная_коммерция","#создание_сайта_под_ключ","#дизайн_сайтов"
]]
url_regex = re.compile(r"https?://[^\s)]+", re.IGNORECASE)

# ---------------- INIT ----------------
alert_bot = Bot(token=ALERT_BOT_TOKEN)
tg_client = TelegramClient("session", API_ID, API_HASH)

# ---------------- LOG ----------------
def log(msg):
    print(f"[ЛОГ] {msg}")

# ---------------- SELENIUM ----------------
def tmp_profile():
    tmp = f"/tmp/chrome-{int(time.time())}-{random.randint(0,9999)}"
    Path(tmp).mkdir(parents=True, exist_ok=True)
    return tmp

def create_driver():
    opts = Options()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1280,900")
    if HEADLESS: opts.add_argument("--headless=new")
    opts.add_argument(f"--user-data-dir={tmp_profile()}")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    drv = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    drv.set_page_load_timeout(60)
    log(f"Chrome готов, HEADLESS={HEADLESS}")
    return drv

driver = create_driver()

def wait_body(timeout=20):
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.TAG_NAME,"body")))
        time.sleep(0.3)
    except TimeoutException:
        log("Таймаут загрузки страницы")

def human_type(el, txt, delay=(0.03,0.1)):
    for ch in txt:
        el.send_keys(ch)
        time.sleep(random.uniform(*delay))

def human_scroll():
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight*0.3);")
        time.sleep(random.uniform(0.2,0.4))
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight*0.6);")
    except: pass

# ---------------- COOKIES ----------------
def save_cookies():
    try:
        with open(COOKIES_FILE,"wb") as f:
            pickle.dump(driver.get_cookies(),f)
        log("Куки сохранены")
    except: pass

def load_cookies():
    if not os.path.exists(COOKIES_FILE): return False
    try:
        with open(COOKIES_FILE,"rb") as f:
            for c in pickle.load(f):
                try: driver.add_cookie(c)
                except: pass
        return True
    except: return False

# ---------------- LOGIN ----------------
def logged_in():
    try:
        driver.find_element(By.CSS_SELECTOR,"a[href='/profile']")
        return True
    except: return False

def login():
    driver.get(LOGIN_URL)
    wait_body()
    load_cookies()
    if logged_in(): return True
    try:
        driver.find_element(By.NAME,"login").send_keys(LOGIN_DATA["login"])
        driver.find_element(By.NAME,"password").send_keys(LOGIN_DATA["password"])
        driver.find_element(By.CSS_SELECTOR,"button[type='submit']").click()
        time.sleep(2)
        wait_body()
        save_cookies()
        log("Авторизация успешна")
        return True
    except Exception as e:
        log(f"Ошибка авторизации: {e}")
        return False

# ---------------- ALERT ----------------
async def send_alert(msg):
    try:
        await alert_bot.send_message(chat_id=ALERT_CHAT_ID,text=msg)
        log(f"TG ALERT: {msg}")
    except: pass

# ---------------- BID ----------------
async def make_bid(url):
    try:
        driver.get(url)
        wait_body()
        load_cookies()
        if not logged_in(): login(); driver.get(url); wait_body()
        human_scroll()

        # Проверка уже сделанной ставки
        try:
            alert_el = driver.find_element(By.CSS_SELECTOR,"div.alert.alert-info")
            log(f"Ставка уже сделана: {alert_el.text}")
            await send_alert(f"⚠️ Уже сделано: {url}\n{alert_el.text}")
            return
        except: pass

        # Заполняем форму
        try:
            driver.find_element(By.ID,"amount-0").clear()
            driver.find_element(By.ID,"amount-0").send_keys("12000")
            driver.find_element(By.ID,"days_to_deliver-0").clear()
            driver.find_element(By.ID,"days_to_deliver-0").send_keys("3")
            driver.find_element(By.ID,"comment-0").clear()
            human_type(driver.find_element(By.ID,"comment-0"), COMMENT_TEXT)
            time.sleep(0.5)
        except Exception as e:
            log(f"Ошибка заполнения формы: {e}")
            await send_alert(f"❌ Ошибка заполнения формы: {url}")
            return

        # JS клик на кнопку "Добавить"
        try:
            driver.execute_script("document.getElementById('add-0').click();")
            log("Кнопка 'Добавить' нажата")
            await send_alert(f"✅ Ставка отправлена: {url}")
            save_cookies()
        except Exception as e:
            log(f"Не удалось кликнуть 'Добавить': {e}")
            await send_alert(f"❌ Не удалось кликнуть 'Добавить': {url}")

    except Exception as e:
        log(f"Ошибка make_bid: {e}")
        await send_alert(f"❌ Ошибка ставки: {url}\n{e}")

# ---------------- TELEGRAM ----------------
def extract_links(msg):
    text = msg.message if hasattr(msg, "message") else str(msg)
    links = re.findall(url_regex,text)
    try:
        for row in getattr(msg,"buttons",[]) or []:
            for btn in row:
                url = getattr(btn,"url",None)
                if url and "freelancehunt.com" in url: links.append(url)
    except: pass
    return list(set(links))

@tg_client.on(events.NewMessage)
async def on_msg(event):
    txt = (event.message.text or "").lower()
    links = extract_links(event.message)
    if links and any(k in txt for k in KEYWORDS):
        for link in links:
            asyncio.create_task(make_bid(link))

# ---------------- MAIN ----------------
async def main():
    if os.path.exists(COOKIES_FILE):
        driver.get("https://freelancehunt.com")
        wait_body()
        load_cookies()
        driver.refresh()
        wait_body()
    await tg_client.start()
    log("Telegram клиент запущен")
    await tg_client.run_until_disconnected()

if __name__=="__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("Завершение работы")
        driver.quit()
