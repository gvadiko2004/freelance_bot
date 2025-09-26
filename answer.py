#!/usr/bin/env python3
# coding: utf-8

import os, time, random, pickle
from pathlib import Path
from twocaptcha import TwoCaptcha
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# ---------------- CONFIG ----------------
API_ID = int(os.getenv("API_ID", "21882740"))
API_HASH = os.getenv("API_HASH", "c80a68894509d01a93f5acfeabfdd922")
ALERT_BOT_TOKEN = os.getenv("ALERT_BOT_TOKEN", "6566504110:AAFK9hA4jxZ0eA7KZGhVvPe8mL2HZj2tQmE")
ALERT_CHAT_ID = int(os.getenv("ALERT_CHAT_ID", "1168962519"))
FH_LOGIN = os.getenv("FH_LOGIN", "Vlari")
FH_PASSWORD = os.getenv("FH_PASSWORD", "Gvadiko_2004")
CAPTCHA_API_KEY = os.getenv("CAPTCHA_API_KEY", "898059857fb8c709ca5c9613d44ffae4")
HEADLESS = False
LOGIN_URL = "https://freelancehunt.com/ua/profile/login"
COOKIES_FILE = "fh_cookies.pkl"

COMMENT_TEXT = ("Доброго дня! Готовий виконати роботу якісно.\n"
                "Портфоліо робіт у моєму профілі.\n"
                "Заздалегідь дякую!")

# ---------------- UTILS ----------------
def log(msg):
    print(f"[ЛОГ] {msg}")

def make_tmp_profile():
    tmp = os.path.join("/tmp", f"chrome-temp-{int(time.time())}-{random.randint(0,9999)}")
    Path(tmp).mkdir(parents=True, exist_ok=True)
    return tmp

def create_driver():
    opts = Options()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1366,900")
    if HEADLESS: opts.add_argument("--headless=new")
    opts.add_argument(f"--user-data-dir={make_tmp_profile()}")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    svc = Service(ChromeDriverManager().install())
    d = webdriver.Chrome(service=svc, options=opts)
    d.set_page_load_timeout(60)
    log(f"Chrome готов, HEADLESS={HEADLESS}")
    return d

def wait_body(driver, timeout=20):
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(0.3)
    except TimeoutException:
        log("Таймаут загрузки страницы (wait_body)")

def human_type(el, text, delay=(0.04,0.12)):
    for ch in text:
        el.send_keys(ch)
        time.sleep(random.uniform(*delay))

# ---------------- CAPTCHA ----------------
solver = TwoCaptcha(CAPTCHA_API_KEY)

def solve_recaptcha(driver):
    try:
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for f in iframes:
            src = f.get_attribute("src") or ""
            if "recaptcha" in src:
                sitekey = None
                import re
                m = re.search(r"sitekey=([A-Za-z0-9_-]+)", src)
                if m: sitekey = m.group(1)
                if not sitekey:
                    try:
                        sitekey = driver.find_element(By.CSS_SELECTOR, "[data-sitekey]").get_attribute("data-sitekey")
                    except:
                        continue
                log(f"reCAPTCHA sitekey найден: {sitekey}")
                res = solver.recaptcha(sitekey=sitekey, url=driver.current_url)
                token = res.get("code") if isinstance(res, dict) else res
                driver.execute_script("""
                (function(token){
                    var el=document.getElementById('g-recaptcha-response');
                    if(!el){el=document.createElement('textarea');el.id='g-recaptcha-response';el.style.display='none';document.body.appendChild(el);}
                    el.innerHTML=token;
                })(arguments[0]);
                """, token)
                log("reCAPTCHA решена")
                return True
    except Exception as e:
        log(f"Ошибка решения reCAPTCHA: {e}")
    return False

# ---------------- LOGIN ----------------
def load_cookies(driver):
    if os.path.exists(COOKIES_FILE):
        try:
            for c in pickle.load(open(COOKIES_FILE,"rb")):
                try: driver.add_cookie(c)
                except: pass
            log("Куки загружены")
        except: pass

def save_cookies(driver):
    try:
        with open(COOKIES_FILE, "wb") as f: pickle.dump(driver.get_cookies(), f)
        log("Куки сохранены")
    except: pass

def is_logged_in(driver):
    try:
        driver.find_element(By.CSS_SELECTOR, "a[href='/profile']")
        return True
    except: return False

def login(driver):
    driver.get(LOGIN_URL)
    wait_body(driver)
    load_cookies(driver)
    if is_logged_in(driver):
        log("Уже авторизован")
        return True
    try:
        login_field = WebDriverWait(driver, 6).until(EC.presence_of_element_located((By.NAME, "login")))
        passwd_field = driver.find_element(By.NAME, "password")
        human_type(login_field, FH_LOGIN)
        human_type(passwd_field, FH_PASSWORD)
        # Попытка решить капчу перед отправкой
        solve_recaptcha(driver)
        submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        driver.execute_script("arguments[0].click();", submit_btn)
        time.sleep(3)
        wait_body(driver)
        # После submit снова проверяем капчу
        solve_recaptcha(driver)
        if is_logged_in(driver):
            save_cookies(driver)
            log("Авторизация успешна")
            return True
        log("Авторизация неуспешна")
        return False
    except Exception as e:
        log(f"Ошибка при логине: {e}")
        return False

# ---------------- MAIN ----------------
if __name__ == "__main__":
    driver = create_driver()
    try:
        if not login(driver):
            log("❌ Не удалось авторизоваться — выходим")
        else:
            log("✅ Авторизация прошла успешно, можно запускать цикл мониторинга")
            # здесь можно вызывать ваш цикл проверки Telegram и обработки ссылок
    finally:
        driver.quit()
