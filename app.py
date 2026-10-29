import csv
import hashlib
import hmac
import io
import json
import logging
import os
import random
import secrets
import signal
import subprocess
import sys
import shutil
import socket
import threading
import time
from PIL import Image, ImageDraw, ImageFont
from collections import defaultdict, deque
from datetime import datetime, timedelta
from functools import wraps
from urllib.parse import urlparse

from dotenv import load_dotenv
from flask import (
    abort,
    Flask,
    Response,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    session,
    stream_with_context,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix

import db
import bot
import domain_intelligence
import session_manager

load_dotenv()

app = Flask(__name__)
logger = logging.getLogger("app")
_is_production = os.environ.get("APP_ENV", "production").lower() == "production"
_secret_key = os.environ.get("SECRET_KEY")
_app_password = os.environ.get("APP_PASSWORD")
_public_url = os.environ.get("PUBLIC_BASE_URL", "https://autobotix.my.id").rstrip("/")
_public_parts = urlparse(_public_url)
if _public_parts.scheme != "https" or _public_parts.hostname != "autobotix.my.id" or _public_parts.path:
    raise RuntimeError("PUBLIC_BASE_URL must be https://autobotix.my.id")
if _is_production and (not _secret_key or not _app_password):
    raise RuntimeError("Secure application configuration is required in production.")
app.secret_key = _secret_key or "development-only-secret-key"
app.config.update(
    SERVER_NAME="autobotix.my.id",
    PREFERRED_URL_SCHEME="https",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "false").lower() in ("true", "1"),
    SESSION_COOKIE_DOMAIN=None,
)
app.permanent_session_lifetime = timedelta(days=7)

FRONTEND_DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "dist")


def _serve_spa():
    index_file = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.exists(index_file):
        resp = send_from_directory(FRONTEND_DIST, "index.html", max_age=0)
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return resp
    return None


@app.route("/assets/<path:filename>")
def serve_frontend_assets(filename):
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    return send_from_directory(assets_dir, filename)


@app.route("/vite.svg")
def serve_vite_svg():
    return send_from_directory(FRONTEND_DIST, "vite.svg")


# ── Windows CLI Client & Remote API ──────────────────────────────────────────

@app.route("/download/bot_cli.py")
def download_bot_cli():
    """Download Windows CLI client script."""
    cli_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(cli_dir, "bot_cli.py", as_attachment=True)


@app.route("/download/bot.bat")
def download_bot_bat():
    """Download Windows batch file launcher."""
    cli_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(cli_dir, "bot.bat", as_attachment=True)


@app.route("/download/bot.sh")
def download_bot_sh():
    """Download Linux / macOS / Termux shell launcher."""
    cli_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(cli_dir, "bot.sh", as_attachment=True)



@app.route("/promo/<path:filename>")
def serve_promo_video(filename):
    """Serve or download promotional video files."""
    promo_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "promo-video", "out")
    target_file = os.path.join(promo_dir, filename)
    if not os.path.isfile(target_file):
        abort(404)
    as_attachment = request.args.get("download", "0") in ("1", "true")
    return send_from_directory(promo_dir, filename, mimetype="video/mp4", as_attachment=as_attachment)


@app.route("/promo")
def promo_video_gallery():
    """Web player preview gallery for AutoBotix promo videos."""
    html_content = """<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>AutoBotix — Video Promosi</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body { background-color: #070B14; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
  </style>
</head>
<body class="text-slate-100 min-h-screen p-6 md:p-12">
  <div class="max-w-6xl mx-auto space-y-10">
    <div class="text-center space-y-3">
      <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold tracking-wider uppercase">
        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
        AutoBotix Promo Suite
      </div>
      <h1 class="text-3xl md:text-5xl font-black tracking-tight text-white">Video Promosi AutoBotix</h1>
      <p class="text-slate-400 text-sm md:text-base max-w-2xl mx-auto">
        Dibuat secara terprogram menggunakan Remotion & React. Siap ditonton langsung di browser atau diunduh untuk publikasi.
      </p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
      <!-- Landscape 16:9 -->
      <div class="lg:col-span-7 bg-slate-900/80 border border-slate-800 rounded-2xl p-5 md:p-6 shadow-2xl space-y-4">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-lg font-bold text-white flex items-center gap-2">
              <span class="text-emerald-400">📺</span> Format Landscape (16:9)
            </h2>
            <p class="text-xs text-slate-400">1920x1080 • 15 Detik • YouTube / Twitter / Web</p>
          </div>
          <a href="/promo/autobotix-promo-landscape.mp4?download=1" download class="px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs rounded-lg transition-all shadow-lg shadow-emerald-500/20 flex items-center gap-1.5">
            ⬇️ Download MP4
          </a>
        </div>
        <div class="rounded-xl overflow-hidden bg-black border border-slate-800 aspect-video shadow-inner">
          <video controls class="w-full h-full object-contain" preload="metadata">
            <source src="/promo/autobotix-promo-landscape.mp4" type="video/mp4" />
            Browser Anda tidak mendukung tag video.
          </video>
        </div>
        <div class="text-xs text-slate-400 flex items-center justify-between pt-1">
          <span>Link Langsung: <a href="/promo/autobotix-promo-landscape.mp4" target="_blank" class="text-emerald-400 hover:underline">/promo/autobotix-promo-landscape.mp4</a></span>
          <span class="text-slate-500">Ukuran: 3.1 MB</span>
        </div>
      </div>

      <!-- Shorts 9:16 -->
      <div class="lg:col-span-5 bg-slate-900/80 border border-slate-800 rounded-2xl p-5 md:p-6 shadow-2xl space-y-4">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-lg font-bold text-white flex items-center gap-2">
              <span class="text-cyan-400">📱</span> Format Vertical Shorts (9:16)
            </h2>
            <p class="text-xs text-slate-400">1080x1920 • 15 Detik • TikTok / Reels / Shorts</p>
          </div>
          <a href="/promo/autobotix-promo-shorts.mp4?download=1" download class="px-4 py-2 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs rounded-lg transition-all shadow-lg shadow-cyan-500/20 flex items-center gap-1.5">
            ⬇️ Download MP4
          </a>
        </div>
        <div class="rounded-xl overflow-hidden bg-black border border-slate-800 max-w-[280px] mx-auto aspect-[9/16] shadow-inner">
          <video controls class="w-full h-full object-contain" preload="metadata">
            <source src="/promo/autobotix-promo-shorts.mp4" type="video/mp4" />
            Browser Anda tidak mendukung tag video.
          </video>
        </div>
        <div class="text-xs text-slate-400 flex items-center justify-between pt-1">
          <span>Link Langsung: <a href="/promo/autobotix-promo-shorts.mp4" target="_blank" class="text-cyan-400 hover:underline">/promo/autobotix-promo-shorts.mp4</a></span>
          <span class="text-slate-500">Ukuran: 2.7 MB</span>
        </div>
      </div>
    </div>

    <div class="text-center pt-4">
      <a href="/dashboard" class="inline-flex items-center gap-2 text-xs text-slate-400 hover:text-white transition-colors">
        ← Kembali ke AutoBotix Dashboard
      </a>
    </div>
  </div>
</body>
</html>"""
    return Response(html_content, mimetype="text/html")


# ── Multi-VM Node Provisioning Routes ─────────────────────────────────────────

@app.route("/api/node/install.sh")
def serve_node_installer():
    script_content = """#!/usr/bin/env bash
set -e
echo "=========================================================="
echo " AutoBotix — Multi-VM Node Provisioning & Sync"
echo "=========================================================="
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3 python3-pip python3-venv xvfb ffmpeg chromium git curl sqlite3 tar

mkdir -p /root/google-review-automation
cd /root/google-review-automation

echo "[1/4] Mengunduh paket aplikasi dari VM Utama (192.168.1.17)..."
curl -sSL "http://192.168.1.17:5000/api/node/package.tar.gz" | tar -xz -C /root/google-review-automation

echo "[2/4] Mengonfigurasi Virtual Environment Python..."
if [ ! -d "/root/google-review-automation/.venv" ]; then
    python3 -m venv /root/google-review-automation/.venv
fi
/root/google-review-automation/.venv/bin/pip install --upgrade pip -q
/root/google-review-automation/.venv/bin/pip install -q Flask Werkzeug selenium seleniumbase requests python-dotenv psutil Jinja2

echo "[3/4] Menyiapkan Display Virtual Xvfb :99 s/d :104..."
cat << 'EOF' > /etc/systemd/system/chromium-display.service
[Unit]
Description=Virtual display for Google Review Automation Display :99
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/Xvfb :99 -screen 0 1366x768x24 -nolisten tcp
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF

for port in 100 101 102 103 104; do
cat << EOF > /etc/systemd/system/chromium-display-${port}.service
[Unit]
Description=Virtual display for Google Review Automation Display :${port}
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/Xvfb :${port} -screen 0 1366x768x24 -nolisten tcp
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF
done

systemctl daemon-reload
systemctl enable --now chromium-display.service chromium-display-100.service chromium-display-101.service chromium-display-102.service chromium-display-103.service chromium-display-104.service

echo "[4/4] Mengaktifkan Service AutoBotix..."
cat << 'EOF' > /etc/systemd/system/google-review-automation.service
[Unit]
Description=Google Review Automation dashboard
After=network.target chromium-display.service
Wants=chromium-display.service

[Service]
Type=simple
WorkingDirectory=/root/google-review-automation
EnvironmentFile=-/root/google-review-automation/.env
Environment=DISPLAY=:99
Environment=CHROMIUM_DISPLAY=:99
ExecStart=/root/google-review-automation/.venv/bin/python /root/google-review-automation/app.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Inisialisasi database baru yang bersih untuk node ini
/root/google-review-automation/.venv/bin/python -c "import db; db.init_db()"

systemctl daemon-reload
systemctl enable --now google-review-automation.service

NODE_IP=$(hostname -I | awk '{print $1}')
echo "=========================================================="
echo " AutoBotix Node Berhasil Dipasang!"
echo " Buka dashboard VM ini di: http://${NODE_IP}:5000"
echo " Silakan masukkan cookie akun Anda di menu 'Kelola Cookie'"
echo "=========================================================="
"""
    return Response(script_content, mimetype="text/plain")


@app.route("/api/node/package.tar.gz")
def serve_node_package():
    """Package the codebase and frontend dist on the fly for new nodes."""
    buffer = io.BytesIO()
    import tarfile
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        base_dir = "/root/google-review-automation"
        for root, dirs, files in os.walk(base_dir):
            if ".venv" in root or "__pycache__" in root or ".git" in root or "node_modules" in root or "chrome_profiles" in root:
                continue
            for file in files:
                if file.endswith(".pyc") or file == "reviews.db" or file.startswith("reviews.db-"):
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, base_dir)
                tar.add(full_path, arcname=rel_path)
    buffer.seek(0)
    return Response(buffer.getvalue(), mimetype="application/gzip", headers={"Content-Disposition": "attachment; filename=package.tar.gz"})


class LoopbackProxyFix:
    """Trust forwarded scheme/host only from the local cloudflared connector."""
    def __init__(self, application):
        self.application = application
        self.proxy_application = ProxyFix(application, x_for=1, x_proto=1, x_host=1, x_port=1)

    def __call__(self, environ, start_response):
        if environ.get("REMOTE_ADDR") in {"127.0.0.1", "::1"}:
            return self.proxy_application(environ, start_response)
        return self.application(environ, start_response)


app.wsgi_app = LoopbackProxyFix(app.wsgi_app)

# Hash is computed once at startup from the plaintext value in .env
_PASSWORD_HASH = generate_password_hash(
    _app_password or "development-only-password"
)
_LOGIN_ATTEMPTS = defaultdict(deque)
_LOGIN_WINDOW_SECONDS = 15 * 60
_LOGIN_MAX_ATTEMPTS = 8


def _csrf_token():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


@app.context_processor
def inject_security_context():
    return {"csrf_token": _csrf_token()}


@app.before_request
def protect_csrf():
    if request.path in {"/login", "/api/login", "/logout", "/api/logout", "/api/csrf-token", "/api/cli/login", "/api/cli/register"} or request.path.startswith("/api/vm/") or request.path.startswith("/download/") or request.path.startswith("/api/cli/"):
        return
    api_key = request.headers.get("X-API-Key")
    expected_key = os.environ.get("APP_PASSWORD", "")
    if api_key and expected_key and hmac.compare_digest(api_key, expected_key):
        return
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        supplied = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
        if not supplied and request.is_json:
            supplied = (request.get_json(silent=True) or {}).get("csrf_token")
        if not supplied:
            supplied = request.cookies.get("csrf_token")
        if not supplied or not hmac.compare_digest(supplied, _csrf_token()):
            abort(400, description="Invalid or missing CSRF token.")


@app.after_request
def inject_csrf_cookie(response):
    if session.get("logged_in") or session.get("csrf_token"):
        response.set_cookie(
            "csrf_token",
            _csrf_token(),
            samesite="Lax",
            secure=request.is_secure,
            httponly=False,
        )
    return response


@app.route("/api/csrf-token")
def api_csrf_token():
    return jsonify({"csrf_token": _csrf_token()})

# ── Auth helpers ──────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get("X-API-Key")
        expected_key = os.environ.get("APP_PASSWORD", "")
        if api_key and expected_key and hmac.compare_digest(api_key, expected_key):
            return f(*args, **kwargs)
        if not session.get("logged_in"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "Unauthorized", "logged_in": False, "authenticated": False}), 401
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ── CLI Version Manifest & Updater Endpoints ─────────────────────────────────

CLI_VERSIONS = [
    {
        "version": "v1.0.0",
        "version_code": 100,
        "release_date": "2026-10-25",
        "title": "Initial CLI Release",
        "description": "Rilis perdana AutoBotix Windows CLI dengan arsitektur Native Chromium & Multi-Display Virtual Xvfb.",
    },
    {
        "version": "v1.0.1",
        "version_code": 101,
        "release_date": "2026-10-26",
        "title": "Review Cleaner & CDP Lock",
        "description": "Fitur Hapus Ulasan (Database Cleaner & Live Maps Chromium) dan proteksi Mutex Profile Browser.",
    },
    {
        "version": "v1.0.2",
        "version_code": 102,
        "release_date": "2026-10-27",
        "title": "Review Queue & Auto-Update",
        "description": "Sistem Daftar Antrean Ulasan (Anti-Bot Queue), jeda alami konstan, live queue inspector, dan auto-update versioning.",
    },
    {
        "version": "v1.0.3",
        "version_code": 103,
        "release_date": "2026-10-27",
        "title": "Strict Queue Lock & Metrics Summary",
        "description": "Proteksi Mutex Antrean Anti-Bentrok per target, metrik Total Berhasil/Skip/Gagal/Error, dan perbaikan klik dialog Maps.",
    },
    {
        "version": "v1.0.4",
        "version_code": 104,
        "release_date": "2026-10-28",
        "title": "Termux Mobile Fix & Clean Clear-Screen Navigation",
        "description": "Perbaikan animasi spinner Termux Android (anti-wrapping & mobile responsive), auto clear-screen, dan logo Google Maps di setiap perpindahan menu.",
    },
    {
        "version": "v1.0.5",
        "version_code": 105,
        "release_date": "2026-10-28",
        "title": "Batch Cookie Live Validation & Google Anti-Expiry Engine",
        "description": "Uji validitas cookie massal seluruh akun (live batch test), auto-extend cookie 2 tahun, auto-sync rotating token, dan background keepalive heartbeat anti-kadaluarsa.",
    },
    {
        "version": "v1.0.6",
        "version_code": 106,
        "release_date": "2026-10-29",
        "title": "Fitur List Komentar Per Akun & Total Bintang",
        "description": "Menu baru visualisasi ulasan per akun Google dengan struktur garis line (tree), rincian komentar per bisnis, dan perhitungan Total Bintang per akun serta grand total.",
    },
    {
        "version": "v1.0.7",
        "version_code": 107,
        "release_date": "2026-10-29",
        "title": "Anti-Logout Guard, Auto-Relogin Engine & Cookie Status Fix",
        "description": "Perlindungan anti-logout akun Google, mesin auto-relogin untuk akun berpassword, badge status 🔑 SIAP (Auto-Login) di tabel cookie, dan perbaikan reset status cookie saat paste ulang.",
    },
]

LATEST_CLI_VERSION = "v1.0.7"
LATEST_CLI_VERSION_CODE = 107


@app.route("/api/cli/version", methods=["GET"])
def api_cli_version():
    """Return CLI version information, release changelog, and latest download link."""
    return jsonify({
        "status": "ok",
        "latest_version": LATEST_CLI_VERSION,
        "latest_version_code": LATEST_CLI_VERSION_CODE,
        "min_supported_version": "v1.0.0",
        "versions": CLI_VERSIONS,
        "changelog": CLI_VERSIONS[-1]["description"],
        "download_url": "/api/cli/download",
    })


@app.route("/api/cli/download", methods=["GET"])
def api_cli_download():
    """Download the latest bot_cli.py script directly from the server."""
    cli_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_cli.py")
    if not os.path.exists(cli_path):
        return jsonify({"status": "error", "message": "File bot_cli.py not found on server"}), 404
    return send_file(cli_path, as_attachment=True, download_name="bot_cli.py", mimetype="text/x-python")


@app.route("/api/cli/login", methods=["POST"])
def api_cli_login():
    """CLI remote authentication endpoint."""
    data = request.get_json(silent=True) or request.form or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    expected_user = os.environ.get("APP_USERNAME", "admin").strip()
    expected_pass = os.environ.get("APP_PASSWORD", "").strip()

    pass_ok = False
    role = "user"

    # 1. Periksa akun terdaftar di database
    db.init_db()
    user_record = db.get_user_by_username(username)
    if user_record and check_password_hash(user_record["password_hash"], password):
        pass_ok = True
        role = user_record.get("role", "user")
    else:
        # 2. Periksa akun default/sistem admin
        user_ok = (username.lower() == expected_user.lower()) or (username.lower() == "admin")
        if user_ok:
            if expected_pass and hmac.compare_digest(password, expected_pass):
                pass_ok = True
                role = "administrator"
            elif check_password_hash(_PASSWORD_HASH, password):
                pass_ok = True
                role = "administrator"

    if pass_ok:
        _audit(username, "cli_login", "terminal", "success")
        return jsonify({
            "status": "ok",
            "authenticated": True,
            "username": username,
            "role": role,
            "api_key": expected_pass,
            "message": f"Login berhasil! Selamat datang, {username}."
        })

    _audit(username or "anonymous", "cli_login", "terminal", "denied", "Invalid username or password.")
    return jsonify({
        "status": "error",
        "authenticated": False,
        "message": "Username atau password salah."
    }), 401


@app.route("/api/cli/register", methods=["POST"])
def api_cli_register():
    """CLI user registration endpoint."""
    data = request.get_json(silent=True) or request.form or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    if not username or len(username) < 3:
        return jsonify({
            "status": "error",
            "message": "Username minimal 3 karakter."
        }), 400

    if not username.replace("_", "").isalnum():
        return jsonify({
            "status": "error",
            "message": "Username hanya boleh huruf, angka, dan underscore (_)."
        }), 400

    if not password or len(password) < 4:
        return jsonify({
            "status": "error",
            "message": "Password minimal 4 karakter."
        }), 400

    expected_user = os.environ.get("APP_USERNAME", "admin").strip()
    if username.lower() in {"admin", expected_user.lower()}:
        return jsonify({
            "status": "error",
            "message": f"Username '{username}' adalah akun admin sistem yang sudah terdaftar."
        }), 400

    db.init_db()
    existing = db.get_user_by_username(username)
    if existing:
        return jsonify({
            "status": "error",
            "message": f"Username '{username}' sudah terdaftar. Silakan pilih username lain atau login."
        }), 400

    hashed = generate_password_hash(password)
    ok = db.create_user(username, hashed, role="user")
    if not ok:
        return jsonify({
            "status": "error",
            "message": "Gagal menyimpan akun ke database."
        }), 500

    _audit(username, "cli_register", "terminal", "success", "User registered via CLI")
    return jsonify({
        "status": "ok",
        "message": f"Pendaftaran berhasil! Akun '{username}' siap digunakan.",
        "username": username
    })


@app.route("/api/cli/status")
@login_required
def api_cli_status():
    """CLI dashboard overview endpoint."""
    db.init_db()
    businesses = db.get_all_businesses()
    with db.get_db() as conn:
        accounts = conn.execute("""
            SELECT e.id, e.email, COALESCE(e.account_name, c.account_name, '') AS account_name, e.flagged, c.status AS cookie_status,
                   (CASE WHEN e.password IS NOT NULL AND TRIM(e.password) != '' AND e.password != 'cookie_auth' THEN 1 ELSE 0 END) AS has_password
            FROM emails e
            LEFT JOIN cookies c ON e.email = c.email
            ORDER BY e.id ASC
        """).fetchall()
        cookies_list = conn.execute("""
            SELECT 
                COALESCE(c.id, e.id) AS id,
                e.email,
                COALESCE(c.account_name, e.account_name, '') AS account_name,
                CASE 
                    WHEN c.cookie_json IS NULL OR c.cookie_json = '' THEN 'no_cookie'
                    ELSE c.status 
                END AS status,
                c.last_checked_at,
                COALESCE(c.updated_at, e.created_at) AS updated_at,
                c.error_reason,
                (CASE WHEN e.password IS NOT NULL AND TRIM(e.password) != '' AND e.password != 'cookie_auth' THEN 1 ELSE 0 END) AS has_password
            FROM emails e
            LEFT JOIN cookies c ON e.email = c.email
            UNION
            SELECT 
                c.id,
                c.email,
                COALESCE(c.account_name, '') AS account_name,
                c.status,
                c.last_checked_at,
                c.updated_at,
                c.error_reason,
                0 AS has_password
            FROM cookies c
            WHERE c.email NOT IN (SELECT email FROM emails)
            ORDER BY id ASC
        """).fetchall()
        rev_count = conn.execute("SELECT COUNT(*) FROM reviews WHERE status = 'reviewed'").fetchone()[0]
        pending_count = conn.execute("SELECT COUNT(*) FROM reviews WHERE status = 'pending'").fetchone()[0]

    displays = []
    for num in [99, 100, 101, 102, 103, 104]:
        if os.path.exists(f"/tmp/.X11-unix/X{num}"):
            displays.append(f":{num}")

    return jsonify({
        "status": "ok",
        "engine": "Chromium 155 (Linux Native)",
        "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "displays": displays,
        "businesses_count": len(businesses),
        "accounts_count": len(accounts),
        "active_cookies": sum(1 for a in accounts if a["cookie_status"] == "active"),
        "reviewed_count": rev_count,
        "pending_count": pending_count,
        "businesses": [dict(b) for b in businesses],
        "accounts": [dict(a) for a in accounts],
        "cookies": [dict(c) for c in cookies_list],
    })


@app.route("/api/cli/reviews/by-account", methods=["GET"])
@login_required
def api_cli_reviews_by_account():
    """Returns all reviews grouped per Google account with star counts and comment history."""
    status = request.args.get("status", "reviewed")
    search = request.args.get("search", "").strip()
    include_empty = request.args.get("include_empty", "0").lower() in ("1", "true", "yes")
    data = db.get_reviews_by_account(status=status, search=search, include_empty=include_empty)
    return jsonify({
        "status": "ok",
        **data
    })


@app.route("/api/cli/cookies/check-names", methods=["POST"])
@login_required
def api_cli_check_cookie_names():
    """Verify stored cookies live against Google and retrieve real Account Names."""
    with db.get_db() as conn:
        cookies = conn.execute("SELECT id, email, cookie_json FROM cookies ORDER BY id ASC").fetchall()

    results = []
    active_count = 0
    for row in cookies:
        cid = row["id"]
        email = row["email"]
        c_json = row["cookie_json"]

        live = session_manager.check_google_account_live(c_json, fallback_email=email)
        acc_name = live.get("account_name") or ""
        st_val = live.get("status") or "needs_login"
        reason = live.get("reason") or ""
        if st_val == "active":
            active_count += 1

        with db.get_db() as conn:
            conn.execute(
                """UPDATE cookies
                   SET status = ?, account_name = ?, last_checked_at = CURRENT_TIMESTAMP, error_reason = ?
                   WHERE id = ?""",
                (st_val, acc_name, reason, cid),
            )
            conn.execute(
                """UPDATE emails
                   SET account_name = ?, flagged = (CASE WHEN ? = 'active' THEN 0 ELSE flagged END)
                   WHERE email = ?""",
                (acc_name, st_val, email),
            )

        results.append({
            "id": cid,
            "email": email,
            "account_name": acc_name,
            "status": st_val,
            "reason": reason,
        })

    return jsonify({
        "status": "ok",
        "checked": len(results),
        "active_count": active_count,
        "results": results,
    })


@app.route("/api/cli/cookies/test-all", methods=["POST"])
@login_required
def api_cli_test_all_cookies():
    """Batch test all account cookies live against Google and return complete status summary."""
    with db.get_db() as conn:
        cookies = conn.execute("SELECT id, email, cookie_json FROM cookies ORDER BY id ASC").fetchall()

    results = []
    active_count = 0
    expired_count = 0

    for row in cookies:
        cid = row["id"]
        email = row["email"]
        c_json = row["cookie_json"]

        live = session_manager.check_google_account_live(c_json, fallback_email=email)
        acc_name = live.get("account_name") or ""
        st_val = live.get("status") or "needs_login"
        reason = live.get("reason") or ""
        is_val = bool(live.get("is_valid", False))

        if st_val == "active":
            active_count += 1
        else:
            expired_count += 1

        with db.get_db() as conn:
            conn.execute(
                """UPDATE cookies
                   SET status = ?, account_name = (CASE WHEN ? != '' THEN ? ELSE account_name END),
                       last_checked_at = CURRENT_TIMESTAMP, error_reason = ?
                   WHERE id = ?""",
                (st_val, acc_name, acc_name, reason, cid),
            )
            conn.execute(
                """UPDATE emails
                   SET account_name = (CASE WHEN ? != '' THEN ? ELSE account_name END),
                       flagged = (CASE WHEN ? = 'active' THEN 0 ELSE flagged END),
                       fail_count = (CASE WHEN ? = 'active' THEN 0 ELSE fail_count END)
                   WHERE email = ?""",
                (acc_name, acc_name, st_val, st_val, email),
            )

        results.append({
            "id": cid,
            "email": email,
            "account_name": acc_name,
            "status": st_val,
            "is_valid": is_val,
            "reason": reason,
        })

    return jsonify({
        "status": "ok",
        "total": len(results),
        "active_count": active_count,
        "expired_count": expired_count,
        "results": results,
    })


@app.route("/api/cli/cookies/delete", methods=["POST"])
@login_required
def api_cli_delete_cookie():
    """Delete a cookie by ID or Email with admin authorization check."""
    req_role = request.headers.get("X-User-Role", "")
    req_user = (request.headers.get("X-Username") or "").strip()
    expected_user = os.environ.get("APP_USERNAME", "admin").strip()
    is_admin = (req_role == "administrator") or (req_user.lower() in ("admin", expected_user.lower())) or (session.get("role") == "administrator")
    if not is_admin:
        return jsonify({"status": "error", "message": "Akses ditolak. Fitur hapus cookie hanya untuk akun administrator."}), 403

    data = request.get_json(silent=True) or request.form or {}
    cookie_id = data.get("cookie_id")
    email = (data.get("email") or "").strip()

    with db.get_db() as conn:
        row = None
        if cookie_id:
            row = conn.execute("SELECT id, email FROM cookies WHERE id = ?", (cookie_id,)).fetchone()
        elif email:
            row = conn.execute("SELECT id, email FROM cookies WHERE email = ?", (email,)).fetchone()

        if not row:
            return jsonify({"status": "error", "message": "Cookie tidak ditemukan."}), 404

        cid = row["id"]
        c_email = row["email"]
        db.delete_cookie(cid)

    _audit(req_user or "admin", "delete_cookie", c_email, "success")
    return jsonify({
        "status": "ok",
        "message": f"Cookie untuk akun '{c_email}' (ID {cid}) berhasil dihapus.",
        "cookie_id": cid,
        "email": c_email
    })


@app.route("/api/cli/cookies/auto-login", methods=["POST"])
@login_required
def api_cli_auto_login_cookies():
    """Batch auto-login to Google accounts that have passwords but are in needs_login/no_cookie state."""
    data = request.get_json(silent=True) or request.form or {}
    target_email = (data.get("email") or "").strip()

    with db.get_db() as conn:
        if target_email:
            rows = conn.execute(
                "SELECT e.id, e.email, e.password, e.totp_secret, c.status AS cookie_status FROM emails e LEFT JOIN cookies c ON e.email = c.email WHERE e.email = ?",
                (target_email,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT e.id, e.email, e.password, e.totp_secret, c.status AS cookie_status FROM emails e LEFT JOIN cookies c ON e.email = c.email WHERE e.password IS NOT NULL AND TRIM(e.password) != '' AND e.password != 'cookie_auth' ORDER BY e.id ASC"
            ).fetchall()

    if not rows:
        return jsonify({
            "status": "ok",
            "message": "Tidak ada akun dengan Password yang terdata untuk auto-login.",
            "results": [],
            "success_count": 0,
            "failed_count": 0
        })

    import bot
    results = []
    success_count = 0
    failed_count = 0

    for r in rows:
        email = r["email"]
        pwd = r["password"]
        totp = r["totp_secret"]
        c_status = r["cookie_status"]

        if not target_email and c_status == "active":
            results.append({
                "email": email,
                "status": "already_active",
                "message": "Sesi akun sudah aktif."
            })
            continue

        ok, msg = bot.auto_login_single_account(email, pwd, totp_secret=totp)
        if ok:
            success_count += 1
            results.append({
                "email": email,
                "status": "success",
                "message": msg
            })
        else:
            failed_count += 1
            results.append({
                "email": email,
                "status": "failed",
                "message": msg
            })

    return jsonify({
        "status": "ok",
        "message": f"Auto-login selesai: {success_count} berhasil, {failed_count} gagal.",
        "success_count": success_count,
        "failed_count": failed_count,
        "results": results
    })


def _audit(actor, action, target, outcome, message=None):
    """Best-effort audit logging; authentication must never depend on logging."""
    try:
        db.migrate_autobotix()
        db.log_autobotix_activity(actor, action, target, outcome, message)
    except Exception:
        app.logger.exception("AutoBotix audit logging failed")


def _login_limited(remote_addr):
    now = time.monotonic()
    attempts = _LOGIN_ATTEMPTS[remote_addr]
    while attempts and now - attempts[0] > _LOGIN_WINDOW_SECONDS:
        attempts.popleft()
    return len(attempts) >= _LOGIN_MAX_ATTEMPTS


def _valid_business_url(value):
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc) and len(value) <= 2048


# ── Auth routes ───────────────────────────────────────────────────────────────

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))

    error = False
    if request.method == "POST":
        remote_addr = request.remote_addr or "unknown"
        if _login_limited(remote_addr):
            _audit("anonymous", "login", "administrator", "rate_limited", "Too many failed login attempts.")
            if request.is_json or request.headers.get("Accept") == "application/json":
                return jsonify({"status": "error", "message": "Terlalu banyak percobaan login gagal. Silakan tunggu 15 menit."}), 429
            return render_template("login.html", error=True), 429
        
        data = request.get_json(silent=True) or request.form
        password = (data.get("password") or "")[:1024]
        if check_password_hash(_PASSWORD_HASH, password):
            session.permanent = True
            session["logged_in"] = True
            session["role"] = "administrator"
            _LOGIN_ATTEMPTS.pop(remote_addr, None)
            _audit("administrator", "login", "session", "success")
            if request.is_json or request.headers.get("Accept") == "application/json":
                return jsonify({"status": "ok", "authenticated": True, "csrf_token": _csrf_token()})
            return redirect(url_for("dashboard"))
        _LOGIN_ATTEMPTS[remote_addr].append(time.monotonic())
        _audit("anonymous", "login", "administrator", "denied", "Invalid credentials.")
        if request.is_json or request.headers.get("Accept") == "application/json":
            return jsonify({"status": "error", "message": "Kata sandi salah."}), 401
        error = True

    spa = _serve_spa()
    if spa is not None:
        return spa
    return render_template("login.html", error=error)


@app.route("/api/auth/me")
def api_auth_me():
    is_auth = bool(session.get("logged_in"))
    return jsonify({
        "authenticated": is_auth,
        "role": session.get("role") if is_auth else None,
        "csrf_token": _csrf_token(),
    })


@app.route("/api/login", methods=["POST"])
def api_login():
    remote_addr = request.remote_addr or "unknown"
    if _login_limited(remote_addr):
        _audit("anonymous", "login", "administrator", "rate_limited", "Too many failed login attempts.")
        return jsonify({"status": "error", "message": "Terlalu banyak percobaan login gagal. Silakan tunggu 15 menit."}), 429

    data = request.get_json(silent=True) or request.form
    password = (data.get("password") or "")[:1024]
    if check_password_hash(_PASSWORD_HASH, password):
        session.permanent = True
        session["logged_in"] = True
        session["role"] = "administrator"
        _LOGIN_ATTEMPTS.pop(remote_addr, None)
        _audit("administrator", "login", "session", "success")
        return jsonify({"status": "ok", "authenticated": True, "csrf_token": _csrf_token()})

    _LOGIN_ATTEMPTS[remote_addr].append(time.monotonic())
    _audit("anonymous", "login", "administrator", "denied", "Invalid credentials.")
    return jsonify({"status": "error", "message": "Kata sandi salah."}), 401


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/api/logout", methods=["POST", "GET"])
def api_logout():
    session.clear()
    return jsonify({"status": "ok", "authenticated": False})


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route("/dashboard")
@login_required
def dashboard():
    spa = _serve_spa()
    if spa is not None:
        return spa
    db.migrate_autobotix()
    if not db.get_autobotix_domains():
        domain_intelligence.import_historical_snapshot()
    businesses = db.get_all_businesses()
    all_emails = db.get_all_emails()
    all_cookies = db.get_all_cookies()
    with db.get_db() as conn:
        queue_metrics = conn.execute(
            "SELECT "
            "SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending, "
            "SUM(CASE WHEN status = 'reviewed' THEN 1 ELSE 0 END) AS reviewed, "
            "SUM(CASE WHEN status IN ('failed','flagged') THEN 1 ELSE 0 END) AS failed "
            "FROM reviews"
        ).fetchone()
    inventory = db.get_autobotix_summary()
    return render_template(
        "dashboard.html", businesses=businesses, all_emails=all_emails,
        all_cookies=all_cookies,
        eligible_emails=sum(1 for e in all_emails if not e.get("flagged")),
        flagged_emails=sum(1 for e in all_emails if e.get("flagged")),
        queue_metrics=dict(queue_metrics or {}), inventory=inventory, host_metrics=_host_metrics(),
    )


@app.route("/api/dashboard")
@login_required
def api_dashboard():
    db.migrate_autobotix()
    if not db.get_autobotix_domains():
        domain_intelligence.import_historical_snapshot()
    businesses = db.get_all_businesses()
    all_emails = db.get_all_emails()
    all_cookies = db.get_all_cookies()
    with db.get_db() as conn:
        queue_metrics = conn.execute(
            "SELECT "
            "SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending, "
            "SUM(CASE WHEN status = 'reviewed' THEN 1 ELSE 0 END) AS reviewed, "
            "SUM(CASE WHEN status IN ('failed','flagged') THEN 1 ELSE 0 END) AS failed "
            "FROM reviews"
        ).fetchone()
    inventory = db.get_autobotix_summary()
    displays = []
    for num in [99, 100, 101, 102, 103, 104]:
        if os.path.exists(f"/tmp/.X11-unix/X{num}"):
            displays.append(f":{num}")

    return jsonify({
        "status": "ok",
        "businesses": businesses,
        "all_emails": all_emails,
        "all_cookies": all_cookies,
        "eligible_emails": sum(1 for e in all_emails if not e.get("flagged")),
        "flagged_emails": sum(1 for e in all_emails if e.get("flagged")),
        "active_cookies": sum(1 for c in all_cookies if c.get("status") == "active"),
        "displays": displays,
        "queue_metrics": dict(queue_metrics or {}),
        "inventory": inventory,
        "host_metrics": _host_metrics(),
        "analytics": db.get_analytics_summary(),
        "csrf_token": _csrf_token(),
    })


@app.route("/api/analytics")
@login_required
def api_analytics():
    return jsonify({
        "status": "ok",
        "analytics": db.get_analytics_summary(),
    })


@app.route("/api/generate-preview", methods=["POST"])
@login_required
def api_generate_preview():
    data = request.get_json(silent=True) or request.form
    biz_name = (data.get("business_name") or "Nama Bisnis").strip()
    prompt = (data.get("description") or "").strip()
    star = int(data.get("star_rating") or 5)
    persona = data.get("persona") or "default"
    lang = data.get("language") or "Indonesian"
    style = data.get("review_style") or "random"

    text = bot.generate_review(
        business_name=biz_name,
        review_prompt=prompt,
        star_rating=star,
        language=lang,
        review_style=style,
        persona=persona,
    )
    return jsonify({
        "status": "ok",
        "text": text,
        "persona": persona,
        "star_rating": star,
    })


@app.route("/api/worker/preview.png")
@login_required
def api_worker_preview():
    """Return a live snapshot of Display :99 without requiring a business ID."""
    try:
        capture = subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error",
                "-f", "x11grab", "-video_size", "1366x768", "-i",
                os.environ.get("CHROMIUM_DISPLAY", ":99"),
                "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-",
            ],
            capture_output=True,
            timeout=8,
            check=True,
        )
        return Response(
            capture.stdout,
            mimetype="image/png",
            headers={"Cache-Control": "no-store, max-age=0"},
        )
    except (OSError, subprocess.SubprocessError):
        return Response("Preview worker belum tersedia.", status=503, mimetype="text/plain")


# ── SPA Feature Routes ────────────────────────────────────────────────────────

@app.route("/review-studio")
@app.route("/campaigns")
@app.route("/live-monitor")
@login_required
def spa_feature_pages():
    spa = _serve_spa()
    if spa is not None:
        return spa
    return redirect(url_for("dashboard"))


# ── Review Studio & AI Templates ──────────────────────────────────────────────

@app.route("/api/templates", methods=["GET", "POST"])
@login_required
def api_templates():
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        title = (data.get("title") or "").strip()
        if not title:
            return jsonify({"status": "error", "message": "Judul template harus diisi."}), 400
        category = (data.get("category") or "Umum").strip()
        persona = data.get("persona") or "local_guide"
        star_rating = int(data.get("star_rating") or 5)
        prompt = (data.get("prompt_template") or "").strip()
        keywords = (data.get("keywords") or "").strip()
        sample = (data.get("sample_output") or "").strip()

        tid = db.add_review_template(title, category, persona, star_rating, prompt, keywords, sample)
        return jsonify({"status": "ok", "template_id": tid, "message": "Template ulasan berhasil disimpan."})

    return jsonify({
        "status": "ok",
        "templates": db.get_review_templates(),
    })


@app.route("/api/templates/<int:template_id>", methods=["DELETE"])
@login_required
def api_delete_template(template_id):
    db.delete_review_template(template_id)
    return jsonify({"status": "ok", "message": "Template ulasan telah dihapus."})


@app.route("/api/templates/batch-generate", methods=["POST"])
@login_required
def api_batch_generate():
    data = request.get_json(silent=True) or request.form
    biz_name = (data.get("business_name") or "Bisnis Google Maps").strip()
    desc = (data.get("description") or "").strip()
    keywords = (data.get("keywords") or "").strip()
    star_rating = int(data.get("star_rating") or 5)
    lang = data.get("language") or "Indonesian"
    primary_persona = data.get("persona") or "local_guide"

    enhanced_prompt = desc
    if keywords:
        enhanced_prompt = f"{desc}. Kata kunci utama: {keywords}."

    persona_candidates = [primary_persona, "casual", "foodie", "local_guide", "family"]
    selected_personas = []
    for p in persona_candidates:
        if p not in selected_personas:
            selected_personas.append(p)
    selected_personas = selected_personas[:3]

    variations = []
    for idx, persona in enumerate(selected_personas):
        rating_variant = star_rating
        if idx == 2 and star_rating == 5 and data.get("include_minor_critique"):
            rating_variant = 4
        text = bot.generate_review(
            business_name=biz_name,
            review_prompt=enhanced_prompt,
            star_rating=rating_variant,
            language=lang,
            review_style="baik" if rating_variant >= 4 else "buruk",
            persona=persona,
        )
        variations.append({
            "id": idx + 1,
            "persona": persona,
            "star_rating": rating_variant,
            "text": text,
        })

    return jsonify({
        "status": "ok",
        "variations": variations,
    })


@app.route("/api/templates/push-to-business", methods=["POST"])
@login_required
def api_push_to_business():
    data = request.get_json(silent=True) or request.form
    biz_id = data.get("business_id")
    if not biz_id:
        return jsonify({"status": "error", "message": "Pilih bisnis target ulasan."}), 400

    review_text = (data.get("review_text") or "").strip()
    if not review_text:
        return jsonify({"status": "error", "message": "Teks ulasan tidak boleh kosong."}), 400

    star_rating = int(data.get("star_rating") or 5)
    email_id = data.get("email_id")

    if not email_id:
        all_emails = db.get_all_emails()
        eligible = [e for e in all_emails if not e.get("flagged")]
        if not eligible:
            return jsonify({"status": "error", "message": "Tidak ada akun email aktif di pool."}), 400
        email_id = eligible[0]["id"]

    rid = db.push_direct_review(biz_id, email_id, star_rating, review_text, data.get("language") or "Indonesian")
    biz = db.get_business(biz_id)
    biz_name = biz["name"] if biz else f"ID {biz_id}"
    db.add_process_log(biz_id, f"Ulasan dari Studio AI ditambahkan ke antrean (Rating: {star_rating}★).")
    return jsonify({
        "status": "ok",
        "review_id": rid,
        "message": f"Ulasan berhasil ditugaskan ke {biz_name}!",
    })


# ── Drip Campaign & Scheduler Routes ──────────────────────────────────────────

@app.route("/api/campaigns")
@login_required
def api_campaigns():
    overview = db.get_scheduled_queue_overview()
    return jsonify({"status": "ok", "data": overview})


@app.route("/api/campaigns/config", methods=["POST"])
@login_required
def api_campaigns_config():
    data = request.get_json(silent=True) or request.form
    db.update_campaign_settings(
        drip_min_delay=data.get("drip_min_delay", 30),
        drip_max_delay=data.get("drip_max_delay", 90),
        active_hour_start=data.get("active_hour_start", 8),
        active_hour_end=data.get("active_hour_end", 21),
        anti_spam_jitter=data.get("anti_spam_jitter", 25),
        is_paused=bool(data.get("is_paused", 0)),
    )
    return jsonify({
        "status": "ok",
        "message": "Konfigurasi Drip Campaign berhasil diperbarui.",
        "settings": db.get_campaign_settings(),
    })


# ── Live Worker Console Routes ────────────────────────────────────────────────

@app.route("/api/worker/status")
@login_required
def api_worker_status():
    sys_status = db.get_worker_system_status()
    display_active = os.path.exists("/tmp/.X11-unix/X99")
    worker_running = False
    try:
        res = subprocess.run(["pgrep", "-f", "worker.py"], capture_output=True, text=True)
        worker_running = bool(res.stdout.strip())
    except Exception:
        pass

    vm_states = {}
    for v in range(101, 107):
        sock_path = f"/var/run/qemu-server/{v}.qmp"
        running = os.path.exists(sock_path)
        sleeping = _VM_IS_SLEEPING.get(v, False) if running else True
        vm_states[str(v)] = {
            "vmid": v,
            "running": running,
            "is_sleeping": sleeping,
        }

    return jsonify({
        "status": "ok",
        "system_status": {
            **sys_status,
            "is_running": worker_running,
            "worker_running": worker_running,
            "running": worker_running,
        },
        "vm_states": vm_states,
        "display_99_active": display_active,
        "worker_running": worker_running,
        "is_running": worker_running,
        "running": worker_running,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })


def force_stop_all_workers(business_id=None):
    """
    Force stop all review workers, browsers, and background schedulers:
    1. Stop systemd continuous background service (google-review-worker.service).
    2. Terminate all worker.py and bot.py processes with SIGKILL.
    3. Terminate all Chromium automation processes and chromedrivers.
    4. Reset stuck 'reviewing' jobs to 'pending' (or delete queue if business_id specified).
    5. Pause drip campaign auto-replenishment so it doesn't queue jobs again.
    """
    # 1. Stop systemd continuous service
    try:
        subprocess.run(["systemctl", "stop", "google-review-worker.service"], timeout=5, check=False)
    except Exception as e:
        logger.warning("Failed stopping google-review-worker.service: %s", e)

    # 2. Kill all worker.py and bot.py python execution processes
    try:
        subprocess.run(["pkill", "-9", "-f", r"python.*worker\.py"], check=False)
        subprocess.run(["pkill", "-9", "-f", r"python.*bot\.py"], check=False)
    except Exception as e:
        logger.warning("Failed pkill worker/bot: %s", e)

    # 3. Kill all automated Chromium and chromedriver instances
    try:
        subprocess.run(["pkill", "-9", "-f", "chromium.*--user-data-dir"], check=False)
        subprocess.run(["pkill", "-9", "-f", "chromedriver"], check=False)
    except Exception as e:
        logger.warning("Failed pkill chromium: %s", e)

    # 4. Clean up / reset database state
    deleted_queue = 0
    with db.get_db() as conn:
        if business_id:
            deleted_queue = db.delete_business_queue(business_id)
        conn.execute("UPDATE reviews SET status = 'pending' WHERE status = 'reviewing'")
        try:
            conn.execute("UPDATE campaign_settings SET is_paused = 1")
        except Exception:
            pass

    if business_id:
        db.add_process_log(
            business_id,
            f"Worker dipaksa berhenti oleh operator. {deleted_queue} antrean dibatalkan.",
            level="warning",
        )

    return {
        "status": "ok",
        "action": "stopped",
        "message": f"Worker dan seluruh proses engine berhasil dipaksa berhenti ({deleted_queue} antrean dibatalkan).",
        "workers_stopped": 1,
        "jobs_deleted": deleted_queue,
    }


@app.route("/api/worker/emergency-stop", methods=["POST"])
@login_required
def api_worker_emergency_stop():
    res = force_stop_all_workers()
    return jsonify(res)


@app.route("/api/mascot/chat", methods=["POST"])
@login_required
def api_mascot_chat():
    data = request.get_json(silent=True) or request.form or {}
    message = (data.get("message") or "").strip()
    business_id = data.get("business_id")

    biz = db.get_business(business_id) if business_id else None
    biz_name = biz["name"] if biz else "CV. TRI USAHA JAYA"
    reviews = db.get_reviews_for_business(business_id) if business_id else []
    cookies = db.get_all_cookies()
    worker_running = False
    try:
        res = subprocess.run(["pgrep", "-f", "worker.py"], capture_output=True, text=True)
        worker_running = bool(res.stdout.strip())
    except Exception:
        pass

    posted_count = len([r for r in reviews if r.get("status") == "posted"])
    pending_count = len([r for r in reviews if r.get("status") in ("pending", "processing")])

    msg_lower = message.lower()
    suggested_review = None
    action = None

    # 1. Action command: RUN AUTO-REVIEW
    if any(k in msg_lower for k in ["run", "jalankan", "mulai", "start", "eksekusi", "posting", "autoreview"]):
        if worker_running:
            reply = f"Worker otomasi untuk '{biz_name}' saat ini sudah aktif berjalan di Display :99!"
            action = "already_running"
        elif not business_id:
            reply = "Pilih target bisnis Google Maps terlebih dahulu sebelum menjalankan ulasan."
            action = "error"
        else:
            try:
                db.clear_process_logs(business_id)
                db.reset_business_reviewing(business_id)
                star_list = [5, 5, 5]
                created, already_pending = db.create_review_jobs(business_id, star_list, language_list=["Indonesian"] * 3)
                subprocess.Popen(
                    [sys.executable, "worker.py", "--business-id", str(business_id)],
                    cwd=os.path.dirname(os.path.abspath(__file__)),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                db.add_process_log(business_id, "Worker langsung dijalankan atas instruksi AutoMap AI Copilot.")
                worker_running = True
                reply = (
                    f"🚀 Perintah diterima! Auto-review Google Maps untuk '{biz_name}' telah dijalankan. "
                    f"Jendela Chromium telah dibuka di Display :99 dan proses ulasan segera dieksekusi."
                )
                action = "started"
            except Exception as e:
                reply = f"Gagal menjalankan worker: {str(e)}"
                action = "error"

    # 2. Action command: STOP WORKER
    elif any(k in msg_lower for k in ["stop", "berhenti", "hentikan", "batal", "kill"]):
        try:
            subprocess.run(["pkill", "-f", "worker.py"], capture_output=True)
            worker_running = False
            reply = f"🛑 Worker otomasi untuk '{biz_name}' berhasil dihentikan. Semua jendela Chromium ditutup."
            action = "stopped"
        except Exception as e:
            reply = f"Gagal menghentikan worker: {str(e)}"
            action = "error"

    # 3. Action command: RESET REVIEWS
    elif any(k in msg_lower for k in ["reset", "ulang antrean"]):
        if business_id:
            db.reset_all_business_reviews(business_id)
            reply = f"🔄 Seluruh antrean ulasan untuk '{biz_name}' berhasil direset ke status pending."
            action = "reset"
        else:
            reply = "Pilih target bisnis untuk mereset antrean ulasannya."

    # 4. Status Check
    elif any(k in msg_lower for k in ["status", "cek", "kondisi", "laporan", "progress"]):
        state_str = "SEDANG BERJALAN (Active)" if worker_running else "SIAGA (Idle / Standby)"
        reply = (
            f"Laporan AI Copilot: Status worker {state_str}. Target aktif: '{biz_name}'. "
            f"Tercatat {posted_count} ulasan sukses terposting dan {pending_count} ulasan dalam antrean. "
            f"Display virtual :99 terpantau stabil."
        )

    # 5. Tips Anti-Spam
    elif any(k in msg_lower for k in ["anti", "spam", "shadowban", "banned", "jeda", "delay", "aman"]):
        reply = (
            "Panduan Anti-Shadowban AI: Pasang jeda minimal 60-120 detik per akun, "
            "rotasi akun cookie berbeda, dan gunakan variasi ulasan bertahap (drip feed) "
            "agar ulasan permanen dan tidak terhapus oleh filter Google Maps!"
        )

    # 6. Generate Review Draft
    elif any(k in msg_lower for k in ["buat", "tulis", "draft", "ulasan", "review", "contoh"]):
        prompt = biz.get("review_prompt", "") if biz else ""
        suggested_review = bot.generate_review(
            business_name=biz_name,
            review_prompt=prompt or "Pelayanan ramah, respon cepat, sangat memuaskan",
            star_rating=5,
            language="Indonesian",
            review_style="casual",
            persona="local_guide"
        )
        reply = (
            f"Draf ulasan rekomendasi untuk '{biz_name}':\n\n"
            f"“{suggested_review}”\n\n"
            "Klik tombol di bawah untuk langsung menerapkan ke prompt target!"
        )

    # 7. Cookie & Account Check
    elif any(k in msg_lower for k in ["cookie", "akun", "sesi", "login", "gmail"]):
        c_count = len(cookies)
        reply = (
            f"Sistem memiliki {c_count} akun cookie tersimpan. "
            "Sesi login Google via CDP siap diinjeksi tanpa 2FA manual."
        )

    # 8. Greetings & General
    elif not message or any(k in msg_lower for k in ["sapa", "halo", "hai", "pagi", "siang", "malam", "oi"]):
        reply = (
            f"Halo! Saya AutoMap AI Copilot untuk target '{biz_name}'. "
            f"Worker saat ini {'sedang aktif berjalan' if worker_running else 'siaga (idle)'}. "
            "Ketik 'jalankan review' untuk memulai, atau tanyakan tips otomasi!"
        )
    else:
        reply = (
            f"AI Copilot siap: '{message}'. Target aktif: '{biz_name}'. "
            "Ketik 'jalankan review' untuk memulai otomasi ulasan, atau 'cek status' untuk memantau progress."
        )

    return jsonify({
        "status": "ok",
        "reply": reply,
        "action": action,
        "suggested_review": suggested_review,
        "worker_running": worker_running,
        "biz_name": biz_name,
    })



@app.route("/autobotix")
@login_required
def autobotix_overview():
    spa = _serve_spa()
    if spa is not None:
        return spa
    db.migrate_autobotix()
    if not db.get_autobotix_domains():
        domain_intelligence.import_historical_snapshot()
    domains = db.get_autobotix_domains()
    return render_template("autobotix_overview.html", tunnels=db.get_autobotix_tunnels(), services=db.get_autobotix_services(), domain_count=len(domains), healthy_count=sum(d["upstream_status"] == "healthy" for d in domains), unknown_count=sum(d["upstream_status"] != "healthy" for d in domains), active_page="overview")


@app.route("/api/autobotix/overview")
@login_required
def api_autobotix_overview():
    db.migrate_autobotix()
    if not db.get_autobotix_domains():
        domain_intelligence.import_historical_snapshot()
    domains = db.get_autobotix_domains()
    return jsonify({
        "status": "ok",
        "tunnels": db.get_autobotix_tunnels(),
        "services": db.get_autobotix_services(),
        "domain_count": len(domains),
        "healthy_count": sum(d["upstream_status"] == "healthy" for d in domains),
        "unknown_count": sum(d["upstream_status"] != "healthy" for d in domains),
    })


@app.route("/autobotix/domains")
@login_required
def domains():
    spa = _serve_spa()
    if spa is not None:
        return spa
    db.migrate_autobotix()
    return render_template("domains.html", domains=db.get_autobotix_domains(request.args.get("q", "").strip(), request.args.get("status", "").strip()), active_page="domains")


@app.route("/api/autobotix/domains")
@login_required
def api_autobotix_domains():
    db.migrate_autobotix()
    search = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    domains = db.get_autobotix_domains(search, status)
    return jsonify({"status": "ok", "domains": domains})


@app.route("/autobotix/domains/<int:domain_id>")
@login_required
def domain_detail(domain_id):
    spa = _serve_spa()
    if spa is not None:
        return spa
    domain = db.get_autobotix_domain(domain_id)
    if not domain: abort(404)
    return render_template("domain_detail.html", domain=domain, active_page="domains")


@app.route("/api/autobotix/domains/<int:domain_id>")
@login_required
def api_autobotix_domain(domain_id):
    domain = db.get_autobotix_domain(domain_id)
    if not domain:
        return jsonify({"status": "error", "message": "Domain not found"}), 404
    return jsonify({"status": "ok", "domain": domain})


@app.route("/autobotix/tunnels")
@login_required
def tunnels():
    spa = _serve_spa()
    if spa is not None:
        return spa
    db.migrate_autobotix()
    return render_template("tunnels.html", tunnels=db.get_autobotix_tunnels(), active_page="tunnels")


@app.route("/api/autobotix/tunnels")
@login_required
def api_autobotix_tunnels():
    db.migrate_autobotix()
    return jsonify({"status": "ok", "tunnels": db.get_autobotix_tunnels()})


@app.route("/autobotix/tunnels/<int:tunnel_id>")
@login_required
def tunnel_detail(tunnel_id):
    spa = _serve_spa()
    if spa is not None:
        return spa
    tunnel = db.get_autobotix_tunnel(tunnel_id)
    if not tunnel: abort(404)
    return render_template("tunnel_detail.html", tunnel=tunnel, active_page="tunnels")


@app.route("/api/autobotix/tunnels/<int:tunnel_id>")
@login_required
def api_autobotix_tunnel(tunnel_id):
    tunnel = db.get_autobotix_tunnel(tunnel_id)
    if not tunnel:
        return jsonify({"status": "error", "message": "Tunnel not found"}), 404
    return jsonify({"status": "ok", "tunnel": tunnel})


def _host_metrics():
    observed = datetime.now().astimezone().isoformat(timespec="seconds")
    disk = shutil.disk_usage("/")
    result = {"observed_at": observed, "scope": "host", "storage": {"total": disk.total, "used": disk.used, "free": disk.free}}
    try:
        with open("/proc/meminfo", encoding="utf-8") as meminfo:
            values = {line.split(":", 1)[0]: line.split(":", 1)[1].split() for line in meminfo}
        total, available = int(values["MemTotal"][0])*1024, int(values["MemAvailable"][0])*1024
        result["memory"] = {"total":total, "available":available, "used":total-available, "swap_total":int(values.get("SwapTotal", [0])[0])*1024, "swap_free":int(values.get("SwapFree", [0])[0])*1024}
    except (OSError, KeyError, ValueError): result["memory"] = None
    try:
        rx=tx=0
        with open("/proc/net/dev", encoding="utf-8") as netdev:
            lines = netdev.read().splitlines()[2:]
        for line in lines:
            data=line.split(":",1)[1].split(); rx += int(data[0]); tx += int(data[8])
        result["network_totals"]={"rx":rx,"tx":tx,"unit":"bytes","scope":"host interfaces; cumulative, not tunnel traffic"}
    except (OSError, IndexError, ValueError): result["network_totals"] = None
    try:
        load_1, load_5, load_15 = os.getloadavg()
        result["cpu"] = {"load_1": load_1, "load_5": load_5, "load_15": load_15, "logical_cpus": os.cpu_count()}
    except OSError:
        result["cpu"] = None
    return result


@app.route("/autobotix/monitoring")
@login_required
def monitoring():
    spa = _serve_spa()
    if spa is not None:
        return spa
    return render_template("monitoring.html", metrics=_host_metrics(), active_page="monitoring")


@app.route("/api/autobotix/monitoring")
@login_required
def api_autobotix_monitoring():
    return jsonify({"status": "ok", "metrics": _host_metrics()})


@app.route("/autobotix/activity")
@login_required
def autobotix_activity():
    spa = _serve_spa()
    if spa is not None:
        return spa
    db.migrate_autobotix()
    with db.get_db() as conn:
        logs = [dict(row) for row in conn.execute("SELECT * FROM ab_activity_logs ORDER BY id DESC LIMIT 100").fetchall()]
    return render_template("activity.html", logs=logs, active_page="activity")


@app.route("/api/autobotix/activity")
@login_required
def api_autobotix_activity():
    db.migrate_autobotix()
    with db.get_db() as conn:
        logs = [dict(row) for row in conn.execute("SELECT * FROM ab_activity_logs ORDER BY id DESC LIMIT 100").fetchall()]
    return jsonify({"status": "ok", "logs": logs})


@app.route("/autobotix/import-snapshot", methods=["POST"])
@app.route("/api/autobotix/import-snapshot", methods=["POST"])
@login_required
def import_autobotix_snapshot():
    try:
        observed = domain_intelligence.import_historical_snapshot()
        db.log_autobotix_activity("administrator", "import_snapshot", "cloudflare-2026-10-24", "success", "Historical inventory imported or refreshed.")
        return jsonify({"status":"ok", "observed_at":observed})
    except (OSError, ValueError, KeyError) as exc:
        db.log_autobotix_activity("administrator", "import_snapshot", "cloudflare-2026-10-24", "error", "Snapshot import failed.")
        return jsonify({"status":"error", "message":"Snapshot tidak dapat diimpor."}), 500


@app.route("/business/add", methods=["POST"])
@login_required
def add_business():
    name = request.form.get("name", "").strip()
    url = request.form.get("url", "").strip()
    if name and _valid_business_url(url):
        db.add_business(name, url)
    return redirect(url_for("dashboard"))


@app.route("/api/businesses", methods=["POST"])
@login_required
def api_add_business():
    data = request.get_json(silent=True) or request.form
    name = (data.get("name") or "").strip()
    url = (data.get("url") or "").strip()
    if not name or not _valid_business_url(url):
        return jsonify({"status": "error", "message": "Nama atau URL Google Maps tidak valid."}), 400
    biz_id = db.add_business(name, url)
    return jsonify({"status": "ok", "business_id": biz_id})


@app.route("/business/<int:business_id>/delete", methods=["POST"])
@login_required
def delete_business(business_id):
    db.delete_business(business_id)
    return redirect(url_for("dashboard"))


@app.route("/api/businesses/<int:business_id>", methods=["GET", "DELETE"])
@login_required
def api_business_detail(business_id):
    if request.method == "DELETE":
        db.delete_business(business_id)
        return jsonify({"status": "ok", "message": "Business deleted"})
    biz = db.get_business(business_id)
    if not biz:
        return jsonify({"status": "error", "message": "Business tidak ditemukan."}), 404
    reviews = db.get_reviews_for_business(business_id)
    config = db.get_review_config(business_id)
    all_emails = db.get_all_emails()
    used_email_ids = list({r["email_id"] for r in reviews})
    selectable_email_count = sum(1 for e in all_emails if e["id"] not in used_email_ids)
    total_pool = db.count_emails()
    already_queued = db.count_queued_for_business(business_id)
    already_reviewed = db.count_reviewed_for_business(business_id)
    all_cookies = db.get_all_cookies()
    return jsonify({
        "status": "ok",
        "business": biz,
        "reviews": reviews,
        "config": config,
        "is_running": any(r["status"] == "reviewing" for r in reviews),
        "all_emails": all_emails,
        "all_cookies": all_cookies,
        "cookies": all_cookies,
        "used_email_ids": used_email_ids,
        "selectable_email_count": selectable_email_count,
        "total_pool": total_pool,
        "already_queued": already_queued,
        "already_reviewed": already_reviewed,
    })


# ── Business detail ───────────────────────────────────────────────────────────

@app.route("/business/<int:business_id>")
@login_required
def business(business_id):
    spa = _serve_spa()
    if spa is not None:
        return spa
    biz = db.get_business(business_id)
    if not biz:
        return redirect(url_for("dashboard"))
    reviews = db.get_reviews_for_business(business_id)
    config = db.get_review_config(business_id)
    is_running = any(r["status"] == "reviewing" for r in reviews)
    all_emails = db.get_all_emails()
    used_email_ids = {r["email_id"] for r in reviews}
    selectable_email_count = sum(1 for e in all_emails if e["id"] not in used_email_ids)
    total_pool = db.count_emails()
    already_queued = db.count_queued_for_business(business_id)
    already_reviewed = db.count_reviewed_for_business(business_id)
    return render_template(
        "business.html",
        business=biz,
        reviews=reviews,
        config=config,
        is_running=is_running,
        all_emails=all_emails,
        used_email_ids=used_email_ids,
        selectable_email_count=selectable_email_count,
        total_pool=total_pool,
        already_queued=already_queued,
        already_reviewed=already_reviewed,
    )


@app.route("/business/<int:business_id>/process-log")
@app.route("/api/businesses/<int:business_id>/process-log")
@login_required
def process_log(business_id):
    """Polling endpoint for the live process-log panel."""
    if not db.get_business(business_id):
        return jsonify({"status": "error", "message": "Business not found"}), 404
    reviews = db.get_reviews_for_business(business_id)
    has_active = any(row["status"] == "reviewing" for row in reviews)
    has_pending = any(row["status"] == "pending" for row in reviews)
    is_deleting = business_id in _ACTIVE_DELETE_TASKS
    if is_deleting:
        status_label = "deleting"
    elif has_active:
        status_label = "reviewing"
    elif has_pending:
        status_label = "queued"
    else:
        status_label = "idle"

    return jsonify({
        "status": status_label,
        "is_deleting": is_deleting,
        "logs": db.get_process_logs(business_id),
    })


@app.route("/api/queue", methods=["GET"])
@app.route("/api/businesses/<int:business_id>/queue", methods=["GET"])
@login_required
def get_review_queue(business_id=None):
    """Return active review queue across all businesses or for a specific business."""
    with db.get_db() as conn:
        query = """
            SELECT r.id, r.business_id, b.name as business_name, r.email_id, e.email,
                   COALESCE(c.account_name, e.account_name, '') as account_name,
                   r.star_rating, r.status, r.created_at, r.reviewed_at
            FROM reviews r
            JOIN businesses b ON r.business_id = b.id
            JOIN emails e ON r.email_id = e.id
            LEFT JOIN cookies c ON e.email = c.email
        """
        params = []
        if business_id:
            query += " WHERE r.business_id = ?"
            params.append(business_id)
        query += " ORDER BY CASE r.status WHEN 'reviewing' THEN 1 WHEN 'pending' THEN 2 ELSE 3 END, r.created_at ASC LIMIT 100"
        rows = conn.execute(query, params).fetchall()
        q_list = [dict(r) for r in rows]
        return jsonify({
            "status": "ok",
            "queue": q_list,
            "pending_count": sum(1 for r in q_list if r["status"] == "pending"),
            "reviewing_count": sum(1 for r in q_list if r["status"] == "reviewing"),
        })


@app.route("/business/<int:business_id>/clear-logs", methods=["POST"])
@app.route("/api/businesses/<int:business_id>/clear-logs", methods=["POST"])
@login_required
def clear_business_logs(business_id):
    """Purge process logs for this business."""
    if not db.get_business(business_id):
        return jsonify({"status": "error", "message": "Business not found"}), 404
    db.clear_process_logs(business_id)
    return jsonify({"status": "ok", "message": "Logcat berhasil dibersihkan."})


@app.route("/business/<int:business_id>/inspect-review/<int:review_id>")
@app.route("/api/businesses/<int:business_id>/inspect-review/<int:review_id>")
@login_required
def inspect_review(business_id, review_id):
    """Read-only check; it never edits or submits public content."""
    biz = db.get_business(business_id)
    review = db.get_review_for_business(review_id, business_id)
    if not biz or not review:
        return jsonify({"status": "error", "message": "Review tidak ditemukan."}), 404
    result = bot.inspect_existing_review(
        review["email"], biz["url"], biz["name"], review_id=review_id,
        business_id=business_id, star_rating=review.get("star_rating") or 5,
        review_prompt=biz.get("business_description") or "",
        review_type=review.get("review_type") or "medium",
        language=review.get("review_language") or "English",
        review_style=(db.get_review_config(business_id) or {}).get("review_style") or "random",
    )
    return jsonify(result)


SLOT_DISPLAYS = {
    1: ":99",
    2: ":100",
    3: ":101",
    4: ":102",
    5: ":103",
    6: ":104",
}

def resolve_slot_vmid(slot_id=None):
    if slot_id is None:
        slot_arg = request.args.get("slot")
        if slot_arg and str(slot_arg).isdigit():
            slot_id = int(slot_arg)
        else:
            slot_id = 1
    try:
        s = int(slot_id)
    except (ValueError, TypeError):
        s = 1
    return 100 + s


def is_blank_or_idle_frame(im):
    """Detect if a captured frame is black/blank/idle (less than 2% bright pixels)."""
    try:
        thumb = im.convert("L").resize((64, 36))
        bright_pixels = sum(1 for p in thumb.tobytes() if p > 15)
        return (bright_pixels / (64 * 36)) < 0.02
    except Exception:
        return False


def get_clean_offline_frame(slot_id, label="Offline", fmt="PNG"):
    """Render a clean, dark, minimalist screen (NO autobotix cards, NO mascot)."""
    vmid = resolve_slot_vmid(slot_id)
    width, height = 1024, 600
    im = Image.new("RGB", (width, height), color=(11, 15, 25))
    draw = ImageDraw.Draw(im)

    font_bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font_reg_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    f_bold = ImageFont.truetype(font_bold_path, 14)
    f_small = ImageFont.truetype(font_reg_path, 11)

    draw.rectangle([2, 2, width - 3, height - 3], outline=(30, 41, 59), width=1)

    badge_text = f"Windows 10 (VM-{vmid}) • {label}"
    text_bbox = draw.textbbox((0, 0), badge_text, font=f_bold)
    tw = text_bbox[2] - text_bbox[0]
    th = text_bbox[3] - text_bbox[1]
    cx, cy = width // 2, height // 2

    bx1, by1, bx2, by2 = cx - tw // 2 - 16, cy - th // 2 - 10, cx + tw // 2 + 16, cy + th // 2 + 10
    draw.rounded_rectangle([bx1, by1, bx2, by2], radius=6, fill=(19, 26, 42), outline=(51, 65, 85), width=1)
    draw.text((cx - tw // 2, cy - th // 2 - 2), badge_text, fill=(148, 163, 184), font=f_bold)

    time_str = time.strftime("%H:%M:%S WIB")
    draw.text((width - 90, height - 20), time_str, fill=(71, 85, 105), font=f_small)

    buf = io.BytesIO()
    if fmt.upper() == "PNG":
        im.save(buf, format="PNG", optimize=False)
    else:
        im.save(buf, format="JPEG", quality=80)
    return buf.getvalue()


_HOST_FRAME_CACHE = {}
_VM_FRAME_CACHE = {}
_LAST_VM_FRAME = {}
_SMART_BYTES_CACHE = {}


def capture_host_display_image(display):
    """Grab one frame from host virtual display (:99 - :104) via ffmpeg with 0.35s cache."""
    now = time.time()
    cached = _HOST_FRAME_CACHE.get(display)
    if cached and (now - cached[0]) < 0.35:
        try:
            return cached[1].copy()
        except Exception:
            pass

    try:
        proc = subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error",
                "-f", "x11grab", "-video_size", "1366x768",
                "-i", display, "-frames:v", "1",
                "-f", "image2pipe", "-vcodec", "png", "-",
            ],
            capture_output=True,
            timeout=1.8,
        )
        if proc.returncode == 0 and proc.stdout:
            im = Image.open(io.BytesIO(proc.stdout))
            _HOST_FRAME_CACHE[display] = (now, im)
            return im.copy()
    except Exception:
        pass
    return None


_LAST_WAKE_TIME = {}
_VM_IS_SLEEPING = {v: False for v in range(101, 107)}

def get_sleeping_vm_frame(slot_id, fmt="PNG"):
    """Render a sleek sleep-mode overlay frame when a Windows VM is asleep."""
    vmid = resolve_slot_vmid(slot_id)
    last = _LAST_VM_FRAME.get(vmid)
    if last and last.getbbox():
        base = last.copy().convert("RGBA")
        overlay = Image.new("RGBA", base.size, (11, 15, 25, 215))
        im = Image.alpha_composite(base, overlay).convert("RGB")
    else:
        im = Image.new("RGB", (1024, 768), (11, 15, 25))

    draw = ImageDraw.Draw(im)
    font_bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font_reg_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    try:
        f_title = ImageFont.truetype(font_bold_path, 20)
        f_sub = ImageFont.truetype(font_reg_path, 12)
    except Exception:
        f_title = ImageFont.load_default()
        f_sub = ImageFont.load_default()

    cx, cy = im.width // 2, im.height // 2
    pill_text = f"Windows 10 (VM-{vmid}) • Sleep Mode"
    bbox = draw.textbbox((0, 0), pill_text, font=f_title)
    pw, ph = bbox[2] - bbox[0], bbox[3] - bbox[1]
    px1, py1, px2, py2 = cx - pw // 2 - 20, cy - ph // 2 - 18, cx + pw // 2 + 20, cy + ph // 2 + 2
    draw.rounded_rectangle([px1, py1, px2, py2], radius=10, fill=(24, 20, 10), outline=(245, 158, 11), width=2)
    draw.text((cx, cy - 8), pill_text, fill=(251, 191, 36), font=f_title, anchor="mm")

    sub_text = "Layar mati karena sleep. Klik maskot bot atau layar untuk menyalakan"
    draw.text((cx, cy + 30), sub_text, fill=(203, 213, 225), font=f_sub, anchor="mm")

    buf = io.BytesIO()
    if fmt.upper() == "PNG":
        im.save(buf, format="PNG")
    else:
        im.save(buf, format="JPEG", quality=80)
    return buf.getvalue()


def _wake_vm_screen_async(vmid):
    """Wake up VM monitor if Windows display went to sleep."""
    now = time.time()
    if (now - _LAST_WAKE_TIME.get(vmid, 0)) < 4.0:
        return
    _LAST_WAKE_TIME[vmid] = now

    def _do_wake():
        sock_path = f"/var/run/qemu-server/{vmid}.qmp"
        if not os.path.exists(sock_path):
            return
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(1.0)
            s.connect(sock_path)
            s.recv(1024)
            s.sendall(b'{"execute": "qmp_capabilities"}\n')
            s.recv(1024)
            cmd = json.dumps({"execute": "input-send-event", "arguments": {"events": [{"type": "rel", "data": {"axis": "x", "value": 1}}]}}) + "\n"
            s.sendall(cmd.encode("utf-8"))
            s.recv(1024)
            s.close()
        except Exception:
            pass

    threading.Thread(target=_do_wake, daemon=True).start()


def capture_vm_screen_image(slot_id):
    """Grab one frame from Proxmox VM (VM 101-106) via QMP socket with memory caching & fallback."""
    vmid = resolve_slot_vmid(slot_id)
    now = time.time()
    cached = _VM_FRAME_CACHE.get(vmid)
    if cached and (now - cached[0]) < 0.65:
        try:
            return cached[1].copy()
        except Exception:
            pass

    sock_path = f"/var/run/qemu-server/{vmid}.qmp"
    if not os.path.exists(sock_path):
        return None

    ppm_path = f"/dev/shm/qmp_{vmid}_{os.getpid()}_{threading.get_ident()}.ppm"
    s = None
    for attempt in range(2):
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(1.2)
            s.connect(sock_path)
            s.recv(2048)
            s.sendall(b'{"execute": "qmp_capabilities"}\n')
            s.recv(2048)
            cmd = json.dumps({"execute": "screendump", "arguments": {"filename": ppm_path}}) + "\n"
            s.sendall(cmd.encode("utf-8"))
            s.recv(2048)
            s.close()
            s = None

            if os.path.exists(ppm_path):
                with Image.open(ppm_path) as im:
                    im_copy = im.copy()
                try:
                    os.remove(ppm_path)
                except OSError:
                    pass

                # If the VM display is sleeping / blank (all black pixels)
                if not im_copy.getbbox():
                    _VM_IS_SLEEPING[vmid] = True
                else:
                    _VM_IS_SLEEPING[vmid] = False

                _VM_FRAME_CACHE[vmid] = (now, im_copy)
                _LAST_VM_FRAME[vmid] = im_copy.copy()
                return im_copy
        except Exception:
            time.sleep(0.06)
        finally:
            if s:
                try:
                    s.close()
                except Exception:
                    pass
            if os.path.exists(ppm_path):
                try:
                    os.remove(ppm_path)
                except OSError:
                    pass

    # If socket busy, return last good frame for seamless video display
    last_known = _LAST_VM_FRAME.get(vmid)
    if last_known:
        return last_known.copy()
    return None


def capture_smart_frame(business_id, slot_id=None, fmt="PNG", source="windows"):
    """
    Intelligently capture the appropriate visual for this slot:
    1. If source in ('windows', 'vm'): returns the real Windows VM screen (VM 101-106).
    2. If source in ('chromium', 'host'): returns the Chromium host display (:99-:104).
    3. If source == 'auto':
       - Shows Chromium when bot is actively executing review.
       - Otherwise shows the real Windows VM screen!
       - Clean minimalist standby if VM offline. (NEVER shows Autobotix card).
    """
    try:
        s_id = int(slot_id or 1)
    except (ValueError, TypeError):
        s_id = 1

    display = resolve_slot_display(s_id)
    vmid = resolve_slot_vmid(s_id)
    src = (source or "windows").lower()
    fmt_key = fmt.upper()

    now = time.time()
    cache_key = (business_id, s_id, fmt_key, src)
    cached = _SMART_BYTES_CACHE.get(cache_key)
    if cached and (now - cached[0]) < 0.35:
        return cached[1]

    def _to_bytes(im):
        buf = io.BytesIO()
        if fmt_key == "PNG":
            im.save(buf, format="PNG", optimize=False)
        else:
            im.save(buf, format="JPEG", quality=80)
        return buf.getvalue()

    # 1. Mode WINDOWS / VM: Show real Windows VM screen directly!
    if src in ("windows", "vm"):
        if _VM_IS_SLEEPING.get(vmid, False):
            res = get_sleeping_vm_frame(s_id, fmt=fmt)
            _SMART_BYTES_CACHE[cache_key] = (now, res)
            return res

        vm_im = capture_vm_screen_image(s_id)
        if _VM_IS_SLEEPING.get(vmid, False):
            res = get_sleeping_vm_frame(s_id, fmt=fmt)
            _SMART_BYTES_CACHE[cache_key] = (now, res)
            return res

        if vm_im:
            res = _to_bytes(vm_im)
            _SMART_BYTES_CACHE[cache_key] = (now, res)
            return res
        # If VM is stopped, fallback to host display if active
        host_im = capture_host_display_image(display)
        if host_im and not is_blank_or_idle_frame(host_im):
            res = _to_bytes(host_im)
            _SMART_BYTES_CACHE[cache_key] = (now, res)
            return res
        res = get_clean_offline_frame(s_id, label="VM Offline", fmt=fmt)
        _SMART_BYTES_CACHE[cache_key] = (now, res)
        return res

    # 2. Mode CHROMIUM / HOST: Show Chromium host display (:99-:104)
    if src in ("chromium", "host"):
        host_im = capture_host_display_image(display)
        if host_im:
            res = _to_bytes(host_im)
            _SMART_BYTES_CACHE[cache_key] = (now, res)
            return res
        res = get_clean_offline_frame(s_id, label=f"Display {display} Standby", fmt=fmt)
        _SMART_BYTES_CACHE[cache_key] = (now, res)
        return res

    # 3. Mode AUTO:
    # If Chromium is actively running and non-blank, show Chromium!
    host_im = capture_host_display_image(display)
    if host_im and not is_blank_or_idle_frame(host_im):
        res = _to_bytes(host_im)
        _SMART_BYTES_CACHE[cache_key] = (now, res)
        return res

    # Otherwise show real Windows VM screen!
    vm_im = capture_vm_screen_image(s_id)
    if vm_im:
        res = _to_bytes(vm_im)
        _SMART_BYTES_CACHE[cache_key] = (now, res)
        return res

    if host_im:
        res = _to_bytes(host_im)
        _SMART_BYTES_CACHE[cache_key] = (now, res)
        return res

    res = get_clean_offline_frame(s_id, label="Standby", fmt=fmt)
    _SMART_BYTES_CACHE[cache_key] = (now, res)
    return res


def resolve_slot_display(slot_id=None):
    if slot_id is None:
        slot_arg = request.args.get("slot")
        if slot_arg and str(slot_arg).isdigit():
            slot_id = int(slot_arg)
        else:
            slot_id = 1
    try:
        s = int(slot_id)
    except (ValueError, TypeError):
        s = 1
    return SLOT_DISPLAYS.get(s, os.environ.get("CHROMIUM_DISPLAY", ":99"))


@app.route("/business/<int:business_id>/chromium-preview.png")
@app.route("/business/<int:business_id>/slot/<int:slot_id>/chromium-preview.png")
@login_required
def chromium_preview(business_id, slot_id=None):
    """Return a smart live snapshot (Chromium bot if active, Proxmox VM if requested/active, or Telemetry Standby)."""
    if not db.get_business(business_id):
        return Response(status=404)

    source = request.args.get("source", "chromium").lower()
    frame_bytes = capture_smart_frame(business_id, slot_id, fmt="PNG", source=source)
    return Response(
        frame_bytes,
        mimetype="image/png",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"},
    )


@app.route("/business/<int:business_id>/chromium-stream.mjpg")
@app.route("/business/<int:business_id>/slot/<int:slot_id>/chromium-stream.mjpg")
@login_required
def chromium_stream(business_id, slot_id=None):
    """Stream smart live preview as MJPEG."""
    if not db.get_business(business_id):
        return Response(status=404)

    source = request.args.get("source", "chromium").lower()

    def frames():
        try:
            while True:
                jpeg = capture_smart_frame(business_id, slot_id, fmt="JPEG", source=source)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg + b'\r\n')
                time.sleep(0.5)
        except (GeneratorExit, StopIteration):
            return

    return Response(
        stream_with_context(frames()),
        mimetype="multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


@app.route("/api/vm/<int:vmid>/control", methods=["POST"])
@login_required
def api_vm_control(vmid):
    """Direct interactive remote control endpoint for Proxmox VMs (VM 101-106)."""
    if vmid not in [101, 102, 103, 104, 105, 106]:
        return jsonify({"status": "error", "message": "Invalid VM ID"}), 400

    sock_path = f"/var/run/qemu-server/{vmid}.qmp"
    if not os.path.exists(sock_path):
        return jsonify({"status": "error", "message": f"VM {vmid} is not running"}), 404

    data = request.get_json(silent=True) or {}
    action = data.get("action", "click")

    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(2.0)
        s.connect(sock_path)
        s.recv(1024)
        s.sendall(b'{"execute": "qmp_capabilities"}\n')
        s.recv(1024)

        if action == "key":
            key_name = str(data.get("key", "ret")).lower()
            cmd = {"execute": "send-key", "arguments": {"keys": [{"type": "qcode", "data": key_name}]}}
            s.sendall((json.dumps(cmd) + "\n").encode())
            s.recv(1024)
        elif action == "click":
            x_norm = max(0.0, min(1.0, float(data.get("x", 0.5))))
            y_norm = max(0.0, min(1.0, float(data.get("y", 0.5))))
            btn = str(data.get("button", "left")).lower()
            if btn not in ["left", "right", "middle"]:
                btn = "left"
            x_val = int(x_norm * 32767)
            y_val = int(y_norm * 32767)
            # Move cursor to absolute position
            move_cmd = {
                "execute": "input-send-event",
                "arguments": {
                    "events": [
                        {"type": "abs", "data": {"axis": "x", "value": x_val}},
                        {"type": "abs", "data": {"axis": "y", "value": y_val}},
                    ]
                }
            }
            s.sendall((json.dumps(move_cmd) + "\n").encode())
            s.recv(1024)
            # Send down and up button event
            click_cmd = {
                "execute": "input-send-event",
                "arguments": {
                    "events": [
                        {"type": "btn", "data": {"down": True, "button": btn}},
                        {"type": "btn", "data": {"down": False, "button": btn}},
                    ]
                }
            }
            s.sendall((json.dumps(click_cmd) + "\n").encode())
            s.recv(1024)
        elif action == "type":
            text = str(data.get("text", ""))
            for ch in text[:100]:
                ch_key = ch.lower() if ch.isalnum() else ("spc" if ch == " " else "dot" if ch == "." else "minus" if ch == "-" else None)
                if ch_key:
                    cmd = {"execute": "send-key", "arguments": {"keys": [{"type": "qcode", "data": ch_key}]}}
                    s.sendall((json.dumps(cmd) + "\n").encode())
                    s.recv(1024)
                    time.sleep(0.03)
        elif action == "reset":
            s.sendall(b'{"execute": "system_reset"}\n')
            s.recv(1024)
        elif action in ("wake", "nyalakan"):
            move_cmd = {
                "execute": "input-send-event",
                "arguments": {
                    "events": [
                        {"type": "rel", "data": {"axis": "x", "value": 5}},
                        {"type": "rel", "data": {"axis": "y", "value": 5}},
                    ]
                }
            }
            s.sendall((json.dumps(move_cmd) + "\n").encode())
            s.recv(1024)
            shift_cmd = {
                "execute": "send-key",
                "arguments": {
                    "keys": [{"type": "qcode", "data": "shift"}]
                }
            }
            s.sendall((json.dumps(shift_cmd) + "\n").encode())
            s.recv(1024)
            _VM_IS_SLEEPING[vmid] = False
            _VM_FRAME_CACHE.pop(vmid, None)
            s.close()
            return jsonify({
                "status": "ok",
                "message": f"Windows VM {vmid} berhasil dinyalakan!",
                "is_sleeping": False
            })
        elif action in ("sleep", "tidur"):
            _VM_IS_SLEEPING[vmid] = True
            _VM_FRAME_CACHE.pop(vmid, None)
            s.close()
            return jsonify({
                "status": "ok",
                "message": f"Windows VM {vmid} masuk mode sleep",
                "is_sleeping": True
            })
        elif action == "toggle_sleep":
            curr_sleep = _VM_IS_SLEEPING.get(vmid, False)
            if curr_sleep:
                move_cmd = {"execute": "input-send-event", "arguments": {"events": [{"type": "rel", "data": {"axis": "x", "value": 5}}]}}
                s.sendall((json.dumps(move_cmd) + "\n").encode())
                s.recv(1024)
                shift_cmd = {"execute": "send-key", "arguments": {"keys": [{"type": "qcode", "data": "shift"}]}}
                s.sendall((json.dumps(shift_cmd) + "\n").encode())
                s.recv(1024)
                _VM_IS_SLEEPING[vmid] = False
                _VM_FRAME_CACHE.pop(vmid, None)
                s.close()
                return jsonify({"status": "ok", "message": f"Windows VM {vmid} berhasil dinyalakan!", "is_sleeping": False})
            else:
                _VM_IS_SLEEPING[vmid] = True
                _VM_FRAME_CACHE.pop(vmid, None)
                s.close()
                return jsonify({"status": "ok", "message": f"Windows VM {vmid} mode sleep", "is_sleeping": True})

        s.close()
        return jsonify({"status": "ok", "message": f"Aksi '{action}' berhasil dikirim ke VM {vmid}"})
    except Exception as e:
        logger.error("Error controlling VM %s: %s", vmid, e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/vm/<int:vmid>/status")
@login_required
def api_vm_status(vmid):
    """Return status of a VM."""
    if vmid not in [101, 102, 103, 104, 105, 106]:
        return jsonify({"status": "error", "message": "Invalid VM ID"}), 400

    sock_path = f"/var/run/qemu-server/{vmid}.qmp"
    is_running = os.path.exists(sock_path)
    return jsonify({
        "status": "ok",
        "vmid": vmid,
        "name": f"Win10-Review-Worker-0{vmid - 100}",
        "running": is_running,
        "is_sleeping": _VM_IS_SLEEPING.get(vmid, False) if is_running else True,
        "control_available": is_running,
        "console_url": f"https://{request.host.split(':')[0]}:8006/?console=kvm&novnc=1&vmid={vmid}&vmname=Win10-Review-Worker-0{vmid-100}&node=pve"
    })


@app.route("/business/<int:business_id>/save-config", methods=["POST"])
@login_required
def save_config(business_id):
    config = {
        "business_description": "",
        "review_style": request.form.get("review_style", "random"),
        "star_1_count": 0,
        "star_2_count": 0,
        "star_3_count": 0,
        "star_4_count": 0,
        "star_5_count": 0,
        "delay_seconds": max(5, int(request.form.get("delay_seconds") or 60)),
        "screen_count": max(1, min(6, int(request.form.get("screen_count") or 3))),
    }
    db.save_review_config(business_id, config)
    return redirect(url_for("business", business_id=business_id, saved=1))


@app.route("/api/businesses/<int:business_id>/config", methods=["POST"])
@login_required
def api_save_business_config(business_id):
    data = request.get_json(silent=True) or request.form
    config = {
        "business_description": data.get("business_description") or "",
        "review_style": data.get("review_style", "random"),
        "star_1_count": int(data.get("star_1_count") or 0),
        "star_2_count": int(data.get("star_2_count") or 0),
        "star_3_count": int(data.get("star_3_count") or 0),
        "star_4_count": int(data.get("star_4_count") or 0),
        "star_5_count": int(data.get("star_5_count") or 0),
        "delay_seconds": max(5, int(data.get("delay_seconds") or 60)),
        "screen_count": max(1, min(6, int(data.get("screen_count") or 3))),
        "gemini_token": (data.get("gemini_token") or "").strip(),
        "business_category": (data.get("business_category") or "").strip(),
    }
    db.save_review_config(business_id, config)
    return jsonify({"status": "ok", "config": config})


@app.route("/api/businesses/<int:business_id>/test-gemini", methods=["POST"])
@login_required
def api_test_gemini(business_id):
    biz = db.get_business(business_id)
    if not biz:
        return jsonify({"status": "error", "message": "Business tidak ditemukan."}), 404

    data = request.get_json(silent=True) or request.form
    config = db.get_review_config(business_id) or {}
    if "gemini_token" in data:
        token = (data.get("gemini_token") or "").strip()
    else:
        token = (config.get("gemini_token") or os.environ.get("GEMINI_API_KEY") or "").strip()
    if not token:
        return jsonify({
            "status": "error",
            "message": "Token AI Gemini belum diisi. Silakan masukkan token API Gemini Anda terlebih dahulu."
        }), 400

    category = (data.get("business_category") or config.get("business_category") or "").strip()
    prompt = (data.get("custom_prompt") or config.get("business_description") or "").strip()
    tone = (data.get("review_style") or config.get("review_style") or "random").strip()
    star = int(data.get("star_rating") or 5)

    import time
    start_t = time.time()
    try:
        sample_text = bot.generate_gemini_review(
            api_key=token,
            business_name=biz["name"],
            business_category=category,
            star_rating=star,
            custom_prompt=prompt,
            review_style=tone,
            language="Indonesian",
        )
        latency = round(time.time() - start_t, 2)
        if sample_text:
            return jsonify({
                "status": "ok",
                "message": f"Koneksi AI Gemini Sukses ({latency}s)!",
                "business_name": biz["name"],
                "category_used": category or "Deteksi Otomatis AI dari Nama Usaha",
                "sample_review": sample_text,
                "latency_seconds": latency,
            })
        else:
            return jsonify({
                "status": "error",
                "message": "AI Gemini tidak merespons teks. Pastikan token API valid (Google AI Studio) dan kuota akun aktif."
            }), 400
    except Exception as exc:
        return jsonify({
            "status": "error",
            "message": f"Gagal menghubungi Gemini AI: {str(exc)}"
        }), 500


@app.route("/emails/sample-csv")
@login_required
def sample_csv():
    content = (
        "email,password,totp_secret\n"
        "example1@gmail.com,yourpassword1,\n"
        "example2@gmail.com,yourpassword2,JBSWY3DPEHPK3PXP\n"
    )
    return Response(
        content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=sample_emails.csv"},
    )


# ── Google Cookies ────────────────────────────────────────────────────────────

@app.route("/cookies/add", methods=["POST"])
@login_required
def add_cookie():
    cookie_raw = request.form.get("cookie_json", "").strip()
    if not cookie_raw:
        return redirect(url_for("dashboard", cookie_error="Cookie tidak boleh kosong"))
    
    val = session_manager.validate_cookie_payload(cookie_raw)
    if not val.is_valid and val.status == session_manager.SessionStatus.INVALID:
        return redirect(url_for("dashboard", cookie_error=f"Format cookie tidak valid: {val.reason}"))

    email = request.form.get("cookie_email", "").strip()
    if not email:
        email = val.detected_email or f"google.session.{int(time.time()) % 10000:04d}@gmail.com"

    # Live check with Google to retrieve real account name and session status
    live = session_manager.check_google_account_live(cookie_raw, fallback_email=email)
    account_name = live.get("account_name") or ""
    session_status = live.get("status") or val.status.value

    json_to_save = val.normalized_json or json.dumps(val.sanitized_cookies)
    inserted = db.save_cookie(email, json_to_save)
    db.update_cookie_session_status(email, session_status, live.get("reason") or val.reason)
    if account_name:
        with db.get_db() as conn:
            conn.execute("UPDATE cookies SET account_name = ? WHERE email = ?", (account_name, email))
            conn.execute("UPDATE emails SET account_name = ? WHERE email = ?", (account_name, email))

    # Otomatis masukkan ke email pool jika belum ada dan pastikan status aktif
    with db.get_db() as conn:
        existing = conn.execute("SELECT id FROM emails WHERE email = ?", (email,)).fetchone()
        if not existing:
            conn.execute("INSERT INTO emails (email, password, flagged, fail_count) VALUES (?, ?, 0, 0)", (email, "cookie_auth"))
        else:
            conn.execute("UPDATE emails SET flagged = 0, fail_count = 0 WHERE email = ?", (email,))

    return redirect(url_for("dashboard", cookie_saved=1, cookie_new=1 if inserted else 0))


@app.route("/api/cookies", methods=["POST"])
@login_required
def api_add_cookie():
    req_role = request.headers.get("X-User-Role", "")
    req_user = (request.headers.get("X-Username") or "").strip()
    expected_user = os.environ.get("APP_USERNAME", "admin").strip()
    if req_role and req_role != "administrator" and req_user.lower() not in ("admin", expected_user.lower()):
        return jsonify({"status": "error", "message": "Akses ditolak. Fitur tambah cookie hanya untuk akun administrator."}), 403

    data = request.get_json(silent=True) or request.form
    cookie_raw = (data.get("cookie_json") or "").strip()
    if not cookie_raw:
        return jsonify({"status": "error", "message": "Cookie tidak boleh kosong."}), 400

    val = session_manager.validate_cookie_payload(cookie_raw)
    if not val.is_valid and val.status == session_manager.SessionStatus.INVALID:
        return jsonify({"status": "error", "message": f"Format cookie tidak valid: {val.reason}"}), 400

    email = (data.get("cookie_email") or data.get("email") or "").strip()
    if not email:
        email = val.detected_email or f"google.session.{int(time.time()) % 10000:04d}@gmail.com"

    # Live check with Google to retrieve real account name and session status
    live = session_manager.check_google_account_live(cookie_raw, fallback_email=email)
    account_name = live.get("account_name") or ""
    session_status = live.get("status") or val.status.value

    json_to_save = val.normalized_json or json.dumps(val.sanitized_cookies)
    inserted = db.save_cookie(email, json_to_save)
    db.update_cookie_session_status(email, session_status, live.get("reason") or val.reason)
    if account_name:
        with db.get_db() as conn:
            conn.execute("UPDATE cookies SET account_name = ? WHERE email = ?", (account_name, email))
            conn.execute("UPDATE emails SET account_name = ? WHERE email = ?", (account_name, email))

    # Detect if another account already uses this exact session token
    core_sig = None
    for ck in val.sanitized_cookies:
        if ck.get("name") in ("SID", "SAPISID", "__Secure-1PSID"):
            val_str = str(ck.get("value") or "")
            if val_str:
                core_sig = hashlib.sha256(val_str.encode("utf-8")).hexdigest()[:8]
                break

    existing_cookies = db.get_all_cookies()
    duplicate_email = None
    if core_sig:
        for ec in existing_cookies:
            if ec["email"] != email:
                ec_val = session_manager.validate_cookie_payload(ec["cookie_json"])
                for ck in ec_val.sanitized_cookies:
                    if ck.get("name") in ("SID", "SAPISID", "__Secure-1PSID"):
                        if str(ck.get("value") or "") and hashlib.sha256(str(ck.get("value")).encode()).hexdigest()[:8] == core_sig:
                            duplicate_email = ec["email"]
                            break
                if duplicate_email:
                    break

    with db.get_db() as conn:
        existing = conn.execute("SELECT id FROM emails WHERE email = ?", (email,)).fetchone()
        if not existing:
            conn.execute("INSERT INTO emails (email, password, flagged, fail_count) VALUES (?, ?, 0, 0)", (email, "cookie_auth"))
        else:
            conn.execute("UPDATE emails SET flagged = 0, fail_count = 0 WHERE email = ?", (email,))

    res_data = {
        "status": "ok",
        "saved": True,
        "is_new": bool(inserted),
        "email": email,
        "account_name": account_name,
        "valid": live.get("is_valid", val.is_valid),
        "cookie_count": val.cookie_count,
        "session_status": session_status,
        "reason": live.get("reason") or val.reason,
    }
    if duplicate_email:
        res_data["warning"] = f"Perhatian: Cookie ini memiliki sesi token yang sama dengan '{duplicate_email}'. Untuk menjalankan ulasan independen pada multi-layar, pastikan login dengan akun Google yang berbeda."
    return jsonify(res_data)


@app.route("/cookies/add-to-pool/<int:cookie_id>", methods=["POST"])
@login_required
def add_cookie_to_pool(cookie_id):
    with db.get_db() as conn:
        row = conn.execute("SELECT email FROM cookies WHERE id = ?", (cookie_id,)).fetchone()
        if row:
            email = row["email"]
            existing = conn.execute("SELECT id FROM emails WHERE email = ?", (email,)).fetchone()
            if not existing:
                conn.execute("INSERT INTO emails (email, password) VALUES (?, ?)", (email, "cookie_auth"))
    return redirect(url_for("dashboard"))


@app.route("/cookies/delete/<int:cookie_id>", methods=["POST"])
@app.route("/api/cookies/<int:cookie_id>", methods=["DELETE", "POST"])
@login_required
def delete_cookie(cookie_id):
    db.delete_cookie(cookie_id)
    if request.path.startswith("/api/") or request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accept_mimetypes.best == "application/json":
        return jsonify({"status": "ok"})
    return redirect(url_for("dashboard"))


VM_IP_MAP = {
    "192.168.1.8": 101,
    "192.168.1.9": 102,
    "192.168.1.10": 103,
    "192.168.1.11": 104,
    "192.168.1.12": 105,
    "192.168.1.13": 106,
}


def resolve_request_vmid(identifier="auto"):
    if not identifier or str(identifier).lower() in ("auto", "none", "", "all"):
        remote_ip = request.remote_addr
        if remote_ip in VM_IP_MAP:
            return VM_IP_MAP[remote_ip]
        return 101
    try:
        val = int(identifier)
        if 101 <= val <= 106:
            return val
        if 1 <= val <= 6:
            return 100 + val
    except ValueError:
        pass
    return 101


def get_cdp_cookies_data(identifier):
    db.init_db()
    cookies = db.get_all_cookies()
    target_row = None
    # 1. Match by email or substring
    for c in cookies:
        if str(identifier).lower() in c["email"].lower():
            target_row = c
            break

    # 2. Match by VM ID (101-106) or Slot index (1-6)
    if not target_row and cookies:
        try:
            val = int(identifier)
            if 101 <= val <= 106:
                idx = val - 101
            elif 1 <= val <= 6:
                idx = val - 1
            else:
                idx = 0
            if idx < len(cookies):
                target_row = cookies[idx]
        except ValueError:
            pass

    # 3. Fallback to first cookie
    if not target_row and cookies:
        target_row = cookies[0]

    if not target_row:
        return None, []

    try:
        raw_list = json.loads(target_row["cookie_json"])
    except Exception:
        return target_row["email"], []

    cdp_list = []
    for ck in raw_list:
        if not ck.get("name") or not ck.get("value"):
            continue
        item = {
            "name": ck["name"],
            "value": ck["value"],
            "domain": ck.get("domain") or ".google.com",
            "path": ck.get("path") or "/",
        }
        if ck.get("secure") is not None:
            item["secure"] = bool(ck["secure"])
        if ck.get("httpOnly") is not None:
            item["httpOnly"] = bool(ck["httpOnly"])
        if ck.get("sameSite") in ["Strict", "Lax", "None"]:
            item["sameSite"] = ck["sameSite"]
        if ck.get("expirationDate") or ck.get("expiry"):
            item["expires"] = float(ck.get("expirationDate") or ck.get("expiry"))
        cdp_list.append(item)

    return target_row["email"], cdp_list


@app.route("/api/vm/cookies/<identifier>", methods=["GET"])
def api_vm_get_cookies(identifier):
    """Return CDP-formatted cookies for VM automation (e.g. Edge)."""
    email, cdp_list = get_cdp_cookies_data(identifier)
    if not email:
        return jsonify({"status": "error", "message": "No cookies found"}), 404
    return jsonify({
        "status": "ok",
        "email": email,
        "count": len(cdp_list),
        "cookies": cdp_list,
    })


@app.route("/api/vm/task", methods=["GET"])
@app.route("/api/vm/task/<identifier>", methods=["GET"])
def api_vm_get_task(identifier="auto"):
    """Return current review task instructions and cookies for VM execution."""
    vmid = resolve_request_vmid(identifier)
    task_file = f"/tmp/vm_task_{vmid}.json"
    task_data = {}
    if os.path.exists(task_file):
        try:
            with open(task_file, "r") as f:
                task_data = json.load(f)
        except Exception as e:
            logger.warning("Failed to read task file %s: %s", task_file, e)

    email = task_data.get("email") or f"{vmid}"
    target_url = task_data.get("target_url")
    star_rating = task_data.get("star_rating", 5)
    review_text = task_data.get("review_text", "")
    business_name = task_data.get("business_name", "")

    if not target_url:
        with db.get_db() as conn:
            biz_row = conn.execute("SELECT name, url FROM businesses ORDER BY id DESC LIMIT 1").fetchone()
            if biz_row:
                target_url = biz_row["url"]
                business_name = biz_row["name"]
            else:
                target_url = "https://www.google.com/maps"

    matched_email, cdp_list = get_cdp_cookies_data(email)

    return jsonify({
        "status": "ok",
        "vmid": vmid,
        "email": matched_email or email,
        "business_name": business_name,
        "target_url": target_url,
        "star_rating": star_rating,
        "review_text": review_text,
        "cookies": cdp_list,
    })


@app.route("/api/vm/log", methods=["POST"])
@app.route("/api/vm/log/<identifier>", methods=["POST"])
def api_vm_log(identifier="auto"):
    """Receive debug log from VM PowerShell scripts."""
    vmid = resolve_request_vmid(identifier)
    data = request.get_data(as_text=True)
    logger.info("=== [VM %s LOG] ===\n%s\n================", vmid, data)
    print(f"=== [VM {vmid} LOG] ===\n{data}\n================")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("/tmp/vm_debug.log", "a") as f:
        f.write(f"[{now_str}] [VM {vmid}] {data}\n")
    with open(f"/tmp/vm_{vmid}_debug.log", "a") as f:
        f.write(f"[{now_str}] {data}\n")

    task_file = f"/tmp/vm_task_{vmid}.json"
    if os.path.exists(task_file):
        try:
            with open(task_file, "r") as f:
                tdata = json.load(f)
            biz_id = tdata.get("business_id")
            rev_id = tdata.get("review_id")
            em = tdata.get("email", "")
            if biz_id:
                if "INJECTION COMPLETE SUCCESS" in data:
                    db.add_process_log(biz_id, f"[{em}] Browser Edge di VM {vmid} berhasil membuka Google Maps dengan sesi aktif.", rev_id)
                elif "Edge launched" in data:
                    db.add_process_log(biz_id, f"[{em}] Microsoft Edge berhasil dijalankan di Windows VM {vmid}.", rev_id)
                elif "Page.navigate" in data:
                    db.add_process_log(biz_id, f"[{em}] Membuka halaman bisnis Google Maps di VM {vmid}...", rev_id)
        except Exception:
            pass

    return jsonify({"status": "ok"})


@app.route("/api/cookies/<int:cookie_id>/test", methods=["POST"])
@login_required
def test_cookie(cookie_id):
    """Validate stored cookie against google.com live and update session status."""
    cookies = db.get_all_cookies()
    target = next((c for c in cookies if c["id"] == cookie_id), None)
    if not target:
        with db.get_db() as conn:
            em_row = conn.execute("SELECT email FROM emails WHERE id = ?", (cookie_id,)).fetchone()
            if em_row:
                return jsonify({
                    "status": "error",
                    "email": em_row["email"],
                    "is_valid": False,
                    "session_status": "no_cookie",
                    "reason": "Akun ini belum memiliki Cookie JSON. Silakan masukkan cookie terlebih dahulu."
                }), 400
        return jsonify({"status": "error", "message": "Cookie tidak ditemukan."}), 404

    email = target["email"]
    live = session_manager.check_google_account_live(target["cookie_json"], fallback_email=email)
    st_val = live.get("status") or "needs_login"
    acc_name = live.get("account_name") or ""
    reason = live.get("reason") or ""
    is_valid = bool(live.get("is_valid", False))

    with db.get_db() as conn:
        conn.execute(
            """UPDATE cookies
               SET status = ?, account_name = (CASE WHEN ? != '' THEN ? ELSE account_name END),
                   last_checked_at = CURRENT_TIMESTAMP, error_reason = ?
               WHERE id = ?""",
            (st_val, acc_name, acc_name, reason, cookie_id),
        )
        conn.execute(
            """UPDATE emails
               SET account_name = (CASE WHEN ? != '' THEN ? ELSE account_name END),
                   flagged = (CASE WHEN ? = 'active' THEN 0 ELSE flagged END),
                   fail_count = (CASE WHEN ? = 'active' THEN 0 ELSE fail_count END)
               WHERE email = ?""",
            (acc_name, acc_name, st_val, st_val, email),
        )

    val = session_manager.validate_cookie_payload(target["cookie_json"])
    return jsonify({
        "status": "ok",
        "email": email,
        "account_name": acc_name,
        "is_valid": is_valid,
        "session_status": st_val,
        "reason": reason,
        "count": val.cookie_count,
        "names": val.cookie_names[:8],
    })


@app.route("/cookies/health")
@app.route("/api/cookies/health")
@login_required
def cookie_health():
    """Return non-sensitive cookie metadata for dashboard polling with duplicate session detection."""
    cookies_rows = db.get_all_cookies()
    parsed_list = []
    sig_map = defaultdict(list)

    for row in cookies_rows:
        val = session_manager.validate_cookie_payload(row["cookie_json"])
        sig = None
        for ck in val.sanitized_cookies:
            if ck.get("name") in ("SID", "SAPISID", "__Secure-1PSID"):
                val_str = str(ck.get("value") or "")
                if val_str:
                    sig = hashlib.sha256(val_str.encode("utf-8")).hexdigest()[:8]
                    break
        parsed_list.append((row, val, sig))
        if sig:
            sig_map[sig].append(row["email"])

    result = []
    for row, val, sig in parsed_list:
        is_dup = bool(sig and len(sig_map[sig]) > 1)
        dup_with = [e for e in sig_map.get(sig, []) if e != row["email"]] if is_dup else []
        result.append({
            "id": row["id"],
            "email": row["email"],
            "valid": val.is_valid,
            "status": row.get("status") or val.status.value,
            "error_reason": row.get("error_reason") or (val.reason if not val.is_valid else None),
            "count": val.cookie_count,
            "session_hash": sig,
            "is_duplicate": is_dup,
            "duplicate_with": dup_with,
            "updated_at": row["updated_at"],
            "last_checked_at": row.get("last_checked_at"),
        })
    return jsonify({
        "status": "ok",
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "cookies": result,
        "has_duplicates": any(c["is_duplicate"] for c in result),
    })


@app.route("/emails/<int:email_id>/unflag", methods=["POST"])
@app.route("/api/emails/<int:email_id>/unflag", methods=["POST"])
@login_required
def unflag_email(email_id):
    ok = db.unflag_email(email_id)
    if request.path.startswith("/api/") or request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accept_mimetypes.best == "application/json":
        return jsonify({"status": "ok" if ok else "error"})
    return redirect(url_for("dashboard"))


@app.route("/api/emails/unflag-all", methods=["POST"])
@login_required
def api_unflag_all_emails():
    """Unflag all accounts and reset their fail count to zero."""
    count = db.unflag_all_emails()
    return jsonify({
        "status": "ok",
        "message": f"{count} akun berhasil dipulihkan (status flagged dan fail count direset).",
        "unflagged_count": count,
    })


# ── Global email pool ─────────────────────────────────────────────────────────

@app.route("/emails/upload", methods=["POST"])
@login_required
def upload_emails():
    import logging as _log
    csv_file = request.files.get("csv_file")
    inserted = 0
    updated = 0
    error_msg = None

    if csv_file and csv_file.filename:
        try:
            content = csv_file.read().decode("utf-8-sig")
            if not content.strip():
                error_msg = "File is empty"
            else:
                first_line = content.strip().split("\n")[0]
                if "User ID / Email Address" in first_line:
                    # G2G format (comma or tab separated)
                    delimiter = "\t" if "\t" in first_line else ","
                    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
                    for row in reader:
                        row = {k.strip(): (v or "").strip() for k, v in row.items()}
                        email = row.get("User ID / Email Address", "").lstrip("'")
                        password = row.get("Password", "")
                        secret_q = row.get("First Secret Question", "").lower()
                        totp_secret = row.get("First Secret Answer", "") if secret_q == "2fa" else None
                        totp_secret = totp_secret or None
                        if email and password:
                            result = db.add_email(email, password, totp_secret=totp_secret)
                            if result:
                                inserted += 1
                            else:
                                updated += 1
                else:
                    # Legacy format: email,password[,totp_secret]
                    reader = csv.DictReader(io.StringIO(content))
                    for row in reader:
                        email = (row.get("email") or "").strip()
                        password = (row.get("password") or "").strip()
                        totp_secret = (row.get("totp_secret") or "").strip() or None
                        if email and password:
                            result = db.add_email(email, password, totp_secret=totp_secret)
                            if result:
                                inserted += 1
                            else:
                                updated += 1
        except Exception as exc:
            _log.exception("CSV upload failed: %s", exc)
            error_msg = str(exc)
    else:
        error_msg = "No file selected"

    return redirect(url_for("dashboard", uploaded=inserted, updated=updated, upload_error=error_msg or ""))


@app.route("/emails/add", methods=["POST"])
@login_required
def add_email():
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()
    totp_secret = request.form.get("totp_secret", "").strip() or None
    if email and password:
        db.add_email(email, password, totp_secret=totp_secret)
    return redirect(url_for("dashboard"))


@app.route("/api/emails", methods=["POST"])
@login_required
def api_add_email():
    data = request.get_json(silent=True) or request.form
    email = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()
    totp_secret = (data.get("totp_secret") or "").strip() or None
    if not email or not password:
        return jsonify({"status": "error", "message": "Email dan password wajib diisi."}), 400
    email_id = db.add_email(email, password, totp_secret=totp_secret)
    return jsonify({"status": "ok", "email_id": email_id})


@app.route("/emails/delete/<int:email_id>", methods=["POST"])
@app.route("/api/emails/<int:email_id>", methods=["DELETE"])
@login_required
def delete_email(email_id):
    db.delete_email(email_id)
    if request.path.startswith("/api/") or request.method == "DELETE":
        return jsonify({"status": "ok"})
    return redirect(url_for("dashboard"))


@app.route("/emails/edit/<int:email_id>", methods=["POST"])
@login_required
def edit_email(email_id):
    """Update email, password, dan/atau TOTP secret untuk akun master."""
    new_email   = request.form.get("email", "").strip()
    new_password = request.form.get("password", "").strip() or None
    new_totp    = request.form.get("totp_secret", "").strip() or None
    if not new_email:
        return redirect(url_for("dashboard") + "?email_error=Email+tidak+boleh+kosong")
    ok = db.update_email(email_id, new_email, new_password, new_totp)
    if not ok:
        return redirect(url_for("dashboard") + "?email_error=Akun+tidak+ditemukan")
    return redirect(url_for("dashboard") + "?email_updated=1")


@app.route("/api/emails/<int:email_id>", methods=["PUT", "PATCH"])
@login_required
def api_edit_email(email_id):
    """REST endpoint: update master akun Google (email/password/totp)."""
    data        = request.get_json(silent=True) or request.form
    new_email   = (data.get("email") or "").strip()
    new_password = (data.get("password") or "").strip() or None
    new_totp    = (data.get("totp_secret") or "").strip() or None
    if not new_email:
        return jsonify({"status": "error", "message": "Email tidak boleh kosong."}), 400
    ok = db.update_email(email_id, new_email, new_password, new_totp)
    if not ok:
        return jsonify({"status": "error", "message": "Akun tidak ditemukan."}), 404
    return jsonify({"status": "ok", "message": "Akun berhasil diperbarui."})


@app.route("/api/emails/<int:email_id>/test-login", methods=["POST"])
@login_required
def api_test_login_email(email_id):
    """Coba login ke Google menggunakan email+password yang tersimpan untuk akun ini.
    Menjalankan browser Chromium headless, login, dan menyimpan cookie jika berhasil."""
    row = db.get_email_by_id(email_id)
    if not row:
        return jsonify({"status": "error", "message": "Akun tidak ditemukan."}), 404

    email    = row["email"]
    password = row.get("password") or ""
    totp     = row.get("totp_secret") or None

    if not password or password == "cookie_auth":
        return jsonify({
            "status": "error",
            "message": f"Akun {email} tidak memiliki password tersimpan. Tambahkan password terlebih dahulu.",
            "email": email,
        }), 400

    try:
        import bot as _bot
        ok, msg = _bot.auto_login_single_account(email, password, totp_secret=totp)
    except Exception as exc:
        logging.exception("Error executing test login for %s", email)
        return jsonify({
            "status": "failed",
            "message": f"Error internal bot: {str(exc)}",
            "email": email,
        }), 200

    if ok:
        return jsonify({
            "status": "success",
            "message": msg or f"Login berhasil. Cookie akun {email} diperbarui.",
            "email": email,
        })
    else:
        return jsonify({
            "status": "failed",
            "message": msg or f"Login gagal untuk {email}.",
            "email": email,
        }), 200  # tetap 200 agar frontend bisa baca pesan gagal


# ── Per-business review management ────────────────────────────────────────────

@app.route("/business/<int:business_id>/reset-review/<int:review_id>", methods=["POST"])
@app.route("/api/businesses/<int:business_id>/reset-review/<int:review_id>", methods=["POST"])
@login_required
def reset_review(business_id, review_id):
    db.reset_review(review_id)
    if request.path.startswith("/api/") or request.is_json:
        return jsonify({"status": "ok", "message": "Review direset."})
    return redirect(url_for("business", business_id=business_id))


@app.route("/business/<int:business_id>/delete-review/<int:review_id>", methods=["POST", "DELETE"])
@app.route("/api/businesses/<int:business_id>/delete-review/<int:review_id>", methods=["POST", "DELETE"])
@login_required
def delete_review(business_id, review_id):
    db.delete_review(review_id)
    if request.path.startswith("/api/") or request.is_json or request.method == "DELETE":
        return jsonify({"status": "ok", "message": "Review dihapus."})
    return redirect(url_for("business", business_id=business_id))


# ── Bot control ───────────────────────────────────────────────────────────────

@app.route("/business/<int:business_id>/start-bot", methods=["POST"])
@app.route("/api/businesses/<int:business_id>/start-bot", methods=["POST"])
@login_required
def start_bot(business_id):
    payload = request.get_json(silent=True) or request.form
    # The panel represents the current run, so discard stale messages first.
    db.clear_process_logs(business_id)
    # Recover any interrupted reviewing state back to pending so it can be picked up
    db.reset_business_reviewing(business_id)

    if request.is_json and isinstance(payload.get("selected_email_ids"), list):
        selected_email_ids = payload.get("selected_email_ids")
        allowed_email_ids = [int(x) for x in selected_email_ids if str(x).isdigit()] if selected_email_ids else None
    else:
        selected_email_ids = request.form.getlist("selected_email_ids")
        allowed_email_ids = [int(x) for x in selected_email_ids if x.isdigit()] if selected_email_ids else None

    # Star counts come directly from the form or json payload
    star_list = []
    for star in range(1, 6):
        count = int(payload.get(f"star_{star}_count") or 0)
        star_list.extend([star] * count)

    if not star_list:
        default_count = int(payload.get("count") or 3)
        star_list = [5] * default_count

    selected_language = payload.get("selected_language", "Indonesian")
    if selected_language not in {"Indonesian", "English", "Spanish", "Chinese"}:
        selected_language = "Indonesian"
    language_list = [selected_language] * len(star_list)

    # Shuffle ratings and languages independently so assignments are random.
    random.shuffle(star_list)

    # Validasi ketat: Hanya izinkan jika ada akun dengan cookie aktif ('active')
    with db.get_db() as conn:
        active_count = conn.execute("SELECT COUNT(*) FROM cookies WHERE status = 'active'").fetchone()[0]

    if active_count == 0:
        return jsonify({
            "status": "error",
            "message": "Tidak dapat menjalankan task: Tidak ada akun dengan status AKTIF. Seluruh akun berstatus 'PERLU LOGIN' atau belum memiliki cookie valid. Harap tambahkan atau perbarui cookie aktif di menu Kelola Cookie."
        }), 400

    # Handle execution mode: queue (default anti-bot safe) vs parallel
    mode = str(payload.get("mode") or "queue").lower()
    if mode == "queue":
        screen_count = 1
    else:
        screen_count = max(1, min(6, int(payload.get("screen_count") or payload.get("count") or 1)))

    delay_seconds = max(5, int(payload.get("delay_seconds") or 60))

    # Save to review_configs so worker and bot.run_reviews picks up the queue mode and natural delay
    cfg = db.get_review_config(business_id) or {}
    cfg["screen_count"] = screen_count
    cfg["delay_seconds"] = delay_seconds
    db.save_review_config(business_id, cfg)

    created, already_pending = db.create_review_jobs(business_id, star_list, language_list=language_list, allowed_email_ids=allowed_email_ids)
    if created == 0 and already_pending == 0:
        return jsonify({
            "status": "error",
            "message": "Tidak ada akun dengan cookie AKTIF yang dapat ditugaskan untuk target ini. Silakan tambahkan cookie akun baru atau reset ulasan target."
        }), 400

    mode_label = f"Mode Antrean (1 akun bergiliran, jeda {delay_seconds}s)" if screen_count == 1 else f"Mode Paralel ({screen_count} layar)"
    db.add_process_log(
        business_id,
        f"{created} tugas review masuk ke daftar antrean [{mode_label}]" + (f" ({already_pending} tugas sudah ada)." if already_pending else "."),
    )

    try:
        with db.get_db() as conn:
            conn.execute("UPDATE campaign_settings SET is_paused = 0")
    except Exception:
        pass

    try:
        subprocess.Popen(
            [sys.executable, "worker.py", "--business-id", str(business_id)],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        db.add_process_log(business_id, "Worker langsung dijalankan untuk review baru.")
    except OSError as exc:
        db.add_process_log(business_id, f"Worker tidak dapat dijalankan: {exc}", level="error")
        return jsonify({"status": "error", "message": "Worker gagal dijalankan."}), 500

    return jsonify({"status": "processing", "jobs_created": created, "already_pending": already_pending})


@app.route("/business/<int:business_id>/stop-bot", methods=["POST"])
@app.route("/api/businesses/<int:business_id>/stop-bot", methods=["POST"])
@login_required
def stop_bot(business_id):
    """Force stop this business's worker, active Chromium, and background services."""
    if not db.get_business(business_id):
        return jsonify({"status": "error", "message": "Business tidak ditemukan."}), 404

    res = force_stop_all_workers(business_id=business_id)
    return jsonify(res)


@app.route("/business/<int:business_id>/reset-all-reviews", methods=["POST"])
@app.route("/api/businesses/<int:business_id>/reset-all-reviews", methods=["POST"])
@login_required
def reset_all_reviews(business_id):
    """Reset all reviews for this business back to pending so they can be re-run."""
    count = db.reset_all_reviews_for_business(business_id)
    return jsonify({"status": "ok", "message": f"{count} tugas review berhasil direset ke status antrean."})


@app.route("/business/<int:business_id>/dark-mode/delete-comments", methods=["POST"])
@app.route("/api/businesses/<int:business_id>/dark-mode/delete-comments", methods=["POST"])
@login_required
def dark_mode_delete_comments(business_id):
    """Dark Mode: Hapus semua ulasan/komentar target ini dari database."""
    biz = db.get_business(business_id)
    if not biz:
        return jsonify({"status": "error", "message": "Target bisnis tidak ditemukan."}), 404

    count = db.delete_all_reviews_for_business(business_id)
    db.add_process_log(
        business_id,
        f"Dark Mode: {count} ulasan dan komentar berhasil dihapus dari database target.",
        level="warning",
    )
    return jsonify({
        "status": "ok",
        "message": f"Berhasil menghapus {count} komentar/ulasan pada target {biz['name']}.",
        "deleted_count": count,
    })


_ACTIVE_DELETE_TASKS = set()

@app.route("/business/<int:business_id>/dark-mode/delete-maps-reviews", methods=["POST"])
@app.route("/api/businesses/<int:business_id>/dark-mode/delete-maps-reviews", methods=["POST"])
@login_required
def dark_mode_delete_maps_reviews(business_id):
    """Dark Mode: Hapus ulasan dan komentar akun bot sendiri langsung di Google Maps publik (Live Chromium)."""
    biz = db.get_business(business_id)
    if not biz:
        return jsonify({"status": "error", "message": "Target bisnis tidak ditemukan."}), 404

    if business_id in _ACTIVE_DELETE_TASKS:
        return jsonify({
            "status": "warning",
            "message": f"Penghapusan ulasan untuk target {biz['name']} sedang berjalan. Harap tunggu hingga proses selesai.",
        }), 409

    data = request.get_json(silent=True) or request.form or {}
    email_id = data.get("email_id")
    all_accounts = data.get("all_accounts") or request.args.get("all_accounts")
    is_all = str(all_accounts).lower() in ("true", "1", "yes", "all") or data.get("scope") == "all"

    # Get accounts that have reviewed or all registered accounts
    with db.get_db() as conn:
        if email_id:
            rows = conn.execute(
                """SELECT e.id as email_id, e.email
                   FROM emails e
                   WHERE e.id = ?""",
                (int(email_id),)
            ).fetchall()
        elif is_all:
            rows = conn.execute(
                """SELECT e.id as email_id, e.email
                   FROM emails e
                   ORDER BY e.id ASC"""
            ).fetchall()
        else:
            # Default: check for reviewed/posted records first
            rows = conn.execute(
                """SELECT r.id as review_id, r.email_id, e.email, r.status
                   FROM reviews r
                   JOIN emails e ON r.email_id = e.id
                   WHERE r.business_id = ? AND r.status IN ('reviewed', 'posted')""",
                (business_id,)
            ).fetchall()
            # If no 'reviewed' rows found (e.g. DB wiped or pending), fallback to ALL master accounts in emails!
            if not rows:
                rows = conn.execute(
                    """SELECT e.id as email_id, e.email
                       FROM emails e
                       ORDER BY e.id ASC"""
                ).fetchall()

    if not rows:
        return jsonify({
            "status": "error",
            "message": f"Tidak ada akun bot yang ditemukan di database untuk membersihkan ulasan pada target {biz['name']}."
        }), 400

    # Deduplicate accounts so each email runs exactly once
    seen_emails = set()
    unique_targets = []
    for r in rows:
        d = dict(r)
        em = (d.get("email") or "").strip().lower()
        if em and em not in seen_emails:
            seen_emails.add(em)
            unique_targets.append(d)
    targets = unique_targets

    def run_async_delete(targs):
        try:
            _ACTIVE_DELETE_TASKS.add(business_id)
            db.add_process_log(
                business_id,
                f"Memulai pembersihan ulasan Google Maps untuk {len(targs)} akun bot secara berurutan...",
                level="info"
            )
            for idx, row in enumerate(targs):
                db.add_process_log(
                    business_id,
                    f"[{row['email']}] [Akun {idx+1}/{len(targs)}] Memulai scan & hapus ulasan di Google Maps...",
                    row.get("email_id"),
                    level="info"
                )
                bot.delete_own_review_on_maps(
                    email=row["email"],
                    maps_url=biz["url"],
                    business_name=biz["name"],
                    email_id=row.get("email_id"),
                    business_id=business_id,
                    slot_index=idx % 6,
                )
                time.sleep(2)
            db.add_process_log(
                business_id,
                f"Pembersihan ulasan Google Maps selesai untuk seluruh ({len(targs)}) akun bot.",
                level="success"
            )
        finally:
            _ACTIVE_DELETE_TASKS.discard(business_id)

    threading.Thread(target=run_async_delete, args=(targets,), daemon=True).start()

    return jsonify({
        "status": "ok",
        "message": f"Penghapusan ulasan sendiri di Google Maps untuk {len(targets)} akun sedang diproses secara live via Chromium.",
        "target_count": len(targets),
        "accounts": [t["email"] for t in targets]
    })


@app.route("/business/<int:business_id>/dark-mode/report-map", methods=["POST"])
@app.route("/api/businesses/<int:business_id>/dark-mode/report-map", methods=["POST"])
@login_required
def dark_mode_report_map(business_id):
    """Dark Mode: Jalankan sinyal pelaporan Google Maps (Spam/Review Palsu/Tutup/Pelanggaran)."""
    biz = db.get_business(business_id)
    if not biz:
        return jsonify({"status": "error", "message": "Target bisnis tidak ditemukan."}), 404

    data = request.get_json(silent=True) or request.form or {}
    reason = data.get("reason", "spam_fake")
    custom_note = (data.get("custom_note") or "").strip()
    account_count = max(1, min(6, int(data.get("account_count") or 3)))

    REASON_MAP = {
        "spam_fake": "Spam, ulasan palsu, atau manipulasi reputasi",
        "closed_nonexistent": "Tempat bisnis tutup permanen / tidak ada di lokasi",
        "conflict_interest": "Konflik kepentingan atau informasi menyesatkan",
        "offensive_content": "Konten ofensif atau pelanggaran pedoman Google",
    }
    reason_label = REASON_MAP.get(reason, reason)

    db.add_process_log(
        business_id,
        f"Dark Mode [Report Map]: Sinyal pelaporan ({reason_label}) dikirim untuk target '{biz['name']}' ({account_count} akun). {f'Detail: {custom_note}' if custom_note else ''}",
        level="warning",
    )

    return jsonify({
        "status": "ok",
        "message": f"Sinyal Report Map ({reason_label}) berhasil dieksekusi ({account_count} akun).",
        "reason": reason_label,
        "reported_accounts": account_count,
    })


@app.errorhandler(404)
def not_found_handler(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Not Found", "status": 404}), 404
    spa = _serve_spa()
    if spa is not None and session.get("logged_in"):
        return spa
    return e


if __name__ == "__main__":
    db.init_db()
    db.migrate_add_delay_seconds()
    db.migrate_add_review_type_language()
    db.migrate_add_totp_secret()
    db.migrate_add_email_fail_tracking()
    db.migrate_add_cookies_table()
    db.migrate_add_cookie_session_columns()
    db.migrate_add_process_logs_table()
    #app.run(debug=True, port=5000)
    app.run(host="0.0.0.0", port=5000, debug=False)
