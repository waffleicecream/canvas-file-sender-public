# Canvas File Tracker

Automatically monitors your NUS Canvas courses for new file uploads and emails them to you daily.

## Features

- ✅ Tracks all active Canvas courses automatically
- ✅ Choose which courses to monitor with `--setup`
- ✅ Sends daily email digest of new files (last 24 hours)
- ✅ Downloads and attaches files to emails
- ✅ Splits large batches into multiple emails (Gmail 25MB limit)
- ✅ Groups files by course
- ✅ Runs automatically via GitHub Actions
- ✅ Completely free to use
- ✅ Error notification emails when something goes wrong
- ✅ Structured logging for easy debugging
- ✅ Safe state management — failed emails are retried next run

## Setup Instructions

### 1. Get Your Canvas API Token

1. Log in to [Canvas NUS](https://canvas.nus.edu.sg)
2. Click on **Account** (left sidebar) → **Settings**
3. Scroll down to **Approved Integrations**
4. Click **+ New Access Token**
5. Give it a purpose (e.g., "File Tracker")
6. Click **Generate Token**
7. **Copy the token immediately** (you won't see it again!)

### 2. Set Up Gmail App Password

1. Go to your [Google Account](https://myaccount.google.com/)
2. Click **Security** (left sidebar)
3. Under "How you sign in to Google", enable **2-Step Verification** (if not already enabled)
4. Go back to Security, scroll to **2-Step Verification**
5. Scroll down to **App passwords**
6. Click **App passwords**
7. In the "App name" field, type: `Canvas Tracker`
8. Click **Create**
9. **Copy the 16-character password** (no spaces)

### 3. Fork This Repository

1. Click the **Fork** button at the top right of this page
2. This creates your own copy of the repository

### 4. Add Secrets to GitHub

1. In your forked repository, go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** and add the following three secrets:

   **Secret 1:**
   - Name: `CANVAS_API_TOKEN`
   - Value: [Paste your Canvas API token from Step 1]

   **Secret 2:**
   - Name: `GMAIL_ADDRESS`
   - Value: [Your Gmail address, e.g., yourname@gmail.com]

   **Secret 3:**
   - Name: `GMAIL_APP_PASSWORD`
   - Value: [Your 16-character app password from Step 2]

### 5. Enable GitHub Actions

1. Go to the **Actions** tab in your repository
2. Click **"I understand my workflows, go ahead and enable them"**
3. The workflow will now run automatically every day at 8 AM SGT

### 6. Test It Manually (Optional)

1. Go to **Actions** tab
2. Click **"Daily Canvas File Check"** in the left sidebar
3. Click **"Run workflow"** dropdown → **"Run workflow"**
4. Wait ~1-2 minutes, then check your email!

## How It Works

1. **Daily Schedule**: Runs every day at 8 AM Singapore Time (configurable)
2. **Checks Canvas**: Fetches all active courses and their files
3. **Filters New Files**: Only processes files uploaded in the last 24 hours
4. **Downloads & Emails**: Downloads files and sends them grouped by course
5. **Tracks Progress**: Updates `seen_files.json` so files aren't sent twice
6. **Error Handling**: If anything fails, you receive an error notification email with details

## Error Handling & Logging

The tracker uses structured logging and handles errors gracefully:

- **Error notification emails**: If any errors occur during a run (API failures, email send failures, etc.), you receive an email with the error details.
- **Safe state updates**: If an email fails to send for a course, those files are NOT marked as seen — they will be retried on the next run.
- **Structured logs**: All output uses Python's `logging` module with levels (DEBUG, INFO, WARNING, ERROR, CRITICAL), visible in the GitHub Actions logs.
- **Exit codes**: Critical failures (Canvas API unreachable, missing credentials) cause the workflow step to fail, which is visible in the Actions tab. Non-critical errors (one course fails) still allow other courses to process.
- **Zero courses warning**: If Canvas returns no active courses (possible enrollment change or token issue), you receive a warning email.

## Course Selection

By default the tracker monitors all your active Canvas courses. You can narrow this down to specific courses using the interactive setup command:

```bash
python canvas_tracker.py --setup
```

This fetches your active courses and lets you pick which ones to monitor:

```
Available courses:
   1. FIN3101 Corporate Finance
   2. EC3101 Microeconomic Analysis
   3. CS2103T Software Engineering
   ...

Enter course numbers to monitor (comma-separated), or 'all' for all courses:
> 1,3

Selected courses:
  - FIN3101 Corporate Finance
  - CS2103T Software Engineering

Confirm? [y/n]: y
Saved. Commit courses_config.json to apply to GitHub Actions.
```

Your selection is saved to `courses_config.json`. **Commit this file** and push it to your repository — GitHub Actions will then only monitor those courses on every subsequent run.

To change your selection at any time, just run `--setup` again locally and commit the updated file.

> **No config file?** The tracker falls back to monitoring all courses — the same behaviour as before.

## Customization

### Change the Schedule Time

Edit `.github/workflows/daily_check.yml`:

```yaml
on:
  schedule:
    # Change this cron expression
    # Format: 'minute hour * * *'
    # Examples:
    # '0 0 * * *'  = Midnight UTC (8 AM SGT)
    # '0 12 * * *' = Noon UTC (8 PM SGT)
    # '30 2 * * *' = 2:30 AM UTC (10:30 AM SGT)
    - cron: '0 0 * * *'
```

Use [Crontab Guru](https://crontab.guru/) to help create cron expressions.

### Change Email Size Limit

Edit `canvas_tracker.py`:

```python
MAX_EMAIL_SIZE_MB = 20  # Change this value (max 25 for Gmail)
```

## File Structure

```
canvas-file-tracker/
├── canvas_tracker.py          # Main Python script
├── seen_files.json            # Tracks which files have been emailed
├── courses_config.json        # Selected courses to monitor (created by --setup)
├── requirements.txt           # Python dependencies
├── .github/
│   └── workflows/
│       └── daily_check.yml    # GitHub Actions workflow
└── README.md                  # This file
```

## Troubleshooting

### Received an error notification email?

- Check the error details in the email body for what went wrong
- Check the **Actions** tab for full structured logs with timestamps
- Critical errors (exit code 1) will show the workflow step as failed (red X)

### No emails received?

1. Check **Actions** tab for errors
2. Verify all three secrets are set correctly
3. Check your Gmail spam folder
4. Ensure you used the App Password, not your regular Gmail password

### "Authentication failed" error?

- Your Gmail App Password may be incorrect
- Make sure 2-Step Verification is enabled on your Google account
- Regenerate the App Password and update the secret

### "401 Unauthorized" from Canvas?

- Your Canvas API token may have expired or is incorrect
- Generate a new token and update the `CANVAS_API_TOKEN` secret

### "No active courses found" warning?

- This means Canvas API responded successfully but returned zero courses
- Your enrollment may have changed, or the API token may have lost access
- Verify you still have active courses on Canvas
- Try regenerating your Canvas API token

### Files missing from email?

- Check if the file was uploaded more than 24 hours ago
- The first run only tracks files from that point forward

### Workflow shows red X (failed)?

- This indicates a critical error — check the Actions logs
- Common causes: Canvas API unreachable, invalid credentials, or failed to save state
- You should also receive an error notification email with details

### Want to reset and re-send all files?

1. Delete the contents of `seen_files.json` (make it just `{}`)
2. Commit and push the change
3. The next run will treat all recent files as "new"

## Privacy & Security

- Your Canvas token and Gmail password are stored as **encrypted GitHub Secrets**
- They are never visible in code or logs
- You can revoke access anytime:
  - Canvas: Delete the token from Account → Settings
  - Gmail: Delete the app password from Google Account → Security

## Stopping the Tracker

To stop receiving emails:

1. Go to **Actions** tab
2. Click **"Daily Canvas File Check"**
3. Click the **"..."** menu → **"Disable workflow"**

Or simply delete your forked repository.

## Support

If you encounter issues:
1. Check the **Actions** tab for error logs
2. Verify all secrets are correctly set
3. Ensure your Canvas token and Gmail app password are valid

## License

Free to use and modify for personal use.
