# SOL YouTube Live Tracker Monitor

An automated Python system that monitors a YouTube Live stream for SOL (Solana) trading signals and sends email alerts with screenshots and current price data.

## Features

- **Automated Monitoring**: Checks YouTube live stream every 30 seconds
- **Signal Detection**: Detects BUY, SHORT, and TAKE PROFIT signals using OCR
- **Price Tracking**: Fetches real-time SOL/USDT prices from Binance
- **Email Alerts**: Sends detailed notifications with:
  - Signal type
  - Current SOL price
  - Timestamp
  - Screenshot attachment
- **Duplicate Prevention**: Avoids sending repeated alerts for the same signal
- **Robust Error Handling**: Continues running despite temporary network or OCR errors
- **Automatic Cleanup**: Manages screenshot storage to prevent disk space issues

## System Architecture

The system operates in a continuous loop:

1. **Browser Automation**: Uses Playwright to load and maintain the YouTube live stream
2. **Screenshot Capture**: Takes periodic screenshots of the stream
3. **OCR Processing**: Extracts text from screenshots using Tesseract
4. **Signal Detection**: Searches for trading signal keywords
5. **Price Fetching**: Queries Binance API for current SOL/USDT price
6. **Email Notification**: Sends alerts via SMTP with screenshot attachments
7. **State Management**: Tracks last signal to prevent duplicate alerts

## Prerequisites

- Python 3.8 or higher
- Tesseract OCR installed on your system
- Gmail account with App Password (or other SMTP email service)
- Stable internet connection

## Installation

### Step 1: Install System Dependencies

#### On Ubuntu/Debian:
```bash
sudo apt update
sudo apt install tesseract-ocr
```

#### On macOS:
```bash
brew install tesseract
```

#### On Windows:
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

After installation, add Tesseract to your system PATH.

### Step 2: Verify Tesseract Installation

```bash
tesseract --version
```

You should see the version information. If not, Tesseract is not properly installed or not in PATH.

### Step 3: Clone or Download This Repository

```bash
git clone <your-repo-url>
cd liveTracker
```

### Step 4: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Install Playwright Browsers

After installing the Python packages, install the required browser:

```bash
playwright install chromium
```

### Step 6: Configure Email Settings

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your email credentials:
   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your_email@gmail.com
   SMTP_PASSWORD=your_app_password
   SENDER_EMAIL=your_email@gmail.com
   ```

#### For Gmail Users:

You **cannot** use your regular Gmail password. You must create an App Password:

1. Go to your Google Account settings
2. Enable 2-Step Verification if not already enabled
3. Go to Security → 2-Step Verification → App passwords
4. Generate a new app password for "Mail"
5. Use this 16-character password in your `.env` file

See: https://support.google.com/accounts/answer/185833

#### For Other Email Providers:

- **Outlook/Hotmail**: `smtp-mail.outlook.com`, port 587
- **Yahoo**: `smtp.mail.yahoo.com`, port 587
- **Custom SMTP**: Consult your email provider's documentation

## Usage

### Running the Monitor

Start the monitoring script:

```bash
python sol_tracker_monitor.py
```

The script will:
- Initialize a headless browser
- Load the YouTube live stream
- Begin monitoring every 30 seconds
- Log all activities to the console
- Send email alerts when signals are detected

### Stopping the Monitor

Press `Ctrl+C` to gracefully stop the script.

### Running in Background (Linux/macOS)

To run the script continuously in the background:

```bash
nohup python sol_tracker_monitor.py > monitor.log 2>&1 &
```

To stop:
```bash
pkill -f sol_tracker_monitor.py
```

### Running as a Service (Recommended for Production)

For long-term deployment, consider using systemd (Linux) or launchd (macOS) to run as a service.

## Configuration

All configuration options are at the top of `sol_tracker_monitor.py`:

### Monitoring Settings

```python
# Check interval in seconds
CHECK_INTERVAL_SECONDS = 30

# Time to wait before sending duplicate alerts (in minutes)
DUPLICATE_COOLDOWN_MINUTES = 5
```

### Signal Keywords

```python
# Add or remove signal keywords (case-insensitive)
SIGNAL_KEYWORDS = ["BUY", "SHORT", "TAKE PROFIT"]
```

### OCR Region

By default, OCR processes the entire screenshot. To improve performance and accuracy, you can specify a region:

```python
# Coordinates: (x, y, width, height)
OCR_REGION = (100, 100, 800, 600)  # Example region

# Or use full screenshot:
OCR_REGION = None
```

**How to find the right region:**

1. Run the script and let it capture a few screenshots
2. Check the `screenshots/` directory
3. Open a screenshot and note the coordinates where signals appear
4. Update `OCR_REGION` with those coordinates

### Viewport Size

```python
# Adjust browser viewport if stream layout differs
VIEWPORT_WIDTH = 1920
VIEWPORT_HEIGHT = 1080
```

### Screenshot Storage

```python
SCREENSHOT_DIR = "screenshots"  # Directory for screenshots

# In cleanup_old_screenshots(), adjust retention:
keep_last_n: int = 50  # Keep last 50 screenshots
```

## Testing

### Test Email Configuration

Create a simple test script to verify your email settings:

```python
import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText

load_dotenv()

smtp_host = os.getenv('SMTP_HOST')
smtp_port = int(os.getenv('SMTP_PORT', '587'))
smtp_username = os.getenv('SMTP_USERNAME')
smtp_password = os.getenv('SMTP_PASSWORD')
sender_email = os.getenv('SENDER_EMAIL')

msg = MIMEText("Test email from SOL Tracker Monitor")
msg['Subject'] = "Test Email"
msg['From'] = sender_email
msg['To'] = "alkubaisi1818@gmail.com"

with smtplib.SMTP(smtp_host, smtp_port) as server:
    server.starttls()
    server.login(smtp_username, smtp_password)
    server.send_message(msg)

print("Test email sent!")
```

### Test OCR

To test Tesseract OCR:

```bash
tesseract screenshot.png output.txt
cat output.txt
```

### Test Signal Detection

Temporarily reduce the check interval for faster testing:

```python
CHECK_INTERVAL_SECONDS = 10  # Check every 10 seconds
```

## Troubleshooting

### Tesseract Not Found

**Error**: `TesseractNotFoundError`

**Solution**:
- Ensure Tesseract is installed: `tesseract --version`
- Add Tesseract to your PATH
- On Windows, set the path explicitly:
  ```python
  pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
  ```

### Email Authentication Failed

**Error**: `SMTPAuthenticationError`

**Solutions**:
- For Gmail: Use an App Password, not your regular password
- Verify your credentials in `.env`
- Check if 2-Step Verification is enabled (required for Gmail App Passwords)
- Some email providers require "Less secure app access" to be enabled

### YouTube Page Not Loading

**Error**: Browser timeout or navigation error

**Solutions**:
- Check your internet connection
- Try running with `headless=False` to see the browser
- Increase timeout in `load_youtube_stream()`:
  ```python
  page.goto(YOUTUBE_URL, wait_until='networkidle', timeout=60000)
  ```
- YouTube may have regional restrictions or rate limiting

### No Signals Detected

**Solutions**:
- Check the screenshots in `screenshots/` directory
- Verify signals are visible in the screenshots
- Adjust `OCR_REGION` to focus on the signal area
- Test OCR output manually with `tesseract screenshot.png output.txt`
- Add more keywords to `SIGNAL_KEYWORDS` if needed
- Improve image preprocessing for better OCR:
  ```python
  # In extract_text_from_screenshot(), before OCR:
  image = image.convert('L')  # Convert to grayscale
  image = image.point(lambda x: 0 if x < 140 else 255)  # Threshold
  ```

### High CPU/Memory Usage

**Solutions**:
- The script already refreshes the page every 100 iterations
- Reduce screenshot quality or size
- Increase `CHECK_INTERVAL_SECONDS`
- Crop `OCR_REGION` to reduce processing area

### Playwright Browser Issues

**Error**: Browser executable not found

**Solution**:
```bash
playwright install chromium
```

## File Structure

```
liveTracker/
├── sol_tracker_monitor.py   # Main script
├── requirements.txt          # Python dependencies
├── .env.example             # Example environment variables
├── .env                     # Your credentials (create this)
├── screenshots/             # Auto-created, stores screenshots
├── README.md               # This file
└── monitor.log             # Log file (if running with nohup)
```

## How It Works

### Duplicate Prevention Logic

The system tracks the last signal sent and prevents duplicates:

1. **First signal**: Always sent immediately
2. **Same signal repeated**: Only sent after cooldown period (default 5 minutes)
3. **Different signal**: Sent immediately, resets cooldown

Example:
- 10:00 - Detects "BUY" → Sends alert
- 10:02 - Detects "BUY" → Skipped (within cooldown)
- 10:03 - Detects "SHORT" → Sends alert (signal changed)
- 10:06 - Detects "BUY" → Sends alert (cooldown expired)

Adjust cooldown in configuration:
```python
DUPLICATE_COOLDOWN_MINUTES = 5  # Change to 10, 15, etc.
```

### Screenshot Management

- Screenshots are saved with timestamps: `screenshot_20240101_120000.png`
- Old screenshots are automatically deleted (keeps last 50 by default)
- Cleanup runs every 20 iterations to prevent disk space issues

### Price Fetching

- Uses Binance public API (no authentication required)
- Falls back gracefully if API is unavailable
- Email is still sent even if price fetch fails (shows "N/A")

## Advanced Customization

### Using Different APIs for Price

Replace the `get_current_sol_price()` function to use CoinGecko or other APIs:

```python
# CoinGecko example
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price"

def get_current_sol_price() -> Optional[float]:
    try:
        params = {'ids': 'solana', 'vs_currencies': 'usd'}
        response = requests.get(COINGECKO_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        price = data['solana']['usd']
        return float(price)
    except Exception as e:
        logger.error(f"Failed to fetch price: {e}")
        return None
```

### Adding More Signal Types

Simply add to the keywords list:

```python
SIGNAL_KEYWORDS = ["BUY", "SHORT", "TAKE PROFIT", "LONG", "SELL", "CLOSE"]
```

### Monitoring Multiple Streams

Create separate instances with different configuration files, or modify the script to accept command-line arguments.

## Security Notes

- **Never commit your `.env` file** to version control
- `.env` is already in `.gitignore`
- Use App Passwords for email, not your main password
- Keep your API keys and credentials secure

## License

This project is provided as-is for personal use.

## Support

For issues or questions:
- Check the Troubleshooting section above
- Review log output for specific errors
- Verify all dependencies are correctly installed

## Changelog

### Version 1.0.0 (Initial Release)
- Automated YouTube live stream monitoring
- OCR-based signal detection
- Email alerts with screenshots
- Binance API integration for price data
- Duplicate prevention system
- Robust error handling and logging
