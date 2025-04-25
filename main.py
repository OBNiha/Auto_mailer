import os
import time
import datetime
import pytz
import traceback
from email.message import EmailMessage
import smtplib
import undetected_chromedriver as uc

# Looker Studio public embed URLs
LOOKER_PAGES = [
    "https://lookerstudio.google.com/embed/reporting/bf8f0517-e040-42c3-a6a9-e9d0b62885df/page/p_fsj6ky8zqd",
    "https://lookerstudio.google.com/embed/reporting/bf8f0517-e040-42c3-a6a9-e9d0b62885df/page/p_mv9sot1urd",
]

# Recipients for the report email
RECIPIENTS = ["niha.singhania@flipkart.com"]

# IST timezone
TIMEZONE = pytz.timezone("Asia/Kolkata")

def get_driver():
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    return uc.Chrome(options=options)

def capture_screens():
    driver = get_driver()
    paths = []
    for i, url in enumerate(LOOKER_PAGES, 1):
        print(f"Loading Looker Studio URL: {url}")
        driver.get(url)
        time.sleep(60)  # wait for full load
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)
        filename = f"screenshot_{i}.png"
        driver.save_screenshot(filename)
        print(f"Saved screenshot: {filename}")
        paths.append(filename)
    driver.quit()
    return paths

def send_mail(paths):
    smtp_username = "niha.singhania@flipkart.com"
    smtp_password = "vadk lmsp zfpw zxab"

    if not smtp_user or not smtp_pass:
        raise Exception("EMAIL_ID or EMAIL_PASS environment variables not set.")

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

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        print("✅ Email sent successfully!")

if __name__ == "__main__":
    try:
        screenshots = capture_screens()
        send_mail(screenshots)
    except Exception as e:
        print(f"❌ Script failed: {e}")
        traceback.print_exc()
