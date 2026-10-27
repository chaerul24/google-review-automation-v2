#!/usr/bin/env python3
"""AutoBotix Google Review Automation — Windows CMD CLI Client

Run this directly from your Windows PC Command Prompt (cmd.exe) or PowerShell:
    python bot_cli.py
or double click:
    bot.bat

Connects over local network to the AutoBotix server (192.168.1.17:5000)
and runs review tasks using native Linux Chromium on the server (zero VM).
"""

import argparse
import json
import os
import re
import sys
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any, Dict, List, Optional

# Enable ANSI colors on Windows cmd.exe
if sys.platform == "win32":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

# ANSI Color Codes
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_DIM = "\033[2m"
C_RED = "\033[91m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_BLUE = "\033[94m"
C_MAGENTA = "\033[95m"
C_CYAN = "\033[96m"
C_WHITE = "\033[97m"

DEFAULT_SERVER = os.environ.get("BOT_SERVER", "http://192.168.1.17:5000")
DEFAULT_API_KEY = os.environ.get("BOT_KEY", "")


class ServerClient:
    """REST API Client communicating with AutoBotix server."""

    def __init__(self, base_url: str = DEFAULT_SERVER, api_key: str = DEFAULT_API_KEY, username: str = "", role: str = ""):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.username = username
        self.role = role or ("administrator" if username.lower() == "admin" else "user")
        self.is_admin = (self.role == "administrator" or self.username.lower() in ("admin",))

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate against the server and retrieve session API key."""
        url = f"{self.base_url}/api/cli/login"
        payload = json.dumps({"username": username, "password": password}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "User-Agent": "AutoBotix-Windows-CLI/1.0",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("authenticated"):
                    self.api_key = data.get("api_key") or password
                    self.username = data.get("username", username)
                    self.role = data.get("role", "administrator" if self.username.lower() == "admin" else "user")
                    self.is_admin = (self.role == "administrator" or self.username.lower() in ("admin",))
                    return data
                raise RuntimeError(data.get("message", "Username atau password salah."))
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8", errors="replace")
            try:
                err_data = json.loads(err_body)
                msg = err_data.get("message") or err_data.get("error") or str(err)
            except Exception:
                msg = f"HTTP {err.code}: {err.reason}"
            raise RuntimeError(msg)
        except urllib.error.URLError as err:
            raise ConnectionError(f"Tidak dapat terhubung ke server {self.base_url}: {err.reason}")

    def register(self, username: str, password: str) -> Dict[str, Any]:
        """Register a new user account on the AutoBotix server."""
        url = f"{self.base_url}/api/cli/register"
        payload = json.dumps({"username": username, "password": password}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "User-Agent": "AutoBotix-Windows-CLI/1.0",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("status") == "ok":
                    return data
                raise RuntimeError(data.get("message", "Registrasi gagal."))
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8", errors="replace")
            try:
                err_data = json.loads(err_body)
                msg = err_data.get("message") or err_data.get("error") or str(err)
            except Exception:
                msg = f"HTTP {err.code}: {err.reason}"
            raise RuntimeError(msg)
        except urllib.error.URLError as err:
            raise ConnectionError(f"Tidak dapat terhubung ke server {self.base_url}: {err.reason}")

    def _request(self, endpoint: str, method: str = "GET", data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        headers = {
            "User-Agent": "AutoBotix-Windows-CLI/1.0",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        if self.username:
            headers["X-Username"] = self.username
        if self.role:
            headers["X-User-Role"] = self.role

        body_bytes = None
        if data is not None:
            body_bytes = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                resp_text = resp.read().decode("utf-8")
                try:
                    return json.loads(resp_text)
                except Exception:
                    return {"status": "ok", "raw": resp_text}
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8", errors="replace")
            try:
                err_json = json.loads(err_body)
                msg = err_json.get("message") or err_json.get("error") or str(err)
            except Exception:
                msg = f"HTTP {err.code}: {err.reason}"
            raise RuntimeError(msg)
        except urllib.error.URLError as err:
            raise ConnectionError(f"Gagal terhubung ke server di {self.base_url}: {err.reason}")

    def add_cookie(self, cookie_json: str, email: str = "") -> Dict[str, Any]:
        """Add a new cookie session to the database (Admin only)."""
        payload = {
            "cookie_json": cookie_json,
            "cookie_email": email,
            "email": email,
        }
        return self._request("/api/cookies", method="POST", data=payload)

    def delete_cookie(self, cookie_id: Optional[int] = None, email: str = "") -> Dict[str, Any]:
        """Delete a cookie session by ID or email (Admin only)."""
        payload = {}
        if cookie_id is not None:
            payload["cookie_id"] = cookie_id
        if email:
            payload["email"] = email
        return self._request("/api/cli/cookies/delete", method="POST", data=payload)

    def test_cookie(self, cookie_id: int) -> Dict[str, Any]:
        """Test a cookie session validity against Google."""
        return self._request(f"/api/cookies/{cookie_id}/test", method="POST")

    def check_account_names(self) -> Dict[str, Any]:
        """Trigger server-side verification of Google account names and live session statuses."""
        return self._request("/api/cli/cookies/check-names", method="POST")

    def get_status(self) -> Dict[str, Any]:
        return self._request("/api/cli/status")

    def get_businesses(self) -> List[Dict[str, Any]]:
        res = self._request("/api/cli/status")
        return res.get("businesses", [])

    def get_accounts(self) -> List[Dict[str, Any]]:
        res = self._request("/api/cli/status")
        return res.get("accounts", [])

    def add_business(self, name: str, url: str, category: str = "General") -> Dict[str, Any]:
        return self._request("/api/businesses", method="POST", data={
            "name": name,
            "url": url,
            "business_category": category,
        })

    def start_task(self, business_id: int, count: int = 1, star_rating: int = 5) -> Dict[str, Any]:
        payload = {
            "count": count,
            f"star_{star_rating}_count": count,
            "selected_language": "Indonesian",
        }
        return self._request(f"/api/businesses/{business_id}/start-bot", method="POST", data=payload)

    def stop_task(self, business_id: int) -> Dict[str, Any]:
        return self._request(f"/api/businesses/{business_id}/stop-bot", method="POST")

    def get_logs(self, business_id: int) -> Dict[str, Any]:
        return self._request(f"/api/businesses/{business_id}/process-log")

    def clear_logs(self, business_id: int) -> Dict[str, Any]:
        return self._request(f"/api/businesses/{business_id}/clear-logs", method="POST")

    def get_business_detail(self, business_id: int) -> Dict[str, Any]:
        """Fetch details and review list for a business."""
        return self._request(f"/api/businesses/{business_id}")

    def delete_single_review(self, business_id: int, review_id: int) -> Dict[str, Any]:
        """Delete an individual review by ID."""
        return self._request(f"/api/businesses/{business_id}/delete-review/{review_id}", method="POST")

    def delete_all_reviews(self, business_id: int) -> Dict[str, Any]:
        """Delete all reviews and queue logs for a business in database."""
        return self._request(f"/api/businesses/{business_id}/dark-mode/delete-comments", method="POST")

    def delete_maps_reviews_live(self, business_id: int, email_id: Optional[int] = None) -> Dict[str, Any]:
        """Delete own posted reviews directly on Google Maps via live Chromium bot."""
        payload = {}
        if email_id:
            payload["email_id"] = email_id
        return self._request(f"/api/businesses/{business_id}/dark-mode/delete-maps-reviews", method="POST", data=payload)


# ── UI Helpers & Animation ───────────────────────────────────────────────────

SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


class Spinner:
    """Animated terminal spinner running in a background thread."""

    def __init__(self, message: str = "Memproses..."):
        self.message = message
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def _spin(self):
        idx = 0
        while self.running:
            frame = SPINNER_FRAMES[idx % len(SPINNER_FRAMES)]
            sys.stdout.write(f"\r {C_CYAN}{frame}{C_RESET} {C_WHITE}{self.message}{C_RESET}\033[K")
            sys.stdout.flush()
            time.sleep(0.08)
            idx += 1

    def start(self, message: Optional[str] = None):
        if message:
            self.message = message
        self.running = True
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()

    def update(self, message: str):
        self.message = message

    def stop(self, final_text: Optional[str] = None):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=0.25)
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()
        if final_text:
            print(final_text)


# ── Google Maps Seeklogo Text Art & UI ───────────────────────────────────────

GOOGLE_MAPS_ICON_LINES = [
    '                      \x1b[97m:\x1b[37m.\x1b[90m.\x1b[91m%%%%\x1b[37m..\x1b[97m:\x1b[0m    ',
    '                   \x1b[97m:\x1b[37m.\x1b[91m%@@@@@@@@@@%\x1b[97m:\x1b[0m  ',
    ' \x1b[37m.\x1b[90m................\x1b[37m.\x1b[91m%@@%%%@@@%%%%@@\x1b[37m.\x1b[0m ',
    '\x1b[90m.\x1b[92m;##;#############\x1b[90m.\x1b[91m@%%%@%\x1b[90m....\x1b[91m%%%%%@\x1b[37m.\x1b[0m',
    '\x1b[92m####\x1b[94m~\x1b[97m:::::\x1b[92m########\x1b[91m%%%%%@\x1b[90m......\x1b[91m%%%%@\x1b[90m.\x1b[0m',
    '\x1b[92m###\x1b[37m.\x1b[0m \x1b[90m.\x1b[92m##\x1b[90m..\x1b[92m########\x1b[90m.\x1b[91m@%%%%@\x1b[90m...\x1b[91m%@%%%@@\x1b[97m:\x1b[0m',
    '\x1b[92m###\x1b[97m:\x1b[0m \x1b[92m#;#\x1b[37m..\x1b[0m  \x1b[92m#######\x1b[91m%@%%%%%%%%%%%@@\x1b[97m:\x1b[0m ',
    '\x1b[92m####\x1b[37m.\x1b[97m::\x1b[37m..\x1b[97m::\x1b[90m.\x1b[92m######\x1b[90m.\x1b[93m=\x1b[90m.\x1b[91m@@%%%%%@%%@%\x1b[97m:\x1b[0m  ',
    '\x1b[92m######\x1b[90m...\x1b[92m#######\x1b[93m======\x1b[91m%@%%%%%%@\x1b[90m.\x1b[97m:\x1b[0m   ',
    '\x1b[92m##############\x1b[93m=======\x1b[97m::\x1b[90m.\x1b[91m@%%%@@\x1b[37m.\x1b[97m:\x1b[0m    ',
    '\x1b[92m############\x1b[93m======\x1b[97m::::::\x1b[37m.\x1b[91m@%@%\x1b[37m.\x1b[97m::\x1b[0m    ',
    '\x1b[92m##########\x1b[93m======\x1b[97m:\x1b[0m     \x1b[97m:::\x1b[90m.\x1b[91m@@\x1b[37m.\x1b[97m:::\x1b[0m    ',
    '\x1b[92m########\x1b[93m======\x1b[37m.\x1b[94m~~\x1b[37m.\x1b[97m:\x1b[0m     \x1b[97m::\x1b[91m@%\x1b[97m::::\x1b[0m    ',
    '\x1b[92m######\x1b[93m======\x1b[37m.\x1b[94m~~~~~~\x1b[37m.\x1b[97m:\x1b[0m     \x1b[37m..\x1b[97m::::\x1b[0m    ',
    '\x1b[92m####\x1b[93m======\x1b[37m.\x1b[94m~~~~~~~~~~\x1b[37m.\x1b[97m:\x1b[0m     \x1b[97m::::\x1b[0m    ',
    '\x1b[92m##\x1b[93m======\x1b[37m.\x1b[94m~~~~~~~~~~~~~~\x1b[37m.\x1b[97m:\x1b[0m     \x1b[97m::\x1b[0m    ',
    '\x1b[93m======\x1b[37m.\x1b[94m~~~~~~~~~~~~~~~~~~~\x1b[97m:\x1b[0m         ',
    '\x1b[97m:\x1b[37m.\x1b[93m==\x1b[37m.\x1b[94m~~~~~~~~~~~~~~~~~~~~~~\x1b[37m.\x1b[97m:\x1b[0m       ',
]


def print_google_maps_logo(padding: str = "                  "):
    """Render Google Maps Icon text logo (from seeklogo 268336) using colorized text & punctuation."""
    for line in GOOGLE_MAPS_ICON_LINES:
        print(f"{padding}{line}")
    print()
    brand_title = (
        f"                   {C_BOLD}{C_BLUE}G{C_RED}o{C_YELLOW}o{C_BLUE}g{C_GREEN}l{C_RED}e{C_RESET} "
        f"{C_BOLD}{C_WHITE}Maps{C_RESET} {C_BOLD}{C_CYAN}Review Automation Bot{C_RESET}"
    )
    print(brand_title)


ANSI_REGEX = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')


def strip_ansi(s: str) -> str:
    """Strip ANSI escape sequences for accurate character width calculation."""
    return ANSI_REGEX.sub('', s)


def str_display_width(s: str) -> int:
    """Calculate terminal column width of string, accounting for wide emojis and ignoring ANSI codes."""
    clean = strip_ansi(s)
    width = 0
    for ch in clean:
        if unicodedata.east_asian_width(ch) in ('W', 'F'):
            width += 2
        else:
            width += 1
    return width


def pad_to_display_width(text: str, width: int) -> str:
    """Pad string with spaces on right to reach exact target visible column width."""
    current_w = str_display_width(text)
    pad = max(0, width - current_w)
    return text + (' ' * pad)


def print_box(lines: List[str], width: int = 68, title: Optional[str] = None):
    """Print an automatically sized and aligned unicode box.
    Guarantees that every row's right border ║ aligns with the box corners.
    """
    content_widths = [str_display_width(l) for l in lines]
    if title:
        content_widths.append(str_display_width(title))
    inner_width = max(width, max(content_widths) if content_widths else width)

    top = f" ╔{'═' * (inner_width + 2)}╗"
    sep = f" ╠{'═' * (inner_width + 2)}╣"
    bot = f" ╚{'═' * (inner_width + 2)}╝"

    print(top)
    if title:
        t_w = str_display_width(title)
        t_pad_left = (inner_width - t_w) // 2
        t_pad_right = inner_width - t_w - t_pad_left
        print(f" ║ {' ' * t_pad_left}{title}{' ' * t_pad_right} ║")
        print(sep)

    for line in lines:
        cur_w = str_display_width(line)
        pad = max(0, inner_width - cur_w)
        print(f" ║ {line}{' ' * pad} ║")

    print(bot)


def box_header(title: str, width: int = 68):
    """Print a single-row boxed banner header with perfect alignment."""
    t_w = str_display_width(title)
    inner_width = max(width, t_w)
    t_pad_left = (inner_width - t_w) // 2
    t_pad_right = inner_width - t_w - t_pad_left
    print(f" ╔{'═' * (inner_width + 2)}╗")
    print(f" ║ {' ' * t_pad_left}{title}{' ' * t_pad_right} ║")
    print(f" ╚{'═' * (inner_width + 2)}╝")


def print_banner(client: ServerClient, status_info: Optional[Dict[str, Any]] = None):
    print()
    print_google_maps_logo("                  ")
    print(f"               {C_DIM}« Native Chromium • Zero-VM Architecture »{C_RESET}")
    print()

    user_label = client.username or "admin"
    lines = [
        f"{C_DIM}Host Server:{C_RESET} {C_GREEN}{client.base_url}{C_RESET}   {C_DIM}User:{C_RESET} {C_CYAN}{user_label}{C_RESET}"
    ]
    if status_info:
        b_cnt = status_info.get("businesses_count", 0)
        a_cnt = status_info.get("accounts_count", 0)
        c_cnt = status_info.get("active_cookies", 0)
        r_cnt = status_info.get("reviewed_count", 0)
        p_cnt = status_info.get("pending_count", 0)
        disps = " ".join(status_info.get("displays", []))
        lines.append(f"Target: {C_WHITE}{b_cnt}{C_RESET} │ Akun: {C_WHITE}{a_cnt}{C_RESET} │ Cookie: {C_WHITE}{c_cnt}{C_RESET} │ Ulasan: {C_WHITE}{r_cnt}{C_RESET} │ Antrean: {C_WHITE}{p_cnt}{C_RESET}")
        lines.append(f"{C_DIM}Display Virtual Xvfb:{C_RESET} {C_CYAN}{disps}{C_RESET}")

    print_box(lines, width=68)


def _do_login(client: ServerClient, default_user: str = "admin") -> bool:
    """Handle login input and verification."""
    import getpass

    print()
    print(f" {C_BOLD}{C_CYAN}─── MASUK (LOGIN) ─────────────────────────────────────────────────────{C_RESET}")
    attempts = 0
    max_attempts = 4
    while attempts < max_attempts:
        attempts += 1
        try:
            user_in = input(f"\n {C_CYAN}Username [{default_user}]: {C_RESET}").strip()
            username = user_in if user_in else default_user

            if sys.stdin.isatty():
                try:
                    password = getpass.getpass(f" {C_CYAN}Password: {C_RESET}").strip()
                except Exception:
                    password = input(f" {C_CYAN}Password: {C_RESET}").strip()
            else:
                password = input(f" {C_CYAN}Password: {C_RESET}").strip()

            if not password:
                print(f" {C_RED}✖ Password tidak boleh kosong.{C_RESET}")
                continue

            spin = Spinner(f"Memverifikasi autentikasi ke server {client.base_url}...")
            spin.start()
            try:
                res = client.login(username, password)
                spin.stop(f" {C_BOLD}{C_GREEN}✓ Login berhasil! Selamat datang, {res.get('username', username)}.{C_RESET}")
                time.sleep(0.7)
                return True
            except Exception as err:
                spin.stop()
                raise err

        except (KeyboardInterrupt, EOFError):
            print(f"\n {C_YELLOW}Kembali ke menu autentikasi.{C_RESET}")
            return False
        except RuntimeError as err:
            print(f" {C_BOLD}{C_RED}✖ {err}{C_RESET}")
            if attempts < max_attempts:
                print(f" {C_DIM}Percobaan {attempts}/{max_attempts}. Silakan coba lagi.{C_RESET}")
        except ConnectionError as err:
            print(f" {C_BOLD}{C_RED}✖ {err}{C_RESET}")
            print(f" {C_YELLOW}Pastikan server AutoBotix aktif di {client.base_url}.{C_RESET}")
            return False

    print(f"\n {C_RED}✖ Terlalu banyak percobaan gagal. Kembali ke menu.{C_RESET}")
    time.sleep(1.5)
    return False


def _do_register(client: ServerClient) -> bool:
    """Handle new user registration and auto-login."""
    import getpass

    print()
    print(f" {C_BOLD}{C_CYAN}─── DAFTAR AKUN BARU (REGISTER) ───────────────────────────────────────{C_RESET}")
    try:
        username = input(f"\n {C_CYAN}Username Baru (min 3 huruf/angka): {C_RESET}").strip()
        if not username:
            print(f" {C_YELLOW}Registrasi dibatalkan.{C_RESET}")
            return False
        if len(username) < 3:
            print(f" {C_RED}✖ Username minimal 3 karakter.{C_RESET}")
            time.sleep(1.5)
            return False
        if not username.replace("_", "").isalnum():
            print(f" {C_RED}✖ Username hanya boleh huruf, angka, dan underscore (_).{C_RESET}")
            time.sleep(1.5)
            return False

        if sys.stdin.isatty():
            try:
                password = getpass.getpass(f" {C_CYAN}Password (min 4 karakter): {C_RESET}").strip()
                confirm = getpass.getpass(f" {C_CYAN}Konfirmasi Password: {C_RESET}").strip()
            except Exception:
                password = input(f" {C_CYAN}Password (min 4 karakter): {C_RESET}").strip()
                confirm = input(f" {C_CYAN}Konfirmasi Password: {C_RESET}").strip()
        else:
            password = input(f" {C_CYAN}Password (min 4 karakter): {C_RESET}").strip()
            confirm = input(f" {C_CYAN}Konfirmasi Password: {C_RESET}").strip()

        if len(password) < 4:
            print(f" {C_RED}✖ Password minimal 4 karakter.{C_RESET}")
            time.sleep(1.5)
            return False

        if password != confirm:
            print(f" {C_RED}✖ Konfirmasi password tidak cocok!{C_RESET}")
            time.sleep(1.5)
            return False

        spin = Spinner(f"Mendaftarkan akun '{username}' ke server...")
        spin.start()
        try:
            reg_res = client.register(username, password)
            spin.stop(f" {C_BOLD}{C_GREEN}✓ {reg_res.get('message', 'Pendaftaran berhasil!')}{C_RESET}")
        except Exception as err:
            spin.stop()
            print(f" {C_BOLD}{C_RED}✖ Gagal registrasi: {err}{C_RESET}")
            time.sleep(2)
            return False

        # Masuk otomatis setelah berhasil registrasi
        auto_spin = Spinner(f"Masuk otomatis dengan akun '{username}'...")
        auto_spin.start()
        try:
            client.login(username, password)
            auto_spin.stop(f" {C_BOLD}{C_GREEN}✓ Login otomatis berhasil! Masuk ke sistem...{C_RESET}")
            time.sleep(0.8)
            return True
        except Exception as e:
            auto_spin.stop()
            print(f" {C_YELLOW}Akun berhasil dibuat. Silakan login manual.{C_RESET}")
            time.sleep(1.5)
            return False

    except (KeyboardInterrupt, EOFError):
        print(f"\n {C_YELLOW}Registrasi dibatalkan.{C_RESET}")
        return False


def prompt_auth(client: ServerClient, default_user: str = "admin") -> bool:
    """Display Authentication Menu (Login / Register / Exit) before task menu."""
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print()
        print_google_maps_logo("                  ")
        print(f"               {C_DIM}« Native Chromium • Zero-VM Architecture »{C_RESET}")
        print()
        print(f" {C_DIM}Host Server Target: {C_GREEN}{client.base_url}{C_RESET}")
        print()
        print(f" {C_BOLD}{C_CYAN}[1]{C_RESET} {C_WHITE}Masuk (Login){C_RESET}")
        print(f" {C_BOLD}{C_CYAN}[2]{C_RESET} {C_WHITE}Daftar Akun Baru (Register){C_RESET}")
        print(f" {C_BOLD}{C_YELLOW}[0]{C_RESET} {C_DIM}Keluar (Exit){C_RESET}")
        print()

        try:
            choice = input(f" {C_GREEN}Pilih menu autentikasi [1]: {C_RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n\n {C_YELLOW}Keluar dari program.{C_RESET}")
            sys.exit(0)

        if not choice:
            choice = "1"

        if choice == "1":
            if _do_login(client, default_user):
                return True
        elif choice == "2":
            if _do_register(client):
                return True
        elif choice == "0":
            print(f"\n {C_YELLOW}Terima kasih. Program selesai.{C_RESET}")
            sys.exit(0)
        else:
            print(f" {C_RED}Pilihan tidak valid. Masukkan 1, 2, atau 0.{C_RESET}")
            time.sleep(1)


# Alias untuk kompatibilitas
prompt_login = prompt_auth


def print_businesses(businesses: List[Dict[str, Any]]):
    print()
    box_header(f"{C_BOLD}{C_CYAN}DAFTAR TARGET GOOGLE MAPS AKTIF{C_RESET}")
    if not businesses:
        print(f"  {C_YELLOW}Belum ada target bisnis terdaftar.{C_RESET}")
        return

    print(f" {C_BOLD}{'ID':<6} {'NAMA BISNIS':<28} {'ULASAN':<8} {'URL GOOGLE MAPS'}{C_RESET}")
    print(" " + "─" * 70)
    for b in businesses:
        bid = b.get("id")
        name = b.get("name", "")[:26]
        rev = b.get("reviewed_count", 0)
        url = b.get("url", "")
        if len(url) > 35:
            url = url[:32] + "..."
        print(f" {C_YELLOW}{bid:<6}{C_RESET} {C_WHITE}{name:<28}{C_RESET} {C_GREEN}{rev:<8}{C_RESET} {C_DIM}{url}{C_RESET}")
    print()


def print_accounts(accounts: List[Dict[str, Any]]):
    print()
    box_header(f"{C_BOLD}{C_CYAN}STATUS AKUN & SESI COOKIE GOOGLE{C_RESET}")
    if not accounts:
        print(f"  {C_YELLOW}Belum ada akun Google terdaftar.{C_RESET}")
        return

    print(f" {C_BOLD}{'ID':<5} {'NAMA AKUN':<22} {'EMAIL AKUN':<32} {'STATUS SESI':<16}{C_RESET}")
    print(" " + "─" * 78)
    for a in accounts:
        aid = a.get("id")
        name = (a.get("account_name") or "-").strip()[:20]
        email = a.get("email", "")[:30]
        c_status = a.get("cookie_status") or "no_cookie"

        if c_status == "active":
            st_color = f"{C_GREEN}● AKTIF{C_RESET}"
        elif c_status == "needs_login":
            st_color = f"{C_YELLOW}▲ PERLU LOGIN{C_RESET}"
        elif c_status == "expired":
            st_color = f"{C_RED}✖ KEDALUWARSA{C_RESET}"
        else:
            st_color = f"{C_DIM}- TIDAK ADA -{C_RESET}"

        st_pad = pad_to_display_width(st_color, 16)
        print(f" {C_YELLOW}{aid:<5}{C_RESET} {C_WHITE}{name:<22}{C_RESET} {C_CYAN}{email:<32}{C_RESET} {st_pad}")
    print()


def print_cookies_table(cookies: List[Dict[str, Any]]):
    print()
    box_header(f"{C_BOLD}{C_CYAN}STATUS SESI & DAFTAR COOKIE GOOGLE{C_RESET}")
    if not cookies:
        print(f"  {C_YELLOW}Belum ada cookie Google terdaftar di database.{C_RESET}")
        return

    print(f" {C_BOLD}{'ID':<5} {'NAMA AKUN GOOGLE':<24} {'EMAIL AKUN':<32} {'STATUS SESI':<16}{C_RESET}")
    print(" " + "─" * 78)
    for c in cookies:
        cid = c.get("id")
        name = (c.get("account_name") or "-").strip()[:22]
        email = c.get("email", "")[:30]
        c_status = (c.get("status") or "unknown").lower()

        if c_status == "active":
            st_color = f"{C_GREEN}● AKTIF{C_RESET}"
        elif c_status in ("expired", "revoked", "invalid"):
            st_color = f"{C_RED}✖ KEDALUWARSA{C_RESET}"
        elif c_status == "needs_login":
            st_color = f"{C_YELLOW}▲ PERLU LOGIN{C_RESET}"
        else:
            st_color = f"{C_DIM}- TIDAK AKTIF -{C_RESET}"

        st_pad = pad_to_display_width(st_color, 16)
        print(f" {C_YELLOW}{cid:<5}{C_RESET} {C_WHITE}{name:<24}{C_RESET} {C_CYAN}{email:<32}{C_RESET} {st_pad}")
    print()


def handle_cookie_menu(client: ServerClient, status_info: Dict[str, Any]):
    """Display cookies and provide Admin Add/Remove capabilities."""
    cookies = status_info.get("cookies", [])
    if not cookies:
        try:
            cur_status = client.get_status()
            cookies = cur_status.get("cookies", [])
        except Exception:
            pass

    while True:
        print_cookies_table(cookies)

        if not client.is_admin:
            print(f" {C_DIM}ℹ️  Anda masuk sebagai akun biasa ({client.username}). Fitur tambah & hapus cookie hanya untuk Administrator.{C_RESET}")
            input(f"\n {C_DIM}Tekan Enter untuk kembali ke menu utama...{C_RESET}")
            break

        # Admin Actions Menu
        print(f" {C_BOLD}{C_CYAN}─── KELOLA COOKIE (AKUN ADMIN) ────────────────────────────────────────{C_RESET}")
        print(f"  {C_YELLOW}[1]{C_RESET} {C_WHITE}➕ Tambah Cookie Baru (Paste JSON atau File .json){C_RESET}")
        print(f"  {C_YELLOW}[2]{C_RESET} {C_WHITE}🗑️  Hapus Cookie (Berdasarkan ID atau Email){C_RESET}")
        print(f"  {C_YELLOW}[3]{C_RESET} {C_WHITE}🔍 Cek Nama Akun & Status Sesi (Live Check Google){C_RESET}")
        print(f"  {C_YELLOW}[4]{C_RESET} {C_WHITE}🔄 Uji Validitas Cookie Tunggal (Test Sesi ID){C_RESET}")
        print(f"  {C_YELLOW}[0]{C_RESET} {C_DIM}↩️  Kembali ke Menu Utama{C_RESET}")
        print()

        try:
            c_opt = input(f" {C_GREEN}Pilih aksi cookie [0-4] (default 0): {C_RESET}").strip() or "0"
        except (KeyboardInterrupt, EOFError):
            break

        if c_opt == "0":
            break

        elif c_opt == "1":
            print(f"\n {C_BOLD}{C_CYAN}─── TAMBAH COOKIE BARU ───────────────────────────────────────────────{C_RESET}")
            print(f" {C_DIM}Tips: Anda dapat memasukkan file path (.json) atau paste JSON cookie langsung.{C_RESET}")
            source_in = input(f" {C_GREEN}Jalur File .json (kosongkan jika ingin paste langsung): {C_RESET}").strip()

            raw_cookie = ""
            if source_in:
                file_path = os.path.expanduser(source_in.strip('\'"'))
                if not os.path.exists(file_path):
                    print(f" {C_RED}✖ File tidak ditemukan: {file_path}{C_RESET}")
                    time.sleep(1.5)
                    continue
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        raw_cookie = f.read().strip()
                except Exception as e:
                    print(f" {C_RED}✖ Gagal membaca file: {e}{C_RESET}")
                    time.sleep(1.5)
                    continue
            else:
                print(f" {C_YELLOW}Paste JSON cookie Anda di bawah ini, lalu tekan Enter:{C_RESET}")
                try:
                    raw_cookie = input(f" JSON: ").strip()
                except (KeyboardInterrupt, EOFError):
                    print(f"\n {C_YELLOW}Batal.{C_RESET}")
                    continue

            if not raw_cookie:
                print(f" {C_RED}✖ Cookie tidak boleh kosong.{C_RESET}")
                time.sleep(1)
                continue

            email_in = input(f" {C_GREEN}Email Google (kosongkan untuk deteksi otomatis dari cookie): {C_RESET}").strip()

            spin = Spinner("Memvalidasi dan menyimpan cookie ke server...")
            spin.start()
            try:
                res = client.add_cookie(raw_cookie, email=email_in)
                detected = res.get("email") or email_in
                st_val = res.get("session_status", "unknown")
                c_cnt = res.get("cookie_count", 0)
                acc_name = res.get("account_name", "")
                spin.stop(f" {C_BOLD}{C_GREEN}✓ Cookie berhasil disimpan untuk akun '{detected}'!{C_RESET}")
                if acc_name:
                    print(f"   {C_DIM}Nama Profil Akun: {C_WHITE}{acc_name}{C_RESET}")
                print(f"   {C_DIM}Status Sesi: {C_GREEN if st_val == 'active' else C_YELLOW}{st_val.upper()}{C_RESET} │ {C_DIM}Jumlah Cookie: {C_WHITE}{c_cnt}{C_RESET}")
                if res.get("warning"):
                    print(f"   {C_YELLOW}⚠️  {res.get('warning')}{C_RESET}")
                time.sleep(1.5)
                try:
                    status_info = client.get_status()
                    cookies = status_info.get("cookies", [])
                except Exception:
                    pass
            except Exception as e:
                spin.stop()
                print(f" {C_BOLD}{C_RED}✖ Gagal menambahkan cookie: {e}{C_RESET}")
                time.sleep(2)

        elif c_opt == "2":
            print(f"\n {C_BOLD}{C_CYAN}─── HAPUS COOKIE ──────────────────────────────────────────────────────{C_RESET}")
            del_in = input(f" {C_GREEN}Masukkan ID Cookie (angka) ATAU Email yang ingin dihapus: {C_RESET}").strip()
            if not del_in:
                print(f" {C_YELLOW}Batal menghapus cookie.{C_RESET}")
                continue

            confirm = input(f" {C_BOLD}{C_RED}Yakin ingin menghapus cookie '{del_in}'? [y/N]: {C_RESET}").strip().lower()
            if confirm in ("y", "yes"):
                spin = Spinner(f"Menghapus cookie '{del_in}' dari server...")
                spin.start()
                try:
                    if del_in.isdigit():
                        res = client.delete_cookie(cookie_id=int(del_in))
                    else:
                        res = client.delete_cookie(email=del_in)
                    spin.stop(f" {C_BOLD}{C_GREEN}✓ {res.get('message', 'Cookie berhasil dihapus.')}{C_RESET}")
                    time.sleep(1.5)
                    try:
                        status_info = client.get_status()
                        cookies = status_info.get("cookies", [])
                    except Exception:
                        pass
                except Exception as e:
                    spin.stop()
                    print(f" {C_BOLD}{C_RED}✖ Gagal menghapus cookie: {e}{C_RESET}")
                    time.sleep(2)

        elif c_opt == "3":
            print(f"\n {C_BOLD}{C_CYAN}─── CEK NAMA AKUN & VALIDITAS SESI GOOGLE ─────────────────────────────{C_RESET}")
            spin = Spinner("Memverifikasi sesi & memeriksa nama profil akun ke Google...")
            spin.start()
            try:
                res = client.check_account_names()
                chk_cnt = res.get("checked", 0)
                act_cnt = res.get("active_count", 0)
                spin.stop(f" {C_BOLD}{C_GREEN}✓ Pemeriksaan selesai! {chk_cnt} akun diperiksa, {act_cnt} akun AKTIF.{C_RESET}")
                time.sleep(1.2)
                try:
                    status_info = client.get_status()
                    cookies = status_info.get("cookies", [])
                except Exception:
                    pass
            except Exception as e:
                spin.stop()
                print(f" {C_BOLD}{C_RED}✖ Gagal memeriksa nama akun: {e}{C_RESET}")
                time.sleep(2)

        elif c_opt == "4":
            print(f"\n {C_BOLD}{C_CYAN}─── UJI VALIDITAS COOKIE ──────────────────────────────────────────────{C_RESET}")
            test_in = input(f" {C_GREEN}Masukkan ID Cookie yang ingin diuji: {C_RESET}").strip()
            if not test_in.isdigit():
                print(f" {C_RED}✖ ID harus berupa angka.{C_RESET}")
                time.sleep(1)
                continue

            cid = int(test_in)
            spin = Spinner(f"Menguji validitas sesi Google untuk Cookie ID {cid}...")
            spin.start()
            try:
                res = client.test_cookie(cid)
                st_val = res.get("session_status", "unknown")
                is_valid = res.get("is_valid", False)
                email_target = res.get("email", str(cid))
                spin.stop(f" {C_BOLD}{C_GREEN if is_valid else C_YELLOW}✓ Akun '{email_target}': Status = {st_val.upper()} (Valid = {is_valid}){C_RESET}")
                time.sleep(2)
            except Exception as e:
                spin.stop()
                print(f" {C_BOLD}{C_RED}✖ Gagal menguji cookie: {e}{C_RESET}")
                time.sleep(2)


# ── Remove Review Handler ─────────────────────────────────────────────────────

def handle_remove_review_menu(client: ServerClient, status_info: Dict[str, Any]):
    """Interactive handler for removing reviews (database deletion or live Google Maps deletion)."""
    os.system("cls" if os.name == "nt" else "clear")
    print_banner(client, status_info)

    businesses = status_info.get("businesses", [])
    if not businesses:
        try:
            cur = client.get_status()
            businesses = cur.get("businesses", [])
        except Exception:
            pass

    box_header("MENU HAPUS / REMOVE ULASAN (REVIEW CLEANER)")
    print()
    print_businesses(businesses)

    if not businesses:
        print(f" {C_YELLOW}Belum ada target bisnis Google Maps terdaftar.{C_RESET}")
        input(f"\n {C_DIM}Tekan Enter untuk kembali...{C_RESET}")
        return

    try:
        bid_in = input(f"\n {C_GREEN}Masukkan ID Bisnis target yang ingin dihapus ulasannya (0 untuk batal): {C_RESET}").strip()
    except (KeyboardInterrupt, EOFError):
        return

    if not bid_in or bid_in == "0" or not bid_in.isdigit():
        return

    bid = int(bid_in)
    target_biz = next((b for b in businesses if b.get("id") == bid), None)
    biz_name = target_biz.get("name", f"Bisnis #{bid}") if target_biz else f"Bisnis #{bid}"

    # Fetch current review records for this business
    spin = Spinner(f"Mengambil data ulasan untuk '{biz_name}'...")
    spin.start()
    try:
        biz_detail = client.get_business_detail(bid)
        spin.stop()
    except Exception as exc:
        spin.stop()
        print(f" {C_RED}✖ Gagal memuat data ulasan: {exc}{C_RESET}")
        input(f"\n {C_DIM}Tekan Enter untuk kembali...{C_RESET}")
        return

    reviews = biz_detail.get("reviews", [])
    reviewed_count = sum(1 for r in reviews if r.get("status") in ("reviewed", "posted"))
    pending_count = sum(1 for r in reviews if r.get("status") == "pending")

    os.system("cls" if os.name == "nt" else "clear")
    print_banner(client, status_info)

    sub_lines = [
        f" Target : {C_BOLD}{biz_name}{C_RESET} (ID: {bid})",
        f" Ulasan : {C_GREEN}{reviewed_count} Sukses Terbit{C_RESET} │ {C_YELLOW}{pending_count} Antrean Pending{C_RESET} │ {C_WHITE}{len(reviews)} Total Record{C_RESET}",
        "─" * 64,
        f" {C_YELLOW}[1]{C_RESET} {C_WHITE}🗑️  HAPUS SEMUA ULASAN DI DATABASE{C_RESET}     {C_DIM}Bersihkan seluruh record ulasan target ini{C_RESET}",
        f" {C_YELLOW}[2]{C_RESET} {C_WHITE}🔍  HAPUS ULASAN TERTENTU (PER ID){C_RESET}      {C_DIM}Pilih ID review tertentu yang ingin dihapus{C_RESET}",
        f" {C_YELLOW}[3]{C_RESET} {C_RED}🛑  HAPUS ULASAN LANGSUNG DI GOOGLE MAPS{C_RESET} {C_DIM}Buka Chromium CDP hapus ulasan terbit{C_RESET}",
        f" {C_YELLOW}[0]{C_RESET} {C_DIM}↩   BATAL & KEMBALI KE MENU UTAMA{C_RESET}",
    ]
    print_box(sub_lines, width=68, title=f"{C_BOLD}{C_CYAN}PILIH METODE REMOVE ULASAN{C_RESET}")

    try:
        sub_choice = input(f"\n {C_GREEN}Pilih opsi [0-3]: {C_RESET}").strip()
    except (KeyboardInterrupt, EOFError):
        return

    if sub_choice == "1":
        # Hapus semua ulasan di database
        if len(reviews) == 0:
            print(f"\n {C_YELLOW}Tidak ada record ulasan tersimpan untuk target ini.{C_RESET}")
            input(f"\n {C_DIM}Tekan Enter untuk kembali...{C_RESET}")
            return

        confirm = input(f"\n {C_BOLD}{C_RED}Yakin ingin menghapus SEMUA ({len(reviews)}) ulasan untuk '{biz_name}' dari database? [y/N]: {C_RESET}").strip().lower()
        if confirm in ("y", "yes"):
            spin = Spinner(f"Menghapus seluruh ulasan target ID {bid}...")
            spin.start()
            try:
                res = client.delete_all_reviews(bid)
                spin.stop(f"\n {C_GREEN}✓ {res.get('message', 'Semua ulasan di database berhasil dihapus.')}{C_RESET}")
            except Exception as exc:
                spin.stop()
                print(f"\n {C_RED}✖ Gagal menghapus ulasan: {exc}{C_RESET}")
        else:
            print(f" {C_DIM}Dibatalkan.{C_RESET}")
        input(f"\n {C_DIM}Tekan Enter untuk kembali...{C_RESET}")

    elif sub_choice == "2":
        # Hapus ulasan per ID
        if len(reviews) == 0:
            print(f"\n {C_YELLOW}Tidak ada record ulasan untuk target ini.{C_RESET}")
            input(f"\n {C_DIM}Tekan Enter untuk kembali...{C_RESET}")
            return

        print(f"\n {C_BOLD}{C_CYAN}DAFTAR RECORD ULASAN UNTUK '{biz_name}':{C_RESET}")
        print(f" {'ID':<6} {'STATUS':<12} {'RATING':<8} {'AKUN EMAIL':<26} {'CUPLIKAN TEKS'}")
        print(" " + "─" * 68)
        for r in reviews[:25]:
            rid = r.get("id")
            st = (r.get("status") or "pending").upper()
            stars = f"{r.get('star_rating') or 5} ★"
            email = (r.get("email") or "-")[:25]
            text = (r.get("review_text") or "-").replace("\n", " ")[:20]
            st_color = C_GREEN if st in ("REVIEWED", "POSTED") else C_YELLOW if st == "PENDING" else C_RED
            print(f" {C_BOLD}#{rid:<5}{C_RESET} {st_color}{st:<12}{C_RESET} {C_YELLOW}{stars:<8}{C_RESET} {C_CYAN}{email:<26}{C_RESET} {C_DIM}{text}...{C_RESET}")

        if len(reviews) > 25:
            print(f" {C_DIM}... dan {len(reviews) - 25} record ulasan lainnya.{C_RESET}")

        try:
            del_rid_in = input(f"\n {C_GREEN}Masukkan ID Review yang ingin dihapus (0 untuk batal): {C_RESET}").strip()
            if del_rid_in and del_rid_in.isdigit() and del_rid_in != "0":
                del_rid = int(del_rid_in)
                spin = Spinner(f"Menghapus review #{del_rid}...")
                spin.start()
                try:
                    res = client.delete_single_review(bid, del_rid)
                    spin.stop(f"\n {C_GREEN}✓ Review #{del_rid} berhasil dihapus dari database.{C_RESET}")
                except Exception as exc:
                    spin.stop()
                    print(f"\n {C_RED}✖ Gagal menghapus review #{del_rid}: {exc}{C_RESET}")
        except (KeyboardInterrupt, EOFError):
            pass
        input(f"\n {C_DIM}Tekan Enter untuk kembali...{C_RESET}")

    elif sub_choice == "3":
        # Hapus ulasan langsung di Google Maps via Live Chromium CDP
        if reviewed_count == 0:
            print(f"\n {C_YELLOW}Tidak terdeteksi ulasan terbit (status 'reviewed') dari akun sendiri untuk target ini.{C_RESET}")
            input(f"\n {C_DIM}Tekan Enter untuk kembali...{C_RESET}")
            return

        print(f"\n {C_BOLD}{C_YELLOW}⚠️  PERHATIAN: PROSES PENGHAPUSAN LANGSUNG DI GOOGLE MAPS PUBLIK{C_RESET}")
        print(f" {C_DIM}Chromium akan login menggunakan cookie akun bot yang pernah mengulas target ini,{C_RESET}")
        print(f" {C_DIM}membuka profil Maps tempat, mencari ulasan sendiri, dan menekan tombol 'Delete Review'.{C_RESET}")
        confirm = input(f"\n {C_BOLD}{C_RED}Luncurkan bot Chromium untuk MENGHAPUS {reviewed_count} ulasan di Google Maps? [y/N]: {C_RESET}").strip().lower()
        if confirm in ("y", "yes"):
            spin = Spinner("Meluncurkan worker Chromium untuk hapus ulasan di Google Maps...")
            spin.start()
            try:
                res = client.delete_maps_reviews_live(bid)
                spin.stop(f"\n {C_GREEN}✓ {res.get('message', 'Worker Chromium diluncurkan untuk menghapus ulasan di Google Maps.')}{C_RESET}")
            except Exception as exc:
                spin.stop()
                print(f"\n {C_RED}✖ Gagal meluncurkan: {exc}{C_RESET}")
        else:
            print(f" {C_DIM}Dibatalkan.{C_RESET}")
        input(f"\n {C_DIM}Tekan Enter untuk kembali...{C_RESET}")


# ── Task Execution & Live Log Monitor ─────────────────────────────────────────

def format_task_log_line(ts: str, lvl: str, msg: str, email: str = "", account_name: str = "") -> str:
    """Format single log entry into a unified CLI tree branch with vertical trunk | and -> process indicator."""
    m_bracket = re.match(r"^\[([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)\]\s*(.*)", msg)
    if m_bracket:
        detected_email = m_bracket.group(1)
        clean_msg = m_bracket.group(2).strip()
    else:
        detected_email = email
        clean_msg = msg.strip()

    if detected_email:
        acc_str = account_name.strip() if account_name else ""
        if acc_str and acc_str.lower() != detected_email.lower():
            label = f"{acc_str} • {detected_email.split('@')[0]}"
        else:
            label = detected_email
        actor_badge = f"{C_BOLD}{C_CYAN}[{label[:26]}]{C_RESET}"
    elif any(w in clean_msg.lower() for w in ("worker", "antrean", "tugas masuk", "jadwal", "delay", "slot")):
        actor_badge = f"{C_YELLOW}[SISTEM WORKER]{C_RESET}"
    else:
        actor_badge = f"{C_BLUE}[SISTEM BROWSER]{C_RESET}"

    if lvl == "success":
        arrow = f"{C_GREEN}──>{C_RESET}"
        msg_out = f"{C_BOLD}{C_GREEN}✓ {clean_msg}{C_RESET}"
    elif lvl in ("error", "fatal"):
        arrow = f"{C_RED}──>{C_RESET}"
        msg_out = f"{C_BOLD}{C_RED}✖ {clean_msg}{C_RESET}"
    elif lvl == "warning":
        arrow = f"{C_YELLOW}──>{C_RESET}"
        msg_out = f"{C_YELLOW}▲ {clean_msg}{C_RESET}"
    else:
        arrow = f"{C_CYAN}──>{C_RESET}"
        msg_out = f"{C_WHITE}{clean_msg}{C_RESET}"

    return f" {C_CYAN}│   ├──{C_RESET} {C_DIM}{ts}{C_RESET} {arrow} {actor_badge} {arrow} {msg_out}"


def run_task_stream(
    client: ServerClient,
    business_id: int,
    count: int = 1,
    star_rating: int = 5,
    business_name: str = "",
    active_accounts: Optional[List[Dict[str, Any]]] = None,
):
    print()
    print(f" {C_CYAN}┌── [2/3] MEMPERSIAPKAN TUGAS ULASAN BOT{C_RESET}")
    biz_label = business_name if business_name else f"Bisnis #{business_id}"
    print(f" {C_CYAN}│   ├──{C_RESET} {C_DIM}Target Bisnis{C_RESET}  ──────> {C_WHITE}{biz_label}{C_RESET}")
    print(f" {C_CYAN}│   ├──{C_RESET} {C_DIM}Jumlah Browser{C_RESET} ─────> {C_CYAN}{count} Layar Chromium Paralel{C_RESET}")
    star_str = "⭐" * star_rating
    print(f" {C_CYAN}│   └──{C_RESET} {C_DIM}Rating Target{C_RESET}  ─────> {C_YELLOW}{star_str}{C_RESET} {C_DIM}({star_rating} Bintang){C_RESET}")
    print(f" {C_CYAN}│{C_RESET}")
    print(f" {C_CYAN}├── [PENUGASAN SLOT BROWSER & DISPLAY]{C_RESET}")

    assigned = (active_accounts or [])[:count]
    for s_idx in range(count):
        disp = f":{99 + s_idx}"
        is_last = (s_idx == count - 1)
        sub_branch = "└──" if is_last else "├──"
        if s_idx < len(assigned):
            acc = assigned[s_idx]
            aname = (acc.get("account_name") or "").strip()
            aemail = acc.get("email", "")
            lbl = f"{aname} ({aemail})" if aname and aname != aemail else aemail
        else:
            lbl = f"Akun Aktif Slot #{s_idx + 1}"
        print(f" {C_CYAN}│   {sub_branch}{C_RESET} [Slot {s_idx + 1}] Display {disp} ──> {C_WHITE}{lbl}{C_RESET} ──> {C_GREEN}[SIAP]{C_RESET}")
        time.sleep(0.04)

    print(f" {C_CYAN}│{C_RESET}")
    print(f" {C_CYAN}├── [PENGIRIMAN INSTRUKSI KE SERVER]{C_RESET}")

    spin = Spinner("Mengirim instruksi task dan menginisialisasi browser di server...")
    spin.start()
    try:
        res = client.start_task(business_id, count=count, star_rating=star_rating)
        spin.stop(f" {C_CYAN}│   └──{C_RESET} Dispatch API ───────> {C_BOLD}{C_GREEN}[BERHASIL DIJADWALKAN 🚀]{C_RESET} (Jobs: {res.get('jobs_created', count)}, Antrean: {res.get('already_pending', 0)})")
    except Exception as exc:
        spin.stop()
        print(f" {C_CYAN}│   └──{C_RESET} Dispatch API ───────> {C_BOLD}{C_RED}[GAGAL: {exc}]{C_RESET}")
        print(f" {C_CYAN}│{C_RESET}")
        print(f" {C_CYAN}└──{C_RESET} {C_RED}Task ulasan dibatalkan karena gagal menghubungi server.{C_RESET}")
        return False

    print(f" {C_CYAN}│{C_RESET}")
    print(f" {C_CYAN}├── [3/3] LIVE PROCESS LOGS (SERVER CHROMIUM){C_RESET}")
    print(f" {C_CYAN}│   {C_DIM}Memantau alur ulasan browser per akun secara live... (Tekan Ctrl+C untuk kembali){C_RESET}")
    print(f" {C_CYAN}│{C_RESET}")

    seen_ids = set()
    start_time = time.time()
    task_finished = False
    sp_idx = 0
    last_poll_time = 0.0
    status = "idle"

    try:
        while True:
            now = time.time()
            elapsed_sec = int(now - start_time)
            mins = elapsed_sec // 60
            secs = elapsed_sec % 60
            time_str = f"{mins:02d}:{secs:02d}s"

            # Poll API every 0.8 seconds
            if now - last_poll_time >= 0.8:
                last_poll_time = now
                try:
                    log_data = client.get_logs(business_id)
                    logs = log_data.get("logs", [])
                    status = log_data.get("status", "idle")

                    new_logs = [l for l in logs if l["id"] not in seen_ids]
                    for l in new_logs:
                        seen_ids.add(l["id"])
                        lvl = (l.get("level") or "info").lower()
                        ts = l.get("created_at", "").split()[-1]
                        msg = l.get("message", "")
                        l_email = l.get("email", "")
                        l_aname = l.get("account_name", "")

                        # Clear spinner line and print log branch
                        sys.stdout.write("\r\033[K")
                        line_out = format_task_log_line(ts, lvl, msg, email=l_email, account_name=l_aname)
                        print(line_out)

                        if "Worker selesai memproses" in msg or "berhasil dikirim" in msg:
                            task_finished = True

                    if task_finished and status == "idle":
                        break
                except Exception:
                    pass

            # Animate spinner on current bottom line (connected to tree trunk)
            sp_idx += 1
            sp_char = SPINNER_FRAMES[sp_idx % len(SPINNER_FRAMES)]
            st_badge = f"{C_GREEN}{status.upper()}{C_RESET}" if status in ("running", "reviewing") else f"{C_YELLOW}{status.upper()}{C_RESET}"
            sys.stdout.write(f"\r {C_CYAN}│   {sp_char}{C_RESET} {C_WHITE}Status: {st_badge} │ {C_DIM}Waktu:{C_RESET} {C_GREEN}{time_str}{C_RESET} │ {C_DIM}Tekan Ctrl+C untuk kembali{C_RESET}\033[K")
            sys.stdout.flush()
            time.sleep(0.09)

    except KeyboardInterrupt:
        sys.stdout.write("\r\033[K")
        print(f" {C_CYAN}│{C_RESET}")
        print(f" {C_CYAN}└──{C_RESET} {C_YELLOW}! Pemantauan live dihentikan oleh user. Tugas ulasan tetap berjalan di background server.{C_RESET}")
        return True

    sys.stdout.write("\r\033[K")
    elapsed = int(time.time() - start_time)
    print(f" {C_CYAN}│{C_RESET}")
    print(f" {C_CYAN}└──{C_RESET} {C_BOLD}{C_GREEN}✓ Seluruh proses ulasan selesai dalam {elapsed} detik!{C_RESET}")
    return True


# ── Interactive Menu Loop ─────────────────────────────────────────────────────

def interactive_menu(client: ServerClient):
    # Wajib login terlebih dahulu sebelum masuk ke sesi task dan menampilkan daftar menu
    if not client.api_key:
        prompt_login(client)

    while True:
        spin = Spinner("Menghubungkan & memuat status server...")
        spin.start()
        try:
            status_info = client.get_status()
            spin.stop()
        except Exception as e:
            spin.stop()
            print(f"\n {C_RED}✖ Gagal menghubungi server {client.base_url}: {e}{C_RESET}")
            print(f" Pastikan server AutoBotix aktif di jaringan (IP: {client.base_url}).")
            try:
                retry = input(f"\n [1] Coba Lagi  [2] Ganti Login  [0] Keluar: ").strip()
                if retry == "2":
                    client.api_key = ""
                    prompt_login(client)
                    continue
                elif retry == "0":
                    break
            except (KeyboardInterrupt, EOFError):
                break
            continue

        os.system("cls" if os.name == "nt" else "clear")
        print_banner(client, status_info)

        cookie_menu_label = (
            f" {C_YELLOW}[4]{C_RESET} {C_WHITE}🍪  KELOLA COOKIE (ADMIN){C_RESET}   {C_DIM}Status, Tambah & Hapus Cookie Sesi{C_RESET}"
            if client.is_admin else
            f" {C_YELLOW}[4]{C_RESET} {C_WHITE}🍪  STATUS COOKIE{C_RESET}        {C_DIM}Cek validitas akun Google & sesi CDP{C_RESET}"
        )

        menu_lines = [
            f" {C_YELLOW}[1]{C_RESET} {C_WHITE}🚀  JALANKAN TASK{C_RESET}        {C_DIM}Mulai ulasan multi-browser otomatis{C_RESET}",
            f" {C_YELLOW}[2]{C_RESET} {C_WHITE}🏢  TARGET GOOGLE MAPS{C_RESET}   {C_DIM}Lihat daftar target & jumlah review{C_RESET}",
            f" {C_YELLOW}[3]{C_RESET} {C_WHITE}➕  TAMBAH BISNIS BARU{C_RESET}   {C_DIM}Daftarkan URL Google Maps baru{C_RESET}",
            cookie_menu_label,
            f" {C_YELLOW}[5]{C_RESET} {C_WHITE}📊  PANTAU LIVE LOGS{C_RESET}     {C_DIM}Lihat log proses aktivitas server{C_RESET}",
            f" {C_YELLOW}[6]{C_RESET} {C_WHITE}🛑  EMERGENCY STOP{C_RESET}       {C_DIM}Hentikan semua worker & browser{C_RESET}",
            f" {C_YELLOW}[7]{C_RESET} {C_WHITE}🔄  RESET ANTREAN{C_RESET}        {C_DIM}Bersihkan antrean ulasan & log bisnis{C_RESET}",
            f" {C_YELLOW}[8]{C_RESET} {C_WHITE}🗑️   REMOVE ULASAN{C_RESET}        {C_DIM}Hapus ulasan database atau Google Maps{C_RESET}",
            f" {C_YELLOW}[0]{C_RESET} {C_RED}🚪  LOGOUT & KELUAR{C_RESET}      {C_DIM}Keluar dari sesi terminal{C_RESET}",
        ]
        print_box(menu_lines, width=68, title=f"{C_BOLD}{C_CYAN}DAFTAR MENU UTAMA{C_RESET}")

        try:
            choice = input(f" {C_GREEN}Pilih menu [0-8] (default 1): {C_RESET}").strip() or "1"
        except (KeyboardInterrupt, EOFError):
            print("\n Keluar.")
            break

        if choice == "0":
            client.api_key = ""
            print(f"\n {C_DIM}Anda telah logout. Terima kasih telah menggunakan AutoBotix CLI. Sampai jumpa!{C_RESET}")
            break

        elif choice == "1":
            print()
            print(f" {C_CYAN}┌── [1/3] MEMERIKSA KESIAPAN AKUN GOOGLE{C_RESET}")
            print(f" {C_CYAN}│{C_RESET}   {C_DIM}Memvalidasi status sesi & profil akun dari database server...{C_RESET}")
            print(f" {C_CYAN}│{C_RESET}")

            spin = Spinner("Memuat data akun dan status sesi Google...")
            spin.start()
            try:
                cur_status = client.get_status()
                spin.stop()
            except Exception as e:
                spin.stop()
                print(f" {C_CYAN}│   └──{C_RESET} {C_RED}Gagal memuat status: {e}{C_RESET}")
                print(f" {C_CYAN}│{C_RESET}")
                print(f" {C_CYAN}└──{C_RESET} {C_RED}Task ulasan dibatalkan.{C_RESET}")
                input(f"\n {C_DIM}Tekan Enter untuk kembali...{C_RESET}")
                continue

            accounts = cur_status.get("accounts", [])
            active_accs = [a for a in accounts if a.get("cookie_status") == "active"]

            # Visualisasi tree per akun dengan status dan panah alur
            limit_show = 12
            to_show = accounts[:limit_show] if accounts else []
            for idx, a in enumerate(to_show, 1):
                is_last = (idx == len(to_show) and len(accounts) <= limit_show)
                branch = "└──" if is_last else "├──"
                c_st = a.get("cookie_status") or "no_cookie"
                acc_name = (a.get("account_name") or "").strip()
                email = a.get("email", "")
                if acc_name:
                    lbl = f"{C_BOLD}{acc_name}{C_RESET} {C_DIM}({email}){C_RESET}"
                else:
                    lbl = f"{C_CYAN}{email}{C_RESET}"

                if c_st == "active":
                    badge = f"{C_GREEN}● AKTIF{C_RESET} {C_DIM}[Siap Digunakan]{C_RESET}"
                elif c_st == "needs_login":
                    badge = f"{C_YELLOW}▲ PERLU LOGIN{C_RESET} {C_DIM}[Dilewati]{C_RESET}"
                elif c_st == "expired":
                    badge = f"{C_RED}✖ KEDALUWARSA{C_RESET} {C_DIM}[Dilewati]{C_RESET}"
                else:
                    badge = f"{C_DIM}- TIDAK ADA COOKIE - [Dilewati]{C_RESET}"

                print(f" {C_CYAN}│   {branch}{C_RESET} [Akun {idx}] {lbl} ────> {badge}")
                time.sleep(0.02)

            if len(accounts) > limit_show:
                rem = len(accounts) - limit_show
                print(f" {C_CYAN}│   └──{C_RESET} {C_DIM}... dan {rem} akun lainnya terdata di database{C_RESET}")

            print(f" {C_CYAN}│{C_RESET}")
            if not active_accs:
                print(f" {C_CYAN}└──{C_RESET} {C_BOLD}{C_RED}✖ Tidak dapat menjalankan task: Tidak ada akun dengan status AKTIF.{C_RESET}")
                print(f"     {C_YELLOW}Semua akun saat ini berstatus 'PERLU LOGIN' atau belum memiliki cookie valid.{C_RESET}")
                print(f"     {C_DIM}Silakan periksa atau tambahkan cookie aktif terlebih dahulu di menu [4] Status Cookie.{C_RESET}")
                input(f"\n {C_DIM}Tekan Enter untuk kembali...{C_RESET}")
                continue

            print(f" {C_CYAN}└──{C_RESET} {C_BOLD}{C_GREEN}✓ Terdeteksi {len(active_accs)} akun dengan sesi AKTIF siap menjalankan ulasan.{C_RESET}")

            businesses = cur_status.get("businesses", [])
            print_businesses(businesses)
            if not businesses:
                input(" Tekan Enter untuk kembali...")
                continue

            try:
                bid_in = input(f" {C_GREEN}Masukkan ID Bisnis target: {C_RESET}").strip()
                if not bid_in.isdigit():
                    print(f" {C_RED}ID tidak valid.{C_RESET}")
                    time.sleep(1)
                    continue
                bid = int(bid_in)
                target_biz = next((b for b in businesses if b.get("id") == bid), None)
                biz_name = target_biz.get("name", f"Bisnis #{bid}") if target_biz else f"Bisnis #{bid}"

                max_slots = max(1, min(6, len(active_accs)))
                slots_in = input(f" {C_GREEN}Jumlah Browser / Akun Paralel (1-{max_slots}, default 1): {C_RESET}").strip() or "1"
                slots = max(1, min(max_slots, int(slots_in) if slots_in.isdigit() else 1))

                stars_in = input(f" {C_GREEN}Rating Bintang (1-5, default 5): {C_RESET}").strip() or "5"
                stars = max(1, min(5, int(stars_in) if stars_in.isdigit() else 5))

                confirm = input(f"\n {C_BOLD}Jalankan {slots} ulasan bintang {stars} untuk '{biz_name}' (ID {bid}) sekarang? [Y/n]: {C_RESET}").strip().lower()
                if confirm in ("", "y", "yes"):
                    run_task_stream(client, bid, count=slots, star_rating=stars, business_name=biz_name, active_accounts=active_accs)
            except Exception as exc:
                print(f" {C_RED}Error: {exc}{C_RESET}")

            input(f"\n {C_DIM}Tekan Enter untuk kembali ke menu...{C_RESET}")

        elif choice == "2":
            print_businesses(status_info.get("businesses", []))
            input(f" {C_DIM}Tekan Enter untuk kembali...{C_RESET}")

        elif choice == "3":
            print(f"\n {C_BOLD}{C_CYAN}=== TAMBAH TARGET BISNIS BARU ==={C_RESET}")
            name = input(f" {C_GREEN}Nama Bisnis / Tempat: {C_RESET}").strip()
            url = input(f" {C_GREEN}URL Google Maps: {C_RESET}").strip()
            cat = input(f" {C_GREEN}Kategori Bisnis (default General): {C_RESET}").strip() or "General"
            if name and url:
                spin = Spinner(f"Mendaftarkan bisnis '{name}' di server...")
                spin.start()
                try:
                    res = client.add_business(name, url, cat)
                    spin.stop(f"\n {C_GREEN}✓ Bisnis '{name}' berhasil didaftarkan di server!{C_RESET}")
                except Exception as e:
                    spin.stop()
                    print(f"\n {C_RED}✖ Gagal menambahkan: {e}{C_RESET}")
            else:
                print(f" {C_YELLOW}Nama dan URL wajib diisi.{C_RESET}")
            input(f"\n {C_DIM}Tekan Enter untuk kembali...{C_RESET}")

        elif choice == "4":
            handle_cookie_menu(client, status_info)

        elif choice == "5":
            businesses = status_info.get("businesses", [])
            print_businesses(businesses)
            bid_in = input(f" {C_GREEN}Masukkan ID Bisnis yang ingin dipantau log-nya: {C_RESET}").strip()
            if bid_in.isdigit():
                bid = int(bid_in)
                spin = Spinner(f"Memuat log untuk Bisnis ID {bid}...")
                spin.start()
                try:
                    log_data = client.get_logs(bid)
                    logs = log_data.get("logs", [])
                    spin.stop()
                    print(f"\n {C_BOLD}{C_CYAN}--- LOG TERBARU (ID {bid}) ---{C_RESET}")
                    for l in logs[-20:]:
                        print(f"  {C_DIM}{l.get('created_at')}{C_RESET} [{l.get('level').upper()}] {l.get('message')}")
                except Exception as e:
                    spin.stop()
                    print(f" {C_RED}Gagal memuat log: {e}{C_RESET}")
            input(f"\n {C_DIM}Tekan Enter untuk kembali...{C_RESET}")

        elif choice == "6":
            businesses = status_info.get("businesses", [])
            print_businesses(businesses)
            bid_in = input(f" {C_GREEN}Masukkan ID Bisnis yang ingin dihentikan task-nya: {C_RESET}").strip()
            if bid_in.isdigit():
                spin = Spinner("Mengirim perintah stop ke server...")
                spin.start()
                try:
                    res = client.stop_task(int(bid_in))
                    spin.stop(f" {C_GREEN}✓ {res.get('message', 'Perintah stop berhasil dikirim ke server.')}{C_RESET}")
                except Exception as e:
                    spin.stop()
                    print(f" {C_RED}Gagal menghentikan: {e}{C_RESET}")
            input(f"\n {C_DIM}Tekan Enter untuk kembali...{C_RESET}")

        elif choice == "7":
            businesses = status_info.get("businesses", [])
            print_businesses(businesses)
            bid_in = input(f" {C_GREEN}Masukkan ID Bisnis yang ingin dibersihkan log-nya: {C_RESET}").strip()
            if bid_in.isdigit():
                spin = Spinner("Membersihkan antrean & log...")
                spin.start()
                try:
                    res = client.clear_logs(int(bid_in))
                    spin.stop(f" {C_GREEN}✓ {res.get('message', 'Log berhasil dibersihkan.')}{C_RESET}")
                except Exception as e:
                    spin.stop()
                    print(f" {C_RED}Gagal membersihkan log: {e}{C_RESET}")
            input(f"\n {C_DIM}Tekan Enter untuk kembali...{C_RESET}")

        elif choice == "8":
            handle_remove_review_menu(client, status_info)


# ── CLI Arguments Entrypoint ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AutoBotix Review Automation Windows Client")
    parser.add_argument("--server", "-H", default=DEFAULT_SERVER, help=f"URL Server AutoBotix (default: {DEFAULT_SERVER})")
    parser.add_argument("--user", "-u", default=None, help="Username login server (default: admin)")
    parser.add_argument("--password", "-p", default=None, help="Password login server")
    parser.add_argument("--key", "-k", default=DEFAULT_API_KEY, help="API Key / Password Server (opsional)")

    subparsers = parser.add_subparsers(dest="command")

    # Command: run
    run_parser = subparsers.add_parser("run", help="Jalankan tugas ulasan langsung")
    run_parser.add_argument("--business", "-b", type=int, required=True, help="ID Bisnis target")
    run_parser.add_argument("--slots", "-s", type=int, default=1, help="Jumlah browser paralel (1-6)")
    run_parser.add_argument("--stars", type=int, default=5, help="Rating bintang (1-5)")

    # Command: status
    subparsers.add_parser("status", help="Lihat status server")

    # Command: businesses
    subparsers.add_parser("businesses", help="Daftar seluruh bisnis target")

    # Command: accounts
    subparsers.add_parser("accounts", help="Daftar akun & cookie")

    # Command: cookies
    subparsers.add_parser("cookies", help="Daftar cookie Google")

    # Command: cookie-add
    p_cadd = subparsers.add_parser("cookie-add", help="Tambah cookie sesi Google (Admin)")
    p_cadd.add_argument("--json", help="Raw JSON string cookie")
    p_cadd.add_argument("--file", help="Jalur file .json cookie")
    p_cadd.add_argument("--email", default="", help="Email akun Google (opsional)")

    # Command: cookie-del
    p_cdel = subparsers.add_parser("cookie-del", help="Hapus cookie sesi Google (Admin)")
    p_cdel.add_argument("--id", type=int, help="ID Cookie yang ingin dihapus")
    p_cdel.add_argument("--email", default="", help="Email akun Google yang ingin dihapus")

    # Command: review-del
    p_rdel = subparsers.add_parser("review-del", help="Hapus ulasan target bisnis")
    p_rdel.add_argument("--business", "-b", type=int, required=True, help="ID Bisnis target")
    p_rdel.add_argument("--review-id", "-r", type=int, default=None, help="ID Review tertentu (opsional)")
    p_rdel.add_argument("--maps", action="store_true", help="Hapus langsung di Google Maps via Chromium")

    args = parser.parse_args()
    client = ServerClient(base_url=args.server, api_key=args.key or "")

    # Auto-login if credentials provided via arguments
    if args.user and args.password:
        try:
            client.login(args.user, args.password)
        except Exception as exc:
            print(f"{C_RED}✖ Gagal login dengan akun {args.user}: {exc}{C_RESET}")
            sys.exit(1)

    if not args.command:
        # Masuk sesi interaktif: prompt login terlebih dahulu, lalu tampilkan daftar menu
        interactive_menu(client)
    else:
        # Non-interactive command: jika belum authenticated, prompt login dahulu
        if not client.api_key:
            prompt_login(client, default_user=args.user or "admin")

        if args.command == "status":
            info = client.get_status()
            print_banner(client, info)
        elif args.command == "businesses":
            print_businesses(client.get_businesses())
        elif args.command == "accounts":
            print_accounts(client.get_accounts())
        elif args.command == "cookies":
            st = client.get_status()
            print_cookies_table(st.get("cookies", []))
        elif args.command == "cookie-add":
            if not client.is_admin:
                print(f"{C_RED}✖ Fitur tambah cookie hanya untuk akun Administrator.{C_RESET}")
                sys.exit(1)
            raw = args.json or ""
            if not raw and args.file:
                with open(os.path.expanduser(args.file), "r", encoding="utf-8") as f:
                    raw = f.read()
            if not raw:
                print(f"{C_RED}✖ Masukkan --json atau --file.{C_RESET}")
                sys.exit(1)
            res = client.add_cookie(raw, email=args.email)
            print(f"{C_GREEN}✓ Cookie berhasil disimpan untuk akun '{res.get('email')}'! Status: {res.get('session_status')}{C_RESET}")
        elif args.command == "cookie-del":
            if not client.is_admin:
                print(f"{C_RED}✖ Fitur hapus cookie hanya untuk akun Administrator.{C_RESET}")
                sys.exit(1)
            if not args.id and not args.email:
                print(f"{C_RED}✖ Masukkan --id atau --email untuk dihapus.{C_RESET}")
                sys.exit(1)
            res = client.delete_cookie(cookie_id=args.id, email=args.email)
            print(f"{C_GREEN}✓ {res.get('message', 'Cookie berhasil dihapus.')}{C_RESET}")
        elif args.command == "run":
            run_task_stream(client, args.business, count=args.slots, star_rating=args.stars)
        elif args.command == "review-del":
            if args.maps:
                res = client.delete_maps_reviews_live(args.business)
                print(f"{C_GREEN}✓ {res.get('message', 'Worker Chromium diluncurkan untuk menghapus ulasan di Google Maps.')}{C_RESET}")
            elif args.review_id:
                res = client.delete_single_review(args.business, args.review_id)
                print(f"{C_GREEN}✓ Review #{args.review_id} berhasil dihapus dari database.{C_RESET}")
            else:
                res = client.delete_all_reviews(args.business)
                print(f"{C_GREEN}✓ {res.get('message', 'Semua ulasan di database berhasil dihapus.')}{C_RESET}")


if __name__ == "__main__":
    main()
