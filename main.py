import time
import smtplib
import traceback
import pickle
import os
import datetime
import subprocess
import tempfile
import pytz
from email.message import EmailMessage
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

def setup_driver():
    print("🔄 Setting up Chrome WebDriver...")
    os.system("pkill -9 chrome")
    os.system("pkill -9 chromedriver")

    os.system("sudo apt-get update")
    os.system("sudo apt-get install -y google-chrome-stable")

    chrome_version = subprocess.check_output("google-chrome-stable --version", shell=True).decode("utf-8").strip().split(" ")[2]
    chromedriver_url = f"https://storage.googleapis.com/chrome-for-testing-public/{chrome_version}/linux64/chromedriver-linux64.zip"

    os.system(f"wget -q {chromedriver_url} -O chromedriver.zip")
    os.system("unzip -o chromedriver.zip")
    os.system("mv chromedriver-linux64/chromedriver /usr/bin/chromedriver")
    os.system("chmod +x /usr/bin/chromedriver")

    temp_dir = tempfile.mkdtemp()
    chrome_options = Options()
    chrome_options.add_argument(f"--user-data-dir={temp_dir}")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    print("✅ ChromeDriver is ready!")
    return driver

def save_cookies(driver):
    cookies = driver.get_cookies()
    with open("cookies.pkl", "wb") as file:
        pickle.dump(cookies, file)
    print("✅ Cookies saved.")

def load_cookies(driver, url):
    try:
        with open("cookies.pkl", "rb") as file:
            cookies = pickle.load(file)
        driver.get(url)
        time.sleep(15)
        for cookie in cookies:
            driver.add_cookie(cookie)
        print("✅ Cookies loaded successfully.")
    except FileNotFoundError:
        print("⚠️ No cookies found. Manual login required.")

def capture_screenshots():
    driver = setup_driver()
    dashboard_urls = [
        "https://lookerstudio.google.com/reporting/bf8f0517-e040-42c3-a6a9-e9d0b62885df/page/p_fsj6ky8zqd",
        "https://lookerstudio.google.com/reporting/bf8f0517-e040-42c3-a6a9-e9d0b62885df/page/p_c7fyt0w5qd"  # Replace with second dashboard URL
    ]

    screenshot_paths = []
    for i, url in enumerate(dashboard_urls):
        driver.get(url)
        print(f"⏳ Waiting for the page to load: {url}")
        time.sleep(30)  # Wait for the page to load initially
        load_cookies(driver, url)

        print("🔄 Refreshing page to load updated data...")
        driver.refresh()  # Refresh page after applying cookies
        time.sleep(30)  # Wait after refresh to ensure new data loads

        screenshot_path = f"dashboard_screenshot_{i+1}.png"
        driver.save_screenshot(screenshot_path)
        print(f"📸 Screenshot saved: {screenshot_path}")
        screenshot_paths.append(screenshot_path)

    save_cookies(driver)
    driver.quit()
    return screenshot_paths

def send_email(screenshot_paths):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    import os
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")

    recipient_email = "niha.singhania@flipkart.com",

    utc_now = datetime.datetime.utcnow()
    ist = pytz.timezone("Asia/Kolkata")
    current_time = utc_now.replace(tzinfo=pytz.utc).astimezone(ist).strftime("%Y-%m-%d %H:%M:%S")

    try:
        msg = EmailMessage()
        msg["Subject"] = f"📊 OB Summary Report for Trueflex & Vendors - {current_time} IST"
        msg["From"] = smtp_username
        msg["To"] = recipient_email
        msg.set_content("""
Dear Team,
Please find below the latest PAN India Summary Reports for both dashboards.

Regards,
Onboarding Team
        """)

        for i, screenshot_path in enumerate(screenshot_paths):
            with open(screenshot_path, "rb") as f:
                msg.add_attachment(f.read(), maintype="image", subtype="png", filename=f"dashboard_screenshot_{i+1}.png")

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)

        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        traceback.print_exc()

def run_periodic_task():
    while True:
        print("🚀 Running Looker Studio Screenshot Task...")
        screenshot_paths = capture_screenshots()
        if screenshot_paths:
            send_email(screenshot_paths)
        else:
            print("❌ Screenshot failed. Skipping email.")
        print("⏳ Waiting 1 hour...")
        time.sleep(3600)

run_periodic_task()
