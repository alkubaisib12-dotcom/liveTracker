# Testing Guide - SOL Tracker Monitor

## Quick Testing Setup

### 1. Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Install Tesseract OCR
# Ubuntu/Debian:
sudo apt install tesseract-ocr

# macOS:
brew install tesseract
```

### 2. Run in Dry-Run Mode (Testing)

The script is **already configured for testing** with `DRY_RUN = True`.

In this mode:
- ✅ Connects to YouTube live stream
- ✅ Captures screenshots every 30 seconds
- ✅ Runs OCR to extract text
- ✅ Logs the current SOL price
- ✅ Detects signals (BUY, SHORT, TAKE PROFIT)
- ✅ Logs what email WOULD be sent
- ❌ Does NOT send actual emails

```bash
python sol_tracker_monitor.py
```

### 3. What You'll See

**Every 30 seconds:**
```
--- Iteration 1 ---
💰 Current SOL/USDT Price: $242.3456
Capturing screenshot...
Screenshot saved: screenshots/screenshot_20251126_143000.png
Running OCR on screenshot...
OCR extracted 1234 characters
OCR Text Extracted:
============================================================
[The actual text extracted from the stream will appear here]
============================================================
✅ No trading signal detected in this frame - monitoring continues
Waiting 30 seconds until next check...
```

**When a signal is detected:**
```
🚨 SIGNAL DETECTED: BUY 🚨
Fetching SOL price from Binance...
Current SOL price: $242.34

================================================================================
📧 [DRY RUN] EMAIL WOULD BE SENT:
================================================================================
To: alkubaisi1818@gmail.com
Subject: SOL SIGNAL: BUY at $242.34
--------------------------------------------------------------------------------
Body:
Detected Signal: BUY

Current SOL Price: $242.34 USDT
Timestamp: 2025-11-26 14:30:00

Screenshot of the live tracker is attached.

---
This is an automated alert from the SOL Tracker Monitor.
--------------------------------------------------------------------------------
Attachment: screenshots/screenshot_20251126_143000.png
================================================================================
📧 [DRY RUN] Email NOT actually sent (DRY_RUN=True)
================================================================================
```

### 4. Check Screenshots

While testing, check the `screenshots/` directory to see what's being captured:

```bash
ls -lh screenshots/
```

Open a few screenshots to verify:
- The stream is loading correctly
- Signals are visible in the image
- The quality is good enough for OCR

### 5. Adjusting Check Interval

For faster testing, reduce the check interval:

Edit `sol_tracker_monitor.py` line 32:
```python
CHECK_INTERVAL_SECONDS = 10  # Check every 10 seconds (instead of 30)
```

### 6. Testing Signal Detection

To test if signals are being detected:

1. Run the script for a few minutes
2. Check the OCR output in the logs
3. Look for the signal keywords in the extracted text
4. If signals aren't detected but are visible in screenshots, you may need to:
   - Adjust the OCR region
   - Improve image preprocessing

### 7. When Ready for Production

When you're home and ready to send real emails:

1. **Create `.env` file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your Gmail App Password:**
   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your_email@gmail.com
   SMTP_PASSWORD=your_16_char_app_password
   SENDER_EMAIL=your_email@gmail.com
   ```

3. **Disable dry-run mode** in `sol_tracker_monitor.py` line 36:
   ```python
   DRY_RUN = False  # Now emails will be sent
   ```

4. **Run the script:**
   ```bash
   python sol_tracker_monitor.py
   ```

### 8. Stopping the Script

Press `Ctrl+C` to stop the monitor gracefully.

## Troubleshooting During Testing

### "Tesseract not found"
```bash
# Verify installation
tesseract --version

# If not found, install:
# Ubuntu: sudo apt install tesseract-ocr
# macOS: brew install tesseract
```

### "Playwright browser not found"
```bash
playwright install chromium
```

### No text extracted from screenshots
- Check screenshots manually - are they showing the stream?
- The stream might not be loading - check your internet connection
- YouTube might have anti-bot protections - try setting `headless=False` temporarily

### Want to see the browser
Edit line 93 in `sol_tracker_monitor.py`:
```python
headless=False,  # You'll see the browser window
```

## Understanding the Logs

| Log Message | Meaning |
|-------------|---------|
| `💰 Current SOL/USDT Price: $X.XX` | Current price fetched from Binance |
| `OCR extracted X characters` | How much text was found |
| `OCR Text Extracted:` | The actual text seen in the screenshot |
| `✅ No trading signal detected` | No BUY/SHORT/TAKE PROFIT found |
| `🚨 SIGNAL DETECTED: BUY 🚨` | Signal found! |
| `📧 [DRY RUN] EMAIL WOULD BE SENT` | What the email would contain (testing mode) |
| `Signal changed from X to Y` | Different signal detected, will send alert |
| `Skipping duplicate signal` | Same signal within cooldown period |

## Next Steps

1. ✅ Run in dry-run mode and verify it connects to YouTube
2. ✅ Check screenshots to see if signals are visible
3. ✅ Review OCR output to see if text is being extracted
4. ✅ Wait to see if signals are detected
5. ✅ When home with Gmail access, configure `.env` and set `DRY_RUN=False`
