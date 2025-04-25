"""Auto-grab public Looker-Studio dashboards and e-mail them.
▸ Share each report ► Manage access ► Anyone on the internet – Viewer
▸ Copy the *embed* link(s) into LOOKER_PAGES below
"""

import os
import traceback
import datetime as dt
from email.message import EmailMessage
from smtplib import SMTP
import pytz
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ──────────────────────────────────────────────────────────── #
# EMBED LINKS
# ──────────────────────────────────────────────────────────── #
LOOKER_PAGES = [
    "https://lookerstudio.google.com/embed/reporting/bf8f0517-e040-42c3-a6a9-e9d0b62885df/page/p_fsj6ky8zqd",
    "https://lookerstudio.google.com/embed/reporting/bf8f0517-e040-42c3-a6a9-e9d0b62885df/page/p_mv9sot1urd",
]

# List of email recipients
RECIPIENTS = ["niha.singhania@flipkart.com"]

# Timezone setup
TZ_IST = pytz.timezone("Asia/Kolkata")

# SMTP credentials pulled from environment variables
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

# ──────────────────────────────────────────────────────────── #
# Chrome helper
# ──────────────────────────────────────────────────────────── #
def get_driver() -> uc.Chrome:
    # Configure and return a headless undetected Chrome driver instance
    opts = uc.ChromeOptions()
    opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    return uc.Chrome(options=opts)

# ──────────────────────────────────────────────────────────── #
# Screen-capture with *active* waits
# ──────────────────────────────────────────────────────────── #
def capture_screens(max_wait_outer=60, max_wait_inner=60) -> list[str]:
    """
    • Waits up to `max_wait_outer` s for the <iframe> container.
    • Then switches *into* the iframe and waits up to `max_wait_inner` s
      for a chart element (<canvas>, <svg>, or <img>).
    """
    driver = get_driver()
    shots: list[str] = []

    for idx, url in enumerate(LOOKER_PAGES, 1):
        print(f" Opening {url}")
        driver.get(url)

        # Wait for iframe to load
        iframe = WebDriverWait(driver, max_wait_outer).until(
            EC.presence_of_element_located((By.TAG_NAME, "iframe"))
        )
        print(" iframe found")

        # Switch to iframe and wait for charts/images to appear
        driver.switch_to.frame(iframe)
        WebDriverWait(driver, max_wait_inner).until(
            EC.any_of(
                EC.presence_of_element_located((By.TAG_NAME, "canvas")),
                EC.presence_of_element_located((By.TAG_NAME, "svg")),
                EC.presence_of_element_located((By.TAG_NAME, "img")),
            )
        )
        print(" chart(s) detected — ready to shoot")

        # Capture screenshot from top-level context
        driver.switch_to.default_content()
        fname = f"screenshot_{idx}.png"
        driver.save_screenshot(fname)
        print(f" Saved {fname}")
        shots.append(fname)

    driver.quit()
    return shots

# ──────────────────────────────────────────────────────────── #
# Mail helper
# ──────────────────────────────────────────────────────────── #
def send_mail(images: list[str]) -> None:
    # Ensure SMTP credentials are present
    if not SMTP_USER or not SMTP_PASS:
        raise RuntimeError("SMTP_USER / SMTP_PASS env vars missing")

    # Format subject with current IST timestamp
    ist_now = dt.datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(TZ_IST)
    subject = f" OB Summary – {ist_now:%d %b %Y %I:%M %p IST}"

    # Compose email
    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = ", ".join(RECIPIENTS)
    msg["Subject"] = subject
    msg.set_content(
        "Hi team,\n\nAttached are the latest PAN-India summary screenshots.\n\n— Onboarding Bot"
    )

    # Attach screenshots to the email
    for path in images:
        with open(path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="image",
                subtype="png",
                filename=os.path.basename(path)
            )

    # Send the email using Gmail SMTP
    with SMTP("smtp.gmail.com", 587) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)
    print(" Mail sent!")

# ──────────────────────────────────────────────────────────── #
# Main
# ──────────────────────────────────────────────────────────── #
if __name__ == "__main__":
    try:
        imgs = capture_screens()
        send_mail(imgs)
    except Exception as exc:
        print(" Script failed:", exc)
        traceback.print_exc()
