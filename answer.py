import time, re, pickle
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from twocaptcha import TwoCaptcha

LOGIN_URL = "https://freelancehunt.com/ua/profile/login"
LOGIN_DATA = {"login": "Vlari", "password": "Gvadiko_2004"}
COOKIES_FILE = "fh_cookies.pkl"
CAPTCHA_API_KEY = "898059857fb8c709ca5c9613d44ffae4"

solver = TwoCaptcha(CAPTCHA_API_KEY)

def wait_for_body(driver, timeout=15):
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(0.3)
    except TimeoutException:
        print("[ЛОГ] Таймаут загрузки body")

def load_cookies(driver):
    try:
        with open(COOKIES_FILE, "rb") as f:
            for c in pickle.load(f):
                try: driver.add_cookie(c)
                except: pass
        print("[ЛОГ] Куки загружены")
    except FileNotFoundError:
        print("[ЛОГ] Файл куки не найден")

def save_cookies(driver):
    try:
        with open(COOKIES_FILE, "wb") as f:
            pickle.dump(driver.get_cookies(), f)
        print("[ЛОГ] Куки сохранены")
    except Exception as e:
        print(f"[ЛОГ] Ошибка сохранения куки: {e}")

def is_logged_in(driver):
    try:
        driver.find_element(By.CSS_SELECTOR, "a[href='/profile']")
        return True
    except:
        return False

def solve_recaptcha(driver):
    try:
        # ищем все iframe
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        sitekey = None
        for f in iframes:
            src = f.get_attribute("src") or ""
            if "recaptcha" in src:
                m = re.search(r"sitekey=([A-Za-z0-9_-]+)", src)
                if m: sitekey = m.group(1)
                break
        if not sitekey:
            # fallback: ищем элемент с data-sitekey
            try:
                sitekey = driver.find_element(By.CSS_SELECTOR, "[data-sitekey]").get_attribute("data-sitekey")
            except:
                pass

        if not sitekey:
            print("[ЛОГ] Sitekey рекапчи не найден")
            return False

        print(f"[ЛОГ] Sitekey найден: {sitekey}, отправляю на 2Captcha...")
        res = solver.recaptcha(sitekey=sitekey, url=driver.current_url)
        token = res.get("code") if isinstance(res, dict) else res

        # вставляем токен в скрытое поле
        driver.execute_script("""
        (function(token){
            var el = document.getElementById('g-recaptcha-response');
            if(!el){
                el = document.createElement('textarea');
                el.id='g-recaptcha-response';
                el.style.display='none';
                document.body.appendChild(el);
            }
            el.innerHTML=token;
        })(arguments[0]);
        """, token)
        print("[ЛОГ] Капча решена и токен вставлен")
        return True
    except Exception as e:
        print(f"[ЛОГ] Ошибка решения капчи: {e}")
        return False

def login(driver):
    driver.get(LOGIN_URL)
    wait_for_body(driver)
    load_cookies(driver)

    if is_logged_in(driver):
        print("[ЛОГ] Уже авторизован")
        return True

    try:
        # ждем поля логина и пароля
        login_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "login")))
        passwd_field = driver.find_element(By.NAME, "password")
        submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

        # вводим данные как человек
        for ch in LOGIN_DATA["login"]: login_field.send_keys(ch); time.sleep(0.08)
        for ch in LOGIN_DATA["password"]: passwd_field.send_keys(ch); time.sleep(0.08)

        # решаем капчу, если есть
        solved = solve_recaptcha(driver)
        if not solved:
            print("[ЛОГ] Капча не найдена или не решена, продолжим без нее")

        # нажимаем submit
        driver.execute_script("arguments[0].click();", submit_btn)
        wait_for_body(driver, timeout=15)
        time.sleep(2)

        if is_logged_in(driver):
            save_cookies(driver)
            print("[ЛОГ] Авторизация успешна")
            return True
        else:
            print("[ЛОГ] Авторизация неуспешна")
            return False

    except Exception as e:
        print(f"[ЛОГ] Ошибка логина: {e}")
        return False
