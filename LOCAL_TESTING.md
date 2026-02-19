# Local Testing Guide (Optional)

If you want to test the script on your computer before deploying to GitHub, follow this guide.

---

## Prerequisites

- Python 3.8+ installed on your computer
- Canvas API Token (see SETUP_GUIDE.md Part 1)
- Gmail App Password (see SETUP_GUIDE.md Part 2)

---

## Setup for Local Testing

### 1. Download the Files

Download all the project files to a folder on your computer, for example:
```
~/canvas-tracker/
```

### 2. Install Python Dependencies

Open Terminal (Mac/Linux) or Command Prompt (Windows) and navigate to your folder:

```bash
cd ~/canvas-tracker
```

Install required packages:

```bash
pip install -r requirements.txt
```

### 3. Set Environment Variables

**On Mac/Linux:**

```bash
export CANVAS_API_TOKEN="your_canvas_token_here"
export GMAIL_ADDRESS="your_email@gmail.com"
export GMAIL_APP_PASSWORD="your_16_char_password"
```

**On Windows (Command Prompt):**

```cmd
set CANVAS_API_TOKEN=your_canvas_token_here
set GMAIL_ADDRESS=your_email@gmail.com
set GMAIL_APP_PASSWORD=your_16_char_password
```

**On Windows (PowerShell):**

```powershell
$env:CANVAS_API_TOKEN="your_canvas_token_here"
$env:GMAIL_ADDRESS="your_email@gmail.com"
$env:GMAIL_APP_PASSWORD="your_16_char_password"
```

### 4. (Optional) Select Which Courses to Monitor

Run the setup command to choose specific courses instead of monitoring all of them:

```bash
python canvas_tracker.py --setup
```

Follow the prompts to pick your courses. This creates `courses_config.json` — commit this file to your repo so GitHub Actions uses it. You can re-run `--setup` at any time to change your selection.

### 5. Run the Script

```bash
python canvas_tracker.py
```

### 6. Check Output

You should see structured log output like:

```
2026-02-02 14:30:00 [INFO] Starting Canvas file check at 2026-02-02 14:30:00
2026-02-02 14:30:01 [INFO] Found 5 active courses
2026-02-02 14:30:01 [INFO] Checking course: FIN3101 Corporate Finance
2026-02-02 14:30:02 [INFO] Found 2 new files in FIN3101 Corporate Finance
2026-02-02 14:30:05 [INFO] Email sent: NUS Canvas Updates: FIN3101 Corporate Finance
2026-02-02 14:30:05 [INFO] Checking course: EC3101 Microeconomic Analysis
2026-02-02 14:30:45 [INFO] Completed check at 2026-02-02 14:30:45 - New files found and emailed
2026-02-02 14:30:45 [INFO] Saved seen_files.json successfully
```

If errors occur, you'll also see WARNING/ERROR/CRITICAL level messages, and an error notification email will be sent to your Gmail.

---

## Using a .env File (Recommended for Local Testing)

Instead of setting environment variables each time, create a `.env` file:

### 1. Create `.env` file

In your project folder, create a file named `.env`:

```
CANVAS_API_TOKEN=your_canvas_token_here
GMAIL_ADDRESS=your_email@gmail.com
GMAIL_APP_PASSWORD=your_16_char_password
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs both `requests` and `python-dotenv`. The script already includes `load_dotenv()` at the top, so it will automatically read your `.env` file.

### 3. Add .env to .gitignore

**IMPORTANT:** Make sure `.env` is in your `.gitignore` file so you don't accidentally commit secrets!

The `.gitignore` file already includes `*.env`, so you're protected.

---

## Common Local Testing Issues

### Issue: "No module named 'requests'"
**Fix:** Run `pip install requests`

### Issue: "CANVAS_API_TOKEN not set"
**Fix:** Make sure you've exported the environment variables or created the `.env` file. The script will exit with code 1 if credentials are missing.

### Issue: "Authentication failed" (Gmail)
**Fix:**
- Verify your Gmail App Password is correct (16 characters)
- Ensure 2-Step Verification is enabled on your Google account
- Try regenerating the App Password

### Issue: "401 Unauthorized" (Canvas)
**Fix:**
- Verify your Canvas API token is correct
- Make sure you're using the NUS Canvas URL (https://canvas.nus.edu.sg)

### Issue: "No active courses found" warning
**Fix:**
- This means the Canvas API responded but returned zero courses
- Verify you still have active enrollments on Canvas
- Try regenerating your Canvas API token

### Issue: "No new files found" but you know there are new files
**Fix:**
- Check if files were uploaded within the last 24 hours
- Delete `seen_files.json` content (make it just `{}`) and run again
- Verify you have active enrollments in those courses

### Issue: Received an error notification email
**Fix:**
- Read the error details in the email body
- Check the log output for the full context (timestamps and log levels help pinpoint the issue)
- If an email failed to send for a course, those files will be retried on the next run automatically

---

## Scheduling on Your Local Computer

If you want to run this on your computer instead of GitHub Actions:

### Mac/Linux (using cron):

1. Open terminal and type:
```bash
crontab -e
```

2. Add this line (runs daily at 8 AM):
```
0 8 * * * cd /path/to/canvas-tracker && /usr/bin/python3 canvas_tracker.py
```

3. Save and exit

### Windows (using Task Scheduler):

1. Open Task Scheduler
2. Create Basic Task
3. Name: "Canvas File Tracker"
4. Trigger: Daily at 8:00 AM
5. Action: Start a program
   - Program: `python`
   - Arguments: `C:\path\to\canvas-tracker\canvas_tracker.py`
   - Start in: `C:\path\to\canvas-tracker`
6. Finish

**Note:** Your computer must be on and connected to the internet for scheduled tasks to run!

---

## Debugging Tips

### Log Levels

The script uses Python's `logging` module with structured output. All logs include timestamps and levels:

- **DEBUG**: Detailed info (e.g., "No new files in course X"). Shown by default.
- **INFO**: Normal operations (e.g., "Found 5 active courses", "Email sent").
- **WARNING**: Non-fatal issues (e.g., file download failed, no courses found).
- **ERROR**: Failures that affect specific courses (e.g., email send failed).
- **CRITICAL**: Failures that stop execution (e.g., Canvas API unreachable, missing credentials).

### Check seen_files.json

After running, open `seen_files.json` to see what's been tracked:

```json
{
  "12345": ["file_id_1", "file_id_2"],
  "67890": ["file_id_3"]
}
```

Each number is a course ID, and the array contains file IDs that have been emailed.

### Check courses_config.json

After running `--setup`, open `courses_config.json` to see which courses are configured:

```json
{
  "selected_course_ids": ["12345", "67890"],
  "selected_course_names": {
    "12345": "FIN3101 Corporate Finance",
    "67890": "EC3101 Microeconomic Analysis"
  },
  "last_updated": "2026-02-19 14:00:00"
}
```

If this file does not exist, the tracker monitors all active courses.

### Test Email Sending Only

Create a simple test script `test_email.py`:

```python
import smtplib
from email.mime.text import MIMEText

sender = "your_email@gmail.com"
password = "your_app_password"

msg = MIMEText("Test email from Canvas Tracker")
msg['Subject'] = "Test Email"
msg['From'] = sender
msg['To'] = sender

with smtplib.SMTP('smtp.gmail.com', 587) as server:
    server.starttls()
    server.login(sender, password)
    server.send_message(msg)

print("Email sent successfully!")
```

Run it to verify Gmail credentials work.

---

## Moving from Local to GitHub Actions

Once you've tested locally and everything works:

1. **Remove .env file** (or make sure it's in .gitignore)
2. Follow SETUP_GUIDE.md Part 3 to upload to GitHub
3. Add secrets to GitHub (not the .env file!)
4. If you ran `--setup`, commit `courses_config.json` to the repository
5. Enable GitHub Actions

The script works the same way - just runs in the cloud instead of your computer!

---

## Why Use GitHub Actions Instead of Local?

**Advantages of GitHub Actions:**
- ✅ Runs even when your computer is off
- ✅ No electricity cost
- ✅ Always connected to internet
- ✅ Free forever (for public/private repos)
- ✅ Reliable scheduling
- ✅ Easy to monitor (workflow logs)

**Advantages of Local:**
- ✅ Easier to debug
- ✅ Full control
- ✅ Faster testing iterations

**Best approach:** Test locally first, then deploy to GitHub Actions for production use!
