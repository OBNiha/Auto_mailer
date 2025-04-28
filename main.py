"""Grabs public Looker-Studio dashboards (cross-origin safe) and e-mails them
hourly. Works inside GitHub Actions with headless Chrome “stable”."""

import os
import time
import traceback
import datetime as dt
from email.message import EmailMessage
from smtplib import SMTP

import pytz
import undetected_chromedriver as uc
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ────────────────────────────────  USER CONFIG  ───────────────────────────────

LOOKER_PAGES = [
    "https://lookerstudio.google.com/embed/reporting/bf8f0517-e040-42c3-a6a9-e9d0b62885df/page/p_fsj6ky8zqd",
    "https://lookerstudio.google.com/embed/reporting/bf8f0517-e040-42c3-a6a9-e9d0b62885df/page/p_mv9sot1urd",
]

RECIPIENTS = ["niha.singhania@flipkart.com", "sujeeth.b@flipkart.com","gaddam.govardhan@flipkart.com"]  # Email recipients

LOAD_GRACE_SECONDS = 70                        # Wait this long after iframe loads
TZ_IST = pytz.timezone("Asia/Kolkata")         # Indian timezone

SMTP_USER = os.getenv("SMTP_USER")             # From environment variable
SMTP_PASS = os.getenv("SMTP_PASS")             # From environment variable

# ────────────────────────────────  BROWSER SETUP  ──────────────────────────────

def get_driver() -> uc.Chrome:
    """Initialize headless Chrome with required flags."""
    opts = uc.ChromeOptions()
    opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    return uc.Chrome(options=opts)

# ────────────────────────────────  SCREENSHOTS  ────────────────────────────────

def capture_screens() -> list[str]:
    """Capture screenshots of Looker Studio dashboards."""
    driver = get_driver()
    shots: list[str] = []

    for idx, url in enumerate(LOOKER_PAGES, 1):
        print(f"   Opening {url}")
        driver.get(url)

        try:
            # Wait up to 60 seconds for the iframe to appear
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.TAG_NAME, "iframe"))
            )
            print(f"   iframe found — sleeping {LOAD_GRACE_SECONDS}s for charts to render …")
        except TimeoutException:
            print("   iframe never appeared – taking blank shot for inspection")

        # Wait for charts to render after iframe loads
        time.sleep(LOAD_GRACE_SECONDS)

        # Save screenshot
        fname = f"screenshot_{idx}.png"
        driver.save_screenshot(fname)
        print(f"   Saved {fname}")
        shots.append(fname)

    driver.quit()
    return shots

# ────────────────────────────────  EMAIL SENDER  ───────────────────────────────

def send_mail(images: list[str]) -> None:
    """Send screenshots via email."""
    if not SMTP_USER or not SMTP_PASS:
        raise RuntimeError("SMTP_USER / SMTP_PASS env vars missing")

    # Timestamp in IST
    ist_now = dt.datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(TZ_IST)
    subject = f" OB Summary – {ist_now:%d %b %Y %I:%M %p IST}"

    # Email message setup
    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = ", ".join(RECIPIENTS)
    msg["Subject"] = subject
    msg.set_content(
        "Hi team,\n\nAttached are the latest PAN-India summary screenshots.\n\n— Onboarding Bot"
    )

    # Attach screenshots
    for p in images:
        with open(p, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="image",
                subtype="png",
                filename=os.path.basename(p)
            )

    # Send email via SMTP (Gmail)
    with SMTP("smtp.gmail.com", 587) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)

    print("   Mail sent!")

# ────────────────────────────────  MAIN ENTRY POINT  ───────────────────────────

if __name__ == "__main__":
    try:
        screenshots = capture_screens()
        send_mail(screenshots)
    except Exception as e:
        print("   Script failed:", e)
        traceback.print_exc()
