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
import shutil
import subprocess
import sys
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any, Dict, List, Optional

# Version Tracking & Manifest
CLI_VERSION = "v1.0.5"
CLI_VERSION_CODE = 105

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
            if "192.168.1.17" in self.base_url:
                try:
                    self.base_url = "https://autobotix.my.id"
                    url = f"{self.base_url}/api/cli/login"
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
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                        if data.get("authenticated"):
                            self.api_key = data.get("api_key") or password
                            self.username = data.get("username", username)
                            self.role = data.get("role", "administrator" if self.username.lower() == "admin" else "user")
                            self.is_admin = (self.role == "administrator" or self.username.lower() in ("admin",))
                            return data
                except Exception:
                    self.base_url = "http://192.168.1.17:5000"
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
            if "192.168.1.17" in self.base_url:
                try:
                    self.base_url = "https://autobotix.my.id"
                    url = f"{self.base_url}/api/cli/login"
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
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                        if data.get("authenticated"):
                            self.api_key = data.get("api_key") or password
                            self.username = data.get("username", username)
                            self.role = data.get("role", "administrator" if self.username.lower() == "admin" else "user")
                            self.is_admin = (self.role == "administrator" or self.username.lower() in ("admin",))
                            return data
                except Exception:
                    self.base_url = "http://192.168.1.17:5000"
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
            if "192.168.1.17" in self.base_url:
                try:
                    self.base_url = "https://autobotix.my.id"
                    url = f"{self.base_url}{endpoint}"
                    req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)
                    with urllib.request.urlopen(req, timeout=12) as resp:
                        resp_text = resp.read().decode("utf-8")
                        try:
                            return json.loads(resp_text)
                        except Exception:
                            return {"status": "ok", "raw": resp_text}
                except Exception:
                    self.base_url = "http://192.168.1.17:5000"
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

    def test_all_cookies(self) -> Dict[str, Any]:
        """Trigger batch verification of all Google account sessions live."""
        return self._request("/api/cli/cookies/test-all", method="POST")

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

    def start_task(self, business_id: int, count: int = 1, star_rating: int = 5, mode: str = "queue", delay: int = 60) -> Dict[str, Any]:
        payload = {
            "count": count,
            f"star_{star_rating}_count": count,
            "selected_language": "Indonesian",
            "mode": mode,
            "delay_seconds": delay,
            "screen_count": 1 if mode == "queue" else count,
        }
        return self._request(f"/api/businesses/{business_id}/start-bot", method="POST", data=payload)

    def get_queue(self, business_id: Optional[int] = None) -> Dict[str, Any]:
        """Fetch active review queue."""
        ep = f"/api/businesses/{business_id}/queue" if business_id else "/api/queue"
        return self._request(ep)

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

    def delete_maps_reviews_live(self, business_id: int, email_id: Optional[int] = None, all_accounts: bool = False) -> Dict[str, Any]:
        """Delete own posted reviews directly on Google Maps via live Chromium bot."""
        payload = {}
        if email_id:
            payload["email_id"] = email_id
        if all_accounts:
            payload["all_accounts"] = True
        return self._request(f"/api/businesses/{business_id}/dark-mode/delete-maps-reviews", method="POST", data=payload)

    def get_cli_version(self) -> Dict[str, Any]:
        """Fetch version manifest and check for newer releases from server."""
        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/cli/version",
                headers={"User-Agent": f"AutoBotix-Windows-CLI/{CLI_VERSION}"},
            )
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            return {}

    def download_cli_update(self) -> Optional[str]:
        """Download latest bot_cli.py source directly from server."""
        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/cli/download",
                headers={"User-Agent": f"AutoBotix-Windows-CLI/{CLI_VERSION}"},
            )
            with urllib.request.urlopen(req, timeout=12.0) as resp:
                return resp.read().decode("utf-8")
        except Exception:
            return None


# ── UI Helpers & Animation ───────────────────────────────────────────────────

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


def truncate_ansi(s: str, max_w: int) -> str:
    """Safely truncate string containing ANSI color codes to max visible display width."""
    if max_w <= 0:
        return ""
    current_w = 0
    i = 0
    out = []
    has_ansi = False
    while i < len(s):
        m = ANSI_REGEX.match(s, i)
        if m:
            out.append(m.group(0))
            has_ansi = True
            i = m.end()
            continue
        ch = s[i]
        cw = 2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1
        if current_w + cw > max_w - 1:
            out.append("…")
            if has_ansi:
                out.append(C_RESET)
            return "".join(out)
        out.append(ch)
        current_w += cw
        i += 1
    if has_ansi:
        out.append(C_RESET)
    return "".join(out)


def get_terminal_width(default: int = 80) -> int:
    """Get active terminal column width with safe fallback."""
    try:
        cols = shutil.get_terminal_size((default, 24)).columns
        return max(35, cols)
    except Exception:
        return default


def clear_screen():
    """Clear terminal screen and scrollback buffer cleanly across Windows, Linux, and Termux."""
    if sys.platform == "win32":
        os.system("cls")
    else:
        # \033[2J clears screen, \033[H cursor to top-left, \033[3J clears scrollback buffer
        sys.stdout.write("\033[2J\033[H\033[3J")
        sys.stdout.flush()
        try:
            os.system("clear 2>/dev/null")
        except Exception:
            pass


def pad_to_display_width(text: str, width: int) -> str:
    """Pad string with spaces on right to reach exact target visible column width."""
    current_w = str_display_width(text)
    pad = max(0, width - current_w)
    return text + (' ' * pad)


SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


class Spinner:
    """Animated terminal spinner running in a background thread with strict mobile & Termux bounds."""

    def __init__(self, message: str = "Memproses..."):
        self.message = message
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def _spin(self):
        idx = 0
        # Hide cursor during spin to prevent blinking & position glitches in Termux
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()
        try:
            while self.running:
                frame = SPINNER_FRAMES[idx % len(SPINNER_FRAMES)]
                cols = get_terminal_width()
                # Frame + space takes 3 visible columns (" ⠋ ")
                max_msg_len = max(10, cols - 6)
                disp_msg = truncate_ansi(self.message, max_msg_len)
                sys.stdout.write(f"\r {C_CYAN}{frame}{C_RESET} {C_WHITE}{disp_msg}{C_RESET}\033[K")
                sys.stdout.flush()
                time.sleep(0.08)
                idx += 1
        finally:
            # Restore cursor
            sys.stdout.write("\033[?25h")
            sys.stdout.flush()

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
        # Clear line and restore cursor
        sys.stdout.write("\r\033[K\033[?25h")
        sys.stdout.flush()
        if final_text:
            cols = get_terminal_width()
            print(truncate_ansi(final_text, cols - 1) if str_display_width(final_text) >= cols else final_text)


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


def print_google_maps_logo(padding: Optional[str] = None):
    """Render Google Maps Icon text logo (seeklogo 268336) centered and responsive."""
    cols = get_terminal_width()
    logo_w = 45
    if padding is None:
        pad_len = max(0, min(18, (cols - logo_w) // 2))
        padding = " " * pad_len

    for line in GOOGLE_MAPS_ICON_LINES:
        l_text = line if cols >= 50 else line.strip()
        print(f"{padding}{l_text}")
    print()
    if cols >= 55:
        brand_colored = (
            f"{C_BOLD}{C_BLUE}G{C_RED}o{C_YELLOW}o{C_BLUE}g{C_GREEN}l{C_RED}e{C_RESET} "
            f"{C_BOLD}{C_WHITE}Maps{C_RESET} {C_BOLD}{C_CYAN}Review Automation Bot{C_RESET}"
        )
    else:
        brand_colored = (
            f"{C_BOLD}{C_BLUE}G{C_RED}o{C_YELLOW}o{C_BLUE}g{C_GREEN}l{C_RED}e{C_RESET} "
            f"{C_BOLD}{C_WHITE}Maps{C_RESET} {C_BOLD}{C_CYAN}Bot{C_RESET}"
        )
    b_w = str_display_width(brand_colored)
    b_pad = max(0, (cols - b_w) // 2)
    print(f"{' ' * b_pad}{brand_colored}")


def print_box(lines: List[str], width: int = 68, title: Optional[str] = None):
    """Print an automatically sized and aligned unicode box.
    Guarantees that every row's right border ║ aligns with the box corners
    and strictly does not wrap on Termux or narrow mobile screens.
    """
    cols = get_terminal_width()
    max_allowed = max(26, cols - 4)
    content_widths = [str_display_width(l) for l in lines]
    if title:
        content_widths.append(str_display_width(title))
    inner_width = min(max_allowed, max(min(width, max_allowed), max(content_widths) if content_widths else width))

    top = f" ╔{'═' * (inner_width + 2)}╗"
    sep = f" ╠{'═' * (inner_width + 2)}╣"
    bot = f" ╚{'═' * (inner_width + 2)}╝"

    print(top)
    if title:
        t_trunc = truncate_ansi(title, inner_width)
        t_w = str_display_width(t_trunc)
        t_pad_left = (inner_width - t_w) // 2
        t_pad_right = inner_width - t_w - t_pad_left
        print(f" ║ {' ' * t_pad_left}{t_trunc}{' ' * t_pad_right} ║")
        print(sep)

    for line in lines:
        line_fit = truncate_ansi(line, inner_width)
        cur_w = str_display_width(line_fit)
        pad = max(0, inner_width - cur_w)
        print(f" ║ {line_fit}{' ' * pad} ║")

    print(bot)


def box_header(title: str, width: int = 68):
    """Print a single-row boxed banner header with perfect alignment."""
    cols = get_terminal_width()
    max_allowed = max(26, cols - 4)
    t_trunc = truncate_ansi(title, max_allowed)
    t_w = str_display_width(t_trunc)
    inner_width = min(max_allowed, max(min(width, max_allowed), t_w))
    t_pad_left = (inner_width - t_w) // 2
    t_pad_right = inner_width - t_w - t_pad_left
    print(f" ╔{'═' * (inner_width + 2)}╗")
    print(f" ║ {' ' * t_pad_left}{t_trunc}{' ' * t_pad_right} ║")
    print(f" ╚{'═' * (inner_width + 2)}╝")


def print_header_screen(client: Optional[ServerClient] = None, title: Optional[str] = None, status_info: Optional[Dict[str, Any]] = None):
    """Clear screen and display the Google Maps logo & AutoBotix Header cleanly on any device."""
    clear_screen()
    cols = get_terminal_width()
    print()
    print_google_maps_logo()

    sub = "« Native Chromium • Zero-VM Architecture »"
    if cols < 50:
        sub = "Zero-VM Architecture"
    sub_pad = max(0, (cols - str_display_width(sub)) // 2)
    print(f"{' ' * sub_pad}{C_DIM}{sub}{C_RESET}")

    ver = f"AutoBotix CLI {CLI_VERSION}"
    ver_pad = max(0, (cols - str_display_width(ver)) // 2)
    print(f"{' ' * ver_pad}{C_BOLD}{C_GREEN}{ver}{C_RESET}")
    print()

    if client:
        user_label = client.username or "admin"
        if cols >= 68:
            lines = [
                f"{C_DIM}Host Server:{C_RESET} {C_GREEN}{client.base_url}{C_RESET}   {C_DIM}User:{C_RESET} {C_CYAN}{user_label}{C_RESET}   {C_DIM}Versi:{C_RESET} {C_YELLOW}{CLI_VERSION}{C_RESET}"
            ]
        else:
            lines = [
                f"{C_DIM}Host:{C_RESET} {C_GREEN}{client.base_url}{C_RESET}",
                f"{C_DIM}User:{C_RESET} {C_CYAN}{user_label}{C_RESET} │ {C_DIM}Versi:{C_RESET} {C_YELLOW}{CLI_VERSION}{C_RESET}"
            ]
        if status_info:
            b_cnt = status_info.get("businesses_count", 0)
            a_cnt = status_info.get("accounts_count", 0)
            c_cnt = status_info.get("active_cookies", 0)
            r_cnt = status_info.get("reviewed_count", 0)
            p_cnt = status_info.get("pending_count", 0)
            disps = " ".join(status_info.get("displays", []))
            if cols >= 68:
                lines.append(f"Target: {C_WHITE}{b_cnt}{C_RESET} │ Akun: {C_WHITE}{a_cnt}{C_RESET} │ Cookie: {C_WHITE}{c_cnt}{C_RESET} │ Ulasan: {C_WHITE}{r_cnt}{C_RESET} │ Antrean: {C_WHITE}{p_cnt}{C_RESET}")
                if disps:
                    lines.append(f"{C_DIM}Display Virtual Xvfb:{C_RESET} {C_CYAN}{disps}{C_RESET}")
            else:
                lines.append(f"Target: {C_WHITE}{b_cnt}{C_RESET} │ Akun: {C_WHITE}{a_cnt}{C_RESET} │ Cookie: {C_WHITE}{c_cnt}{C_RESET}")
                lines.append(f"Ulasan: {C_WHITE}{r_cnt}{C_RESET} │ Antrean: {C_WHITE}{p_cnt}{C_RESET}")
        print_box(lines, width=min(cols - 4, 68))

    if title:
        print()
        box_header(title, width=min(cols - 4, 68))
        print()


def print_banner(client: ServerClient, status_info: Optional[Dict[str, Any]] = None):
    print_header_screen(client=client, status_info=status_info)


def _do_login(client: ServerClient, default_user: str = "admin") -> bool:
    """Handle login input and verification."""
    import getpass

    print_header_screen(client, title="MASUK (LOGIN)")
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

    print_header_screen(client, title="DAFTAR AKUN BARU (REGISTER)")
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


def print_version_history(client: ServerClient):
    """Display changelog history of all released versions."""
    spin = Spinner("Mengambil riwayat versi dari server...")
    spin.start()
    try:
        ver_info = client.get_cli_version()
        spin.stop()
    except Exception:
        spin.stop()
        ver_info = {}

    versions = ver_info.get("versions") or [
        {
            "version": "v1.0.0",
            "release_date": "2026-10-25",
            "title": "Initial Release",
            "description": "Rilis perdana AutoBotix Windows CLI Native Chromium & Multi-Display Xvfb.",
        },
        {
            "version": "v1.0.1",
            "release_date": "2026-10-26",
            "title": "Review Cleaner & CDP Lock",
            "description": "Fitur Hapus Ulasan (Database Cleaner & Live Maps Chromium) + Proteksi CDP Session.",
        },
        {
            "version": "v1.0.2",
            "release_date": "2026-10-27",
            "title": "Queue Anti-Bot & Auto-Update",
            "description": "Sistem Antrean Ulasan Anti-Bot, jeda konstan, live queue inspector, dan auto-update versioning.",
        },
    ]

    print_header_screen(client, title="RIWAYAT VERSI & CHANGELOG")
    cols = get_terminal_width()
    div_w = min(cols - 2, 78)
    print(f" {C_BOLD}{'VERSI':<9} {'TANGGAL':<12} {'KETERANGAN & FITUR BARU'}{C_RESET}")
    print(" " + "─" * div_w)

    for v in versions:
        v_num = v.get("version", "")
        v_date = v.get("release_date", "")
        v_desc = v.get("description", "")
        v_badge = f"{C_BOLD}{C_GREEN}{v_num:<9}{C_RESET}" if v_num == CLI_VERSION else f"{C_CYAN}{v_num:<9}{C_RESET}"
        print(f" {v_badge} {C_DIM}{v_date:<12}{C_RESET} {C_WHITE}{v_desc}{C_RESET}")

    print()
    input(f" {C_DIM}Tekan Enter untuk kembali ke menu autentikasi...{C_RESET}")


def check_and_apply_update(client: ServerClient) -> bool:
    """Check server for new CLI version, auto-update, and reload if available.
    
    Returns True if current version is up-to-date or update was handled.
    If updated, automatically re-executes the python process and never returns.
    """
    if os.environ.get("BOT_NO_UPDATE") == "1":
        return True

    # Avoid recursive loops if just reloaded
    if os.environ.get("BOT_JUST_RELOADED") == "1":
        os.environ.pop("BOT_JUST_RELOADED", None)
        print(f"\n {C_BOLD}{C_GREEN}✓ Aplikasi berhasil dimuat ulang dengan versi terbaru ({CLI_VERSION})!{C_RESET}")
        time.sleep(0.9)
        return True

    print()
    spin = Spinner(f"Memeriksa pembaruan AutoBotix CLI (Versi lokal: {CLI_VERSION})...")
    spin.start()

    try:
        ver_info = client.get_cli_version()
        spin.stop()
    except Exception:
        spin.stop()
        return True

    if not ver_info or ver_info.get("status") != "ok":
        # Server unreachable or endpoint not available
        return True

    latest_ver = ver_info.get("latest_version") or CLI_VERSION
    latest_code = int(ver_info.get("latest_version_code") or 0)
    changelog = ver_info.get("changelog") or "Pembaruan sistem & perbaikan bug."

    # Parse version codes if not provided
    if latest_code == 0:
        try:
            latest_code = int(latest_ver.replace("v", "").replace(".", ""))
        except Exception:
            latest_code = CLI_VERSION_CODE

    # Check if update is needed
    if latest_code > CLI_VERSION_CODE or latest_ver != CLI_VERSION:
        print()
        box_lines = [
            f"{C_BOLD}{C_YELLOW}🚀 PEMBARUAN VERSI DITEMUKAN!{C_RESET}",
            f" Versi Terpasang : {C_RED}{CLI_VERSION}{C_RESET}",
            f" Versi Terbaru   : {C_BOLD}{C_GREEN}{latest_ver}{C_RESET}",
            f" Changelog       : {C_WHITE}{changelog}{C_RESET}",
            "─" * 64,
            f"{C_CYAN}Mengunduh & memasang pembaruan otomatis...{C_RESET}",
        ]
        print_box(box_lines, width=68)
        print()

        update_success = False

        # 1. Try git pull if running inside git clone repository
        script_dir = os.path.dirname(os.path.abspath(__file__))
        is_git_repo = os.path.isdir(os.path.join(script_dir, ".git"))

        if is_git_repo and shutil.which("git"):
            g_spin = Spinner("Memperbarui source code via Git (git pull origin main)...")
            g_spin.start()
            try:
                sub_res = subprocess.run(
                    ["git", "pull", "origin", "main"],
                    cwd=script_dir,
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                if sub_res.returncode == 0:
                    g_spin.stop(f" {C_BOLD}{C_GREEN}✓ Berhasil memperbarui source code dari Git!{C_RESET}")
                    update_success = True
                else:
                    g_spin.stop(f" {C_YELLOW}▲ Git pull gagal, mencoba download langsung dari server...{C_RESET}")
            except Exception:
                g_spin.stop()

        # 2. If not git or git pull failed, download latest bot_cli.py from server
        if not update_success:
            d_spin = Spinner("Mengunduh bot_cli.py terbaru langsung dari server AutoBotix...")
            d_spin.start()
            new_code = client.download_cli_update()
            if new_code and len(new_code) > 1000 and "AutoBotix" in new_code:
                cur_file = os.path.abspath(__file__)
                tmp_file = cur_file + ".new"
                try:
                    with open(tmp_file, "w", encoding="utf-8") as f:
                        f.write(new_code)
                    if sys.platform == "win32":
                        bak_file = cur_file + ".bak"
                        if os.path.exists(bak_file):
                            try:
                                os.remove(bak_file)
                            except Exception:
                                pass
                        try:
                            os.replace(tmp_file, cur_file)
                        except Exception:
                            os.rename(cur_file, bak_file)
                            os.rename(tmp_file, cur_file)
                    else:
                        os.replace(tmp_file, cur_file)
                    d_spin.stop(f" {C_BOLD}{C_GREEN}✓ File bot_cli.py berhasil diperbarui ke {latest_ver}!{C_RESET}")
                    update_success = True
                except Exception as w_err:
                    d_spin.stop(f" {C_RED}✖ Gagal menulis pembaruan: {w_err}{C_RESET}")
                    if os.path.exists(tmp_file):
                        try:
                            os.remove(tmp_file)
                        except Exception:
                            pass
            else:
                d_spin.stop(f" {C_RED}✖ Gagal mengunduh file pembaruan dari server.{C_RESET}")

        if update_success:
            print(f"\n {C_BOLD}{C_GREEN}Memuat ulang aplikasi secara otomatis (Auto-Reload)...{C_RESET}")
            time.sleep(1.2)
            os.environ["BOT_JUST_RELOADED"] = "1"
            # Auto reload current Python process
            os.execv(sys.executable, [sys.executable] + sys.argv)
            sys.exit(0)
        else:
            print(f" {C_YELLOW}Melanjutkan program dengan versi lokal saat ini ({CLI_VERSION})...{C_RESET}")
            time.sleep(1.2)
            return True
    else:
        # Up-to-date
        spin.stop(f" {C_BOLD}{C_GREEN}✓ AutoBotix CLI {CLI_VERSION} (Versi Terkini • Sistem Siap Digunakan){C_RESET}")
        time.sleep(0.6)
        return True


def prompt_auth(client: ServerClient, default_user: str = "admin") -> bool:
    """Display Authentication Menu (Login / Register / Exit) before task menu."""
    while True:
        print_header_screen(client, title="AUTENTIKASI PENGGUNA")
        print(f" {C_DIM}Host Server Target : {C_GREEN}{client.base_url}{C_RESET}")
        print(f" {C_DIM}Versi Aplikasi     : {C_CYAN}{CLI_VERSION}{C_RESET} {C_GREEN}(Auto-Update Aktif ●){C_RESET}")
        print()
        print(f" {C_BOLD}{C_CYAN}[1]{C_RESET} {C_WHITE}Masuk (Login){C_RESET}")
        print(f" {C_BOLD}{C_CYAN}[2]{C_RESET} {C_WHITE}Daftar Akun Baru (Register){C_RESET}")
        print(f" {C_BOLD}{C_CYAN}[3]{C_RESET} {C_WHITE}Riwayat Versi (Changelog v1.0.0 - {CLI_VERSION}){C_RESET}")
        print(f" {C_BOLD}{C_YELLOW}[0]{C_RESET} {C_DIM}Keluar (Exit){C_RESET}")
        print()

        try:
            choice = input(f" {C_GREEN}Pilih menu autentikasi [1-3] (default 1): {C_RESET}").strip()
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
        elif choice == "3":
            print_version_history(client)
        elif choice == "0":
            print(f"\n {C_YELLOW}Terima kasih. Program selesai.{C_RESET}")
            sys.exit(0)
        else:
            print(f" {C_RED}Pilihan tidak valid. Masukkan 1, 2, 3, atau 0.{C_RESET}")
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

    cols = get_terminal_width()
    if cols < 70:
        for a in accounts:
            aid = a.get("id")
            name = (a.get("account_name") or "-").strip()
            email = a.get("email", "")
            c_status = a.get("cookie_status") or "no_cookie"
            if c_status == "active":
                st_badge = f"{C_GREEN}● AKTIF{C_RESET}"
            elif c_status == "needs_login":
                st_badge = f"{C_YELLOW}▲ PERLU LOGIN{C_RESET}"
            elif c_status == "expired":
                st_badge = f"{C_RED}✖ KEDALUWARSA{C_RESET}"
            else:
                st_badge = f"{C_DIM}- TIDAK ADA -{C_RESET}"
            line1 = f" {C_YELLOW}[#{aid}]{C_RESET} {C_WHITE}{C_BOLD}{name}{C_RESET} ──> {st_badge}"
            line2 = f"       {C_CYAN}{email}{C_RESET}"
            print(truncate_ansi(line1, cols - 1))
            print(truncate_ansi(line2, cols - 1))
        print()
        return

    print(f" {C_BOLD}{'ID':<5} {'NAMA AKUN':<22} {'EMAIL AKUN':<32} {'STATUS SESI':<16}{C_RESET}")
    print(" " + "─" * min(78, cols - 2))
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
        row = f" {C_YELLOW}{aid:<5}{C_RESET} {C_WHITE}{name:<22}{C_RESET} {C_CYAN}{email:<32}{C_RESET} {st_pad}"
        print(truncate_ansi(row, cols - 1))
    print()


def print_cookies_table(cookies: List[Dict[str, Any]]):
    print()
    box_header(f"{C_BOLD}{C_CYAN}STATUS SESI & DAFTAR COOKIE GOOGLE{C_RESET}")
    if not cookies:
        print(f"  {C_YELLOW}Belum ada cookie Google terdaftar di database.{C_RESET}")
        return

    cols = get_terminal_width()
    if cols < 70:
        for c in cookies:
            cid = c.get("id")
            name = (c.get("account_name") or "-").strip()
            email = c.get("email", "")
            c_status = (c.get("status") or "unknown").lower()
            if c_status == "active":
                st_badge = f"{C_GREEN}● AKTIF{C_RESET}"
            elif c_status in ("expired", "revoked", "invalid"):
                st_badge = f"{C_RED}✖ KEDALUWARSA{C_RESET}"
            elif c_status == "needs_login":
                st_badge = f"{C_YELLOW}▲ PERLU LOGIN{C_RESET}"
            else:
                st_badge = f"{C_DIM}- TIDAK AKTIF -{C_RESET}"
            line1 = f" {C_YELLOW}[#{cid}]{C_RESET} {C_WHITE}{C_BOLD}{name}{C_RESET} ──> {st_badge}"
            line2 = f"       {C_CYAN}{email}{C_RESET}"
            print(truncate_ansi(line1, cols - 1))
            print(truncate_ansi(line2, cols - 1))
        print()
        return

    print(f" {C_BOLD}{'ID':<5} {'NAMA AKUN GOOGLE':<24} {'EMAIL AKUN':<32} {'STATUS SESI':<16}{C_RESET}")
    print(" " + "─" * min(78, cols - 2))
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
        row = f" {C_YELLOW}{cid:<5}{C_RESET} {C_WHITE}{name:<24}{C_RESET} {C_CYAN}{email:<32}{C_RESET} {st_pad}"
        print(truncate_ansi(row, cols - 1))
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
        print_header_screen(client, title="STATUS & KELOLA COOKIE GOOGLE")
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
        print(f"  {C_YELLOW}[4]{C_RESET} {C_WHITE}🔄 Uji Validitas Sesi Seluruh Akun (Live Batch Test & Auto-Refresh){C_RESET}")
        print(f"  {C_YELLOW}[0]{C_RESET} {C_DIM}↩️  Kembali ke Menu Utama{C_RESET}")
        print()

        try:
            c_opt = input(f" {C_GREEN}Pilih aksi cookie [0-4] (default 0): {C_RESET}").strip() or "0"
        except (KeyboardInterrupt, EOFError):
            break

        if c_opt == "0":
            break

        elif c_opt == "1":
            print_header_screen(client, title="TAMBAH COOKIE SESI BARU")
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
            print_header_screen(client, title="HAPUS COOKIE SESI")
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
            print_header_screen(client, title="PERIKSA STATUS & NAMA PROFIL")
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
            print_header_screen(client, title="UJI VALIDITAS SESI GOOGLE (LIVE TEST)")
            cols = get_terminal_width()
            print(f" {C_BOLD}{C_CYAN}┌── PILIH MODE PENGUJIAN SESI GOOGLE{C_RESET}")
            print(f" {C_BOLD}{C_CYAN}│{C_RESET}   {C_YELLOW}[1]{C_RESET} {C_WHITE}Uji SEMUA Akun Sekaligus (Batch Live Validation) {C_GREEN}[Rekomendasi / Default]{C_RESET}")
            print(f" {C_BOLD}{C_CYAN}│{C_RESET}   {C_YELLOW}[2]{C_RESET} {C_WHITE}Uji Cookie Tunggal (Berdasarkan ID Akun){C_RESET}")
            print(f" {C_BOLD}{C_CYAN}│{C_RESET}   {C_YELLOW}[0]{C_RESET} {C_DIM}Batal / Kembali ke Menu Cookie{C_RESET}")
            print(f" {C_BOLD}{C_CYAN}└───────────────────────────────────────────────────────────────────{C_RESET}")
            print()
            try:
                t_mode = input(f" {C_GREEN}Pilih mode pengujian [1/2/0] (default 1): {C_RESET}").strip() or "1"
            except (KeyboardInterrupt, EOFError):
                continue

            if t_mode == "0":
                continue

            if t_mode == "1":
                spin = Spinner("Menguji validitas live seluruh akun ke Google & memperbarui token sesi...")
                spin.start()
                try:
                    res = client.test_all_cookies()
                    results = res.get("results", [])
                    tot = res.get("total", len(results))
                    act = res.get("active_count", 0)
                    exp = res.get("expired_count", 0)
                    spin.stop(f" {C_BOLD}{C_GREEN}✓ Uji validitas batch selesai! ({act}/{tot} Akun Aktif){C_RESET}")

                    print()
                    print_header_screen(client, title="HASIL VALIDASI SELURUH SESI AKUN GOOGLE")
                    print(f" {C_BOLD}{C_CYAN}┌── RINGKASAN VALIDASI SESI SELURUH AKUN{C_RESET}")
                    print(f" {C_BOLD}{C_CYAN}│{C_RESET}   {C_WHITE}Total Akun Teruji  : {C_YELLOW}{tot}{C_RESET}")
                    print(f" {C_BOLD}{C_CYAN}│{C_RESET}   {C_WHITE}Sesi Google Aktif  : {C_GREEN}● {act} Akun (Siap Memberi Ulasan){C_RESET}")
                    print(f" {C_BOLD}{C_CYAN}│{C_RESET}   {C_WHITE}Perlu Login / Mati : {C_RED if exp > 0 else C_DIM}▲ {exp} Akun{C_RESET}")
                    print(f" {C_BOLD}{C_CYAN}│{C_RESET}")
                    print(f" {C_BOLD}{C_CYAN}├── DAFTAR RINCIAN STATUS AKUN GOOGLE{C_RESET}")
                    for r in results:
                        rid = r.get("id")
                        rem = r.get("email", "")
                        rname = r.get("account_name") or "-"
                        rst = r.get("status", "unknown")
                        if rst == "active":
                            badge = f"{C_GREEN}● AKTIF{C_RESET}"
                        elif rst == "needs_login":
                            badge = f"{C_YELLOW}▲ PERLU LOGIN{C_RESET}"
                        else:
                            badge = f"{C_RED}✖ KEDALUWARSA{C_RESET}"

                        r_line = f" {C_BOLD}{C_CYAN}│{C_RESET}   [#{rid}] {C_WHITE}{rem:<28}{C_RESET} ──> {badge} {C_DIM}({rname}){C_RESET}"
                        print(truncate_ansi(r_line, cols - 1))

                    print(f" {C_BOLD}{C_CYAN}│{C_RESET}")
                    print(f" {C_BOLD}{C_CYAN}└── 🛡️ ANTI-EXPIRY: Auto-Extend 2 Tahun & Auto-Sync Token Aktif telah tersimpan.{C_RESET}")
                    print()
                    try:
                        status_info = client.get_status()
                        cookies = status_info.get("cookies", [])
                    except Exception:
                        pass
                    input(f" {C_DIM}Tekan Enter untuk kembali ke menu cookie...{C_RESET}")
                except Exception as e:
                    spin.stop()
                    print(f" {C_BOLD}{C_RED}✖ Gagal menjalankan uji validitas massal: {e}{C_RESET}")
                    time.sleep(2)

            elif t_mode == "2":
                test_in = input(f" {C_GREEN}Masukkan ID Cookie yang ingin diuji: {C_RESET}").strip()
                if not test_in.isdigit():
                    print(f" {C_RED}✖ ID harus berupa angka.{C_RESET}")
                    time.sleep(1)
                    continue

                cid = int(test_in)
                spin = Spinner(f"Menguji validitas live Google untuk Cookie ID {cid}...")
                spin.start()
                try:
                    res = client.test_cookie(cid)
                    st_val = res.get("session_status", "unknown")
                    is_valid = res.get("is_valid", False)
                    email_target = res.get("email", str(cid))
                    acc_name = res.get("account_name", "")
                    name_disp = f" ({acc_name})" if acc_name else ""
                    if is_valid and st_val == "active":
                        spin.stop(f" {C_BOLD}{C_GREEN}✓ Akun '{email_target}'{name_disp}: Status = AKTIF (Live Google OK){C_RESET}")
                    else:
                        spin.stop(f" {C_BOLD}{C_YELLOW}▲ Akun '{email_target}'{name_disp}: Status = {st_val.upper()} ({res.get('reason', 'Perlu login ulang')}){C_RESET}")
                    print(f"   {C_DIM}🛡️ Anti-Expiry Engine: Expiry token diperpanjang 2 tahun & disinkronkan.{C_RESET}")
                    time.sleep(2)
                    try:
                        status_info = client.get_status()
                        cookies = status_info.get("cookies", [])
                    except Exception:
                        pass
                except Exception as e:
                    spin.stop()
                    print(f" {C_BOLD}{C_RED}✖ Gagal menguji cookie: {e}{C_RESET}")
                    time.sleep(2)


# ── Queue & Antrean Handler ───────────────────────────────────────────────────

def print_queue_table(queue_items: List[Dict[str, Any]], title: str = "DAFTAR ANTREAN REVIEW (LIVE QUEUE)"):
    print()
    box_header(f"{C_BOLD}{C_CYAN}{title}{C_RESET}")
    if not queue_items:
        print(f"  {C_GREEN}✓ Antrean kosong! Tidak ada tugas review yang sedang menunggu atau berjalan.{C_RESET}\n")
        return

    print(f" {C_BOLD}{'NO':<4} {'STATUS / URUTAN':<22} {'TARGET BISNIS':<22} {'AKUN EMAIL':<26} {'RATING':<8}{C_RESET}")
    print(" " + "─" * 84)

    pending_idx = 0
    for idx, item in enumerate(queue_items, 1):
        status = (item.get("status") or "pending").lower()
        stars = "★" * int(item.get("star_rating") or 5)
        biz = (item.get("business_name") or f"Bisnis #{item.get('business_id')}")[:20]
        email = (item.get("email") or "-")[:24]

        if status == "reviewing":
            st_str = f"{C_BLUE}⚡ Sedang Diproses{C_RESET}"
        elif status == "pending":
            pending_idx += 1
            st_str = f"{C_YELLOW}⏳ Antrean #{pending_idx}{C_RESET}"
        elif status in ("reviewed", "posted"):
            st_str = f"{C_GREEN}✓ Sukses Terbit{C_RESET}"
        elif status in ("failed", "error"):
            st_str = f"{C_RED}✖ Gagal{C_RESET}"
        else:
            st_str = f"{C_DIM}{status.upper()}{C_RESET}"

        st_pad = pad_to_display_width(st_str, 22)
        print(f" {C_DIM}#{idx:<3}{C_RESET} {st_pad} {C_WHITE}{biz:<22}{C_RESET} {C_CYAN}{email:<26}{C_RESET} {C_YELLOW}{stars:<8}{C_RESET}")

    pending_count = sum(1 for r in queue_items if r.get("status") == "pending")
    active_count = sum(1 for r in queue_items if r.get("status") == "reviewing")
    done_count = sum(1 for r in queue_items if r.get("status") in ("reviewed", "posted"))
    print(" " + "─" * 84)
    print(f" {C_DIM}Ringkasan:{C_RESET} {C_YELLOW}Menunggu Antrean: {pending_count}{C_RESET} │ {C_BLUE}Sedang Berjalan: {active_count}{C_RESET} │ {C_GREEN}Selesai: {done_count}{C_RESET} │ {C_WHITE}Total: {len(queue_items)}{C_RESET}\n")


def handle_queue_menu(client: ServerClient, status_info: Dict[str, Any]):
    """Interactive queue management and inspection."""
    while True:
        print_header_screen(client, title="DAFTAR ANTREAN ULASAN", status_info=status_info)
        spin = Spinner("Memuat daftar antrean ulasan...")
        spin.start()
        try:
            res = client.get_queue()
            spin.stop()
            q_list = res.get("queue", [])
        except Exception as exc:
            spin.stop()
            print(f" {C_RED}✖ Gagal memuat antrean: {exc}{C_RESET}")
            input(f"\n {C_DIM}Tekan Enter untuk kembali...{C_RESET}")
            return

        print_queue_table(q_list)

        print(f" {C_BOLD}{C_CYAN}─── AKSI DAFTAR ANTREAN ───────────────────────────────────────────────{C_RESET}")
        print(f"  {C_YELLOW}[1]{C_RESET} {C_WHITE}🔄 Segarkan Antrean (Refresh){C_RESET}")
        print(f"  {C_YELLOW}[2]{C_RESET} {C_WHITE}🏢 Filter Antrean Berdasarkan Target Bisnis{C_RESET}")
        print(f"  {C_YELLOW}[3]{C_RESET} {C_WHITE}🧹 Bersihkan Semua Antrean Pending (Reset){C_RESET}")
        print(f"  {C_YELLOW}[0]{C_RESET} {C_DIM}↩️  Kembali ke Menu Utama{C_RESET}")
        print()

        try:
            q_opt = input(f" {C_GREEN}Pilih aksi antrean [0-3] (default 1): {C_RESET}").strip() or "1"
        except (KeyboardInterrupt, EOFError):
            break

        if q_opt == "0":
            break
        elif q_opt == "1":
            os.system("cls" if os.name == "nt" else "clear")
            print_banner(client, status_info)
            continue
        elif q_opt == "2":
            print_header_screen(client, title="FILTER ANTREAN BISNIS")
            businesses = status_info.get("businesses", [])
            print_businesses(businesses)
            bid_in = input(f" {C_GREEN}Masukkan ID Bisnis target: {C_RESET}").strip()
            if bid_in.isdigit():
                bid = int(bid_in)
                spin = Spinner(f"Memuat antrean untuk Bisnis #{bid}...")
                spin.start()
                try:
                    res_biz = client.get_queue(bid)
                    spin.stop()
                    print_queue_table(res_biz.get("queue", []), title=f"ANTREAN ULASAN - BISNIS #{bid}")
                except Exception as exc:
                    spin.stop()
                    print(f" {C_RED}✖ Gagal: {exc}{C_RESET}")
            input(f" {C_DIM}Tekan Enter untuk melanjutkan...{C_RESET}")
        elif q_opt == "3":
            print_header_screen(client, title="RESET ANTREAN BISNIS")
            businesses = status_info.get("businesses", [])
            print_businesses(businesses)
            bid_in = input(f" {C_GREEN}Masukkan ID Bisnis yang antreannya ingin direset: {C_RESET}").strip()
            if bid_in.isdigit():
                confirm = input(f" {C_RED}Yakin ingin mereset antrean bisnis #{bid_in}? [y/N]: {C_RESET}").strip().lower()
                if confirm in ("y", "yes"):
                    spin = Spinner("Mereset antrean ulasan...")
                    spin.start()
                    try:
                        res_rst = client.clear_logs(int(bid_in))
                        spin.stop(f" {C_GREEN}✓ {res_rst.get('message', 'Antrean berhasil direset.')}{C_RESET}")
                    except Exception as exc:
                        spin.stop()
                        print(f" {C_RED}✖ Gagal: {exc}{C_RESET}")
            input(f" {C_DIM}Tekan Enter untuk melanjutkan...{C_RESET}")


# ── Remove Review Handler ─────────────────────────────────────────────────────

def handle_remove_review_menu(client: ServerClient, status_info: Dict[str, Any]):
    """Interactive handler for removing reviews (database deletion or live Google Maps deletion)."""
    print_header_screen(client, title="HAPUS ULASAN GOOGLE MAPS", status_info=status_info)

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

    print_header_screen(client, title=f"HAPUS ULASAN - {biz_name[:25]}", status_info=status_info)

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
        print(f"\n {C_BOLD}{C_CYAN}PILIH CAKUPAN PENGHAPUSAN DI GOOGLE MAPS:{C_RESET}")
        print(f" {C_YELLOW}[1]{C_RESET} {C_WHITE}🌐  SEMUA AKUN MASTER / TERDAFTAR{C_RESET}    {C_DIM}Setiap akun bot login & bersihkan ulasan sendiri di Maps{C_RESET}")
        print(f" {C_YELLOW}[2]{C_RESET} {C_WHITE}📑  HANYA AKUN 'REVIEWED' DI DB{C_RESET}      {C_DIM}Hanya akun yang tercatat status ulasannya sukses terbit{C_RESET}")
        print(f" {C_YELLOW}[3]{C_RESET} {C_WHITE}👤  AKUN TERTENTU (PER EMAIL ID){C_RESET}    {C_DIM}Pilih ID akun email tertentu{C_RESET}")
        print(f" {C_YELLOW}[0]{C_RESET} {C_DIM}↩   Batal{C_RESET}")

        try:
            scope_c = input(f"\n {C_GREEN}Pilih cakupan [0-3]: {C_RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            return

        if scope_c == "1":
            confirm = input(f"\n {C_BOLD}{C_RED}Luncurkan bot Chromium untuk SCAN & HAPUS ulasan dari SEMUA akun bot terdaftar di Maps? [y/N]: {C_RESET}").strip().lower()
            if confirm in ("y", "yes"):
                all_accs = status_info.get("accounts", [])
                if not all_accs:
                    try:
                        all_accs = client.get_status().get("accounts", [])
                    except Exception:
                        pass
                run_delete_maps_stream(
                    client,
                    bid,
                    business_name=biz_name,
                    scope_label=f"Semua Akun Master ({len(all_accs)} Akun Terdaftar)",
                    all_accounts=True,
                    target_accounts=all_accs,
                )
        elif scope_c == "2":
            if reviewed_count == 0:
                print(f"\n {C_YELLOW}Tidak ada record ulasan berstatus 'reviewed' di database untuk bisnis ini.{C_RESET}")
            else:
                confirm = input(f"\n {C_BOLD}{C_RED}Luncurkan bot Chromium untuk HAPUS {reviewed_count} ulasan terbit di Maps? [y/N]: {C_RESET}").strip().lower()
                if confirm in ("y", "yes"):
                    rev_accs = [r for r in reviews if r.get("status") in ("reviewed", "posted")]
                    run_delete_maps_stream(
                        client,
                        bid,
                        business_name=biz_name,
                        scope_label=f"Hanya Akun Review Terbit ({len(rev_accs)} Akun)",
                        all_accounts=False,
                        target_accounts=rev_accs,
                    )
        elif scope_c == "3":
            all_emails = status_info.get("emails", [])
            if not all_emails:
                try:
                    all_emails = client.get_status().get("emails", [])
                except Exception:
                    pass
            if all_emails:
                print(f"\n {C_BOLD}{C_CYAN}DAFTAR AKUN BOT TERSEDIA:{C_RESET}")
                for em in all_emails[:20]:
                    print(f" {C_BOLD}#{em.get('id')}{C_RESET}: {C_WHITE}{em.get('email')}{C_RESET}")
            eid_in = input(f"\n {C_GREEN}Masukkan ID Akun Email yang ingin dihapus ulasannya di Maps: {C_RESET}").strip()
            if eid_in.isdigit():
                sel_acc = next((e for e in all_emails if e.get("id") == int(eid_in)), {"id": int(eid_in), "email": f"ID #{eid_in}"})
                run_delete_maps_stream(
                    client,
                    bid,
                    business_name=biz_name,
                    scope_label=f"Akun Tunggal ({sel_acc.get('email')})",
                    email_id=int(eid_in),
                    all_accounts=False,
                    target_accounts=[sel_acc],
                )
        input(f"\n {C_DIM}Tekan Enter untuk kembali...{C_RESET}")


# ── Task Execution & Live Log Monitor ─────────────────────────────────────────

def format_task_log_line(ts: str, lvl: str, msg: str, email: str = "", account_name: str = "") -> str:
    """Format single log entry into a unified CLI tree branch with vertical trunk | and -> process indicator."""
    import html as _html_mod
    # Sanitize account_name: decode HTML entities (&amp;#10; &#10; etc), strip newlines/tabs
    if account_name:
        account_name = _html_mod.unescape(account_name)
        account_name = re.sub(r'[\n\r\t&#;0-9]+', ' ', account_name)
        account_name = re.sub(r'\s{2,}', ' ', account_name).strip()

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


def run_delete_maps_stream(
    client: ServerClient,
    business_id: int,
    business_name: str = "",
    scope_label: str = "Semua Akun Master",
    email_id: Optional[int] = None,
    all_accounts: bool = False,
    target_accounts: Optional[List[Dict[str, Any]]] = None,
) -> bool:
    """Stream live Chromium scan & delete logs with unified tree lines and real-time status."""
    print()
    print(f" {C_CYAN}┌── [1/2] PERSIAPAN SCAN & HAPUS ULASAN GOOGLE MAPS{C_RESET}")
    biz_label = business_name if business_name else f"Bisnis #{business_id}"
    print(f" {C_CYAN}│   ├──{C_RESET} {C_DIM}Target Bisnis{C_RESET}   ──────> {C_WHITE}{biz_label}{C_RESET}")
    print(f" {C_CYAN}│   ├──{C_RESET} {C_DIM}Cakupan Target{C_RESET}  ─────> {C_YELLOW}{scope_label}{C_RESET}")
    print(f" {C_CYAN}│   └──{C_RESET} {C_DIM}Metode Aksi{C_RESET}     ─────> {C_RED}Live Chromium CDP (Hapus Ulasan Publik Sendiri){C_RESET}")
    print(f" {C_CYAN}│{C_RESET}")

    if target_accounts:
        print(f" {C_CYAN}├── [DAFTAR AKUN TARGET SCAN & CLEAN]{C_RESET}")
        for s_idx, acc in enumerate(target_accounts):
            is_last = (s_idx == len(target_accounts) - 1)
            sub_branch = "└──" if is_last else "├──"
            aemail = acc.get("email", "")
            aname = (acc.get("account_name") or "").strip()
            lbl = f"{aname} ({aemail})" if aname and aname != aemail else aemail
            disp = f":{99 + (s_idx % 6)}"
            print(f" {C_CYAN}│   {sub_branch}{C_RESET} [Slot {s_idx + 1}] Display {disp} ──> {C_WHITE}{lbl}{C_RESET} ──> {C_GREEN}[SIAP SCAN]{C_RESET}")
            time.sleep(0.03)
        print(f" {C_CYAN}│{C_RESET}")

    print(f" {C_CYAN}├── [PENGIRIMAN PERINTAH KE SERVER]{C_RESET}")
    spin = Spinner("Mengirim instruksi hapus ulasan Maps ke server AutoBotix...")
    spin.start()
    try:
        res = client.delete_maps_reviews_live(business_id, email_id=email_id, all_accounts=all_accounts)
        t_count = res.get("target_count", len(target_accounts or []))
        spin.stop(f" {C_CYAN}│   └──{C_RESET} Dispatch API ───────> {C_BOLD}{C_GREEN}[BERHASIL DILUNCURKAN 🚀]{C_RESET} ({t_count} Akun dalam Antrean Scan)")
    except Exception as exc:
        spin.stop()
        print(f" {C_CYAN}│   └──{C_RESET} Dispatch API ───────> {C_BOLD}{C_RED}[GAGAL: {exc}]{C_RESET}")
        print(f" {C_CYAN}│{C_RESET}")
        print(f" {C_CYAN}└──{C_RESET} {C_RED}Proses pembersihan ulasan dibatalkan.{C_RESET}")
        return False

    print(f" {C_CYAN}│{C_RESET}")
    print(f" {C_CYAN}├── [2/2] LIVE PROCESS LOGS (SERVER CHROMIUM SCAN & CLEAN){C_RESET}")
    print(f" {C_CYAN}│   {C_DIM}Memantau alur pembersihan ulasan Maps secara live... (Tekan Ctrl+C untuk kembali){C_RESET}")
    print(f" {C_CYAN}│{C_RESET}")

    seen_ids = set()
    start_time = time.time()
    clean_finished = False
    sp_idx = 0
    last_poll_time = 0.0
    status = "running"
    idle_count = 0

    # Metrics counters for deletion
    del_berhasil = 0
    del_notfound = 0
    del_gagal = 0

    try:
        while True:
            now = time.time()
            elapsed_sec = int(now - start_time)
            mins = elapsed_sec // 60
            secs = elapsed_sec % 60
            time_str = f"{mins:02d}:{secs:02d}s"

            if now - last_poll_time >= 0.8:
                last_poll_time = now
                try:
                    log_data = client.get_logs(business_id)
                    logs = log_data.get("logs", [])
                    status = log_data.get("status", "idle")
                    is_del = log_data.get("is_deleting", False)

                    new_logs = [l for l in logs if l["id"] not in seen_ids]
                    for l in new_logs:
                        seen_ids.add(l["id"])
                        lvl = (l.get("level") or "info").lower()
                        ts = l.get("created_at", "").split()[-1]
                        msg = l.get("message", "")
                        l_email = l.get("email", "")
                        l_aname = l.get("account_name", "")

                        msg_low = msg.lower()
                        if "ulasan akun berhasil dihapus" in msg_low or "berhasil dihapus dari google maps" in msg_low:
                            del_berhasil += 1
                        elif "tidak ditemukan ulasan" in msg_low:
                            del_notfound += 1
                        elif "gagal menghapus" in msg_low or "gagal mengakses profil" in msg_low:
                            del_gagal += 1

                        sys.stdout.write("\r\033[K")
                        line_out = format_task_log_line(ts, lvl, msg, email=l_email, account_name=l_aname)
                        print(line_out)

                        if "Pembersihan ulasan Google Maps selesai" in msg or "selesai untuk seluruh" in msg:
                            clean_finished = True

                    if not is_del and clean_finished:
                        idle_count += 1
                        if idle_count >= 2:
                            time.sleep(1.0)
                            try:
                                final_data = client.get_logs(business_id)
                                for l in final_data.get("logs", []):
                                    if l["id"] not in seen_ids:
                                        seen_ids.add(l["id"])
                                        lvl = (l.get("level") or "info").lower()
                                        ts = l.get("created_at", "").split()[-1]
                                        sys.stdout.write("\r\033[K")
                                        print(format_task_log_line(ts, lvl, l.get("message", ""), email=l.get("email", ""), account_name=l.get("account_name", "")))
                            except Exception:
                                pass
                            break
                    elif not is_del and not new_logs and elapsed_sec > 8:
                        idle_count += 1
                        if idle_count >= 4:
                            break
                    else:
                        idle_count = 0
                except Exception:
                    pass

            sp_idx += 1
            sp_char = SPINNER_FRAMES[sp_idx % len(SPINNER_FRAMES)]
            cols = get_terminal_width()
            if cols >= 85:
                st_badge = f"{C_RED}MEMBERSIHKAN ULASAN MAPS{C_RESET}" if status == "deleting" or not clean_finished else f"{C_GREEN}SELESAI{C_RESET}"
                metrics_del = f"│ {C_GREEN}Dihapus: {del_berhasil}{C_RESET} │ {C_YELLOW}Tidak Ada: {del_notfound}{C_RESET} │ {C_RED}Gagal: {del_gagal}{C_RESET}"
                line_del = f"\r {C_CYAN}│   {sp_char}{C_RESET} {C_WHITE}Status: {st_badge} │ {C_DIM}Waktu:{C_RESET} {C_GREEN}{time_str}{C_RESET} {metrics_del} │ {C_DIM}Ctrl+C{C_RESET}\033[K"
            else:
                st_badge = f"{C_RED}HAPUS{C_RESET}" if status == "deleting" or not clean_finished else f"{C_GREEN}OK{C_RESET}"
                line_del = f"\r {C_CYAN}│ {sp_char}{C_RESET} {st_badge} {C_GREEN}{time_str}{C_RESET} │ {C_GREEN}H:{del_berhasil}{C_RESET} {C_YELLOW}N:{del_notfound}{C_RESET} {C_RED}G:{del_gagal}{C_RESET}\033[K"
            sys.stdout.write(truncate_ansi(line_del, cols - 1))
            sys.stdout.flush()
            time.sleep(0.09)

    except KeyboardInterrupt:
        sys.stdout.write("\r\033[K")
        print(f" {C_CYAN}│{C_RESET}")
        print(f" {C_CYAN}└──{C_RESET} {C_YELLOW}! Pemantauan live dihentikan oleh user. Pembersihan ulasan tetap berjalan di server.{C_RESET}")
        return True

    sys.stdout.write("\r\033[K")
    elapsed = int(time.time() - start_time)
    print(f" {C_CYAN}│{C_RESET}")
    print(f" {C_CYAN}├── [RINGKASAN PEMBERSIHAN ULASAN GOOGLE MAPS]{C_RESET}")
    print(f" {C_CYAN}│   ├──{C_RESET} {C_DIM}Total Berhasil Dihapus{C_RESET} ────> {C_BOLD}{C_GREEN}{del_berhasil} Ulasan{C_RESET}")
    print(f" {C_CYAN}│   ├──{C_RESET} {C_DIM}Total Akun Bersih{C_RESET}      ────> {C_BOLD}{C_YELLOW}{del_notfound} Akun{C_RESET} (Tidak Ditemukan Ulasan)")
    print(f" {C_CYAN}│   └──{C_RESET} {C_DIM}Total Gagal/Error{C_RESET}      ────> {C_BOLD}{C_RED if del_gagal > 0 else C_WHITE}{del_gagal} Akun{C_RESET}")
    print(f" {C_CYAN}│{C_RESET}")
    print(f" {C_CYAN}└──{C_RESET} {C_BOLD}{C_GREEN}✓ Seluruh proses scan & hapus ulasan di Google Maps selesai dalam {elapsed} detik!{C_RESET}")
    return True


def run_task_stream(
    client: ServerClient,
    business_id: int,
    count: int = 1,
    star_rating: int = 5,
    mode: str = "queue",
    delay: int = 60,
    business_name: str = "",
    active_accounts: Optional[List[Dict[str, Any]]] = None,
):
    print()
    print(f" {C_CYAN}┌── [2/3] MEMPERSIAPKAN DAFTAR ANTREAN TUGAS ULASAN BOT{C_RESET}")
    biz_label = business_name if business_name else f"Bisnis #{business_id}"
    print(f" {C_CYAN}│   ├──{C_RESET} {C_DIM}Target Bisnis{C_RESET}   ──────> {C_WHITE}{biz_label}{C_RESET}")

    if mode == "queue":
        print(f" {C_CYAN}│   ├──{C_RESET} {C_DIM}Metode Eksekusi{C_RESET} ────> {C_GREEN}📋 Mode Daftar Antrean (1 Akun Bergiliran - Anti-Bot Safe){C_RESET}")
        print(f" {C_CYAN}│   ├──{C_RESET} {C_DIM}Jumlah Antrean{C_RESET}  ─────> {C_CYAN}{count} Akun Terjadwal Berurutan{C_RESET}")
        print(f" {C_CYAN}│   ├──{C_RESET} {C_DIM}Jeda Antar Akun{C_RESET} ─────> {C_YELLOW}{delay} detik tetap di setiap antrean{C_RESET}")
    else:
        print(f" {C_CYAN}│   ├──{C_RESET} {C_DIM}Metode Eksekusi{C_RESET} ────> {C_YELLOW}⚡ Mode Paralel ({count} Layar Chromium Serentak){C_RESET}")
        print(f" {C_CYAN}│   ├──{C_RESET} {C_DIM}Jumlah Browser{C_RESET}  ─────> {C_CYAN}{count} Layar Chromium Paralel{C_RESET}")

    star_str = "⭐" * star_rating
    print(f" {C_CYAN}│   └──{C_RESET} {C_DIM}Rating Target{C_RESET}   ─────> {C_YELLOW}{star_str}{C_RESET} {C_DIM}({star_rating} Bintang){C_RESET}")
    print(f" {C_CYAN}│{C_RESET}")

    assigned = (active_accounts or [])[:count]
    if mode == "queue":
        print(f" {C_CYAN}├── [URUTAN JADWAL DAFTAR ANTREAN AKUN]{C_RESET}")
        for s_idx in range(count):
            is_last = (s_idx == count - 1)
            sub_branch = "└──" if is_last else "├──"
            if s_idx < len(assigned):
                acc = assigned[s_idx]
                aname = (acc.get("account_name") or "").strip()
                aemail = acc.get("email", "")
                lbl = f"{aname} ({aemail})" if aname and aname != aemail else aemail
            else:
                lbl = f"Akun Antrean #{s_idx + 1}"

            if s_idx == 0:
                est = f"{C_GREEN}[Giliran Pertama • Segera Jalan 🚀]{C_RESET}"
            else:
                est = f"{C_YELLOW}[Antrean #{s_idx + 1} • Jeda Tetap {delay}s ⏳]{C_RESET}"

            print(f" {C_CYAN}│   {sub_branch}{C_RESET} [Urutan #{s_idx + 1}] {C_WHITE}{lbl}{C_RESET} ──> {est}")
            time.sleep(0.04)
    else:
        print(f" {C_CYAN}├── [PENUGASAN SLOT BROWSER & DISPLAY]{C_RESET}")
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

    spin = Spinner("Mengirim instruksi antrean task ke server AutoBotix...")
    spin.start()
    try:
        res = client.start_task(business_id, count=count, star_rating=star_rating, mode=mode, delay=delay)
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

    # Metrics counters (Total Berhasil, Total Skip, Total Gagal, Total Error)
    total_berhasil = 0
    total_skip = 0
    total_gagal = 0
    total_error = 0

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

                        # Tally metrics
                        msg_low = msg.lower()
                        if "ulasan bintang" in msg_low and "berhasil dikirim" in msg_low:
                            total_berhasil += 1
                        elif "skip: komentar/ulasan dari akun ini sudah ada" in msg_low:
                            total_skip += 1
                        elif "proses gagal" in msg_low or "gagal mengakses profil" in msg_low:
                            total_gagal += 1
                        elif lvl in ("error", "fatal"):
                            total_error += 1

                        # Clear spinner line and print log branch
                        sys.stdout.write("\r\033[K")
                        line_out = format_task_log_line(ts, lvl, msg, email=l_email, account_name=l_aname)
                        print(line_out)

                        if "Worker selesai memproses" in msg or "seluruh antrean ulasan selesai" in msg_low:
                            task_finished = True

                    if task_finished and status == "idle":
                        time.sleep(1.2)
                        try:
                            log_data = client.get_logs(business_id)
                            for l in log_data.get("logs", []):
                                if l["id"] not in seen_ids:
                                    seen_ids.add(l["id"])
                                    lvl = (l.get("level") or "info").lower()
                                    ts = l.get("created_at", "").split()[-1]
                                    msg = l.get("message", "")
                                    msg_low = msg.lower()
                                    if "ulasan bintang" in msg_low and "berhasil dikirim" in msg_low:
                                        total_berhasil += 1
                                    elif "skip: komentar/ulasan dari akun ini sudah ada" in msg_low:
                                        total_skip += 1
                                    elif "proses gagal" in msg_low or "gagal mengakses profil" in msg_low:
                                        total_gagal += 1
                                    elif lvl in ("error", "fatal"):
                                        total_error += 1
                                    sys.stdout.write("\r\033[K")
                                    print(format_task_log_line(ts, lvl, msg, email=l.get("email", ""), account_name=l.get("account_name", "")))
                        except Exception:
                            pass
                        break
                except Exception:
                    pass

            # Animate spinner on current bottom line (connected to tree trunk) with live metrics
            sp_idx += 1
            sp_char = SPINNER_FRAMES[sp_idx % len(SPINNER_FRAMES)]
            cols = get_terminal_width()
            if status in ("running", "reviewing"):
                st_badge = f"{C_GREEN}PROSES{C_RESET}" if cols < 85 else f"{C_GREEN}SEDANG MEMPROSES{C_RESET}"
            elif status == "queued":
                st_badge = f"{C_YELLOW}ANTREAN{C_RESET}" if cols < 85 else f"{C_YELLOW}JEDA ANTREAN{C_RESET}"
            else:
                st_badge = f"{C_CYAN}{status.upper()[:8]}{C_RESET}"

            if cols >= 85:
                metrics_bar = f"│ {C_GREEN}Berhasil: {total_berhasil}{C_RESET} │ {C_YELLOW}Skip: {total_skip}{C_RESET} │ {C_RED}Gagal: {total_gagal}{C_RESET}"
                task_line = f"\r {C_CYAN}│   {sp_char}{C_RESET} {C_WHITE}Status: {st_badge} │ {C_DIM}Waktu:{C_RESET} {C_GREEN}{time_str}{C_RESET} {metrics_bar} │ {C_DIM}Ctrl+C{C_RESET}\033[K"
            else:
                task_line = f"\r {C_CYAN}│ {sp_char}{C_RESET} {st_badge} {C_GREEN}{time_str}{C_RESET} │ {C_GREEN}B:{total_berhasil}{C_RESET} {C_YELLOW}S:{total_skip}{C_RESET} {C_RED}G:{total_gagal}{C_RESET}\033[K"
            sys.stdout.write(truncate_ansi(task_line, cols - 1))
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
    print(f" {C_CYAN}├── [RINGKASAN HASIL EKSEKUSI TUGAS ULASAN]{C_RESET}")
    print(f" {C_CYAN}│   ├──{C_RESET} {C_DIM}Total Berhasil{C_RESET} ────> {C_BOLD}{C_GREEN}{total_berhasil} Akun{C_RESET} (Ulasan Sukses Terbit ⭐)")
    print(f" {C_CYAN}│   ├──{C_RESET} {C_DIM}Total Dilewati{C_RESET} ────> {C_BOLD}{C_YELLOW}{total_skip} Akun{C_RESET} (Komentar Sudah Ada di Maps ⏭️)")
    print(f" {C_CYAN}│   ├──{C_RESET} {C_DIM}Total Gagal{C_RESET}    ────> {C_BOLD}{C_RED if total_gagal > 0 else C_WHITE}{total_gagal} Akun{C_RESET}")
    print(f" {C_CYAN}│   └──{C_RESET} {C_DIM}Total Error{C_RESET}    ────> {C_BOLD}{C_RED if total_error > 0 else C_WHITE}{total_error} Kendala Teknis{C_RESET}")
    print(f" {C_CYAN}│{C_RESET}")
    print(f" {C_CYAN}└──{C_RESET} {C_BOLD}{C_GREEN}✓ Seluruh proses antrean ulasan selesai dalam {elapsed} detik!{C_RESET}")
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
            f" {C_YELLOW}[1]{C_RESET} {C_WHITE}🚀  JALANKAN TASK{C_RESET}        {C_DIM}Mulai ulasan otomatis (Antrean / Paralel){C_RESET}",
            f" {C_YELLOW}[2]{C_RESET} {C_WHITE}🏢  TARGET GOOGLE MAPS{C_RESET}   {C_DIM}Lihat daftar target & jumlah review{C_RESET}",
            f" {C_YELLOW}[3]{C_RESET} {C_WHITE}➕  TAMBAH BISNIS BARU{C_RESET}   {C_DIM}Daftarkan URL Google Maps baru{C_RESET}",
            cookie_menu_label,
            f" {C_YELLOW}[5]{C_RESET} {C_WHITE}📊  PANTAU LIVE LOGS{C_RESET}     {C_DIM}Lihat log proses aktivitas server{C_RESET}",
            f" {C_YELLOW}[6]{C_RESET} {C_WHITE}📋  DAFTAR ANTREAN{C_RESET}       {C_DIM}Lihat status antrean ulasan & urutan{C_RESET}",
            f" {C_YELLOW}[7]{C_RESET} {C_WHITE}🛑  EMERGENCY STOP{C_RESET}       {C_DIM}Hentikan semua worker & browser{C_RESET}",
            f" {C_YELLOW}[8]{C_RESET} {C_WHITE}🔄  RESET ANTREAN{C_RESET}        {C_DIM}Bersihkan antrean ulasan & log bisnis{C_RESET}",
            f" {C_YELLOW}[9]{C_RESET} {C_WHITE}🗑️   REMOVE ULASAN{C_RESET}        {C_DIM}Hapus ulasan database atau Google Maps{C_RESET}",
            f" {C_YELLOW}[0]{C_RESET} {C_RED}🚪  LOGOUT & KELUAR{C_RESET}      {C_DIM}Keluar dari sesi terminal{C_RESET}",
        ]
        print_box(menu_lines, width=68, title=f"{C_BOLD}{C_CYAN}DAFTAR MENU UTAMA{C_RESET}")

        try:
            choice = input(f" {C_GREEN}Pilih menu [0-9] (default 1): {C_RESET}").strip() or "1"
        except (KeyboardInterrupt, EOFError):
            print("\n Keluar.")
            break

        if choice == "0":
            client.api_key = ""
            print(f"\n {C_DIM}Anda telah logout. Terima kasih telah menggunakan AutoBotix CLI. Sampai jumpa!{C_RESET}")
            break

        elif choice == "1":
            print_header_screen(client, title="JALANKAN TASK ULASAN GOOGLE MAPS")
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

                max_slots = len(active_accs)
                slots_in = input(f" {C_GREEN}Jumlah Ulasan yang ingin dikirim (1-{max_slots}, default {max_slots}): {C_RESET}").strip() or str(max_slots)
                slots = max(1, min(max_slots, int(slots_in) if slots_in.isdigit() else 1))

                stars_in = input(f" {C_GREEN}Rating Bintang (1-5, default 5): {C_RESET}").strip() or "5"
                stars = max(1, min(5, int(stars_in) if stars_in.isdigit() else 5))

                print()
                print(f" {C_BOLD}{C_CYAN}Pilih Metode Eksekusi Ulasan:{C_RESET}")
                print(f"  {C_YELLOW}[1]{C_RESET} {C_BOLD}{C_GREEN}📋 Mode Daftar Antrean (1 Akun Bergiliran + Jeda Anti-Bot) [DIREKOMENDASIKAN]{C_RESET}")
                print(f"      {C_DIM}Akun memposting ulasan satu per satu dengan jeda alami untuk menghindari deteksi spam/bot Google.{C_RESET}")
                print(f"  {C_YELLOW}[2]{C_RESET} {C_WHITE}⚡ Mode Paralel ({slots} Layar Chromium Serentak){C_RESET}")
                print(f"      {C_DIM}Membuka {slots} browser sekaligus secara bersamaan di virtual display.{C_RESET}")

                m_in = input(f"\n {C_GREEN}Pilih mode eksekusi [1-2] (default 1): {C_RESET}").strip() or "1"
                if m_in == "2":
                    mode = "parallel"
                    delay_val = 15
                else:
                    mode = "queue"
                    d_in = input(f" {C_GREEN}Jeda alami antar ulasan (detik, default 60): {C_RESET}").strip() or "60"
                    delay_val = max(10, int(d_in) if d_in.isdigit() else 60)

                mode_title = f"Antrean {slots} Akun (Jeda {delay_val}s)" if mode == "queue" else f"Paralel {slots} Layar"
                confirm = input(f"\n {C_BOLD}Jalankan {slots} ulasan bintang {stars} [{mode_title}] untuk '{biz_name}' (ID {bid}) sekarang? [Y/n]: {C_RESET}").strip().lower()
                if confirm in ("", "y", "yes"):
                    run_task_stream(client, bid, count=slots, star_rating=stars, mode=mode, delay=delay_val, business_name=biz_name, active_accounts=active_accs)
            except Exception as exc:
                print(f" {C_RED}Error: {exc}{C_RESET}")

            input(f"\n {C_DIM}Tekan Enter untuk kembali ke menu...{C_RESET}")

        elif choice == "2":
            print_header_screen(client, title="DAFTAR TARGET GOOGLE MAPS")
            print_businesses(status_info.get("businesses", []))
            input(f" {C_DIM}Tekan Enter untuk kembali...{C_RESET}")

        elif choice == "3":
            print_header_screen(client, title="TAMBAH TARGET BISNIS BARU")
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
            print_header_screen(client, title="PANTAU LIVE PROCESS LOGS")
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
            handle_queue_menu(client, status_info)

        elif choice == "7":
            print_header_screen(client, title="EMERGENCY STOP WORKER")
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

        elif choice == "8":
            print_header_screen(client, title="BERSIHKAN LOG & ANTREAN")
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

        elif choice == "9":
            handle_remove_review_menu(client, status_info)


# ── CLI Arguments Entrypoint ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AutoBotix Review Automation Windows Client")
    parser.add_argument("--server", "-H", default=DEFAULT_SERVER, help=f"URL Server AutoBotix (default: {DEFAULT_SERVER})")
    parser.add_argument("--user", "-u", default=None, help="Username login server (default: admin)")
    parser.add_argument("--password", "-p", default=None, help="Password login server")
    parser.add_argument("--key", "-k", default=DEFAULT_API_KEY, help="API Key / Password Server (opsional)")
    parser.add_argument("--version", "-v", action="version", version=f"AutoBotix CLI {CLI_VERSION} (Build {CLI_VERSION_CODE})")
    parser.add_argument("--no-update", action="store_true", help="Lewati pemeriksaan update otomatis saat startup")

    subparsers = parser.add_subparsers(dest="command")

    # Command: run
    run_parser = subparsers.add_parser("run", help="Jalankan tugas ulasan langsung")
    run_parser.add_argument("--business", "-b", type=int, required=True, help="ID Bisnis target")
    run_parser.add_argument("--slots", "-s", type=int, default=1, help="Jumlah ulasan yang ingin dikirim")
    run_parser.add_argument("--stars", type=int, default=5, help="Rating bintang (1-5)")
    run_parser.add_argument("--mode", "-m", choices=["queue", "parallel"], default="queue", help="Mode eksekusi: queue (anti-bot aman) atau parallel")
    run_parser.add_argument("--delay", "-d", type=int, default=60, help="Jeda alami antar antrean akun dalam detik (default: 60)")

    # Command: queue
    q_parser = subparsers.add_parser("queue", help="Lihat daftar antrean review aktif")
    q_parser.add_argument("--business", "-b", type=int, default=None, help="ID Bisnis target (opsional)")

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
    p_rdel.add_argument("--all-accounts", "-a", action="store_true", help="Hapus ulasan dari SEMUA akun bot di Google Maps")

    args = parser.parse_args()
    client = ServerClient(base_url=args.server, api_key=args.key or "")

    # Jalankan pemeriksaan update versi otomatis sebelum masuk menu / task
    if not args.no_update:
        check_and_apply_update(client)

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
        elif args.command == "queue":
            res = client.get_queue(args.business)
            print_queue_table(res.get("queue", []))
        elif args.command == "run":
            run_task_stream(client, args.business, count=args.slots, star_rating=args.stars, mode=args.mode, delay=args.delay)
        elif args.command == "review-del":
            if args.maps:
                run_delete_maps_stream(
                    client,
                    args.business,
                    scope_label="Semua Akun Master" if args.all_accounts else "Akun Review Terbit",
                    all_accounts=args.all_accounts,
                )
            elif args.review_id:
                res = client.delete_single_review(args.business, args.review_id)
                print(f"{C_GREEN}✓ Review #{args.review_id} berhasil dihapus dari database.{C_RESET}")
            else:
                res = client.delete_all_reviews(args.business)
                print(f"{C_GREEN}✓ {res.get('message', 'Semua ulasan di database berhasil dihapus.')}{C_RESET}")


if __name__ == "__main__":
    main()
