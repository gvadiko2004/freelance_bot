#!/usr/bin/env python3
# coding: utf-8

import os, time, random, pickle, asyncio, re
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
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
DEFAULT_DAYS = "3"
DEFAULT_AMOUNT = "1111"

KEYWORDS = [k.lower() for k in [
    "#html_и_css_верстка","#веб_программирование","#cms",
    "#интернет_магазины_и_электронная_коммерция","#создание_сайта_под_ключ","#дизайн_сайтов"
]]

# ---------------- INIT ----------------
alert_bot = Bot(token=ALERT_BOT_TOKEN)
tg_client = TelegramClient("session", API_ID, API_HASH)
driver = None

# ---------------- UTILS ----------------
def log(msg):
    print(f"[ЛОГ] {msg}")

def tmp_profile():
    tmp = f"/tmp/chrome-{int(time.time())}-{random.randint(0,9999)}"
    Path(tmp).mkdir(parents=True, exist_ok=True)
    return tmp

def create_driver():
    opts = Options()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1366,900")
    if HEADLESS: opts.add_argument("--headless=new")
    opts.add_argument(f"--user-data-dir={tmp_profile()}")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    drv = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    drv.set_page_load_timeout(60)
    log(f"Chrome готов, HEADLESS={HEADLESS}")
    return drv

def wait_body(timeout=20):
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.TAG_NAME,"body")))
        time.sleep(0.3)
    except TimeoutException:
        log("Таймаут загрузки страницы")

def human_type(el, text, delay=(0.03,0.08)):
    for ch in text:
        el.send_keys(ch)
        time.sleep(random.uniform(*delay))

def human_scroll():
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight*0.3);")
        time.sleep(random.uniform(0.2,0.4))
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight*0.6);")
        ActionChains(driver).move_by_offset(random.randint(1,50), random.randint(1,50)).perform()
    except: pass

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
        log("Куки загружены")
        return True
    except: return False

def logged_in():
    try:
        driver.find_element(By.CSS_SELECTOR,"a[href='/profile']")
        return True
    except: return False

# ---------------- LOGIN ----------------
def login():
    driver.get(LOGIN_URL)
    wait_body()
    load_cookies()
    if logged_in():
        log("Уже авторизован")
        return True

    try:
        login_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "login-0"))
        )
        password_input = driver.find_element(By.ID, "password-0")
        submit_btn = driver.find_element(By.ID, "save-0")

        login_input.clear()
        login_input.send_keys(LOGIN_DATA["login"])
        password_input.clear()
        password_input.send_keys(LOGIN_DATA["password"])
        submit_btn.click()

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,"a[href='/profile']"))
        )
        log("Авторизация успешна")
        save_cookies()
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
        log(f"Открываю: {url}")
        driver.get(url)
        wait_body()
        load_cookies()
        if not logged_in(): login(); driver.get(url); wait_body()

        # проверка "ставка уже сделана"
        try:
            alert_el = driver.find_element(By.CSS_SELECTOR,"div.alert.alert-info")
            text = alert_el.text
            log(f"Ставка уже сделана: {text}")
            await send_alert(f"⚠️ Уже сделано: {url}\n{text}")
            return
        except: pass

        # клик "Сделать ставку"
        try:
            add_bid_btn = WebDriverWait(driver,5).until(
                EC.element_to_be_clickable((By.ID,"add-bid"))
            )
            driver.execute_script("arguments[0].click();", add_bid_btn)
            log("Кликнули 'Сделать ставку'")
            time.sleep(0.5)
            human_scroll()
        except:
            log("Кнопка 'Сделать ставку' не найдена")
            return

        # заполнение полей
        try:
            amount_input = WebDriverWait(driver,5).until(EC.presence_of_element_located((By.ID,"amount-0")))
            days_input = driver.find_element(By.ID,"days_to_deliver-0")
            comment_input = driver.find_element(By.ID,"comment-0")

            human_type(amount_input, DEFAULT_AMOUNT)
            human_type(days_input, DEFAULT_DAYS)
            human_type(comment_input, COMMENT_TEXT)
        except Exception as e:
            log(f"Ошибка заполнения полей: {e}")
            return

        # клик "Добавить"
        try:
            add_btn = driver.find_element(By.ID,"add-0")
            driver.execute_script("arguments[0].click();", add_btn)
            log("Ставка отправлена!")
            await send_alert(f"✅ Ставка отправлена: {url}")
            save_cookies()
        except Exception as e:
            log(f"Ошибка клика 'Добавить': {e}")

    except Exception as e:
        log(f"Ошибка make_bid: {e}")
        await send_alert(f"❌ Ошибка ставки: {e}\n{url}")

# ---------------- TELEGRAM ----------------
def extract_links(msg):
    text = msg.message if hasattr(msg,"message") else str(msg)
    links = re.findall(r"https?://[^\s)]+", text)
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
    global driver
    driver = create_driver()
    load_cookies()
    await tg_client.start()
    log("Telegram клиент запущен")
    await tg_client.run_until_disconnected()

if __name__=="__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("Завершение работы")
        driver.quit()
