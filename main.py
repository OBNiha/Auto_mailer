"""
main.py – grab two Looker Studio pages, e‑mail screenshots, exit.
Runs inside GitHub Actions; Chrome + chromedriver are pre‑installed.
"""

import time
import datetime
import pytz
import pickle
import traceback
import os
from email.message import EmailMessage
import smtplib
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# List of Looker Studio pages to capture screenshots from
LOOKER_PAGES = [
    "https://lookerstudio.google.com/reporting/bf8f0517-e040-42c3-a6a9-e9d0b62885df/page/p_fsj6ky8zqd",
    "https://lookerstudio.google.com/reporting/bf8f0517-e040-42c3-a6a9-e9d0b62885df/page/p_c7fyt0w5qd",
]

# File to store cookies for session management
COOKIE_FILE = "cookies.pkl"


def get_driver() -> webdriver.Chrome:
    """
    Initializes and returns a headless Chrome WebDriver with the necessary options.
    """
    opts = Options()
    opts.add_argument("--headless=new")  # Run headless (no UI)
    opts.add_argument("--no-sandbox")    # Disables the sandbox for the Chromium process
    opts.add_argument("--disable-dev-shm-usage")  # Avoids limited memory usage errors
    opts.add_argument("--window-size=1920,1080")  # Sets window size to capture full page
    return webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=opts)


def load_cookies(driver, url):
    """
    Loads cookies from a pickle file to maintain session across script runs.
    If cookies are not found, it will print a message and let the user log in manually.
    """
    try:
        with open(COOKIE_FILE, "rb") as f:
            cookies = pickle.load(f)
        driver.get(url)
        time.sleep(5)  # Allow time for the page to load
        for c in cookies:
            driver.add_cookie(c)
        driver.refresh()
    except FileNotFoundError:
        print("No cookies.pkl – first run will require manual login and saving.")


def save_cookies(driver):
    """
    Saves the current cookies to a file for future session use.
    """
    with open(COOKIE_FILE, "wb") as f:
        pickle.dump(driver.get_cookies(), f)


def capture():
    """
    Captures screenshots of the Looker Studio pages and returns a list of file paths.
    """
    driver = get_driver()  # Initialize the WebDriver
    paths = []
    for i, url in enumerate(LOOKER_PAGES, 1):
        load_cookies(driver, url)  # Load cookies for maintaining session
        print(f"⏳ loading {url}")
        time.sleep(25)  # Let charts render fully before taking a screenshot
        path = f"screenshot_{i}.png"
        driver.save_screenshot(path)  # Capture screenshot and save it
        paths.append(path)
        print(f"✅ saved {path}")
    
    save_cookies(driver)  # Save cookies for future use
    driver.quit()  # Close the browser
    return paths


def send_mail(paths):
    """
    Sends an email with the screenshots as attachments.
    """
    smtp_user = os.getenv("SMTP_USERNAME")  # Fetch SMTP username from environment variables
    smtp_pass = os.getenv("SMTP_PASSWORD")  # Fetch SMTP password from environment variables
    recips = ["niha.singhania@flipkart.com", "sujeeth.b@flipkart.com", "gaddam.govardhan@flipkart.com"]  # List of recipients

    # Get the current time in IST timezone for email subject
    ist_now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(pytz.timezone("Asia/Kolkata"))
    subject = f"📊 OB Summary Report – {ist_now:%Y-%m-%d %H:%M IST}"

    # Create the email message with subject, body, and recipients
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = ", ".join(recips)
    msg.set_content("Attached: latest PAN‑India summary screenshots.\n— Onboarding Bot")

    # Attach screenshots to the email
    for p in paths:
        with open(p, "rb") as f:
            msg.add_attachment(f.read(), maintype="image", subtype="png", filename=p)

    # Send the email using Gmail's SMTP server
    with smtplib.SMTP("smtp.gmail.com", 587) as s:
        s.starttls()  # Upgrade the connection to a secure encrypted SSL/TLS connection
        s.login(smtp_user, smtp_pass)  # Log in to the SMTP server
        s.send_message(msg)  # Send the email
    print("📧 mail sent")


if __name__ == "__main__":
    """
    Main function to capture screenshots and send the email.
    If any error occurs, it prints the stack trace and surfaces the error to GitHub Actions.
    """
    try:
        screenshots = capture()  # Capture screenshots
        send_mail(screenshots)  # Send email with screenshots
    except Exception:
        traceback.print_exc()  # Print error stack trace
        raise  # Reraise the error to GitHub Actions
