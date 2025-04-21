import os
import time
import datetime
import pytz
import pickle
import traceback
from email.message import EmailMessage
import smtplib
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

LOOKER_PAGES = [
    "https://lookerstudio.google.com/reporting/bf8f0517-e040-42c3-a6a9-e9d0b62885df/page/p_fsj6ky8zqd",
    "https://lookerstudio.google.com/reporting/bf8f0517-e040-42c3-a6a9-e9d0b62885df/page/p_c7fyt0w5qd",
]

RECIPIENTS = "niha.singhania@flipkart.com",
  

COOKIE_FILE = "cookies.pkl"
TIMEZONE = pytz.timezone("Asia/Kolkata")

def get_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=opts)

def load_cookies(driver, url):
    if not os.path.exists(COOKIE_FILE):
        return
    with open(COOKIE_FILE, "rb") as f:
        cookies = pickle.load(f)
    driver.get(url)
    time.sleep(5)
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.refresh()

def save_cookies(driver):
    with open(COOKIE_FILE, "wb") as f:
        pickle.dump(driver.get_cookies(), f)

def capture_screens():
    driver = get_driver()
    paths = []
    for i, url in enumerate(LOOKER_PAGES, 1):
        print(f"⏳ Loading: {url}")
        load_cookies(driver, url)
        time.sleep(25)
        filename = f"screenshot_{i}.png"
        driver.save_screenshot(filename)
        print(f"✅ Saved: {filename}")
        paths.append(filename)
    save_cookies(driver)
    driver.quit()
    return paths

def send_mail(paths):
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_pass = os.getenv("SMTP_PASSWORD")

    ist_now = datetime.datetime.utcnow().replace(
        tzinfo=pytz.utc).astimezone(TIMEZONE)
    subject = f"📊 OB Summary Report – {ist_now:%Y-%m-%d %H:%M IST}"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = ", ".join(RECIPIENTS)
    msg.set_content("Hi team,\n\nPlease find attached the latest PAN India summary screenshots.\n\n– Onboarding Bot")

    for path in paths:
        with open(path, "rb") as f:
            msg.add_attachment(f.read(), maintype="image", subtype="png", filename=path)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Email failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    screenshots = capture_screens()
    send_mail(screenshots)
