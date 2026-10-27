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
import sys
import time
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

    def __init__(self, base_url: str = DEFAULT_SERVER, api_key: str = DEFAULT_API_KEY, username: str = ""):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.username = username

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

    def _request(self, endpoint: str, method: str = "GET", data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        headers = {
            "User-Agent": "AutoBotix-Windows-CLI/1.0",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["X-API-Key"] = self.api_key

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


# ── UI Helpers ────────────────────────────────────────────────────────────────

def print_banner(client: ServerClient, status_info: Optional[Dict[str, Any]] = None):
    print(f"{C_CYAN}")
    print(r"  ___         __        ____        __  _      ")
    print(r" /   | __  __/ /_____  / __ )____  / /_(_)  __ ")
    print(r"/ /| |/ / / / __/ __ \/ __  / __ \/ __/ / |/_/ ")
    print(r"/ ___ / /_/ / /_/ /_/ / /_/ / /_/ / /_/ />  <   ")
    print(r"/_/  |_\__,_/\__/\____/_____/\____/\__/_/_/|_|   ")
    print(f"{C_RESET}")
    print(f" {C_BOLD}{C_WHITE}AutoBotix Google Review Automation • Windows CMD Client{C_RESET}")
    user_str = f" {C_DIM}| Login User: {C_GREEN}{client.username or 'admin'}{C_RESET}" if client.api_key else ""
    print(f" {C_DIM}Koneksi Server: {C_GREEN}{client.base_url}{C_RESET} {C_DIM}(Engine: Native Chromium / Zero-VM){C_RESET}{user_str}")

    if status_info:
        b_cnt = status_info.get("businesses_count", 0)
        a_cnt = status_info.get("accounts_count", 0)
        c_cnt = status_info.get("active_cookies", 0)
        r_cnt = status_info.get("reviewed_count", 0)
        p_cnt = status_info.get("pending_count", 0)
        disps = " ".join(status_info.get("displays", []))
        print(f" {C_DIM}Target Bisnis: {C_WHITE}{b_cnt}{C_RESET} {C_DIM}| Akun: {C_WHITE}{a_cnt}{C_RESET} {C_DIM}| Cookie Aktif: {C_GREEN}{c_cnt}{C_RESET} {C_DIM}| Ulasan Selesai: {C_GREEN}{r_cnt}{C_RESET} {C_DIM}| Antrean: {C_YELLOW}{p_cnt}{C_RESET}")
        print(f" {C_DIM}Xvfb Displays Aktif: {C_CYAN}{disps}{C_RESET}")
    print("-" * 72)


def prompt_login(client: ServerClient, default_user: str = "admin") -> bool:
    """Prompt user for username and password with masked input before accessing task menu."""
    import getpass

    os.system("cls" if os.name == "nt" else "clear")
    print(f"{C_CYAN}")
    print(r"  ___         __        ____        __  _      ")
    print(r" /   | __  __/ /_____  / __ )____  / /_(_)  __ ")
    print(r"/ /| |/ / / / __/ __ \/ __  / __ \/ __/ / |/_/ ")
    print(r"/ ___ / /_/ / /_/ /_/ / /_/ / /_/ / /_/ />  <   ")
    print(r"/_/  |_\__,_/\__/\____/_____/\____/\__/_/_/|_|   ")
    print(f"{C_RESET}")
    print(f" {C_BOLD}{C_WHITE}AutoBotix Google Review Automation • Windows CMD Client{C_RESET}")
    print(f" {C_DIM}Koneksi Server: {C_GREEN}{client.base_url}{C_RESET} {C_DIM}(Engine: Native Chromium / Zero-VM){C_RESET}")
    print("=" * 72)
    print(f" {C_BOLD}{C_YELLOW}LOGIN PENGGUNA (AUTENTIKASI SEBELUM MASUK DAFTAR MENU){C_RESET}")
    print(f" {C_DIM}Silakan masukkan username dan password akun server AutoBotix Anda.{C_RESET}")
    print("=" * 72)

    attempts = 0
    max_attempts = 5
    while attempts < max_attempts:
        attempts += 1
        try:
            user_in = input(f"\n{C_CYAN}Username [{default_user}]: {C_RESET}").strip()
            username = user_in if user_in else default_user

            if sys.stdin.isatty():
                try:
                    password = getpass.getpass(f"{C_CYAN}Password: {C_RESET}").strip()
                except Exception:
                    password = input(f"{C_CYAN}Password: {C_RESET}").strip()
            else:
                password = input(f"{C_CYAN}Password: {C_RESET}").strip()

            if not password:
                print(f" {C_RED}✖ Password tidak boleh kosong.{C_RESET}")
                continue

            print(f" {C_DIM}Memverifikasi autentikasi ke server {client.base_url}...{C_RESET}")
            res = client.login(username, password)
            print(f" {C_BOLD}{C_GREEN}✓ Login berhasil! Selamat datang, {res.get('username', username)}.{C_RESET}")
            time.sleep(0.8)
            return True

        except (KeyboardInterrupt, EOFError):
            print(f"\n\n{C_YELLOW}Login dibatalkan oleh pengguna. Keluar.{C_RESET}")
            sys.exit(0)
        except RuntimeError as err:
            print(f" {C_BOLD}{C_RED}✖ {err}{C_RESET}")
            if attempts < max_attempts:
                print(f" {C_DIM}Percobaan {attempts}/{max_attempts}. Silakan coba lagi.{C_RESET}")
        except ConnectionError as err:
            print(f" {C_BOLD}{C_RED}✖ {err}{C_RESET}")
            print(f" {C_YELLOW}Pastikan server AutoBotix aktif di {client.base_url}.{C_RESET}")
            try:
                retry = input(f"\nCoba lagi? [Y/n]: ").strip().lower()
                if retry in ("n", "no"):
                    sys.exit(1)
            except (KeyboardInterrupt, EOFError):
                sys.exit(0)

    print(f"\n{C_RED}✖ Terlalu banyak percobaan gagal. Akses ditolak.{C_RESET}")
    sys.exit(1)


def print_businesses(businesses: List[Dict[str, Any]]):
    print(f"\n{C_BOLD}{C_CYAN}=== DAFTAR TARGET GOOGLE MAPS ==={C_RESET}")
    if not businesses:
        print(f"  {C_YELLOW}Belum ada target bisnis terdaftar.{C_RESET}")
        return

    print(f" {C_BOLD}{'ID':<5} {'NAMA BISNIS':<28} {'ULASAN':<8} {'URL GOOGLE MAPS'}{C_RESET}")
    print(" " + "-" * 70)
    for b in businesses:
        bid = b.get("id")
        name = b.get("name", "")[:26]
        rev = b.get("reviewed_count", 0)
        url = b.get("url", "")
        if len(url) > 35:
            url = url[:32] + "..."
        print(f" {C_YELLOW}{bid:<5}{C_RESET} {C_WHITE}{name:<28}{C_RESET} {C_GREEN}{rev:<8}{C_RESET} {C_DIM}{url}{C_RESET}")
    print()


def print_accounts(accounts: List[Dict[str, Any]]):
    print(f"\n{C_BOLD}{C_CYAN}=== STATUS AKUN & COOKIE GOOGLE ==={C_RESET}")
    if not accounts:
        print(f"  {C_YELLOW}Belum ada akun Google terdaftar.{C_RESET}")
        return

    print(f" {C_BOLD}{'ID':<5} {'AKUN EMAIL':<35} {'STATUS COOKIE':<18} {'FLAGGED'}{C_RESET}")
    print(" " + "-" * 70)
    for a in accounts:
        aid = a.get("id")
        email = a.get("email", "")[:33]
        c_status = a.get("cookie_status") or "no_cookie"
        flag = "Flagged" if a.get("flagged") else "Normal"

        if c_status == "active":
            st_color = f"{C_GREEN}● AKTIF{C_RESET}"
        elif c_status == "needs_login":
            st_color = f"{C_YELLOW}▲ PERLU LOGIN{C_RESET}"
        elif c_status == "expired":
            st_color = f"{C_RED}✖ KEDALUWARSA{C_RESET}"
        else:
            st_color = f"{C_DIM}- TIDAK ADA -{C_RESET}"

        fl_color = f"{C_RED}{flag}{C_RESET}" if flag == "Flagged" else f"{C_GREEN}{flag}{C_RESET}"
        print(f" {C_YELLOW}{aid:<5}{C_RESET} {C_WHITE}{email:<35}{C_RESET} {st_color:<27} {fl_color}")
    print()


# ── Task Execution & Live Log Monitor ─────────────────────────────────────────

def run_task_stream(client: ServerClient, business_id: int, count: int = 1, star_rating: int = 5):
    print(f"\n{C_BOLD}{C_CYAN}--- MEMULAI TUGAS ULASAN DARI WINDOWS CMD ---{C_RESET}")
    print(f" {C_DIM}Mengirim instruksi ke server {client.base_url}...{C_RESET}")

    try:
        res = client.start_task(business_id, count=count, star_rating=star_rating)
        print(f" {C_GREEN}✓ Task berhasil dijadwalkan di server!{C_RESET} (Jobs: {res.get('jobs_created', count)}, Antrean: {res.get('already_pending', 0)})")
        print(f" {C_DIM}Membuka {count} browser Chromium native pada server Linux...{C_RESET}")
    except Exception as exc:
        print(f" {C_RED}✖ Gagal memulai task: {exc}{C_RESET}")
        return False

    print(f"\n{C_BOLD}{C_CYAN}=== LIVE PROCESS LOGS (SERVER CHROMIUM) ==={C_RESET}")
    print(f" {C_DIM}Memantau perkembangan ulasan secara live... (Tekan Ctrl+C untuk kembali){C_RESET}\n")

    seen_ids = set()
    start_time = time.time()
    task_finished = False
    spinner_chars = ["|", "/", "-", "\\"]
    sp_idx = 0

    try:
        while True:
            sp_idx = (sp_idx + 1) % len(spinner_chars)
            sp = spinner_chars[sp_idx]

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

                    if lvl == "success":
                        tag = f"{C_GREEN}[SUCCESS]{C_RESET}"
                        msg_color = f"{C_GREEN}{msg}{C_RESET}"
                    elif lvl in ("error", "fatal"):
                        tag = f"{C_RED}[ERROR]{C_RESET}"
                        msg_color = f"{C_RED}{msg}{C_RESET}"
                    elif lvl == "warning":
                        tag = f"{C_YELLOW}[WARN]{C_RESET}"
                        msg_color = f"{C_YELLOW}{msg}{C_RESET}"
                    else:
                        tag = f"{C_BLUE}[INFO]{C_RESET}"
                        msg_color = f"{C_WHITE}{msg}{C_RESET}"

                    print(f" {C_DIM}{ts}{C_RESET} {tag} {msg_color}")

                    if "Worker selesai memproses" in msg or "berhasil dikirim" in msg:
                        task_finished = True

                # If status becomes idle and we saw logs
                if task_finished and status == "idle":
                    break

            except Exception:
                pass

            time.sleep(1.0)
    except KeyboardInterrupt:
        print(f"\n{C_YELLOW}! Pemantauan live dihentikan oleh user. Tugas tetap berjalan di server.{C_RESET}")
        return True

    elapsed = int(time.time() - start_time)
    print(f"\n{C_BOLD}{C_GREEN}✓ Seluruh proses ulasan selesai dalam {elapsed} detik!{C_RESET}")
    return True


# ── Interactive Menu Loop ─────────────────────────────────────────────────────

def interactive_menu(client: ServerClient):
    # Wajib login terlebih dahulu sebelum masuk ke sesi task dan menampilkan daftar menu
    if not client.api_key:
        prompt_login(client)

    while True:
        try:
            status_info = client.get_status()
        except Exception as e:
            print(f"\n{C_RED}✖ Gagal menghubungi server {client.base_url}: {e}{C_RESET}")
            print(f"Pastikan server AutoBotix aktif di jaringan (IP: {client.base_url}).")
            try:
                retry = input(f"\n[1] Coba Lagi  [2] Ganti Login  [0] Keluar: ").strip()
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

        print(f"{C_BOLD}{C_CYAN}  DAFTAR MENU UTAMA:{C_RESET}")
        print(f"  {C_YELLOW}[1]{C_RESET} {C_WHITE}🚀 Jalankan Task (Run Review Automation){C_RESET}")
        print(f"  {C_YELLOW}[2]{C_RESET} {C_WHITE}🏢 Daftar Target Bisnis Google Maps{C_RESET}")
        print(f"  {C_YELLOW}[3]{C_RESET} {C_WHITE}➕ Tambah Target Bisnis Baru{C_RESET}")
        print(f"  {C_YELLOW}[4]{C_RESET} {C_WHITE}🍪 Status Akun & Cookie Google{C_RESET}")
        print(f"  {C_YELLOW}[5]{C_RESET} {C_WHITE}📊 Pantau Live Logs Server{C_RESET}")
        print(f"  {C_YELLOW}[6]{C_RESET} {C_WHITE}🛑 Hentikan Semua Worker / Emergency Stop{C_RESET}")
        print(f"  {C_YELLOW}[7]{C_RESET} {C_WHITE}🔄 Bersihkan Log / Reset Antrean Bisnis{C_RESET}")
        print(f"  {C_YELLOW}[0]{C_RESET} {C_RED}🚪 Logout & Keluar{C_RESET}")
        print("-" * 72)

        try:
            choice = input(f"{C_GREEN}Pilih menu [0-7] (default 1): {C_RESET}").strip() or "1"
        except (KeyboardInterrupt, EOFError):
            print("\nKeluar.")
            break

        if choice == "0":
            client.api_key = ""
            print(f"\n{C_DIM}Anda telah logout. Terima kasih telah menggunakan AutoBotix CLI. Sampai jumpa!{C_RESET}")
            break

        elif choice == "1":
            businesses = status_info.get("businesses", [])
            print_businesses(businesses)
            if not businesses:
                input("Tekan Enter untuk kembali...")
                continue

            try:
                bid_in = input(f"{C_GREEN}Masukkan ID Bisnis target: {C_RESET}").strip()
                if not bid_in.isdigit():
                    print(f"{C_RED}ID tidak valid.{C_RESET}")
                    time.sleep(1)
                    continue
                bid = int(bid_in)

                slots_in = input(f"{C_GREEN}Jumlah Browser / Akun Paralel (1-6, default 1): {C_RESET}").strip() or "1"
                slots = max(1, min(6, int(slots_in) if slots_in.isdigit() else 1))

                stars_in = input(f"{C_GREEN}Rating Bintang (1-5, default 5): {C_RESET}").strip() or "5"
                stars = max(1, min(5, int(stars_in) if stars_in.isdigit() else 5))

                confirm = input(f"\n{C_BOLD}Jalankan {slots} ulasan bintang {stars} untuk ID {bid} sekarang? [Y/n]: {C_RESET}").strip().lower()
                if confirm in ("", "y", "yes"):
                    run_task_stream(client, bid, count=slots, star_rating=stars)
            except Exception as exc:
                print(f"{C_RED}Error: {exc}{C_RESET}")

            input(f"\n{C_DIM}Tekan Enter untuk kembali ke menu...{C_RESET}")

        elif choice == "2":
            print_businesses(status_info.get("businesses", []))
            input(f"{C_DIM}Tekan Enter untuk kembali...{C_RESET}")

        elif choice == "3":
            print(f"\n{C_BOLD}{C_CYAN}=== TAMBAH TARGET BISNIS BARU ==={C_RESET}")
            name = input(f"{C_GREEN}Nama Bisnis / Tempat: {C_RESET}").strip()
            url = input(f"{C_GREEN}URL Google Maps: {C_RESET}").strip()
            cat = input(f"{C_GREEN}Kategori Bisnis (default General): {C_RESET}").strip() or "General"
            if name and url:
                try:
                    res = client.add_business(name, url, cat)
                    print(f"\n{C_GREEN}✓ Bisnis '{name}' berhasil didaftarkan di server!{C_RESET}")
                except Exception as e:
                    print(f"\n{C_RED}✖ Gagal menambahkan: {e}{C_RESET}")
            else:
                print(f"{C_YELLOW}Nama dan URL wajib diisi.{C_RESET}")
            input(f"\n{C_DIM}Tekan Enter untuk kembali...{C_RESET}")

        elif choice == "4":
            print_accounts(status_info.get("accounts", []))
            input(f"{C_DIM}Tekan Enter untuk kembali...{C_RESET}")

        elif choice == "5":
            businesses = status_info.get("businesses", [])
            print_businesses(businesses)
            bid_in = input(f"{C_GREEN}Masukkan ID Bisnis yang ingin dipantau log-nya: {C_RESET}").strip()
            if bid_in.isdigit():
                bid = int(bid_in)
                try:
                    log_data = client.get_logs(bid)
                    logs = log_data.get("logs", [])
                    print(f"\n{C_BOLD}{C_CYAN}--- LOG TERBARU (ID {bid}) ---{C_RESET}")
                    for l in logs[-20:]:
                        print(f" {C_DIM}{l.get('created_at')}{C_RESET} [{l.get('level').upper()}] {l.get('message')}")
                except Exception as e:
                    print(f"{C_RED}Gagal memuat log: {e}{C_RESET}")
            input(f"\n{C_DIM}Tekan Enter untuk kembali...{C_RESET}")

        elif choice == "6":
            businesses = status_info.get("businesses", [])
            print_businesses(businesses)
            bid_in = input(f"{C_GREEN}Masukkan ID Bisnis yang ingin dihentikan task-nya: {C_RESET}").strip()
            if bid_in.isdigit():
                try:
                    res = client.stop_task(int(bid_in))
                    print(f"{C_GREEN}✓ {res.get('message', 'Perintah stop berhasil dikirim ke server.')}{C_RESET}")
                except Exception as e:
                    print(f"{C_RED}Gagal menghentikan: {e}{C_RESET}")
            input(f"\n{C_DIM}Tekan Enter untuk kembali...{C_RESET}")

        elif choice == "7":
            businesses = status_info.get("businesses", [])
            print_businesses(businesses)
            bid_in = input(f"{C_GREEN}Masukkan ID Bisnis yang ingin dibersihkan log-nya: {C_RESET}").strip()
            if bid_in.isdigit():
                try:
                    res = client.clear_logs(int(bid_in))
                    print(f"{C_GREEN}✓ {res.get('message', 'Log berhasil dibersihkan.')}{C_RESET}")
                except Exception as e:
                    print(f"{C_RED}Gagal membersihkan log: {e}{C_RESET}")
            input(f"\n{C_DIM}Tekan Enter untuk kembali...{C_RESET}")


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
        elif args.command == "run":
            run_task_stream(client, args.business, count=args.slots, star_rating=args.stars)


if __name__ == "__main__":
    main()
