#!/usr/bin/env python3
"""
Take two Looker Studio screenshots with headless Chrome,
e‑mail them via Gmail API using a GCP service‑account,
then exit (for GitHub Actions).
"""

import os, time, datetime, pickle, base64, traceback
from email.message import EmailMessage

import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from google.oauth2 import service_account
from googleapiclient.discovery import build


# ── CONFIG ──────────────────────────────────────────────────────────────────── #

LOOKER_PAGES = [
    "https://lookerstudio.google.com/reporting/"
    "bf8f0517-e040-42c3-a6a9-e9d0b62885df/page/p_fsj6ky8zqd",
    "https://lookerstudio.google.com/reporting/"
    "bf8f0517-e040-42c3-a6a9-e9d0b62885df/page/p_c7fyt0w5qd",
]
RECIPIENTS = "niha.singhania@flipkart.com"
SENDER = "niha.singhania@flipkart.com" # Workspace mailbox you’ll send as
SA_FILE = "sa.json" # Written by the workflow step
COOKIE_FILE = "cookies.pkl" # Re‑used between runs
TIMEZONE = pytz.timezone("Asia/Kolkata")

# ── BROWSER HELPERS ─────────────────────────────────────────────────────────── #

def get_driver() -> webdriver.Chrome:
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=opts)


def load_cookies(driver, url: str):
    if not os.path.exists(COOKIE_FILE):
        return
    with open(COOKIE_FILE, "rb") as f:
        cookies = pickle.load(f)
    driver.get(url)
    time.sleep(5)
    for c in cookies:
        driver.add_cookie(c)
    driver.refresh()


def save_cookies(driver):
    with open(COOKIE_FILE, "wb") as f:
        pickle.dump(driver.get_cookies(), f)

# ── CORE FUNCTIONS ─────────────────────────────────────────────────────────── #

def capture_screens() -> list[str]:
    driver = get_driver()
    paths = []
    for i, url in enumerate(LOOKER_PAGES, 1):
        load_cookies(driver, url)
        print(f"⏳ Loading {url}")
        time.sleep(25) # allow charts to render
        path = f"screenshot_{i}.png"
        driver.save_screenshot(path)
        print(f"✅ Saved {path}")
        paths.append(path)
    save_cookies(driver)
    driver.quit()
    return paths


def gmail_service() -> build:
    creds = (
        service_account.Credentials.from_service_account_file(
            SA_FILE,
            scopes=["https://www.googleapis.com/auth/gmail.send"],
        )
        .with_subject(SENDER)
    )
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def send_mail(paths: list[str]):
    ist_now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(TIMEZONE)
    subject = f"📊 OB Summary Report – {ist_now:%Y-%m-%d %H:%M IST}"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SENDER
    msg["To"] = ", ".join(RECIPIENTS)
    msg.set_content(
        "Hi team,\n\nPlease find the latest PAN‑India summary screenshots attached.\n\n— Onboarding Bot"
    )

    for p in paths:
        with open(p, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="image",
                subtype="png",
                filename=os.path.basename(p),
            )

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    gmail_service().users().messages().send(userId="me", body={"raw": raw}).execute()
    print("📧 Mail sent via Gmail API")


# ── MAIN ───────────────────────────────────────────────────────────────────── #

if __name__ == "__main__":
    try:
        imgs = capture_screens()
        send_mail(imgs)
    except Exception:
        traceback.print_exc()
        raise
