"""Grab public Looker-Studio dashboards → e-mail them.
    The reports **must** be shared with:    Share ▸ Manage access ▸ Anyone on the internet → Viewer"""

import os, time, traceback, datetime as dt
from email.message import EmailMessage
from smtplib import SMTP
import pytz
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ───────────────────────────────────────────────────────────── 
# LIST YOUR *EMBED* LINKS HERE (after making them public)
# ───────────────────────────────────────────────────────────── 
# Example URLs of the Looker Studio reports you wish to capture
LOOKER_PAGES = [
    "https://lookerstudio.google.com/embed/reporting/bf8f0517-e040-42c3-a6a9-e9d0b62885df/page/p_fsj6ky8zqd",
    "https://lookerstudio.google.com/embed/reporting/bf8f0517-e040-42c3-a6a9-e9d0b62885df/page/p_mv9sot1urd",
]

# Email settings
RECIPIENTS = ["niha.singhania@flipkart.com"]  # List of recipients to send the email to
TZ_IST = pytz.timezone("Asia/Kolkata")  # Time zone set to IST (Indian Standard Time)
SMTP_USER = os.getenv("SMTP_USER")  # Get SMTP user from environment variable
SMTP_PASS = os.getenv("SMTP_PASS")  # Get SMTP password from environment variable

# Function to initialize the Chrome WebDriver
def get_driver() -> uc.Chrome:
    opts = uc.ChromeOptions()
    opts.add_argument("--headless=new")  # Run browser in headless mode (without GUI)
    opts.add_argument("--window-size=1920,1080")  # Set browser window size
    opts.add_argument("--no-sandbox")  # Disable sandbox for the browser
    opts.add_argument("--disable-dev-shm-usage")  # Disable shared memory usage (for Docker)
    opts.add_argument("--disable-blink-features=AutomationControlled")  # Disable automation features to bypass detection
    return uc.Chrome(options=opts)  # Return the WebDriver instance

# Function to capture screenshots of Looker Studio pages
def capture_screens() -> list[str]:
    driver = get_driver()  # Initialize WebDriver
    shots: list[str] = []  # List to store the screenshot file paths
    for idx, url in enumerate(LOOKER_PAGES, 1):  # Iterate through all Looker pages
        print(f" Opening {url}")
        driver.get(url)  # Open the Looker page in the browser
        time.sleep(5)  # Wait for 5 seconds to let any redirects complete
        final_url = driver.current_url  # Get the current URL
        print(" Current URL →", final_url)

        # Check if the page is public by looking for 'lookerstudio.google.com' in the URL
        if "lookerstudio.google.com" not in final_url:
            driver.quit()  # Close the browser if the page is not public
            raise RuntimeError("Report isn’t public – set sharing to 'Anyone on the internet'.")

        # Wait for the first iframe (chart container) to appear
        try:
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.TAG_NAME, "iframe"))
            )
        except Exception:
            print(" Chart load timed out – taking full-page screenshot anyway.")
        
        # Save the screenshot with a unique file name
        fname = f"screenshot_{idx}.png"
        driver.save_screenshot(fname)
        print(f" Saved {fname}")
        shots.append(fname)  # Add the screenshot file path to the list
    driver.quit()  # Close the WebDriver after capturing screenshots
    return shots  # Return the list of screenshot file paths

# Function to send an email with the screenshots attached
def send_mail(images: list[str]) -> None:
    if not SMTP_USER or not SMTP_PASS:
        raise RuntimeError("SMTP_USER / SMTP_PASS env vars missing")  # Ensure SMTP credentials are set

    # Get current time in IST and format the subject line
    ist_now = dt.datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(TZ_IST)
    subject = f" OB Summary – {ist_now:%d %b %Y %I:%M %p IST}"
    
    # Set up the email message
    msg = EmailMessage()
    msg["From"] = SMTP_USER  # Sender email address
    msg["To"] = ", ".join(RECIPIENTS)  # Recipient email addresses
    msg["Subject"] = subject  # Subject line
    msg.set_content(
        "Hi team,\n\nAttached are the latest PAN-India summary screenshots.\n\n— Onboarding Bot"
    )  # Email body text
    
    # Attach screenshots to the email
    for path in images:
        with open(path, "rb") as f:  # Open the screenshot file in binary mode
            msg.add_attachment(f.read(), maintype="image", subtype="png",
                               filename=os.path.basename(path))  # Attach as PNG image
    
    # Send the email using SMTP
    with SMTP("smtp.gmail.com", 587) as s:
        s.starttls()  # Start TLS encryption for the SMTP connection
        s.login(SMTP_USER, SMTP_PASS)  # Log in to the SMTP server
        s.send_message(msg)  # Send the email message
    print(" Mail sent!")  # Print confirmation after sending the email

# Main script execution
if __name__ == "__main__":
    try:
        imgs = capture_screens()  # Capture screenshots
        send_mail(imgs)  # Send the email with the captured screenshots
    except Exception as exc:  # Handle any errors
        print(" Script failed:", exc)  # Print the error message
        traceback.print_exc()  # Print the traceback for debugging
