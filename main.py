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

# URLs of Looker Studio dashboards to capture
LOOKER_PAGES = [
    "https://lookerstudio.google.com/reporting/bf8f0517-e040-42c3-a6a9-e9d0b62885df/page/p_fsj6ky8zqd",
    "https://lookerstudio.google.com/reporting/bf8f0517-e040-42c3-a6a9-e9d0b62885df/page/p_c7fyt0w5qd",
]

# Email recipient(s)
RECIPIENTS = "niha.singhania@flipkart.com",

# File to store browser cookies
COOKIE_FILE = "cookies.pkl"

# Set timezone to IST
TIMEZONE = pytz.timezone("Asia/Kolkata")

# Initialize headless Chrome WebDriver
def get_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=opts)

# Load cookies into browser to maintain login session
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

# Save browser cookies to file
def save_cookies(driver):
    with open(COOKIE_FILE, "wb") as f:
        pickle.dump(driver.get_cookies(), f)

# Capture screenshots of all Looker Studio pages
def capture_screens():
    driver = get_driver()
    paths = []
    for i, url in enumerate(LOOKER_PAGES, 1):
        print(f"⏳ Loading: {url}")
        load_cookies(driver, url)
        
        # Wait for Looker Studio to load completely
        print("⌛ Waiting for dashboard to render (30 seconds)...")
        time.sleep(30)  # Wait here before capturing screenshot

        filename = f"screenshot_{i}.png"
        driver.save_screenshot(filename)
        print(f"✅ Saved: {filename}")
        paths.append(filename)

    save_cookies(driver)
    driver.quit()
    return paths

# Send email with screenshots as attachments
def send_mail(paths):
    smtp_user = "niha.singhania@flipkart.com"
    smtp_pass = "vadk lmsp zfpw zxab"

    # Generate current timestamp in IST
    ist_now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(TIMEZONE)
    subject = f"📊 OB Summary Report – {ist_now:%Y-%m-%d %H:%M IST}"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = ", ".join(RECIPIENTS)
    msg.set_content("Hi team,\n\nPlease find attached the latest PAN India summary screenshots.\n\n– Onboarding Bot")

    # Attach each screenshot
    for path in paths:
        with open(path, "rb") as f:
            msg.add_attachment(f.read(), maintype="image", subtype="png", filename=path)

    # Send email via SMTP
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Email failed: {e}")
        traceback.print_exc()

# Main execution flow
if __name__ == "__main__":
    screenshots = capture_screens()
    send_mail(screenshots)
