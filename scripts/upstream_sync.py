#!/usr/bin/env python3
"""
Upstream sync automation script.

Fetch upstream changes, merge into fork main and dev branches,
and notify via Telegram on conflicts.
"""
import subprocess
import sys
import os
import datetime
import logging

import requests

# Configuration
HERMES_HOME = os.path.expanduser(os.getenv("HERMES_HOME", "~/Work/Explore/hermes"))
REPO_DIR = os.path.join(HERMES_HOME, "hermes-agent")
UPSTREAM_REMOTE = "upstream"
ORIGIN_REMOTE = "origin"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # e.g. "-1003800695683"
DEBUG = False


def run(cmd, cwd=REPO_DIR, check=True):
    logging.debug(f"Running: {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if DEBUG:
        logging.debug(proc.stdout)
        logging.debug(proc.stderr)
    if check and proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd, output=proc.stdout, stderr=proc.stderr)
    return proc


def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("Telegram credentials not set; skipping alert")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    resp = requests.post(url, json=payload)
    resp.raise_for_status()


def main():
    global DEBUG
    parser = subprocess.Popen  # placeholder for argparse import below
    import argparse
    p = argparse.ArgumentParser(description="Automate upstream sync")
    p.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = p.parse_args()
    if args.debug:
        DEBUG = True
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    # Step 1: Fetch upstream
    run(["git", "fetch", UPSTREAM_REMOTE, "main"])

    # Step 2: Sync fork/main (ensure local main tracks origin/main)
    try:
        run(["git", "fetch", ORIGIN_REMOTE, "main"])
        run(["git", "checkout", "-B", "main", f"{ORIGIN_REMOTE}/main"])
        run(["git", "merge", "--no-ff", f"{UPSTREAM_REMOTE}/main"])
        run(["git", "push", ORIGIN_REMOTE, "main"])
    except subprocess.CalledProcessError:
        run(["git", "merge", "--abort"], check=False)
        branch = f"upstream-sync-conflict-{timestamp}"
        run(["git", "checkout", "-b", branch])
        send_telegram(f"⚠️ Upstream merge conflict on main. Resolve branch: {branch}")
        run(["gh", "pr", "create", "--title", f"Upstream Merge Conflict {timestamp}", "--body", "Automatic conflict PR", "--head", branch, "--base", "main"])
        sys.exit(1)

    # Step 3: Sync dev
    try:
        run(["git", "checkout", "dev"])
        run(["git", "merge", "--no-ff", "main"])
        run(["git", "push", ORIGIN_REMOTE, "dev"])
    except subprocess.CalledProcessError:
        run(["git", "merge", "--abort"], check=False)
        branch = f"dev-sync-conflict-{timestamp}"
        run(["git", "checkout", "-b", branch])
        send_telegram(f"⚠️ Merge conflict on dev. Resolve branch: {branch}")
        run(["gh", "pr", "create", "--title", f"Dev Merge Conflict {timestamp}", "--body", "Automatic conflict PR", "--head", branch, "--base", "dev"])
        sys.exit(1)

    # Step 4: Merge dev → release (auto-triggers release workflow)
    try:
        run(["git", "checkout", "release"])
        run(["git", "merge", "--no-ff", "dev"])
        run(["git", "push", ORIGIN_REMOTE, "release"])
        send_telegram(f"🚀 Merged dev → release. Release workflow triggered.")
    except subprocess.CalledProcessError:
        run(["git", "merge", "--abort"], check=False)
        send_telegram(f"⚠️ Merge conflict on release. Manual resolution needed.")
        sys.exit(1)

    # Log successful main → dev sync to markdown log
    log_dir = os.path.join(HERMES_HOME, "logs", "git-merge")
    os.makedirs(log_dir, exist_ok=True)
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"001-{date_str}-upstream-main-to-dev.md")
    with open(log_file, "w") as f:
        f.write(f"# Upstream main → dev Sync - {date_str}\n\n")
        f.write(f"- **Timestamp:** {datetime.datetime.utcnow().isoformat()}Z\n")
        main_sha = run(["git", "rev-parse", "main"]).stdout.strip()
        dev_sha = run(["git", "rev-parse", "dev"]).stdout.strip()
        f.write(f"- **Main SHA:** {main_sha}\n")
        f.write(f"- **Dev SHA:** {dev_sha}\n")
    # Send Telegram alert for success
    try:
        send_telegram(f"✅ Upstream sync successful. Main SHA: {main_sha}, Dev SHA: {dev_sha}")
    except Exception as e:
        logging.warning(f"Failed to send Telegram success alert: {e}")
    logging.info("\u2705 Upstream sync completed successfully.")


if __name__ == "__main__":
    main()
