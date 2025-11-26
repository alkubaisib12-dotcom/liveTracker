# Windows Setup Guide - SOL Tracker Monitor

Complete guide for setting up and running the SOL tracker on Windows.

## Prerequisites

- Windows 10 or 11
- Python 3.8 or higher (installed and added to PATH)
- Stable internet connection

## Step-by-Step Installation

### 1. Verify Python Installation

Open PowerShell or Command Prompt and check:

```powershell
python --version
```

You should see Python 3.8 or higher. If not installed, download from: https://www.python.org/downloads/

**IMPORTANT:** During Python installation, check "Add Python to PATH"

### 2. Update pip (Recommended)

```powershell
python -m pip install --upgrade pip
```

### 3. Install Tesseract OCR

Tesseract is required for reading text from screenshots.

**Download Tesseract:**
- Go to: https://github.com/UB-Mannheim/tesseract/wiki
- Download the latest Windows installer (tesseract-ocr-w64-setup-X.X.X.exe)
- Run the installer

**Important during installation:**
- Note the installation path (usually `C:\Program Files\Tesseract-OCR`)
- The installer should add Tesseract to your PATH automatically

**Verify Tesseract installation:**
```powershell
tesseract --version
```

If you see version information, it's installed correctly.

**If "tesseract is not recognized":**

You need to add Tesseract to PATH manually:
1. Open System Properties → Advanced → Environment Variables
2. Under "System variables", find "Path"
3. Click "Edit" → "New"
4. Add: `C:\Program Files\Tesseract-OCR`
5. Click OK, close and reopen PowerShell

### 4. Navigate to Project Directory

```powershell
cd C:\Users\a.alkubaesy\liveTracker
```

### 5. Install Python Dependencies

```powershell
pip install -r requirements.txt
```

This installs:
- playwright (browser automation)
- Pillow (image processing)
- pytesseract (OCR wrapper)
- requests (HTTP requests)
- python-dotenv (environment variables)

**If you still get errors with Pillow**, try installing packages individually:

```powershell
pip install playwright
pip install Pillow
pip install pytesseract
pip install requests
pip install python-dotenv
```

### 6. Install Playwright Browser

```powershell
playwright install chromium
```

This downloads the Chromium browser needed for automation (~150MB).

### 7. Test Tesseract Integration

Create a test file `test_tesseract.py`:

```python
import pytesseract

# If tesseract is not in PATH, set it explicitly:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

try:
    version = pytesseract.get_tesseract_version()
    print(f"✅ Tesseract is working! Version: {version}")
except Exception as e:
    print(f"❌ Tesseract error: {e}")
    print("Set the path explicitly in sol_tracker_monitor.py")
```

Run it:
```powershell
python test_tesseract.py
```

**If Tesseract is not found**, you need to set the path in `sol_tracker_monitor.py`.

### 8. Set Tesseract Path (If Needed)

If Tesseract is not automatically found, edit `sol_tracker_monitor.py` and add this line after the imports (around line 23):

```python
# Add this line if Tesseract is not in PATH
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

## Running the Monitor

### Test Mode (No Emails)

The script is configured for testing by default:

```powershell
python sol_tracker_monitor.py
```

**What happens:**
- Opens YouTube live stream (headless browser)
- Captures screenshots every 30 seconds
- Logs current SOL price
- Shows OCR text extracted from stream
- Logs what emails WOULD be sent (but doesn't send)
- Screenshots saved in `screenshots\` folder

**To stop:** Press `Ctrl+C`

### Check Screenshots

```powershell
dir screenshots
```

Open some screenshots to verify:
- Stream is loading correctly
- Signals are visible
- Quality is good

### Faster Testing

For quicker testing, edit `sol_tracker_monitor.py` line 32:

```python
CHECK_INTERVAL_SECONDS = 10  # Check every 10 seconds instead of 30
```

## Production Mode (Send Real Emails)

When ready to send actual emails:

### 1. Create `.env` File

Copy the example:
```powershell
copy .env.example .env
```

Edit `.env` in Notepad:
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_16_char_app_password
SENDER_EMAIL=your_email@gmail.com
```

**For Gmail, you MUST use an App Password:**
1. Go to: https://myaccount.google.com/security
2. Enable 2-Step Verification
3. Go to: https://myaccount.google.com/apppasswords
4. Create app password for "Mail"
5. Use the 16-character password in `.env`

### 2. Disable Dry-Run Mode

Edit `sol_tracker_monitor.py` line 36:

```python
DRY_RUN = False  # Change from True to False
```

### 3. Run in Production

```powershell
python sol_tracker_monitor.py
```

Now emails will be sent to `alkubaisi1818@gmail.com` when signals are detected!

## Running in Background

### Option 1: PowerShell Background

```powershell
Start-Process python -ArgumentList "sol_tracker_monitor.py" -WindowStyle Hidden
```

To stop, find and kill the process in Task Manager.

### Option 2: Using `pythonw` (No Console Window)

```powershell
pythonw sol_tracker_monitor.py
```

This runs without a console window. To stop, use Task Manager.

### Option 3: Redirect Output to File

```powershell
python sol_tracker_monitor.py > monitor.log 2>&1
```

All output goes to `monitor.log` file.

## Troubleshooting

### Issue: "python is not recognized"

**Solution:** Add Python to PATH:
1. Find Python installation (usually `C:\Users\USERNAME\AppData\Local\Programs\Python\PythonXX`)
2. Add to System PATH in Environment Variables
3. Restart PowerShell

### Issue: "playwright install fails"

**Solution:** Run PowerShell as Administrator:
```powershell
playwright install chromium
```

### Issue: "ModuleNotFoundError"

**Solution:** Ensure you're in the correct directory and virtual environment (if using one):
```powershell
pip list  # Check installed packages
pip install -r requirements.txt  # Reinstall
```

### Issue: "Tesseract not found" even after installation

**Solutions:**
1. Verify Tesseract is in PATH: `tesseract --version`
2. Set path explicitly in `sol_tracker_monitor.py`:
   ```python
   import pytesseract
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```
3. Restart PowerShell after adding to PATH

### Issue: "Access Denied" or "Permission Error"

**Solutions:**
- Run PowerShell as Administrator
- Install to user directory: `pip install --user -r requirements.txt`
- Disable antivirus temporarily

### Issue: YouTube page not loading

**Solutions:**
- Check internet connection
- Firewall may be blocking the browser
- Try running with `headless=False` to see the browser (edit line 93)
- YouTube may have regional restrictions

### Issue: No signals detected

**Solutions:**
1. Check screenshots in `screenshots\` folder
2. Verify signals are visible in images
3. Review OCR output in logs
4. Adjust `OCR_REGION` if needed
5. Test OCR manually: `tesseract screenshot.png output.txt`

### Issue: High CPU usage

**Solutions:**
- Increase `CHECK_INTERVAL_SECONDS` to 60 or more
- Reduce `VIEWPORT_WIDTH` and `VIEWPORT_HEIGHT`
- Set `OCR_REGION` to process only signal area

## Configuration Options

Edit these in `sol_tracker_monitor.py`:

```python
# Check frequency
CHECK_INTERVAL_SECONDS = 30  # How often to check (seconds)

# Testing vs Production
DRY_RUN = True  # True = testing, False = send emails

# Signals to detect
SIGNAL_KEYWORDS = ["BUY", "SHORT", "TAKE PROFIT"]

# OCR region (optional - for better performance)
OCR_REGION = None  # or (x, y, width, height)

# Viewport size
VIEWPORT_WIDTH = 1920
VIEWPORT_HEIGHT = 1080
```

## Performance Tips

1. **Use OCR Region:** Process only the area where signals appear
   ```python
   OCR_REGION = (100, 100, 800, 400)  # Adjust based on your screenshots
   ```

2. **Reduce Resolution:** Lower viewport size if CPU usage is high
   ```python
   VIEWPORT_WIDTH = 1280
   VIEWPORT_HEIGHT = 720
   ```

3. **Increase Interval:** Check less frequently
   ```python
   CHECK_INTERVAL_SECONDS = 60  # Check every minute
   ```

## File Structure on Windows

```
C:\Users\a.alkubaesy\liveTracker\
├── sol_tracker_monitor.py      # Main script
├── requirements.txt             # Dependencies
├── .env.example                # Email config template
├── .env                        # Your credentials (create this)
├── screenshots\                # Auto-created screenshots
├── README.md                   # General documentation
├── TESTING_GUIDE.md            # Testing instructions
└── WINDOWS_SETUP.md            # This file
```

## Next Steps

1. ✅ Verify all installations with the test commands above
2. ✅ Run in test mode: `python sol_tracker_monitor.py`
3. ✅ Check logs and screenshots
4. ✅ When satisfied, configure `.env` for email
5. ✅ Set `DRY_RUN = False` for production

## Support

If you encounter issues:
1. Check the error message carefully
2. Verify all prerequisites are installed
3. Review the Troubleshooting section above
4. Check `screenshots\` folder to see what's being captured
5. Review the main README.md and TESTING_GUIDE.md

## Windows Firewall

Windows Defender may prompt you to allow Python and Chromium:
- Click "Allow access" when prompted
- Or manually allow in: Settings → Privacy & Security → Windows Security → Firewall & network protection

Good luck with your SOL tracker! 🚀
