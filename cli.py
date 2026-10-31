#!/usr/bin/env python3
"""AutoBotix Google Review Automation — Native Chromium CLI

A standalone, interactive terminal dashboard and automation engine.
Runs purely on Linux host with native Chromium (no Windows VM required).
"""

import argparse
import json
import logging
import os
import random
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Rich UI Library
from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table
from rich.text import Text
from rich.spinner import Spinner

# Internal modules
import db
import bot
import session_manager

console = Console()
logging.basicConfig(level=logging.WARNING)

SLOT_DISPLAYS = {
    0: ":99",
    1: ":100",
    2: ":101",
    3: ":102",
    4: ":103",
    5: ":104",
}

APP_TITLE = "AutoBotix Review Automation"
APP_SUBTITLE = "Native Linux Chromium Engine (Zero-VM Architecture)"


# ── System Diagnostics ────────────────────────────────────────────────────────

def get_chromium_version() -> str:
    try:
        out = subprocess.check_output(["chromium", "--version"], stderr=subprocess.DEVNULL, text=True)
        return out.strip().split("\n")[0]
    except Exception:
        return "Chromium (Tidak Ditemukan)"


def get_active_displays() -> Dict[str, bool]:
    displays = {}
    for slot, disp in SLOT_DISPLAYS.items():
        sock_num = disp.replace(":", "")
        sock_path = f"/tmp/.X11-unix/X{sock_num}"
        displays[disp] = os.path.exists(sock_path)
    return displays


def get_stats() -> Dict[str, Any]:
    db.init_db()
    with db.get_db() as conn:
        biz_count = conn.execute("SELECT COUNT(*) FROM businesses").fetchone()[0]
        acc_count = conn.execute("SELECT COUNT(*) FROM emails").fetchone()[0]
        cookie_count = conn.execute("SELECT COUNT(*) FROM cookies").fetchone()[0]
        active_cookies = conn.execute("SELECT COUNT(*) FROM cookies WHERE status = 'active'").fetchone()[0]
        oauth_count = conn.execute("SELECT COUNT(*) FROM cookies WHERE auth_method = 'oauth'").fetchone()[0]
        reviewed_count = conn.execute("SELECT COUNT(*) FROM reviews WHERE status = 'reviewed'").fetchone()[0]
        pending_count = conn.execute("SELECT COUNT(*) FROM reviews WHERE status = 'pending'").fetchone()[0]
    return {
        "businesses": biz_count,
        "accounts": acc_count,
        "cookies": cookie_count,
        "active_cookies": active_cookies,
        "oauth_count": oauth_count,
        "reviewed": reviewed_count,
        "pending": pending_count,
    }


# ── UI Components ─────────────────────────────────────────────────────────────

GOOGLE_MAPS_ICON_ART = """                      [bold white]:[/bold white][white]..[/white][bold red]%%%%[/bold red][white]..[/white][bold white]:[/bold white]
                   [bold white]:[/bold white][white].[/white][bold red]%@@@@@@@@@@%[/bold red][bold white]:[/bold white]
 [white]..................[/white][bold red]%@@%%%@@@%%%%@@[/bold red][white].[/white]
[dim white].[/dim white][bold green];##;#############[/bold green][dim white].[/dim white][bold red]@%%%@%[/bold red][dim white]....[/dim white][bold red]%%%%%@[/bold red][white].[/white]
[bold green]####[/bold green][bold blue]~[/bold blue][bold white]:::::[/bold white][bold green]########[/bold green][bold red]%%%%%@[/bold red][dim white]......[/dim white][bold red]%%%%@[/bold red][dim white].[/dim white]
[bold green]###[/bold green][white].[/white] [dim white].[/dim white][bold green]##[/bold green][dim white]..[/dim white][bold green]########[/bold green][dim white].[/dim white][bold red]@%%%%@[/bold red][dim white]...[/dim white][bold red]%@%%%@@[/bold red][bold white]:[/bold white]
[bold green]###[/bold green][bold white]:[/bold white] [bold green]#;#[/bold green][white]..[/white]  [bold green]#######[/bold green][bold red]%@%%%%%%%%%%%@@[/bold red][bold white]:[/bold white]
[bold green]####[/bold green][white].[/white][bold white]::[/bold white][white]..[/white][bold white]::[/bold white][dim white].[/dim white][bold green]######[/bold green][dim white].[/dim white][bold yellow]=[/bold yellow][dim white].[/dim white][bold red]@@%%%%%@%%@%[/bold red][bold white]:[/bold white]
[bold green]######[/bold green][dim white]...[/dim white][bold green]#######[/bold green][bold yellow]======[/bold yellow][bold red]%@%%%%%%@[/bold red][dim white].[/dim white][bold white]:[/bold white]
[bold green]##############[/bold green][bold yellow]=======[/bold yellow][bold white]::[/bold white][dim white].[/dim white][bold red]@%%%@@[/bold red][white].[/white][bold white]:[/bold white]
[bold green]############[/bold green][bold yellow]======[/bold yellow][bold white]::::::[/bold white][white].[/white][bold red]@%@%[/bold red][white].[/white][bold white]::[/bold white]
[bold green]##########[/bold green][bold yellow]======[/bold yellow][bold white]:[/bold white]     [bold white]:::[/bold white][dim white].[/dim white][bold red]@@[/bold red][white].[/white][bold white]:::[/bold white]
[bold green]########[/bold green][bold yellow]======[/bold yellow][white].[/white][bold blue]~~[/bold blue][white].[/white][bold white]:[/bold white]     [bold white]::[/bold white][bold red]@%[/bold red][bold white]::::[/bold white]
[bold green]######[/bold green][bold yellow]======[/bold yellow][white].[/white][bold blue]~~~~~~[/bold blue][white].[/white][bold white]:[/bold white]     [white]..[/white][bold white]::::[/bold white]
[bold green]####[/bold green][bold yellow]======[/bold yellow][white].[/white][bold blue]~~~~~~~~~~[/bold blue][white].[/white][bold white]:[/bold white]     [bold white]::::[/bold white]
[bold green]##[/bold green][bold yellow]======[/bold yellow][white].[/white][bold blue]~~~~~~~~~~~~~~[/bold blue][white].[/white][bold white]:[/bold white]     [bold white]::[/bold white]
[bold yellow]======[/bold yellow][white].[/white][bold blue]~~~~~~~~~~~~~~~~~~~[/bold blue][bold white]:[/bold white]
[bold white]:[/bold white][white].[/white][bold yellow]==[/bold yellow][white].[/white][bold blue]~~~~~~~~~~~~~~~~~~~~~~[/bold blue][white].[/white][bold white]:[/bold white]"""


def render_banner() -> Panel:
    stats = get_stats()
    displays = get_active_displays()
    active_disp_str = " ".join([
        f"[bold green]{d}[/bold green]" if ok else f"[dim red]{d}[/dim red]"
        for d, ok in displays.items()
    ])
    chrom_ver = get_chromium_version()

    brand_header = (
        "[bold blue]G[/bold blue][bold red]o[/bold red][bold yellow]o[/bold yellow]"
        "[bold blue]g[/bold blue][bold green]l[/bold green][bold red]e[/bold red] "
        "[bold white]Maps[/bold white] [bold cyan]Review Automation Bot[/bold cyan]"
    )

    banner_text = f"""{GOOGLE_MAPS_ICON_ART}

{brand_header}
[dim]« Native Chromium • Zero-VM Architecture »[/dim]

[dim]Engine: {chrom_ver} | Display Xvfb: {active_disp_str}[/dim]
[dim]Target Bisnis: [bold white]{stats['businesses']}[/bold white] | Akun Google: [bold white]{stats['accounts']}[/bold white] | Akun Aktif: [bold green]{stats['active_cookies']}[/bold green] | OAuth: [bold blue]{stats.get('oauth_count', 0)}[/bold blue] | Ulasan Selesai: [bold green]{stats['reviewed']}[/bold green] | Antrean: [bold yellow]{stats['pending']}[/bold yellow][/dim]"""

    return Panel(
        Align.center(banner_text),
        box=box.ROUNDED,
        border_style="bright_blue",
        padding=(0, 2),
    )


def print_businesses_table():
    businesses = db.get_all_businesses()
    if not businesses:
        console.print("[yellow]Belum ada target bisnis terdaftar. Tambahkan bisnis melalui menu [3].[/yellow]")
        return

    table = Table(title="🏢 Daftar Target Google Maps", box=box.ROUNDED, header_style="bold cyan")
    table.add_column("ID", justify="center", style="bold white", width=6)
    table.add_column("Nama Bisnis", style="bold yellow")
    table.add_column("Kategori", style="dim")
    table.add_column("Ulasan Selesai", justify="center", style="green")
    table.add_column("URL Google Maps", style="dim blue", overflow="ellipsis", max_width=45)

    for b in businesses:
        table.add_row(
            str(b["id"]),
            b["name"],
            b.get("business_category") or "-",
            str(b.get("reviewed_count") or 0),
            b["url"]
        )

    console.print(table)


def print_cookies_table():
    db.init_db()
    with db.get_db() as conn:
        rows = conn.execute("""
            SELECT e.id, e.email, e.flagged, e.fail_count,
                   c.status AS cookie_status, c.updated_at, c.error_reason,
                   c.auth_method, c.account_name,
                   LENGTH(c.cookie_json) AS cookie_len,
                   c.oauth_account_expiry,
                   c.oauth_access_token
            FROM emails e
            LEFT JOIN cookies c ON e.email = c.email
            ORDER BY e.id ASC
        """).fetchall()

    if not rows:
        console.print("[yellow]Belum ada akun Google terdaftar di database.[/yellow]")
        return

    table = Table(title="🔑 Daftar Akun Google (OAuth & Cookie)", box=box.ROUNDED, header_style="bold cyan")
    table.add_column("ID", justify="center", width=5)
    table.add_column("Akun Email", style="bold white")
    table.add_column("Nama Akun", style="cyan", max_width=20)
    table.add_column("Metode", justify="center", width=10)
    table.add_column("Status", justify="center")
    table.add_column("Info Sesi", justify="right", style="dim")
    table.add_column("Flag / Gagal", justify="center")
    table.add_column("Catatan / Error", style="dim red", overflow="ellipsis", max_width=35)

    import time as _time
    now = _time.time()

    for r in rows:
        c_status = r["cookie_status"] or "no_cookie"
        auth_method = r["auth_method"] or "cookie"
        account_name = r["account_name"] or "-"

        if c_status == "active":
            status_badge = "[bold green]● AKTIF[/bold green]"
        elif c_status == "needs_login":
            status_badge = "[bold yellow]▲ PERLU LOGIN[/bold yellow]"
        elif c_status == "expired":
            status_badge = "[bold red]✖ KEDALUWARSA[/bold red]"
        else:
            status_badge = "[dim]TIDAK ADA[/dim]"

        if auth_method == "oauth":
            method_badge = "[bold blue]OAuth 2.0[/bold blue]"
            expiry = r["oauth_account_expiry"] or 0
            if expiry:
                secs_left = max(0, expiry - now)
                d = int(secs_left // 86400)
                h = int((secs_left % 86400) // 3600)
                time_str = f"{d}h {h}j" if d > 0 else f"{h}j"
            else:
                time_str = "-"
            tok = r["oauth_access_token"] or ""
            if tok:
                tok_snippet = f"{tok[:35]}... [Secured in Server DB]"
                session_info = f"{time_str}\n[dim cyan]{tok_snippet}[/dim cyan]"
            else:
                session_info = f"{time_str}"
        else:
            method_badge = "[dim]Cookie CDP[/dim]"
            cookie_sz = r["cookie_len"] or 0
            session_info = f"{cookie_sz} B" if cookie_sz else "-"

        flag_badge = f"[red]Flagged ({r['fail_count']})[/red]" if r["flagged"] else f"[green]Normal ({r['fail_count']})[/green]"

        table.add_row(
            str(r["id"]),
            r["email"],
            account_name,
            method_badge,
            status_badge,
            session_info,
            flag_badge,
            r["error_reason"] or "-"
        )

    console.print(table)


def print_recent_logs(business_id: Optional[int] = None, limit: int = 15):
    db.init_db()
    with db.get_db() as conn:
        if business_id:
            rows = conn.execute(
                "SELECT created_at, level, message FROM process_logs WHERE business_id = ? ORDER BY id DESC LIMIT ?",
                (business_id, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT created_at, level, message FROM process_logs ORDER BY id DESC LIMIT ?",
                (limit,)
            ).fetchall()

    table = Table(title="📊 Log Proses Terkini", box=box.SIMPLE, header_style="bold cyan")
    table.add_column("Waktu", style="dim", width=20)
    table.add_column("Level", justify="center", width=10)
    table.add_column("Pesan Log", style="white")

    for r in reversed(rows):
        lvl = (r["level"] or "info").lower()
        if lvl == "success":
            lvl_badge = "[bold green]SUCCESS[/bold green]"
        elif lvl in ("error", "fatal"):
            lvl_badge = "[bold red]ERROR[/bold red]"
        elif lvl == "warning":
            lvl_badge = "[bold yellow]WARN[/bold yellow]"
        else:
            lvl_badge = "[bold blue]INFO[/bold blue]"

        table.add_row(str(r["created_at"]), lvl_badge, r["message"])

    console.print(table)


# ── Live Terminal Review Task Runner ──────────────────────────────────────────

def run_task_interactive(business_id: int, screen_count: int = 1, star_rating: int = 5):
    biz = db.get_business(business_id)
    if not biz:
        console.print(f"[bold red]Bisnis ID {business_id} tidak ditemukan.[/bold red]")
        return False

    config = db.get_review_config(business_id) or {
        "business_description": "",
        "review_style": "random",
        "delay_seconds": 30,
        "screen_count": screen_count,
    }

    star_list = [star_rating] * screen_count
    db.clear_process_logs(business_id)
    db.reset_business_reviewing(business_id)

    created, pending_cnt = db.create_review_jobs(business_id, star_list)
    total_assigned = created + pending_cnt
    if total_assigned == 0:
        console.print("[bold red]Gagal: Tidak ada akun Google dengan cookie aktif yang tersedia.[/bold red]")
        console.print("[dim]Pastikan akun memiliki cookie aktif di menu Kelola Cookie.[/dim]")
        return False

    console.print(Panel(
        f"[bold white]Target:[/bold white] [bold yellow]{biz['name']}[/bold yellow]\n"
        f"[bold white]URL Google Maps:[/bold white] [dim]{biz['url']}[/dim]\n"
        f"[bold white]Alokasi Browser:[/bold white] [bold cyan]{screen_count} Chromium Instance(s) paralel pada Xvfb :99 s/d :{99 + screen_count - 1}[/bold cyan]\n"
        f"[bold white]Rating:[/bold white] [bold yellow]{'★' * star_rating}[/bold yellow] ({star_rating} Bintang)",
        title="🚀 Menjalankan Otomasi Ulasan Google Maps",
        border_style="cyan",
        box=box.ROUNDED
    ))

    # Run bot in a background thread
    worker_error = None
    is_done = False

    def _worker_thread():
        nonlocal worker_error, is_done
        try:
            bot.run_reviews(business_id, biz, config, delay=int(config.get("delay_seconds") or 30), max_parallel=screen_count)
        except Exception as exc:
            worker_error = exc
        finally:
            is_done = True

    t = threading.Thread(target=_worker_thread, daemon=True)
    t.start()

    # Live UI update loop
    spinner = Spinner("dots", style="bold cyan")
    with Live(console=console, refresh_per_second=3) as live:
        start_time = time.time()
        while not is_done:
            elapsed = int(time.time() - start_time)

            # Query current active/pending reviews
            with db.get_db() as conn:
                cur_reviews = conn.execute("""
                    SELECT r.id, r.status, r.star_rating, r.review_text, e.email
                    FROM reviews r
                    JOIN emails e ON r.email_id = e.id
                    WHERE r.business_id = ?
                    ORDER BY r.id ASC
                """, (business_id,)).fetchall()

                recent_logs = conn.execute("""
                    SELECT created_at, level, message
                    FROM process_logs
                    WHERE business_id = ?
                    ORDER BY id DESC LIMIT 5
                """, (business_id,)).fetchall()

            # Build slots table
            slots_table = Table(box=box.ROUNDED, expand=True, header_style="bold cyan")
            slots_table.add_column("Slot / Display", justify="center", width=16)
            slots_table.add_column("Akun Google", style="bold white", width=28)
            slots_table.add_column("Rating", justify="center", width=10)
            slots_table.add_column("Status Engine", width=26)

            for idx, rev in enumerate(cur_reviews[:screen_count]):
                disp = SLOT_DISPLAYS.get(idx, f":{99 + idx}")
                st = rev["status"]
                if st == "reviewed":
                    status_str = "[bold green]✓ Selesai Terbit[/bold green]"
                elif st == "reviewing":
                    status_str = f"{spinner.render(time.time())} [bold yellow]Sedang Memproses...[/bold yellow]"
                elif st == "failed":
                    status_str = "[bold red]✖ Gagal[/bold red]"
                else:
                    status_str = "[dim]Menunggu Giliran[/dim]"

                stars_badge = f"[yellow]{'★' * (rev['star_rating'] or 5)}[/yellow]"
                slots_table.add_row(
                    f"Slot {idx + 1} ({disp})",
                    rev["email"],
                    stars_badge,
                    status_str
                )

            # Build logs panel
            log_lines = []
            for l in reversed(recent_logs):
                lvl = l["level"]
                col = "green" if lvl == "success" else ("red" if lvl in ("error", "fatal") else ("yellow" if lvl == "warning" else "white"))
                log_lines.append(f"[dim]{l['created_at'].split()[-1]}[/dim] [{col}]{l['message']}[/{col}]")

            logs_text = "\n".join(log_lines) if log_lines else "[dim]Menunggu event engine...[/dim]"
            logs_panel = Panel(logs_text, title="📋 Live Engine Logs", box=box.ROUNDED, border_style="dim")

            panel_main = Panel(
                Group(
                    slots_table,
                    logs_panel,
                    Text(f"⏱ Waktu Berjalan: {elapsed} detik • Tekan Ctrl+C untuk membatalkan", justify="center", style="dim")
                ),
                title=f"⚡ Status Eksekusi Chromium Native ({biz['name']})",
                border_style="bright_blue",
                box=box.ROUNDED
            )

            live.update(panel_main)
            time.sleep(0.4)

    t.join(timeout=2.0)
    console.print()
    if worker_error:
        console.print(f"[bold red]Terjadi error selama eksekusi: {worker_error}[/bold red]")
        return False
    else:
        console.print("[bold green]✓ Seluruh tugas ulasan berhasil diselesaikan oleh engine Chromium![/bold green]")
        print_recent_logs(business_id, limit=6)
        return True


# ── Quick Diagnostic Test ─────────────────────────────────────────────────────

def test_chromium_native(display: str = ":99"):
    console.print(f"\n[cyan]Menjalankan uji cepat Chromium pada Display {display}...[/cyan]")
    from seleniumbase import Driver

    os.environ["DISPLAY"] = display
    driver = None
    try:
        console.print("[dim]1. Membuka browser Chromium...[/dim]")
        driver = Driver(browser="chrome", headless=False, uc=True)
        console.print("[dim]2. Menavigasi ke Google Maps...[/dim]")
        driver.get("https://www.google.com/maps?hl=en")
        driver.sleep(4)
        title = driver.title
        cur_url = driver.current_url
        console.print(f"[bold green]✓ Sukses! Chromium terhubung di {display}[/bold green]")
        console.print(f"  [dim]Title: {title}[/dim]")
        console.print(f"  [dim]URL:   {cur_url[:65]}...[/dim]")

        # Test cookie injection CDP
        console.print("[dim]3. Menguji kapabilitas CDP Network.setCookies...[/dim]")
        driver.execute_cdp_cmd("Network.enable", {})
        driver.execute_cdp_cmd("Network.setCookies", {"cookies": [
            {"name": "test_token", "value": "autobotix_ok", "domain": ".google.com", "path": "/"}
        ]})
        console.print("[bold green]✓ Injeksi cookie CDP Native Chromium berfungsi 100%![/bold green]")
        return True
    except Exception as exc:
        console.print(f"[bold red]✖ Uji diagnostik Chromium gagal: {exc}[/bold red]")
        return False
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


# ── Interactive Menu ──────────────────────────────────────────────────────────

def prompt_login_server(default_user: str = "admin") -> bool:
    """Prompt user for username and password before entering task session."""
    expected_user = os.environ.get("APP_USERNAME", "admin").strip()
    expected_pass = os.environ.get("APP_PASSWORD", "").strip()

    console.clear()
    console.print(Align.center(Panel(
        Text.assemble(
            ("AutoBotix Google Review Automation\n", "bold cyan"),
            ("Autentikasi Pengguna Sebelum Masuk Menu Task\n\n", "bold yellow"),
            ("Engine: Native Linux Chromium • Zero-VM Architecture\n", "dim"),
        ),
        box=box.ROUNDED,
        border_style="cyan",
        title="[bold yellow]LOGIN PENGGUNA[/bold yellow]",
    )))

    attempts = 0
    max_attempts = 5
    while attempts < max_attempts:
        attempts += 1
        try:
            u = Prompt.ask("[bold green]Username[/bold green]", default=default_user).strip()
            p = Prompt.ask("[bold green]Password[/bold green]", password=True).strip()

            pass_ok = (p == expected_pass)
            user_ok = (u.lower() == expected_user.lower() or u.lower() == "admin")

            if user_ok and pass_ok:
                console.print(f"\n[bold green]✓ Login berhasil! Selamat datang, {u}.[/bold green]")
                time.sleep(0.8)
                return True
            else:
                console.print(f"[bold red]✖ Username atau password salah! (Percobaan {attempts}/{max_attempts})[/bold red]\n")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Dibatalkan.[/dim]")
            sys.exit(0)

    console.print("[bold red]Terlalu banyak percobaan gagal. Akses ditolak.[/bold red]")
    sys.exit(1)


def interactive_loop():
    prompt_login_server()
    while True:
        console.clear()
        console.print(render_banner())

        console.print("\n[bold cyan]── MENU UTAMA ────────────────────────────────────────────────────────[/bold cyan]")
        console.print("  [bold yellow][1][/bold yellow] 🚀 [bold white]Jalankan Task (Run Review Automation)[/bold white]")
        console.print("  [bold yellow][2][/bold yellow] 🏢 [bold white]Daftar Target Bisnis[/bold white]")
        console.print("  [bold yellow][3][/bold yellow] ➕ [bold white]Tambah Target Bisnis Baru[/bold white]")
        console.print("  [bold yellow][4][/bold yellow] 🍪 [bold white]Kelola Cookie & Akun Google[/bold white]")
        console.print("  [bold yellow][5][/bold yellow] 🧪 [bold white]Tes Sesi & Validitas Cookie[/bold white]")
        console.print("  [bold yellow][6][/bold yellow] 📊 [bold white]Pantau Live Process Logs[/bold white]")
        console.print("  [bold yellow][7][/bold yellow] 🖥️  [bold white]Uji Browser Chromium (Diagnostik)[/bold white]")
        console.print("  [bold yellow][8][/bold yellow] 🔄 [bold white]Reset Antrean Ulasan Bisnis[/bold white]")
        console.print("  [bold yellow][9][/bold yellow] 🗑️  [bold white]Remove Ulasan (Hapus Review DB / Google Maps)[/bold white]")
        console.print("  [bold yellow][0][/bold yellow] 🚪 [bold red]Keluar[/bold red]")
        console.print("[bold cyan]───────────────────────────────────────────────────────────────────────[/bold cyan]")

        choice = Prompt.ask("\n[bold green]Pilih menu[/bold green]", choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], default="1")

        if choice == "0":
            console.print("\n[dim]Sampai jumpa![/dim]")
            break

        elif choice == "1":
            console.clear()
            console.print(render_banner())
            print_businesses_table()

            biz_id_str = Prompt.ask("\n[bold green]Masukkan ID Bisnis target[/bold green]")
            if not biz_id_str.isdigit():
                console.print("[red]ID tidak valid.[/red]")
                time.sleep(1.5)
                continue
            biz_id = int(biz_id_str)
            biz = db.get_business(biz_id)
            if not biz:
                console.print(f"[red]Bisnis dengan ID {biz_id} tidak ditemukan.[/red]")
                time.sleep(1.5)
                continue

            slots = IntPrompt.ask("[bold green]Jumlah Layar / Akun Paralel (1-6)[/bold green]", default=1)
            slots = max(1, min(6, slots))
            stars = IntPrompt.ask("[bold green]Rating Bintang (1-5)[/bold green]", default=5)
            stars = max(1, min(5, stars))

            if Confirm.ask(f"[bold cyan]Jalankan {slots} ulasan bintang {stars} untuk '{biz['name']}' sekarang?[/bold cyan]", default=True):
                run_task_interactive(biz_id, screen_count=slots, star_rating=stars)
            Prompt.ask("\n[dim]Tekan Enter untuk kembali ke menu...[/dim]")

        elif choice == "2":
            console.clear()
            console.print(render_banner())
            print_businesses_table()
            Prompt.ask("\n[dim]Tekan Enter untuk kembali...[/dim]")

        elif choice == "3":
            console.clear()
            console.print(render_banner())
            console.print("[bold cyan]➕ Tambah Target Google Maps Baru[/bold cyan]\n")
            name = Prompt.ask("[bold green]Nama Bisnis / Tempat[/bold green]")
            url = Prompt.ask("[bold green]URL Google Maps[/bold green]")
            cat = Prompt.ask("[bold green]Kategori Bisnis (Opsional)[/bold green]", default="General")
            desc = Prompt.ask("[bold green]Deskripsi Singkat (Opsional)[/bold green]", default="")

            if name and url:
                new_id = db.add_business(name, url)
                db.set_business_category(new_id, cat)
                if desc:
                    cfg = db.get_review_config(new_id) or {}
                    cfg["business_description"] = desc
                    db.save_review_config(new_id, cfg)
                console.print(f"\n[bold green]✓ Target '{name}' berhasil didaftarkan dengan ID {new_id}![/bold green]")
            Prompt.ask("\n[dim]Tekan Enter untuk kembali...[/dim]")

        elif choice == "4":
            console.clear()
            console.print(render_banner())
            print_cookies_table()
            Prompt.ask("\n[dim]Tekan Enter untuk kembali...[/dim]")

        elif choice == "5":
            console.clear()
            console.print(render_banner())
            print_cookies_table()
            email_target = Prompt.ask("\n[bold green]Masukkan email akun yang ingin diuji (atau 'all' untuk semua)[/bold green]", default="all")

            if email_target.lower() == "all":
                with db.get_db() as conn:
                    all_accs = conn.execute(
                        "SELECT email, auth_method FROM cookies ORDER BY id ASC"
                    ).fetchall()
            else:
                with db.get_db() as conn:
                    row = conn.execute("SELECT email, auth_method FROM cookies WHERE email = ?", (email_target.strip(),)).fetchone()
                all_accs = [row] if row else []

            console.print(f"\n[cyan]Menguji validitas sesi {len(all_accs)} akun...[/cyan]")
            import requests as _req
            sm = session_manager.SessionManager()
            for acc_row in all_accs:
                em = acc_row["email"]
                method = acc_row["auth_method"] or "cookie"
                if method == "oauth":
                    token = db.get_valid_oauth_token(em)
                    if token:
                        try:
                            ui = _req.get(
                                "https://www.googleapis.com/oauth2/v3/tokeninfo",
                                params={"access_token": token},
                                timeout=8,
                            )
                            if ui.status_code == 200:
                                console.print(f"  [bold green]✓ [OAuth] {em}: Token Aktif & Valid[/bold green]")
                            else:
                                console.print(f"  [bold yellow]▲ [OAuth] {em}: Token invalid (HTTP {ui.status_code})[/bold yellow]")
                        except Exception as e:
                            console.print(f"  [bold yellow]▲ [OAuth] {em}: Tidak dapat verifikasi ({e})[/bold yellow]")
                    else:
                        console.print(f"  [bold red]✖ [OAuth] {em}: Token kedaluwarsa, perlu re-auth[/bold red]")
                else:
                    res = sm.validate_account_cookie(em, target_domain="google.com")
                    if res.is_valid:
                        console.print(f"  [bold green]✓ [Cookie] {em}: Sesi Valid & Aktif[/bold green]")
                    else:
                        console.print(f"  [bold red]✖ [Cookie] {em}: {res.status.value} ({res.reason})[/bold red]")
            Prompt.ask("\n[dim]Tekan Enter untuk kembali...[/dim]")

        elif choice == "6":
            console.clear()
            console.print(render_banner())
            print_recent_logs(limit=25)
            Prompt.ask("\n[dim]Tekan Enter untuk kembali...[/dim]")

        elif choice == "7":
            console.clear()
            console.print(render_banner())
            disp_choice = Prompt.ask("[bold green]Pilih Display virtual[/bold green]", default=":99")
            test_chromium_native(display=disp_choice)
            Prompt.ask("\n[dim]Tekan Enter untuk kembali...[/dim]")

        elif choice == "8":
            console.clear()
            console.print(render_banner())
            print_businesses_table()
            b_id_str = Prompt.ask("\n[bold green]Masukkan ID Bisnis yang ingin di-reset antreannya[/bold green]")
            if b_id_str.isdigit():
                b_id = int(b_id_str)
                db.delete_business_queue(b_id)
                db.clear_process_logs(b_id)
                console.print(f"[bold green]✓ Antrean ulasan dan log untuk Bisnis ID {b_id} telah dibersihkan.[/bold green]")
            Prompt.ask("\n[dim]Tekan Enter untuk kembali...[/dim]")

        elif choice == "9":
            console.clear()
            console.print(render_banner())
            print_businesses_table()
            b_id_str = Prompt.ask("\n[bold green]Masukkan ID Bisnis target yang ingin dihapus ulasannya[/bold green]")
            if b_id_str.isdigit():
                b_id = int(b_id_str)
                biz = db.get_business(b_id)
                if not biz:
                    console.print(f"[red]Bisnis ID {b_id} tidak ditemukan.[/red]")
                else:
                    reviews = db.get_reviews_for_business(b_id)
                    console.print(f"\n[bold cyan]Target: {biz['name']} (ID {b_id})[/bold cyan] — Total {len(reviews)} ulasan tercatat.")
                    console.print("  [bold yellow][1][/bold yellow] 🗑️  Hapus SEMUA ulasan di database target ini")
                    console.print("  [bold yellow][2][/bold yellow] 🔍  Hapus ulasan tertentu berdasarkan ID Review")
                    console.print("  [bold yellow][3][/bold yellow] 🛑  Hapus ulasan akun bot langsung di Google Maps (Chromium Live)")
                    console.print("  [bold yellow][0][/bold yellow] ↩️  Batal")

                    sub_c = Prompt.ask("[bold green]Pilih opsi[/bold green]", choices=["0", "1", "2", "3"], default="0")
                    if sub_c == "1":
                        if Confirm.ask(f"[bold red]Yakin hapus SEMUA ({len(reviews)}) ulasan untuk '{biz['name']}' dari database?[/bold red]"):
                            count = db.delete_all_reviews_for_business(b_id)
                            console.print(f"[bold green]✓ {count} ulasan berhasil dihapus dari database target {biz['name']}.[/bold green]")
                    elif sub_c == "2":
                        if not reviews:
                            console.print("[yellow]Tidak ada record ulasan untuk bisnis ini.[/yellow]")
                        else:
                            t = Table(box=box.SIMPLE_HEAVY)
                            t.add_column("ID", style="bold")
                            t.add_column("Status")
                            t.add_column("Rating")
                            t.add_column("Akun Email")
                            t.add_column("Cuplikan Ulasan")
                            for r in reviews[:20]:
                                st = str(r.get("status", "pending")).upper()
                                t.add_row(str(r["id"]), st, f"{r.get('star_rating', 5)} ★", str(r.get("email", "-")), (r.get("review_text") or "-")[:25])
                            console.print(t)
                            rid_in = Prompt.ask("[bold green]Masukkan ID Review yang ingin dihapus[/bold green]")
                            if rid_in.isdigit():
                                db.delete_review(int(rid_in))
                                console.print(f"[bold green]✓ Review #{rid_in} berhasil dihapus dari database.[/bold green]")
                    elif sub_c == "3":
                        posted = [r for r in reviews if r.get("status") in ("reviewed", "posted")]
                        with db.get_db() as conn:
                            all_emails = [dict(r) for r in conn.execute("SELECT id as email_id, email FROM emails ORDER BY id ASC").fetchall()]

                        console.print("\n[bold cyan]Pilih Target Akun di Google Maps:[/bold cyan]")
                        console.print(f"  [bold yellow][1][/bold yellow] 🌐  SEMUA Akun Master ({len(all_emails)} akun bot login & bersihkan ulasannya)")
                        console.print(f"  [bold yellow][2][/bold yellow] 📑  Hanya Akun yang Berstatus 'Reviewed' ({len(posted)} ulasan tercatat)")
                        console.print(f"  [bold yellow][0][/bold yellow] ↩️  Batal")
                        sc = Prompt.ask("[bold green]Pilih opsi[/bold green]", choices=["0", "1", "2"], default="1")

                        targets_to_clean = []
                        if sc == "1":
                            targets_to_clean = all_emails
                        elif sc == "2":
                            if not posted:
                                console.print("[yellow]Tidak ada ulasan berstatus 'reviewed' tercatat untuk bisnis ini.[/yellow]")
                            else:
                                targets_to_clean = posted

                        if targets_to_clean:
                            if Confirm.ask(f"[bold red]Luncurkan bot Chromium untuk MENGHAPUS ulasan di Google Maps untuk {len(targets_to_clean)} akun?[/bold red]"):
                                def run_del_bg(targs):
                                    for idx, row in enumerate(targs):
                                        bot.delete_own_review_on_maps(
                                            email=row.get("email"),
                                            maps_url=biz["url"],
                                            business_name=biz["name"],
                                            email_id=row.get("email_id"),
                                            business_id=b_id,
                                            slot_index=idx % 6,
                                        )
                                        time.sleep(2)
                                threading.Thread(target=run_del_bg, args=(targets_to_clean,), daemon=True).start()
                                console.print(f"[bold green]✓ Worker Chromium diluncurkan di background untuk memeriksa & menghapus ulasan {len(targets_to_clean)} akun di Google Maps.[/bold green]")
            Prompt.ask("\n[dim]Tekan Enter untuk kembali...[/dim]")


# ── CLI Subcommands Entrypoint ────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AutoBotix Native Chromium CLI Engine (Zero-VM)")
    subparsers = parser.add_subparsers(dest="command", help="Perintah langsung")

    # Command: run
    run_parser = subparsers.add_parser("run", help="Jalankan tugas ulasan u/ bisnis tertentu")
    run_parser.add_argument("--business", "-b", type=int, required=True, help="ID Bisnis target")
    run_parser.add_argument("--slots", "-s", type=int, default=1, help="Jumlah slot browser paralel (1-6)")
    run_parser.add_argument("--stars", type=int, default=5, help="Rating bintang (1-5)")

    # Command: status
    subparsers.add_parser("status", help="Lihat ringkasan status sistem & database")

    # Command: businesses
    subparsers.add_parser("businesses", help="Daftar seluruh target bisnis Google Maps")

    # Command: cookies
    cookie_parser = subparsers.add_parser("cookies", help="Daftar status akun & cookie Google")
    cookie_parser.add_argument("--check", action="store_true", help="Uji validitas cookie")

    # Command: logs
    log_parser = subparsers.add_parser("logs", help="Lihat log proses terkini")
    log_parser.add_argument("--business", "-b", type=int, default=None, help="Filter per ID Bisnis")
    log_parser.add_argument("--lines", "-n", type=int, default=25, help="Jumlah baris log")

    # Command: test-browser
    test_parser = subparsers.add_parser("test-browser", help="Uji Chromium pada display Xvfb")
    test_parser.add_argument("--display", "-d", default=":99", help="Display virtual (default: :99)")

    args = parser.parse_args()

    if not args.command:
        # Interactive TUI mode
        try:
            interactive_loop()
        except KeyboardInterrupt:
            console.print("\n[dim]Dibatalkan oleh pengguna. Keluar.[/dim]")
            sys.exit(0)
    elif args.command == "status":
        console.print(render_banner())
    elif args.command == "businesses":
        print_businesses_table()
    elif args.command == "cookies":
        print_cookies_table()
        if args.check:
            import requests as _req
            import time as _t
            with db.get_db() as conn:
                all_accounts = conn.execute(
                    "SELECT email, auth_method, oauth_access_token, oauth_refresh_token, "
                    "oauth_token_expiry, cookie_json FROM cookies ORDER BY id ASC"
                ).fetchall()

            console.print("\n[bold cyan]🔍 Memverifikasi semua akun...[/bold cyan]")
            for row in all_accounts:
                em = row["email"]
                method = row["auth_method"] or "cookie"
                if method == "oauth":
                    # Check via token validity
                    token = db.get_valid_oauth_token(em)
                    if token:
                        try:
                            ui = _req.get(
                                "https://www.googleapis.com/oauth2/v3/tokeninfo",
                                params={"access_token": token},
                                timeout=8,
                            )
                            if ui.status_code == 200:
                                console.print(f"[green]● [OAuth] {em}: AKTIF ✓[/green]")
                            else:
                                console.print(f"[yellow]▲ [OAuth] {em}: Token invalid (HTTP {ui.status_code})[/yellow]")
                        except Exception as e:
                            console.print(f"[yellow]▲ [OAuth] {em}: Tidak dapat verifikasi ({e})[/yellow]")
                    else:
                        console.print(f"[red]✖ [OAuth] {em}: Token kedaluwarsa, perlu re-auth[/red]")
                else:
                    sm = session_manager.SessionManager()
                    res = sm.validate_account_cookie(em, target_domain="google.com")
                    col = "green" if res.is_valid else "red"
                    console.print(f"[{col}]● [Cookie] {em}: {res.status.value} ({res.reason})[/{col}]")
    elif args.command == "logs":
        print_recent_logs(business_id=args.business, limit=args.lines)
    elif args.command == "test-browser":
        test_chromium_native(display=args.display)
    elif args.command == "run":
        run_task_interactive(args.business, screen_count=args.slots, star_rating=args.stars)


if __name__ == "__main__":
    main()
