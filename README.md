# Google Review Automation 🤖⭐

An automated Google Maps review bot that uses local review templates and **undetected browser automation** (SeleniumBase) to post reviews from multiple Google accounts to any Google Maps business listing — managed through a simple Flask web dashboard.

---

## Features

- **Local Review Templates** — Uses selectable Random, Baik, and Buruk templates without an AI API
- **Multi-Account Support** — Manage a pool of Google accounts, each with its own persistent Chrome profile to maintain login sessions
- **Per-Business Configuration** — Set custom star rating distributions, business descriptions, and review styles per business
- **Background Worker** — Standalone `worker.py` polls the database and processes review jobs independently from the web app
- **Web Dashboard** — Password-protected Flask UI to add businesses, manage email accounts, queue review jobs, and track status
- **Proxy Support** — Route all browser traffic through a configurable proxy

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Web App | Flask |
| Browser Automation | SeleniumBase (undetected Chrome) |
| Review Text | Local templates (no AI API) |
| Database | SQLite (WAL mode) |
| Auth | Session-based with hashed password |

---

## Project Structure

```
.
├── app.py          # Flask web dashboard (auth, business/email management, job queuing)
├── bot.py          # Core automation: review generation + Selenium posting logic
├── db.py           # SQLite database layer
├── worker.py       # Background scheduler that processes pending review jobs
├── requirements.txt
├── chrome_profiles/  # Persistent Chrome profiles per Google account
├── templates/
│   ├── login.html
│   ├── dashboard.html
│   └── business.html
└── .env            # Environment variables (see below)
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file in the project root:

```env
SECRET_KEY=your_flask_secret_key
APP_PASSWORD=your_dashboard_password
PROXY=http://user:pass@host:port   # optional
```

### 3. Initialize the database

The database is auto-initialized on first run.

### 4. Run the web app

```bash
python app.py
```

Access the dashboard at `http://localhost:5000`.

### 5. Run the background worker

In a separate terminal:

```bash
python worker.py
```

The worker polls the database every 60 seconds and processes pending review jobs.

---

## How It Works

### Safe parallel Chromium dry-run

The project includes `dry_run_workers.py` for testing multiple isolated Chromium
instances without logging in or submitting public reviews. The worker limit is
configurable and each worker reports `Starting`, `Running`, `Completed`,
`Failed`, or `Stopped`, including runtime and active-worker count, before
cleaning its temporary profile.

```bash
DISPLAY=:99 .venv/bin/python dry_run_workers.py --workers 3 --duration 5 --delay 10 about:blank about:blank about:blank
```

Dry-run task waves start immediately by default. An optional fixed delay can be
enabled with `--delay`; when enabled, the worker emits a real countdown. This
setting does not change the production review path.

The production review path remains sequential and is intentionally not
parallelized for public posting.

### Browser automation storage

The systemd service stores dry-run temporary profiles, caches, downloads, logs,
and benchmark artifacts on `/mnt/hdd-500gb/browser-storage`. The service sets
`BROWSER_AUTOMATION_STORAGE`, `TMPDIR`, `TEMP`, and `TMP` accordingly. Login
profiles under `chrome_profiles/` and the project database are intentionally
not moved. If the HDD path is unavailable, dry-run exits with an explicit
storage error instead of silently filling the root filesystem.

1. **Add a business** — Paste a Google Maps URL and configure star rating distribution and business description via the dashboard.
2. **Add email accounts** — Add Google account credentials to the shared email pool.
3. **Queue reviews** — Assign emails to a business to create pending review jobs.
4. **Worker picks up jobs** — The background worker selects a local review template for each job and posts it via an undetected Chrome browser logged into the corresponding Google account.
5. **Status tracking** — Each job transitions through `pending → reviewing → reviewed` (or back to `pending` on failure).

---

## Requirements

- Python 3.10+
- Google Chrome installed
- Google accounts with access to post reviews

---

## Tags

`google-maps` `review-automation` `selenium` `seleniumbase` `flask` `python` `bot` `web-scraping` `chrome-automation` `undetected-chromedriver` `sqlite` `review-bot`

---

## Disclaimer

This project is for **educational purposes only**. Automating Google reviews may violate [Google's Terms of Service](https://policies.google.com/terms). Use responsibly.
