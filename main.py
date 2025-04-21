import os
import time
import datetime
import pytz
import pickle
import traceback
from email.message import EmailMessage
import smtplib
import undetected_chromedriver as uc # NEW

# List of Looker Studio URLs to capture
LOOKER_PAGES = [
    "https://lookerstudio.google.com/reporting/bf8f0517-e040-42c3-a6a9-e9d0b62885df/page/p_fsj6ky8zqd",
    "https://lookerstudio.google.com/reporting/bf8f0517-e040-42c3-a6a9-e9d0b62885df/page/p_c7fyt0w5qd",
]

# Email recipient(s)
RECIPIENTS = "niha.singhania@flipkart.com",

# File to store cookies (so login persists)
COOKIE_FILE = "cookies.pkl"

# Set timezone to IST
TIMEZONE = pytz.timezone("Asia/Kolkata")

# Setup undetected Chrome browser
def get_driver():
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    return uc.Chrome(headless=True, options=options)

# Load saved cookies to avoid login
def load_cookies(driver, url):
    if not os.path.exists(COOKIE_FILE):
        return
    with open(COOKIE_FILE, "rb") as f:
        cookies = pickle.load(f)
    driver.get(url)
    time.sleep(5)
    for cookie in cookies:
        try:
            driver.add_cookie(cookie)
        except:
            continue
    driver.refresh()

# Save cookies after login
def save_cookies(driver):
    with open(COOKIE_FILE, "wb") as f:
        pickle.dump(driver.get_cookies(), f)

# Capture screenshot after full page load
def capture_screens():
    driver = get_driver()
    paths = []
    for i, url in enumerate(LOOKER_PAGES, 1):
        print(f"⏳ Loading: {url}")
        load_cookies(driver, url)

        print("⌛ Waiting 45 seconds for dashboard to render...")
        time.sleep(45) # Wait for Looker Studio to load fully

        # Scroll to bottom to trigger JS load
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)

        filename = f"screenshot_{i}.png"
        driver.save_screenshot(filename)
        print(f"✅ Saved: {filename}")
        paths.append(filename)

    save_cookies(driver)
    driver.quit()
    return paths

# Email the screenshots
def send_mail(paths):
    smtp_user = "niha.singhania@flipkart.com"
    smtp_pass = "xckn wjbm jzol riba"

    ist_now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(TIMEZONE)
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

# Main script execution
if __name__ == "__main__":
    screenshots = capture_screens()
    send_mail(screenshots)
