# Google Review Automation v2 🤖⭐

An automated Google Maps review bot and automation suite built with **Native Linux Chromium**, **CDP Cookie Injection**, and **Zero-VM Architecture**. Posts reviews from multiple authenticated Google accounts to any Google Maps business listing — controllable via Web Dashboard, Server TUI CLI, or remote Windows CMD client.

---

## What's New in v2

- **Zero-VM Architecture** — Completely replaced heavy Windows VMs with lightweight native Linux Chromium running on virtual Xvfb displays (`:99` to `:104`).
- **Windows CMD CLI Client (`bot_cli.py` & `bot.bat`)** — Control review automation directly from your physical Windows PC Command Prompt over local network with live log streaming.
- **User Authentication** — Secure login prompt (`username`, `password`) before accessing task sessions and interactive menus.
- **CDP Cookie Restoration** — Instant session restoration using Chrome DevTools Protocol (`Network.setCookies`) bypassing restrictive domain limitations.
- **Independent Parallel CDP Ports** — Dedicated debugging ports (`9222 + slot_index`) prevent browser connection collisions during parallel execution.
- **Interactive Server TUI (`cli.py`)** — Rich terminal user interface with live stats, account cookie status, business management, and browser diagnostic test.

---

## Features

- **Local & AI Review Generation** — Supports template-based reviews (Baik, Buruk, Random) and AI-assisted generation via Google AI Gemini.
- **Multi-Account & Cookie Pool** — Manage Google accounts with JSON cookie storage and automatic session health validation.
- **Parallel Multi-Browser Automation** — Run up to 6 concurrent Chromium browser slots simultaneously.
- **Web Dashboard & REST API** — Flask web dashboard with live Sharescreen preview, audit logs, and REST API endpoints.
- **Background Worker & Drip Campaign** — Independent worker process with auto-replenishment during business hours.

---

## Tech Stack

| Component | Technology |
|---|---|
| Engine | Linux Native Chromium (Xvfb `:99..:104`) |
| Automation | SeleniumBase / Selenium CDP (Undetected Mode) |
| Web Backend | Flask, Werkzeug, SQLite (WAL mode) |
| CLI Clients | Python `urllib` (Windows Zero-pip Client), Rich TUI (Server) |
| AI Generation | Google Gemini API (Optional) |
| Auth | Session-based & HMAC SHA-256 API Key verification |

---

## Project Structure

```
.
├── app.py                  # Flask web dashboard & REST API
├── bot.py                  # Core native Chromium review automation engine
├── db.py                   # SQLite database layer & schema migrations
├── worker.py               # Background scheduler & drip campaign processor
├── session_manager.py      # CDP cookie management & session health validator
├── cli.py                  # Rich terminal interactive dashboard (Linux Host)
├── bot_cli.py              # Windows Command Prompt client script
├── bot.bat                 # Windows 1-click batch launcher & auto-updater
├── requirements.txt
├── templates/              # Dashboard Jinja2 HTML templates
└── static/                 # CSS, JavaScript & client assets
```

---

## Setup & Quick Start

### 1. Host Server Installation (Linux)

```bash
git clone https://github.com/chaerul24/google-review-automation-v2.git
cd google-review-automation-v2

# Create virtual environment & install requirements
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your SECRET_KEY and APP_PASSWORD
```

### 2. Start Services

```bash
# Start Web Dashboard
python app.py

# Start Background Worker
python worker.py

# Or launch Server CLI
python cli.py
```

---

## Client Usage (Windows, Android Termux, Linux)

### A. Android (Termux) & Linux
Kontrol dan monitor jalannya bot langsung dari HP Android melalui **Termux**:

1. Buka aplikasi Termux, install dependensi dasar (hanya Python & cURL):
   ```bash
   pkg update && pkg install python curl -y
   ```
2. Unduh launcher dan jalankan:
   ```bash
   curl -O https://autobotix.my.id/download/bot.sh && bash bot.sh
   ```
   *(Atau gunakan IP lokal jika satu jaringan WiFi: `curl -O http://<SERVER_IP>:5000/download/bot.sh && bash bot.sh`)*
3. Masukkan Username dan Password akun AutoBotix Anda.
4. Pilih menu `[1] 🚀 Jalankan Task` untuk menjalankan atau memantau ulasan secara live!

---

### B. Windows Client Usage

Run review tasks directly from any physical Windows PC on the local network:

1. Download the launcher from your browser or Command Prompt:
   ```cmd
   curl -O http://<SERVER_IP>:5000/download/bot.bat
   ```
2. Double click `bot.bat` or run:
   ```cmd
   bot.bat
   ```
3. Enter your server **Username** and **Password**.
4. Select menu `[1] 🚀 Jalankan Task` and watch the live streaming review logs!

---

## Tags

`google-maps` `review-automation` `selenium` `seleniumbase` `flask` `python` `bot` `cdp` `chromium` `xvfb` `sqlite`

---

## Disclaimer

This project is for **educational and testing purposes only**. Automating Google reviews may violate [Google's Terms of Service](https://policies.google.com/terms). Use responsibly.
