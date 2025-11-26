#!/usr/bin/env python3
"""
SOL YouTube Live Tracker Monitor
Monitors a YouTube live stream for SOL trading signals and sends email alerts.
"""

import os
import time
import logging
import smtplib
import requests
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from pathlib import Path
from typing import Optional, Tuple

from playwright.sync_api import sync_playwright, Page
from PIL import Image
import pytesseract
from dotenv import load_dotenv

# ============================================================================
# CONFIGURATION
# ============================================================================

# YouTube live stream URL
YOUTUBE_URL = "https://www.youtube.com/live/CF2SVyV8A4I?si=WukMf7n9bbRbrK_r"

# Monitoring settings
CHECK_INTERVAL_SECONDS = 30  # Check every 30 seconds
DUPLICATE_COOLDOWN_MINUTES = 5  # Don't send same signal again for 5 minutes

# Signal keywords to detect (case-insensitive)
SIGNAL_KEYWORDS = ["BUY", "SHORT", "TAKE PROFIT"]

# OCR region (coordinates: x, y, width, height)
# None = full screenshot, or specify tuple like (100, 100, 800, 600)
# Adjust these values based on where signals appear on your stream
OCR_REGION = None  # Full screenshot by default

# Screenshot settings
SCREENSHOT_DIR = "screenshots"
VIEWPORT_WIDTH = 1920
VIEWPORT_HEIGHT = 1080

# Email settings (from environment variables)
RECIPIENT_EMAIL = "alkubaisi1818@gmail.com"

# API settings
BINANCE_API_URL = "https://api.binance.com/api/v3/ticker/price"
SOL_SYMBOL = "SOLUSDT"

# Logging configuration
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

# ============================================================================
# INITIALIZATION
# ============================================================================

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# Create screenshots directory
Path(SCREENSHOT_DIR).mkdir(exist_ok=True)

# State tracking for duplicate prevention
last_signal_sent = None
last_signal_time = None

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def initialize_browser(playwright):
    """
    Initialize and return a Playwright browser instance with a page.

    Args:
        playwright: Playwright instance

    Returns:
        tuple: (browser, page) objects
    """
    logger.info("Initializing browser...")
    browser = playwright.chromium.launch(
        headless=True,  # Set to False for debugging
        args=['--no-sandbox', '--disable-setuid-sandbox']
    )
    context = browser.new_context(
        viewport={'width': VIEWPORT_WIDTH, 'height': VIEWPORT_HEIGHT},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    )
    page = context.new_page()
    return browser, page


def load_youtube_stream(page: Page) -> bool:
    """
    Load the YouTube live stream page.

    Args:
        page: Playwright page object

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Loading YouTube stream: {YOUTUBE_URL}")
        page.goto(YOUTUBE_URL, wait_until='networkidle', timeout=30000)

        # Wait a moment for video player to load
        time.sleep(3)

        # Try to dismiss any popups/cookie notices
        try:
            # Click "Reject all" or "Accept all" on cookie consent if present
            reject_button = page.locator('button[aria-label*="Reject"]').first
            if reject_button.is_visible(timeout=2000):
                reject_button.click()
                time.sleep(1)
        except:
            pass

        logger.info("YouTube stream loaded successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to load YouTube stream: {e}")
        return False


def capture_screenshot(page: Page) -> Optional[str]:
    """
    Capture a screenshot of the current page.

    Args:
        page: Playwright page object

    Returns:
        str: Path to the saved screenshot, or None if failed
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(SCREENSHOT_DIR, f"screenshot_{timestamp}.png")

        logger.info("Capturing screenshot...")
        page.screenshot(path=screenshot_path, full_page=False)

        logger.info(f"Screenshot saved: {screenshot_path}")
        return screenshot_path

    except Exception as e:
        logger.error(f"Failed to capture screenshot: {e}")
        return None


def extract_text_from_screenshot(screenshot_path: str) -> str:
    """
    Extract text from screenshot using OCR.

    Args:
        screenshot_path: Path to the screenshot image

    Returns:
        str: Extracted text
    """
    try:
        logger.info("Running OCR on screenshot...")

        # Open image
        image = Image.open(screenshot_path)

        # Crop to OCR region if specified
        if OCR_REGION:
            x, y, w, h = OCR_REGION
            image = image.crop((x, y, x + w, y + h))

        # Run OCR
        text = pytesseract.image_to_string(image)

        logger.info(f"OCR extracted {len(text)} characters")
        logger.debug(f"OCR text preview: {text[:200]}")

        return text

    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return ""


def detect_signal(text: str) -> Optional[str]:
    """
    Detect trading signal from extracted text.

    Args:
        text: OCR-extracted text

    Returns:
        str: Detected signal keyword (uppercase), or None if no signal found
    """
    # Convert text to uppercase for case-insensitive matching
    text_upper = text.upper()

    # Check for each signal keyword
    for keyword in SIGNAL_KEYWORDS:
        if keyword.upper() in text_upper:
            logger.info(f"Signal detected: {keyword}")
            return keyword.upper()

    logger.debug("No signal detected")
    return None


def should_send_alert(signal: str) -> bool:
    """
    Determine if an alert should be sent based on duplicate prevention logic.

    Args:
        signal: Detected signal

    Returns:
        bool: True if alert should be sent, False otherwise
    """
    global last_signal_sent, last_signal_time

    # If no previous signal, always send
    if last_signal_sent is None:
        return True

    # If signal changed, always send
    if signal != last_signal_sent:
        logger.info(f"Signal changed from {last_signal_sent} to {signal}")
        return True

    # If same signal, check cooldown period
    time_since_last = datetime.now() - last_signal_time
    cooldown = timedelta(minutes=DUPLICATE_COOLDOWN_MINUTES)

    if time_since_last >= cooldown:
        logger.info(f"Cooldown period ({DUPLICATE_COOLDOWN_MINUTES} min) elapsed")
        return True

    logger.info(f"Skipping duplicate signal (cooldown: {cooldown - time_since_last} remaining)")
    return False


def update_signal_state(signal: str):
    """
    Update the last signal sent and timestamp.

    Args:
        signal: Signal that was sent
    """
    global last_signal_sent, last_signal_time
    last_signal_sent = signal
    last_signal_time = datetime.now()
    logger.info(f"Updated signal state: {signal} at {last_signal_time}")


def get_current_sol_price() -> Optional[float]:
    """
    Fetch current SOL/USDT price from Binance API.

    Returns:
        float: Current SOL price in USDT, or None if failed
    """
    try:
        logger.info("Fetching SOL price from Binance...")

        params = {'symbol': SOL_SYMBOL}
        response = requests.get(BINANCE_API_URL, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        price = float(data['price'])

        logger.info(f"Current SOL price: ${price:.2f}")
        return price

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch SOL price (network error): {e}")
        return None
    except (KeyError, ValueError) as e:
        logger.error(f"Failed to parse SOL price (invalid response): {e}")
        return None


def send_email(signal: str, price: Optional[float], screenshot_path: str):
    """
    Send email alert with signal details and screenshot.

    Args:
        signal: Detected signal (BUY, SHORT, TAKE PROFIT)
        price: Current SOL price in USDT
        screenshot_path: Path to screenshot attachment
    """
    try:
        # Get email configuration from environment
        smtp_host = os.getenv('SMTP_HOST')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        sender_email = os.getenv('SENDER_EMAIL')

        # Validate required settings
        if not all([smtp_host, smtp_username, smtp_password, sender_email]):
            logger.error("Missing required email configuration in environment variables")
            logger.error("Please set: SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SENDER_EMAIL")
            return

        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = RECIPIENT_EMAIL

        # Format price
        price_str = f"${price:.2f}" if price else "N/A"

        # Subject
        msg['Subject'] = f"SOL SIGNAL: {signal} at {price_str}"

        # Body
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")
        body = f"""
Detected Signal: {signal}

Current SOL Price: {price_str} USDT
Timestamp: {timestamp}

Screenshot of the live tracker is attached.

---
This is an automated alert from the SOL Tracker Monitor.
        """.strip()

        msg.attach(MIMEText(body, 'plain'))

        # Attach screenshot
        try:
            with open(screenshot_path, 'rb') as f:
                img = MIMEImage(f.read())
                img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(screenshot_path))
                msg.attach(img)
        except Exception as e:
            logger.warning(f"Failed to attach screenshot: {e}")

        # Send email
        logger.info(f"Sending email to {RECIPIENT_EMAIL}...")

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)

        logger.info("Email sent successfully!")

    except Exception as e:
        logger.error(f"Failed to send email: {e}")


def cleanup_old_screenshots(keep_last_n: int = 50):
    """
    Delete old screenshots to prevent disk space issues.

    Args:
        keep_last_n: Number of most recent screenshots to keep
    """
    try:
        screenshots = sorted(
            Path(SCREENSHOT_DIR).glob("screenshot_*.png"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        # Delete older screenshots
        for screenshot in screenshots[keep_last_n:]:
            screenshot.unlink()
            logger.debug(f"Deleted old screenshot: {screenshot}")

    except Exception as e:
        logger.warning(f"Failed to cleanup screenshots: {e}")


def process_frame(page: Page) -> bool:
    """
    Process a single frame: capture, OCR, detect signal, and send alert if needed.

    Args:
        page: Playwright page object

    Returns:
        bool: True if processing succeeded, False otherwise
    """
    try:
        # Capture screenshot
        screenshot_path = capture_screenshot(page)
        if not screenshot_path:
            return False

        # Extract text using OCR
        text = extract_text_from_screenshot(screenshot_path)
        if not text:
            logger.warning("No text extracted from screenshot")
            return True  # Not a critical error

        # Detect signal
        signal = detect_signal(text)
        if not signal:
            logger.info("No trading signal detected in this frame")
            return True

        # Check if we should send alert
        if not should_send_alert(signal):
            return True

        # Get current SOL price
        price = get_current_sol_price()

        # Send email alert
        send_email(signal, price, screenshot_path)

        # Update state
        update_signal_state(signal)

        return True

    except Exception as e:
        logger.error(f"Error processing frame: {e}")
        return False


def main_loop():
    """
    Main monitoring loop.
    """
    logger.info("=" * 80)
    logger.info("SOL YouTube Live Tracker Monitor Starting")
    logger.info("=" * 80)
    logger.info(f"YouTube URL: {YOUTUBE_URL}")
    logger.info(f"Check interval: {CHECK_INTERVAL_SECONDS} seconds")
    logger.info(f"Signal keywords: {', '.join(SIGNAL_KEYWORDS)}")
    logger.info(f"Duplicate cooldown: {DUPLICATE_COOLDOWN_MINUTES} minutes")
    logger.info(f"Recipient email: {RECIPIENT_EMAIL}")
    logger.info("=" * 80)

    iteration = 0
    browser = None
    page = None

    try:
        with sync_playwright() as playwright:
            # Initialize browser
            browser, page = initialize_browser(playwright)

            # Load YouTube stream
            if not load_youtube_stream(page):
                logger.error("Failed to load YouTube stream. Exiting.")
                return

            logger.info("Starting monitoring loop (Press Ctrl+C to stop)...")

            while True:
                iteration += 1
                logger.info(f"\n--- Iteration {iteration} ---")

                try:
                    # Process current frame
                    success = process_frame(page)

                    if not success:
                        logger.warning("Frame processing failed, will retry next iteration")

                    # Periodic cleanup
                    if iteration % 20 == 0:
                        cleanup_old_screenshots()

                    # Refresh page periodically to avoid memory issues
                    if iteration % 100 == 0:
                        logger.info("Refreshing page to prevent memory issues...")
                        load_youtube_stream(page)

                except Exception as e:
                    logger.error(f"Error in iteration {iteration}: {e}")

                # Wait before next check
                logger.info(f"Waiting {CHECK_INTERVAL_SECONDS} seconds until next check...")
                time.sleep(CHECK_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        logger.info("\nReceived interrupt signal. Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error in main loop: {e}")
    finally:
        # Cleanup
        if browser:
            logger.info("Closing browser...")
            browser.close()

        logger.info("Shutdown complete.")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Verify Tesseract installation
    try:
        pytesseract.get_tesseract_version()
        logger.info(f"Tesseract version: {pytesseract.get_tesseract_version()}")
    except Exception as e:
        logger.error("Tesseract OCR is not installed or not in PATH!")
        logger.error("Please install Tesseract: https://github.com/tesseract-ocr/tesseract")
        exit(1)

    # Run main loop
    main_loop()
