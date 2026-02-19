#!/usr/bin/env python3
"""
Canvas File Tracker
Monitors NUS Canvas courses for new files and emails them daily.
"""

import os
import json
import argparse
import logging
import sys
import traceback
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("canvas_tracker")

# Configuration - Set these as environment variables or GitHub Secrets
CANVAS_URL = "https://canvas.nus.edu.sg"
CANVAS_API_TOKEN = os.environ.get("CANVAS_API_TOKEN", "")
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

# Constants
SEEN_FILES_PATH = "seen_files.json"
COURSES_CONFIG_PATH = "courses_config.json"
MAX_EMAIL_SIZE_MB = 20  # Keep under Gmail's 25MB limit with buffer
HEADERS = {"Authorization": f"Bearer {CANVAS_API_TOKEN}"}


def load_seen_files():
    """Load the record of previously seen files."""
    if os.path.exists(SEEN_FILES_PATH):
        try:
            with open(SEEN_FILES_PATH, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error("seen_files.json is corrupted: %s", e)
            return {}
        except OSError as e:
            logger.error("Failed to read seen_files.json: %s", e)
            return {}
    return {}


def save_seen_files(seen_files):
    """Save the record of seen files. Raises OSError on failure."""
    temp_path = SEEN_FILES_PATH + ".tmp"
    with open(temp_path, 'w') as f:
        json.dump(seen_files, f, indent=2)
    shutil.move(temp_path, SEEN_FILES_PATH)
    logger.info("Saved seen_files.json successfully")


def load_courses_config():
    """Load selected course IDs from config. Returns None if no config exists (monitor all)."""
    if not os.path.exists(COURSES_CONFIG_PATH):
        return None
    try:
        with open(COURSES_CONFIG_PATH, 'r') as f:
            data = json.load(f)
        return data.get("selected_course_ids")
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Could not read courses_config.json: %s - monitoring all courses", e)
        return None


def save_courses_config(course_ids, courses):
    """Save selected course IDs to config file."""
    id_to_name = {str(c['id']): c['name'] for c in courses}
    data = {
        "selected_course_ids": course_ids,
        "selected_course_names": {cid: id_to_name.get(cid, "Unknown") for cid in course_ids},
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    temp_path = COURSES_CONFIG_PATH + ".tmp"
    with open(temp_path, 'w') as f:
        json.dump(data, f, indent=2)
    shutil.move(temp_path, COURSES_CONFIG_PATH)
    logger.info("Saved courses_config.json with %d selected courses", len(course_ids))


def get_active_courses():
    """Fetch all active courses from Canvas. Raises on API failure."""
    url = f"{CANVAS_URL}/api/v1/courses"
    params = {
        "enrollment_state": "active",
        "per_page": 100
    }

    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    courses = response.json()

    # Filter out courses without a name (sometimes API returns incomplete data)
    return [c for c in courses if c.get('name')]


def get_course_files(course_id):
    """Fetch all files from a specific course. Raises on API failure."""
    url = f"{CANVAS_URL}/api/v1/courses/{course_id}/files"
    params = {"per_page": 100}
    all_files = []

    while url:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        all_files.extend(response.json())

        # Handle pagination
        if 'next' in response.links:
            url = response.links['next']['url']
            params = {}  # URL already contains params
        else:
            url = None

    return all_files


def download_file(file_url, file_name, temp_dir):
    """Download a file from Canvas."""
    try:
        response = requests.get(file_url, headers=HEADERS, stream=True)
        response.raise_for_status()

        file_path = os.path.join(temp_dir, file_name)
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return file_path
    except requests.exceptions.RequestException as e:
        logger.warning("Error downloading file %s: %s", file_name, e)
        return None


def get_file_size_mb(file_path):
    """Get file size in MB."""
    return os.path.getsize(file_path) / (1024 * 1024)


def send_email_with_attachments(course_name, files, part_num=None, total_parts=None):
    """Send an email with file attachments."""
    msg = MIMEMultipart()
    msg['From'] = GMAIL_ADDRESS
    msg['To'] = GMAIL_ADDRESS

    # Create subject line
    if part_num and total_parts:
        subject = f"NUS Canvas Updates: {course_name} - Part {part_num} of {total_parts}"
    else:
        subject = f"NUS Canvas Updates: {course_name}"

    msg['Subject'] = subject

    # Email body
    body = f"New files uploaded to {course_name}:\n\n"
    for file_info in files:
        body += f"- {file_info['display_name']}\n"
        body += f"  Uploaded: {file_info['created_at']}\n\n"

    msg.attach(MIMEText(body, 'plain'))

    # Attach files
    for file_info in files:
        if file_info['local_path'] and os.path.exists(file_info['local_path']):
            try:
                with open(file_info['local_path'], 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {file_info["display_name"]}'
                    )
                    msg.attach(part)
            except Exception as e:
                logger.error("Error attaching file %s: %s", file_info['display_name'], e)

    # Send email
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        logger.info("Email sent: %s", subject)
        return True
    except Exception as e:
        logger.error("Error sending email: %s", e)
        return False


def send_error_email(error_summary):
    """Send an error notification email with details of failures."""
    msg = MIMEMultipart()
    msg['From'] = GMAIL_ADDRESS
    msg['To'] = GMAIL_ADDRESS
    msg['Subject'] = "Canvas File Tracker - Error Report"

    body = (
        f"The Canvas File Tracker encountered errors during execution "
        f"at {datetime.now()}.\n\n"
        f"Error Details:\n"
        f"{'=' * 50}\n"
        f"{error_summary}\n"
    )
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        logger.info("Error notification email sent successfully")
    except Exception as e:
        logger.error("Failed to send error notification email: %s", e)


def send_no_updates_email(num_courses):
    """Send a summary email when no new files were found."""
    msg = MIMEMultipart()
    msg['From'] = GMAIL_ADDRESS
    msg['To'] = GMAIL_ADDRESS
    msg['Subject'] = "NUS Canvas Updates: No new files today"

    body = (
        f"No new files were found across {num_courses} active courses.\n\n"
        f"Checked at: {datetime.now()}\n"
    )
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        logger.info("No-updates summary email sent")
    except Exception as e:
        logger.error("Failed to send no-updates summary email: %s", e)


def split_files_by_size(files_info, max_size_mb):
    """Split files into batches that don't exceed max size."""
    batches = []
    current_batch = []
    current_size = 0

    for file_info in files_info:
        file_size = get_file_size_mb(file_info['local_path']) if file_info['local_path'] else 0

        if current_size + file_size > max_size_mb and current_batch:
            # Start new batch
            batches.append(current_batch)
            current_batch = [file_info]
            current_size = file_size
        else:
            current_batch.append(file_info)
            current_size += file_size

    if current_batch:
        batches.append(current_batch)

    return batches


def run_setup(courses):
    """Interactively select which courses to monitor and save the config."""
    print("\nAvailable courses:")
    for i, course in enumerate(courses, 1):
        print(f"  {i:2}. {course['name']}")

    print("\nEnter course numbers to monitor (comma-separated), or 'all' for all courses:")

    while True:
        raw = input("> ").strip()
        if not raw:
            print("Please enter at least one course number or 'all'.")
            continue

        if raw.lower() == "all":
            selected = courses
            break

        try:
            indices = [int(x.strip()) for x in raw.split(",")]
            if any(i < 1 or i > len(courses) for i in indices):
                print(f"Please enter numbers between 1 and {len(courses)}.")
                continue
            selected = [courses[i - 1] for i in indices]
            break
        except ValueError:
            print("Invalid input. Enter numbers separated by commas, or 'all'.")

    print("\nSelected courses:")
    for course in selected:
        print(f"  - {course['name']}")

    confirm = input("\nConfirm? [y/n]: ").strip().lower()
    if confirm != "y":
        print("Setup cancelled.")
        return

    course_ids = [str(c['id']) for c in selected]
    save_courses_config(course_ids, courses)
    print(f"\nSaved. Commit {COURSES_CONFIG_PATH} to apply to GitHub Actions.")


def process_new_files(selected_ids=None):
    """Main function to check for new files and send emails."""
    logger.info("Starting Canvas file check at %s", datetime.now())

    # Load seen files
    seen_files = load_seen_files()
    errors = []
    has_critical_error = False

    # Get active courses
    try:
        courses = get_active_courses()
    except requests.exceptions.RequestException as e:
        logger.critical("Cannot reach Canvas API: %s", e)
        errors.append(f"CRITICAL - Cannot reach Canvas API:\n{traceback.format_exc()}")
        return errors, True

    if not courses:
        logger.warning("No active courses found - enrollment may have changed or API token lost access")
        errors.append("WARNING - Canvas API returned zero active courses. This may indicate enrollment changes or API token issues.")
        return errors, False

    logger.info("Found %d active courses", len(courses))

    # Filter to selected courses if a config exists
    if selected_ids is not None:
        courses = [c for c in courses if str(c['id']) in selected_ids]
        logger.info("Filtered to %d configured courses", len(courses))

    # Track if any new files were found
    new_files_found = False
    successfully_seen = {}  # course_id -> [file_ids] to mark as seen ONLY on success

    # Process each course
    for course in courses:
        course_id = str(course['id'])
        course_name = course['name']
        logger.info("Checking course: %s", course_name)

        # Initialize seen files for this course if not exists
        if course_id not in seen_files:
            seen_files[course_id] = []

        # Get all files from course
        try:
            files = get_course_files(course_id)
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 403:
                logger.debug("Skipping course %s - file access forbidden (403)", course_name)
                continue
            logger.error("Failed to fetch files for course %s: %s", course_name, e)
            errors.append(f"Failed to fetch files for '{course_name}':\n{traceback.format_exc()}")
            continue
        except requests.exceptions.RequestException as e:
            logger.error("Failed to fetch files for course %s: %s", course_name, e)
            errors.append(f"Failed to fetch files for '{course_name}':\n{traceback.format_exc()}")
            continue

        # Filter for files uploaded in last 24 hours
        cutoff_time = datetime.now() - timedelta(hours=24)
        new_files = []

        for file in files:
            file_id = str(file['id'])

            # Skip if we've already seen this file
            if file_id in seen_files[course_id]:
                continue

            # Parse upload time
            try:
                created_at = datetime.strptime(file['created_at'], "%Y-%m-%dT%H:%M:%SZ")
                if created_at >= cutoff_time:
                    new_files.append(file)
            except (ValueError, KeyError):
                # If we can't parse the date, include it to be safe
                new_files.append(file)

        if not new_files:
            logger.debug("No new files in %s", course_name)
            continue

        logger.info("Found %d new files in %s", len(new_files), course_name)
        new_files_found = True

        # Create temporary directory for downloads
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download files and prepare info
            files_info = []
            for file in new_files:
                file_path = download_file(file['url'], file['display_name'], temp_dir)
                files_info.append({
                    'id': str(file['id']),
                    'display_name': file['display_name'],
                    'created_at': file.get('created_at', 'Unknown'),
                    'local_path': file_path
                })

            # Split into batches if needed
            batches = split_files_by_size(files_info, MAX_EMAIL_SIZE_MB)

            # Send emails
            total_parts = len(batches)
            all_emails_sent = True

            for idx, batch in enumerate(batches, 1):
                if total_parts > 1:
                    success = send_email_with_attachments(course_name, batch, idx, total_parts)
                else:
                    success = send_email_with_attachments(course_name, batch)

                if not success:
                    all_emails_sent = False
                    errors.append(
                        f"Failed to send email for '{course_name}' "
                        f"(batch {idx}/{total_parts})"
                    )

            # ONLY mark files as seen if ALL emails for this course succeeded
            if all_emails_sent:
                if course_id not in successfully_seen:
                    successfully_seen[course_id] = []
                for file_info in files_info:
                    successfully_seen[course_id].append(file_info['id'])
            else:
                logger.warning(
                    "Not marking files as seen for %s due to email failures",
                    course_name
                )

    # Apply successful marks to seen_files
    for course_id, file_ids in successfully_seen.items():
        seen_files[course_id].extend(file_ids)

    # Save seen files
    try:
        save_seen_files(seen_files)
    except OSError:
        errors.append(f"Failed to save seen_files.json:\n{traceback.format_exc()}")
        has_critical_error = True

    if new_files_found:
        logger.info("Completed check at %s - New files found and emailed", datetime.now())
    else:
        logger.info("Completed check at %s - No new files found", datetime.now())
        send_no_updates_email(len(courses))

    return errors, has_critical_error


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(description="Canvas File Tracker")
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Interactively select which courses to monitor"
    )
    args = parser.parse_args()

    # Validate configuration
    if not CANVAS_API_TOKEN:
        logger.critical("CANVAS_API_TOKEN not set")
        sys.exit(1)

    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        logger.critical("Gmail credentials not set")
        sys.exit(1)

    # Setup mode: interactive course selection
    if args.setup:
        try:
            courses = get_active_courses()
        except requests.exceptions.RequestException as e:
            logger.critical("Cannot reach Canvas API: %s", e)
            sys.exit(1)
        if not courses:
            logger.warning("No active courses found on Canvas")
            sys.exit(1)
        run_setup(courses)
        return

    # Normal run: load course config and process
    selected_ids = load_courses_config()
    if selected_ids is None:
        logger.info("No courses_config.json found - monitoring all courses (run --setup to configure)")
    else:
        logger.info("Monitoring %d configured courses", len(selected_ids))

    try:
        errors, has_critical_error = process_new_files(selected_ids)
    except Exception:
        logger.critical("Unhandled exception", exc_info=True)
        error_summary = f"Unhandled exception:\n{traceback.format_exc()}"
        send_error_email(error_summary)
        sys.exit(1)

    # Send error summary email if any errors occurred
    if errors:
        error_summary = "\n\n".join(errors)
        logger.warning("Errors occurred during execution:\n%s", error_summary)
        send_error_email(error_summary)

    if has_critical_error:
        sys.exit(1)


if __name__ == "__main__":
    main()
