#!/usr/bin/env python3
# coding: utf-8
"""
Bot for Freelancehunt — robust, runs on VPS, shows Chrome in VNC.
Does NOT bypass reCAPTCHA. If CAPTCHA detected — takes screenshot and alerts.
"""

import os
import time
import random
import pickle
import re
import threading
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from telethon import TelegramClient, events
from telegram import Bot  # for simple alert with file (optional)

# ---------------- CONFIG ----------------
API_ID = 21882740
API_HASH = "c80a68894509d01a93f5acfeabfdd922"

ALERT_BOT_TOKEN = ""      # <-- Впиши сюда токен бота Telegram (опционально, для отправки фото/сообщений)
ALERT_CHAT_ID   = 0       # <-- Впиши chat_id (опционально)

HEADLESS = False          # must be False to show Chrome in VNC
PROFILE_PATH = "/root/chrome_profile"   # профиль Chrome на VPS (user-data-dir)
COOKIES_FILE = "fh_cookies.pkl"

# Bot behaviour
COMMENT_TEXT = (
    "Доброго дня! Готовий виконати роботу якісно.\n"
    "Портфоліо робіт у моєму профілі.\n"
    "Заздалегідь дякую!"
)
DEFAULT_DAYS = "3"
DEFAULT_AMOUNT = "1111"

KEYWORDS = [k.lower() for k in [
    "#html_и_css_верстка","#веб_программирование","#cms",
    "#интернет_магазины_и_электронная_коммерция","#создание_сайта_под_ключ","#дизайн_сайтов"
]]

# ---------------- INIT ----------------
alert_bot = Bot(token=ALERT_BOT_TOKEN) if ALERT_BOT_TOKEN else None
tg_client = TelegramClient("session", API_ID, API_HASH)

# Ensure profile path exists
Path(PROFILE_PATH).mkdir(parents=True, exist_ok=True)

# ---------------- HELPERS ----------------
def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

def random_sleep(a=0.2, b=0.6):
    time.sleep(random.uniform(a,b))

def save_cookies(driver):
    try:
        with open(COOKIES_FILE, "wb") as f:
            pickle.dump(driver.get_cookies(), f)
        log("Cookies saved")
    except Exception as e:
        log(f"Failed to save cookies: {e}")

def load_cookies(driver, url):
    if not os.path.exists(COOKIES_FILE):
        return False
    try:
        driver.get(url)
        with open(COOKIES_FILE, "rb") as f:
            cookies = pickle.load(f)
        for c in cookies:
            try:
                # ensure domain/path keys present
                driver.add_cookie(c)
            except Exception:
                pass
        driver.refresh()
        log("Cookies loaded")
        return True
    except Exception as e:
        log(f"Failed to load cookies: {e}")
        return False

def send_alert_text(text):
    log(f"ALERT: {text}")
    if alert_bot and ALERT_CHAT_ID:
        try:
            alert_bot.send_message(chat_id=ALERT_CHAT_ID, text=text)
        except Exception as e:
            log(f"Failed to send TG alert: {e}")

def send_alert_file(path, caption=None):
    log(f"ALERT file: {path} ({caption})")
    if alert_bot and ALERT_CHAT_ID:
        try:
            with open(path, "rb") as f:
                alert_bot.send_photo(chat_id=ALERT_CHAT_ID, photo=f, caption=caption or "")
        except Exception as e:
            log(f"Failed to send TG photo: {e}")

# ---------------- SELENIUM ----------------
def create_driver():
    opts = Options()
    # visual mode for VNC: HEADLESS must be False
    if HEADLESS:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    # set profile path so cookies, logins persist
    opts.add_argument(f"--user-data-dir={PROFILE_PATH}")
    opts.add_argument("--window-size=1366,768")
    # evade some automation flags
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)

    # for root processes (on many VPS) --no-sandbox is required
    drv = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    drv.set_page_load_timeout(60)
    log("Chrome driver created")
    return drv

def detect_captcha(driver):
    # very conservative checks: if any recaptcha elements present or iframe google recaptcha
    try:
        # common recaptcha markers
        if driver.find_elements(By.CSS_SELECTOR, "div.g-recaptcha") or \
           driver.find_elements(By.CSS_SELECTOR, "div.recaptcha-checkbox") or \
           driver.find_elements(By.CSS_SELECTOR, "iframe[src*='recaptcha']") or \
           driver.find_elements(By.XPATH, "//*[contains(@class,'recaptcha')]"):
            return True
    except Exception:
        pass
    return False

def take_screenshot(driver, prefix="captcha"):
    fname = f"{prefix}_{int(time.time())}.png"
    try:
        driver.save_screenshot(fname)
        log(f"Saved screenshot: {fname}")
        if alert_bot and ALERT_CHAT_ID:
            send_alert_file(fname, caption="Captcha / problem screenshot")
    except Exception as e:
        log(f"Failed to save/send screenshot: {e}")
    return fname

# ---------------- BUSINESS LOGIC ----------------
def make_bid(url):
    log(f"Opening {url}")
    try:
        driver = create_driver()
    except WebDriverException as e:
        log(f"Cannot start Chrome driver: {e}")
        return

    wait = WebDriverWait(driver, 25)
    try:
        driver.get(url)
    except Exception as e:
        log(f"Page open error: {e}")
        driver.quit()
        return

    # wait for ready state
    try:
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
    except TimeoutException:
        log("Page load timed out but continuing")

    # try loading cookies (if exist)
    load_cookies(driver, url)

    # short human-like scroll
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight*0.3);")
        random_sleep(0.3, 0.7)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight*0.6);")
    except Exception:
        pass

    # detect captcha
    if detect_captcha(driver):
        log("Detected CAPTCHA on page")
        take_screenshot(driver, "captcha_detect")
        send_alert_text(f"⚠️ CAPTCHA detected on {url} — manual solve required via VNC")
        # leave browser open so you can solve manually via VNC
        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            pass
        driver.quit()
        return

    # check if already bid (site-specific)
    try:
        alert_el = driver.find_element(By.CSS_SELECTOR, "div.alert.alert-info")
        if alert_el and "ставк" in alert_el.text.lower():
            log("Already bid or info alert present; aborting")
            send_alert_text(f"⚠️ Already bid or blocked: {url}\n{alert_el.text}")
            driver.quit()
            return
    except Exception:
        pass

    # find and click "Make bid" button
    try:
        add_bid_btn = wait.until(EC.element_to_be_clickable((By.ID, "add-bid")))
        driver.execute_script("arguments[0].click();", add_bid_btn)
        log("Clicked 'Make bid'")
        random_sleep(0.5, 1.0)
    except (TimeoutException, NoSuchElementException) as e:
        log(f"'Make bid' button not found: {e}")
        take_screenshot(driver, "no_add_bid")
        send_alert_text(f"❌ 'Make bid' not found on {url}")
        driver.quit()
        return

    # fill form
    try:
        amount_input = wait.until(EC.presence_of_element_located((By.ID, "amount-0")))
        days_input   = driver.find_element(By.ID, "days_to_deliver-0")
        comment_input= driver.find_element(By.ID, "comment-0")

        # amount — try to detect suggested value
        price = DEFAULT_AMOUNT
        try:
            price_span = driver.find_element(By.CSS_SELECTOR, "span.text-green.bold.pull-right.price.with-tooltip.hidden-xs")
            price_text = re.sub(r"[^\d]", "", price_span.text)
            if price_text:
                price = price_text
        except Exception:
            pass

        # human-like typing
        for ch in price:
            amount_input.send_keys(ch)
            time.sleep(random.uniform(0.02, 0.06))
        random_sleep(0.1, 0.3)
        for ch in DEFAULT_DAYS:
            days_input.send_keys(ch)
            time.sleep(random.uniform(0.02, 0.06))
        random_sleep(0.1, 0.3)

        # set comment via JS to avoid send_keys issues
        driver.execute_script("arguments[0].value = arguments[1];", comment_input, COMMENT_TEXT)
        random_sleep(0.2, 0.6)

        # click confirm button (may be id add-0 or submit inside modal)
        try:
            confirm_btn = driver.find_element(By.ID, "add-0")
            driver.execute_script("arguments[0].click();", confirm_btn)
        except Exception:
            # fallback: submit form
            try:
                comment_input.submit()
            except Exception:
                pass

        log("Bid submitted (attempt).")
        save_cookies(driver)
        send_alert_text(f"✅ Bid attempt submitted: {url}")

        # leave browser open for manual check in VNC
        log("Leaving browser open for manual inspection. Close it from VNC when done.")
        while True:
            time.sleep(5)

    except Exception as e:
        log(f"Error filling form / submitting: {e}")
        take_screenshot(driver, "submit_error")
        send_alert_text(f"❌ Error submitting bid on {url}: {e}")
        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            pass
    finally:
        try:
            driver.quit()
        except Exception:
            pass

def process_project(url):
    t = threading.Thread(target=make_bid, args=(url,), daemon=True)
    t.start()
    return t

# ---------------- TELEGRAM ----------------
@tg_client.on(events.NewMessage)
async def on_msg(event):
    text = (event.message.text or "").lower()
    # quick filter
    if any(k in text for k in KEYWORDS):
        log(f"New message with keyword: {text[:120]}")
        links = re.findall(r"https?://[^\s)]+", event.message.text or "")
        if links:
            url = links[0]
            process_project(url)
        else:
            log("No links in message")

# ---------------- START ----------------
def main():
    log("Starting Telegram client...")
    tg_client.start()
    log("Telegram client started, waiting messages...")
    tg_client.run_until_disconnected()

if __name__ == "__main__":
    main()
