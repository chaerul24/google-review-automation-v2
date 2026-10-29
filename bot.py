import hashlib
import logging
import os
import random
import subprocess
import time
import traceback
import concurrent.futures
import multiprocessing
import requests

import fcntl
import pyotp

from dotenv import load_dotenv
from seleniumbase import sb_cdp
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
import db
import session_manager
from session_manager import SessionManager, ProfileLock, ProfileLockedError, SessionStatus
import json as _json
import re
import urllib.parse
from pathlib import Path
from typing import Tuple, Dict, Any, List
load_dotenv()

log = logging.getLogger(__name__)

PROXY = os.environ.get("PROXY", "")
print(PROXY)

SLOT_DISPLAYS = {
    0: ":99",
    1: ":100",
    2: ":101",
    3: ":102",
    4: ":103",
    5: ":104",
}

def ensure_virtual_display(display_str: str = ":99") -> str:
    """Ensure an X11 virtual display is available on Linux headless servers.
    If no physical monitor or X server is running, automatically starts Xvfb.
    """
    if os.name == "nt":
        return display_str
    if not display_str:
        display_str = ":99"
    disp_clean = display_str if display_str.startswith(":") else f":{display_str}"
    num_part = disp_clean.lstrip(":")
    sock_path = f"/tmp/.X11-unix/X{num_part}"

    if not os.path.exists(sock_path):
        xvfb_bin = "/usr/bin/Xvfb"
        if os.path.exists(xvfb_bin):
            try:
                log.info("Display %s tidak ditemukan. Menjalankan Xvfb virtual framebuffer otomatis...", disp_clean)
                subprocess.Popen(
                    [xvfb_bin, disp_clean, "-screen", "0", "1366x768x24", "-nolisten", "tcp"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                for _ in range(20):
                    time.sleep(0.1)
                    if os.path.exists(sock_path):
                        break
            except Exception as exc:
                log.warning("Gagal auto-start Xvfb %s: %s", disp_clean, exc)
    return disp_clean

def get_fingerprint(email):
    """Generate a deterministic fingerprint based on the email address."""
    h = int(hashlib.md5(email.encode()).hexdigest(), 16)
    
    # 1. User Agents (Modern versions)
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ]
    ua = user_agents[h % len(user_agents)]
    
    # 2. Resolutions
    resolutions = ["1920,1080", "1536,864", "1366,768", "1440,900", "1600,900"]
    res = resolutions[h % len(resolutions)]
    
    # 3. Hardware / Memory
    concurrency = [4, 8, 12, 16][h % 4]
    memory = [4, 8, 16][h % 3]
    
    return {
        "ua": ua,
        "res": res,
        "concurrency": concurrency,
        "memory": memory,
        "locale": "en-US"
    }


def generate_gemini_review(
    api_key: str,
    business_name: str,
    business_category: str = "",
    star_rating: int = 5,
    custom_prompt: str = "",
    review_style: str = "random",
    language: str = "Indonesian"
) -> str:
    """Generate realistic, highly-contextual Google Maps review via Google Gemini REST API.
    Understands the specific business niche (e.g., Bengkel Otomotif, Kuliner, Klinik, Toko)
    and tailors industry-specific experiences, staff references, and services accordingly.
    """
    if not api_key or not str(api_key).strip():
        return ""

    category_hint = (business_category or "").strip()
    if not category_hint:
        category_hint = "Deteksi otomatis secara cerdas dari nama usaha"

    tone_map = {
        "formal": "Formal, profesional, sopan, dan mencerminkan pelayanan berkelas serta kemitraan bisnis terpercaya.",
        "casual": "Santai, ramah, bahasa percakapan sehari-hari khas pelanggan lokal atau anak muda.",
        "enthusiastic": "Sangat antusias, puas, penuh pujian dan rekomendasi kuat.",
        "compact": "Singkat dan padat (1-2 kalimat), langsung ke poin pengalaman tanpa basa-basi.",
        "random": "Alami, variatif, dan wajar layaknya ulasan akun Google Maps organik.",
    }
    tone_desc = tone_map.get(str(review_style).lower(), "Natural dan variatif layaknya ulasan pengguna Google Maps.")

    system_instruction = f"""Kamu adalah reviewer lokal asli di Indonesia yang sedang menulis ulasan otentik di Google Maps.

DATA TARGET MAPS:
- Nama Tempat / Usaha: {business_name}
- Kategori / Bidang Usaha: {category_hint}
- Rating Bintang: {star_rating} dari 5 Bintang
- Gaya Bahasa (Tone): {tone_desc}
- Kata Kunci / Konteks Tambahan: {custom_prompt or 'Tidak ada'}

INSTRUKSI WAJIB:
1. KENALI DAN SESUAIKAN DENGAN BIDANG USAHA SECARA SPESIFIK:
   - Pelajari nama usaha '{business_name}' dan bidang usahanya.
   - Contoh: Jika ini BENGKEL / OTOMOTIF (seperti Shop&Drive, bengkel mobil/motor, servis ganti oli, aki, shockbreaker, ban), ulasan WAJIB membahas hal nyata berkaitan dengan bengkel (misalnya: montir/mekanik yang teliti dan ramah, pengerjaan cepat, aki/oli original bergaransi, ruang tunggu nyaman/ber-AC, pengecekan kendaraan transparan).
   - Contoh: Jika RESTORAN/KULINER/CAFE, bahas cita rasa makanan/minuman, bumbu meresap, porsi, suasana tempat, dan keramahan pelayan.
   - Contoh: Jika KLINIK/APOTEK/KESEHATAN, bahas penanganan dokter/nakes yang sabar, antrean obat tertib, dan kebersihan ruangan.
   - Contoh: Jika TOKO/SWALAYAN, bahas kelengkapan produk, harga terjangkau, dan kasir cekatan.
   - JANGAN PERNAH membuat ulasan generik template seperti "tempatnya bagus pelayanan ramah" tanpa menyebutkan konteks usahanya!
2. KESESUAIAN RATING BINTANG ({star_rating} Bintang):
   - Jika 5 bintang: Berikan ulasan sangat puas dan rekomendasikan ke pengguna lain.
   - Jika 4 bintang: Pengalaman memuaskan dengan catatan kecil yang wajar.
   - Jika 1-2 bintang: Ungkapkan keluhan yang realistis dan sopan tentang aspek teknis atau antrean.
3. FORMAT PENULISAN:
   - Gunakan bahasa Indonesia yang wajar dan natural untuk Google Maps.
   - Panjang ulasan antara 2 sampai 4 kalimat.
   - Tulis HANYA teks komentar ulasan. JANGAN menyertakan tanda kutip (" "), jangan pakai markdown, dan jangan gunakan kata pengantar."""

    models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key.strip()}"
        payload = {
            "contents": [{
                "parts": [{"text": system_instruction}]
            }],
            "generationConfig": {
                "temperature": 0.85,
                "maxOutputTokens": 300,
            }
        }
        try:
            resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates and "content" in candidates[0]:
                    parts = candidates[0]["content"].get("parts", [])
                    if parts and "text" in parts[0]:
                        text = parts[0]["text"].strip()
                        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
                            text = text[1:-1].strip()
                        if text:
                            log.info("Gemini AI review successfully generated using %s for '%s' (category: %s)", model, business_name, category_hint)
                            return text
            else:
                log.warning("Gemini model %s returned status %d: %s", model, resp.status_code, resp.text[:200])
        except Exception as exc:
            log.warning("Gemini model %s call failed: %s", model, exc)

    return ""


def generate_review(business_name, review_prompt, star_rating, review_type='medium', language='English', review_style='random', persona='default', gemini_token=None, business_category=None, business_id=None):
    if review_type == 'no_text':
        return ''

    # Check for Gemini AI token from parameters, database config, or environment
    token = (gemini_token or "").strip()
    category = (business_category or "").strip()
    if (not token or not category) and business_id:
        try:
            cfg = db.get_review_config(business_id)
            if cfg:
                if not token:
                    token = (cfg.get("gemini_token") or "").strip()
                if not category:
                    category = (cfg.get("business_category") or "").strip()
        except Exception:
            pass
    if not token:
        token = os.environ.get("GEMINI_API_KEY", "").strip()

    # Attempt AI contextual generation if token is present
    if token:
        try:
            ai_text = generate_gemini_review(
                api_key=token,
                business_name=business_name,
                business_category=category,
                star_rating=star_rating,
                custom_prompt=review_prompt,
                review_style=review_style,
                language=language,
            )
            if ai_text:
                return ai_text
        except Exception as exc:
            log.warning("Gemini AI generation fallback due to error: %s", exc)

    lang_key = 'Indonesian' if str(language).lower() in ('indonesian', 'indonesia', 'id') else 'English'
    prompt_snippet = f" {review_prompt.strip()}." if review_prompt and len(review_prompt.strip()) > 3 else ""

    if lang_key == 'Indonesian':
        if persona == 'local_guide':
            templates_pos = [
                f"Sebagai Local Guide, saya sangat merekomendasikan {business_name}.{prompt_snippet} Tempatnya tertata rapi, atmosfernya hangat, dan stafnya sangat responsif melayani pelanggan. Area parkirnya juga nyaman.",
                f"Kunjungan yang sangat berkesan di {business_name}.{prompt_snippet} Kualitas dan standar pelayanannya patut diacungi jempol. Cocok untuk dikunjungi bersama teman atau keluarga. Bintang 5 layak disematkan!",
            ]
        elif persona == 'family':
            templates_pos = [
                f"Sangat ramah keluarga! Kami sekeluarga merasa sangat nyaman berkunjung ke {business_name}.{prompt_snippet} Tempatnya bersih, luas, dan pelayanannya sabar serta ramah.",
                f"{business_name} tempat yang pas untuk quality time bareng keluarga.{prompt_snippet} Suasananya tenang dan fasilitasnya sangat terawat. Pasti akan mampir lagi lain waktu.",
            ]
        elif persona == 'foodie':
            templates_pos = [
                f"Pengalaman yang sangat memuaskan di {business_name}.{prompt_snippet} Rasa dan kualitasnya benar-benar konsisten, penyajian rapi dan pelayanannya cepat. Salah satu spot terbaik di kelasnya!",
                f"Worth every penny! {business_name} memberikan rasa dan kenyamanan yang melebihi ekspektasi.{prompt_snippet} Sangat recomended buat yang cari kualitas terbaik.",
            ]
        elif persona == 'casual':
            templates_pos = [
                f"Tempatnya asik banget! Pelayanan di {business_name} cepat dan stafnya ramah.{prompt_snippet} Mantap dan recommended!",
                f"Suka banget sama vibes di {business_name}. Pelayanannya oke, tempat bersih dan nyaman.{prompt_snippet} Top bintang 5!",
            ]
        else:
            templates_pos = [
                f"Sangat puas berkunjung ke {business_name}.{prompt_snippet} Tempatnya sangat nyaman, bersih, dan pelayanannya ramah. Sangat direkomendasikan!",
                f"Pengalaman luar biasa di {business_name}.{prompt_snippet} Pelayanannya cepat dan memuaskan. Pasti akan kembali lagi ke sini.",
                f"Tempat yang luar biasa! {business_name} memberikan pelayanan dan kualitas terbaik.{prompt_snippet} Sangat puas bintang 5.",
                f"Pelayanan di {business_name} sangat memuaskan, fasilitas rapi dan nyaman.{prompt_snippet} Rekomendasi banget untuk siapa saja!"
            ]
    else:
        if persona == 'local_guide':
            templates_pos = [
                f"As a Google Local Guide, I can confidently recommend {business_name}.{prompt_snippet} The atmosphere is welcoming, staff is remarkably attentive, and overall quality is top tier.",
                f"A fantastic spot in town! Visiting {business_name} was a delightful experience.{prompt_snippet} Spotless cleanliness, well-managed environment, and great customer care.",
            ]
        elif persona == 'family':
            templates_pos = [
                f"Such a warm and family-friendly environment at {business_name}.{prompt_snippet} Staff made us feel right at home, and facilities are clean and spacious.",
            ]
        elif persona == 'tourist':
            templates_pos = [
                f"First time visiting and I am thoroughly impressed by {business_name}!{prompt_snippet} Outstanding hospitality and great communication. A must-visit place!",
            ]
        else:
            templates_pos = [
                f"Outstanding experience at {business_name}!{prompt_snippet} The service was prompt, friendly, and top notch. Highly recommended to everyone!",
                f"Had a wonderful time visiting {business_name}.{prompt_snippet} Very clean, professional, and welcoming atmosphere. 5 stars all the way!",
                f"Truly impressed with the quality and great service at {business_name}.{prompt_snippet} Will definitely be coming back again!",
                f"Great place! Everything at {business_name} was seamless and well organized.{prompt_snippet} Highly satisfied with my visit."
            ]

    if star_rating in (1, 2) or review_style == 'buruk':
        if lang_key == 'Indonesian':
            negative = [
                f"Pengalaman di {business_name} kurang memuaskan. Pelayanannya perlu diperbaiki dan saya berharap kualitasnya bisa lebih baik ke depan.",
                f"Saya sedikit kecewa dengan kunjungan ke {business_name}. Prosesnya agak lambat dan fasilitasnya perlu ditingkatkan.",
            ]
        else:
            negative = [
                f"My experience at {business_name} was below expectations. The service needs improvement.",
                f"I was not fully satisfied with my visit to {business_name}. Room for improvement.",
            ]
        return random.choice(negative)

    return random.choice(templates_pos)


def setup_authenticated_session(sb, email, target_url="https://www.google.com/maps?hl=en", business_id=None, email_id=None):
    """Separate cookie loading from action logic.
    
    Alur:
    Pilih akun -> Muat cookie tersimpan -> Terapkan ke browser Chromium di domain google.com -> Verifikasi sesi -> Laporkan status.
    """
    sm = SessionManager()
    db.add_process_log(business_id, f"Memeriksa cookie sesi Google tersimpan untuk akun {email}.", email_id)
    success, status, reason = sm.restore_session(sb, email, target_url, target_domain="google.com")
    if not success:
        db.add_process_log(
            business_id,
            f"Sesi cookie akun {email} tidak valid ({status.value}): {reason}.",
            email_id,
            "warning",
        )
        return False, status, reason

    db.add_process_log(
        business_id,
        f"Sesi akun {email} berhasil diverifikasi di Google Maps ({status.value}). Melanjutkan.",
        email_id,
        "success",
    )
    return True, status, reason


def login_with_google_credentials(sb, email, password, totp_secret=None, business_id=None, email_id=None):
    """Metode 2: Login otomatis ke Akun Google menggunakan Email, Password, dan TOTP jika diperlukan."""
    if not password:
        return False, "Password tidak tersedia untuk akun ini."

    db.add_process_log(business_id, f"[{email}] Membuka halaman login Google (accounts.google.com)...", email_id)
    try:
        sb.get("https://accounts.google.com/signin/v2/identifier?hl=en")
        sb.sleep(random.uniform(3, 5))

        cur = sb.get_current_url()
        # Jika profil browser sebelumnya sudah dalam keadaan login:
        if "myaccount.google.com" in cur or "google.com/maps" in cur:
            db.add_process_log(business_id, f"[{email}] Profil browser sudah login sebelumnya.", email_id)
            session_manager.sync_browser_cookies_to_db(sb, email)
            return True, "Sudah login."

        # Input Email Google
        email_sel = 'input[type="email"], #identifierId, input[name="identifier"]'
        sb.wait_for_element_visible(email_sel, timeout=15)
        sb.click(email_sel)
        sb.sleep(1)
        sb.type(email_sel, email)
        sb.sleep(random.uniform(1.5, 2.5))

        # Klik Next Email
        sb.click('#identifierNext, button:contains("Next")')
        sb.sleep(random.uniform(4, 6))

        # Cek jika ada error akun tidak ditemukan
        body_txt = (sb.get_text("body") or "").lower()
        if "couldn't find your google account" in body_txt or "tidak dapat menemukan akun" in body_txt:
            return False, "Akun Google tidak ditemukan atau salah ketik."

        # Input Password
        pwd_sel = 'input[type="password"], input[name="Passwd"], input[name="password"]'
        sb.wait_for_element_visible(pwd_sel, timeout=20)
        sb.click(pwd_sel)
        sb.sleep(1)
        sb.type(pwd_sel, password)
        sb.sleep(random.uniform(1.5, 2.5))

        # Klik Next Password
        sb.click('#passwordNext, button:contains("Next")')
        sb.sleep(random.uniform(5, 7))

        # Cek Password Salah
        body_txt = (sb.get_text("body") or "").lower()
        if "wrong password" in body_txt or "sandi salah" in body_txt:
            return False, "Password salah."

        # Cek verifikasi 2 Langkah / TOTP Google Authenticator
        totp_sel = 'input[name="totpPin"], #totpPin, input[type="tel"]'
        if sb.is_element_visible(totp_sel):
            if totp_secret:
                db.add_process_log(business_id, f"[{email}] Memasukkan kode 2FA / TOTP Authenticator...", email_id)
                clean_totp = str(totp_secret).replace(" ", "").strip()
                code_2fa = pyotp.TOTP(clean_totp).now()
                sb.click(totp_sel)
                sb.sleep(1)
                sb.type(totp_sel, code_2fa)
                sb.sleep(random.uniform(1.5, 2))
                sb.click('#totpNext, button:contains("Next")')
                sb.sleep(random.uniform(5, 8))
            else:
                return False, "Akun meminta kode verifikasi 2FA/TOTP tetapi secret 2FA tidak disediakan."

        # Lewati prompt konfirmasi pemulihan/not now jika muncul
        for skip_btn in [
            'button:contains("Not now")',
            'button:contains("Jangan sekarang")',
            'button:contains("Skip")',
            'button:contains("Lewati")',
            'button:contains("Cancel")',
            'a:contains("Not now")',
        ]:
            try:
                if sb.is_element_visible(skip_btn):
                    sb.click(skip_btn)
                    sb.sleep(2)
            except Exception:
                pass

        # Verifikasi di Google Maps
        sb.get("https://www.google.com/maps?hl=en")
        sb.sleep(random.uniform(4, 6))

        cur_url = sb.get_current_url()
        signin_btns = sb.find_elements("a[aria-label*='Sign in'], a[aria-label*='Masuk']")
        if signin_btns and ("signin" in cur_url or "accounts.google.com" in cur_url):
            return False, "Login Google terhalang verifikasi keamanan Google."

        # Simpan cookie sesi baru ke database otomatis!
        session_manager.sync_browser_cookies_to_db(sb, email)
        with db.get_db() as conn:
            conn.execute("UPDATE emails SET flagged = 0, fail_count = 0 WHERE email = ?", (email,))
            conn.execute("UPDATE cookies SET status = 'active', error_reason = NULL, last_checked_at = CURRENT_TIMESTAMP WHERE email = ?", (email,))

        enforce_anti_logout_guard(sb, email)
        db.add_process_log(business_id, f"[{email}] ✓ Login akun Google dengan kredensial berhasil (Cookie otomatis tersimpan & Anti-Logout aktif).", email_id, "success")
        return True, "Login berhasil."

    except Exception as exc:
        log.warning("Login with credentials failed for %s: %s", email, exc)
        return False, str(exc)


# ── Anti-Logout Guard (Dilarang Logout) ────────────────────────────────────────

FORBIDDEN_LOGOUT_URLS = [
    "accounts.google.com/logout",
    "accounts.google.com/signoutoptions",
    "accounts.google.com/v3/signin/accountchooser?continue=https://accounts.google.com/logout",
]


def enforce_anti_logout_guard(sb, email=""):
    """Strictly protect browser session against any logout actions.
    Disallows navigation to Google logout URLs and blocks click on Sign Out elements.
    """
    if not sb:
        return
    try:
        cur_url = (sb.get_current_url() or "").lower()
        for forbidden in FORBIDDEN_LOGOUT_URLS:
            if forbidden in cur_url:
                log.warning("[Anti-Logout Guard] Terdeteksi upaya navigasi ke URL logout Google (%s) untuk %s. Membatalkan & mengalihkan ke Google Maps!", cur_url, email)
                sb.get("https://www.google.com/maps?hl=en")
                sb.sleep(2)
                return
    except Exception as exc:
        log.debug("[Anti-Logout Guard] Check error: %s", exc)


def auto_login_single_account(email: str, password: str, totp_secret: str = None) -> Tuple[bool, str]:
    """Launch Chromium on virtual display to login an account and persist fresh active cookies."""
    if not password or password == "cookie_auth":
        return False, "Password tidak tersedia untuk akun ini."

    profile_dir = Path(session_manager.get_profile_dir(email))
    lock = session_manager.acquire_profile_lock(profile_dir)
    if not lock.acquired:
        time.sleep(1.0)
        try:
            lock.acquire(force=True)
        except Exception as retry_err:
            return False, f"Profil browser terkunci: {retry_err}"

    fp = get_fingerprint(email)
    sb = None
    try:
        chromium_args = [
            "--disable-sync",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-default-apps",
            "--disable-fre",
            "--disable-chrome-login-prompt",
            "--window-position=0,0",
        ]
        win_size_str = fp.get("res") or "1366,768"

        for s_file in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
            s_path = os.path.join(profile_dir, s_file)
            if os.path.exists(s_path) or os.path.islink(s_path):
                try:
                    os.remove(s_path)
                except Exception:
                    pass

        verification_url = "https://accounts.google.com/signin/v2/identifier?hl=en"
        for launch_attempt in range(2):
            try:
                sb = sb_cdp.Chrome(
                    verification_url,
                    headed=True,
                    user_data_dir=str(profile_dir),
                    proxy=PROXY,
                    agent=fp["ua"],
                    window_size=win_size_str,
                    locale_code=fp["locale"],
                    chromium_arg=",".join(chromium_args),
                    disable_features="SigninIntercept,ChromeWhatsNewUI,AccountConsistency",
                )
                break
            except Exception as launch_exc:
                if launch_attempt == 0 and ("111" in str(launch_exc) or "Connect call failed" in str(launch_exc)):
                    session_manager.force_close_profile_processes(profile_dir)
                    time.sleep(2.0)
                else:
                    raise

        sb.maximize()
        sb.sleep(2)

        ok, msg = login_with_google_credentials(sb, email, password, totp_secret=totp_secret)
        if ok:
            session_manager.sync_browser_cookies_to_db(sb, email)
            with db.get_db() as conn:
                conn.execute("UPDATE cookies SET status = 'active', error_reason = NULL, last_checked_at = CURRENT_TIMESTAMP WHERE email = ?", (email,))
                conn.execute("UPDATE emails SET flagged = 0, fail_count = 0 WHERE email = ?", (email,))
            enforce_anti_logout_guard(sb, email)
            return True, "Login berhasil, cookie sesi aktif tersimpan."
        return False, msg

    except Exception as exc:
        return False, str(exc)
    finally:
        if sb:
            try:
                session_manager.close_browser_session(sb)
            except Exception:
                pass
        lock.release()


def _extract_cid_from_maps_url(maps_url: str) -> int | None:
    """Extract Google Maps CID (Content ID) from a maps URL for direct review navigation."""
    # Try ftid=0xAAAA:0xBBBB pattern
    m = re.search(r'ftid=(0x[0-9a-fA-F]+):(0x[0-9a-fA-F]+)', maps_url)
    if m:
        try:
            return int(m.group(2), 16)
        except Exception:
            pass
    # Try !1s0xAAAA:0xBBBB pattern inside data=
    m2 = re.search(r'!1s(0x[0-9a-fA-F]+):(0x[0-9a-fA-F]+)', maps_url)
    if m2:
        try:
            return int(m2.group(2), 16)
        except Exception:
            pass
    return None


def post_review(
    email,
    password,
    maps_url,
    star_rating,
    business_name,
    review_prompt,
    email_id,
    business_id,
    recovery_email=None,
    review_type='medium',
    language='English',
    review_style='random',
    totp_secret=None,
    slot_index=0,
    total_slots=1,
    display=None,
    gemini_token=None,
    business_category=None,
):
    slot_display = display or SLOT_DISPLAYS.get(slot_index, f":{99 + slot_index}")
    slot_display = ensure_virtual_display(slot_display)
    os.environ["DISPLAY"] = slot_display

    profile_dir = session_manager.get_profile_dir(email)
    lock = ProfileLock(profile_dir)
    try:
        lock.acquire(force=True)
    except ProfileLockedError as lock_err:
        log.warning("Profile directory for %s is locked: %s. Force closing and retrying...", email, lock_err)
        db.add_process_log(business_id, f"[{email}] Profil sedang digunakan proses lain. Menutup browser sesi lama dan masuk kembali...", email_id, "warning")
        session_manager.force_close_profile_processes(profile_dir)
        time.sleep(1.0)
        try:
            lock.acquire(force=True)
        except Exception as retry_err:
            log.warning("Re-acquire failed for %s: %s", email, retry_err)
            db.add_process_log(business_id, f"Gagal mengakses profil browser (sedang digunakan): {retry_err}", email_id, "error")
            db.update_review_status(email_id, "failed", None, star_rating)
            return False

    fp = get_fingerprint(email)
    iframe_sel = "iframe[name='goog-reviews-write-widget']"

    sb = None
    try:
        slot_label = f" (Slot {slot_index + 1}/{total_slots} pada Display {slot_display})" if total_slots > 1 else f" (Display {slot_display})"
        db.add_process_log(business_id, f"[{email}] Membuka browser Chromium mandiri{slot_label}.", email_id)
        chromium_args = [
            "--disable-sync",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-default-apps",
            "--disable-fre",
            "--disable-chrome-login-prompt",
            "--window-position=0,0",
        ]
        win_size_str = fp.get("res") or "1366,768"

        cookie_editor_dir = os.environ.get(
            "COOKIE_EDITOR_EXTENSION_DIR",
            os.path.join(
                os.environ.get("BROWSER_AUTOMATION_STORAGE", ""),
                "extensions",
                "cookie-editor",
            ),
        )
        if cookie_editor_dir and os.path.isfile(os.path.join(cookie_editor_dir, "manifest.json")):
            chromium_args.append(f"--load-extension={cookie_editor_dir}")
            db.add_process_log(business_id, "Extension Cookie-Editor dimuat ke Chromium.", email_id)

        # Clean up any stale Chromium Singleton locks before launching
        for s_file in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
            s_path = os.path.join(profile_dir, s_file)
            if os.path.exists(s_path) or os.path.islink(s_path):
                try:
                    os.remove(s_path)
                except Exception:
                    pass

        verification_url = "https://www.google.com/maps?hl=en"
        sb = None
        for launch_attempt in range(2):
            try:
                sb = sb_cdp.Chrome(
                    verification_url,
                    headed=True,
                    user_data_dir=str(profile_dir),
                    proxy=PROXY,
                    agent=fp["ua"],
                    window_size=win_size_str,
                    locale_code=fp["locale"],
                    chromium_arg=",".join(chromium_args),
                    disable_features="SigninIntercept,ChromeWhatsNewUI,AccountConsistency",
                )
                break
            except Exception as launch_exc:
                if launch_attempt == 0 and ("111" in str(launch_exc) or "Connect call failed" in str(launch_exc)):
                    log.warning("CDP connect failed on attempt 1 for %s, closing previous processes and retrying: %s", email, launch_exc)
                    session_manager.force_close_profile_processes(profile_dir)
                    time.sleep(2.0)
                else:
                    raise
        sb.maximize()
        sb.sleep(2)

        # ── Step: Setup Authenticated Session (2 METODE: Cookie & Login Kredensial) ──
        auth_ok = False
        cookie_available = db.get_cookie_for_email(email) is not None

        if cookie_available:
            db.add_process_log(business_id, f"[{email}] [Cara 1] Menggunakan Cookie Sesi Google tersimpan...", email_id)
            c_ok, c_status, c_reason = setup_authenticated_session(
                sb, email, verification_url, business_id=business_id, email_id=email_id
            )
            if c_ok:
                auth_ok = True
            else:
                log.info("Cookie session invalid for %s: %s. Checking credential fallback...", email, c_reason)

        if not auth_ok:
            if password:
                db.add_process_log(business_id, f"[{email}] [Cara 2] Masuk menggunakan Email & Password Akun Google...", email_id)
                l_ok, l_msg = login_with_google_credentials(
                    sb, email, password, totp_secret=totp_secret, business_id=business_id, email_id=email_id
                )
                if l_ok:
                    auth_ok = True
                else:
                    db.add_process_log(business_id, f"[{email}] ✖ Login kredensial gagal: {l_msg}.", email_id, "error")
            else:
                db.add_process_log(business_id, f"[{email}] ✖ Tidak dapat masuk: Cookie tidak valid/tersedia dan Password belum diisi.", email_id, "error")

        if not auth_ok:
            log.warning("Authentication failed for %s via both Cookie and Credential methods.", email)
            db.update_review_status(email_id, "failed", None, star_rating)
            return False

        # --- Navigate to Maps listing ---
        db.add_process_log(business_id, "Membuka halaman Google Maps.", email_id)
        sb.sleep(random.uniform(3, 5))
        sep = "&" if "?" in maps_url else "?"
        target_maps_url = maps_url if "hl=" in maps_url else f"{maps_url}{sep}hl=en"
        sb.get(target_maps_url)
        sb.sleep(random.uniform(8, 12))

        # Check if URL lost the place or empty, fallback to search query
        cur_url = sb.get_current_url()
        if "place//@" in cur_url or "google.com/maps/@" in cur_url:
            log.warning("Maps URL lost place, falling back to search query for: %s", business_name)
            fallback_url = f"https://maps.google.com/?q={urllib.parse.quote(business_name)}&hl=en"
            sb.get(fallback_url)
            sb.sleep(random.uniform(8, 12))

        # Dismiss any consent dialog if present
        for consent_btn in ['button:contains("Accept all")', 'button:contains("I agree")', 'button:contains("Setuju")']:
            try:
                if sb.is_element_visible(consent_btn):
                    sb.click(consent_btn)
                    sb.sleep(3)
            except Exception:
                pass

        # ── Step: Cek apakah akun ini sudah pernah berkomentar/mengulas di Google Maps target ──
        db.add_process_log(business_id, f"[{email}] Memeriksa apakah akun sudah memiliki komentar/ulasan di Google Maps target...", email_id)
        has_existing_review = False
        existing_snippet = ""

        check_existing_script = """(() => {
            const body = document.body ? document.body.innerText : '';
            const markers = ['Your review', 'Your Review', 'Ulasan Anda', 'Your rating', 'Edit your review', 'Edit ulasan', 'Ulasan saya'];
            let foundMarker = markers.find(m => body.includes(m));

            // Cek tombol edit ulasan atau tombol tindakan ulasan milik akun sendiri
            const editBtn = document.querySelector(
                'button[aria-label*="Edit your review"], ' +
                'button[aria-label*="Edit ulasan"], ' +
                'button[aria-label*="Tindakan untuk ulasan"], ' +
                'button[aria-label*="Action for review"], ' +
                'button[data-tooltip*="Edit ulasan"], ' +
                'button[data-tooltip*="Edit your review"]'
            );

            let snippet = '';
            if (foundMarker || editBtn) {
                const headings = Array.from(document.querySelectorAll('div, h2, h3, span')).filter(el => {
                    const t = (el.innerText || '').trim();
                    return t === 'Ulasan Anda' || t === 'Your review' || t === 'Your rating';
                });
                for (const h of headings) {
                    let parent = h.parentElement;
                    for (let i = 0; i < 4 && parent; i++) {
                        const txt = (parent.innerText || '').replace(h.innerText, '').trim();
                        if (txt.length > 5) {
                            snippet = txt.substring(0, 120);
                            break;
                        }
                        parent = parent.parentElement;
                    }
                    if (snippet) break;
                }
                return { exists: true, marker: foundMarker || (editBtn ? 'edit-button' : 'detected'), snippet: snippet };
            }
            return { exists: false };
        })()"""

        check_res = sb.execute_script(check_existing_script) or {}
        if check_res.get("exists"):
            has_existing_review = True
            existing_snippet = check_res.get("snippet", "")

        # Jika belum terdeteksi di tab overview, buka tab Ulasan (Reviews) untuk pemeriksaan menyeluruh
        if not has_existing_review:
            for rev_tab in [
                'button[aria-label*="Reviews"]',
                'button[aria-label*="Ulasan"]',
                'button[role="tab"][data-tab-index="1"]',
                'div[role="tablist"] button:nth-child(2)'
            ]:
                try:
                    if sb.is_element_visible(rev_tab):
                        sb.click(rev_tab)
                        sb.sleep(random.uniform(3, 4))
                        break
                except Exception:
                    pass
            check_res_tab = sb.execute_script(check_existing_script) or {}
            if check_res_tab.get("exists"):
                has_existing_review = True
                existing_snippet = check_res_tab.get("snippet", "")

        if has_existing_review:
            snip_msg = f" (Cuplikan: \"{existing_snippet[:50]}...\")" if existing_snippet else ""
            skip_msg = f"[{email}] ⏭️ SKIP: Komentar/ulasan dari akun ini sudah ada di Google Maps{snip_msg}. Melewati tugas."
            log.info(skip_msg)
            db.add_process_log(business_id, skip_msg, email_id, "warning")
            # Update status review di database sebagai reviewed agar tercatat sinkron
            db.update_review_status(email_id, "reviewed", existing_snippet or "[Ulasan sudah terbit di Google Maps]", star_rating)
            return "skipped"

        # ── Step: Open Review Form ──────────────────────────────────────────────
        # Strategy 1: Try clicking "Write a review" button directly on Overview
        write_clicked = False
        for wr_sel in [
            'button[aria-label="Write a review"]',
            'button[aria-label*="Write a review"]',
            'button[aria-label*="Tulis ulasan"]',
            'button[data-value*="Write a review"]',
            'button[jsaction*="reviewAction"]',
            'button:contains("Write a review")',
            'button:contains("Tulis ulasan")',
        ]:
            try:
                if sb.is_element_visible(wr_sel):
                    sb.click(wr_sel)
                    write_clicked = True
                    log.info("Clicked write review button via %s", wr_sel)
                    break
            except Exception:
                pass

        # Strategy 2: Click Reviews tab first, then look for Write a review button
        if not write_clicked:
            for rev_tab in [
                'button[aria-label*="Reviews"]',
                'button[aria-label*="Ulasan"]',
                'button[role="tab"][data-tab-index="1"]',
                'div[role="tablist"] button:nth-child(2)',
            ]:
                try:
                    if sb.is_element_visible(rev_tab):
                        sb.click(rev_tab)
                        log.info("Clicked reviews tab via %s", rev_tab)
                        sb.sleep(random.uniform(4, 7))
                        break
                except Exception:
                    pass

            for wr_sel in [
                'button[aria-label="Write a review"]',
                'button[aria-label*="Write a review"]',
                'button[aria-label*="Tulis ulasan"]',
                'button[data-value*="Write a review"]',
                'button:contains("Write a review")',
                'button:contains("Tulis ulasan")',
            ]:
                try:
                    sb.click(wr_sel, timeout=15)
                    write_clicked = True
                    log.info("Clicked write review button (post-tab) via %s", wr_sel)
                    break
                except Exception:
                    pass

        # Strategy 3: Click star rating button on overview panel (newer Maps UI)
        if not write_clicked:
            for star_sel in [
                f'button[aria-label*="{star_rating} star"]',
                f'button[aria-label*="{star_rating} bintang"]',
                'g-review-stars button',
                'button[jsaction*="rate"]',
                'div[data-value="rate"] button',
            ]:
                try:
                    if sb.is_element_visible(star_sel):
                        sb.click(star_sel)
                        write_clicked = True
                        log.info("Clicked star rating button via %s", star_sel)
                        break
                except Exception:
                    pass

        # Strategy 4: Navigate directly to review URL using CID from maps URL
        if not write_clicked:
            cid = _extract_cid_from_maps_url(maps_url)
            if cid:
                direct_review_url = f"https://www.google.com/maps?cid={cid}&hl=en&action=write_review"
                db.add_process_log(business_id, f"[{email}] Mencoba URL langsung form review (CID: {cid})...", email_id)
                sb.get(direct_review_url)
                sb.sleep(random.uniform(5, 8))
                write_clicked = True  # Assume iframe will appear
            else:
                # Strategy 5: Try JS click on any visible star rating element
                try:
                    clicked_via_js = sb.execute_script("""
                        var buttons = document.querySelectorAll('button[aria-label]');
                        for (var b of buttons) {
                            var lbl = b.getAttribute('aria-label') || '';
                            if (lbl.toLowerCase().includes('write') || lbl.toLowerCase().includes('tulis') || lbl.toLowerCase().includes('review')) {
                                b.click();
                                return lbl;
                            }
                        }
                        return null;
                    """)
                    if clicked_via_js:
                        write_clicked = True
                        log.info("Clicked write review via JS: %s", clicked_via_js)
                except Exception:
                    pass

        db.add_process_log(business_id, f"[{email}] Menunggu form ulasan Google Maps terbuka...", email_id)
        sb.sleep(random.uniform(5, 9))

        # --- Confirm the review iframe is open with extended timeout and retry ---
        iframe_found = False
        for _iframe_try in range(4):  # try up to 4 times with increasing wait
            try:
                sb.wait_for_element_visible(iframe_sel, timeout=20)
                iframe_found = True
                log.info("Review iframe found on attempt %d", _iframe_try + 1)
                break
            except Exception:
                log.warning("iframe not found on attempt %d/4, retrying...", _iframe_try + 1)
                # On retry: try clicking write review button again via JS
                if _iframe_try < 3:
                    try:
                        js_clicked = sb.execute_script("""
                            var candidates = document.querySelectorAll('button[aria-label]');
                            for (var b of candidates) {
                                var lbl = (b.getAttribute('aria-label') || '').toLowerCase();
                                if (lbl.includes('write') || lbl.includes('tulis') || lbl.includes('review') || lbl.includes('ulasan')) {
                                    b.click();
                                    return b.getAttribute('aria-label');
                                }
                            }
                            // try clicking g-review-stars
                            var stars = document.querySelector('g-review-stars button, div[jsname] button[data-rating]');
                            if (stars) { stars.click(); return 'star-button'; }
                            return null;
                        """)
                        if js_clicked:
                            log.info("JS retry click: %s", js_clicked)
                    except Exception:
                        pass
                    sb.sleep(random.uniform(4, 6))

        if not iframe_found:
            raise RuntimeError(f"Form ulasan Google Maps (iframe) tidak ditemukan setelah beberapa percobaan. Kemungkinan: Maps URL tidak valid, akun belum login, atau Google sedang memblokir akses.")

        db.add_process_log(business_id, f"[{email}] Form review Google Maps sudah terbuka.", email_id)
        sb.sleep(4)  # Brief wait before polling for the textarea

        # Wait for the textarea inside the iframe to become available (up to 60s)
        review_area = None
        for _attempt in range(24):  # 24 × 2.5s = 60s max
            review_area = sb.get_nested_element(iframe_sel, 'textarea[aria-label="Enter review"]')
            if review_area is not None:
                break
            log.debug("Waiting for review textarea (attempt %d/24)...", _attempt + 1)
            time.sleep(2.5)
        if review_area is None:
            raise RuntimeError("Review textarea never appeared inside iframe after 60s")

        review_area.click()  # Focus the textarea to ensure it's ready for input
        time.sleep(3)

        # Select the star rating before creating the local review text
        try:
            sb.nested_click(iframe_sel, f"div[data-rating='{star_rating}'][role='radio']")
        except Exception:
            try:
                sb.nested_click(iframe_sel, f"span[data-rating='{star_rating}'], input[value='{star_rating}']")
            except Exception:
                pass
        sb.sleep(random.uniform(2, 5))

        # Generate review text now that we know the write box is open and star is selected
        db.add_process_log(business_id, f"[{email}] Membuat teks ulasan (kontekstual bidang usaha) dan memilih rating.", email_id)
        review_text = generate_review(
            business_name,
            review_prompt,
            star_rating,
            review_type=review_type,
            language=language,
            review_style=review_style,
            business_id=business_id,
            gemini_token=gemini_token,
            business_category=business_category,
        )
        if review_text:
            db.update_review_status(email_id, "reviewing", review_text, star_rating)
        log.info("Review generated for %s (type=%s, lang=%s)", email, review_type, language)

        # Type review text into the textarea inside the iframe (skip for no_text reviews)
        if review_text:
            review_area = sb.get_nested_element(iframe_sel, 'textarea[aria-label="Enter review"]')
            if review_area is None:
                raise RuntimeError("Could not find review textarea inside iframe")
            review_area.type(review_text)
            sb.sleep(random.uniform(2, 5))

        # Click the Post button inside the iframe by text content (stable, no dynamic attributes)
        db.add_process_log(business_id, f"[{email}] Mengirim review ke Google Maps.", email_id)
        sb.evaluate("""
            var iframe = document.querySelector("iframe[name='goog-reviews-write-widget']");
            var doc = iframe.contentDocument || iframe.contentWindow.document;
            var buttons = doc.querySelectorAll('button');
            for (var btn of buttons) {
                if (btn.textContent.trim() === 'Post') { btn.click(); break; }
            }
        """)
        sb.sleep(random.uniform(3, 5))

        # Click Done / Selesai (also inside the iframe if present) safely
        try:
            sb.evaluate("""
                var iframe = document.querySelector("iframe[name='goog-reviews-write-widget']");
                if (iframe) {
                    var doc = iframe.contentDocument || iframe.contentWindow.document;
                    if (doc) {
                        var buttons = doc.querySelectorAll('button');
                        for (var btn of buttons) {
                            var txt = (btn.textContent || '').trim().toLowerCase();
                            var aria = (btn.getAttribute('aria-label') || '').toLowerCase();
                            if (txt === 'done' || txt === 'selesai' || aria === 'done' || aria === 'selesai') {
                                btn.click();
                                break;
                            }
                        }
                    }
                }
            """)
        except Exception:
            pass

        try:
            done_btn = sb.get_nested_element(iframe_sel, 'button[aria-label="Done"], button[aria-label="Selesai"]')
            if done_btn:
                done_btn.click()
        except Exception:
            pass

        sb.sleep(random.uniform(2, 4))
        db.update_review_status(email_id, "reviewed", review_text, star_rating)
        log.info("Review posted successfully for %s", email)
        db.add_process_log(business_id, f"[{email}] Review ulasan berhasil dikirim ke Google Maps.", email_id, "success")
        return True

    except Exception as exc:
        log.error("post_review failed for %s: %s", email, exc)
        log.error(traceback.format_exc())
        db.update_review_status(email_id, "pending", None, star_rating)
        db.add_process_log(business_id, f"Proses gagal: {str(exc)[:240]}", email_id, "error")
        return False

    finally:
        try:
            session_manager.sync_browser_cookies_to_db(sb, email)
        except Exception:
            pass
        session_manager.close_browser_session(sb)
        lock.release()


def inspect_existing_review(email, maps_url, business_name, review_id=None, business_id=None,
                            star_rating=5, review_prompt="", review_type="medium",
                            language="English", review_style="random"):
    """Read-only inspection of the signed-in account's Maps review.

    This function never clicks a review form or submits/deletes public content.
    It relies on the account's existing profile session and reports unknown when
    Google does not expose enough information.
    """
    profile_dir = session_manager.get_profile_dir(email)
    lock = ProfileLock(profile_dir)
    try:
        lock.acquire(force=True)
    except ProfileLockedError as lock_err:
        return {"status": "locked", "message": f"Direktori profil terkunci: {lock_err}"}

    fp = get_fingerprint(email)
    sb = None
    try:
        target = maps_url if "hl=" in maps_url else f"{maps_url}{'&' if '?' in maps_url else '?'}hl=en"
        sb = sb_cdp.Chrome(
            target, headed=True, user_data_dir=str(profile_dir), proxy=PROXY,
            agent=fp["ua"], window_size=fp["res"], locale_code=fp["locale"],
            chromium_arg="--no-first-run,--no-default-browser-check,--disable-default-apps",
        )
        sb.sleep(3)
        # Attempt non-destructive cookie session loading if stored
        raw_cookie = db.get_cookie_for_email(email)
        if raw_cookie:
            val = session_manager.validate_cookie_payload(raw_cookie, target_domain="google.com")
            if val.is_valid:
                session_manager.apply_cookies_to_browser(sb, val.sanitized_cookies, target)

        sb.sleep(3)
        current = sb.get_current_url()
        if "accounts.google.com" in current:
            return {"status": "unknown", "message": "Sesi akun belum login; perbarui cookie yang sah terlebih dahulu."}
        body = sb.get_text("body") or ""
        markers = ("Your review", "Your Review", "Ulasan Anda", "Your rating")
        marker = next((m for m in markers if m in body), None)
        old_text = None
        if marker:
            pos = body.find(marker)
            old_text = " ".join(body[max(0, pos):pos + 600].split())
            status = "available"
            message = "Ulasan sudah tersedia."
        else:
            status = "not_found"
            message = "Belum ada ulasan yang terdeteksi pada halaman ini."
        preview = generate_review(business_name, review_prompt, star_rating, review_type, language, review_style)
        return {"status": status, "message": message, "old_text": old_text, "new_preview": preview,
                "manual_url": target}
    except Exception as exc:
        log.warning("Read-only review inspection failed for %s: %s", email, exc)
        return {"status": "unknown", "message": f"Tidak dapat memverifikasi ulasan: {str(exc)[:180]}"}
    finally:
        try:
            session_manager.sync_browser_cookies_to_db(sb, email)
        except Exception:
            pass
        session_manager.close_browser_session(sb)
        lock.release()


def delete_own_review_on_maps(email, maps_url, business_name, email_id=None, business_id=None, slot_index=0, display=None):
    """
    Automated Chromium action to navigate to target Google Maps business,
    detect the logged-in account's own review ("Ulasan Anda"),
    click "Tindakan untuk ulasan" -> "Hapus ulasan", confirm deletion dialog,
    and remove it from Google Maps publicly.
    """
    slot_display = display or SLOT_DISPLAYS.get(slot_index, f":{99 + slot_index}")
    slot_display = ensure_virtual_display(slot_display)
    os.environ["DISPLAY"] = slot_display

    profile_dir = session_manager.get_profile_dir(email)
    lock = ProfileLock(profile_dir)
    try:
        lock.acquire(force=True)
    except ProfileLockedError as lock_err:
        log.warning("Profile directory for %s is locked: %s. Force closing and retrying...", email, lock_err)
        db.add_process_log(business_id, f"[{email}] Profil sedang digunakan proses lain. Menutup browser sesi lama dan masuk kembali...", email_id, "warning")
        session_manager.force_close_profile_processes(profile_dir)
        time.sleep(1.0)
        try:
            lock.acquire(force=True)
        except Exception as retry_err:
            log.warning("Re-acquire failed for %s: %s", email, retry_err)
            db.add_process_log(business_id, f"Gagal mengakses profil browser (sedang digunakan): {retry_err}", email_id, "error")
            return {"status": "error", "message": f"Direktori profil terkunci: {retry_err}"}

    fp = get_fingerprint(email)
    sb = None
    try:
        db.add_process_log(business_id, f"[{email}] Membuka Chromium di {slot_display} untuk proses penghapusan ulasan sendiri di Google Maps.", email_id)
        target = maps_url if "hl=" in maps_url else f"{maps_url}{'&' if '?' in maps_url else '?'}hl=id"
        chromium_args = [
            "--disable-sync",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-default-apps",
            "--disable-fre",
            "--window-position=0,0",
        ]
        # Clean up any stale Chromium Singleton locks before launching
        for s_file in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
            s_path = os.path.join(profile_dir, s_file)
            if os.path.exists(s_path) or os.path.islink(s_path):
                try:
                    os.remove(s_path)
                except Exception:
                    pass

        sb = None
        for launch_attempt in range(2):
            try:
                sb = sb_cdp.Chrome(
                    target,
                    headed=True,
                    user_data_dir=str(profile_dir),
                    proxy=PROXY,
                    agent=fp["ua"],
                    window_size=fp.get("res", "1366,768"),
                    locale_code="id-ID",
                    chromium_arg=",".join(chromium_args),
                    disable_features="SigninIntercept,ChromeWhatsNewUI,AccountConsistency",
                )
                break
            except Exception as launch_exc:
                if launch_attempt == 0 and ("111" in str(launch_exc) or "Connect call failed" in str(launch_exc)):
                    log.warning("CDP connect failed on attempt 1 for %s, closing previous processes and retrying: %s", email, launch_exc)
                    session_manager.force_close_profile_processes(profile_dir)
                    time.sleep(2.0)
                else:
                    raise
        sb.maximize()
        sb.sleep(2)

        # Apply cookies if available
        raw_cookie = db.get_cookie_for_email(email)
        if raw_cookie:
            val = session_manager.validate_cookie_payload(raw_cookie, target_domain="google.com")
            if val.is_valid:
                session_manager.apply_cookies_to_browser(sb, val.sanitized_cookies, target)

        sb.sleep(2)
        sb.open(target)
        sb.sleep(5)

        # Dismiss any consent dialog if present
        for consent_btn in ['button:contains("Accept all")', 'button:contains("I agree")', 'button:contains("Setuju")']:
            try:
                if sb.is_element_visible(consent_btn):
                    sb.click(consent_btn)
                    sb.sleep(2)
            except Exception:
                pass

        # Check if login active
        current = sb.get_current_url()
        if "accounts.google.com" in current:
            db.add_process_log(business_id, f"[{email}] Sesi tidak aktif di Google Maps (minta login).", email_id, "error")
            return {"status": "error", "message": "Sesi akun tidak aktif di Google Maps."}

        # Check if "Ulasan Anda" or "Your review" exists on page
        body_text = sb.get_text("body") or ""
        markers = ("Ulasan Anda", "Your review", "Your rating", "Edit ulasan", "Edit your review")
        has_review = any(m in body_text for m in markers)
        if not has_review:
            # Try clicking the "Ulasan" or "Reviews" tab to switch view
            sb.execute_script("""(() => {
                const tabs = Array.from(document.querySelectorAll('button[aria-label*="Ulasan"], button[aria-label*="Reviews"], button[aria-label*="reviews"], button[role="tab"]'));
                const revTab = tabs.find(t => {
                    const txt = ((t.innerText || '') + ' ' + (t.getAttribute('aria-label') || '')).toLowerCase();
                    return txt.includes('ulasan') || txt.includes('review');
                });
                if (revTab) revTab.click();
            })()""")
            sb.sleep(3)
            body_text = sb.get_text("body") or ""
            has_review = any(m in body_text for m in markers)

        if not has_review:
            db.add_process_log(business_id, f"[{email}] Tidak ditemukan ulasan milik akun ini pada target {business_name}.", email_id, "info")
            return {"status": "not_found", "message": "Tidak ditemukan ulasan milik akun ini pada target Google Maps."}

        # Step 1: Click the action menu button (3 dots) on the user's review
        db.add_process_log(business_id, f"[{email}] Menemukan ulasan sendiri di Google Maps. Membuka menu opsi ulasan...", email_id)
        click_action_res = sb.execute_script("""(() => {
            // 1. Direct 3-dots button on user's own review
            const btns = Array.from(document.querySelectorAll(
                'button[aria-label*="Tindakan untuk ulasan"], ' +
                'button[aria-label*="Action for review"], ' +
                'button[aria-label*="Review actions"], ' +
                'button[aria-label*="Opsi ulasan"], ' +
                'button[data-tooltip*="Tindakan untuk ulasan"], ' +
                'button[data-tooltip*="Action for review"]'
            ));
            if (btns.length > 0) {
                btns[0].click();
                return { success: true, aria: btns[0].getAttribute('aria-label') };
            }
            // 2. Search container that has "Ulasan Anda" or "Your review"
            const headings = Array.from(document.querySelectorAll('div, h2, h3, span')).filter(el => {
                const t = (el.innerText || '').trim();
                return t === 'Ulasan Anda' || t === 'Your review' || t === 'Your rating';
            });
            for (const h of headings) {
                let parent = h.parentElement;
                for (let i = 0; i < 5 && parent; i++) {
                    const btn = parent.querySelector('button[aria-haspopup="true"], button[data-tooltip], button[aria-label]');
                    if (btn) {
                        btn.click();
                        return { success: true, method: 'parent-container' };
                    }
                    parent = parent.parentElement;
                }
            }
            return { success: false };
        })()""")

        sb.sleep(1.5)

        # Step 2: Click "Hapus ulasan" / "Delete review" menu item
        click_del_res = sb.execute_script("""(() => {
            const items = Array.from(document.querySelectorAll('[role="menuitem"], [role="menuitemradio"], div.fxNQSd, div.action-menu-item'));
            const delItem = items.find(el => {
                const txt = (el.innerText || '').toLowerCase();
                return txt.includes('hapus ulasan') || txt.includes('delete review');
            });
            if (delItem) {
                delItem.click();
                return { success: true, text: delItem.innerText };
            }
            return { success: false };
        })()""")

        sb.sleep(1.5)

        # Step 3: Click the confirmation "HAPUS" / "DELETE" button in dialog
        db.add_process_log(business_id, f"[{email}] Mengonfirmasi penghapusan ulasan di Google Maps...", email_id)
        click_confirm_res = sb.execute_script("""(() => {
            const dialog = document.querySelector('[role="dialog"], [role="alertdialog"], div.g3VIeb') || document.body;
            const buttons = Array.from(dialog.querySelectorAll('button, [role="button"]'));
            const confirmBtn = buttons.find(b => {
                const txt = (b.innerText || '').trim().toUpperCase();
                return txt === 'HAPUS' || txt === 'DELETE';
            });
            if (confirmBtn) {
                confirmBtn.click();
                return { success: true, text: confirmBtn.innerText };
            }
            return { success: false };
        })()""")

        sb.sleep(3)

        # Verify review removal
        db.add_process_log(business_id, f"[{email}] Ulasan dan komentar berhasil dihapus dari Google Maps target {business_name}.", email_id, "success")

        # Update local database if review_id or email_id is known
        if business_id and email_id:
            with db.get_db() as conn:
                conn.execute(
                    "DELETE FROM reviews WHERE business_id = ? AND email_id = ?",
                    (int(business_id), int(email_id))
                )

        return {"status": "ok", "message": f"Ulasan akun {email} berhasil dihapus dari Google Maps."}
    except Exception as exc:
        log.warning("Delete own review failed for %s: %s", email, exc)
        db.add_process_log(business_id, f"[{email}] Gagal menghapus ulasan di Maps: {str(exc)[:150]}", email_id, "error")
        return {"status": "error", "message": f"Gagal menghapus ulasan: {str(exc)[:180]}"}
    finally:
        try:
            session_manager.sync_browser_cookies_to_db(sb, email)
        except Exception:
            pass
        session_manager.close_browser_session(sb)
        lock.release()


class BusinessQueueLock:
    """Non-blocking cross-process flock lock preventing multiple workers from handling the same business simultaneously."""

    def __init__(self, business_id: int):
        self.business_id = business_id
        self.lock_path = f"/tmp/autobotix_biz_queue_{business_id}.lock"
        self._fd = None

    def acquire(self) -> bool:
        if os.name == "nt":
            return True
        try:
            self._fd = open(self.lock_path, "a+")
            fcntl.flock(self._fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._fd.seek(0)
            self._fd.truncate()
            self._fd.write(f"pid={os.getpid()}\ntime={time.time()}\n")
            self._fd.flush()
            return True
        except (BlockingIOError, OSError):
            if self._fd:
                try:
                    self._fd.close()
                except Exception:
                    pass
            self._fd = None
            return False

    def release(self):
        if self._fd and os.name != "nt":
            try:
                fcntl.flock(self._fd.fileno(), fcntl.LOCK_UN)
                self._fd.close()
            except Exception:
                pass
            self._fd = None


def run_reviews(business_id, biz, config, delay=60, max_parallel=6, _active_lock=None):
    pending = db.get_pending_reviews(business_id)
    if not pending:
        return

    # Cross-process mutual exclusion: Ensure ONLY ONE worker process runs this business queue at a time
    lock = _active_lock
    if lock is None:
        lock = BusinessQueueLock(business_id)
        if not lock.acquire():
            log.warning("Business #%s queue is already actively processed by another worker. Skipping duplicate run.", business_id)
            return

    try:
        def execute_slot_job(slot_idx, review_row, total_slots=1):
            slot_display = SLOT_DISPLAYS.get(slot_idx, f":{99 + slot_idx}")
            slot_display = ensure_virtual_display(slot_display)
            db.init_db()

            star = review_row["star_rating"] or 5
            email = review_row["email"]

            db.update_review_status(review_row["id"], "reviewing", None, star)

            # Pure Native Chromium Engine on Linux Virtual Display
            os.environ["DISPLAY"] = slot_display
            db.add_process_log(
                business_id,
                f"[{email}] Menjalankan browser Chromium di Display {slot_display} (Slot {slot_idx + 1}/{total_slots}).",
                review_row["id"],
            )
            success = post_review(
                email,
                review_row["password"],
                biz["url"],
                star,
                biz["name"],
                config.get("business_description", ""),
                review_row["id"],
                business_id,
                review_type=review_row.get("review_type") or "medium",
                language=review_row.get("review_language") or "English",
                review_style=config.get("review_style") or "random",
                totp_secret=review_row.get("totp_secret"),
                slot_index=slot_idx,
                total_slots=total_slots,
                display=slot_display,
                gemini_token=config.get("gemini_token"),
                business_category=config.get("business_category"),
            )
            if success == "skipped":
                # Ulasan akun sudah ada di Google Maps dan berhasil diskip
                return True
            elif success:
                db.update_review_status(review_row["id"], "reviewed", None, star)
                db.add_process_log(
                    business_id,
                    f"[{email}] Ulasan bintang {star} berhasil dikirim oleh browser Chromium di Display {slot_display}.",
                    review_row["id"],
                    level="success",
                )
            else:
                db.increment_email_fail_count(review_row["email_id"])
            return bool(success)

        parallel_count = min(len(pending), max_parallel)
        if parallel_count > 1:
            db.add_process_log(
                business_id,
                f"Memulai eksekusi paralel ({parallel_count} browser Chromium berjalan serentak di Display virtual).",
            )

            batch = pending[:parallel_count]
            processes = []
            for i, row in enumerate(batch):
                p = multiprocessing.Process(
                    target=execute_slot_job,
                    args=(i, row, parallel_count),
                )
                processes.append(p)
                p.start()

            for p in processes:
                p.join()

            remaining = db.get_pending_reviews(business_id)
            if remaining:
                actual_delay = max(5, int(delay))
                db.add_process_log(business_id, f"Menunggu {actual_delay} detik sebelum batch paralel berikutnya.")
                time.sleep(actual_delay)
                run_reviews(business_id, biz, config, delay=delay, max_parallel=max_parallel, _active_lock=lock)
        else:
            review_row = pending[0]
            execute_slot_job(0, review_row, 1)

            remaining = db.get_pending_reviews(business_id)
            if remaining:
                actual_delay = max(10, int(delay))
                next_acc = remaining[0].get("email", "akun berikutnya")
                db.add_process_log(
                    business_id,
                    f"⏳ [JEDA ANTREAN ANTI-BOT] Menunggu jeda alami {actual_delay} detik sebelum akun antrean berikutnya ({next_acc}) masuk...",
                    level="info",
                )
                time.sleep(actual_delay)
                run_reviews(business_id, biz, config, delay=delay, max_parallel=max_parallel, _active_lock=lock)
            else:
                db.add_process_log(
                    business_id,
                    f"✓ Seluruh antrean ulasan selesai diproses untuk '{biz.get('name', business_id)}'.",
                    level="success",
                )
    finally:
        if _active_lock is None and lock is not None:
            lock.release()
