# Setup Guide with Visual References

This guide walks you through each step with descriptions of what you'll see.

---

## Part 1: Canvas API Token

### Step 1.1: Login to Canvas
- Go to: https://canvas.nus.edu.sg
- Login with your NUS credentials

### Step 1.2: Navigate to Settings
- Look at the left sidebar
- Click on **"Account"** 
- Click on **"Settings"**

### Step 1.3: Find Approved Integrations
- Scroll down the page
- Look for a section called **"Approved Integrations"**
- You'll see a button **"+ New Access Token"**

### Step 1.4: Generate Token
- Click **"+ New Access Token"**
- A popup will appear asking for "Purpose"
- Type: `File Tracker` (or any name you like)
- Click **"Generate Token"**

### Step 1.5: COPY THE TOKEN IMMEDIATELY
- A long string will appear (looks like: `1234~abcdef...`)
- **COPY IT NOW** - You won't see it again!
- Paste it somewhere safe temporarily (you'll use it in Part 3)

---

## Part 2: Gmail App Password

### Step 2.1: Go to Google Account Security
- Go to: https://myaccount.google.com/security
- Make sure you're logged into the Gmail you want to use

### Step 2.2: Enable 2-Step Verification (if not already on)
- Look for **"2-Step Verification"** section
- If it says "Off", click it and follow the setup
- If it says "On", you're good - continue to next step

### Step 2.3: Access App Passwords
- Go back to Security page
- Click on **"2-Step Verification"**
- Scroll down to find **"App passwords"**
- Click on it

### Step 2.4: Create App Password
- In the "App name" field, type: `Canvas Tracker`
- Click **"Create"**

### Step 2.5: COPY THE PASSWORD
- You'll see a 16-character password (looks like: `abcd efgh ijkl mnop`)
- **COPY IT** (you can copy with or without spaces - both work)
- Paste it somewhere safe temporarily
- Click **"Done"**

---

## Part 3: GitHub Setup

### Step 3.1: Create GitHub Account (if you don't have one)
- Go to: https://github.com/signup
- Create a free account
- Verify your email

### Step 3.2: Upload the Project Files
- Login to GitHub
- Click the **"+"** icon (top right) → **"New repository"**
- Repository name: `canvas-file-tracker` (or any name)
- Choose **"Public"** or **"Private"** (your choice)
- Check **"Add a README file"**
- Click **"Create repository"**

### Step 3.3: Upload All Files
- In your new repository, click **"Add file"** → **"Upload files"**
- Drag and drop ALL these files from the download:
  - `canvas_tracker.py`
  - `seen_files.json`
  - `requirements.txt`
  - `README.md`
  - `QUICK_START.md`
  - `.gitignore`
  - `.github/` folder (with workflows inside)
- Click **"Commit changes"**
- If you have already run `--setup` locally, also upload `courses_config.json`

### Step 3.4: Add Secrets
- In your repository, click **"Settings"** tab (top menu)
- In the left sidebar, click **"Secrets and variables"** → **"Actions"**
- Click **"New repository secret"** button

**Add Secret #1:**
- Name: `CANVAS_API_TOKEN`
- Secret: [Paste your Canvas token from Part 1]
- Click **"Add secret"**

**Add Secret #2:**
- Name: `GMAIL_ADDRESS`
- Secret: [Type your Gmail address, e.g., joel@gmail.com]
- Click **"Add secret"**

**Add Secret #3:**
- Name: `GMAIL_APP_PASSWORD`
- Secret: [Paste your 16-character password from Part 2]
- Click **"Add secret"**

You should now see 3 secrets listed (you won't see their values - that's normal!)

---

## Part 4: (Optional) Choose Which Courses to Monitor

By default the tracker monitors all your active Canvas courses. To limit it to specific ones, run this command locally before pushing to GitHub:

```bash
python canvas_tracker.py --setup
```

You will see a numbered list of your active courses:

```
Available courses:
   1. FIN3101 Corporate Finance
   2. EC3101 Microeconomic Analysis
   3. CS2103T Software Engineering
   ...

Enter course numbers to monitor (comma-separated), or 'all' for all courses:
> 1,3
```

After confirming, a `courses_config.json` file is created. **Commit and push this file** to your GitHub repository so Actions uses it.

To change your selection later, run `--setup` again locally and commit the updated file.

---

## Part 5: Enable and Test

### Step 5.1: Enable Actions
- Click the **"Actions"** tab (top menu)
- If you see a green button saying **"I understand my workflows, go ahead and enable them"**, click it
- You should now see "Daily Canvas File Check" workflow

### Step 5.2: Run Your First Test
- Click on **"Daily Canvas File Check"** (in the left sidebar)
- Click the **"Run workflow"** dropdown button (right side)
- Click the green **"Run workflow"** button
- Wait about 5-10 seconds, then refresh the page

### Step 5.3: Check the Run
- You'll see a yellow dot (running) then a green checkmark (success) or red X (failed)
- If green ✅ - Check your Gmail! You should have an email
- If red ❌ - Click on it to see structured error logs. You should also receive an error notification email with details

### Step 5.4: Verify Email
- Check your Gmail inbox
- Subject should be: "NUS Canvas Updates: [Course Name]"
- Files should be attached
- If not in inbox, check Spam folder

---

## Part 6: Understanding Automatic Runs

### When Does It Run?
- Automatically every day at **8 AM Singapore Time**
- No need to do anything - it just runs

### Where to See Run History?
- Go to **Actions** tab in your GitHub repo
- You'll see a list of all runs (successful and failed)
- Click any run to see details/logs

### How to Change the Time?
- In your repository, click on `.github/workflows/daily_check.yml`
- Click the pencil icon ✏️ (edit)
- Find the line: `- cron: '0 0 * * *'`
- Change it:
  - `'0 0 * * *'` = 8 AM SGT (Midnight UTC)
  - `'0 12 * * *'` = 8 PM SGT (Noon UTC)
  - `'30 2 * * *'` = 10:30 AM SGT
- Click **"Commit changes"**

---

## Troubleshooting

### Received an Error Notification Email
**What it means:** Something went wrong during a run. The email contains error details.
**What to do:**
1. Read the error details in the email
2. Check the **Actions** tab for full structured logs with timestamps
3. See below for common errors and fixes

### Error: "Authentication failed"
**Problem:** Gmail credentials wrong
**Fix:**
1. Go to GitHub repo → Settings → Secrets → Actions
2. Delete `GMAIL_APP_PASSWORD` secret
3. Go back to Gmail and generate a NEW app password
4. Add the new password as a secret

### Error: "401 Unauthorized"
**Problem:** Canvas token wrong/expired
**Fix:**
1. Go to Canvas → Account → Settings
2. Generate a NEW access token
3. Update `CANVAS_API_TOKEN` secret in GitHub

### Warning: "No active courses found"
**Problem:** Canvas API returned zero courses — enrollment may have changed or API token lost access
**Fix:**
1. Verify you still have active courses on Canvas
2. Try regenerating your Canvas API token
3. Update `CANVAS_API_TOKEN` secret in GitHub

### Workflow Shows Red X (Failed)
**What it means:** A critical error occurred (Canvas API unreachable, missing credentials, or state save failure)
**What to do:**
1. You should receive an error notification email with details
2. Click the failed run in the Actions tab to see full logs
3. Note: when the workflow fails, `seen_files.json` is NOT updated — files will be retried next run

### No Email Received (but workflow shows green ✅)
**Check:**
1. Gmail Spam folder
2. Look at workflow logs - it might say "No new files"
3. Files might have been uploaded >24 hours ago

### Want to Change Which Courses Are Monitored?
1. Run `python canvas_tracker.py --setup` on your local machine
2. Select the courses you want
3. Commit the updated `courses_config.json` to your repository
4. GitHub Actions will use the new selection on the next run

### Want to Re-send All Files?
1. In GitHub repo, click `seen_files.json`
2. Click pencil icon ✏️ (edit)
3. Delete everything and type just: `{}`
4. Commit changes
5. Next run will treat all recent files as "new"

---

## Security & Privacy

✅ **All credentials are encrypted** - GitHub Secrets are encrypted and never shown in logs
✅ **Only you have access** - Your forked repo is yours
✅ **Revoke anytime** - Delete tokens/passwords from Canvas/Gmail settings
✅ **No data stored elsewhere** - Everything runs in GitHub's secure environment

---

## Need Help?

1. Check the **Actions** tab for error messages
2. Read the error logs carefully
3. Verify all 3 secrets are correctly entered
4. Make sure Canvas token hasn't expired
5. Ensure Gmail 2-Step Verification is ON

---

**Congratulations! 🎉** 

Your Canvas File Tracker is now set up and will automatically email you new files every day!
