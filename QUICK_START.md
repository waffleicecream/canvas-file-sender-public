# Quick Start Guide - Canvas File Tracker

## Prerequisites Checklist

- [ ] GitHub account (free)
- [ ] Gmail account
- [ ] NUS Canvas account

## 5-Minute Setup

### Step 1: Get Canvas Token (2 min)
1. Login to https://canvas.nus.edu.sg
2. Account → Settings
3. Scroll to "Approved Integrations"
4. Click "+ New Access Token"
5. **Copy the token** (save it somewhere temporarily)

### Step 2: Get Gmail App Password (2 min)
1. Go to https://myaccount.google.com/security
2. Enable "2-Step Verification" (if not already on)
3. Go to "App passwords" (search for it)
4. Create app password named "Canvas Tracker"
5. **Copy the 16-character password** (save it somewhere temporarily)

### Step 3: Set Up GitHub (1 min)
1. Fork this repository (click Fork button)
2. Go to Settings → Secrets and variables → Actions
3. Create 3 secrets:
   - `CANVAS_API_TOKEN` = [your Canvas token]
   - `GMAIL_ADDRESS` = [your Gmail, e.g., joel@gmail.com]
   - `GMAIL_APP_PASSWORD` = [your 16-char password]

### Step 4: (Optional) Choose Which Courses to Monitor
Run this locally to pick specific courses instead of all of them:
```bash
python canvas_tracker.py --setup
```
Follow the prompts, then commit the generated `courses_config.json` to your repo. Skip this step to monitor all courses.

### Step 5: Enable & Test
1. Go to Actions tab
2. Click "I understand my workflows, go ahead and enable them"
3. Click "Daily Canvas File Check" → "Run workflow"
4. Wait 2 minutes, check your email! ✅

## What Happens Next?

- Runs automatically **every day at 8 AM SGT**
- Emails you files uploaded in the **last 24 hours**
- Files are **grouped by course** (only selected courses if configured)
- Large batches **split into multiple emails**
- If any errors occur, you receive an **error notification email**
- Failed emails are **retried on the next run** automatically

## Customizing Run Time

Edit `.github/workflows/daily_check.yml` and change:

```yaml
- cron: '0 0 * * *'  # Midnight UTC = 8 AM SGT
```

**Common times:**
- `0 0 * * *` = 8 AM SGT (default)
- `0 12 * * *` = 8 PM SGT
- `30 2 * * *` = 10:30 AM SGT

Use https://crontab.guru/ to create custom schedules.

## Emergency Stop

**Disable workflow:**
Actions → Daily Canvas File Check → "..." → Disable workflow

**Or delete the repo entirely**

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Error notification email received | Check the error details in the email; see Actions tab for full logs |
| No email received | Check Actions tab for errors; verify secrets are correct |
| "Authentication failed" | Regenerate Gmail app password; ensure 2-Step Verification is on |
| "401 Unauthorized" | Canvas token expired; generate a new one |
| "No active courses found" | Enrollment may have changed; verify courses on Canvas; regenerate API token |
| Workflow shows red X | Critical error occurred; check Actions logs and error notification email |
| Want to change monitored courses | Run `python canvas_tracker.py --setup` locally and commit `courses_config.json` |
| Want to re-send all files | Edit `seen_files.json` to `{}` and commit |

## Security Notes

✅ All credentials stored as encrypted GitHub Secrets
✅ Never visible in code or logs
✅ Revocable anytime from Canvas/Gmail settings
✅ Only you have access to your forked repo

---

**That's it! You're all set.** The tracker will now run automatically every day.
